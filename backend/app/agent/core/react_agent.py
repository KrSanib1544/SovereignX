# backend/app/agent/core/react_agent.py
"""
Bounded ReAct Agent Orchestrator
Executes multi-step industrial reasoning with deterministic tool gating,
budget bounds (max 15 steps, 180s timeout), loop prevention, and private reasoning filtering.
"""

import asyncio
import json
import re
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.agent.core.loop_detector import LoopDetector
from backend.app.agent.core.state import (
    AgentState,
    AgentStepRecord,
    AgentTaskResult,
    CitationReference,
    GeneratedArtifact,
    PendingApproval,
)
from backend.app.agent.policy.engine import PolicyEngine
from backend.app.agent.policy.types import PolicyDecisionType, PolicyEvaluationResult
from backend.app.agent.tools.base import BaseTool
from backend.app.agent.tools.registry import ToolRegistry
from backend.app.config import settings
from backend.app.core.audit_logger import AuditLogger
from backend.app.db.models.task_orm import TaskORM, TaskStepORM
from backend.app.models.router import ModelRouter
from backend.app.models.types import GenerationRequest


SYSTEM_PROMPT_TEMPLATE = """You are SOVEREIGN-X, an air-gapped industrial AI agent operating on confidential engineering data.
Your objective is to complete the user's task using verifiable tools.

CRITICAL INVARIANTS:
1. NEVER hallucinate measurements, part numbers, or safety thresholds.
2. Every technical assertion MUST be grounded in an ingested document, table, or calculation.
3. When searching or asking questions about PDFs, manuals, or engineering reports, ALWAYS use the `search_knowledge` tool first with a search query.
4. To run calculations or data analysis, use the `run_python` tool.
5. If visual inspection is needed on images/diagrams, use the `inspect_image` tool.
6. To read plain text logs or scripts, use the `read_file` tool.
7. YOU MUST ALWAYS RESPOND EXCLUSIVELY WITH A VALID JSON OBJECT. Do not output conversational explanations or monologues outside JSON.

AVAILABLE TOOLS:
{tools_declaration}

FORMAT INSTRUCTIONS:
To invoke a tool, output strictly:
```json
{{
  "thought": "Short rationale for choosing this tool",
  "tool": "<tool_name>",
  "arguments": {{ ... }}
}}
```

When you have obtained the information and completed the task, output:
```json
{{
  "thought": "Summary of findings",
  "final_answer": "Complete structured answer to the user's question, citing evidence where applicable."
}}
```
"""


