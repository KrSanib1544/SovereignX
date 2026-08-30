# backend/app/agent/policy/types.py
"""
Policy Engine Types & Decisions
Defines deterministic decision enums and evaluation result contracts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyDecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class PolicyEvaluationResult(BaseModel):
    decision: PolicyDecisionType
    tool_name: str
    allowed: bool
    requires_approval: bool = False
    reason: Optional[str] = None
    violation_code: Optional[str] = None
    sanitized_arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"
