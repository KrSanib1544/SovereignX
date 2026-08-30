# backend/app/core/audit_logger.py
"""
Immutable Cryptographic Audit Logger
Implements SHA-256 hash-chaining to provide mathematical tamper evidence
over all system actions, tool executions, and security decisions.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.core.security import generate_uuid, utc_now, format_canonical_timestamp
from backend.app.db.models.audit_orm import AuditEventORM


GENESIS_HASH = "0" * 64


def canonical_json(data: Any) -> str:
    """
    Serialize data into a deterministic, sorted, compact JSON string for consistent hashing.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_event_hash(
    previous_hash: str,
    event_uuid: str,
    timestamp_iso: str,
    event_type: str,
    payload_json: str
) -> str:
    """
    Compute SHA-256 hash over the canonical concatenated event representation:
    SHA256(previous_hash + event_uuid + timestamp_iso + event_type + payload_json)
    """
    hasher = hashlib.sha256()
    hasher.update(previous_hash.encode("utf-8"))
    hasher.update(event_uuid.encode("utf-8"))
    hasher.update(timestamp_iso.encode("utf-8"))
    hasher.update(event_type.encode("utf-8"))
    hasher.update(payload_json.encode("utf-8"))
    return hasher.hexdigest()


@dataclass
class AuditVerificationResult:
    """Represents the outcome of a cryptographic audit chain verification run."""
    is_valid: bool
    verified_count: int
    failed_event_id: Optional[int] = None
    failed_event_uuid: Optional[str] = None
    error_reason: Optional[str] = None
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None


class AuditLogger:
    """
    Provides atomic hash-chain recording and verification methods for audit trails.
    """

    @staticmethod
    def record_event(
        session: Session,
        event_type: str,
        payload: Dict[str, Any],
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        actor: str = "SYSTEM_AGENT",
        client_ip: str = "127.0.0.1"
    ) -> AuditEventORM:
        """
        Atomically appends an audit event to the cryptographic hash chain.
        """
        # 1. Fetch the latest audit record to obtain previous_hash
        latest_event = session.execute(
            select(AuditEventORM).order_by(desc(AuditEventORM.id)).limit(1)
        ).scalar_one_or_none()

        previous_hash = latest_event.current_hash if latest_event else GENESIS_HASH

        # 2. Build canonical event metadata
        event_uuid = generate_uuid("evt")
        event_time = utc_now()
        timestamp_iso = format_canonical_timestamp(event_time)
        payload_str = canonical_json(payload)

        # 3. Compute current entry hash
        current_hash = compute_event_hash(
            previous_hash=previous_hash,
            event_uuid=event_uuid,
            timestamp_iso=timestamp_iso,
            event_type=event_type,
            payload_json=payload_str
        )

        # 4. Create and persist ORM model
        audit_record = AuditEventORM(
            event_uuid=event_uuid,
            timestamp=event_time,
            actor=actor,
            workspace_id=workspace_id,
            task_id=task_id,
            event_type=event_type,
            payload_json=payload_str,
            client_ip=client_ip,
            previous_hash=previous_hash,
            current_hash=current_hash
        )

        session.add(audit_record)
        session.flush()  # Flush to assign ID within active transaction
        return audit_record

    @staticmethod
    def verify_chain(session: Session, workspace_id: Optional[str] = None) -> AuditVerificationResult:
        """
        Traverse and mathematically verify the entire audit event chain.
        Detects any modified payload, altered timestamp, deleted row, or reordered sequence.
        """
        query = select(AuditEventORM).order_by(AuditEventORM.id.asc())
        if workspace_id:
            # If scoped to a workspace, verify workspace events
            query = query.where(AuditEventORM.workspace_id == workspace_id)

        events: List[AuditEventORM] = list(session.execute(query).scalars().all())

        if not events:
            return AuditVerificationResult(is_valid=True, verified_count=0)

        expected_prev_hash = GENESIS_HASH

        for idx, event in enumerate(events):
            # 1. Verify previous_hash link
            if event.previous_hash != expected_prev_hash:
                return AuditVerificationResult(
                    is_valid=False,
                    verified_count=idx,
                    failed_event_id=event.id,
                    failed_event_uuid=event.event_uuid,
                    error_reason="BROKEN_CHAIN_LINK: previous_hash does not match previous record's current_hash.",
                    expected_hash=expected_prev_hash,
                    actual_hash=event.previous_hash
                )

            # 2. Re-compute and verify current_hash integrity
            timestamp_canonical = format_canonical_timestamp(event.timestamp)
            recalculated_hash = compute_event_hash(
                previous_hash=event.previous_hash,
                event_uuid=event.event_uuid,
                timestamp_iso=timestamp_canonical,
                event_type=event.event_type,
                payload_json=event.payload_json
            )

            if event.current_hash != recalculated_hash:
                return AuditVerificationResult(
                    is_valid=False,
                    verified_count=idx,
                    failed_event_id=event.id,
                    failed_event_uuid=event.event_uuid,
                    error_reason="PAYLOAD_TAMPERING: recalculated SHA-256 does not match stored current_hash.",
                    expected_hash=recalculated_hash,
                    actual_hash=event.current_hash
                )

            expected_prev_hash = event.current_hash

        return AuditVerificationResult(is_valid=True, verified_count=len(events))
