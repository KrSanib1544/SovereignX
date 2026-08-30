# backend/app/ingestion/pipeline.py
"""
Master Document Ingestion Pipeline Coordinator
Unifies validation, parsing (PDF, OCR, XLSX, CSV, TXT), hierarchical chunking,
local CPU embedding, Qdrant indexing, SQLite provenance persistence, and cryptographic auditing.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.audit_logger import AuditLogger
from backend.app.core.security import generate_uuid, resolve_secure_workspace_path
from backend.app.db.models import WorkspaceORM, DocumentORM, DocumentChunkORM
from backend.app.ingestion.models import ParsedDocument, SourceType
from backend.app.ingestion.validator import DocumentValidator, DocumentValidationResult
from backend.app.ingestion.pdf_parser import PDFParser
from backend.app.ingestion.excel_parser import ExcelParser
from backend.app.ingestion.text_parser import TextAndCSVParser
from backend.app.rag.chunking import HierarchicalChunker
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.provenance import ChunkProvenance
from backend.app.rag.vector_store import QdrantVectorStore


class DocumentIngestionPipeline:
    """
    Coordinates the full end-to-end local document ingestion lifecycle.
    """

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_engine: Optional[LocalEmbeddingEngine] = None
    ):
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_engine = embedding_engine or LocalEmbeddingEngine.get_instance()
        # Ensure Qdrant collection is initialized
        self.vector_store.init_collection(dimension=self.embedding_engine.dimension)

    def ingest_file(
        self,
        session: Session,
        workspace_id: str,
        relative_path: str,
        classification: Optional[str] = None,
        enable_ocr: bool = True
    ) -> DocumentORM:
        """
        Validate, parse, chunk, embed, index into Qdrant, and persist to SQLite.
        """
        workspace = session.get(WorkspaceORM, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace '{workspace_id}' does not exist.")

        workspace_dir = Path(workspace.storage_path)
        classification_level = classification or workspace.classification_level

        # 1. Validation
        validation: DocumentValidationResult = DocumentValidator.validate(
            workspace_dir=workspace_dir,
            relative_path=relative_path
        )
        resolved_file = Path(validation.resolved_path)

        # 2. Check for existing document or create new DocumentORM record
        existing_doc = session.query(DocumentORM).filter_by(
            workspace_id=workspace_id,
            filename=validation.filename
        ).first()

        if existing_doc:
            doc_id = existing_doc.id
            doc_orm = existing_doc
            doc_orm.size_bytes = validation.size_bytes
            doc_orm.sha256_hash = validation.sha256_hash
            doc_orm.parsing_status = "PARSING"
            doc_orm.error_message = None
            # Clean old Qdrant chunks for idempotent re-indexing
            self.vector_store.delete_document_chunks(doc_id)
            # Remove old DB chunks
            session.query(DocumentChunkORM).filter_by(document_id=doc_id).delete()
        else:
            doc_id = generate_uuid("doc")
            doc_orm = DocumentORM(
                id=doc_id,
                workspace_id=workspace_id,
                filename=validation.filename,
                filepath=str(resolved_file),
                mime_type=validation.mime_type,
                size_bytes=validation.size_bytes,
                sha256_hash=validation.sha256_hash,
                parsing_status="PARSING"
            )
            session.add(doc_orm)

        session.flush()

        try:
            # 3. Parse Document into Normalized Representation
            ext = validation.extension.lower()
            if ext == ".pdf":
                parsed_doc: ParsedDocument = PDFParser.parse(
                    filepath=resolved_file,
                    enable_ocr=enable_ocr,
                    filename_override=validation.filename
                )
            elif ext in (".xlsx", ".xls"):
                parsed_doc = ExcelParser.parse(
                    filepath=resolved_file,
                    filename_override=validation.filename
                )
            elif ext == ".csv":
                parsed_doc = TextAndCSVParser.parse_csv(
                    filepath=resolved_file,
                    filename_override=validation.filename
                )
            elif ext == ".txt":
                parsed_doc = TextAndCSVParser.parse_txt(
                    filepath=resolved_file,
                    filename_override=validation.filename
                )
            else:
                raise ValueError(f"No parser available for format '{ext}'")

            parsed_doc.sha256_hash = validation.sha256_hash

            # 4. Hierarchical Chunking
            chunks: List[ChunkProvenance] = HierarchicalChunker.chunk_document(
                parsed_doc=parsed_doc,
                document_id=doc_id,
                workspace_id=workspace_id,
                classification=classification_level
            )

            # 5. Local CPU Embeddings
            chunk_texts = [c.content for c in chunks]
            vectors: List[List[float]] = self.embedding_engine.embed_documents(chunk_texts)

            # 6. Index into Qdrant
            self.vector_store.upsert_chunks(chunks=chunks, vectors=vectors)

            # 7. Persist Chunks into SQLite
            for chunk in chunks:
                chunk_orm = DocumentChunkORM(
                    id=chunk.chunk_id,
                    document_id=doc_id,
                    workspace_id=workspace_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    bbox_json=json.dumps(chunk.bbox) if chunk.bbox else None,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding_id=chunk.chunk_id
                )
                session.add(chunk_orm)

            # 8. Update Document State
            doc_orm.page_count = parsed_doc.page_count
            doc_orm.ocr_applied = parsed_doc.ocr_applied
            doc_orm.parsing_status = "INDEXED"
            doc_orm.error_message = None

            # 9. Cryptographic Audit Event
            AuditLogger.record_event(
                session=session,
                event_type="INGEST_SUCCESS",
                payload={
                    "document_id": doc_id,
                    "filename": validation.filename,
                    "chunks_indexed": len(chunks),
                    "pages": parsed_doc.page_count,
                    "ocr_applied": parsed_doc.ocr_applied,
                    "sha256": validation.sha256_hash
                },
                workspace_id=workspace_id,
                actor="INGESTION_ENGINE"
            )

            session.commit()
            return doc_orm

        except Exception as e:
            session.rollback()
            # Record failed state in new transaction
            doc_orm.parsing_status = "FAILED"
            doc_orm.error_message = str(e)
            session.add(doc_orm)
            AuditLogger.record_event(
                session=session,
                event_type="INGEST_FAILED",
                payload={
                    "document_id": doc_id,
                    "filename": validation.filename,
                    "error": str(e)
                },
                workspace_id=workspace_id,
                actor="INGESTION_ENGINE"
            )
            session.commit()
            raise
