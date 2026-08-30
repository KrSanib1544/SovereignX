// frontend/src/api/workspaces.ts
import { request } from './client';
import { Workspace, DocumentSummary, DocumentDetail, QueryResultItem } from '../types/workspace';

export async function fetchWorkspaces(): Promise<Workspace[]> {
  return request<Workspace[]>('/workspaces');
}

export async function createWorkspace(data: {
  name: string;
  description?: string;
  classification_level: string;
}): Promise<Workspace> {
  return request<Workspace>('/workspaces', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchWorkspace(workspaceId: string): Promise<Workspace> {
  return request<Workspace>(`/workspaces/${workspaceId}`);
}

export async function deleteWorkspace(workspaceId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/workspaces/${workspaceId}`, {
    method: 'DELETE',
  });
}

export async function uploadDocuments(
  workspaceId: string,
  files: File[],
  classification?: string,
  enableOcr: boolean = true
): Promise<{ workspace_id: string; ingested_count: number; documents: any[] }> {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  if (classification) {
    formData.append('classification', classification);
  }
  formData.append('enable_ocr', String(enableOcr));

  return request<{ workspace_id: string; ingested_count: number; documents: any[] }>(
    `/workspaces/${workspaceId}/documents`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

export async function fetchDocuments(workspaceId: string): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>(`/workspaces/${workspaceId}/documents`);
}

export async function fetchDocumentDetail(workspaceId: string, documentId: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/workspaces/${workspaceId}/documents/${documentId}`);
}

export async function queryKnowledgeVault(
  workspaceId: string,
  query: string,
  topK: number = 4,
  documentId?: string
): Promise<QueryResultItem[]> {
  return request<QueryResultItem[]>(`/workspaces/${workspaceId}/query`, {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK, document_id: documentId || null }),
  });
}

export function getArtifactDownloadUrl(workspaceId: string, filename: string): string {
  return `http://localhost:8000/api/v1/workspaces/${workspaceId}/artifacts/${encodeURIComponent(filename)}`;
}
