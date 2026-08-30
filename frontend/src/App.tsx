// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { Layout } from './components/layout/Layout';
import { TabType } from './components/layout/Sidebar';
import { CommandCenter } from './pages/CommandCenter';
import { AIWorkspace } from './pages/AIWorkspace';
import { KnowledgeVault } from './pages/KnowledgeVault';
import { EvidenceViewer } from './pages/EvidenceViewer';
import { AuditMonitor } from './pages/AuditMonitor';
import { Workspace } from './types/workspace';
import { HardwareTelemetryResponse, ModelInfo } from './types/telemetry';
import { CitationReference } from './types/agent';
import { fetchHardwareTelemetry, fetchModelList } from './api/telemetry';
import { fetchWorkspaces } from './api/workspaces';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('command');
  const [telemetry, setTelemetry] = useState<HardwareTelemetryResponse | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  
  // Cross-page state for evidence viewer
  const [activeCitations, setActiveCitations] = useState<CitationReference[]>([]);
  const [summaryText, setSummaryText] = useState<string | null>(null);

  const loadTelemetry = async () => {
    try {
      const data = await fetchHardwareTelemetry();
      setTelemetry(data);
    } catch (err) {
      console.error('Failed to fetch telemetry:', err);
    }
  };

  const loadModels = async () => {
    try {
      const modelList = await fetchModelList();
      setModels(modelList);
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  };

  const loadWorkspaces = async () => {
    try {
      const list = await fetchWorkspaces();
      setWorkspaces(list);
      if (list.length > 0 && !activeWorkspace) {
        setActiveWorkspace(list[0]);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
    }
  };

  useEffect(() => {
    loadTelemetry();
    loadModels();
    loadWorkspaces();

    // 2-second background telemetry polling
    const interval = setInterval(() => {
      loadTelemetry();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleViewEvidence = (citations: CitationReference[], summary: string | null) => {
    setActiveCitations(citations);
    setSummaryText(summary);
    setActiveTab('evidence');
  };

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      telemetry={telemetry}
      workspaces={workspaces}
      activeWorkspace={activeWorkspace}
      onSelectWorkspace={setActiveWorkspace}
      onRefreshWorkspaces={loadWorkspaces}
      onRefreshTelemetry={loadTelemetry}
    >
      {activeTab === 'command' && (
        <CommandCenter
          telemetry={telemetry}
          models={models}
          workspaces={workspaces}
          activeWorkspace={activeWorkspace}
          onNavigateTab={setActiveTab}
          onRefreshTelemetry={loadTelemetry}
        />
      )}

      {activeTab === 'workspace' && (
        <AIWorkspace
          activeWorkspace={activeWorkspace}
          onViewEvidence={handleViewEvidence}
        />
      )}

      {activeTab === 'vault' && (
        <KnowledgeVault activeWorkspace={activeWorkspace} />
      )}

      {activeTab === 'evidence' && (
        <EvidenceViewer
          citations={activeCitations}
          summaryText={summaryText}
        />
      )}

      {activeTab === 'audit' && (
        <AuditMonitor activeWorkspace={activeWorkspace} />
      )}
    </Layout>
  );
}

export default App;
