// frontend/src/types/telemetry.ts

export interface AirGapTelemetry {
  is_isolated: boolean;
  active_interfaces: string[];
  external_dns_reachable: boolean;
  wan_bytes_transmitted: number;
}

export interface GpuTelemetry {
  available: boolean;
  device_name: string;
  vram_total_mb: number;
  vram_used_mb: number;
  vram_free_mb: number;
  vram_utilization_pct: number;
  gpu_utilization_pct: number;
  temperature_c: number;
}

export interface SystemTelemetry {
  ram_total_mb: number;
  ram_used_mb: number;
  ram_free_mb: number;
  ram_utilization_pct: number;
  cpu_core_count: number;
  cpu_utilization_pct: number;
}

export interface ActiveModelTelemetry {
  model_id: string;
  status: string;
  vram_allocated_mb: number;
}

export interface HardwareTelemetryResponse {
  timestamp: string;
  airgap_status: AirGapTelemetry;
  hardware: {
    gpu: GpuTelemetry;
    ram: {
      total_mb: number;
      used_mb: number;
      free_mb: number;
      system_utilization_pct: number;
    };
    cpu: {
      core_count: number;
      utilization_pct: number;
    };
  };
  active_model: ActiveModelTelemetry;
}

export interface ModelInfo {
  model_id: string;
  name: string;
  description: string;
  parameter_size: string;
  quantization: string;
  vram_required_mb: number;
  context_window: number;
  is_multimodal: boolean;
  is_loaded: boolean;
}
