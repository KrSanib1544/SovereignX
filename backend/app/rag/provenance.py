# backend/app/rag/provenance.py
"""
Provenance & Citation Data Structures
Defines chunk payload metadata required for pre-retrieval authorization,
verifiable citations, and UI split-screen evidence highlights.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChunkProvenance(BaseModel):
    """
    Complete provenance and access control metadata attached to every vector chunk.
    """
    chunk_id: str
    document_id: str
    workspace_id: str
    filename: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    source_location: Optional[str] = None
    bbox: Optional[List[float]] = None  # Normalized [x0, y0, x1, y1] within [0, 1000]
    classification: str = "INTERNAL_ENGINEERING"
    is_table: bool = False
    token_count: int = 0
    content: str

    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Convert chunk into a queryable Qdrant payload dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "workspace_id": self.workspace_id,
            "filename": self.filename,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "section_title": self.section_title or "General",
            "source_location": self.source_location or "",
            "bbox": self.bbox,
            "classification": self.classification,
            "is_table": self.is_table,
            "token_count": self.token_count,
            "text": self.content,
        }
