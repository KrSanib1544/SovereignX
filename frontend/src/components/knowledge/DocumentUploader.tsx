// frontend/src/components/knowledge/DocumentUploader.tsx
import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocuments } from '../../api/workspaces';

interface DocumentUploaderProps {
  workspaceId: string;
  onUploadSuccess: () => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  workspaceId,
  onUploadSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [classification, setClassification] = useState('INTERNAL_ENGINEERING');
  const [enableOcr, setEnableOcr] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);
    setUploadStatus(null);

    try {
      const res = await uploadDocuments(workspaceId, selectedFiles, classification, enableOcr);
      setUploadStatus({
        type: 'success',
        message: `Successfully ingested ${res.ingested_count} document(s) into local Qdrant & SQLite.`,
      });
      setSelectedFiles([]);
      onUploadSuccess();
    } catch (err: any) {
      setUploadStatus({
        type: 'error',
        message: `Upload failed: ${err.message}`,
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-lg">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-gray-200 text-sm tracking-wide">INGEST NEW DOCUMENTS</h3>
        <span className="text-[11px] text-gray-500">PDF, XLSX, CSV, JPG, PNG, TXT</span>
      </div>

      {/* Dropzone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-cyan-500 bg-cyan-950/20'
            : 'border-gray-800 hover:border-gray-700 bg-[#0B0F17]/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.xlsx,.xls,.csv,.txt,.jpg,.jpeg,.png"
        />
        <UploadCloud className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
        <p className="text-gray-300 font-medium text-xs">
          Click to browse or drag and drop engineering files here
        </p>
        <p className="text-[10px] text-gray-500 mt-1">
          Files will be parsed, OCR-processed offline, and embedded with FastEmbed ONNX
        </p>
      </div>

      {/* Selected Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="space-y-1.5 bg-[#0B0F17] p-3 rounded-lg border border-gray-800 max-h-36 overflow-y-auto">
          <span className="text-gray-400 text-[10px] block mb-1">SELECTED FILES ({selectedFiles.length}):</span>
          {selectedFiles.map((f, i) => (
            <div key={i} className="flex items-center justify-between text-gray-300 text-[11px]">
              <div className="flex items-center space-x-2 truncate">
                <File className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="truncate">{f.name}</span>
              </div>
              <span className="text-gray-500 text-[10px] shrink-0">{(f.size / 1024).toFixed(1)} KB</span>
            </div>
          ))}
        </div>
      )}

      {/* Options & Upload Controls */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-800">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-gray-400 text-[11px]">Classification:</label>
            <select
              value={classification}
              onChange={(e) => setClassification(e.target.value)}
              className="bg-[#0B0F17] border border-gray-700 rounded px-2 py-1 text-gray-200 focus:outline-none focus:border-cyan-500 text-[11px]"
            >
              <option value="INTERNAL_ENGINEERING">INTERNAL_ENGINEERING</option>
              <option value="RESTRICTED_CONFIDENTIAL">RESTRICTED_CONFIDENTIAL</option>
              <option value="PUBLIC">PUBLIC</option>
            </select>
          </div>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableOcr}
              onChange={(e) => setEnableOcr(e.target.checked)}
              className="rounded bg-[#0B0F17] border-gray-700 text-cyan-500 focus:ring-0"
            />
            <span className="text-gray-400 text-[11px]">Enable Offline OCR</span>
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={selectedFiles.length === 0 || isUploading}
          className="flex items-center space-x-2 px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Ingesting & Embedding...</span>
            </>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Ingest Package ({selectedFiles.length})</span>
            </>
          )}
        </button>
      </div>

      {/* Status Message */}
      {uploadStatus && (
        <div
          className={`p-3 rounded-lg flex items-center space-x-2 text-[11px] ${
            uploadStatus.type === 'success'
              ? 'bg-emerald-950/50 border border-emerald-800 text-emerald-300'
              : 'bg-rose-950/50 border border-rose-800 text-rose-300'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span>{uploadStatus.message}</span>
        </div>
      )}
    </div>
  );
};
