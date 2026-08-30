// frontend/src/pages/AIWorkspace.tsx
import React, { useState } from 'react';
import {
  Bot,
  Send,
  Loader2,
  Shield,
  FileCheck2,
  AlertTriangle,
  Sparkles,
  Terminal,
  Bookmark,
  RefreshCw
} from 'lucide-react';
import { Workspace } from '../types/workspace';
import { AgentTaskResult, StepRecord } from '../types/agent';
import { createAgentTask, approveTaskAction } from '../api/agent';
import { StepTraceCard } from '../components/workspace/StepTraceCard';
import { ApprovalModal } from '../components/workspace/ApprovalModal';
import { ArtifactCard } from '../components/workspace/ArtifactCard';
import { Badge } from '../components/common/Badge';

interface AIWorkspaceProps {
  activeWorkspace: Workspace | null;
  onViewEvidence: (citations: any[], summaryText: string | null) => void;
}

export const AIWorkspace: React.FC<AIWorkspaceProps> = ({
  activeWorkspace,
  onViewEvidence,
}) => {
  const [prompt, setPrompt] = useState(
    'Read pump_turbine_log.txt and verify casing wall thickness against safety standards.'
  );
  const [autoApproveHighRisk, setAutoApproveHighRisk] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [taskResult, setTaskResult] = useState<AgentTaskResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // HITL Approval State
  const [pendingApproval, setPendingApproval] = useState<{
    toolName: string;
    argumentsPayload: Record<string, any>;
    riskReasons: string;
  } | null>(null);

  const handleRunTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !prompt.trim() || isExecuting) return;

    setIsExecuting(true);
    setErrorMessage(null);
    setPendingApproval(null);

    try {
      const result = await createAgentTask(activeWorkspace.id, prompt, autoApproveHighRisk);
      setTaskResult(result);

      if (result.state === 'WAITING_APPROVAL' && result.pending_approval) {
        setPendingApproval({
          toolName: result.pending_approval.tool_name,
          argumentsPayload: result.pending_approval.arguments,
          riskReasons: result.pending_approval.reason,
        });
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Execution failed.');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApproveAction = async () => {
    if (!activeWorkspace || !taskResult || !pendingApproval) return;
    setIsExecuting(true);
    try {
      const resumedResult = await approveTaskAction(
        activeWorkspace.id,
        taskResult.task_id,
        true,
        pendingApproval.toolName,
        pendingApproval.argumentsPayload
      );
      setTaskResult(resumedResult);
      setPendingApproval(null);
    } catch (err: any) {
      alert(`Approval execution failed: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRejectAction = async () => {
    if (!activeWorkspace || !taskResult || !pendingApproval) return;
    setIsExecuting(true);
    try {
      const rejectedResult = await approveTaskAction(
        activeWorkspace.id,
        taskResult.task_id,
        false,
        pendingApproval.toolName,
        pendingApproval.argumentsPayload
      );
      setTaskResult(rejectedResult);
      setPendingApproval(null);
    } catch (err: any) {
      alert(`Rejection error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs max-w-6xl mx-auto pb-8">
      {/* Header & Controls */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-100">AI WORKSPACE & BOUNDED REACT RUNTIME</h2>
              <p className="text-gray-400 text-[11px]">
                Target Workspace: <span className="text-emerald-400 font-semibold">{activeWorkspace?.name || 'None'}</span>
              </p>
            </div>
          </div>

          <Badge variant="accent" size="sm">
            MAX 15 STEPS • LOOP DETECTOR ACTIVE
          </Badge>
        </div>

        {/* Task Input Box */}
        <form onSubmit={handleRunTask} className="space-y-3">
          <div className="relative">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder="Enter engineering inspection prompt..."
              className="w-full bg-[#0B0F17] border border-gray-700 rounded-xl p-4 text-gray-100 text-xs focus:outline-none focus:border-cyan-500 font-mono leading-relaxed"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center space-x-2 text-gray-400 text-[11px] cursor-pointer">
              <input
                type="checkbox"
                checked={autoApproveHighRisk}
                onChange={(e) => setAutoApproveHighRisk(e.target.checked)}
                className="rounded bg-[#0B0F17] border-gray-700 text-cyan-500 focus:ring-0"
              />
              <span>Auto-Approve High Risk Tools (Testing Mode)</span>
            </label>

            <button
              type="submit"
              disabled={isExecuting || !prompt.trim() || !activeWorkspace}
              className="flex items-center space-x-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-xl transition-all shadow-md shadow-cyan-950/50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isExecuting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Agent Executing...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Execute Task</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-rose-300 text-xs">
          <strong>Execution Error:</strong> {errorMessage}
        </div>
      )}

      {/* Execution Results Section */}
      {taskResult && (
        <div className="space-y-6">
          {/* Status Bar */}
          <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-gray-400 text-xs">TASK ID:</span>
              <span className="font-bold text-gray-200">{taskResult.task_id}</span>
              <Badge
                variant={
                  taskResult.state === 'COMPLETED'
                    ? 'success'
                    : taskResult.state === 'WAITING_APPROVAL'
                    ? 'warning'
                    : 'danger'
                }
                size="sm"
              >
                {taskResult.state}
              </Badge>
            </div>

            <div className="flex items-center space-x-3 text-gray-400 text-xs">
              <span>Steps Executed: <strong className="text-cyan-400">{taskResult.steps.length}</strong></span>
              {taskResult.citations && taskResult.citations.length > 0 && (
                <button
                  onClick={() => onViewEvidence(taskResult.citations || [], taskResult.final_answer)}
                  className="flex items-center space-x-1 px-3 py-1 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded-lg text-xs transition-colors"
                >
                  <Bookmark className="w-3.5 h-3.5" />
                  <span>View {taskResult.citations.length} Citations</span>
                </button>
              )}
            </div>
          </div>

          {/* Final Answer / Deliverable Summary */}
          {taskResult.final_answer && (
            <div className="bg-[#111827] border border-emerald-900/60 rounded-2xl p-6 space-y-3 shadow-xl">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
                <FileCheck2 className="w-5 h-5" />
                <span>FINAL AGENT SYNTHESIS & RESOLUTION</span>
              </div>
              <div className="bg-[#0B0F17] p-4 rounded-xl border border-gray-800/80 text-gray-200 text-xs leading-relaxed">
                {taskResult.final_answer}
              </div>
            </div>
          )}

          {/* Generated Artifacts Section */}
          {taskResult.artifacts && taskResult.artifacts.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-gray-300">GENERATED DELIVERABLES</h3>
              <div className="grid grid-cols-1 gap-3">
                {taskResult.artifacts.map((art) => (
                  <ArtifactCard
                    key={art.id || art.filename}
                    artifact={art}
                    workspaceId={activeWorkspace?.id || ''}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Live Step Trace Visualizer Stream */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-gray-300">EXECUTION STEP TRACE ({taskResult.steps.length})</h3>
            <div className="space-y-3">
              {taskResult.steps.map((step) => (
                <StepTraceCard key={step.step_number} step={step} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* HITL Approval Modal */}
      {pendingApproval && (
        <ApprovalModal
          isOpen={true}
          toolName={pendingApproval.toolName}
          argumentsPayload={pendingApproval.argumentsPayload}
          riskReasons={pendingApproval.riskReasons}
          onApprove={handleApproveAction}
          onReject={handleRejectAction}
        />
      )}
    </div>
  );
};
