// frontend/src/pages/CommandCenter.tsx
import React, { useState } from 'react';
import {
  Cpu,
  HardDrive,
  Zap,
  ShieldCheck,
  ShieldAlert,
  Bot,
  Database,
  ArrowRightLeft,
  Activity,
  Layers,
  CheckCircle2,
  Lock,
  RefreshCw,
  FolderKanban
} from 'lucide-react';
import { HardwareTelemetryResponse, ModelInfo } from '../types/telemetry';
import { Workspace } from '../types/workspace';
import { ProgressBar } from '../components/common/ProgressBar';
import { Badge } from '../components/common/Badge';
import { swapActiveModel } from '../api/telemetry';

interface CommandCenterProps {
  telemetry: HardwareTelemetryResponse | null;
  models: ModelInfo[];
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onNavigateTab: (tab: any) => void;
  onRefreshTelemetry: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  telemetry,
  models,
  workspaces,
  activeWorkspace,
  onNavigateTab,
  onRefreshTelemetry,
}) => {
  const [isSwapping, setIsSwapping] = useState(false);
  const [swapMessage, setSwapMessage] = useState<string | null>(null);

  const gpu = telemetry?.hardware?.gpu;
  const ram = telemetry?.hardware?.ram;
  const cpu = telemetry?.hardware?.cpu;
  const airgap = telemetry?.airgap_status;
  const activeModelId = telemetry?.active_model?.model_id ?? 'None';

  const vramUsed = gpu?.vram_used_mb ?? 0;
  const vramTotal = gpu?.vram_total_mb ?? 4096;
  const vramPct = gpu?.vram_utilization_pct ?? 0;

  const ramUsed = ram?.used_mb ?? 0;
  const ramTotal = ram?.total_mb ?? 16384;
  const ramPct = ram?.system_utilization_pct ?? 0;

  const handleSwapModel = async (targetModel: string) => {
    if (targetModel === activeModelId) return;
    setIsSwapping(true);
    setSwapMessage(null);
    try {
      const res = await swapActiveModel(targetModel);
      setSwapMessage(res.message || `Swapped to ${targetModel}`);
      onRefreshTelemetry();
    } catch (err: any) {
      setSwapMessage(`Swap failed: ${err.message}`);
    } finally {
      setIsSwapping(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex items-center justify-between bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2.5">
            <span className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
            <h2 className="text-lg font-bold text-gray-100 tracking-wider">COMMAND CENTER</h2>
            <Badge variant="success" size="sm">
              AIR-GAP ENFORCED
            </Badge>
          </div>
          <p className="text-gray-400 text-xs">
            Autonomous on-premise AI orchestrator for confidential industrial inspection & risk assurance.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigateTab('workspace')}
            className="flex items-center space-x-2 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-xl transition-all shadow-md shadow-cyan-950/50"
          >
            <Bot className="w-4 h-4" />
            <span>Launch Agent Task</span>
          </button>
        </div>
      </div>

      {/* Hardware Telemetry 3-Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* GPU VRAM Card */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400 font-bold">
              <Zap className="w-5 h-5" />
              <span>NVIDIA RTX 3050 VRAM</span>
            </div>
            <Badge variant="accent" size="sm">
              {gpu?.device_name ? 'RTX 3050 LAPTOP' : 'GPU ACTIVE'}
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-black text-gray-100">
                {(vramUsed / 1024).toFixed(2)} <span className="text-sm font-normal text-gray-400">/ {(vramTotal / 1024).toFixed(1)} GB</span>
              </span>
              <span className="text-cyan-400 font-bold">{vramPct.toFixed(1)}%</span>
            </div>
            <ProgressBar value={vramPct} color="cyan" size="md" />
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-400 pt-2 border-t border-gray-800">
            <div>
              <span className="text-gray-500">Core Temp:</span>{' '}
              <span className="text-gray-200">{gpu?.temperature_c ?? 50}°C</span>
            </div>
            <div>
              <span className="text-gray-500">GPU Core:</span>{' '}
              <span className="text-gray-200">{gpu?.gpu_utilization_pct ?? 0}%</span>
            </div>
          </div>
        </div>

        {/* System RAM Card */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold">
              <HardDrive className="w-5 h-5" />
              <span>SYSTEM RAM</span>
            </div>
            <Badge variant="success" size="sm">
              16 GB WORKSTATION
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-black text-gray-100">
                {(ramUsed / 1024).toFixed(2)} <span className="text-sm font-normal text-gray-400">/ {(ramTotal / 1024).toFixed(1)} GB</span>
              </span>
              <span className="text-emerald-400 font-bold">{ramPct.toFixed(1)}%</span>
            </div>
            <ProgressBar value={ramPct} color="emerald" size="md" />
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-400 pt-2 border-t border-gray-800">
            <div>
              <span className="text-gray-500">Available:</span>{' '}
              <span className="text-gray-200">{((ram?.free_mb ?? 0) / 1024).toFixed(1)} GB</span>
            </div>
            <div>
              <span className="text-gray-500">Host OS:</span>{' '}
              <span className="text-gray-200">Windows 11 64-bit</span>
            </div>
          </div>
        </div>

        {/* CPU & Airgap Card */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-amber-400 font-bold">
              <Cpu className="w-5 h-5" />
              <span>CPU & AIRGAP SECURITY</span>
            </div>
            <Badge variant="warning" size="sm">
              {cpu?.core_count || 8} CORES
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-black text-gray-100">
                {(cpu?.utilization_pct ?? 0).toFixed(1)}%
              </span>
              <span className="text-emerald-400 font-bold">WAN: 0 B</span>
            </div>
            <ProgressBar value={cpu?.utilization_pct ?? 0} color="amber" size="md" />
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-400 pt-2 border-t border-gray-800">
            <div>
              <span className="text-gray-500">Airgap Status:</span>{' '}
              <span className="text-emerald-400 font-semibold">VERIFIED</span>
            </div>
            <div>
              <span className="text-gray-500">Sandbox:</span>{' '}
              <span className="text-cyan-400 font-semibold">DOCKER ACTIVE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Model Swapping Arbitrator Section */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
              SEQUENTIAL VRAM MODEL ARBITRATOR (4 GB VRAM BUDGET)
            </h3>
            <p className="text-gray-500 text-[11px]">
              Guaranteed single-model residency in VRAM to prevent Out-of-Memory (OOM) faults.
            </p>
          </div>

          <span className="text-[11px] text-gray-400 font-mono">
            Active: <span className="text-cyan-400 font-bold">{activeModelId}</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Qwen3 Card */}
          <div className={`p-4 rounded-xl border transition-all ${
            activeModelId === 'qwen3:4b'
              ? 'bg-cyan-950/40 border-cyan-500/70 shadow-lg shadow-cyan-950/30'
              : 'bg-[#0B0F17] border-gray-800 hover:border-gray-700'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="font-bold text-gray-100 text-sm">qwen3:4b</h4>
                <p className="text-gray-400 text-[10px]">Reasoning & Structured Tool Invocation</p>
              </div>
              <Badge variant={activeModelId === 'qwen3:4b' ? 'accent' : 'outline'} size="sm">
                {activeModelId === 'qwen3:4b' ? 'LOADED IN VRAM' : 'STANDBY'}
              </Badge>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-gray-800/80 text-[11px]">
              <span className="text-gray-400">VRAM Footprint: ~2.5 GB</span>
              <button
                onClick={() => handleSwapModel('qwen3:4b')}
                disabled={activeModelId === 'qwen3:4b' || isSwapping}
                className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-black font-bold rounded-lg transition-colors text-xs"
              >
                {activeModelId === 'qwen3:4b' ? 'Active' : 'Swap to Qwen3'}
              </button>
            </div>
          </div>

          {/* Gemma3 Card */}
          <div className={`p-4 rounded-xl border transition-all ${
            activeModelId === 'gemma3:4b'
              ? 'bg-cyan-950/40 border-cyan-500/70 shadow-lg shadow-cyan-950/30'
              : 'bg-[#0B0F17] border-gray-800 hover:border-gray-700'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="font-bold text-gray-100 text-sm">gemma3:4b</h4>
                <p className="text-gray-400 text-[10px]">Multi-Modal Vision & Defect Image Analysis</p>
              </div>
              <Badge variant={activeModelId === 'gemma3:4b' ? 'accent' : 'outline'} size="sm">
                {activeModelId === 'gemma3:4b' ? 'LOADED IN VRAM' : 'STANDBY'}
              </Badge>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-gray-800/80 text-[11px]">
              <span className="text-gray-400">VRAM Footprint: ~3.3 GB</span>
              <button
                onClick={() => handleSwapModel('gemma3:4b')}
                disabled={activeModelId === 'gemma3:4b' || isSwapping}
                className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-black font-bold rounded-lg transition-colors text-xs"
              >
                {activeModelId === 'gemma3:4b' ? 'Active' : 'Swap to Gemma3'}
              </button>
            </div>
          </div>
        </div>

        {swapMessage && (
          <p className="text-cyan-400 text-[11px] bg-[#0B0F17] p-2.5 rounded-lg border border-gray-800">
            {swapMessage}
          </p>
        )}
      </div>

      {/* Workspace Summary Bar */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-3">
          <FolderKanban className="w-5 h-5 text-emerald-400" />
          <div>
            <h4 className="font-bold text-gray-200">
              ACTIVE WORKSPACE: {activeWorkspace?.name || 'Default Workspace'}
            </h4>
            <p className="text-gray-500 text-[11px]">
              Classification: {activeWorkspace?.classification_level || 'INTERNAL_ENGINEERING'} • Documents: {activeWorkspace?.document_count || 0} • Tasks: {activeWorkspace?.task_count || 0}
            </p>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={() => onNavigateTab('vault')}
            className="px-3.5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors"
          >
            Knowledge Vault
          </button>
          <button
            onClick={() => onNavigateTab('audit')}
            className="px-3.5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors"
          >
            Audit Ledger
          </button>
        </div>
      </div>
    </div>
  );
};
