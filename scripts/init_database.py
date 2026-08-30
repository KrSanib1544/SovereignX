# scripts/init_database.py
"""
Manual Database Initialization and Self-Test Script
Initializes ./data/sovereign.db in WAL mode and verifies schema creation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.db.session import engine, init_db, get_db
from backend.app.db.models import WorkspaceORM
from backend.app.core.audit_logger import AuditLogger
from backend.app.core.security import generate_uuid


def main():
    print("=" * 60)
    print("SOVEREIGN-X Database Initialization & Verification")
    print("=" * 60)
    print(f"Target Database File: {settings.DATABASE_PATH}")
    print(f"Base Directory:       {settings.BASE_DIR}")
    print(f"Air-Gap Mode:         {settings.AIRGAP_MODE}")
    print("-" * 60)

    # 1. Initialize DB Schema
    print("[1/4] Creating tables and configuring SQLite WAL pragmas...")
    init_db(engine)
    print("      -> Tables created successfully.")

    # 2. Verify File Creation on Disk
    if settings.DATABASE_PATH.exists():
        print(f"[2/4] Verified database file on disk ({settings.DATABASE_PATH.stat().st_size} bytes).")
    else:
        print("[ERROR] Database file not found on disk!")
        sys.exit(1)

    # 3. Insert Smoke-Test Workspace & Audit Event
    print("[3/4] Testing transactional write & cryptographic audit chain...")
    with get_db() as session:
        ws_id = generate_uuid("ws")
        test_ws = WorkspaceORM(
            id=ws_id,
            name="Plant 4 Maintenance Analysis",
            description="Autonomous multi-modal inspection workspace for SIH 2026",
            classification_level="INTERNAL_ENGINEERING",
            storage_path=str(settings.WORKSPACES_DIR / ws_id)
        )
        session.add(test_ws)
        session.flush()

        AuditLogger.record_event(
            session=session,
            event_type="WORKSPACE_INIT",
            payload={"workspace_name": test_ws.name, "classification": test_ws.classification_level},
            workspace_id=ws_id,
            actor="SYSTEM_INIT"
        )

    # 4. Verify Audit Chain
    print("[4/4] Verifying cryptographic hash-chain integrity...")
    with get_db() as session:
        result = AuditLogger.verify_chain(session)
        if result.is_valid:
            print(f"      -> Cryptographic hash-chain VERIFIED. ({result.verified_count} events validated)")
        else:
            print(f"[ERROR] Audit chain failed verification: {result.error_reason}")
            sys.exit(1)

    print("=" * 60)
    print("DATABASE INITIALIZATION & VERIFICATION COMPLETE (100% PASS)")
    print("=" * 60)


if __name__ == "__main__":
    main()
