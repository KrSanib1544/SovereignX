// frontend/src/components/layout/Layout.tsx
import React from 'react';
import { Header } from './Header';
import { Sidebar, TabType } from './Sidebar';
import { TelemetryBar } from './TelemetryBar';
import { Workspace } from '../../types/workspace';
import { HardwareTelemetryResponse } from '../../types/telemetry';

interface LayoutProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  telemetry: HardwareTelemetryResponse | null;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onRefreshWorkspaces: () => void;
  onRefreshTelemetry: () => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  activeTab,
  onTabChange,
  telemetry,
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onRefreshWorkspaces,
  onRefreshTelemetry,
  children,
}) => {
  return (
    <div className="flex flex-col h-screen w-screen bg-[#0B0F17] text-gray-100 overflow-hidden">
      {/* Top Header */}
      <Header
        telemetry={telemetry}
        workspaces={workspaces}
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={onSelectWorkspace}
        onRefreshWorkspaces={onRefreshWorkspaces}
        onRefreshTelemetry={onRefreshTelemetry}
      />

      {/* Main Workspace Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar activeTab={activeTab} onTabChange={onTabChange} />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0B0F17] relative">
          {children}
        </main>
      </div>

      {/* Bottom Telemetry Bar */}
      <TelemetryBar telemetry={telemetry} />
    </div>
  );
};
