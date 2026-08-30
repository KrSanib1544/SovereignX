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
3. When referencing documents, provide exact citations (e.g. [CIT-01]).
4. To run calculations or data analysis, use the `run_python` tool.
5. If visual inspection is needed on images/diagrams, use the `inspect_image` tool.
6. YOU MUST ALWAYS RESPOND WITH A VALID JSON OBJECT.

AVAILABLE TOOLS:
{tools_declaration}

FORMAT INSTRUCTIONS:
To invoke a tool, output JSON:
```json
{{
  "thought": "Short rationale for choosing this tool",
  "tool": "<tool_name>",
  "arguments": {{ ... }}
}}
```

When you have completed the task, output:
```json
{{
  "thought": "I have completed all required analyses and deliverables",
  "final_answer": "Comprehensive answer or summary of deliverables produced"
}}
```
"""


class ReActAgent:
    """
    Core ReAct Agent State Machine Engine.
    """

    MAX_STEPS = 15
    MAX_TIMEOUT_SECONDS = 180.0

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

        # Strategy 1: Search for fenced markdown code block first
        code_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text)
        for block in code_blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict):
                    t = data.get("thought", "")
                    tool = data.get("tool")
                    args = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
                    fa = data.get("final_answer")
                    if tool or fa is not None:
                        return t, tool, args if tool else None, fa
            except Exception:
                continue

        # Strategy 2: Direct top-level JSON parse
        try:
            data = json.loads(clean_text)
            if isinstance(data, dict):
                t = data.get("thought", "")
                tool = data.get("tool")
                args = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
                fa = data.get("final_answer")
                if tool or fa is not None:
                    return t, tool, args if tool else None, fa
        except Exception:
            pass

        # Strategy 3: Safe regex extraction of any embedded JSON object
        # Match outermost curly-bracket objects from conversational text
        json_matches = re.finditer(r"(\{[\s\S]*\})", clean_text)
        for m in json_matches:
            snippet = m.group(1)
            # Find matching balanced closing brace
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
                            if isinstance(data, dict):
                                t = data.get("thought", "")
                                tool = data.get("tool")
                                args = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
                                fa = data.get("final_answer")
                                if tool or fa is not None:
                                    return t, tool, args if tool else None, fa
                        except Exception:
                            continue

        # Strategy 4: Fallback conversational Tool/Action detection
        tool_match = re.search(r"(?:Tool|Action):\s*`?([a-zA-Z0-9_]+)`?", clean_text, re.IGNORECASE)
        if tool_match:
            t_name = tool_match.group(1)
            return "Invoking tool from extracted reasoning.", t_name, {}, None

        # Strategy 5: Plain final answer
        return "Formulating final response.", None, None, clean_text

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
                max_tokens=1000
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
