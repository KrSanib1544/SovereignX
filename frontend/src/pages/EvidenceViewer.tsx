// frontend/src/pages/EvidenceViewer.tsx
import React from 'react';
import { SplitSquareVertical, Info } from 'lucide-react';
import { CitationReference } from '../types/agent';
import { SplitScreenViewer } from '../components/evidence/SplitScreenViewer';

interface EvidenceViewerProps {
  citations: CitationReference[];
  summaryText: string | null;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  citations,
  summaryText,
}) => {
  return (
    <div className="space-y-6 font-mono text-xs max-w-7xl mx-auto pb-8">
      {/* Top Banner */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl flex items-center justify-between">
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
      </div>

      {/* Split Screen Component */}
      <SplitScreenViewer citations={citations} summaryText={summaryText} />
    </div>
  );
};
