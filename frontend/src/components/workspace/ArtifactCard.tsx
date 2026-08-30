// frontend/src/components/workspace/ArtifactCard.tsx
import React from 'react';
import { FileText, Download, ShieldCheck, HardDrive } from 'lucide-react';
import { GeneratedArtifact } from '../../types/agent';
import { getArtifactDownloadUrl } from '../../api/workspaces';

interface ArtifactCardProps {
  artifact: GeneratedArtifact;
  workspaceId: string;
}

export const ArtifactCard: React.FC<ArtifactCardProps> = ({ artifact, workspaceId }) => {
  const downloadUrl = getArtifactDownloadUrl(workspaceId, artifact.filename);

  return (
    <div className="bg-[#111827] border border-cyan-900/50 rounded-xl p-4 flex items-center justify-between font-mono text-xs shadow-lg shadow-cyan-950/20 hover:border-cyan-700/60 transition-all">
      <div className="flex items-center space-x-3.5">
        <div className="w-10 h-10 rounded-lg bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
          <FileText className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <h4 className="font-bold text-gray-100 text-sm">{artifact.filename}</h4>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/50 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> VERIFIED ARTIFACT
            </span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-gray-400">
            <span>{artifact.size_bytes != null ? `${(artifact.size_bytes / 1024).toFixed(1)} KB` : 'Generated Document'}</span>
            {artifact.sha256_hash && (
              <>
                <span>•</span>
                <span className="truncate max-w-xs font-mono text-gray-500" title={artifact.sha256_hash}>
                  SHA-256: {artifact.sha256_hash.slice(0, 16)}...
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      <a
        href={downloadUrl}
        download={artifact.filename}
        className="flex items-center space-x-1.5 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg transition-colors shadow-sm"
      >
        <Download className="w-4 h-4" />
        <span>Download</span>
      </a>
    </div>
  );
};
