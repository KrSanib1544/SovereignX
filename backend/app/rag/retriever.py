# backend/app/rag/retriever.py
"""
Authorization-Aware Retrieval Service
Performs dense vector retrieval over Qdrant with pre-retrieval security filters
and provenance-rich result objects.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore


class RetrievalResultItem(BaseModel):
    """
    Structured retrieval result item containing exact provenance and bounding box details.
    """
    chunk_id: str
    score: float
    content: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    source_location: Optional[str] = None
    bbox: Optional[List[float]] = None
    classification: str
    is_table: bool = False
    token_count: int = 0


class RetrievalResponse(BaseModel):
    """
    Response returned by the retrieval service.
    """
    workspace_id: str
    query: str
    total_results: int
    items: List[RetrievalResultItem]


class RetrievalService:
    """
    Core RAG retrieval engine enforcing pre-retrieval access control boundaries.
    """

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_engine: Optional[LocalEmbeddingEngine] = None
    ):
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_engine = embedding_engine or LocalEmbeddingEngine.get_instance()

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        allowed_classifications: Optional[List[str]] = None,
        top_k: int = 4,
        score_threshold: float = 0.0,
        filter_document_id: Optional[str] = None
    ) -> RetrievalResponse:
        """
        Execute semantic search with mandatory pre-retrieval authorization filters.
        """
        if not query or not query.strip():
            return RetrievalResponse(
                workspace_id=workspace_id,
                query=query,
                total_results=0,
                items=[]
            )

        # Default classification scope
        classifications = allowed_classifications or ["PUBLIC", "INTERNAL_ENGINEERING", "RESTRICTED_CONFIDENTIAL"]

        # 1. Local CPU Embedding
        query_vector = self.embedding_engine.embed_query(query.strip())

        # 2. Pre-Retrieval Filtered Search in Qdrant
        raw_results = self.vector_store.search(
            query_vector=query_vector,
            workspace_id=workspace_id,
            allowed_classifications=classifications,
            top_k=top_k,
            filter_document_id=filter_document_id
        )

        # 3. Filter by score threshold and construct typed results
        items = []
        for r in raw_results:
            if r["score"] >= score_threshold:
                items.append(RetrievalResultItem(**r))

        return RetrievalResponse(
            workspace_id=workspace_id,
            query=query,
            total_results=len(items),
            items=items
        )
