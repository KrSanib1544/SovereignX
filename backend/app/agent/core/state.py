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


class AgentTaskResult(BaseModel):
    task_id: str
    workspace_id: str
    state: AgentState
    prompt: str
    final_answer: Optional[str] = None
    steps: List[AgentStepRecord] = Field(default_factory=list)
    pending_approval: Optional[PendingApproval] = None
    total_steps: int = 0
    total_duration_ms: float = 0.0
    error: Optional[str] = None
