# backend/tests/unit/test_foreign_keys_and_transactions.py
"""
Unit Tests for Foreign Key Constraints, Cascade Deletions, and Transaction Rollbacks
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.app.core.security import generate_uuid
from backend.app.db.models import (
    WorkspaceORM,
    DocumentORM,
    DocumentChunkORM,
    TaskORM,
    TaskStepORM,
    ToolExecutionORM,
    ArtifactORM,
)


def test_foreign_key_violation_raises_error(db_session):
    """Test that inserting an entity with a non-existent foreign key fails."""
    non_existent_ws_id = "ws_nonexistent_999"
    doc = DocumentORM(
        id=generate_uuid("doc"),
        workspace_id=non_existent_ws_id,  # Invalid FK
        filename="unanchored_file.pdf",
        filepath="/tmp/unanchored_file.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        sha256_hash="0" * 64,
        parsing_status="PENDING"
    )
    db_session.add(doc)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_workspace(db_session):
    """Test that deleting a workspace cascades and removes all dependent documents, chunks, tasks, and artifacts."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Workspace To Delete",
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    db_session.flush()

    # Add Document & Chunk
    doc_id = generate_uuid("doc")
    doc = DocumentORM(
        id=doc_id,
        workspace_id=ws_id,
        filename="report.pdf",
        filepath=f"./data/workspaces/{ws_id}/report.pdf",
        mime_type="application/pdf",
        size_bytes=500,
        sha256_hash="c" * 64,
        parsing_status="INDEXED"
    )
    db_session.add(doc)
    db_session.flush()

    chk_id = generate_uuid("chk")
    chunk = DocumentChunkORM(
        id=chk_id,
        document_id=doc_id,
        workspace_id=ws_id,
        chunk_index=0,
        content="Chunk sample content",
        token_count=10
    )
    db_session.add(chunk)

    # Add Task, Step, Tool Exec, Artifact
    task_id = generate_uuid("tsk")
    task = TaskORM(id=task_id, workspace_id=ws_id, prompt="Test prompt", status="COMPLETED")
    db_session.add(task)
    db_session.flush()

    step_id = generate_uuid("stp")
    step = TaskStepORM(id=step_id, task_id=task_id, step_number=1, model_used="qwen3:4b")
    db_session.add(step)
    db_session.flush()

    tex_id = generate_uuid("tex")
    tool_exec = ToolExecutionORM(
        id=tex_id,
        step_id=step_id,
        task_id=task_id,
        tool_name="read_file",
        risk_level="LOW",
        arguments_json="{}",
        status="SUCCESS"
    )
    db_session.add(tool_exec)

    art_id = generate_uuid("art")
    artifact = ArtifactORM(
        id=art_id,
        task_id=task_id,
        workspace_id=ws_id,
        filename="output.docx",
        filepath=f"./data/workspaces/{ws_id}/output.docx",
        mime_type="application/docx",
        size_bytes=1000,
        sha256_hash="d" * 64
    )
    db_session.add(artifact)
    db_session.commit()

    # Delete Workspace
    ws_to_delete = db_session.get(WorkspaceORM, ws_id)
    db_session.delete(ws_to_delete)
    db_session.commit()

    # Expire session identity map to force refetching directly from SQLite
    db_session.expire_all()

    # Assert that all dependent records were cascade deleted in database
    assert db_session.get(WorkspaceORM, ws_id) is None
    assert db_session.get(DocumentORM, doc_id) is None
    assert db_session.get(DocumentChunkORM, chk_id) is None
    assert db_session.get(TaskORM, task_id) is None
    assert db_session.get(TaskStepORM, step_id) is None
    assert db_session.get(ToolExecutionORM, tex_id) is None
    assert db_session.get(ArtifactORM, art_id) is None


def test_transaction_rollback_behavior(db_session):
    """Test that an error inside a multi-write transaction rolls back cleanly without partial writes."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(
        id=ws_id,
        name="Rollback Test Workspace",
        storage_path=f"./data/workspaces/{ws_id}"
    )
    db_session.add(workspace)
    db_session.commit()

    try:
        # Step 1: Valid insert
        doc1 = DocumentORM(
            id=generate_uuid("doc"),
            workspace_id=ws_id,
            filename="valid_file.pdf",
            filepath="/tmp/valid_file.pdf",
            mime_type="application/pdf",
            size_bytes=200,
            sha256_hash="e" * 64,
            parsing_status="INDEXED"
        )
        db_session.add(doc1)

        # Step 2: Invalid insert (violating NOT NULL / Check Constraint)
        doc2 = DocumentORM(
            id=generate_uuid("doc"),
            workspace_id=ws_id,
            filename="invalid_file.pdf",
            filepath="/tmp/invalid_file.pdf",
            mime_type="application/pdf",
            size_bytes=200,
            sha256_hash="f" * 64,
            parsing_status="ILLEGAL_STATUS"  # Violates check constraint
        )
        db_session.add(doc2)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()

    # Verify that doc1 was rolled back and is NOT present in the database
    docs = db_session.execute(
        select(DocumentORM).where(DocumentORM.workspace_id == ws_id)
    ).scalars().all()
    assert len(docs) == 0, "Partial transaction write was not rolled back."
