# backend/app/agent/tools/run_python.py
"""
Run Python Tool
Dispatches executable Python data/calculation scripts to the SandboxManager.
Classified as HIGH risk — requires Policy Engine approval before execution.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.agent.sandbox.manager import (
    SandboxExecutionResult,
    SandboxManager,
    SandboxUnavailableError,
)
from backend.app.agent.tools.base import BaseTool, ToolDefinition, ToolRiskLevel


class RunPythonInput(BaseModel):
    script: str = Field(..., description="Complete executable Python 3.11 code snippet")
    timeout_seconds: int = Field(15, ge=1, le=30, description="Execution timeout limit in seconds (max 30)")


class RunPythonOutput(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    generated_files: List[str]
    execution_time_ms: float
    timed_out: bool
    status: str


class RunPythonTool(BaseTool):
    def __init__(self, sandbox_manager: Optional[SandboxManager] = None):
        self.sandbox_manager = sandbox_manager or SandboxManager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="run_python",
            description="Execute Python code inside an isolated Docker sandbox container for data calculations and analysis.",
            input_schema=RunPythonInput,
            output_schema=RunPythonOutput,
            risk_level=ToolRiskLevel.HIGH,
            required_permissions=["workspace:read", "workspace:write", "sandbox:execute"],
            requires_human_approval=True
        )

    async def execute(self, workspace_id: str, input_data: RunPythonInput) -> RunPythonOutput:
        try:
            res: SandboxExecutionResult = await self.sandbox_manager.execute_python(
                workspace_id=workspace_id,
                script_code=input_data.script,
                timeout_seconds=input_data.timeout_seconds
            )
            return RunPythonOutput(
                exit_code=res.exit_code,
                stdout=res.stdout,
                stderr=res.stderr,
                generated_files=res.generated_files,
                execution_time_ms=res.execution_time_ms,
                timed_out=res.timed_out,
                status="SUCCESS" if res.exit_code == 0 else "EXECUTION_ERROR"
            )
        except SandboxUnavailableError as sue:
            return RunPythonOutput(
                exit_code=-1,
                stdout="",
                stderr=f"[SECURITY_BLOCK] {str(sue)}",
                generated_files=[],
                execution_time_ms=0.0,
                timed_out=False,
                status="SANDBOX_UNAVAILABLE"
            )
        except Exception as e:
            return RunPythonOutput(
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox error: {str(e)}",
                generated_files=[],
                execution_time_ms=0.0,
                timed_out=False,
                status="INTERNAL_ERROR"
            )
