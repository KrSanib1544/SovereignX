# backend/app/api/endpoints/agent_api.py
"""
Agent Tasks REST & SSE Endpoints
Provides APIs to initialize agent tasks, inspect steps, approve high-risk actions, and stream events.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.agent.core.react_agent import ReActAgent
from backend.app.agent.core.router import TaskExecutionRouter
from backend.app.agent.core.state import AgentState, AgentTaskResult
from backend.app.agent.policy.engine import PolicyEngine
from backend.app.db.models.task_orm import TaskORM, TaskStepORM
from backend.app.db.session import get_db_session

router = APIRouter()


class CreateTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Task prompt for the agent")
    auto_approve_high_risk: bool = Field(False, description="Whether to automatically approve HIGH risk actions")
    document_id: Optional[str] = Field(None, description="Optional document UUID filter for scoped retrieval")


class ApproveActionRequest(BaseModel):
    approved: bool = Field(..., description="True to execute, False to reject")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


@router.post("/workspaces/{workspace_id}/tasks", response_model=AgentTaskResult)
async def create_agent_task(
    workspace_id: str,
    req: CreateTaskRequest,
    db: Session = Depends(get_db_session)
):
    """
    Initialize and execute a task in the given workspace via intelligent execution routing.
    """
    policy = PolicyEngine(auto_approve_high_risk=req.auto_approve_high_risk)
    task_router = TaskExecutionRouter(policy_engine=policy)

    result = await task_router.execute(
        workspace_id=workspace_id,
        prompt=req.prompt,
        db_session=db,
        document_id=req.document_id,
    )
    return result


@router.get("/workspaces/{workspace_id}/tasks/{task_id}")
async def get_task_details(
    workspace_id: str,
    task_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Retrieve stored status and steps of an agent task.
    """
    task = db.query(TaskORM).filter(
        TaskORM.id == task_id,
        TaskORM.workspace_id == workspace_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found in this workspace")

    steps = db.query(TaskStepORM).filter(TaskStepORM.task_id == task_id).order_by(TaskStepORM.step_number.asc()).all()

    return {
        "task_id": task.id,
        "workspace_id": task.workspace_id,
        "prompt": task.prompt,
        "status": task.status,
        "summary_result": task.summary_result,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "steps": [
            {
                "step_number": s.step_number,
                "thought": s.thought_reasoning,
                "model_used": s.model_used,
                "execution_time_ms": s.execution_time_ms
            }
            for s in steps
        ]
    }


@router.post("/workspaces/{workspace_id}/tasks/{task_id}/approve", response_model=AgentTaskResult)
async def approve_task_action(
    workspace_id: str,
    task_id: str,
    req: ApproveActionRequest,
    db: Session = Depends(get_db_session)
):
    """
    Approve or reject a pending high-risk tool action for a waiting task.
    """
    task = db.query(TaskORM).filter(
        TaskORM.id == task_id,
        TaskORM.workspace_id == workspace_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not req.approved:
        task.status = "FAILED"
        task.error_message = f"Action '{req.tool_name}' was rejected by human operator."
        db.commit()
        return AgentTaskResult(
            task_id=task_id,
            workspace_id=workspace_id,
            state=AgentState.FAILED,
            prompt=task.prompt or "",
            error="Action rejected by operator."
        )

    # Resume agent with pre-approved action
    agent = ReActAgent()
    result = await agent.execute_task(
        workspace_id=workspace_id,
        prompt=task.prompt or "",
        db_session=db,
        task_id=task_id,
        pre_approved_action={
            "tool_name": req.tool_name,
            "arguments": req.arguments
        }
    )
    return result
