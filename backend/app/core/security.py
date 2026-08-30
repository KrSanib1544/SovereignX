# backend/app/core/security.py
"""
SOVEREIGN-X Security Utilities
Provides cryptographically secure ID generation, UTC timestamp helpers,
and path-traversal sanitizers.
"""

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


class SecurityPolicyViolationError(Exception):
    """Raised when an operation violates a security boundary or containment policy."""
    pass


def generate_uuid(prefix: str = "") -> str:
    """
    Generate a cryptographically secure random identifier with an optional prefix.
    Example: generate_uuid("ws") -> "ws_3f92b7c4d81a"
    """
    random_hex = uuid.uuid4().hex[:12]
    return f"{prefix}_{random_hex}" if prefix else random_hex


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def format_canonical_timestamp(dt: datetime) -> str:
    """
    Format a datetime into a canonical UTC ISO-8601 string for deterministic hashing.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def resolve_secure_workspace_path(
    base_workspace_dir: Path,
    relative_path: str,
    must_exist: bool = False
) -> Path:
    """
    Canonicalizes and validates that a relative path stays strictly within the workspace jail.
    Guards against path traversal, absolute drive letters, symlink escapes, and parent directory attacks.
    """
    if not relative_path or not relative_path.strip():
        raise SecurityPolicyViolationError("Empty relative path provided.")

    base_dir = base_workspace_dir.resolve()
    clean_str = relative_path.strip().replace("\\", "/")

    # 1. Reject absolute paths or Windows drive letters (e.g., C:/, /etc/passwd)
    if clean_str.startswith("/") or re.match(r"^[a-zA-Z]:", relative_path):
        raise SecurityPolicyViolationError(
            f"Absolute path or drive letter detected: '{relative_path}'. Only workspace-relative paths permitted."
        )

    # 2. Reject any path containing consecutive dots (e.g. .., ..., ....) which indicate traversal attempts
    if re.search(r"\.{2,}", clean_str):
        raise SecurityPolicyViolationError(
            f"Path traversal sequence detected in relative path: '{relative_path}'."
        )

    # 3. Resolve path and ensure strict ancestor containment
    target_path = (base_dir / clean_str).resolve()
    
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise SecurityPolicyViolationError(
            f"Path traversal detected! Path '{relative_path}' escapes workspace root '{base_dir}'."
        )
        
    if must_exist and not target_path.exists():
        raise FileNotFoundError(f"Requested file '{relative_path}' not found in workspace.")
        
    return target_path
