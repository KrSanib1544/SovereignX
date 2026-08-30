# backend/tests/conftest.py
"""
Pytest Fixtures for SOVEREIGN-X Persistence Layer
Provides temporary, isolated test SQLite databases with WAL and foreign key support.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.db.base import Base
from backend.app.db.session import _set_sqlite_pragma
import backend.app.db.models  # Register all models


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[Path, None, None]:
    """Provides a temporary file path for a test SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        yield tmp_path
    finally:
        if tmp_path.exists():
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@pytest.fixture(scope="function")
def test_engine(temp_db_path: Path) -> Generator[Engine, None, None]:
    """Creates a temporary test SQLite engine with WAL mode and foreign key pragmas."""
    db_url = f"sqlite:///{temp_db_path.as_posix()}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _set_sqlite_pragma)

    # Initialize schema
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Provides a clean, isolated SQLAlchemy Session for a single test function."""
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
