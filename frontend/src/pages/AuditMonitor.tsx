// frontend/src/pages/AuditMonitor.tsx
import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, Link, RefreshCw, CheckCircle2, AlertTriangle, Lock, Eye } from 'lucide-react';
import { AuditEvent, AuditVerification } from '../types/audit';
import { Workspace } from '../types/workspace';
import { fetchAuditEvents, verifyAuditLedger } from '../api/audit';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

interface AuditMonitorProps {
  activeWorkspace: Workspace | null;
}

export const AuditMonitor: React.FC<AuditMonitorProps> = ({ activeWorkspace }) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [verification, setVerification] = useState<AuditVerification | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  const loadEvents = async () => {
    setIsLoading(true);
    try {
      const data = await fetchAuditEvents(activeWorkspace?.id, 100);
      setEvents(data);
    } catch (err: any) {
      console.error('Failed to load audit events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    setVerificationError(null);
    try {
      const res = await verifyAuditLedger();
      setVerification(res);
    } catch (err: any) {
      setVerificationError(err.message || 'Audit verification request failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    loadEvents();
    handleVerifyChain();
  }, [activeWorkspace?.id]);

  return (
    <div className="space-y-6 font-mono text-xs max-w-7xl mx-auto pb-8">
      {/* Top Banner & Verification Status */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-100">IMMUTABLE CRYPTOGRAPHIC AUDIT LEDGER</h2>
              <p className="text-gray-400 text-[11px]">
                Continuous SHA-256 hash-chaining across all agent reasoning steps, tool calls, and model swaps.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleVerifyChain}
              disabled={isVerifying}
              className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-black font-bold rounded-xl transition-all shadow-md shadow-emerald-950/50 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isVerifying ? 'animate-spin' : ''}`} />
              <span>Verify Hash Chain</span>
            </button>
          </div>
        </div>

        {/* Verification Error Notice */}
        {verificationError && (
          <div className="p-4 rounded-xl border bg-rose-950/40 border-rose-700/60 text-rose-300 flex items-center space-x-3">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
            <div>
              <span className="font-bold text-xs block">VERIFICATION ERROR</span>
              <span className="text-[11px] text-gray-300 font-mono block">{verificationError}</span>
            </div>
          </div>
        )}

        {/* Verification Report Bar */}
        {verification && (
          <div className={`p-4 rounded-xl border flex items-center justify-between ${
            verification.is_valid
              ? 'bg-emerald-950/40 border-emerald-700/60 text-emerald-300'
              : 'bg-rose-950/40 border-rose-700/60 text-rose-300'
          }`}>
            <div className="flex items-center space-x-3">
              {verification.is_valid ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
              )}
              <div>
                <span className="font-bold text-xs block">
                  {verification.is_valid
                    ? `HASH CHAIN INTEGRITY VALIDATED (${verification.total_events} TOTAL EVENTS)`
                    : `CHAIN TAMPER DETECTED: ${verification.error_reason}`}
                </span>
                <span className="text-[10px] text-gray-400 font-mono truncate max-w-xl block">
                  Latest Block Hash: {verification.last_verified_hash || 'None'}
                </span>
              </div>
            </div>

            <Badge variant={verification.is_valid ? 'success' : 'danger'} size="md">
              {verification.is_valid ? '100% UNTAMPERED' : 'INVALID'}
            </Badge>
          </div>
        )}
      </div>

      {/* Audit Event Stream Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-gray-800 bg-[#0B0F17]/50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Link className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-gray-200">HISTORICAL AUDIT BLOCKS ({events.length})</h3>
          </div>
          <button
            onClick={loadEvents}
            className="p-1.5 hover:bg-gray-800 rounded text-gray-400 hover:text-gray-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-gray-800 bg-[#0B0F17]/30 text-gray-400">
                <th className="py-3 px-4 font-semibold">ID</th>
                <th className="py-3 px-4 font-semibold">TIMESTAMP</th>
                <th className="py-3 px-4 font-semibold">ACTOR</th>
                <th className="py-3 px-4 font-semibold">EVENT TYPE</th>
                <th className="py-3 px-4 font-semibold">PREVIOUS HASH</th>
                <th className="py-3 px-4 font-semibold">CURRENT HASH</th>
                <th className="py-3 px-4 font-semibold text-right">PAYLOAD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {events.map((evt) => (
                <tr key={evt.id} className="hover:bg-[#151D2C] transition-colors">
                  <td className="py-3 px-4 font-bold text-cyan-400">#{evt.id}</td>
                  <td className="py-3 px-4 text-gray-300 whitespace-nowrap">
                    {evt.timestamp.replace('T', ' ').slice(0, 19)}
                  </td>
                  <td className="py-3 px-4 text-gray-400">{evt.actor}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-200 font-semibold text-[10px]">
                      {evt.event_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-500 font-mono" title={evt.previous_hash}>
                    {evt.previous_hash.slice(0, 10)}...
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-semibold" title={evt.current_hash}>
                    {evt.current_hash.slice(0, 10)}...
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setSelectedEvent(evt)}
                      className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors text-[10px] flex items-center gap-1 ml-auto"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Payload Modal */}
      <Modal
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={`AUDIT EVENT #${selectedEvent?.id} — ${selectedEvent?.event_type}`}
        maxWidth="xl"
      >
        {selectedEvent && (
          <div className="space-y-3 font-mono text-xs max-h-[70vh] overflow-y-auto">
            <div className="space-y-1 text-gray-400 bg-[#0B0F17] p-3 rounded-lg border border-gray-800 text-[11px]">
              <div><strong>UUID:</strong> {selectedEvent.event_uuid}</div>
              <div><strong>Actor:</strong> {selectedEvent.actor}</div>
              <div><strong>Timestamp:</strong> {selectedEvent.timestamp}</div>
              <div><strong>Previous Hash:</strong> <span className="text-gray-500">{selectedEvent.previous_hash}</span></div>
              <div><strong>Current Hash:</strong> <span className="text-emerald-400">{selectedEvent.current_hash}</span></div>
            </div>

            <div>
              <span className="text-gray-400 block mb-1 font-semibold text-[11px]">RAW PAYLOAD JSON:</span>
              <pre className="bg-[#070A0F] border border-gray-800 rounded-lg p-3 text-cyan-300 overflow-x-auto whitespace-pre-wrap text-[11px]">
                {JSON.stringify(JSON.parse(selectedEvent.payload_json || '{}'), null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
