# backend/app/agent/tools/read_file.py
"""
Read File Tool
Safely reads text, markdown, CSV, or log content within the workspace jail.
Enforces size limits (max 64KB) and line offset pagination.
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.agent.tools.base import (
    BaseTool,
    ToolDefinition,
    ToolRiskLevel,
    resolve_secure_workspace_path,
)


class ReadFileInput(BaseModel):
    filename: str = Field(..., description="Relative path of file within workspace")
    offset_lines: int = Field(0, ge=0, description="Starting line index (0-based)")
    max_lines: int = Field(200, ge=1, le=1000, description="Maximum number of lines to read")


class ReadFileOutput(BaseModel):
    filename: str
    content: str
    total_lines: int
    returned_lines: int
    truncated: bool


class ReadFileTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="Read content from a text, CSV, markdown, or JSON file within the workspace.",
            input_schema=ReadFileInput,
            output_schema=ReadFileOutput,
            risk_level=ToolRiskLevel.LOW,
            required_permissions=["workspace:read"],
            requires_human_approval=False
        )

    async def execute(self, workspace_id: str, input_data: ReadFileInput) -> ReadFileOutput:
        target_path = resolve_secure_workspace_path(
            workspace_id=workspace_id,
            relative_path=input_data.filename,
            must_exist=True
        )

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            raise RuntimeError(f"Failed to read file '{input_data.filename}': {str(e)}") from e

        total_lines = len(lines)
        start = input_data.offset_lines
        end = start + input_data.max_lines
        selected_lines = lines[start:end]
        content_str = "".join(selected_lines)

        # Enforce hard 64KB cap
        max_bytes = 64 * 1024
        truncated = False
        if len(content_str.encode("utf-8")) > max_bytes:
            content_str = content_str[:max_bytes] + "\n... [TRUNCATED: Content exceeded 64KB limit]"
            truncated = True

        return ReadFileOutput(
            filename=input_data.filename,
            content=content_str,
            total_lines=total_lines,
            returned_lines=len(selected_lines),
            truncated=truncated or (end < total_lines)
        )
