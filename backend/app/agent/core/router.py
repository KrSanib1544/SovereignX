# backend/app/agent/core/router.py
"""
Intelligent Execution Router
Routes incoming user tasks dynamically between:
- CLASS A (Fast RAG Direct Pipeline): 1 Vector Retrieval + 1 Direct LLM Synthesis (~15-25s)
- CLASS B (Bounded Multi-Step ReAct Agent): Autonomous planning loop for code, docker, vision, and deliverables.
"""

import re
import time
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.agent.core.react_agent import ReActAgent
from backend.app.agent.core.state import (
    AgentState,
    AgentStepRecord,
    AgentTaskResult,
    CitationReference,
    ExecutionMetrics,
)
from backend.app.agent.policy.engine import PolicyEngine
from backend.app.agent.tools.search_knowledge import (
    SearchKnowledgeInput,
    SearchKnowledgeTool,
)
from backend.app.config import settings
from backend.app.core.audit_logger import AuditLogger
from backend.app.db.models.task_orm import TaskORM, TaskStepORM
from backend.app.models.router import ModelRouter
from backend.app.models.types import GenerationRequest


CLASS_B_KEYWORDS = [
    r"\bpython\b",
    r"\bcode\b",
    r"\bcalculate\b",
    r"\bcalculation\b",
    r"\bregression\b",
    r"\bscript\b",
    r"\bsandbox\b",
    r"\bdocker\b",
    r"\binspect_image\b",
    r"\bimage\b",
    r"\bphoto\b",
    r"\bpicture\b",
    r"\bweld\b",
    r"\bvisual inspection\b",
    r"\.jpg\b",
    r"\.jpeg\b",
    r"\.png\b",
    r"\bgenerate_docx\b",
    r"\bdocx\b",
    r"\bapproval note\b",
    r"\bdeliverable\b",
    r"\bexport report\b",
    r"\bcorrelate\b",
    r"\bcross-reference\b",
]


