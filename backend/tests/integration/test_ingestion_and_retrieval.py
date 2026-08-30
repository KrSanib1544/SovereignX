# backend/tests/integration/test_ingestion_and_retrieval.py
"""
End-to-End Integration Tests for Document Ingestion & Local Vector Retrieval
Validates the full chain: Validation -> Parsing -> Chunking -> FastEmbed -> Qdrant -> Authorized Retrieval -> Provenance
"""

from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.core.security import generate_uuid
from backend.app.db.models import WorkspaceORM, DocumentORM, DocumentChunkORM
from backend.app.ingestion.pipeline import DocumentIngestionPipeline
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore
from backend.app.rag.retriever import RetrievalService
from backend.tests.fixtures_helper import (
    create_sample_digital_pdf,
    create_sample_xlsx,
    create_sample_csv,
)


def test_end_to_end_ingestion_and_retrieval(db_session: Session, tmp_path: Path):
    """
    Test complete lifecycle: Ingest PDF + XLSX into workspace, query semantic retrieval,
    and assert exact page-level provenance.
    """
    # 1. Setup Workspace and In-Memory Vector Store
    ws_id = generate_uuid("ws")
    ws_dir = tmp_path / "workspaces" / ws_id
    (ws_dir / "uploads").mkdir(parents=True, exist_ok=True)

    workspace = WorkspaceORM(
        id=ws_id,
        name="Reflux Inspection Package Workspace",
        classification_level="INTERNAL_ENGINEERING",
        storage_path=str(ws_dir)
    )
    db_session.add(workspace)
    db_session.commit()

    # Use in-memory Qdrant for fast isolated integration testing
    mem_vector_store = QdrantVectorStore(location=":memory:")
    embedder = LocalEmbeddingEngine.get_instance()
    mem_vector_store.init_collection(dimension=embedder.dimension, recreate=True)

    pipeline = DocumentIngestionPipeline(
        vector_store=mem_vector_store,
        embedding_engine=embedder
    )
    retriever = RetrievalService(
        vector_store=mem_vector_store,
        embedding_engine=embedder
    )

    # 2. Ingest Digital PDF
    pdf_path = create_sample_digital_pdf(ws_dir / "uploads" / "inspection_report.pdf")
    doc_orm = pipeline.ingest_file(
        session=db_session,
        workspace_id=ws_id,
        relative_path="uploads/inspection_report.pdf",
        classification="RESTRICTED_CONFIDENTIAL"
    )

    assert doc_orm.parsing_status == "INDEXED"
    assert doc_orm.page_count == 2
    assert len(doc_orm.chunks) >= 2

    # 3. Ingest Excel Workbook
    xlsx_path = create_sample_xlsx(ws_dir / "uploads" / "maintenance_history.xlsx")
    xlsx_orm = pipeline.ingest_file(
        session=db_session,
        workspace_id=ws_id,
        relative_path="uploads/maintenance_history.xlsx",
        classification="INTERNAL_ENGINEERING"
    )

    assert xlsx_orm.parsing_status == "INDEXED"
    assert xlsx_orm.page_count == 2

    # 4. Test Semantic Retrieval on Thickness Findings
    query = "What is the measured ultrasonic wall thickness at node C-12?"
    response = retriever.retrieve(
        workspace_id=ws_id,
        query=query,
        allowed_classifications=["RESTRICTED_CONFIDENTIAL", "INTERNAL_ENGINEERING"],
        top_k=3
    )

    assert response.total_results >= 1
    top_hit = response.items[0]
    assert "3.42 mm" in top_hit.content
    assert top_hit.filename == "inspection_report.pdf"
    assert top_hit.page_number == 2
    assert top_hit.section_title and "Section 3.2" in top_hit.section_title
    assert top_hit.bbox is not None
    assert len(top_hit.bbox) == 4

    # 5. Test Semantic Retrieval on OEM Replacement Thresholds (XLSX)
    query_oem = "minimum allowable shell thickness before mandatory replacement"
    response_oem = retriever.retrieve(
        workspace_id=ws_id,
        query=query_oem,
        allowed_classifications=["INTERNAL_ENGINEERING"],
        top_k=2
    )

    assert response_oem.total_results >= 1
    assert any("MANDATORY_REPLACEMENT" in hit.content for hit in response_oem.items)


