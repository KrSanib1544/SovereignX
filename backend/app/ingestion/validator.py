# backend/app/ingestion/validator.py
"""
Document Ingestion Validator
Validates file extensions, MIME signatures, magic bytes, file size limits,
and workspace boundary containment before ingestion.
"""

import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Set, Tuple
from pydantic import BaseModel

from backend.app.core.security import resolve_secure_workspace_path, SecurityPolicyViolationError


class DocumentValidationError(Exception):
    """Raised when a document fails security, format, or size validation."""
    pass


class DocumentValidationResult(BaseModel):
    is_valid: bool
    resolved_path: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    extension: str


# Supported extensions and magic byte signatures
SUPPORTED_EXTENSIONS: Set[str] = {".pdf", ".xlsx", ".xls", ".csv", ".txt"}
MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

# Magic byte signatures for file verification
MAGIC_SIGNATURES: Dict[str, bytes] = {
    ".pdf": b"%PDF",
    ".xlsx": b"PK\x03\x04",   # ZIP header for OOXML
    ".xls": b"\xd0\xcf\x11\xe0", # Compound File Binary
}


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file efficiently in chunks."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DocumentValidator:
    """
    Validates documents before parsing to prevent path traversal,
    corrupted uploads, and unsupported binary formats.
    """

    @classmethod
    def validate(
        cls,
        workspace_dir: Path,
        relative_path: str,
        max_size_bytes: int = MAX_FILE_SIZE_BYTES
    ) -> DocumentValidationResult:
        """
        Validate file path containment, existence, extension, magic signature, and size.
        """
        # 1. Path Containment & Traversal Validation
        target_path = resolve_secure_workspace_path(
            base_workspace_dir=workspace_dir,
            relative_path=relative_path,
            must_exist=True
        )

        filename = target_path.name
        extension = target_path.suffix.lower()

        # 2. Extension Check
        if extension not in SUPPORTED_EXTENSIONS:
            raise DocumentValidationError(
                f"Unsupported file format '{extension}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        # 3. File Size Validation
        size_bytes = target_path.stat().st_size
        if size_bytes == 0:
            raise DocumentValidationError(f"File '{filename}' is empty (0 bytes).")
        if size_bytes > max_size_bytes:
            raise DocumentValidationError(
                f"File '{filename}' size ({size_bytes} bytes) exceeds maximum limit ({max_size_bytes} bytes)."
            )

        # 4. Magic Byte Signature Verification
        if extension in MAGIC_SIGNATURES:
            expected_prefix = MAGIC_SIGNATURES[extension]
            with open(target_path, "rb") as f:
                header = f.read(len(expected_prefix))
                if not header.startswith(expected_prefix):
                    raise DocumentValidationError(
                        f"File '{filename}' magic signature mismatch. Expected {expected_prefix!r}, got {header!r}."
                    )

        # 5. Compute SHA-256 and Determine MIME Type
        sha256_hash = compute_file_sha256(target_path)
        mime_type, _ = mimetypes.guess_type(target_path)
        if not mime_type:
            if extension == ".pdf":
                mime_type = "application/pdf"
            elif extension == ".xlsx":
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif extension == ".csv":
                mime_type = "text/csv"
            elif extension == ".txt":
                mime_type = "text/plain"
            else:
                mime_type = "application/octet-stream"

        return DocumentValidationResult(
            is_valid=True,
            resolved_path=str(target_path),
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            extension=extension
        )
