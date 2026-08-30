# backend/app/ingestion/__init__.py
"""
SOVEREIGN-X Ingestion Module
"""

from backend.app.ingestion.models import (
    ParsedDocument,
    ExtractedBlock,
    SourceType,
    ExtractionMethod,
    df_to_clean_markdown,
)
from backend.app.ingestion.validator import (
    DocumentValidator,
    DocumentValidationResult,
    DocumentValidationError,
)
from backend.app.ingestion.pdf_parser import PDFParser
from backend.app.ingestion.ocr_engine import OCREngine
from backend.app.ingestion.excel_parser import ExcelParser
from backend.app.ingestion.text_parser import TextAndCSVParser

__all__ = [
    "ParsedDocument",
    "ExtractedBlock",
    "SourceType",
    "ExtractionMethod",
    "df_to_clean_markdown",
    "DocumentValidator",
    "DocumentValidationResult",
    "DocumentValidationError",
    "PDFParser",
    "OCREngine",
    "ExcelParser",
    "TextAndCSVParser",
]
