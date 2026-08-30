# backend/tests/unit/test_pdf_parser.py
"""
Unit Tests for Digital PDF Parser
Tests page-by-page extraction, structural headings, coordinates, and bounding box normalization.
"""

from pathlib import Path
from backend.app.ingestion.pdf_parser import PDFParser
from backend.app.ingestion.models import SourceType, ExtractionMethod
from backend.tests.fixtures_helper import create_sample_digital_pdf, create_sample_scanned_pdf


def test_digital_pdf_parsing(tmp_path):
    """Test extracting native text and normalized bounding boxes from a 2-page digital PDF."""
    pdf_path = create_sample_digital_pdf(tmp_path / "inspection.pdf")

    parsed_doc = PDFParser.parse(pdf_path)

    assert parsed_doc.filename == "inspection.pdf"
    assert parsed_doc.page_count == 2
    assert parsed_doc.ocr_applied is False
    assert parsed_doc.source_type == SourceType.PDF_DIGITAL
    assert len(parsed_doc.blocks) >= 2

    # Check Page 1 Content
    p1_blocks = [b for b in parsed_doc.blocks if b.page_number == 1]
    assert any("Reflux Pump 3B" in b.content for b in p1_blocks)

    # Check Page 2 Content & Heading
    p2_blocks = [b for b in parsed_doc.blocks if b.page_number == 2]
    assert any("3.42 mm" in b.content for b in p2_blocks)
    assert any(b.section_title and "Section 3.2" in b.section_title for b in p2_blocks)

    # Verify Bounding Box Coordinates are within [0, 1000]
    for block in parsed_doc.blocks:
        if block.bbox:
            assert len(block.bbox) == 4
            assert all(0.0 <= coord <= 1000.0 for coord in block.bbox)
            assert block.bbox[0] <= block.bbox[2]
            assert block.bbox[1] <= block.bbox[3]


def test_scanned_pdf_detection(tmp_path):
    """Test that image-only PDF triggers scanned-page handler."""
    scanned_path = create_sample_scanned_pdf(tmp_path / "scanned_field_log.pdf")

    parsed_doc = PDFParser.parse(scanned_path, enable_ocr=True)

    assert parsed_doc.page_count == 1
    assert parsed_doc.ocr_applied is True
    assert parsed_doc.source_type == SourceType.PDF_OCR
    assert len(parsed_doc.blocks) >= 1
