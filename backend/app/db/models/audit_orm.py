# backend/app/db/models/audit_orm.py
"""
Immutable Hash-Chained Audit Event ORM Model
Stores cryptographic audit trail records for zero-trust compliance.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Text, Integer, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.core.security import utc_now

if TYPE_CHECKING:
    from backend.app.db.models.workspace_orm import WorkspaceORM
    from backend.app.db.models.task_orm import TaskORM


class AuditEventORM(Base):
    """
    Represents an immutable, cryptographically chained audit log entry.
    Every row contains the SHA-256 hash of its predecessor, creating a tamper-evident event sequence.
    """
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    actor: Mapped[str] = mapped_column(String(100), default="SYSTEM_AGENT", nullable=False)
    workspace_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    client_ip: Mapped[str] = mapped_column(String(45), default="127.0.0.1", nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("idx_audit_task", "task_id"),
        Index("idx_audit_workspace", "workspace_id"),
        Index("idx_audit_uuid", "event_uuid"),
    )

    # Relationships
    workspace: Mapped[Optional["WorkspaceORM"]] = relationship(
        "WorkspaceORM",
        back_populates="audit_events"
    )
    task: Mapped[Optional["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="audit_events"
    )

    def __repr__(self) -> str:
        return f"<AuditEventORM(id={self.id}, uuid='{self.event_uuid}', type='{self.event_type}', hash='{self.current_hash[:10]}...')>"
