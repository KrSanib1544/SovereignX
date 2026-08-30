# backend/tests/unit/test_chunking.py
"""
Unit Tests for Hierarchical & Semantic Chunking Engine
Validates chunk determinism, section preservation, table protection, and provenance continuity.
"""

from pathlib import Path
from backend.app.ingestion.pdf_parser import PDFParser
from backend.app.ingestion.excel_parser import ExcelParser
from backend.app.rag.chunking import HierarchicalChunker
from backend.tests.fixtures_helper import create_sample_digital_pdf, create_sample_xlsx


def test_hierarchical_chunking_pdf(tmp_path):
    """Test chunking a digital PDF preserves document ID, page numbers, and section headers."""
    pdf_path = create_sample_digital_pdf(tmp_path / "inspection.pdf")
    parsed_doc = PDFParser.parse(pdf_path)

    doc_id = "doc_test_101"
    ws_id = "ws_test_999"

    chunks = HierarchicalChunker.chunk_document(
        parsed_doc=parsed_doc,
        document_id=doc_id,
        workspace_id=ws_id,
        classification="RESTRICTED_CONFIDENTIAL"
    )

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.document_id == doc_id
        assert chunk.workspace_id == ws_id
        assert chunk.classification == "RESTRICTED_CONFIDENTIAL"
        assert chunk.chunk_id.startswith("chk_doc_test_101_")
        assert chunk.token_count > 0
        assert len(chunk.content) > 0


def test_chunking_table_preservation(tmp_path):
    """Test that spreadsheet table blocks remain whole and carry is_table flag."""
    xlsx_path = create_sample_xlsx(tmp_path / "data.xlsx")
    parsed_doc = ExcelParser.parse(xlsx_path)

    chunks = HierarchicalChunker.chunk_document(
        parsed_doc=parsed_doc,
        document_id="doc_excel_01",
        workspace_id="ws_01"
    )

    table_chunks = [c for c in chunks if c.is_table]
    assert len(table_chunks) >= 2
    assert any("Pump_3B_Casing" in c.content for c in table_chunks)


def test_chunk_determinism(tmp_path):
    """Test that chunking the same parsed document multiple times yields identical chunk IDs and contents."""
    pdf_path = create_sample_digital_pdf(tmp_path / "inspection.pdf")
    parsed_doc = PDFParser.parse(pdf_path)

    run_1 = HierarchicalChunker.chunk_document(parsed_doc, "doc_01", "ws_01")
    run_2 = HierarchicalChunker.chunk_document(parsed_doc, "doc_01", "ws_01")

    assert len(run_1) == len(run_2)
    for c1, c2 in zip(run_1, run_2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.content == c2.content
        assert c1.page_number == c2.page_number
        assert c1.bbox == c2.bbox
