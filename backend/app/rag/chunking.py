# backend/app/rag/chunking.py
"""
Hierarchical & Semantic Chunking Engine
Splits parsed documents into retrieval-optimized chunks while strictly preserving
structural section headers, table formats, and page-level provenance.
"""

from typing import List, Optional
from backend.app.ingestion.models import ParsedDocument, ExtractedBlock
from backend.app.rag.provenance import ChunkProvenance


def estimate_token_count(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters or ~0.75 words)."""
    words = len(text.split())
    return max(int(words * 1.3), 1)


class HierarchicalChunker:
    """
    Transforms ParsedDocument blocks into indexed ChunkProvenance units.
    """

    DEFAULT_CHUNK_SIZE: int = 1500   # ~350-400 tokens
    DEFAULT_OVERLAP: int = 250      # ~60 tokens

    @classmethod
    def chunk_document(
        cls,
        parsed_doc: ParsedDocument,
        document_id: str,
        workspace_id: str,
        classification: str = "INTERNAL_ENGINEERING",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_OVERLAP
    ) -> List[ChunkProvenance]:
        """
        Chunk a parsed document into a list of ChunkProvenance objects.
        """
        chunks: List[ChunkProvenance] = []
        chunk_idx = 0

        current_buffer: List[str] = []
        current_buffer_len: int = 0
        current_page: Optional[int] = None
        current_section: Optional[str] = None
        current_location: Optional[str] = None
        current_bbox: Optional[List[float]] = None

        for block in parsed_doc.blocks:
            # 1. If block is a table, flush current text buffer and emit table as standalone chunk
            if block.is_table:
                if current_buffer:
                    combined_text = "\n\n".join(current_buffer).strip()
                    if combined_text:
                        chunks.append(ChunkProvenance(
                            chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                            document_id=document_id,
                            workspace_id=workspace_id,
                            filename=parsed_doc.filename,
                            chunk_index=chunk_idx,
                            page_number=current_page,
                            section_title=current_section,
                            source_location=current_location,
                            bbox=current_bbox,
                            classification=classification,
                            is_table=False,
                            token_count=estimate_token_count(combined_text),
                            content=combined_text
                        ))
                        chunk_idx += 1
                    current_buffer = []
                    current_buffer_len = 0

                # Add table chunk directly
                chunks.append(ChunkProvenance(
                    chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                    document_id=document_id,
                    workspace_id=workspace_id,
                    filename=parsed_doc.filename,
                    chunk_index=chunk_idx,
                    page_number=block.page_number,
                    section_title=block.section_title,
                    source_location=block.source_location,
                    bbox=block.bbox,
                    classification=classification,
                    is_table=True,
                    token_count=estimate_token_count(block.content),
                    content=block.content
                ))
                chunk_idx += 1
                continue

            # 2. Large Block Splitting (> chunk_size)
            if len(block.content) > chunk_size:
                # Flush existing buffer first
                if current_buffer:
                    combined_text = "\n\n".join(current_buffer).strip()
                    if combined_text:
                        chunks.append(ChunkProvenance(
                            chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                            document_id=document_id,
                            workspace_id=workspace_id,
                            filename=parsed_doc.filename,
                            chunk_index=chunk_idx,
                            page_number=current_page,
                            section_title=current_section,
                            source_location=current_location,
                            bbox=current_bbox,
                            classification=classification,
                            is_table=False,
                            token_count=estimate_token_count(combined_text),
                            content=combined_text
                        ))
                        chunk_idx += 1
                    current_buffer = []
                    current_buffer_len = 0

                # Split large text with overlap
                text_to_split = block.content
                start_pos = 0
                while start_pos < len(text_to_split):
                    end_pos = min(start_pos + chunk_size, len(text_to_split))
                    
                    # Try to break on sentence boundary if not at end
                    if end_pos < len(text_to_split):
                        last_period = text_to_split.rfind(". ", start_pos, end_pos)
                        last_newline = text_to_split.rfind("\n", start_pos, end_pos)
                        split_break = max(last_period + 2 if last_period != -1 else -1, last_newline + 1 if last_newline != -1 else -1)
                        if split_break > start_pos + (chunk_size // 2):
                            end_pos = split_break

                    slice_text = text_to_split[start_pos:end_pos].strip()
                    if slice_text:
                        chunks.append(ChunkProvenance(
                            chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                            document_id=document_id,
                            workspace_id=workspace_id,
                            filename=parsed_doc.filename,
                            chunk_index=chunk_idx,
                            page_number=block.page_number,
                            section_title=block.section_title,
                            source_location=block.source_location,
                            bbox=block.bbox,
                            classification=classification,
                            is_table=False,
                            token_count=estimate_token_count(slice_text),
                            content=slice_text
                        ))
                        chunk_idx += 1

                    if end_pos >= len(text_to_split):
                        break
                    start_pos = end_pos - chunk_overlap
                continue

            # 3. Standard Text Block Accumulation
            # If section changed or adding block exceeds chunk_size, flush buffer
            if (current_buffer and (
                (block.section_title and block.section_title != current_section) or
                (current_buffer_len + len(block.content) > chunk_size)
            )):
                combined_text = "\n\n".join(current_buffer).strip()
                if combined_text:
                    chunks.append(ChunkProvenance(
                        chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                        document_id=document_id,
                        workspace_id=workspace_id,
                        filename=parsed_doc.filename,
                        chunk_index=chunk_idx,
                        page_number=current_page,
                        section_title=current_section,
                        source_location=current_location,
                        bbox=current_bbox,
                        classification=classification,
                        is_table=False,
                        token_count=estimate_token_count(combined_text),
                        content=combined_text
                    ))
                    chunk_idx += 1
                current_buffer = []
                current_buffer_len = 0

            # Set tracking metadata from first block in buffer
            if not current_buffer:
                current_page = block.page_number
                current_section = block.section_title
                current_location = block.source_location
                current_bbox = block.bbox

            current_buffer.append(block.content)
            current_buffer_len += len(block.content)

        # Flush any remaining buffer
        if current_buffer:
            combined_text = "\n\n".join(current_buffer).strip()
            if combined_text:
                chunks.append(ChunkProvenance(
                    chunk_id=f"chk_{document_id}_{chunk_idx:04d}",
                    document_id=document_id,
                    workspace_id=workspace_id,
                    filename=parsed_doc.filename,
                    chunk_index=chunk_idx,
                    page_number=current_page,
                    section_title=current_section,
                    source_location=current_location,
                    bbox=current_bbox,
                    classification=classification,
                    is_table=False,
                    token_count=estimate_token_count(combined_text),
                    content=combined_text
                ))

        return chunks
