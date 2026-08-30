# backend/app/db/models/task_orm.py
"""
Task, Step, ToolExecution, and Artifact ORM Models
Manages multi-step agent execution runs, reasoning logs, and generated deliverables.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.core.security import utc_now

if TYPE_CHECKING:
    from backend.app.db.models.workspace_orm import WorkspaceORM
    from backend.app.db.models.audit_orm import AuditEventORM


class TaskORM(Base):
    """
    Represents an autonomous agent task execution session.
    """
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="QUEUED", nullable=False
    )
    max_steps: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED', 'PLANNING', 'EXECUTING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name="chk_task_status"
        ),
        Index("idx_tasks_workspace", "workspace_id"),
    )

    # Relationships
    workspace: Mapped["WorkspaceORM"] = relationship(
        "WorkspaceORM",
        back_populates="tasks"
    )
    steps: Mapped[List["TaskStepORM"]] = relationship(
        "TaskStepORM",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    tool_executions: Mapped[List["ToolExecutionORM"]] = relationship(
        "ToolExecutionORM",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    artifacts: Mapped[List["ArtifactORM"]] = relationship(
        "ArtifactORM",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    audit_events: Mapped[List["AuditEventORM"]] = relationship(
        "AuditEventORM",
        back_populates="task"
    )

    def __repr__(self) -> str:
        return f"<TaskORM(id='{self.id}', status='{self.status}', step={self.current_step}/{self.max_steps})>"


class TaskStepORM(Base):
    """
    Represents an individual step in the agent's ReAct execution loop.
    """
    __tablename__ = "task_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    thought_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    vram_used_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("idx_steps_task", "task_id"),
    )

    # Relationships
    task: Mapped["TaskORM"] = relationship(
        "TaskORM",
        back_populates="steps"
    )
    tool_executions: Mapped[List["ToolExecutionORM"]] = relationship(
        "ToolExecutionORM",
        back_populates="step",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<TaskStepORM(id='{self.id}', task_id='{self.task_id}', step={self.step_number})>"


class ToolExecutionORM(Base):
    """
    Represents a specific tool invocation requested by the agent and verified by the Policy Engine.
    """
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    step_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_steps.id", ondelete="CASCADE"),
        nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    arguments_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="chk_tool_risk_level"
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXECUTING', 'SUCCESS', 'FAILED', 'TIMED_OUT')",
            name="chk_tool_status"
        ),
        Index("idx_tool_exec_task", "task_id"),
    )

    # Relationships
    step: Mapped["TaskStepORM"] = relationship(
        "TaskStepORM",
        back_populates="tool_executions"
    )
    task: Mapped["TaskORM"] = relationship(
        "TaskORM",
        back_populates="tool_executions"
    )

    def __repr__(self) -> str:
        return f"<ToolExecutionORM(id='{self.id}', tool='{self.tool_name}', risk='{self.risk_level}', status='{self.status}')>"


class ArtifactORM(Base):
    """
    Represents an engineering deliverable generated by the agent (DOCX, PPTX, reports, charts).
    """
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("idx_artifacts_task", "task_id"),
    )

    # Relationships
    task: Mapped["TaskORM"] = relationship(
        "TaskORM",
        back_populates="artifacts"
    )
    workspace: Mapped["WorkspaceORM"] = relationship(
        "WorkspaceORM",
        back_populates="artifacts"
    )

    def __repr__(self) -> str:
        return f"<ArtifactORM(id='{self.id}', filename='{self.filename}', size={self.size_bytes})>"
