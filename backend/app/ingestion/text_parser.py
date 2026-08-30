# backend/app/ingestion/text_parser.py
"""
Plain Text and CSV Ingestion Engine
Parses UTF-8 text documents and comma-separated value tables into structured blocks.
"""

from pathlib import Path
from typing import List, Optional
import pandas as pd

from backend.app.ingestion.models import (
    ParsedDocument,
    ExtractedBlock,
    SourceType,
    ExtractionMethod,
    df_to_clean_markdown,
)


class TextAndCSVParser:
    """
    Parses UTF-8 plain text files and CSV tables.
    """

    ROWS_PER_CSV_BLOCK: int = 25

    @classmethod
    def parse_csv(
        cls,
        filepath: Path,
        filename_override: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse CSV into schema summary and row-partitioned Markdown table blocks.
        """
        filename = filename_override or filepath.name
        df = pd.read_csv(filepath)

        extracted_blocks: List[ExtractedBlock] = []

        # 1. Schema Block
        columns_str = ", ".join([str(c) for c in df.columns])
        summary = (
            f"### CSV File: {filename} (Schema Summary)\n"
            f"- **Columns ({len(df.columns)})**: {columns_str}\n"
            f"- **Total Rows**: {len(df)}\n"
        )
        extracted_blocks.append(ExtractedBlock(
            content=summary,
            page_number=1,
            section_title="CSV Schema Summary",
            source_location="Header",
            extraction_method=ExtractionMethod.PANDAS_TABULAR,
            is_table=True
        ))

        # 2. Segment Data Rows
        total_rows = len(df)
        for start_row in range(0, total_rows, cls.ROWS_PER_CSV_BLOCK):
            end_row = min(start_row + cls.ROWS_PER_CSV_BLOCK, total_rows)
            sub_df = df.iloc[start_row:end_row]

            table_md = (
                f"### {filename} (Rows {start_row + 1} to {end_row})\n"
                f"{df_to_clean_markdown(sub_df)}"
            )

            extracted_blocks.append(ExtractedBlock(
                content=table_md,
                page_number=1,
                section_title=f"Rows {start_row + 1}-{end_row}",
                source_location=f"Rows {start_row + 1}-{end_row}",
                extraction_method=ExtractionMethod.PANDAS_TABULAR,
                is_table=True
            ))

        size_bytes = filepath.stat().st_size if filepath.exists() else 0

        return ParsedDocument(
            filename=filename,
            mime_type="text/csv",
            size_bytes=size_bytes,
            sha256_hash="",
            page_count=1,
            ocr_applied=False,
            source_type=SourceType.CSV,
            blocks=extracted_blocks,
            metadata={"row_count": total_rows, "columns": list(df.columns)}
        )

    @classmethod
    def parse_txt(
        cls,
        filepath: Path,
        filename_override: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse UTF-8 plain text file, splitting by double newlines or section headings.
        """
        filename = filename_override or filepath.name
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        extracted_blocks: List[ExtractedBlock] = []

        current_section = "General"
        for idx, para in enumerate(paragraphs):
            if para.startswith("#"):
                current_section = para.split("\n")[0].strip()

            extracted_blocks.append(ExtractedBlock(
                content=para,
                page_number=1,
                section_title=current_section,
                source_location=f"Paragraph {idx + 1}",
                extraction_method=ExtractionMethod.PLAIN_TEXT,
                is_table=False
            ))

        size_bytes = filepath.stat().st_size if filepath.exists() else 0

        return ParsedDocument(
            filename=filename,
            mime_type="text/plain",
            size_bytes=size_bytes,
            sha256_hash="",
            page_count=1,
            ocr_applied=False,
            source_type=SourceType.TEXT,
            blocks=extracted_blocks,
            metadata={"paragraph_count": len(paragraphs)}
        )
