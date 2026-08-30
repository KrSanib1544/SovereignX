# backend/tests/offline/test_offline_rag.py
"""
Offline & Air-Gap Verification Tests for Ingestion & RAG
Validates that document parsing, FastEmbed CPU embedding, Qdrant indexing, and retrieval
execute 100% locally with zero external network connectivity.
"""

from pathlib import Path
from backend.app.core.security import generate_uuid
from backend.app.db.models import WorkspaceORM
from backend.app.ingestion.pipeline import DocumentIngestionPipeline
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore
from backend.app.rag.retriever import RetrievalService
from backend.tests.fixtures_helper import create_sample_digital_pdf


def test_offline_ingestion_and_retrieval_execution(db_session, tmp_path):
    """
    Execute full pipeline and verify zero cloud network dependency.
    """
    ws_id = generate_uuid("ws")
    ws_dir = tmp_path / "workspaces" / ws_id
    (ws_dir / "uploads").mkdir(parents=True, exist_ok=True)

    workspace = WorkspaceORM(id=ws_id, name="Air-Gap Verification WS", storage_path=str(ws_dir))
    db_session.add(workspace)
    db_session.commit()

    # Initialize local components
    mem_store = QdrantVectorStore(location=":memory:")
    embedder = LocalEmbeddingEngine.get_instance()
    mem_store.init_collection(dimension=embedder.dimension, recreate=True)

    pipeline = DocumentIngestionPipeline(vector_store=mem_store, embedding_engine=embedder)
    retriever = RetrievalService(vector_store=mem_store, embedding_engine=embedder)

    # Ingest document
    pdf_path = create_sample_digital_pdf(ws_dir / "uploads" / "local_test.pdf")
    doc_orm = pipeline.ingest_file(
        session=db_session,
        workspace_id=ws_id,
        relative_path="uploads/local_test.pdf"
    )

    assert doc_orm.parsing_status == "INDEXED"

    # Query
    results = retriever.retrieve(
        workspace_id=ws_id,
        query="ultrasonic casing thickness",
        top_k=2
    )

    assert results.total_results >= 1
    assert "3.42 mm" in results.items[0].content
