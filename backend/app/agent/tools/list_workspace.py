# backend/app/agent/tools/list_workspace.py
"""
List Workspace Tool
Enumerates files, ingested documents, artifacts, and scratch files in the workspace.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.agent.tools.base import (
    BaseTool,
    ToolDefinition,
    ToolRiskLevel,
    resolve_secure_workspace_path,
)
from backend.app.config import settings


class FileEntry(BaseModel):
    name: str
    path: str
    size_bytes: int
    is_dir: bool


class ListWorkspaceInput(BaseModel):
    subdirectory: Optional[str] = Field(None, description="Optional subdirectory to list (e.g. 'artifacts' or 'scratch')")


class ListWorkspaceOutput(BaseModel):
    workspace_id: str
    files: List[FileEntry]
    total_files: int


class ListWorkspaceTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_workspace",
            description="List available files, ingested documents, and generated artifacts in the current workspace.",
            input_schema=ListWorkspaceInput,
            output_schema=ListWorkspaceOutput,
            risk_level=ToolRiskLevel.LOW,
            required_permissions=["workspace:read"],
            requires_human_approval=False
        )

    async def execute(self, workspace_id: str, input_data: ListWorkspaceInput) -> ListWorkspaceOutput:
        rel = input_data.subdirectory or ""
        target_dir = resolve_secure_workspace_path(
            workspace_id=workspace_id,
            relative_path=rel,
            must_exist=False
        )

        entries: List[FileEntry] = []
        if target_dir.exists() and target_dir.is_dir():
            for root, dirs, files in os.walk(target_dir):
                # Omit hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for d in dirs:
                    d_path = Path(root) / d
                    rel_p = str(d_path.relative_to(target_dir)).replace("\\", "/")
                    entries.append(FileEntry(
                        name=d,
                        path=rel_p,
                        size_bytes=0,
                        is_dir=True
                    ))
                for f in files:
                    if f.startswith("."):
                        continue
                    f_path = Path(root) / f
                    rel_p = str(f_path.relative_to(target_dir)).replace("\\", "/")
                    try:
                        sz = f_path.stat().st_size
                    except Exception:
                        sz = 0
                    entries.append(FileEntry(
                        name=f,
                        path=rel_p,
                        size_bytes=sz,
                        is_dir=False
                    ))

        return ListWorkspaceOutput(
            workspace_id=workspace_id,
            files=entries,
            total_files=len(entries)
        )
