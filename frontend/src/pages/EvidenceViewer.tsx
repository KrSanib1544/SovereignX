// frontend/src/pages/EvidenceViewer.tsx
import React, { useState } from 'react';
import { SplitSquareVertical, Sparkles, FileText, Search, RefreshCw, Loader2, ChevronDown } from 'lucide-react';
import { CitationReference } from '../types/agent';
import { Workspace, DocumentSummary } from '../types/workspace';
import { SplitScreenViewer } from '../components/evidence/SplitScreenViewer';
import { queryKnowledgeVault } from '../api/workspaces';

interface EvidenceViewerProps {
  citations: CitationReference[];
  summaryText: string | null;
  activeWorkspace: Workspace | null;
  documents: DocumentSummary[];
  selectedDocument: DocumentSummary | null;
  onSelectDocument: (doc: DocumentSummary | null) => void;
  onUpdateEvidence?: (citations: CitationReference[], summary: string | null, targetDocId?: string) => void;
  onNavigateTab?: (tab: any) => void;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  citations,
  summaryText,
  activeWorkspace,
  documents,
  selectedDocument,
  onSelectDocument,
  onUpdateEvidence,
  onNavigateTab,
}) => {
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  const handleExtractEvidence = async () => {
    if (!activeWorkspace) {
      setExtractError('No active workspace selected.');
      return;
    }
    if (!selectedDocument) {
      setExtractError('No document selected. Select a document from Knowledge Vault to view evidence.');
      return;
    }
    if (selectedDocument.chunk_count === 0) {
      setExtractError('No indexed evidence available for this document.');
      return;
    }

    setIsExtracting(true);
    setExtractError(null);

    try {
      // Query specifically scoped to selectedDocument.id
      const hits = await queryKnowledgeVault(
        activeWorkspace.id,
        'engineering findings measurements inspection summary parameters',
        5,
        selectedDocument.id
      );

      // Verify that all returned chunks belong to the selected document
      const matchingHits = hits.filter(
        (h) => !h.document_id || h.document_id === selectedDocument.id
      );

      if (matchingHits.length === 0) {
        setExtractError('No indexed evidence available for this document.');
        onUpdateEvidence?.([], null, selectedDocument.id);
        return;
      }

      const extractedCitations: CitationReference[] = matchingHits.map((h, idx) => {
        return {
          citation_id: `CIT-${String(idx + 1).padStart(2, '0')}`,
          workspace_id: activeWorkspace.id,
          document_id: selectedDocument.id,
          document_name: selectedDocument.filename,
          chunk_id: h.chunk_id,
          page_number: h.page_number,
          section: h.section_title || 'General',
          excerpt: h.content,
          bbox: null,
        };
      });

      const topChunk = matchingHits[0].content;
      const synthesizedSummary = `Extracted from ${selectedDocument.filename} (Page ${matchingHits[0].page_number ?? 1}): ${topChunk.slice(0, 300)}...`;

      onUpdateEvidence?.(extractedCitations, synthesizedSummary, selectedDocument.id);
    } catch (err: any) {
      setExtractError(err.message || 'Evidence extraction failed.');
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs max-w-7xl mx-auto pb-8">
      {/* Top Banner & Document Selector */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
              <SplitSquareVertical className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-100">SIDE-BY-SIDE EVIDENCE & PROVENANCE VIEWER</h2>
              <p className="text-gray-400 text-[11px]">
                Verifiable assertion matching with document page coordinates and OCR bounding boxes.
              </p>
            </div>
          </div>

          {/* Extract Evidence Action Button */}
          {selectedDocument && selectedDocument.chunk_count > 0 && (
            <button
              onClick={handleExtractEvidence}
              disabled={isExtracting}
              className="flex items-center space-x-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-xl transition-all shadow-md shadow-cyan-950/50 disabled:opacity-50"
            >
              {isExtracting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              <span>Extract Provenance ({selectedDocument.filename})</span>
            </button>
          )}
        </div>

        {/* Selected Document Scoping Cockpit */}
        <div className="flex flex-wrap items-center justify-between bg-[#0B0F17] border border-gray-800 rounded-xl p-3.5 gap-3">
          <div className="flex items-center space-x-3">
            <span className="text-gray-400 font-semibold text-[11px]">SELECTED DOCUMENT:</span>
            <select
              value={selectedDocument?.id || ''}
              onChange={(e) => {
                const doc = documents.find((d) => d.id === e.target.value) || null;
                onSelectDocument(doc);
              }}
              className="bg-[#111827] border border-gray-700 text-cyan-300 font-semibold px-3 py-1.5 rounded-lg focus:outline-none focus:border-cyan-500 cursor-pointer text-xs"
            >
              {documents.length === 0 && <option value="">No documents in workspace</option>}
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.page_count}p, {d.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>

          {selectedDocument && (
            <div className="flex items-center space-x-4 text-[11px] text-gray-400">
              <span>
                Document ID: <strong className="text-cyan-400 font-mono">{selectedDocument.id}</strong>
              </span>
              <span>•</span>
              <span>
                Chunks: <strong className="text-emerald-400">{selectedDocument.chunk_count}</strong>
              </span>
              <span>•</span>
              <span>
                Status: <strong className="text-gray-200">{selectedDocument.parsing_status}</strong>
              </span>
            </div>
          )}
        </div>
      </div>

      {extractError && (
        <div className="p-4 bg-rose-950/40 border border-rose-800 rounded-xl text-rose-300 text-xs">
          <strong>Extraction Notice:</strong> {extractError}
        </div>
      )}

      {/* Split Screen Component */}
      <SplitScreenViewer
        citations={citations}
        summaryText={summaryText}
        activeWorkspace={activeWorkspace}
        selectedDocument={selectedDocument}
        onExtractEvidence={handleExtractEvidence}
        onNavigateTab={onNavigateTab}
        isExtracting={isExtracting}
        extractError={extractError}
      />
    </div>
  );
};
