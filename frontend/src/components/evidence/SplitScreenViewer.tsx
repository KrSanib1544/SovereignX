// frontend/src/components/evidence/SplitScreenViewer.tsx
import React, { useState, useEffect } from 'react';
import {
  FileText,
  ShieldCheck,
  Bookmark,
  Sparkles,
  Bot,
  Loader2,
  AlertCircle,
  Layers,
  FolderKanban
} from 'lucide-react';
import { CitationReference } from '../../types/agent';
import { Workspace, DocumentSummary } from '../../types/workspace';
import { Badge } from '../common/Badge';

interface SplitScreenViewerProps {
  citations: CitationReference[];
  summaryText?: string | null;
  activeWorkspace?: Workspace | null;
  selectedDocument?: DocumentSummary | null;
  onExtractEvidence?: () => void;
  onNavigateTab?: (tab: any) => void;
  isExtracting?: boolean;
  extractError?: string | null;
}

export const SplitScreenViewer: React.FC<SplitScreenViewerProps> = ({
  citations,
  summaryText,
  activeWorkspace,
  selectedDocument,
  onExtractEvidence,
  onNavigateTab,
  isExtracting = false,
  extractError = null,
}) => {
  // Strict Security Enforcement: Filter citations belonging strictly to the active workspace and selected document
  const filteredCitations = citations.filter((c) => {
    const wsMatches = !c.workspace_id || c.workspace_id === activeWorkspace?.id;
    const docMatches = !c.document_id || (selectedDocument && c.document_id === selectedDocument.id);
    return wsMatches && docMatches;
  });

  const [selectedCitationId, setSelectedCitationId] = useState<string>(
    filteredCitations[0]?.citation_id || ''
  );

  useEffect(() => {
    if (filteredCitations.length > 0 && !filteredCitations.some((c) => c.citation_id === selectedCitationId)) {
      setSelectedCitationId(filteredCitations[0].citation_id);
    }
  }, [filteredCitations, selectedCitationId]);

  const activeCitation =
    filteredCitations.find((c) => c.citation_id === selectedCitationId) || filteredCitations[0];

  // 1. If no document is selected
  if (!selectedDocument) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-12 text-center font-mono text-xs shadow-xl space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-500 mx-auto">
          <FileText className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-1.5">
          <h3 className="text-sm font-bold text-gray-300">NO TARGET DOCUMENT SELECTED</h3>
          <p className="text-gray-500 text-xs">
            No document selected. Select a document from Knowledge Vault to view evidence.
          </p>
        </div>
        {onNavigateTab && (
          <div className="pt-2">
            <button
              onClick={() => onNavigateTab('vault')}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-cyan-300 font-semibold rounded-xl transition-all border border-gray-700 inline-flex items-center space-x-2"
            >
              <FolderKanban className="w-4 h-4" />
              <span>Go to Knowledge Vault</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // 2. If evidence is currently being extracted
  if (isExtracting) {
    return (
      <div className="bg-[#111827] border border-cyan-700/60 rounded-2xl p-12 text-center font-mono text-xs shadow-xl space-y-4 animate-pulse">
        <div className="w-12 h-12 rounded-2xl bg-cyan-950/80 border border-cyan-600 flex items-center justify-center text-cyan-400 mx-auto">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
        <div className="max-w-md mx-auto space-y-1.5">
          <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-wider">
            EXTRACTING PROVENANCE ASSERTIONS
          </h3>
          <p className="text-gray-300 text-xs">
            Extracting evidence from <strong className="text-emerald-400">{selectedDocument.filename}</strong>...
          </p>
          <p className="text-gray-500 text-[11px]">
            Executing FastEmbed dense query against Qdrant with document UUID filter <code className="text-cyan-400 font-mono">[{selectedDocument.id}]</code>
          </p>
        </div>
      </div>
    );
  }

  // 3. If selected document has 0 chunks or no citations are available
  if (filteredCitations.length === 0) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-10 text-center font-mono text-xs shadow-xl space-y-5">
        <div className="w-12 h-12 rounded-2xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400 mx-auto">
          <Bookmark className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-2">
          <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
            EVIDENCE CITATIONS FOR {selectedDocument.filename}
          </h3>
          <p className="text-gray-400 text-xs">
            Target Document: <span className="text-emerald-400 font-semibold">{selectedDocument.filename}</span> (ID: <code className="text-cyan-400">{selectedDocument.id}</code>)
          </p>
          <p className="text-gray-500 text-[11px] leading-relaxed">
            {selectedDocument.chunk_count === 0
              ? 'No indexed evidence available for this document.'
              : 'Extract verifiable assertions with exact document page numbers, sections, and source text from this document.'}
          </p>
        </div>

        {extractError && (
          <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-xl text-rose-300 max-w-lg mx-auto text-left">
            <strong>Extraction Error:</strong> {extractError}
          </div>
        )}

        <div className="flex items-center justify-center space-x-3 pt-2">
          {onExtractEvidence && selectedDocument.chunk_count > 0 && (
            <button
              onClick={onExtractEvidence}
              disabled={isExtracting}
              className="flex items-center space-x-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-xl transition-all shadow-md shadow-cyan-950/50 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>Extract Evidence from {selectedDocument.filename}</span>
            </button>
          )}

          {onNavigateTab && (
            <button
              onClick={() => onNavigateTab('workspace')}
              className="flex items-center space-x-2 px-5 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold rounded-xl transition-all border border-gray-700"
            >
              <Bot className="w-4 h-4 text-emerald-400" />
              <span>Launch AI Workspace Task</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  // 4. Evidence Available
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 font-mono text-xs h-[calc(100vh-14rem)]">
      {/* Left Pane: Generated Assertion & Citation Selector */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl flex flex-col overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 border-b border-gray-800 bg-[#0B0F17]/50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bookmark className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-gray-200 tracking-wide">GENERATED SYNTHESIS & ASSERTIONS</h3>
          </div>
          <Badge variant="success" size="sm">
            {filteredCitations.length} VERIFIABLE CITATIONS
          </Badge>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {summaryText && (
            <div className="bg-[#0B0F17] border border-gray-800 rounded-xl p-4 space-y-2">
              <span className="text-gray-500 font-semibold block text-[10px]">ENGINEERING SUMMARY:</span>
              <p className="text-gray-200 text-xs leading-relaxed select-text">{summaryText}</p>
            </div>
          )}

          <div className="space-y-2">
            <span className="text-gray-400 font-semibold block text-[10px]">
              CLICK CITATION TO HIGHLIGHT PROVENANCE IN {selectedDocument.filename}:
            </span>
            {filteredCitations.map((c) => {
              const isSelected = selectedCitationId === c.citation_id;
              return (
                <div
                  key={c.citation_id}
                  onClick={() => setSelectedCitationId(c.citation_id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-cyan-950/60 border-cyan-500/80 shadow-md shadow-cyan-950/40'
                      : 'bg-[#0B0F17] border-gray-800 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="px-2 py-0.5 rounded bg-cyan-900/60 text-cyan-300 font-bold text-[10px]">
                      [{c.citation_id}]
                    </span>
                    <span className="text-gray-400 text-[10px] truncate max-w-xs font-semibold">
                      {c.document_name}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px] leading-relaxed line-clamp-2 select-text">
                    {c.excerpt}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Pane: Source Provenance & Evidence Verification */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl flex flex-col overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 border-b border-gray-800 bg-[#0B0F17]/50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-gray-200 tracking-wide">SOURCE DOCUMENT PROVENANCE</h3>
          </div>
          {activeCitation && (
            <span className="text-[10px] text-cyan-400">
              {activeCitation.document_name} {activeCitation.page_number ? `(Page ${activeCitation.page_number})` : ''}
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeCitation ? (
            <div className="space-y-4">
              {/* Document Header Box */}
              <div className="bg-[#0B0F17] border border-gray-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-gray-200 text-sm">{activeCitation.document_name}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> VERIFIED EVIDENCE
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-400 pt-2 border-t border-gray-800/80">
                  <div>
                    <span className="text-gray-500">Document ID:</span>{' '}
                    <span className="text-cyan-400 font-mono">{activeCitation.document_id || selectedDocument.id}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Page Number:</span>{' '}
                    <span className="text-gray-300 font-semibold">{activeCitation.page_number ?? 'N/A (Tabular/Image)'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Section Title:</span>{' '}
                    <span className="text-gray-300 font-semibold">{activeCitation.section ?? 'General'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Citation ID:</span>{' '}
                    <span className="text-emerald-400 font-bold">{activeCitation.citation_id}</span>
                  </div>
                </div>
              </div>

              {/* Verified Text Excerpt */}
              <div className="space-y-1.5">
                <span className="text-gray-500 font-semibold text-[10px] block">VERIFIED SOURCE EXCERPT:</span>
                <div className="bg-[#070A0F] border-l-4 border-emerald-500 p-4 rounded-r-lg text-emerald-300 text-xs leading-relaxed select-text whitespace-pre-wrap">
                  "{activeCitation.excerpt}"
                </div>
              </div>

              {/* Bounding Box Coordinates (if available) */}
              {activeCitation.bbox && (
                <div className="bg-[#0B0F17] border border-gray-800 rounded-lg p-3 text-[11px] text-gray-400">
                  <span className="text-gray-500 block mb-1">BOUNDING BOX PROVENANCE (PDF/OCR):</span>
                  <p className="font-mono text-cyan-300">
                    [{activeCitation.bbox.map((v) => v.toFixed(1)).join(', ')}]
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-10">Select a citation from the left pane to view source details.</p>
          )}
        </div>
      </div>
    </div>
  );
};
