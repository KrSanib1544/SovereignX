// frontend/src/api/telemetry.ts
import { request } from './client';
import { HardwareTelemetryResponse, ModelInfo } from '../types/telemetry';

export async function fetchHardwareTelemetry(): Promise<HardwareTelemetryResponse> {
  return request<HardwareTelemetryResponse>('/telemetry');
}

export async function fetchSystemHealth(): Promise<{ status: string; airgap_verified: boolean; timestamp: string }> {
  return request<{ status: string; airgap_verified: boolean; timestamp: string }>('/health');
}

export async function fetchModelList(): Promise<ModelInfo[]> {
  return request<ModelInfo[]>('/models');
}

export async function swapActiveModel(modelId: string): Promise<{ status: string; active_model: string; message: string }> {
  return request<{ status: string; active_model: string; message: string }>('/models/swap', {
    method: 'POST',
    body: JSON.stringify({ target_model_id: modelId }),
  });
}
