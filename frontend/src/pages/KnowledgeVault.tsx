// frontend/src/pages/KnowledgeVault.tsx
import React, { useState } from 'react';
import { Database, FileText, Search, RefreshCw, Layers } from 'lucide-react';
import { Workspace, DocumentSummary, DocumentDetail } from '../types/workspace';
import { fetchDocumentDetail } from '../api/workspaces';
import { DocumentUploader } from '../components/knowledge/DocumentUploader';
import { DocumentList } from '../components/knowledge/DocumentList';
import { SearchTester } from '../components/knowledge/SearchTester';
import { Modal } from '../components/common/Modal';

interface KnowledgeVaultProps {
  activeWorkspace: Workspace | null;
  documents: DocumentSummary[];
  selectedDocument: DocumentSummary | null;
  onSelectDocument: (doc: DocumentSummary) => void;
  onRefreshDocuments: () => void;
}

export const KnowledgeVault: React.FC<KnowledgeVaultProps> = ({
  activeWorkspace,
  documents,
  selectedDocument,
  onSelectDocument,
  onRefreshDocuments,
}) => {
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const handleInspectDocument = async (doc: DocumentSummary) => {
    if (!activeWorkspace) return;
    setIsLoadingDetail(true);
    try {
      const detail = await fetchDocumentDetail(activeWorkspace.id, doc.id);
      setDocDetail(detail);
      setIsDetailModalOpen(true);
    } catch (err: any) {
      alert(`Failed to load document details: ${err.message}`);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs max-w-6xl mx-auto pb-8">
      {/* Top Header */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-100">KNOWLEDGE VAULT & MULTI-MODAL INDEX</h2>
            <p className="text-gray-400 text-[11px]">
              Workspace: <span className="text-emerald-400 font-semibold">{activeWorkspace?.name || 'None'}</span> ({activeWorkspace?.classification_level || 'PUBLIC'})
              {selectedDocument && (
                <span className="ml-2 text-cyan-300">
                  • Active Target: <strong className="text-gray-200">{selectedDocument.filename}</strong>
                </span>
              )}
            </p>
          </div>
        </div>

        <button
          onClick={onRefreshDocuments}
          disabled={!activeWorkspace}
          className="flex items-center space-x-1.5 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-xl transition-colors disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Vault</span>
        </button>
      </div>

      {activeWorkspace ? (
        <div className="space-y-6">
          {/* Uploader */}
          <DocumentUploader
            workspaceId={activeWorkspace.id}
            onUploadSuccess={onRefreshDocuments}
          />

          {/* Document List */}
          <DocumentList
            documents={documents}
            onSelectDocument={onSelectDocument}
            onInspectDocument={handleInspectDocument}
            selectedDocId={selectedDocument?.id || null}
          />

          {/* Vector Search Tester */}
          <SearchTester workspaceId={activeWorkspace.id} />
        </div>
      ) : (
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-12 text-center text-gray-500 font-mono text-xs">
          Select or create a workspace to view its Knowledge Vault.
        </div>
      )}

      {/* Document Chunks Inspector Modal */}
      {docDetail && (
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title={`DOCUMENT INSPECTION: ${docDetail.filename}`}
          maxWidth="xl"
        >
          <div className="space-y-4 font-mono text-xs max-h-[70vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-[#0B0F17] p-3 rounded-xl border border-gray-800">
              <div>
                <span className="text-gray-500 block text-[10px]">DOCUMENT ID:</span>
                <span className="text-cyan-300 font-bold">{docDetail.id}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">TOTAL CHUNKS:</span>
                <span className="text-emerald-400 font-bold">{docDetail.chunks.length}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">PAGE COUNT:</span>
                <span className="text-gray-300">{docDetail.page_count}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">SHA-256 HASH:</span>
                <span className="text-gray-400 text-[10px] truncate block" title={docDetail.sha256_hash}>
                  {docDetail.sha256_hash.slice(0, 16)}...
                </span>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <h4 className="font-bold text-gray-300 text-xs flex items-center justify-between">
                <span>INDEXED VECTOR CHUNKS</span>
                <span className="text-[10px] text-gray-500">FastEmbed ONNX (384-dim)</span>
              </h4>

              {docDetail.chunks.map((chunk) => (
                <div
                  key={chunk.chunk_id}
                  className="bg-[#0B0F17] border border-gray-800 rounded-xl p-4 space-y-2 hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-bold">
                      Chunk #{chunk.chunk_index + 1} ({chunk.chunk_id})
                    </span>
                    <span className="text-gray-400">
                      Page {chunk.page_number ?? 'N/A'} • {chunk.section_title || 'General'}
                    </span>
                  </div>

                  <p className="text-gray-300 text-xs leading-relaxed bg-[#070A0F] p-3 rounded-lg border border-gray-900">
                    "{chunk.content_preview}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