class TaskExecutionRouter:
    """
    Intelligent Router selecting the optimal execution pipeline based on task complexity.
    """

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        model_router: Optional[ModelRouter] = None,
        search_tool: Optional[SearchKnowledgeTool] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_router = model_router or ModelRouter()
        self.search_tool = search_tool or SearchKnowledgeTool()
        self.react_agent = ReActAgent(
            policy_engine=self.policy_engine,
            model_router=self.model_router,
        )

    def classify_prompt(self, prompt: str) -> str:
        """
        Classify prompt into CLASS_A_FAST_RAG or CLASS_B_MULTI_STEP_AGENT.
        """
        prompt_lower = prompt.lower()
        for pat in CLASS_B_KEYWORDS:
            if re.search(pat, prompt_lower):
                return "CLASS_B_MULTI_STEP_AGENT"
        return "CLASS_A_FAST_RAG"

    async def execute(
        self,
        workspace_id: str,
        prompt: str,
        db_session: Optional[Session] = None,
        task_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> AgentTaskResult:
        """
        Execute task through the classified optimal pipeline.
        """
        t_start = time.perf_counter()
        pipeline_class = self.classify_prompt(prompt)
        t_classify = round((time.perf_counter() - t_start) * 1000.0, 2)

        if pipeline_class == "CLASS_A_FAST_RAG":
            return await self._execute_fast_rag(
                workspace_id=workspace_id,
                prompt=prompt,
                db_session=db_session,
                task_id=task_id,
                document_id=document_id,
                t_start=t_start,
                t_classify=t_classify,
            )
        else:
            res = await self.react_agent.execute_task(
                workspace_id=workspace_id,
                prompt=prompt,
                db_session=db_session,
                task_id=task_id,
            )
            total_dur = round((time.perf_counter() - t_start) * 1000.0, 2)
            res.metrics = ExecutionMetrics(
                pipeline_type="CLASS_B_MULTI_STEP_AGENT",
                classification_ms=t_classify,
                retrieval_ms=0.0,
                llm_generation_ms=res.total_duration_ms,
                tool_execution_ms=0.0,
                total_duration_ms=total_dur,
                model_invocations=max(1, len(res.steps)),
                model_name=settings.REASONING_MODEL,
            )
            return res

    async def _execute_fast_rag(
        self,
        workspace_id: str,
        prompt: str,
        db_session: Optional[Session],
        task_id: Optional[str],
        document_id: Optional[str],
        t_start: float,
        t_classify: float,
    ) -> AgentTaskResult:
        """
        Execute single-turn Fast RAG Pipeline (1 Retrieval + 1 Direct LLM Generation).
        """
        task_id = task_id or str(uuid.uuid4())

        task_orm = None
        if db_session:
            task_orm = TaskORM(
                id=task_id,
                workspace_id=workspace_id,
                prompt=prompt,
                status="EXECUTING",
            )
            db_session.add(task_orm)
            db_session.flush()

            AuditLogger.record_event(
                session=db_session,
                workspace_id=workspace_id,
                task_id=task_id,
                event_type="TASK_INITIALIZED",
                payload={"prompt": prompt, "pipeline": "CLASS_A_FAST_RAG", "document_id": document_id},
            )
            db_session.commit()

        # 1. Fast Semantic Retrieval
        t_ret_0 = time.perf_counter()
        citations: List[CitationReference] = []
        excerpt_blocks: List[str] = []

        try:
            search_out = await self.search_tool.execute(
                workspace_id=workspace_id,
                input_data=SearchKnowledgeInput(query=prompt, top_k=4, document_id=document_id),
            )
            for c in search_out.results:
                citations.append(
                    CitationReference(
                        citation_id=c.citation_id,
                        workspace_id=workspace_id,
                        document_id=c.document_id,
                        document_name=c.document_name,
                        page_number=c.page_number,
                        section=c.section_title,
                        excerpt=c.content,
                    )
                )
                p_str = f"Page {c.page_number}" if c.page_number else ""
                s_str = f", {c.section_title}" if c.section_title else ""
                loc = f" ({p_str}{s_str})" if (p_str or s_str) else ""
                excerpt_blocks.append(
                    f"[{c.citation_id}] Document: {c.document_name}{loc}\nExcerpt: {c.content}"
                )
        except Exception as e:
            excerpt_blocks.append(f"Vector search retrieval error: {str(e)}")

        t_retrieval = round((time.perf_counter() - t_ret_0) * 1000.0, 2)
        retrieved_context = (
            "\n\n".join(excerpt_blocks)
            if excerpt_blocks
            else "No relevant documents found in workspace."
        )

        # 2. Single LLM Synthesis Generation
        t_llm_0 = time.perf_counter()
        system_prompt = (
            "You are SOVEREIGN-X, an air-gapped industrial AI engineering assistant operating on confidential data.\n"
            "Answer the user's inquiry based strictly on the retrieved document excerpts provided below.\n\n"
            "CRITICAL INVARIANTS:\n"
            "1. Ground every technical fact, measurement, and assertion in the provided excerpts.\n"
            "2. Cite evidence directly using the citation markers (e.g. [CIT-01]).\n"
            "3. If information is not present in the excerpts, clearly state that the requested document/data is unavailable.\n"
            "4. Provide a direct, complete, and professional engineering answer.\n"
            "5. Do NOT output internal chain-of-thought monologues (such as 'Okay, let's see'). Write only the direct answer."
        )

        user_content = (
            f"RETRIEVED DOCUMENT EXCERPTS:\n{retrieved_context}\n\n"
            f"USER INQUIRY:\n{prompt}"
        )

        gen_req = GenerationRequest(
            model=settings.REASONING_MODEL,
            prompt=user_content,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=2048,
        )

        try:
            gen_res = await self.model_router.generate(gen_req)
            raw_answer = gen_res.content
            # Clean monologue preambles if present
            final_answer = self._clean_synthesis(raw_answer)
            task_status = AgentState.COMPLETED
            error_msg = None
        except Exception as e:
            final_answer = f"Synthesis generation error: {str(e)}"
            task_status = AgentState.FAILED
            error_msg = str(e)

        t_llm = round((time.perf_counter() - t_llm_0) * 1000.0, 2)
        total_duration = round((time.perf_counter() - t_start) * 1000.0, 2)

        # 3. Create Single Execution Step Record
        step_rec = AgentStepRecord(
            step_number=1,
            thought="Direct semantic knowledge retrieval & single-turn LLM synthesis",
            tool_name="search_knowledge",
            tool_arguments={"query": prompt, "top_k": 4},
            policy_decision="ALLOW",
            observation=f"Retrieved {len(citations)} citations in {t_retrieval}ms.",
            duration_ms=t_retrieval + t_llm,
            status="COMPLETED" if task_status == AgentState.COMPLETED else "ERROR",
        )

        if db_session:
            step_orm = TaskStepORM(
                id=str(uuid.uuid4()),
                task_id=task_id,
                step_number=1,
                thought_reasoning="Direct semantic knowledge retrieval & single-turn LLM synthesis",
                model_used=settings.REASONING_MODEL,
                execution_time_ms=int(t_retrieval + t_llm),
            )
            db_session.add(step_orm)
            if task_orm:
                task_orm.status = "COMPLETED" if task_status == AgentState.COMPLETED else "FAILED"
                task_orm.summary_result = final_answer
                task_orm.error_message = error_msg
            db_session.commit()

        metrics = ExecutionMetrics(
            pipeline_type="CLASS_A_FAST_RAG",
            classification_ms=t_classify,
            retrieval_ms=t_retrieval,
            llm_generation_ms=t_llm,
            tool_execution_ms=t_retrieval,
            total_duration_ms=total_duration,
            model_invocations=1,
            model_name=settings.REASONING_MODEL,
        )

        return AgentTaskResult(
            task_id=task_id,
            workspace_id=workspace_id,
            state=task_status,
            prompt=prompt,
            final_answer=final_answer,
            steps=[step_rec],
            citations=citations,
            artifacts=[],
            metrics=metrics,
            total_steps=1,
            total_duration_ms=total_duration,
            error=error_msg,
        )

    def _clean_synthesis(self, text: str) -> str:
        """Filter leading conversational monologue preambles from model output."""
        cleaned = text.strip()
        # If response is a JSON string with final_answer, extract it
        if cleaned.startswith("{") and "final_answer" in cleaned:
            try:
                import json
                d = json.loads(cleaned)
                if isinstance(d, dict) and "final_answer" in d:
                    return str(d["final_answer"]).strip()
            except Exception:
                pass

        # Remove <think> tags if any
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
        paras = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        filtered = [
            p
            for p in paras
            if not re.match(
                r"^(?:Okay, let's see|First, I need to|Hmm,|Wait,|Looking at the search results|I should structure|The key points from)",
                p,
                re.IGNORECASE,
            )
        ]
        if filtered:
            return "\n\n".join(filtered)
        return cleaned
