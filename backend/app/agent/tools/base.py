# backend/app/agent/tools/base.py
"""
Base Tool Definitions & Security Boundaries
Defines the strict typed Tool interface, Risk Level classification,
and server-side workspace path containment.
"""

from abc import ABC, abstractmethod
from enum import Enum
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from backend.app.config import settings


class ToolRiskLevel(str, Enum):
    LOW = "LOW"            # Read-only queries within workspace (read_file, list_workspace, search_knowledge)
    MEDIUM = "MEDIUM"      # Non-destructive generation/multimodal (inspect_image, generate_docx)
    HIGH = "HIGH"          # Code execution / destructive changes (run_python)
    CRITICAL = "CRITICAL"  # System configuration or bulk deletions (Never automated)


class ToolDefinition(BaseModel):
    """
    Immutable specification metadata for an agent tool.
    """
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    required_permissions: List[str] = Field(default_factory=lambda: ["workspace:read"])
    requires_human_approval: bool = False


class SecurityPolicyViolationError(Exception):
    """Raised when a tool argument attempts path traversal or privilege escalation."""
    def __init__(self, message: str, violation_code: str = "SEC_ERR_POLICY_VIOLATION"):
        self.violation_code = violation_code
        super().__init__(f"[{violation_code}] {message}")


def resolve_secure_workspace_path(
    workspace_id: str,
    relative_path: str,
    must_exist: bool = True,
    allow_scratch_only: bool = False
) -> Path:
    """
    Server-side Path Containment Jail.
    Strictly verifies that the resolved path resides within WORKSPACES_DIR/{workspace_id}/.
    Rejects directory traversal (..), absolute paths, null bytes, and out-of-jail targets.
    """
    if "\x00" in relative_path:
        raise SecurityPolicyViolationError(
            "Null byte detected in file path argument",
            violation_code="SEC_ERR_NULL_BYTE"
        )

    base_dir = (settings.WORKSPACES_DIR / workspace_id).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    enforced_root = (base_dir / "scratch").resolve() if allow_scratch_only else base_dir
    enforced_root.mkdir(parents=True, exist_ok=True)

    rel_p = Path(relative_path)
    if rel_p.is_absolute():
        # Absolute path provided
        try:
            target_path = rel_p.resolve()
            target_path.relative_to(enforced_root)
        except ValueError:
            raise SecurityPolicyViolationError(
                f"Absolute path escape detected: '{relative_path}' is outside workspace root '{enforced_root}'",
                violation_code="SEC_ERR_PATH_TRAVERSAL"
            )
    else:
        # Relative path provided
        target_path = (enforced_root / relative_path).resolve()
        try:
            target_path.relative_to(enforced_root)
        except ValueError:
            raise SecurityPolicyViolationError(
                f"Path traversal detected: '{relative_path}' attempts to escape workspace root '{enforced_root}'",
                violation_code="SEC_ERR_PATH_TRAVERSAL"
            )

    if must_exist and not target_path.exists():
        raise FileNotFoundError(f"Requested file '{relative_path}' not found in workspace.")

    return target_path


class BaseTool(ABC):
    """
    Abstract Base Class for all Sovereign-X Agent Tools.
    """
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the immutable tool definition specification."""
        pass

    @abstractmethod
    async def execute(self, workspace_id: str, input_data: BaseModel) -> BaseModel:
        """Execute the tool action within the secured workspace context."""
        pass
