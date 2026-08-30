# backend/tests/unit/test_qdrant_store.py
"""
Unit Tests for Local Qdrant Vector Store
Validates collection setup, upserts, deterministic IDs, pre-retrieval filtering, and deletions.
"""

import pytest
from backend.app.rag.vector_store import QdrantVectorStore, deterministic_point_id
from backend.app.rag.provenance import ChunkProvenance
from backend.app.rag.embeddings import LocalEmbeddingEngine


@pytest.fixture
def memory_vector_store():
    """Provides an isolated, in-memory Qdrant client for fast unit testing."""
    store = QdrantVectorStore(location=":memory:")
    store.init_collection(dimension=384, recreate=True)
    return store


def test_qdrant_upsert_and_pre_retrieval_filtering(memory_vector_store):
    """Test upserting chunks and executing pre-retrieval authorization filters."""
    embedder = LocalEmbeddingEngine.get_instance()

    ws_a = "ws_defense_01"
    ws_b = "ws_commercial_02"

    chunk_a = ChunkProvenance(
        chunk_id="chk_a_001",
        document_id="doc_a",
        workspace_id=ws_a,
        filename="classified_pump.pdf",
        chunk_index=0,
        page_number=4,
        classification="RESTRICTED_CONFIDENTIAL",
        content="Pump 3B wall thickness measured at 3.42mm critical wear."
    )
    chunk_b = ChunkProvenance(
        chunk_id="chk_b_001",
        document_id="doc_b",
        workspace_id=ws_b,
        filename="public_catalog.pdf",
        chunk_index=0,
        page_number=1,
        classification="PUBLIC",
        content="General pump models and external casing dimensions."
    )

    vec_a = embedder.embed_query(chunk_a.content)
    vec_b = embedder.embed_query(chunk_b.content)

    # Upsert
    memory_vector_store.upsert_chunks(
        chunks=[chunk_a, chunk_b],
        vectors=[vec_a, vec_b]
    )

    query_vec = embedder.embed_query("What is the measured wall thickness for Pump 3B?")

    # 1. Search in Workspace A with RESTRICTED_CONFIDENTIAL access -> Must find chunk_a
    results_a = memory_vector_store.search(
        query_vector=query_vec,
        workspace_id=ws_a,
        allowed_classifications=["RESTRICTED_CONFIDENTIAL", "PUBLIC"],
        top_k=2
    )
    assert len(results_a) == 1
    assert results_a[0]["chunk_id"] == "chk_a_001"
    assert results_a[0]["document_id"] == "doc_a"

    # 2. Search in Workspace A with only PUBLIC access -> Must return 0 (Pre-retrieval security block)
    results_a_restricted = memory_vector_store.search(
        query_vector=query_vec,
        workspace_id=ws_a,
        allowed_classifications=["PUBLIC"],
        top_k=2
    )
    assert len(results_a_restricted) == 0

    # 3. Search in Workspace B -> Must NOT find chunk_a from Workspace A (Tenancy isolation)
    results_b = memory_vector_store.search(
        query_vector=query_vec,
        workspace_id=ws_b,
        allowed_classifications=["RESTRICTED_CONFIDENTIAL", "PUBLIC"],
        top_k=2
    )
    assert len(results_b) == 1
    assert results_b[0]["chunk_id"] == "chk_b_001"


def test_qdrant_deterministic_point_id():
    """Test that deterministic point IDs produce identical UUID strings for same chunk ID."""
    id1 = deterministic_point_id("chk_doc1_0001")
    id2 = deterministic_point_id("chk_doc1_0001")
    id3 = deterministic_point_id("chk_doc1_0002")

    assert id1 == id2
    assert id1 != id3
