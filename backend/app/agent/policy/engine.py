# backend/app/agent/policy/engine.py
"""
Deterministic Policy Engine
Evaluates proposed agent tool invocations through a mandatory 4-stage decision gate:
VALIDATE -> AUTHORIZE -> RESOURCE_CHECK -> APPROVAL_CHECK -> POLICY DECISION.
The Policy Engine is purely a decision gate and does not perform tool execution.
"""

from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from backend.app.agent.policy.types import PolicyDecisionType, PolicyEvaluationResult
from backend.app.agent.tools.base import (
    BaseTool,
    SecurityPolicyViolationError,
    ToolRiskLevel,
    resolve_secure_workspace_path,
)
from backend.app.models.telemetry import ResourceTelemetry


class PolicyEngine:
    """
    Deterministic Zero-Trust Policy Decision Gate.
    """

    def __init__(
        self,
        auto_approve_high_risk: bool = False,
        enforce_path_containment: bool = True
    ):
        self.auto_approve_high_risk = auto_approve_high_risk
        self.enforce_path_containment = enforce_path_containment

    def evaluate(
        self,
        tool: BaseTool,
        workspace_id: str,
        arguments: Dict[str, Any],
        caller_permissions: Optional[List[str]] = None,
        is_pre_approved: bool = False
    ) -> PolicyEvaluationResult:
        """
        Evaluate a proposed tool call and return an immutable PolicyDecision.
        """
        tool_def = tool.definition
        tool_name = tool_def.name
        caller_perms = set(
            caller_permissions or [
                "workspace:read",
                "workspace:write",
                "rag:search",
                "model:vision",
                "sandbox:execute"
            ]
        )

        # -------------------------------------------------------------
        # STAGE 1: VALIDATE (Schema, Types, Argument Range, Path Bounds)
        # -------------------------------------------------------------
        try:
            validated_input = tool_def.input_schema.model_validate(arguments)
            sanitized_args = validated_input.model_dump()
        except ValidationError as ve:
            return PolicyEvaluationResult(
                decision=PolicyDecisionType.DENY,
                tool_name=tool_name,
                allowed=False,
                reason=f"Argument validation failed: {str(ve)}",
                violation_code="SEC_ERR_INVALID_SCHEMA",
                sanitized_arguments={},
                risk_level=tool_def.risk_level.value
            )

        # Inspect path arguments for directory traversal attempts
        if self.enforce_path_containment:
            for field_name, val in sanitized_args.items():
                if isinstance(val, str) and ("path" in field_name.lower() or "file" in field_name.lower()):
                    if val.strip():
                        try:
                            resolve_secure_workspace_path(
                                workspace_id=workspace_id,
                                relative_path=val,
                                must_exist=False
                            )
                        except SecurityPolicyViolationError as se:
                            return PolicyEvaluationResult(
                                decision=PolicyDecisionType.DENY,
                                tool_name=tool_name,
                                allowed=False,
                                reason=str(se),
                                violation_code=se.violation_code,
                                sanitized_arguments=sanitized_args,
                                risk_level=tool_def.risk_level.value
                            )

        # -------------------------------------------------------------
        # STAGE 2: AUTHORIZE (RBAC Permissions & Workspace Boundary)
        # -------------------------------------------------------------
        required_perms = set(tool_def.required_permissions)
        missing_perms = required_perms - caller_perms
        if missing_perms:
            return PolicyEvaluationResult(
                decision=PolicyDecisionType.DENY,
                tool_name=tool_name,
                allowed=False,
                reason=f"Caller lacks required permissions: {list(missing_perms)}",
                violation_code="SEC_ERR_UNAUTHORIZED_ACTION",
                sanitized_arguments=sanitized_args,
                risk_level=tool_def.risk_level.value
            )

        # -------------------------------------------------------------
        # STAGE 3: RESOURCE CHECK (RAM / GPU VRAM Safety)
        # -------------------------------------------------------------
        sys_info = ResourceTelemetry.get_system_telemetry()
        if sys_info.ram_free_mb < 256:
            return PolicyEvaluationResult(
                decision=PolicyDecisionType.DENY,
                tool_name=tool_name,
                allowed=False,
                reason="Host system free RAM is dangerously low (< 256 MB)",
                violation_code="SEC_ERR_RESOURCE_EXHAUSTED",
                sanitized_arguments=sanitized_args,
                risk_level=tool_def.risk_level.value
            )

        # -------------------------------------------------------------
        # STAGE 4: APPROVAL CHECK (Human-in-the-Loop Gating)
        # -------------------------------------------------------------
        requires_approval = (
            (tool_def.risk_level in (ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL) or tool_def.requires_human_approval)
            and not self.auto_approve_high_risk
            and not is_pre_approved
        )

        if requires_approval:
            return PolicyEvaluationResult(
                decision=PolicyDecisionType.REQUIRE_APPROVAL,
                tool_name=tool_name,
                allowed=False,
                requires_approval=True,
                reason=f"Tool '{tool_name}' carries {tool_def.risk_level.value} risk and requires human operator signoff.",
                violation_code=None,
                sanitized_arguments=sanitized_args,
                risk_level=tool_def.risk_level.value
            )

        # -------------------------------------------------------------
        # STAGE 5: POLICY DECISION -> ALLOW
        # -------------------------------------------------------------
        return PolicyEvaluationResult(
            decision=PolicyDecisionType.ALLOW,
            tool_name=tool_name,
            allowed=True,
            requires_approval=False,
            reason="All policy validation, authorization, and security checks passed.",
            violation_code=None,
            sanitized_arguments=sanitized_args,
            risk_level=tool_def.risk_level.value
        )
