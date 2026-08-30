// frontend/src/types/workspace.ts

export type ClassificationLevel = 'PUBLIC' | 'INTERNAL_ENGINEERING' | 'RESTRICTED_CONFIDENTIAL';

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  classification_level: ClassificationLevel;
  storage_path: string;
  document_count: number;
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash: string;
  page_count: number;
  chunk_count: number;
  ocr_applied: boolean;
  parsing_status: 'PENDING' | 'PARSING' | 'INDEXED' | 'FAILED';
  created_at: string;
}

export interface ChunkDetail {
  chunk_id: string;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
  token_count: number;
  bbox_json: string | null;
  content_preview: string;
}

export interface DocumentDetail {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash: string;
  page_count: number;
  ocr_applied: boolean;
  parsing_status: string;
  chunks: ChunkDetail[];
}

export interface QueryResultItem {
  chunk_id: string;
  score: number;
  content: string;
  document_id: string;
  filename: string;
  page_number: number | null;
  section_title: string | null;
  classification: string | null;
}