class ReActAgent:
    """
    Core ReAct Agent State Machine Engine.
    """

    MAX_STEPS = 15
    MAX_TIMEOUT_SECONDS = float(settings.TASK_TIMEOUT_SECONDS)

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        policy_engine: Optional[PolicyEngine] = None,
        model_router: Optional[ModelRouter] = None
    ):
        self.tool_registry = tool_registry or ToolRegistry()
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_router = model_router or ModelRouter()
        self.loop_detector = LoopDetector(max_consecutive_repeats=3)

    def _parse_model_output(self, raw_text: str) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Parse raw model text into (thought, tool_name, tool_arguments, final_answer).
        Filters out private thinking blocks (<think>...</think>) and robustly parses JSON.
        """
        clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

        def _clean_final_answer(text: str) -> str:
            cleaned = text.strip()
            patterns = [
                r'(?i)(?:Therefore|In summary|In conclusion|So the answer (?:is|would be):?|Based on the (?:provided )?documents?:?)\s*(.*)',
                r'(?i)(?:The answer is:?)\s*(.*)',
            ]
            for pat in patterns:
                m = re.search(pat, cleaned, flags=re.DOTALL)
                if m and len(m.group(1).strip()) > 20:
                    return m.group(1).strip()
            # Filter leading conversational thoughts if paragraphs exist
            paras = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
            filtered = [
                p for p in paras
                if not re.match(r"^(?:Okay, let's see|First, I need to|Hmm,|Wait,|Looking at the search results|I should structure|The key points from)", p, re.IGNORECASE)
            ]
            # Trim dangling short incomplete trailing fragment
            if filtered and len(filtered) > 1:
                last_line = filtered[-1].strip()
                if len(last_line.split()) <= 3 and not last_line.endswith(('.', '!', '?', ':', '"', '`', ')')):
                    filtered.pop()
            if filtered:
                return "\n\n".join(filtered)
            return cleaned

        def _extract_from_dict(data: dict) -> Optional[Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[str]]]:
            if not isinstance(data, dict):
                return None
            t = str(data.get("thought", "")).strip()
            tool = data.get("tool")
            args = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
            fa = data.get("final_answer") or data.get("answer") or data.get("response") or data.get("result")
            if tool:
                return t or "Executing requested tool.", str(tool).strip(), args, None
            if fa is not None:
                return t or "Formulating final response.", None, None, _clean_final_answer(str(fa))
            if t:
                return t, None, None, _clean_final_answer(t)
            return None

        # Strategy 1: Search for fenced markdown code block first
        code_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text)
        for block in code_blocks:
            try:
                data = json.loads(block)
                res = _extract_from_dict(data)
                if res:
                    return res
            except Exception:
                continue

        # Strategy 2: Direct top-level JSON parse
        try:
            data = json.loads(clean_text)
            res = _extract_from_dict(data)
            if res:
                return res
        except Exception:
            pass

        # Strategy 3: Safe regex extraction of any embedded JSON object
        json_matches = re.finditer(r"(\{[\s\S]*\})", clean_text)
        for m in json_matches:
            snippet = m.group(1)
            depth = 0
            start_idx = -1
            for idx, ch in enumerate(snippet):
                if ch == "{":
                    if depth == 0:
                        start_idx = idx
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0 and start_idx != -1:
                        candidate = snippet[start_idx:idx + 1]
                        try:
                            data = json.loads(candidate)
                            res = _extract_from_dict(data)
                            if res:
                                return res
                        except Exception:
                            continue

        # Strategy 4: Fallback conversational Tool/Action detection
        tool_match = re.search(r"(?:Tool|Action):\s*`?([a-zA-Z0-9_]+)`?", clean_text, re.IGNORECASE)
        if tool_match:
            t_name = tool_match.group(1)
            return "Invoking tool from extracted reasoning.", t_name, {}, None

        # Strategy 5: Plain final answer
        return "Formulating final response.", None, None, _clean_final_answer(clean_text)

    async def execute_task(
        self,
        workspace_id: str,
        prompt: str,
        db_session: Optional[Session] = None,
        task_id: Optional[str] = None,
        pre_approved_action: Optional[Dict[str, Any]] = None
    ) -> AgentTaskResult:
        """
        Execute bounded ReAct execution loop.
        """
        task_id = task_id or str(uuid.uuid4())
        t_start = time.perf_counter()

        task_orm = None
        if db_session:
            task_orm = TaskORM(
                id=task_id,
                workspace_id=workspace_id,
                prompt=prompt,
                status="PLANNING"
            )
            db_session.add(task_orm)
            db_session.flush()

            AuditLogger.record_event(
                session=db_session,
                workspace_id=workspace_id,
                task_id=task_id,
                event_type="TASK_INITIALIZED",
                payload={"prompt": prompt}
            )
            db_session.commit()

        tools_declaration = self.tool_registry.format_tools_for_prompt()
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tools_declaration=tools_declaration)

        conversation_history: List[str] = [
            f"User Task: {prompt}\nContext: Workspace ID '{workspace_id}'"
        ]

        steps: List[AgentStepRecord] = []
        collected_citations: List[CitationReference] = []
        collected_artifacts: List[GeneratedArtifact] = []
        state = AgentState.ACTING
        final_answer: Optional[str] = None
        error_msg: Optional[str] = None
        pending_approval: Optional[PendingApproval] = None

        self.loop_detector.reset()

        # Check if resuming with pre-approved action
        if pre_approved_action:
            p_tool = pre_approved_action.get("tool_name")
            p_args = pre_approved_action.get("arguments", {})
            tool_inst = self.tool_registry.get_tool(p_tool)
            if tool_inst:
                res = await self._execute_approved_tool(
                    workspace_id=workspace_id,
                    tool=tool_inst,
                    arguments=p_args,
                    step_num=1,
                    db_session=db_session,
                    task_id=task_id
                )
                steps.append(res)
                conversation_history.append(f"Observation from {p_tool}: {res.observation}")

        for step_num in range(len(steps) + 1, self.MAX_STEPS + 1):
            elapsed = time.perf_counter() - t_start
            if elapsed > self.MAX_TIMEOUT_SECONDS:
                state = AgentState.TIMED_OUT
                error_msg = f"Task exceeded hard timeout limit ({self.MAX_TIMEOUT_SECONDS}s)"
                break

            # 1. Prompt Model for Next Action
            current_prompt = "\n\n".join(conversation_history) + "\n\nOutput your next step as valid JSON:"
            gen_req = GenerationRequest(
                model=settings.REASONING_MODEL,
                prompt=current_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2048
            )

            t_step_0 = time.perf_counter()
            try:
                gen_res = await self.model_router.generate(gen_req)
            except Exception as e:
                state = AgentState.FAILED
                error_msg = f"Model generation error: {str(e)}"
                break

            thought, tool_name, tool_args, f_ans = self._parse_model_output(gen_res.content)

            # 2. Check for Final Answer
            if f_ans or not tool_name:
                final_answer = f_ans or gen_res.content
                state = AgentState.COMPLETED
                duration_ms = round((time.perf_counter() - t_step_0) * 1000.0, 2)
                steps.append(AgentStepRecord(
                    step_number=step_num,
                    thought=thought,
                    tool_name=None,
                    observation="Task execution completed successfully.",
                    duration_ms=duration_ms,
                    status="COMPLETED"
                ))

                if db_session:
                    step_orm = TaskStepORM(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        step_number=step_num,
                        thought_reasoning=thought,
                        model_used=settings.REASONING_MODEL,
                        execution_time_ms=int(duration_ms)
                    )
                    db_session.add(step_orm)
                    db_session.commit()
                break

            # 3. Loop & Repetition Check
            tool_args = tool_args or {}
            is_loop, loop_reason = self.loop_detector.record_action(tool_name, tool_args)
            if is_loop:
                state = AgentState.BUDGET_EXHAUSTED
                error_msg = loop_reason
                break

            # 4. Lookup Tool
            tool_instance = self.tool_registry.get_tool(tool_name)
            if not tool_instance:
                obs = f"Error: Tool '{tool_name}' is not in the approved registry. Available: {[t.name for t in self.tool_registry.list_tools()]}"
                steps.append(AgentStepRecord(
                    step_number=step_num,
                    thought=thought,
                    tool_name=tool_name,
                    tool_arguments=tool_args,
                    policy_decision="DENY",
                    observation=obs,
                    duration_ms=round((time.perf_counter() - t_step_0) * 1000.0, 2),
                    status="DENIED"
                ))
                conversation_history.append(f"Observation: {obs}")
                continue

            # 5. Policy Engine Gating
            policy_result: PolicyEvaluationResult = self.policy_engine.evaluate(
                tool=tool_instance,
                workspace_id=workspace_id,
                arguments=tool_args
            )

            if db_session:
                AuditLogger.record_event(
                    session=db_session,
                    workspace_id=workspace_id,
                    task_id=task_id,
                    event_type="POLICY_EVALUATION",
                    payload={
                        "tool": tool_name,
                        "decision": policy_result.decision.value,
                        "reason": policy_result.reason,
                        "risk_level": policy_result.risk_level
                    }
                )
                db_session.commit()

            if policy_result.decision == PolicyDecisionType.DENY:
                obs = f"[POLICY DENIAL] Action '{tool_name}' blocked: {policy_result.reason}"
                steps.append(AgentStepRecord(
                    step_number=step_num,
                    thought=thought,
                    tool_name=tool_name,
                    tool_arguments=tool_args,
                    policy_decision="DENY",
                    observation=obs,
                    duration_ms=round((time.perf_counter() - t_step_0) * 1000.0, 2),
                    status="DENIED"
                ))
                conversation_history.append(f"Observation: {obs}")
                continue

            if policy_result.decision == PolicyDecisionType.REQUIRE_APPROVAL:
                state = AgentState.WAITING_APPROVAL
                pending_approval = PendingApproval(
                    tool_name=tool_name,
                    arguments=tool_args,
                    risk_level=policy_result.risk_level,
                    reason=policy_result.reason or "High risk action requires human signoff."
                )
                steps.append(AgentStepRecord(
                    step_number=step_num,
                    thought=thought,
                    tool_name=tool_name,
                    tool_arguments=tool_args,
                    policy_decision="REQUIRE_APPROVAL",
                    observation=f"[WAITING APPROVAL] Operator signoff required for '{tool_name}'.",
                    duration_ms=round((time.perf_counter() - t_step_0) * 1000.0, 2),
                    status="WAITING_APPROVAL"
                ))
                break

            # 6. Execute Allowed Tool
            validated_input = tool_instance.definition.input_schema.model_validate(policy_result.sanitized_arguments)
            try:
                tool_output = await tool_instance.execute(workspace_id, validated_input)
                obs_str = tool_output.model_dump_json() if hasattr(tool_output, "model_dump_json") else str(tool_output)
                step_status = "COMPLETED"
            except Exception as e:
                obs_str = f"Execution error in '{tool_name}': {str(e)}"
                step_status = "ERROR"

            if len(obs_str.encode("utf-8")) > 64 * 1024:
                obs_str = obs_str[:64 * 1024] + "\n... [TRUNCATED: Observation exceeded 64KB]"

            duration_ms = round((time.perf_counter() - t_step_0) * 1000.0, 2)
            step_record = AgentStepRecord(
                step_number=step_num,
                thought=thought,
                tool_name=tool_name,
                tool_arguments=tool_args,
                policy_decision="ALLOW",
                observation=obs_str,
                duration_ms=duration_ms,
                status=step_status
            )
            steps.append(step_record)

            if db_session:
                step_orm = TaskStepORM(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    step_number=step_num,
                    thought_reasoning=thought,
                    model_used=settings.REASONING_MODEL,
                    execution_time_ms=int(duration_ms)
                )
                db_session.add(step_orm)
                db_session.commit()

            # Record citations or artifacts if generated
            if tool_name == "search_knowledge" and hasattr(tool_output, "results"):
                citation_lines = []
                for c in tool_output.results:
                    collected_citations.append(CitationReference(
                        citation_id=c.citation_id,
                        workspace_id=workspace_id,
                        document_id=c.document_id,
                        document_name=c.document_name,
                        page_number=c.page_number,
                        section=c.section_title,
                        excerpt=c.content
                    ))
                    p_str = f"Page {c.page_number}" if c.page_number else ""
                    s_str = f", {c.section_title}" if c.section_title else ""
                    loc_str = f" ({p_str}{s_str})" if (p_str or s_str) else ""
                    citation_lines.append(f"[{c.citation_id}] Document: {c.document_name}{loc_str}\nExcerpt: {c.content}")
                obs_summary = "\n\n".join(citation_lines) if citation_lines else "No matching chunks found in workspace documents."
                conversation_history.append(f"Tool `search_knowledge` Results:\n{obs_summary}")
            elif tool_name == "generate_docx" and hasattr(tool_output, "filename"):
                collected_artifacts.append(GeneratedArtifact(
                    filename=tool_output.filename,
                    size_bytes=getattr(tool_output, "size_bytes", None),
                    sha256_hash=getattr(tool_output, "sha256_hash", None)
                ))
                conversation_history.append(f"Tool `{tool_name}` Output:\n{obs_str}")
            else:
                conversation_history.append(f"Tool `{tool_name}` Output:\n{obs_str}")

        if step_num >= self.MAX_STEPS and state not in (AgentState.COMPLETED, AgentState.WAITING_APPROVAL):
            state = AgentState.BUDGET_EXHAUSTED
            error_msg = f"Task exhausted maximum step budget ({self.MAX_STEPS} steps)."

        total_duration = round((time.perf_counter() - t_start) * 1000.0, 2)

        if db_session and task_orm:
            task_status_map = {
                AgentState.COMPLETED: "COMPLETED",
                AgentState.FAILED: "FAILED",
                AgentState.WAITING_APPROVAL: "WAITING_APPROVAL",
                AgentState.TIMED_OUT: "FAILED",
                AgentState.BUDGET_EXHAUSTED: "FAILED",
                AgentState.ACTING: "EXECUTING",
                AgentState.PLANNING: "PLANNING",
            }
            task_orm.status = task_status_map.get(state, "COMPLETED")
            task_orm.summary_result = final_answer
            task_orm.error_message = error_msg
            db_session.commit()

        return AgentTaskResult(
            task_id=task_id,
            workspace_id=workspace_id,
            state=state,
            prompt=prompt,
            final_answer=final_answer,
            steps=steps,
            pending_approval=pending_approval,
            citations=collected_citations,
            artifacts=collected_artifacts,
            total_steps=len(steps),
            total_duration_ms=total_duration,
            error=error_msg
        )

    async def _execute_approved_tool(
        self,
        workspace_id: str,
        tool: BaseTool,
        arguments: Dict[str, Any],
        step_num: int,
        db_session: Optional[Session],
        task_id: str
    ) -> AgentStepRecord:
        """Helper to run a human-pre-approved tool."""
        t0 = time.perf_counter()
        validated_input = tool.definition.input_schema.model_validate(arguments)
        try:
            output = await tool.execute(workspace_id, validated_input)
            obs = output.model_dump_json() if hasattr(output, "model_dump_json") else str(output)
            status = "COMPLETED"
        except Exception as e:
            obs = f"Error: {str(e)}"
            status = "ERROR"

        dur = round((time.perf_counter() - t0) * 1000.0, 2)
        return AgentStepRecord(
            step_number=step_num,
            thought="Executing human-approved action.",
            tool_name=tool.definition.name,
            tool_arguments=arguments,
            policy_decision="APPROVED_BY_OPERATOR",
            observation=obs,
            duration_ms=dur,
            status=status
        )
