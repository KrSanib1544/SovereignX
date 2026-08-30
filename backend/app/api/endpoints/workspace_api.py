# backend/app/api/endpoints/workspace_api.py
"""
Workspaces, Document Ingestion & Artifacts REST Endpoints
Provides full lifecycle management for isolated local workspaces, multipart document ingestion,
vector similarity search exploration, and artifact downloads.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.audit_logger import AuditLogger
from backend.app.core.security import generate_uuid, resolve_secure_workspace_path
from backend.app.db.models.document_orm import DocumentORM, DocumentChunkORM
from backend.app.db.models.task_orm import TaskORM, ArtifactORM
from backend.app.db.models.workspace_orm import WorkspaceORM
from backend.app.db.session import get_db_session
from backend.app.ingestion.pipeline import DocumentIngestionPipeline
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore

router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Workspace display name")
    description: Optional[str] = Field(None, description="Optional description")
    classification_level: str = Field(
        "INTERNAL_ENGINEERING",
        description="Data classification: 'PUBLIC', 'INTERNAL_ENGINEERING', or 'RESTRICTED_CONFIDENTIAL'"
    )


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    classification_level: str
    storage_path: str
    document_count: int = 0
    task_count: int = 0
    created_at: str
    updated_at: str


class DocumentSummary(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    page_count: int
    chunk_count: int
    ocr_applied: bool
    parsing_status: str
    created_at: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Semantic search query")
    top_k: int = Field(4, ge=1, le=10, description="Max results to retrieve")
    document_id: Optional[str] = Field(None, description="Optional document UUID filter")


class QueryResultItem(BaseModel):
    chunk_id: str
    score: float
    content: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    classification: Optional[str] = None


@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(db: Session = Depends(get_db_session)):
    """
    List all local workspaces with summary document and task counts.
    """
    workspaces = db.query(WorkspaceORM).order_by(WorkspaceORM.created_at.desc()).all()
    results = []
    for ws in workspaces:
        doc_count = db.query(DocumentORM).filter(DocumentORM.workspace_id == ws.id).count()
        task_count = db.query(TaskORM).filter(TaskORM.workspace_id == ws.id).count()
        results.append(WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            description=ws.description,
            classification_level=ws.classification_level,
            storage_path=ws.storage_path,
            document_count=doc_count,
            task_count=task_count,
            created_at=ws.created_at.isoformat() if ws.created_at else "",
            updated_at=ws.updated_at.isoformat() if ws.updated_at else ""
        ))
    return results


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(req: CreateWorkspaceRequest, db: Session = Depends(get_db_session)):
    """
    Create a new isolated local workspace sandbox folder and SQLite record.
    """
    if req.classification_level not in ('PUBLIC', 'INTERNAL_ENGINEERING', 'RESTRICTED_CONFIDENTIAL'):
        raise HTTPException(
            status_code=400,
            detail="Invalid classification_level. Must be 'PUBLIC', 'INTERNAL_ENGINEERING', or 'RESTRICTED_CONFIDENTIAL'."
        )

    ws_id = f"ws_{uuid.uuid4().hex[:8]}"
    ws_dir = (settings.WORKSPACES_DIR / ws_id).resolve()
    ws_dir.mkdir(parents=True, exist_ok=True)
    (ws_dir / "documents").mkdir(exist_ok=True)
    (ws_dir / "artifacts").mkdir(exist_ok=True)
    (ws_dir / "scratch").mkdir(exist_ok=True)

    now = datetime.now(timezone.utc)
    ws = WorkspaceORM(
        id=ws_id,
        name=req.name,
        description=req.description,
        classification_level=req.classification_level,
        storage_path=str(ws_dir),
        created_at=now,
        updated_at=now
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)

    AuditLogger.record_event(
        session=db,
        workspace_id=ws_id,
        event_type="WORKSPACE_CREATED",
        payload={"name": req.name, "classification": req.classification_level}
    )

    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        classification_level=ws.classification_level,
        storage_path=ws.storage_path,
        document_count=0,
        task_count=0,
        created_at=ws.created_at.isoformat(),
        updated_at=ws.updated_at.isoformat()
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, db: Session = Depends(get_db_session)):
    """
    Retrieve single workspace details.
    """
    ws = db.query(WorkspaceORM).filter(WorkspaceORM.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    doc_count = db.query(DocumentORM).filter(DocumentORM.workspace_id == ws.id).count()
    task_count = db.query(TaskORM).filter(TaskORM.workspace_id == ws.id).count()

    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        classification_level=ws.classification_level,
        storage_path=ws.storage_path,
        document_count=doc_count,
        task_count=task_count,
        created_at=ws.created_at.isoformat() if ws.created_at else "",
        updated_at=ws.updated_at.isoformat() if ws.updated_at else ""
    )


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_200_OK)
async def delete_workspace(workspace_id: str, db: Session = Depends(get_db_session)):
    """
    Wipe workspace, delete vector collection points, and remove local filesystem directory.
    """
    ws = db.query(WorkspaceORM).filter(WorkspaceORM.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Wipe Qdrant vectors
    try:
        store = QdrantVectorStore()
        store.delete_workspace_chunks(workspace_id)
    except Exception:
        pass

    # Delete filesystem folder
    ws_dir = Path(ws.storage_path)
    if ws_dir.exists():
        try:
            shutil.rmtree(ws_dir)
        except Exception:
            pass

    db.delete(ws)
    db.commit()

    return {"status": "DELETED", "workspace_id": workspace_id}


@router.post("/workspaces/{workspace_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_documents(
    workspace_id: str,
    files: List[UploadFile] = File(...),
    classification: Optional[str] = Form(None),
    enable_ocr: bool = Form(True),
    db: Session = Depends(get_db_session)
):
    """
    Multi-part upload documents and run offline ingestion pipeline into Qdrant & SQLite.
    """
    ws = db.query(WorkspaceORM).filter(WorkspaceORM.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    pipeline = DocumentIngestionPipeline()
    ingested_docs = []

    ws_docs_dir = Path(ws.storage_path) / "documents"
    ws_docs_dir.mkdir(parents=True, exist_ok=True)

    for upload_file in files:
        safe_filename = Path(upload_file.filename).name
        target_path = ws_docs_dir / safe_filename
        
        # Save file to disk
        content = await upload_file.read()
        with open(target_path, "wb") as f:
            f.write(content)

        relative_path = f"documents/{safe_filename}"

        try:
            doc_orm = pipeline.ingest_file(
                session=db,
                workspace_id=workspace_id,
                relative_path=relative_path,
                classification=classification or ws.classification_level,
                enable_ocr=enable_ocr
            )
            ingested_docs.append({
                "id": doc_orm.id,
                "filename": doc_orm.filename,
                "size_bytes": doc_orm.size_bytes,
                "mime_type": doc_orm.mime_type,
                "page_count": doc_orm.page_count,
                "ocr_applied": doc_orm.ocr_applied,
                "parsing_status": doc_orm.parsing_status,
                "sha256_hash": doc_orm.sha256_hash
            })
        except Exception as e:
            # Still record file even if ingestion failed
            ingested_docs.append({
                "filename": safe_filename,
                "status": "FAILED",
                "error": str(e)
            })

    return {
        "workspace_id": workspace_id,
        "ingested_count": len(ingested_docs),
        "documents": ingested_docs
    }


@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentSummary])
async def list_documents(workspace_id: str, db: Session = Depends(get_db_session)):
    """
    List all ingested documents in the workspace.
    """
    docs = db.query(DocumentORM).filter(DocumentORM.workspace_id == workspace_id).order_by(DocumentORM.created_at.desc()).all()
    results = []
    for d in docs:
        chunk_count = db.query(DocumentChunkORM).filter(DocumentChunkORM.document_id == d.id).count()
        results.append(DocumentSummary(
            id=d.id,
            filename=d.filename,
            mime_type=d.mime_type,
            size_bytes=d.size_bytes,
            sha256_hash=d.sha256_hash,
            page_count=d.page_count,
            chunk_count=chunk_count,
            ocr_applied=d.ocr_applied,
            parsing_status=d.parsing_status,
            created_at=d.created_at.isoformat() if d.created_at else ""
        ))
    return results


@router.get("/workspaces/{workspace_id}/documents/{document_id}")
async def get_document(workspace_id: str, document_id: str, db: Session = Depends(get_db_session)):
    """
    Retrieve document details and its extracted chunks.
    """
    doc = db.query(DocumentORM).filter(
        DocumentORM.id == document_id,
        DocumentORM.workspace_id == workspace_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(DocumentChunkORM).filter(
        DocumentChunkORM.document_id == document_id
    ).order_by(DocumentChunkORM.chunk_index.asc()).all()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size_bytes": doc.size_bytes,
        "sha256_hash": doc.sha256_hash,
        "page_count": doc.page_count,
        "ocr_applied": doc.ocr_applied,
        "parsing_status": doc.parsing_status,
        "chunks": [
            {
                "chunk_id": c.id,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "token_count": c.token_count,
                "bbox_json": c.bbox_json,
                "content_preview": c.content[:200]
            }
            for c in chunks
        ]
    }


@router.post("/workspaces/{workspace_id}/query", response_model=List[QueryResultItem])
async def query_knowledge_vault(
    workspace_id: str,
    req: QueryRequest,
    db: Session = Depends(get_db_session)
):
    """
    Execute semantic similarity query directly against local Qdrant vectors.
    """
    ws = db.query(WorkspaceORM).filter(WorkspaceORM.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    embedder = LocalEmbeddingEngine.get_instance()
    query_vector = embedder.embed_query(req.query)

    store = QdrantVectorStore()
    raw_hits = store.search(
        query_vector=query_vector,
        workspace_id=workspace_id,
        top_k=req.top_k,
        filter_document_id=req.document_id
    )

    results = []
    for hit in raw_hits:
        results.append(QueryResultItem(
            chunk_id=hit.get("chunk_id", ""),
            score=hit.get("score", 0.0),
            content=hit.get("content", ""),
            document_id=hit.get("document_id", ""),
            filename=hit.get("filename", ""),
            page_number=hit.get("page_number"),
            section_title=hit.get("section_title"),
            classification=hit.get("classification")
        ))
    return results


@router.get("/workspaces/{workspace_id}/artifacts/{filename}")
async def download_artifact(
    workspace_id: str,
    filename: str,
    db: Session = Depends(get_db_session)
):
    """
    Download a generated artifact (.docx, .csv, chart) strictly from the workspace artifacts jail.
    """
    try:
        file_path = resolve_secure_workspace_path(workspace_id, f"artifacts/{filename}")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Access denied: {str(e)}")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact '{filename}' not found.")

    media_type = "application/octet-stream"
    if filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )
