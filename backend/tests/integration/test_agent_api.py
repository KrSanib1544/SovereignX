# backend/tests/integration/test_agent_api.py
"""
Integration Tests for Agent Task REST Endpoints
Validates task creation, retrieval, step auditing, and human approval gating via FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend.app.main import app
from backend.app.models.types import GenerationResponse
from backend.app.agent.core.state import AgentState
from backend.app.db.models.workspace_orm import WorkspaceORM
from backend.app.db.session import SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_test_workspace():
    """Ensure a valid test workspace exists in the database for task foreign key constraints."""
    db = SessionLocal()
    try:
        ws = db.query(WorkspaceORM).filter(WorkspaceORM.id == "ws-agent-test").first()
        if not ws:
            ws = WorkspaceORM(
                id="ws-agent-test",
                name="Test Agent Workspace",
                classification_level="INTERNAL_ENGINEERING",
                storage_path="./data/workspaces/ws-agent-test"
            )
            db.add(ws)
            db.commit()
    finally:
        db.close()


def test_agent_task_lifecycle_mocked():
    with patch("backend.app.models.router.ModelRouter.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = GenerationResponse(
            model="qwen3:4b",
            content='{"thought": "Inspecting workspace", "final_answer": "All documents verified."}',
            total_duration_ms=150.0
        )

        # 1. Initialize Task
        res = client.post(
            "/api/v1/workspaces/ws-agent-test/tasks",
            json={"prompt": "Review all pump data", "auto_approve_high_risk": False}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["state"] == "COMPLETED"
        assert data["final_answer"] == "All documents verified."
        assert len(data["steps"]) >= 1
        task_id = data["task_id"]

        # 2. Get Task Details
        get_res = client.get(f"/api/v1/workspaces/ws-agent-test/tasks/{task_id}")
        assert get_res.status_code == 200
        task_data = get_res.json()
        assert task_data["task_id"] == task_id
        assert task_data["status"] == "COMPLETED"
        assert len(task_data["steps"]) >= 1


def test_agent_approval_rejection():
    # Test rejection of a non-existent task returns 404
    res = client.post(
        "/api/v1/workspaces/ws-agent-test/tasks/non-existent-task/approve",
        json={
            "approved": False,
            "tool_name": "run_python",
            "arguments": {"script": "print(1)"}
        }
    )
    assert res.status_code == 404
