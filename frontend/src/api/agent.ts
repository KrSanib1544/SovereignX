// frontend/src/api/agent.ts
import { request } from './client';
import { AgentTaskResult } from '../types/agent';

export async function createAgentTask(
  workspaceId: string,
  prompt: string,
  autoApproveHighRisk: boolean = false
): Promise<AgentTaskResult> {
  return request<AgentTaskResult>(`/workspaces/${workspaceId}/tasks`, {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      auto_approve_high_risk: autoApproveHighRisk,
    }),
  });
}

export async function getTaskDetails(workspaceId: string, taskId: string): Promise<any> {
  return request<any>(`/workspaces/${workspaceId}/tasks/${taskId}`);
}

export async function approveTaskAction(
  workspaceId: string,
  taskId: string,
  approved: boolean,
  toolName: string,
  argumentsPayload: Record<string, any>
): Promise<AgentTaskResult> {
  return request<AgentTaskResult>(`/workspaces/${workspaceId}/tasks/${taskId}/approve`, {
    method: 'POST',
    body: JSON.stringify({
      approved,
      tool_name: toolName,
      arguments: argumentsPayload,
    }),
  });
}
