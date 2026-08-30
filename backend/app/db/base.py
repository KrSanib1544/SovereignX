# backend/app/db/base.py
"""
SOVEREIGN-X Database Base Declarative Model
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM model instance into a Python dictionary."""
        result = {}
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if isinstance(val, datetime):
                result[column.name] = val.isoformat()
            else:
                result[column.name] = val
        return result
