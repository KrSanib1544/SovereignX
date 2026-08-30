# backend/tests/unit/test_audit_hashchain.py
"""
Unit Tests for Cryptographic Audit Hash-Chaining & Tamper Detection
Mathematically verifies SHA-256 chain continuity and tamper detection.
"""

from datetime import datetime, timezone
from sqlalchemy import select, delete
from backend.app.core.audit_logger import AuditLogger, GENESIS_HASH
from backend.app.core.security import generate_uuid
from backend.app.db.models import WorkspaceORM, AuditEventORM


def test_audit_hashchain_creation_and_continuity(db_session):
    """Test creating sequential audit events and verifying the unbroken SHA-256 chain."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(id=ws_id, name="Audit Workspace", storage_path=f"./data/{ws_id}")
    db_session.add(workspace)
    db_session.commit()

    # Record 5 sequential audit events
    events_data = [
        ("INGEST", {"filename": "inspection_report.pdf", "size_bytes": 1048576}),
        ("OCR_EXTRACT", {"page": 1, "words_detected": 420}),
        ("TOOL_EXEC", {"tool": "search_knowledge", "query": "Pump 3B wall thickness"}),
        ("APPROVAL", {"action": "run_python_sandbox", "status": "APPROVED"}),
        ("ARTIFACT_GEN", {"artifact": "Approval_Note.docx", "sha256": "3" * 64}),
    ]

    for event_type, payload in events_data:
        AuditLogger.record_event(
            session=db_session,
            event_type=event_type,
            payload=payload,
            workspace_id=ws_id,
            actor="SYSTEM_AGENT"
        )
    db_session.commit()

    # Verify chain integrity
    result = AuditLogger.verify_chain(session=db_session)
    assert result.is_valid is True
    assert result.verified_count == 5
    assert result.error_reason is None

    # Inspect the raw DB records
    records = db_session.execute(
        select(AuditEventORM).order_by(AuditEventORM.id.asc())
    ).scalars().all()

    assert len(records) == 5
    assert records[0].previous_hash == GENESIS_HASH
    for i in range(1, len(records)):
        assert records[i].previous_hash == records[i - 1].current_hash


def test_tamper_detection_modified_payload(db_session):
    """Test that modifying a single character in an audit record payload is immediately detected."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(id=ws_id, name="Tamper Test WS", storage_path=f"./data/{ws_id}")
    db_session.add(workspace)
    db_session.commit()

    # Record 3 events
    events = []
    for i in range(3):
        evt = AuditLogger.record_event(
            session=db_session,
            event_type="TOOL_EXEC",
            payload={"step": i, "command": f"action_{i}"},
            workspace_id=ws_id
        )
        events.append(evt)
    db_session.commit()

    target_event_id = events[1].id

    # Tamper with event 2 in the database
    target_event = db_session.execute(
        select(AuditEventORM).where(AuditEventORM.id == target_event_id)
    ).scalar_one()

    # Modify payload without recalculating current_hash
    target_event.payload_json = '{"command":"MALICIOUS_TAMPERED_ACTION","step":1}'
    db_session.commit()

    # Run verification
    result = AuditLogger.verify_chain(session=db_session)
    assert result.is_valid is False
    assert result.failed_event_id == target_event_id
    assert "PAYLOAD_TAMPERING" in result.error_reason


def test_tamper_detection_deleted_middle_record(db_session):
    """Test that deleting an audit event from the sequence breaks the chain."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(id=ws_id, name="Delete Test WS", storage_path=f"./data/{ws_id}")
    db_session.add(workspace)
    db_session.commit()

    events = []
    for i in range(4):
        evt = AuditLogger.record_event(
            session=db_session,
            event_type="STEP_EXEC",
            payload={"step": i},
            workspace_id=ws_id
        )
        events.append(evt)
    db_session.commit()

    deleted_id = events[1].id
    next_id = events[2].id

    # Delete record #2 (events[1])
    db_session.execute(delete(AuditEventORM).where(AuditEventORM.id == deleted_id))
    db_session.commit()

    # Run verification
    result = AuditLogger.verify_chain(session=db_session)
    assert result.is_valid is False
    # Next record directly follows #1, so its previous_hash won't match
    assert result.failed_event_id == next_id
    assert "BROKEN_CHAIN_LINK" in result.error_reason


def test_tamper_detection_modified_timestamp(db_session):
    """Test that backdating or altering an event timestamp is detected as tampering."""
    ws_id = generate_uuid("ws")
    workspace = WorkspaceORM(id=ws_id, name="Timestamp Test WS", storage_path=f"./data/{ws_id}")
    db_session.add(workspace)
    db_session.commit()

    evt = AuditLogger.record_event(
        session=db_session,
        event_type="LOGIN",
        payload={"user": "operator_1"},
        workspace_id=ws_id
    )
    db_session.commit()
    target_id = evt.id

    # Alter timestamp directly
    event = db_session.execute(select(AuditEventORM).where(AuditEventORM.id == target_id)).scalar_one()
    event.timestamp = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    db_session.commit()

    result = AuditLogger.verify_chain(session=db_session)
    assert result.is_valid is False
    assert result.failed_event_id == target_id
    assert "PAYLOAD_TAMPERING" in result.error_reason
