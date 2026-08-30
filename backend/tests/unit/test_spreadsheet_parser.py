# backend/tests/unit/test_spreadsheet_parser.py
"""
Unit Tests for Spreadsheet (XLSX) and CSV Parsers
Validates multi-sheet workbook parsing, column schema extraction, and row provenance.
"""

from pathlib import Path
from backend.app.ingestion.excel_parser import ExcelParser
from backend.app.ingestion.text_parser import TextAndCSVParser
from backend.app.ingestion.models import SourceType, ExtractionMethod
from backend.tests.fixtures_helper import create_sample_xlsx, create_sample_csv, create_sample_txt


def test_excel_multi_sheet_parsing(tmp_path):
    """Test extracting multi-sheet Excel workbook with schema summary and markdown row blocks."""
    xlsx_path = create_sample_xlsx(tmp_path / "maintenance_history.xlsx")

    parsed_doc = ExcelParser.parse(xlsx_path)

    assert parsed_doc.filename == "maintenance_history.xlsx"
    assert parsed_doc.page_count == 2
    assert parsed_doc.source_type == SourceType.SPREADSHEET
    assert parsed_doc.metadata["sheet_count"] == 2
    assert "Thickness_Log" in parsed_doc.metadata["sheets"]
    assert "OEM_Limits" in parsed_doc.metadata["sheets"]

    # Verify blocks contain Markdown table formatting and expected data
    assert any("Year" in b.content and "Component" in b.content and "|" in b.content for b in parsed_doc.blocks)
    assert any("Pump_3B_Casing" in b.content for b in parsed_doc.blocks)
    assert any("MANDATORY_REPLACEMENT" in b.content for b in parsed_doc.blocks)


def test_csv_parsing(tmp_path):
    """Test parsing CSV table into schema and row blocks."""
    csv_path = create_sample_csv(tmp_path / "telemetry.csv")

    parsed_doc = TextAndCSVParser.parse_csv(csv_path)

    assert parsed_doc.filename == "telemetry.csv"
    assert parsed_doc.source_type == SourceType.CSV
    assert parsed_doc.page_count == 1
    assert any("Sensor_ID" in b.content for b in parsed_doc.blocks)
    assert any("VIB-3B-01" in b.content for b in parsed_doc.blocks)


def test_txt_parsing(tmp_path):
    """Test parsing UTF-8 text document into logical section blocks."""
    txt_path = create_sample_txt(tmp_path / "directive.txt")

    parsed_doc = TextAndCSVParser.parse_txt(txt_path)

    assert parsed_doc.filename == "directive.txt"
    assert parsed_doc.source_type == SourceType.TEXT
    assert len(parsed_doc.blocks) >= 2
    assert any("Engineering Directive" in b.content for b in parsed_doc.blocks)
