# backend/app/ingestion/excel_parser.py
"""
Tabular Spreadsheet Ingestion Engine (XLSX, XLS)
Processes multi-sheet workbooks using openpyxl / pandas, generating
schema summaries and retrieval-optimized Markdown table blocks with row provenance.
"""

from pathlib import Path
from typing import List, Optional
import openpyxl
import pandas as pd

from backend.app.ingestion.models import (
    ParsedDocument,
    ExtractedBlock,
    SourceType,
    ExtractionMethod,
    df_to_clean_markdown,
)


class ExcelParser:
    """
    Parses multi-sheet Excel files into retrieval-friendly Markdown table blocks.
    """

    ROWS_PER_BLOCK: int = 20

    @classmethod
    def parse(
        cls,
        filepath: Path,
        filename_override: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse all sheets in an Excel workbook, preserving sheet names, columns, and row indices.
        """
        filename = filename_override or filepath.name
        excel_file = pd.ExcelFile(filepath, engine="openpyxl")
        sheet_names = excel_file.sheet_names

        extracted_blocks: List[ExtractedBlock] = []

        for sheet_idx, sheet_name in enumerate(sheet_names):
            page_num = sheet_idx + 1
            df = excel_file.parse(sheet_name)

            if df.empty:
                extracted_blocks.append(ExtractedBlock(
                    content=f"### Sheet: {sheet_name}\n[Empty Sheet]",
                    page_number=page_num,
                    section_title=f"Sheet: {sheet_name}",
                    source_location=f"Sheet: {sheet_name}",
                    extraction_method=ExtractionMethod.PANDAS_TABULAR,
                    is_table=True
                ))
                continue

            # 1. Schema & Summary Block
            columns_str = ", ".join([str(c) for c in df.columns])
            summary_content = (
                f"### Sheet: {sheet_name} (Schema Summary)\n"
                f"- **Columns ({len(df.columns)})**: {columns_str}\n"
                f"- **Total Rows**: {len(df)}\n"
            )
            extracted_blocks.append(ExtractedBlock(
                content=summary_content,
                page_number=page_num,
                section_title=f"Sheet: {sheet_name} Summary",
                source_location=f"Sheet: {sheet_name}, Summary",
                extraction_method=ExtractionMethod.PANDAS_TABULAR,
                is_table=True
            ))

            # 2. Segment Data Rows into Structured Markdown Table Blocks
            total_rows = len(df)
            for start_row in range(0, total_rows, cls.ROWS_PER_BLOCK):
                end_row = min(start_row + cls.ROWS_PER_BLOCK, total_rows)
                sub_df = df.iloc[start_row:end_row]

                # Convert subset to clean Markdown table
                table_md = (
                    f"### Sheet: {sheet_name} (Rows {start_row + 1} to {end_row})\n"
                    f"{df_to_clean_markdown(sub_df)}"
                )

                extracted_blocks.append(ExtractedBlock(
                    content=table_md,
                    page_number=page_num,
                    section_title=f"Sheet: {sheet_name}",
                    source_location=f"Sheet: {sheet_name}, Rows {start_row + 1}-{end_row}",
                    extraction_method=ExtractionMethod.PANDAS_TABULAR,
                    is_table=True
                ))

        size_bytes = filepath.stat().st_size if filepath.exists() else 0

        return ParsedDocument(
            filename=filename,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=size_bytes,
            sha256_hash="",
            page_count=len(sheet_names),
            ocr_applied=False,
            source_type=SourceType.SPREADSHEET,
            blocks=extracted_blocks,
            metadata={"sheet_count": len(sheet_names), "sheets": sheet_names}
        )