def test_unauthorized_classification_blocked_at_retrieval(db_session: Session, tmp_path: Path):
    """
    Test that chunks with higher classification are never returned to a query
    with restricted access scope (Pre-retrieval authorization).
    """
    ws_id = generate_uuid("ws")
    ws_dir = tmp_path / "workspaces" / ws_id
    (ws_dir / "uploads").mkdir(parents=True, exist_ok=True)

    workspace = WorkspaceORM(
        id=ws_id,
        name="Security Gate Workspace",
        classification_level="RESTRICTED_CONFIDENTIAL",
        storage_path=str(ws_dir)
    )
    db_session.add(workspace)
    db_session.commit()

    mem_vector_store = QdrantVectorStore(location=":memory:")
    embedder = LocalEmbeddingEngine.get_instance()
    mem_vector_store.init_collection(dimension=embedder.dimension, recreate=True)

    pipeline = DocumentIngestionPipeline(vector_store=mem_vector_store, embedding_engine=embedder)
    retriever = RetrievalService(vector_store=mem_vector_store, embedding_engine=embedder)

    create_sample_digital_pdf(ws_dir / "uploads" / "classified_doc.pdf")
    pipeline.ingest_file(
        session=db_session,
        workspace_id=ws_id,
        relative_path="uploads/classified_doc.pdf",
        classification="RESTRICTED_CONFIDENTIAL"
    )

    # Operator only has PUBLIC access -> Should get 0 results
    response_blocked = retriever.retrieve(
        workspace_id=ws_id,
        query="ultrasonic wall thickness",
        allowed_classifications=["PUBLIC"],
        top_k=5
    )
    assert response_blocked.total_results == 0

    # Operator has RESTRICTED_CONFIDENTIAL access -> Should get results
    response_allowed = retriever.retrieve(
        workspace_id=ws_id,
        query="ultrasonic wall thickness",
        allowed_classifications=["RESTRICTED_CONFIDENTIAL"],
        top_k=5
    )
    assert response_allowed.total_results >= 1


def test_idempotent_reindexing(db_session: Session, tmp_path: Path):
    """
    Test that re-indexing the same file updates the record without creating duplicate vectors or chunks.
    """
    ws_id = generate_uuid("ws")
    ws_dir = tmp_path / "workspaces" / ws_id
    (ws_dir / "uploads").mkdir(parents=True, exist_ok=True)

    workspace = WorkspaceORM(id=ws_id, name="Idempotency Workspace", storage_path=str(ws_dir))
    db_session.add(workspace)
    db_session.commit()

    mem_vector_store = QdrantVectorStore(location=":memory:")
    embedder = LocalEmbeddingEngine.get_instance()
    mem_vector_store.init_collection(dimension=embedder.dimension, recreate=True)

    pipeline = DocumentIngestionPipeline(vector_store=mem_vector_store, embedding_engine=embedder)

    pdf_file = ws_dir / "uploads" / "test_reindex.pdf"
    create_sample_digital_pdf(pdf_file)

    # Ingestion 1
    doc1 = pipeline.ingest_file(db_session, ws_id, "uploads/test_reindex.pdf")
    initial_doc_id = doc1.id
    initial_chunks = db_session.query(DocumentChunkORM).filter_by(document_id=initial_doc_id).count()

    # Ingestion 2 (Re-indexing same file)
    doc2 = pipeline.ingest_file(db_session, ws_id, "uploads/test_reindex.pdf")
    reindexed_chunks = db_session.query(DocumentChunkORM).filter_by(document_id=initial_doc_id).count()

    assert doc1.id == doc2.id
    assert initial_chunks == reindexed_chunks
    assert db_session.query(DocumentORM).filter_by(workspace_id=ws_id).count() == 1
