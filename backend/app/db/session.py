# backend/app/db/session.py
"""
Database Session and Engine Management
Configures SQLite with WAL mode, foreign key enforcement, connection pooling,
and safe transaction context managers.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.config import settings
from backend.app.db.base import Base
import backend.app.db.models  # Ensure all ORM models are registered with Base metadata


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enforces SQLite pragmas on every connection:
    - WAL journal mode for concurrent read/write throughput
    - Foreign key constraints enforcement
    - Synchronous = NORMAL for optimal NVMe SSD performance
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.close()


def create_sqlite_engine(database_url: str = settings.DATABASE_URL) -> Engine:
    """
    Create a configured SQLite SQLAlchemy engine with security pragmas.
    """
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
    event.listen(engine, "connect", _set_sqlite_pragma)
    return engine


# Default application engine and session factory
engine = create_sqlite_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def init_db(target_engine: Engine = engine) -> None:
    """
    Initialize SQLite schema and create all defined tables if not present.
    """
    settings.ensure_directories()
    Base.metadata.create_all(bind=target_engine)


@contextmanager
def get_db(target_session_factory=SessionLocal) -> Generator[Session, None, None]:
    """
    Safe transactional database session context manager.
    Commits on success, rolls back on exceptions, and closes reliably.
    """
    session: Session = target_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
