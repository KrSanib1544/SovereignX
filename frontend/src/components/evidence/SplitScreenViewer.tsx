// frontend/src/components/evidence/SplitScreenViewer.tsx
import React, { useState } from 'react';
import { FileText, ExternalLink, ShieldCheck, CheckCircle2, Bookmark, Layers } from 'lucide-react';
import { CitationReference } from '../../types/agent';
import { Badge } from '../common/Badge';

interface SplitScreenViewerProps {
  citations: CitationReference[];
  summaryText?: string | null;
}

export const SplitScreenViewer: React.FC<SplitScreenViewerProps> = ({
  citations,
  summaryText,
}) => {
  const [selectedCitationId, setSelectedCitationId] = useState<string>(
    citations[0]?.citation_id || ''
  );

  const activeCitation = citations.find((c) => c.citation_id === selectedCitationId) || citations[0];

  if (citations.length === 0) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-12 text-center text-gray-500 font-mono text-xs">
        No active evidence citations available. Run an AI Workspace task to extract verifiable assertions.
      </div>
    );
  }

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
            {citations.length} VERIFIABLE CITATIONS
          </Badge>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {summaryText && (
            <div className="bg-[#0B0F17] border border-gray-800 rounded-xl p-4 space-y-2">
              <span className="text-gray-500 font-semibold block text-[10px]">ENGINEERING SUMMARY:</span>
              <p className="text-gray-200 text-xs leading-relaxed">{summaryText}</p>
            </div>
          )}

          <div className="space-y-2">
            <span className="text-gray-400 font-semibold block text-[10px]">CLICK CITATION TO HIGHLIGHT PROVENANCE:</span>
            {citations.map((c) => {
              const isSelected = selectedCitationId === c.citation_id;
              return (
                <div
                  key={c.citation_id}
                  onClick={() => setSelectedCitationId(c.citation_id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-cyan-950/60 border-cyan-500/80 shadow-md shadow-cyan-950/40'
                      : 'bg-[#0B0F17] border-gray-800 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="px-2 py-0.5 rounded bg-cyan-900/60 text-cyan-300 font-bold text-[10px]">
                      [{c.citation_id}]
                    </span>
                    <span className="text-gray-400 text-[10px] truncate max-w-xs">{c.document_name}</span>
                  </div>
                  <p className="text-gray-300 text-[11px] leading-relaxed line-clamp-2">
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
                    <span className="text-gray-500">Page Number:</span>{' '}
                    <span className="text-gray-300 font-semibold">{activeCitation.page_number ?? 'N/A (Tabular/Image)'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Section Title:</span>{' '}
                    <span className="text-gray-300 font-semibold">{activeCitation.section ?? 'General'}</span>
                  </div>
                </div>
              </div>

              {/* Verified Text Excerpt */}
              <div className="space-y-1.5">
                <span className="text-gray-500 font-semibold text-[10px] block">VERIFIED SOURCE EXCERPT:</span>
                <div className="bg-[#070A0F] border-l-4 border-emerald-500 p-4 rounded-r-lg text-emerald-300 text-xs leading-relaxed">
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
