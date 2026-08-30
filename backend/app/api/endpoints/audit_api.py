# backend/app/api/endpoints/audit_api.py
"""
Audit & Ledger REST Endpoints
Provides APIs to inspect immutable SQLite audit logs and execute real-time SHA-256 continuous hash chain verification.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.audit_logger import AuditLogger
from backend.app.db.models.audit_orm import AuditEventORM
from backend.app.db.session import get_db_session

router = APIRouter()


class AuditEventResponse(BaseModel):
    id: int
    event_uuid: str
    timestamp: str
    actor: str
    workspace_id: Optional[str] = None
    task_id: Optional[str] = None
    event_type: str
    payload_json: str
    client_ip: Optional[str] = None
    previous_hash: str
    current_hash: str


class AuditVerificationResponse(BaseModel):
    is_valid: bool
    total_events: int
    error_reason: Optional[str] = None
    last_verified_hash: Optional[str] = None


@router.get("/audit", response_model=List[AuditEventResponse])
async def list_audit_events(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve historical audit log events ordered by creation timestamp descending.
    """
    query = db.query(AuditEventORM)
    if workspace_id:
        query = query.filter(AuditEventORM.workspace_id == workspace_id)

    events = query.order_by(AuditEventORM.id.desc()).limit(limit).all()

    return [
        AuditEventResponse(
            id=e.id,
            event_uuid=e.event_uuid,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
            actor=e.actor,
            workspace_id=e.workspace_id,
            task_id=e.task_id,
            event_type=e.event_type,
            payload_json=e.payload_json,
            client_ip=e.client_ip,
            previous_hash=e.previous_hash,
            current_hash=e.current_hash
        )
        for e in events
    ]


@router.post("/audit/verify", response_model=AuditVerificationResponse)
async def verify_audit_hash_chain(db: Session = Depends(get_db_session)):
    """
    Perform complete cryptographic verification of the SHA-256 continuous hash chain.
    """
    res = AuditLogger.verify_chain(db)
    last_event = db.query(AuditEventORM).order_by(AuditEventORM.id.desc()).first()

    return AuditVerificationResponse(
        is_valid=res.is_valid,
        total_events=res.verified_count,
        error_reason=res.error_reason,
        last_verified_hash=last_event.current_hash if last_event else None
    )
