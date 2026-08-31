// frontend/src/components/knowledge/DocumentList.tsx
import React from 'react';
import { FileText, Eye, CheckCircle2, ScanLine, BookmarkCheck, Check } from 'lucide-react';
import { DocumentSummary } from '../../types/workspace';
import { Badge } from '../common/Badge';

interface DocumentListProps {
  documents: DocumentSummary[];
  onSelectDocument: (doc: DocumentSummary) => void;
  onInspectDocument?: (doc: DocumentSummary) => void;
  selectedDocId: string | null;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onSelectDocument,
  onInspectDocument,
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
        <div className="flex items-center space-x-2">
          <h3 className="font-bold text-gray-200 tracking-wide">INDEXED ASSETS ({documents.length})</h3>
          <span className="text-gray-500 text-[10px]">CLICK TO TARGET FOR EVIDENCE & AI WORKSPACE</span>
        </div>
      </div>

      <div className="divide-y divide-gray-800/80">
        {documents.map((doc) => {
          const isSelected = selectedDocId === doc.id;
          return (
            <div
              key={doc.id}
              onClick={() => onSelectDocument(doc)}
              className={`p-4 flex items-center justify-between cursor-pointer transition-all ${
                isSelected
                  ? 'bg-cyan-950/40 border-l-4 border-cyan-400'
                  : 'hover:bg-[#151D2C]'
              }`}
            >
              <div className="flex items-center space-x-3.5 min-w-0">
                <div
                  className={`w-9 h-9 rounded-lg border flex items-center justify-center shrink-0 ${
                    isSelected
                      ? 'bg-cyan-900/60 border-cyan-500 text-cyan-300'
                      : 'bg-[#0B0F17] border-gray-800 text-cyan-400'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-200 text-xs truncate max-w-sm" title={doc.filename}>
                      {doc.filename}
                    </h4>
                    {isSelected && (
                      <span className="text-[9px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700/80 font-bold flex items-center gap-1">
                        <Check className="w-2.5 h-2.5" /> ACTIVE TARGET
                      </span>
                    )}
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
                    <span className="text-gray-400 font-mono">ID: {doc.id}</span>
                    <span>•</span>
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
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectDocument(doc);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-colors flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-cyan-600 text-black'
                      : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                  }`}
                >
                  {isSelected ? (
                    <>
                      <BookmarkCheck className="w-3.5 h-3.5" />
                      <span>Target Selected</span>
                    </>
                  ) : (
                    <span>Select Target</span>
                  )}
                </button>

                {onInspectDocument && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onInspectDocument(doc);
                    }}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-[11px] transition-colors flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Inspect Chunks</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
