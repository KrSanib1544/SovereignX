# backend/tests/unit/test_workspace_isolation.py
"""
Unit Tests for Strict Workspace Isolation & Path Containment
Ensures multi-workspace tenancy bounds are mathematically separated.
"""

from pathlib import Path
import pytest
from sqlalchemy import select
from backend.app.core.security import (
    generate_uuid,
    resolve_secure_workspace_path,
    SecurityPolicyViolationError,
)
from backend.app.db.models import WorkspaceORM, DocumentORM, DocumentChunkORM


def test_workspace_query_isolation(db_session):
    """Test that queries scoped to Workspace A never retrieve data from Workspace B."""
    ws_a_id = generate_uuid("ws")
    ws_b_id = generate_uuid("ws")

    ws_a = WorkspaceORM(id=ws_a_id, name="Project Alpha (Defense)", storage_path=f"./data/{ws_a_id}")
    ws_b = WorkspaceORM(id=ws_b_id, name="Project Beta (Commercial)", storage_path=f"./data/{ws_b_id}")
    db_session.add_all([ws_a, ws_b])
    db_session.flush()

    # Ingest document into Workspace A
    doc_a = DocumentORM(
        id=generate_uuid("doc"),
        workspace_id=ws_a_id,
        filename="classified_blueprint.pdf",
        filepath=f"./data/{ws_a_id}/classified_blueprint.pdf",
        mime_type="application/pdf",
        size_bytes=4000,
        sha256_hash="1" * 64,
        parsing_status="INDEXED"
    )
    # Ingest document into Workspace B
    doc_b = DocumentORM(
        id=generate_uuid("doc"),
        workspace_id=ws_b_id,
        filename="public_catalog.pdf",
        filepath=f"./data/{ws_b_id}/public_catalog.pdf",
        mime_type="application/pdf",
        size_bytes=2000,
        sha256_hash="2" * 64,
        parsing_status="INDEXED"
    )
    db_session.add_all([doc_a, doc_b])
    db_session.commit()

    # Query strictly for Workspace A
    results_a = db_session.execute(
        select(DocumentORM).where(DocumentORM.workspace_id == ws_a_id)
    ).scalars().all()

    assert len(results_a) == 1
    assert results_a[0].filename == "classified_blueprint.pdf"
    assert all(d.workspace_id == ws_a_id for d in results_a)

    # Query strictly for Workspace B
    results_b = db_session.execute(
        select(DocumentORM).where(DocumentORM.workspace_id == ws_b_id)
    ).scalars().all()

    assert len(results_b) == 1
    assert results_b[0].filename == "public_catalog.pdf"
    assert all(d.workspace_id == ws_b_id for d in results_b)


def test_secure_workspace_path_containment(tmp_path):
    """Test that path resolution strictly jails operations within the target workspace directory."""
    workspace_root = tmp_path / "workspaces" / "ws_test_123"
    workspace_root.mkdir(parents=True, exist_ok=True)

    # Valid relative paths
    valid_path = resolve_secure_workspace_path(workspace_root, "uploads/inspection.pdf")
    assert valid_path == (workspace_root / "uploads" / "inspection.pdf").resolve()

    # Dangerous path traversal attacks
    traversal_payloads = [
        "../../Windows/System32/cmd.exe",
        "/etc/shadow",
        "..\\..\\sovereign.db",
        "uploads/../../secret.txt",
        "....//....//config.json"
    ]

    for payload in traversal_payloads:
        with pytest.raises(SecurityPolicyViolationError):
            resolve_secure_workspace_path(workspace_root, payload)
