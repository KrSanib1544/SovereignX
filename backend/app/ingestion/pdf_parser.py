# backend/app/ingestion/pdf_parser.py
"""
Digital PDF & Scanned Document Parser
Uses PyMuPDF (fitz) for native vector text, structural tables, and layout coordinates,
with automatic fallback to OCREngine for scanned pages.
"""

import re
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF

from backend.app.ingestion.models import (
    ParsedDocument,
    ExtractedBlock,
    SourceType,
    ExtractionMethod,
)
from backend.app.ingestion.ocr_engine import OCREngine


class PDFParser:
    """
    High-performance, local-only PDF extraction engine.
    """

    MIN_NATIVE_TEXT_CHARS: int = 50

    @classmethod
    def parse(
        cls,
        filepath: Path,
        enable_ocr: bool = True,
        filename_override: Optional[str] = None
    ) -> ParsedDocument:
        """
        Extract text, tables, and coordinates from a digital or scanned PDF.
        """
        filename = filename_override or filepath.name
        doc = fitz.open(filepath)
        page_count = len(doc)
        
        extracted_blocks: List[ExtractedBlock] = []
        any_ocr_applied = False
        current_section: Optional[str] = None

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_rect = page.rect
            page_w = max(page_rect.width, 1.0)
            page_h = max(page_rect.height, 1.0)

            # 1. Check for native vector tables first (if supported by PyMuPDF version)
            table_rects = []
            try:
                tabs = page.find_tables()
                if tabs.tables:
                    for t_idx, table in enumerate(tabs.tables):
                        tab_df = table.to_pandas()
                        if not tab_df.empty:
                            table_md = tab_df.to_markdown(index=False)
                            t_bbox = [
                                round((table.bbox[0] / page_w) * 1000.0, 2),
                                round((table.bbox[1] / page_h) * 1000.0, 2),
                                round((table.bbox[2] / page_w) * 1000.0, 2),
                                round((table.bbox[3] / page_h) * 1000.0, 2),
                            ]
                            table_rects.append(table.bbox)
                            extracted_blocks.append(ExtractedBlock(
                                content=table_md,
                                page_number=page_num,
                                section_title=current_section or f"Table (Page {page_num})",
                                source_location=f"Page {page_num}, Table {t_idx + 1}",
                                bbox=t_bbox,
                                extraction_method=ExtractionMethod.NATIVE_TEXT,
                                is_table=True
                            ))
            except Exception:
                # Table finder optional/graceful fallback
                pass

            # 2. Extract Native Text Blocks
            page_text = page.get_text("text").strip()
            
            # Scanned page detection
            if len(page_text) < cls.MIN_NATIVE_TEXT_CHARS and enable_ocr:
                # Rasterize page to image and perform OCR
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                ocr_blocks, ocr_success = OCREngine.extract_from_image(img_bytes, page_number=page_num)
                if ocr_blocks:
                    extracted_blocks.extend(ocr_blocks)
                    any_ocr_applied = True
                continue

            # Native Text Extraction with block coordinates
            raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
            for block in raw_blocks:
                if len(block) >= 5 and block[6] == 0:  # text block
                    text_content = block[4].strip()
                    if not text_content:
                        continue

                    # Heading Detection heuristic (e.g. "# Section 3", "3.2 Wear Analysis")
                    first_line = text_content.split("\n")[0].strip()
                    if re.match(r"^(#+|[0-9]+(\.[0-9]+)*\s+[A-Z])", first_line) and len(first_line) < 80:
                        current_section = first_line

                    # Normalize bounding box to [0, 1000]
                    norm_bbox = [
                        round((block[0] / page_w) * 1000.0, 2),
                        round((block[1] / page_h) * 1000.0, 2),
                        round((block[2] / page_w) * 1000.0, 2),
                        round((block[3] / page_h) * 1000.0, 2),
                    ]

                    extracted_blocks.append(ExtractedBlock(
                        content=text_content,
                        page_number=page_num,
                        section_title=current_section,
                        source_location=f"Page {page_num}, Block {block[5]}",
                        bbox=norm_bbox,
                        extraction_method=ExtractionMethod.NATIVE_TEXT,
                        is_table=False
                    ))

        doc.close()

        source_type = SourceType.PDF_OCR if any_ocr_applied else SourceType.PDF_DIGITAL

        # Compute file stats
        size_bytes = filepath.stat().st_size if filepath.exists() else 0

        return ParsedDocument(
            filename=filename,
            mime_type="application/pdf",
            size_bytes=size_bytes,
            sha256_hash="",  # Populated by pipeline/validator
            page_count=page_count,
            ocr_applied=any_ocr_applied,
            source_type=source_type,
            blocks=extracted_blocks,
            metadata={"total_blocks": len(extracted_blocks)}
        )
