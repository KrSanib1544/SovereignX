# backend/app/ingestion/ocr_engine.py
"""
Offline OCR Engine
Extracts text and normalized bounding boxes [0, 1000] from rasterized document images.
Runs 100% locally with zero external network connectivity.
"""

import io
import shutil
from typing import List, Optional, Tuple
from PIL import Image
import pytesseract

from backend.app.ingestion.models import ExtractedBlock, ExtractionMethod


def is_tesseract_available() -> bool:
    """Check if Tesseract binary is accessible in the system PATH."""
    return shutil.which("tesseract") is not None


class OCREngine:
    """
    Offline OCR Processor providing text extraction with normalized coordinates [0, 1000].
    """

    @classmethod
    def extract_from_image(
        cls,
        image_bytes: bytes,
        page_number: int = 1
    ) -> Tuple[List[ExtractedBlock], bool]:
        """
        Processes image bytes, performing OCR and extracting lines/words with normalized bounding rects.
        Returns (blocks, ocr_success_flag).
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            img_w, img_h = image.size
        except Exception as e:
            return ([ExtractedBlock(
                content=f"[OCR Error: Failed to decode image: {str(e)}]",
                page_number=page_number,
                source_location=f"Page {page_number}",
                extraction_method=ExtractionMethod.OCR_FALLBACK
            )], False)

        if not is_tesseract_available():
            # Graceful local fallback when tesseract binary is not installed on host
            return ([ExtractedBlock(
                content=f"[Scanned Page {page_number} - Image dimensions {img_w}x{img_h} px. Tesseract OCR binary not detected on host system.]",
                page_number=page_number,
                source_location=f"Page {page_number} (Image)",
                bbox=[0.0, 0.0, 1000.0, 1000.0],
                extraction_method=ExtractionMethod.OCR_FALLBACK,
                confidence=None
            )], True)

        try:
            # Run Tesseract with TSV/Data output to capture coordinates and confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            blocks: List[ExtractedBlock] = []
            current_line_words: List[str] = []
            current_line_boxes: List[Tuple[int, int, int, int]] = []
            current_confidences: List[float] = []

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = float(data["conf"][i])
                if not text:
                    continue

                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                current_line_words.append(text)
                current_line_boxes.append((x, y, x + w, y + h))
                if conf > 0:
                    current_confidences.append(conf / 100.0)

                # When line ends or text block completes
                if (i + 1 == n_boxes) or (data["line_num"][i] != data["line_num"][i + 1]):
                    if current_line_words:
                        line_text = " ".join(current_line_words)
                        # Compute aggregate bounding box
                        min_x = min(b[0] for b in current_line_boxes)
                        min_y = min(b[1] for b in current_line_boxes)
                        max_x = max(b[2] for b in current_line_boxes)
                        max_y = max(b[3] for b in current_line_boxes)

                        # Normalize to [0, 1000]
                        norm_bbox = [
                            round((min_x / img_w) * 1000.0, 2),
                            round((min_y / img_h) * 1000.0, 2),
                            round((max_x / img_w) * 1000.0, 2),
                            round((max_y / img_h) * 1000.0, 2),
                        ]

                        avg_conf = (
                            round(sum(current_confidences) / len(current_confidences), 3)
                            if current_confidences else None
                        )

                        blocks.append(ExtractedBlock(
                            content=line_text,
                            page_number=page_number,
                            source_location=f"Page {page_number}, OCR Line {len(blocks) + 1}",
                            bbox=norm_bbox,
                            extraction_method=ExtractionMethod.OCR_TESSERACT,
                            confidence=avg_conf
                        ))

                        current_line_words = []
                        current_line_boxes = []
                        current_confidences = []

            return (blocks, True)
        except Exception as e:
            return ([ExtractedBlock(
                content=f"[OCR Processing Error on Page {page_number}: {str(e)}]",
                page_number=page_number,
                source_location=f"Page {page_number}",
                extraction_method=ExtractionMethod.OCR_FALLBACK
            )], False)
