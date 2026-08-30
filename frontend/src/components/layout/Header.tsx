// frontend/src/components/layout/Header.tsx
import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Cpu, FolderKanban, Plus, Layers, RefreshCw } from 'lucide-react';
import { Workspace } from '../../types/workspace';
import { HardwareTelemetryResponse } from '../../types/telemetry';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { createWorkspace } from '../../api/workspaces';

interface HeaderProps {
  telemetry: HardwareTelemetryResponse | null;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onRefreshWorkspaces: () => void;
  onRefreshTelemetry: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  telemetry,
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onRefreshWorkspaces,
  onRefreshTelemetry,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');
  const [newWsClass, setNewWsClass] = useState('INTERNAL_ENGINEERING');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    try {
      setIsSubmitting(true);
      const created = await createWorkspace({
        name: newWsName,
        description: newWsDesc,
        classification_level: newWsClass,
      });
      onRefreshWorkspaces();
      onSelectWorkspace(created);
      setIsModalOpen(false);
      setNewWsName('');
      setNewWsDesc('');
    } catch (err: any) {
      alert(`Failed to create workspace: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isAirGapped = telemetry?.airgap_status?.is_isolated ?? true;
  const activeModel = telemetry?.active_model?.model_id ?? 'None';
  const vramUsed = telemetry?.hardware?.gpu?.vram_used_mb ?? 0;
  const vramTotal = telemetry?.hardware?.gpu?.vram_total_mb ?? 4096;

  return (
    <header className="h-16 bg-[#0B0F17] border-b border-gray-800 px-6 flex items-center justify-between select-none">
      {/* Brand & Airgap Indicator */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-emerald-500 flex items-center justify-center font-black text-black text-sm tracking-tighter">
            SX
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-gray-100 font-mono flex items-center gap-1.5">
              SOVEREIGN-X
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-700/50">
                v0.4.0
              </span>
            </h1>
            <p className="text-[10px] text-gray-400 font-mono">CONFIDENTIAL AGENT RUNTIME</p>
          </div>
        </div>

        <div className="h-5 w-px bg-gray-800" />

        {/* Airgap Status LED */}
        <div className="flex items-center space-x-2 bg-[#111827] px-3 py-1 rounded-full border border-gray-800">
          <div className={`w-2.5 h-2.5 rounded-full ${isAirGapped ? 'bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/80' : 'bg-rose-500 shadow-sm shadow-rose-500/80'}`} />
          <span className="text-xs font-mono font-medium text-gray-300">
            {isAirGapped ? 'AIR-GAPPED (ZERO EGRESS)' : 'NETWORK DETECTED'}
          </span>
          {isAirGapped ? (
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 ml-1" />
          ) : (
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 ml-1" />
          )}
        </div>
      </div>

      {/* Model & Workspace Cockpit Selectors */}
      <div className="flex items-center space-x-4">
        {/* Active Local Model Badge */}
        <div className="flex items-center space-x-2 bg-[#111827] px-3 py-1.5 rounded-lg border border-gray-800 text-xs font-mono">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span className="text-gray-400">Model:</span>
          <span className="text-cyan-300 font-semibold">{activeModel}</span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-300">{(vramUsed / 1024).toFixed(1)} / {(vramTotal / 1024).toFixed(1)} GB VRAM</span>
        </div>

        {/* Workspace Dropdown */}
        <div className="flex items-center space-x-2 bg-[#111827] px-3 py-1.5 rounded-lg border border-gray-800 text-xs font-mono">
          <FolderKanban className="w-4 h-4 text-emerald-400" />
          <span className="text-gray-400">Workspace:</span>
          <select
            value={activeWorkspace?.id || ''}
            onChange={(e) => {
              const ws = workspaces.find((w) => w.id === e.target.value);
              if (ws) onSelectWorkspace(ws);
            }}
            className="bg-transparent text-emerald-300 font-medium focus:outline-none cursor-pointer"
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id} className="bg-[#111827] text-gray-200">
                {ws.name} ({ws.classification_level})
              </option>
            ))}
          </select>
          <button
            onClick={() => setIsModalOpen(true)}
            className="ml-1 p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-cyan-400 transition-colors"
            title="Create New Workspace"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>

        <button
          onClick={() => {
            onRefreshTelemetry();
            onRefreshWorkspaces();
          }}
          className="p-2 bg-[#111827] hover:bg-gray-800 border border-gray-800 rounded-lg text-gray-400 hover:text-gray-200 transition-colors"
          title="Refresh All State"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* New Workspace Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="CREATE ISOLATED WORKSPACE"
      >
        <form onSubmit={handleCreateWorkspace} className="space-y-4 font-mono text-xs">
          <div>
            <label className="block text-gray-300 mb-1 font-medium">Workspace Name *</label>
            <input
              type="text"
              required
              value={newWsName}
              onChange={(e) => setNewWsName(e.target.value)}
              placeholder="e.g., Reflux Pump 3B Inspection"
              className="w-full bg-[#0B0F17] border border-gray-700 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 font-medium">Description</label>
            <textarea
              value={newWsDesc}
              onChange={(e) => setNewWsDesc(e.target.value)}
              rows={2}
              placeholder="Confidential engineering inspection logs and tolerance analysis..."
              className="w-full bg-[#0B0F17] border border-gray-700 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 font-medium">Data Classification Level *</label>
            <select
              value={newWsClass}
              onChange={(e) => setNewWsClass(e.target.value)}
              className="w-full bg-[#0B0F17] border border-gray-700 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-cyan-500 cursor-pointer"
            >
              <option value="INTERNAL_ENGINEERING">INTERNAL_ENGINEERING (Standard Confidential)</option>
              <option value="RESTRICTED_CONFIDENTIAL">RESTRICTED_CONFIDENTIAL (High Assurance Isolated)</option>
              <option value="PUBLIC">PUBLIC (Unclassified / General)</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-black font-semibold rounded-lg transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Create Workspace'}
            </button>
          </div>
        </form>
      </Modal>
    </header>
  );
};
