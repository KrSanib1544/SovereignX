# backend/app/rag/__init__.py
"""
SOVEREIGN-X Retrieval-Augmented Generation (RAG) Module
"""

from backend.app.rag.provenance import ChunkProvenance
from backend.app.rag.chunking import HierarchicalChunker
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore, deterministic_point_id
from backend.app.rag.retriever import (
    RetrievalService,
    RetrievalResponse,
    RetrievalResultItem,
)

__all__ = [
    "ChunkProvenance",
    "HierarchicalChunker",
    "LocalEmbeddingEngine",
    "QdrantVectorStore",
    "deterministic_point_id",
    "RetrievalService",
    "RetrievalResponse",
    "RetrievalResultItem",
]
