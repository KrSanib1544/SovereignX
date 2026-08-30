# backend/app/db/models/document_orm.py
"""
Document and DocumentChunk ORM Models
Manages ingested documents and vector-searchable chunks with explicit page-level provenance.
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


class DocumentORM(Base):
    """
    Represents an ingested engineering document, PDF, OCR scan, spreadsheet, or image.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
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
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ocr_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parsing_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "parsing_status IN ('PENDING', 'PARSING', 'INDEXED', 'FAILED')",
            name="chk_document_parsing_status"
        ),
        Index("idx_docs_workspace", "workspace_id"),
        Index("idx_docs_hash", "sha256_hash"),
    )

    # Relationships
    workspace: Mapped["WorkspaceORM"] = relationship(
        "WorkspaceORM",
        back_populates="documents"
    )
    chunks: Mapped[List["DocumentChunkORM"]] = relationship(
        "DocumentChunkORM",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<DocumentORM(id='{self.id}', filename='{self.filename}', status='{self.parsing_status}')>"


class DocumentChunkORM(Base):
    """
    Represents an extracted semantic chunk retained for RAG retrieval with provenance coordinates.
    """
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bbox_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: [x0, y0, x1, y1]
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("idx_chunks_doc", "document_id"),
        Index("idx_chunks_workspace", "workspace_id"),
    )

    # Relationships
    document: Mapped["DocumentORM"] = relationship(
        "DocumentORM",
        back_populates="chunks"
    )
    workspace: Mapped["WorkspaceORM"] = relationship(
        "WorkspaceORM",
        back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<DocumentChunkORM(id='{self.id}', doc_id='{self.document_id}', page={self.page_number})>"
