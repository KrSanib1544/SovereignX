# backend/tests/unit/test_validation.py
"""
Unit Tests for Document Ingestion Validator
Validates file extensions, size limits, path jail containment, and magic signatures.
"""

from pathlib import Path
import pytest
from backend.app.core.security import SecurityPolicyViolationError
from backend.app.ingestion.validator import (
    DocumentValidator,
    DocumentValidationError,
    SUPPORTED_EXTENSIONS,
)
from backend.tests.fixtures_helper import (
    create_sample_digital_pdf,
    create_sample_xlsx,
    create_sample_csv,
    create_sample_txt,
)


def test_supported_document_validation(tmp_path):
    """Test that all supported formats (PDF, XLSX, CSV, TXT) pass validation with correct metadata."""
    workspace_dir = tmp_path / "workspaces" / "ws_valid"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = create_sample_digital_pdf(workspace_dir / "report.pdf")
    xlsx_path = create_sample_xlsx(workspace_dir / "data.xlsx")
    csv_path = create_sample_csv(workspace_dir / "telemetry.csv")
    txt_path = create_sample_txt(workspace_dir / "notes.txt")

    for rel_path in ["report.pdf", "data.xlsx", "telemetry.csv", "notes.txt"]:
        res = DocumentValidator.validate(workspace_dir=workspace_dir, relative_path=rel_path)
        assert res.is_valid is True
        assert res.size_bytes > 0
        assert len(res.sha256_hash) == 64
        assert res.extension in SUPPORTED_EXTENSIONS


def test_unsupported_extension_rejection(tmp_path):
    """Test that executable and dangerous file types are rejected."""
    workspace_dir = tmp_path / "workspaces" / "ws_unsupported"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    bad_file = workspace_dir / "script.exe"
    with open(bad_file, "wb") as f:
        f.write(b"MZ\x90\x00BinaryPayload")

    with pytest.raises(DocumentValidationError) as exc:
        DocumentValidator.validate(workspace_dir=workspace_dir, relative_path="script.exe")
    assert "Unsupported file format '.exe'" in str(exc.value)


def test_empty_file_rejection(tmp_path):
    """Test that 0-byte empty files are rejected."""
    workspace_dir = tmp_path / "workspaces" / "ws_empty"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    empty_file = workspace_dir / "empty.txt"
    empty_file.touch()

    with pytest.raises(DocumentValidationError) as exc:
        DocumentValidator.validate(workspace_dir=workspace_dir, relative_path="empty.txt")
    assert "is empty (0 bytes)" in str(exc.value)


def test_path_traversal_rejection(tmp_path):
    """Test that path traversal attempts are stopped at validation boundary."""
    workspace_dir = tmp_path / "workspaces" / "ws_jail"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SecurityPolicyViolationError):
        DocumentValidator.validate(workspace_dir=workspace_dir, relative_path="../../secret.pdf")
