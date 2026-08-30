# backend/tests/unit/test_agent_tools.py
"""
Unit Tests for Agent Tools
Validates tool definitions, workspace path jail enforcement, and file/artifact generation.
"""

import os
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.agent.tools.base import (
    SecurityPolicyViolationError,
    ToolRiskLevel,
    resolve_secure_workspace_path,
)
from backend.app.agent.tools.read_file import ReadFileInput, ReadFileTool
from backend.app.agent.tools.list_workspace import ListWorkspaceInput, ListWorkspaceTool
from backend.app.agent.tools.search_knowledge import SearchKnowledgeInput, SearchKnowledgeTool
from backend.app.agent.tools.generate_docx import FindingRow, GenerateDocxInput, GenerateDocxTool
from backend.app.config import settings


@pytest.fixture
def temp_workspace(tmp_path, monkeypatch):
    """Set up temporary isolated workspace for testing tools."""
    ws_base = tmp_path / "workspaces"
    monkeypatch.setattr(settings, "WORKSPACES_DIR", ws_base)
    ws_id = "test-ws-tools-001"
    ws_dir = ws_base / ws_id
    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_id, ws_dir


def test_path_jail_resolution_and_rejection(temp_workspace):
    ws_id, ws_dir = temp_workspace
    test_file = ws_dir / "valid.txt"
    test_file.write_text("Hello Sovereign", encoding="utf-8")

    # Valid file resolution
    res = resolve_secure_workspace_path(ws_id, "valid.txt", must_exist=True)
    assert res == test_file.resolve()

    # Path traversal attempts
    with pytest.raises(SecurityPolicyViolationError):
        resolve_secure_workspace_path(ws_id, "../../../Windows/System32/cmd.exe", must_exist=False)

    with pytest.raises(SecurityPolicyViolationError):
        resolve_secure_workspace_path(ws_id, "sub/../../../../etc/passwd", must_exist=False)

    with pytest.raises(SecurityPolicyViolationError):
        resolve_secure_workspace_path(ws_id, "valid.txt\x00.exe", must_exist=False)


@pytest.mark.asyncio
async def test_read_file_tool(temp_workspace):
    ws_id, ws_dir = temp_workspace
    f = ws_dir / "log.txt"
    f.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n", encoding="utf-8")

    tool = ReadFileTool()
    req = ReadFileInput(filename="log.txt", offset_lines=1, max_lines=2)
    output = await tool.execute(ws_id, req)

    assert output.filename == "log.txt"
    assert output.total_lines == 5
    assert output.returned_lines == 2
    assert output.content == "Line 2\nLine 3\n"
    assert output.truncated is True


@pytest.mark.asyncio
async def test_list_workspace_tool(temp_workspace):
    ws_id, ws_dir = temp_workspace
    (ws_dir / "doc1.pdf").write_text("dummy", encoding="utf-8")
    (ws_dir / "scratch").mkdir()
    (ws_dir / "scratch" / "data.csv").write_text("a,b,c", encoding="utf-8")

    tool = ListWorkspaceTool()
    req = ListWorkspaceInput()
    output = await tool.execute(ws_id, req)

    assert output.workspace_id == ws_id
    assert output.total_files >= 2
    paths = [f.path for f in output.files]
    assert "doc1.pdf" in paths


@pytest.mark.asyncio
async def test_generate_docx_tool(temp_workspace):
    ws_id, ws_dir = temp_workspace
    tool = GenerateDocxTool()
    req = GenerateDocxInput(
        output_filename="Pump_Inspection.docx",
        title="Centrifugal Pump 3B Defect Evaluation",
        executive_summary="Ultrasonic testing indicates localized casing thinning.",
        findings=[
            FindingRow(
                component="Casing Wall",
                observed_defect="3.42mm thickness (below 4.00mm min)",
                threshold="4.00mm min",
                risk_level="HIGH",
                citation="[CIT-01]"
            )
        ],
        recommendations=["Schedule replacement within 14 days."]
    )

    output = await tool.execute(ws_id, req)
    assert output.filename == "Pump_Inspection.docx"
    assert output.status == "CREATED"
    assert output.size_bytes > 0

    created_file = ws_dir / "artifacts" / "Pump_Inspection.docx"
    assert created_file.exists()
