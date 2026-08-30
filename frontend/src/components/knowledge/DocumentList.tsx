// frontend/src/components/knowledge/DocumentList.tsx
import React from 'react';
import { FileText, Eye, CheckCircle2, ScanLine, Clock, HardDrive } from 'lucide-react';
import { DocumentSummary } from '../../types/workspace';
import { Badge } from '../common/Badge';

interface DocumentListProps {
  documents: DocumentSummary[];
  onSelectDocument: (docId: string) => void;
  selectedDocId: string | null;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onSelectDocument,
  selectedDocId,
}) => {
  if (documents.length === 0) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-8 text-center text-gray-500 font-mono text-xs">
        No documents indexed in this workspace yet. Upload an inspection package above.
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden font-mono text-xs shadow-lg">
      <div className="px-5 py-3.5 border-b border-gray-800 bg-[#0B0F17]/50 flex items-center justify-between">
        <h3 className="font-bold text-gray-200 tracking-wide">INDEXED ASSETS ({documents.length})</h3>
        <span className="text-gray-500 text-[10px]">FAST-EMBED & QDRANT RETRIEVAL READY</span>
      </div>

      <div className="divide-y divide-gray-800/80">
        {documents.map((doc) => {
          const isSelected = selectedDocId === doc.id;
          return (
            <div
              key={doc.id}
              onClick={() => onSelectDocument(doc.id)}
              className={`p-4 flex items-center justify-between cursor-pointer transition-all ${
                isSelected
                  ? 'bg-cyan-950/40 border-l-4 border-cyan-400'
                  : 'hover:bg-[#151D2C]'
              }`}
            >
              <div className="flex items-center space-x-3.5 min-w-0">
                <div className="w-9 h-9 rounded-lg bg-[#0B0F17] border border-gray-800 flex items-center justify-center text-cyan-400 shrink-0">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-200 text-xs truncate max-w-sm" title={doc.filename}>
                      {doc.filename}
                    </h4>
                    {doc.ocr_applied && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-1">
                        <ScanLine className="w-2.5 h-2.5" /> OCR
                      </span>
                    )}
                    <Badge
                      variant={doc.parsing_status === 'INDEXED' ? 'success' : 'default'}
                      size="sm"
                    >
                      {doc.parsing_status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-3 text-[10px] text-gray-500">
                    <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                    <span>•</span>
                    <span>{doc.page_count} page(s)</span>
                    <span>•</span>
                    <span className="text-cyan-400 font-semibold">{doc.chunk_count} vector chunks</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectDocument(doc.id);
                  }}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-[11px] transition-colors flex items-center gap-1.5"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Chunks</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
