# backend/app/agent/core/state.py
"""
Agent State Machine Enums & Data Contracts
Defines execution phases, task state transitions, and step summaries.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    ACTING = "ACTING"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    OBSERVATION = "OBSERVATION"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


class AgentStepRecord(BaseModel):
    step_number: int
    thought: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    policy_decision: Optional[str] = None
    observation: Optional[str] = None
    duration_ms: float = 0.0
    status: str = "COMPLETED"


class PendingApproval(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    risk_level: str
    reason: str


class CitationReference(BaseModel):
    citation_id: str
    workspace_id: Optional[str] = None
    document_id: Optional[str] = None
    document_name: str
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    excerpt: str
    bbox: Optional[List[float]] = None


class GeneratedArtifact(BaseModel):
    id: Optional[str] = None
    filename: str
    size_bytes: Optional[int] = None
    sha256_hash: Optional[str] = None


class ExecutionMetrics(BaseModel):
    pipeline_type: str = "CLASS_A_FAST_RAG"
    classification_ms: float = 0.0
    retrieval_ms: float = 0.0
    llm_generation_ms: float = 0.0
    tool_execution_ms: float = 0.0
    total_duration_ms: float = 0.0
    model_invocations: int = 1
    model_name: str = "qwen3:4b"
    tokens_generated: Optional[int] = None
    prompt_tokens: Optional[int] = None


class AgentTaskResult(BaseModel):
    task_id: str
    workspace_id: str
    state: AgentState
    prompt: str
    final_answer: Optional[str] = None
    steps: List[AgentStepRecord] = Field(default_factory=list)
    pending_approval: Optional[PendingApproval] = None
    citations: List[CitationReference] = Field(default_factory=list)
    artifacts: List[GeneratedArtifact] = Field(default_factory=list)
    metrics: Optional[ExecutionMetrics] = None
    total_steps: int = 0
    total_duration_ms: float = 0.0
    error: Optional[str] = None
