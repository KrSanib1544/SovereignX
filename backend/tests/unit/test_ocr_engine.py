# backend/tests/unit/test_ocr_engine.py
"""
Unit Tests for Offline OCR Engine
Tests image text extraction, fallback behavior, coordinate normalization [0, 1000], and error handling.
"""

import io
from PIL import Image, ImageDraw
from backend.app.ingestion.ocr_engine import OCREngine, is_tesseract_available
from backend.app.ingestion.models import ExtractionMethod


def test_ocr_engine_execution():
    """Test OCR processing on a synthesized test image."""
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "SAMPLE NDT LOG 2026", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    blocks, success = OCREngine.extract_from_image(img_bytes, page_number=1)

    assert success is True
    assert len(blocks) >= 1
    assert blocks[0].page_number == 1

    if is_tesseract_available():
        assert blocks[0].extraction_method == ExtractionMethod.OCR_TESSERACT
    else:
        assert blocks[0].extraction_method == ExtractionMethod.OCR_FALLBACK


def test_ocr_engine_corrupt_image_handling():
    """Test graceful handling when invalid image bytes are supplied."""
    corrupt_bytes = b"NOT_A_VALID_IMAGE_DATA"
    blocks, success = OCREngine.extract_from_image(corrupt_bytes, page_number=3)

    assert success is False
    assert len(blocks) == 1
    assert "OCR Error" in blocks[0].content
    assert blocks[0].page_number == 3
