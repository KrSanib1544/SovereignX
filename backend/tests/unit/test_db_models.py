# backend/tests/unit/test_db_models.py
"""
Unit Tests for Core Database ORM Models
Validates creation, schema constraints, and queries for workspaces, documents, chunks, tasks, and artifacts.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.core.security import generate_uuid, utc_now
from backend.app.db.models import (
    WorkspaceORM,
    DocumentORM,
    DocumentChunkORM,
    TaskORM,
    TaskStepORM,
    ToolExecutionORM,
    ArtifactORM,
)


def test_workspace_creation(db_session):
    """Test creating and querying an isolated workspace entity."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Reflux Unit Inspection",
        description="Hydrocarbon reflux unit inspection package",
        classification_level="RESTRICTED_CONFIDENTIAL",
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    db_session.commit()

    queried = db_session.get(WorkspaceORM, ws_id)
    assert queried is not None
    assert queried.name == "Reflux Unit Inspection"
    assert queried.classification_level == "RESTRICTED_CONFIDENTIAL"
    assert queried.created_at is not None


def test_workspace_invalid_classification_constraint(db_session):
    """Test that check constraint rejects invalid classification levels."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Invalid Workspace",
        classification_level="INVALID_TOP_SECRET",  # Not in allowed list
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_document_and_chunk_creation(db_session):
    """Test creating a document and linked document chunks with provenance."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Turbine Workspace",
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    db_session.flush()

    # Create Document
    doc_id = generate_uuid("doc")
    doc = DocumentORM(
        id=doc_id,
        workspace_id=ws_id,
        filename="ultrasonic_ndt_report.pdf",
        filepath=f"./data/workspaces/{ws_id}/uploads/ultrasonic_ndt_report.pdf",
        mime_type="application/pdf",
        size_bytes=1048576,
        sha256_hash="a" * 64,
        page_count=8,
        ocr_applied=False,
        parsing_status="INDEXED"
    )
    db_session.add(doc)
    db_session.flush()

    # Create Chunk
    chk_id = generate_uuid("chk")
    chunk = DocumentChunkORM(
        id=chk_id,
        document_id=doc_id,
        workspace_id=ws_id,
        chunk_index=0,
        page_number=4,
        section_title="3.2 Shell Thickness Gauging",
        bbox_json="[45.0, 120.5, 480.0, 320.0]",
        content="Measured wall thickness at node C-12: 3.42mm (below minimum tolerance).",
        token_count=180,
        embedding_id="point_001"
    )
    db_session.add(chunk)
    db_session.commit()

    # Verify relationships
    retrieved_doc = db_session.get(DocumentORM, doc_id)
    assert retrieved_doc is not None
    assert len(retrieved_doc.chunks) == 1
    assert retrieved_doc.chunks[0].page_number == 4
    assert retrieved_doc.chunks[0].section_title == "3.2 Shell Thickness Gauging"
    assert retrieved_doc.chunks[0].workspace_id == ws_id


def test_task_step_and_artifact_creation(db_session):
    """Test creating an agent task with execution steps, tool calls, and generated artifacts."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Task Test Workspace",
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    db_session.flush()

    # Create Task
    task_id = generate_uuid("tsk")
    task = TaskORM(
        id=task_id,
        workspace_id=ws_id,
        prompt="Analyze inspection package and verify OEM tolerances.",
        status="EXECUTING",
        max_steps=15,
        current_step=1
    )
    db_session.add(task)
    db_session.flush()

    # Create Step
    step_id = generate_uuid("stp")
    step = TaskStepORM(
        id=step_id,
        task_id=task_id,
        step_number=1,
        thought_reasoning="Need to query knowledge base for thickness readings.",
        model_used="qwen3:4b",
        vram_used_mb=2560,
        execution_time_ms=850
    )
    db_session.add(step)
    db_session.flush()

    # Create Tool Execution
    tex_id = generate_uuid("tex")
    tool_exec = ToolExecutionORM(
        id=tex_id,
        step_id=step_id,
        task_id=task_id,
        tool_name="search_knowledge",
        risk_level="LOW",
        arguments_json='{"query": "Pump 3B wall thickness"}',
        output_json='{"results": [{"page": 4, "text": "3.42mm"}]}',
        status="SUCCESS",
        duration_ms=45
    )
    db_session.add(tool_exec)
    db_session.flush()

    # Create Artifact
    art_id = generate_uuid("art")
    artifact = ArtifactORM(
        id=art_id,
        task_id=task_id,
        workspace_id=ws_id,
        filename="Approval_Note_Pump3B.docx",
        filepath=f"./data/workspaces/{ws_id}/artifacts/Approval_Note_Pump3B.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=45200,
        sha256_hash="b" * 64
    )
    db_session.add(artifact)
    db_session.commit()

    # Verification
    retrieved_task = db_session.get(TaskORM, task_id)
    assert retrieved_task is not None
    assert len(retrieved_task.steps) == 1
    assert len(retrieved_task.tool_executions) == 1
    assert len(retrieved_task.artifacts) == 1
    assert retrieved_task.artifacts[0].filename == "Approval_Note_Pump3B.docx"
