// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import {
  LayoutDashboard,
  Bot,
  Database,
  SplitSquareVertical,
  ShieldCheck,
  Terminal,
  Activity
} from 'lucide-react';

export type TabType = 'command' | 'workspace' | 'vault' | 'evidence' | 'audit';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const navItems: { id: TabType; label: string; icon: React.FC<{ className?: string }>; badge?: string }[] = [
    { id: 'command', label: 'Command Center', icon: LayoutDashboard },
    { id: 'workspace', label: 'AI Workspace', icon: Bot },
    { id: 'vault', label: 'Knowledge Vault', icon: Database },
    { id: 'evidence', label: 'Evidence Viewer', icon: SplitSquareVertical },
    { id: 'audit', label: 'Audit & Sovereignty', icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 bg-[#0B0F17] border-r border-gray-800 flex flex-col justify-between p-4 select-none shrink-0">
      <div className="space-y-6">
        <div className="px-2">
          <p className="text-[10px] font-mono font-bold text-gray-500 uppercase tracking-widest">
            Tactical Operations
          </p>
        </div>

        {/* Navigation List */}
        <nav className="space-y-1 font-mono text-xs">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all text-left group ${
                  isActive
                    ? 'bg-cyan-950/60 text-cyan-400 border border-cyan-700/50 shadow-sm shadow-cyan-900/20 font-semibold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#111827]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive ? 'text-cyan-400' : 'text-gray-500 group-hover:text-gray-300'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Runtime Invariant Box */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-3 space-y-2 font-mono text-[11px]">
        <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
          <Activity className="w-3.5 h-3.5" />
          <span>INVARIANTS ACTIVE</span>
        </div>
        <ul className="space-y-1 text-gray-400 text-[10px]">
          <li className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Docker Sandbox (--net none)</span>
          </li>
          <li className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>5-Stage Policy Gate</span>
          </li>
          <li className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Sequential VRAM Arbitrator</span>
          </li>
          <li className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>SHA-256 Audit Chain</span>
          </li>
        </ul>
      </div>
    </aside>
  );
};
