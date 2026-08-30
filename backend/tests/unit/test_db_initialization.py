# backend/tests/unit/test_db_initialization.py
"""
Unit Tests for Database Engine Initialization & Pragmas
"""

import sqlite3
from sqlalchemy import text
from backend.app.db.base import Base
from backend.app.db.session import init_db, create_sqlite_engine


def test_database_initialization_and_tables(temp_db_path):
    """Test that init_db creates all required tables in a fresh database."""
    db_url = f"sqlite:///{temp_db_path.as_posix()}"
    engine = create_sqlite_engine(db_url)
    
    init_db(target_engine=engine)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        )
        table_names = [row[0] for row in result.fetchall()]

    expected_tables = {
        "workspaces",
        "documents",
        "document_chunks",
        "tasks",
        "task_steps",
        "tool_executions",
        "artifacts",
        "audit_events",
    }

    for table in expected_tables:
        assert table in table_names, f"Table '{table}' was not created during init_db."

    engine.dispose()


def test_sqlite_pragmas(test_engine):
    """Test that WAL mode, foreign keys, and synchronous normal are enforced."""
    with test_engine.connect() as conn:
        # Check foreign keys
        fk_result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_result == 1, "Foreign keys are not enabled."

        # Check journal mode (in WAL mode, or memory if in-memory)
        journal_result = conn.execute(text("PRAGMA journal_mode;")).scalar()
        assert str(journal_result).lower() in ("wal", "memory"), f"Unexpected journal mode: {journal_result}"

        # Check synchronous
        sync_result = conn.execute(text("PRAGMA synchronous;")).scalar()
        # NORMAL is integer 1 in SQLite
        assert sync_result in (1, "1", "NORMAL", "normal"), f"Unexpected synchronous setting: {sync_result}"
