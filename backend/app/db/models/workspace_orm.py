# backend/app/db/models/workspace_orm.py
"""
Workspace ORM Model
Defines isolated workspaces for partitioning documents, tasks, and audit traces.
"""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.core.security import utc_now

if TYPE_CHECKING:
    from backend.app.db.models.document_orm import DocumentORM, DocumentChunkORM
    from backend.app.db.models.task_orm import TaskORM, ArtifactORM
    from backend.app.db.models.audit_orm import AuditEventORM


class WorkspaceORM(Base):
    """
    Represents an isolated workspace sandbox containing confidential engineering assets.
    """
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    classification_level: Mapped[str] = mapped_column(
        String(50), default="INTERNAL_ENGINEERING", nullable=False
    )
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "classification_level IN ('PUBLIC', 'INTERNAL_ENGINEERING', 'RESTRICTED_CONFIDENTIAL')",
            name="chk_workspace_classification"
        ),
    )

    # Relationships with CASCADE delete to ensure clean workspace deletion
    documents: Mapped[List["DocumentORM"]] = relationship(
        "DocumentORM",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    chunks: Mapped[List["DocumentChunkORM"]] = relationship(
        "DocumentChunkORM",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    artifacts: Mapped[List["ArtifactORM"]] = relationship(
        "ArtifactORM",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    audit_events: Mapped[List["AuditEventORM"]] = relationship(
        "AuditEventORM",
        back_populates="workspace"
    )

    def __repr__(self) -> str:
        return f"<WorkspaceORM(id='{self.id}', name='{self.name}', classification='{self.classification_level}')>"
