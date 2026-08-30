// frontend/src/api/audit.ts
import { request } from './client';
import { AuditEvent, AuditVerification } from '../types/audit';

export async function fetchAuditEvents(workspaceId?: string, limit: number = 50): Promise<AuditEvent[]> {
  const queryParam = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}&limit=${limit}` : `?limit=${limit}`;
  return request<AuditEvent[]>(`/audit${queryParam}`);
}

export async function verifyAuditLedger(): Promise<AuditVerification> {
  return request<AuditVerification>('/audit/verify', {
    method: 'POST',
  });
}
