// frontend/src/components/layout/TelemetryBar.tsx
import React from 'react';
import { Cpu, HardDrive, Zap, GlobeLock } from 'lucide-react';
import { HardwareTelemetryResponse } from '../../types/telemetry';
import { ProgressBar } from '../common/ProgressBar';

interface TelemetryBarProps {
  telemetry: HardwareTelemetryResponse | null;
}

export const TelemetryBar: React.FC<TelemetryBarProps> = ({ telemetry }) => {
  const gpu = telemetry?.hardware?.gpu;
  const ram = telemetry?.hardware?.ram;
  const cpu = telemetry?.hardware?.cpu;
  const airgap = telemetry?.airgap_status;

  const vramUsed = gpu?.vram_used_mb ?? 0;
  const vramTotal = gpu?.vram_total_mb ?? 4096;
  const vramPct = gpu?.vram_utilization_pct ?? 0;

  const ramUsed = ram?.used_mb ?? 0;
  const ramTotal = ram?.total_mb ?? 16384;
  const ramPct = ram?.system_utilization_pct ?? 0;

  const cpuPct = cpu?.utilization_pct ?? 0;

  return (
    <footer className="h-14 bg-[#0B0F17] border-t border-gray-800 px-6 flex items-center justify-between font-mono text-xs select-none shrink-0">
      {/* GPU VRAM Gauge */}
      <div className="flex items-center space-x-3 w-64">
        <Zap className="w-4 h-4 text-cyan-400 shrink-0" />
        <div className="w-full">
          <ProgressBar
            value={vramPct}
            label={`RTX 3050 VRAM: ${(vramUsed / 1024).toFixed(1)} / ${(vramTotal / 1024).toFixed(1)} GB`}
            sublabel={`${vramPct.toFixed(0)}%`}
            color="cyan"
            size="sm"
          />
        </div>
      </div>

      <div className="h-4 w-px bg-gray-800" />

      {/* System RAM Gauge */}
      <div className="flex items-center space-x-3 w-64">
        <HardDrive className="w-4 h-4 text-emerald-400 shrink-0" />
        <div className="w-full">
          <ProgressBar
            value={ramPct}
            label={`RAM: ${(ramUsed / 1024).toFixed(1)} / ${(ramTotal / 1024).toFixed(1)} GB`}
            sublabel={`${ramPct.toFixed(0)}%`}
            color="emerald"
            size="sm"
          />
        </div>
      </div>

      <div className="h-4 w-px bg-gray-800" />

      {/* CPU Gauge */}
      <div className="flex items-center space-x-3 w-52">
        <Cpu className="w-4 h-4 text-amber-400 shrink-0" />
        <div className="w-full">
          <ProgressBar
            value={cpuPct}
            label={`CPU (${cpu?.core_count || 8} Cores)`}
            sublabel={`${cpuPct.toFixed(1)}%`}
            color="amber"
            size="sm"
          />
        </div>
      </div>

      <div className="h-4 w-px bg-gray-800" />

      {/* Airgap Egress Counter */}
      <div className="flex items-center space-x-2 text-gray-400">
        <GlobeLock className="w-4 h-4 text-emerald-400" />
        <span>WAN EGRESS:</span>
        <span className="text-emerald-400 font-semibold">{airgap?.wan_bytes_transmitted ?? 0} B</span>
        <span className="text-gray-600">|</span>
        <span className="text-gray-500">{airgap?.external_dns_reachable ? 'DNS REACHABLE' : 'DNS UNREACHABLE (SECURE)'}</span>
      </div>
    </footer>
  );
};
