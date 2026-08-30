// frontend/src/types/agent.ts

export type AgentStatus = 'IDLE' | 'PLANNING' | 'ACTING' | 'TOOL_EXECUTION' | 'OBSERVATION' | 'WAITING_APPROVAL' | 'COMPLETED' | 'FAILED' | 'TIMED_OUT' | 'BUDGET_EXHAUSTED';
export type ToolRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type PolicyDecision = 'ALLOW' | 'DENY' | 'REQUIRE_APPROVAL';

export interface StepRecord {
  step_number: number;
  thought: string;
  tool_name: string | null;
  tool_arguments: Record<string, any> | null;
  tool_risk_level?: ToolRiskLevel | null;
  policy_decision: string | null;
  policy_reason?: string | null;
  observation: string | null;
  model_used?: string | null;
  duration_ms: number;
  status: string;
}

export interface CitationReference {
  citation_id: string;
  document_name: string;
  page_number?: number | null;
  section?: string | null;
  excerpt: string;
  bbox?: number[] | null;
}

export interface GeneratedArtifact {
  id?: string;
  filename: string;
  size_bytes?: number;
  sha256_hash?: string;
}

export interface PendingApproval {
  tool_name: string;
  arguments: Record<string, any>;
  risk_level: string;
  reason: string;
}

export interface AgentTaskResult {
  task_id: string;
  workspace_id: string;
  state: AgentStatus;
  prompt: string;
  final_answer: string | null;
  steps: StepRecord[];
  pending_approval: PendingApproval | null;
  citations?: CitationReference[];
  artifacts?: GeneratedArtifact[];
  total_steps: number;
  total_duration_ms: number;
  error: string | null;
}
