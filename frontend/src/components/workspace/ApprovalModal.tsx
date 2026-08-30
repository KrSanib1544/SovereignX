// frontend/src/components/workspace/ApprovalModal.tsx
import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, Check, X, Terminal } from 'lucide-react';
import { Modal } from '../common/Modal';

interface ApprovalModalProps {
  isOpen: boolean;
  toolName: string;
  argumentsPayload: Record<string, any>;
  riskReasons: string;
  onApprove: () => void;
  onReject: () => void;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  toolName,
  argumentsPayload,
  riskReasons,
  onApprove,
  onReject,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await onApprove();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await onReject();
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onReject}
      title="HUMAN-IN-THE-LOOP (HITL) APPROVAL REQUIRED"
      maxWidth="2xl"
    >
      <div className="space-y-4 font-mono text-xs">
        {/* Warning Banner */}
        <div className="flex items-start space-x-3 bg-amber-950/40 border border-amber-600/50 rounded-xl p-3.5 text-amber-200">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-amber-300">HIGH RISK ACTION GATED BY POLICY ENGINE</h4>
            <p className="text-[11px] text-amber-200/80 leading-relaxed">
              The agent is requesting permission to execute an action classified as HIGH risk.
              Deterministic security invariant #7 requires explicit operator sign-off before proceeding.
            </p>
          </div>
        </div>

        {/* Action Details */}
        <div className="bg-[#0B0F17] border border-gray-800 rounded-xl p-3.5 space-y-2">
          <div className="flex items-center space-x-2 text-gray-300">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span className="text-gray-400">Target Tool:</span>
            <span className="font-bold text-cyan-300 text-sm">{toolName}</span>
          </div>

          <div>
            <span className="text-gray-400 block mb-1">Risk Evaluation Reason:</span>
            <p className="text-rose-300 text-[11px] bg-rose-950/30 px-2.5 py-1.5 rounded border border-rose-900/40">
              {riskReasons || 'Executing dynamic script inside Docker sandbox.'}
            </p>
          </div>

          <div>
            <span className="text-gray-400 block mb-1">Arguments & Code Preview:</span>
            <div className="bg-[#070A0F] border border-gray-800 rounded-lg p-3 max-h-60 overflow-y-auto">
              <pre className="text-cyan-300 text-[11px] whitespace-pre-wrap font-mono">
                {typeof argumentsPayload?.script === 'string'
                  ? argumentsPayload.script
                  : JSON.stringify(argumentsPayload, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-800">
          <span className="text-[11px] text-gray-500">Operator Action Sign-off</span>
          <div className="flex space-x-3">
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="flex items-center space-x-1.5 px-4 py-2 bg-rose-950/60 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 rounded-lg transition-colors font-semibold"
            >
              <X className="w-4 h-4" />
              <span>Reject Action</span>
            </button>
            <button
              onClick={handleApprove}
              disabled={isProcessing}
              className="flex items-center space-x-1.5 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-black rounded-lg transition-colors font-bold shadow-lg shadow-emerald-950/50"
            >
              <Check className="w-4 h-4" />
              <span>Approve & Execute</span>
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
