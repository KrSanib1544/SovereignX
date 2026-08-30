# backend/app/ingestion/models.py
"""
Normalized Ingestion Data Models
Defines universal structures produced by all document parsers (PDF, OCR, XLSX, CSV, TXT)
prior to downstream chunking and vector embedding.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PDF_DIGITAL = "PDF_DIGITAL"
    PDF_OCR = "PDF_OCR"
    SPREADSHEET = "SPREADSHEET"
    CSV = "CSV"
    TEXT = "TEXT"
    IMAGE = "IMAGE"


class ExtractionMethod(str, Enum):
    NATIVE_TEXT = "NATIVE_TEXT"
    OCR_TESSERACT = "OCR_TESSERACT"
    OCR_FALLBACK = "OCR_FALLBACK"
    PANDAS_TABULAR = "PANDAS_TABULAR"
    PLAIN_TEXT = "PLAIN_TEXT"


def df_to_clean_markdown(df: pd.DataFrame) -> str:
    """Safely convert a pandas DataFrame to Markdown table format."""
    try:
        return df.to_markdown(index=False)
    except Exception:
        # Fallback simple markdown generator
        headers = [str(c) for c in df.columns]
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for _, row in df.iterrows():
            row_vals = [str(v) if pd.notna(v) else "" for v in row]
            lines.append("| " + " | ".join(row_vals) + " |")
        return "\n".join(lines)


class ExtractedBlock(BaseModel):
    """
    Represents a single structural unit of extracted content with exact provenance.
    """
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    source_location: Optional[str] = None  # e.g., "Sheet: History, Row: 12" or "Page: 4, Block: 2"
    bbox: Optional[List[float]] = None     # Normalized [x0, y0, x1, y1] within [0, 1000]
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE_TEXT
    is_table: bool = False
    confidence: Optional[float] = None     # 0.0 - 1.0 confidence score if available


class ParsedDocument(BaseModel):
    """
    Universal intermediate representation produced by all document parsers.
    """
    filename: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    page_count: int = 1
    ocr_applied: bool = False
    source_type: SourceType
    blocks: List[ExtractedBlock] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def total_text_length(self) -> int:
        return sum(len(b.content) for b in self.blocks)
