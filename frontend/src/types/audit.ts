// frontend/src/types/audit.ts

export interface AuditEvent {
  id: number;
  event_uuid: string;
  timestamp: string;
  actor: string;
  workspace_id: string | null;
  task_id: string | null;
  event_type: string;
  payload_json: string;
  client_ip: string | null;
  previous_hash: string;
  current_hash: string;
}

export interface AuditVerification {
  is_valid: boolean;
  total_events: number;
  error_reason: string | null;
  last_verified_hash: string | null;
}
