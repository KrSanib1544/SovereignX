// frontend/src/pages/KnowledgeVault.tsx
import React, { useState, useEffect } from 'react';
import { Database, FileText, Search, RefreshCw, Layers } from 'lucide-react';
import { Workspace, DocumentSummary, DocumentDetail } from '../types/workspace';
import { fetchDocuments, fetchDocumentDetail } from '../api/workspaces';
import { DocumentUploader } from '../components/knowledge/DocumentUploader';
import { DocumentList } from '../components/knowledge/DocumentList';
import { SearchTester } from '../components/knowledge/SearchTester';
import { Modal } from '../components/common/Modal';

interface KnowledgeVaultProps {
  activeWorkspace: Workspace | null;
}

export const KnowledgeVault: React.FC<KnowledgeVaultProps> = ({ activeWorkspace }) => {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const loadDocuments = async () => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    try {
      const docs = await fetchDocuments(activeWorkspace.id);
      setDocuments(docs);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [activeWorkspace?.id]);

  const handleSelectDocument = async (docId: string) => {
    if (!activeWorkspace) return;
    setSelectedDocId(docId);
    try {
      const detail = await fetchDocumentDetail(activeWorkspace.id, docId);
      setDocDetail(detail);
      setIsDetailModalOpen(true);
    } catch (err: any) {
      alert(`Failed to load document details: ${err.message}`);
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
            </p>
          </div>
        </div>

        <button
          onClick={loadDocuments}
          disabled={isLoading || !activeWorkspace}
          className="flex items-center space-x-1.5 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-xl transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Vault</span>
        </button>
      </div>

      {activeWorkspace ? (
        <div className="space-y-6">
          {/* Uploader */}
          <DocumentUploader
            workspaceId={activeWorkspace.id}
            onUploadSuccess={loadDocuments}
          />

          {/* Document List */}
          <DocumentList
            documents={documents}
            onSelectDocument={handleSelectDocument}
            selectedDocId={selectedDocId}
          />

          {/* Vector Search Tester */}
          <SearchTester workspaceId={activeWorkspace.id} />
        </div>
      ) : (
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-12 text-center text-gray-500 font-mono text-xs">
          Select or create a workspace to view its Knowledge Vault.
        </div>
      )}

      {/* Document Detail & Chunks Modal */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={`DOCUMENT PROVENANCE: ${docDetail?.filename || ''}`}
        maxWidth="2xl"
      >
        {docDetail && (
          <div className="space-y-4 font-mono text-xs max-h-[70vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-2 gap-3 bg-[#0B0F17] p-3 rounded-lg border border-gray-800 text-[11px] text-gray-400">
              <div>
                <span className="text-gray-500">File Size:</span> {(docDetail.size_bytes / 1024).toFixed(1)} KB
              </div>
              <div>
                <span className="text-gray-500">Pages:</span> {docDetail.page_count}
              </div>
              <div>
                <span className="text-gray-500">OCR Applied:</span> {docDetail.ocr_applied ? 'Yes' : 'No'}
              </div>
              <div>
                <span className="text-gray-500">Status:</span> {docDetail.parsing_status}
              </div>
              <div className="col-span-2 truncate">
                <span className="text-gray-500">SHA-256:</span> {docDetail.sha256_hash}
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-gray-400 font-bold block text-[11px]">
                EXTRACTED VECTOR CHUNKS ({docDetail.chunks.length}):
              </span>
              <div className="space-y-2">
                {docDetail.chunks.map((chunk) => (
                  <div key={chunk.chunk_id} className="bg-[#0B0F17] p-3 rounded-lg border border-gray-800 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-gray-500">
                      <span>Chunk #{chunk.chunk_index} {chunk.page_number ? `• Page ${chunk.page_number}` : ''}</span>
                      <span>{chunk.token_count} tokens</span>
                    </div>
                    <p className="text-gray-300 text-[11px] leading-relaxed">
                      {chunk.content_preview}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
