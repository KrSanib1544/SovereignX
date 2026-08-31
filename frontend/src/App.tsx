// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { Layout } from './components/layout/Layout';
import { TabType } from './components/layout/Sidebar';
import { CommandCenter } from './pages/CommandCenter';
import { AIWorkspace } from './pages/AIWorkspace';
import { KnowledgeVault } from './pages/KnowledgeVault';
import { EvidenceViewer } from './pages/EvidenceViewer';
import { AuditMonitor } from './pages/AuditMonitor';
import { Workspace, DocumentSummary } from './types/workspace';
import { HardwareTelemetryResponse, ModelInfo } from './types/telemetry';
import { CitationReference } from './types/agent';
import { fetchHardwareTelemetry, fetchModelList } from './api/telemetry';
import { fetchWorkspaces, fetchDocuments } from './api/workspaces';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('command');
  const [telemetry, setTelemetry] = useState<HardwareTelemetryResponse | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  
  // Scoped Document state
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<DocumentSummary | null>(null);

  // Document-scoped evidence state
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

  const loadWorkspaceDocuments = async (workspaceId: string, preferredDocId?: string | null) => {
    try {
      const docs = await fetchDocuments(workspaceId);
      setDocuments(docs);

      const targetDocId = preferredDocId || localStorage.getItem(`sovereign_selected_doc_${workspaceId}`);
      const matched = docs.find((d) => d.id === targetDocId) || (docs.length > 0 ? docs[0] : null);

      setSelectedDocument(matched);

      if (matched) {
        localStorage.setItem(`sovereign_selected_doc_${workspaceId}`, matched.id);
        // Load document-scoped evidence cache
        try {
          const cachedEvidence = localStorage.getItem(`sovereign_evidence_${workspaceId}_${matched.id}`);
          if (cachedEvidence) {
            const parsed = JSON.parse(cachedEvidence);
            setActiveCitations(parsed.citations || []);
            setSummaryText(parsed.summary || null);
          } else {
            setActiveCitations([]);
            setSummaryText(null);
          }
        } catch {
          setActiveCitations([]);
          setSummaryText(null);
        }
      } else {
        setActiveCitations([]);
        setSummaryText(null);
      }
    } catch (err) {
      console.error('Failed to fetch documents for workspace:', err);
      setDocuments([]);
      setSelectedDocument(null);
      setActiveCitations([]);
      setSummaryText(null);
    }
  };

  const loadWorkspaces = async () => {
    try {
      const list = await fetchWorkspaces();
      setWorkspaces(list);
      if (list.length > 0) {
        const savedId = localStorage.getItem('sovereign_active_workspace_id');
        const matched = list.find((w) => w.id === savedId) || list[0];
        setActiveWorkspace(matched);
        await loadWorkspaceDocuments(matched.id);
      }
    } catch (err) {
      console.error('Failed to fetch workspaces:', err);
    }
  };

  const handleSelectWorkspace = async (ws: Workspace) => {
    setActiveWorkspace(ws);
    try {
      localStorage.setItem('sovereign_active_workspace_id', ws.id);
    } catch {
      // Ignored
    }
    // Clear old workspace evidence immediately
    setActiveCitations([]);
    setSummaryText(null);
    await loadWorkspaceDocuments(ws.id);
  };

  const handleSelectDocument = (doc: DocumentSummary | null) => {
    setSelectedDocument(doc);
    // Clear old document evidence immediately
    setActiveCitations([]);
    setSummaryText(null);

    if (doc && activeWorkspace) {
      try {
        localStorage.setItem(`sovereign_selected_doc_${activeWorkspace.id}`, doc.id);
        const cachedEvidence = localStorage.getItem(`sovereign_evidence_${activeWorkspace.id}_${doc.id}`);
        if (cachedEvidence) {
          const parsed = JSON.parse(cachedEvidence);
          setActiveCitations(parsed.citations || []);
          setSummaryText(parsed.summary || null);
        }
      } catch {
        // Ignored
      }
    }
  };

  const handleUpdateEvidence = (
    citations: CitationReference[],
    summary: string | null,
    targetDocId?: string
  ) => {
    const docId = targetDocId || selectedDocument?.id;
    
    // Security check: Ensure citations are tagged with current workspace and document
    const securedCitations = citations.map((c) => ({
      ...c,
      workspace_id: activeWorkspace?.id || c.workspace_id,
      document_id: docId || c.document_id,
    }));

    setActiveCitations(securedCitations);
    setSummaryText(summary);

    if (activeWorkspace && docId) {
      try {
        localStorage.setItem(
          `sovereign_evidence_${activeWorkspace.id}_${docId}`,
          JSON.stringify({ citations: securedCitations, summary })
        );
      } catch {
        // Ignored
      }
    }
  };

  const handleViewEvidence = (
    citations: CitationReference[],
    summary: string | null,
    targetDocId?: string
  ) => {
    handleUpdateEvidence(citations, summary, targetDocId);
    setActiveTab('evidence');
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

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      telemetry={telemetry}
      workspaces={workspaces}
      activeWorkspace={activeWorkspace}
      onSelectWorkspace={handleSelectWorkspace}
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
          documents={documents}
          selectedDocument={selectedDocument}
          onSelectDocument={handleSelectDocument}
          onViewEvidence={handleViewEvidence}
          onUpdateEvidence={handleUpdateEvidence}
        />
      )}

      {activeTab === 'vault' && (
        <KnowledgeVault
          activeWorkspace={activeWorkspace}
          documents={documents}
          selectedDocument={selectedDocument}
          onSelectDocument={handleSelectDocument}
          onRefreshDocuments={() => activeWorkspace && loadWorkspaceDocuments(activeWorkspace.id)}
        />
      )}

      {activeTab === 'evidence' && (
        <EvidenceViewer
          citations={activeCitations}
          summaryText={summaryText}
          activeWorkspace={activeWorkspace}
          documents={documents}
          selectedDocument={selectedDocument}
          onSelectDocument={handleSelectDocument}
          onUpdateEvidence={handleUpdateEvidence}
          onNavigateTab={setActiveTab}
        />
      )}

      {activeTab === 'audit' && (
        <AuditMonitor activeWorkspace={activeWorkspace} />
      )}
    </Layout>
  );
}

export default App;
