# backend/tests/unit/test_policy_engine.py
"""
Unit Tests for Deterministic Policy Engine
Validates the 5-stage decision gate: VALIDATE -> AUTHORIZE -> RESOURCE_CHECK -> APPROVAL_CHECK -> DECISION.
"""

import pytest
from backend.app.agent.policy.engine import PolicyEngine
from backend.app.agent.policy.types import PolicyDecisionType
from backend.app.agent.tools.read_file import ReadFileTool
from backend.app.agent.tools.run_python import RunPythonTool


def test_policy_allow_valid_low_risk_call():
    policy = PolicyEngine()
    tool = ReadFileTool()
    args = {"filename": "report.txt", "offset_lines": 0, "max_lines": 50}

    result = policy.evaluate(
        tool=tool,
        workspace_id="ws-123",
        arguments=args
    )

    assert result.decision == PolicyDecisionType.ALLOW
    assert result.allowed is True
    assert result.requires_approval is False


def test_policy_deny_path_traversal():
    policy = PolicyEngine()
    tool = ReadFileTool()
    args = {"filename": "../../../Windows/win.ini"}

    result = policy.evaluate(
        tool=tool,
        workspace_id="ws-123",
        arguments=args
    )

    assert result.decision == PolicyDecisionType.DENY
    assert result.allowed is False
    assert result.violation_code == "SEC_ERR_PATH_TRAVERSAL"


def test_policy_deny_invalid_arguments_schema():
    policy = PolicyEngine()
    tool = ReadFileTool()
    # Missing required 'filename' argument
    args = {"offset_lines": -50}

    result = policy.evaluate(
        tool=tool,
        workspace_id="ws-123",
        arguments=args
    )

    assert result.decision == PolicyDecisionType.DENY
    assert result.allowed is False
    assert result.violation_code == "SEC_ERR_INVALID_SCHEMA"


def test_policy_require_approval_for_high_risk_tool():
    policy = PolicyEngine(auto_approve_high_risk=False)
    tool = RunPythonTool()
    args = {"script": "print('calc')", "timeout_seconds": 10}

    result = policy.evaluate(
        tool=tool,
        workspace_id="ws-123",
        arguments=args,
        is_pre_approved=False
    )

    assert result.decision == PolicyDecisionType.REQUIRE_APPROVAL
    assert result.allowed is False
    assert result.requires_approval is True


def test_policy_allow_pre_approved_high_risk_tool():
    policy = PolicyEngine(auto_approve_high_risk=False)
    tool = RunPythonTool()
    args = {"script": "print('calc')", "timeout_seconds": 10}

    result = policy.evaluate(
        tool=tool,
        workspace_id="ws-123",
        arguments=args,
        is_pre_approved=True
    )

    assert result.decision == PolicyDecisionType.ALLOW
    assert result.allowed is True
    assert result.requires_approval is False
