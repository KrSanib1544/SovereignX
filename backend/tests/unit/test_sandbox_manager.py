# backend/tests/unit/test_sandbox_manager.py
"""
Unit Tests for SandboxManager
Validates Docker availability detection and strict host execution denial when Docker is absent.
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.app.agent.sandbox.manager import SandboxManager, SandboxUnavailableError


def test_sandbox_docker_check():
    sandbox = SandboxManager()
    is_avail, err = sandbox.check_docker_available()
    assert isinstance(is_avail, bool)
    assert isinstance(err, str)


@pytest.mark.asyncio
async def test_sandbox_strictly_denies_host_execution_when_docker_missing():
    """
    Verify Mandatory Security Invariant #6:
    If Docker is unavailable, Python code is NEVER executed on the Windows host.
    """
    sandbox = SandboxManager()
    # Force Docker unavailable state
    sandbox._docker_checked = True
    sandbox._docker_available = False
    sandbox._docker_error = "Docker daemon is offline or not installed."

    with pytest.raises(SandboxUnavailableError) as exc_info:
        await sandbox.execute_python(
            workspace_id="test-ws",
            script_code="import os; print(os.getcwd())",
            timeout_seconds=5
        )

    assert "Security Invariant #6" in str(exc_info.value)
