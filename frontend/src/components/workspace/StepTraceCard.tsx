// frontend/src/components/workspace/StepTraceCard.tsx
import React, { useState } from 'react';
import { Terminal, Shield, ChevronDown, ChevronRight, Clock, Cpu, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { StepRecord } from '../../types/agent';
import { Badge } from '../common/Badge';

interface StepTraceCardProps {
  step: StepRecord;
}

export const StepTraceCard: React.FC<StepTraceCardProps> = ({ step }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getRiskVariant = (level: string | null) => {
    switch (level) {
      case 'LOW':
        return 'success';
      case 'MEDIUM':
        return 'warning';
      case 'HIGH':
      case 'CRITICAL':
        return 'danger';
      default:
        return 'default';
    }
  };

  const getPolicyIcon = (decision: string | null) => {
    switch (decision) {
      case 'ALLOW':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case 'REQUIRE_APPROVAL':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
      case 'DENY':
        return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 space-y-3 font-mono text-xs shadow-lg transition-all hover:border-gray-700">
      {/* Step Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/40 font-bold text-xs">
            STEP #{step.step_number}
          </span>
          {step.tool_name && (
            <div className="flex items-center space-x-1.5 text-gray-200">
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span className="font-semibold">{step.tool_name}</span>
            </div>
          )}
          {step.tool_risk_level && (
            <Badge variant={getRiskVariant(step.tool_risk_level)} size="sm">
              RISK: {step.tool_risk_level}
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-4 text-gray-400 text-[11px]">
          <div className="flex items-center space-x-1">
            <Cpu className="w-3 h-3 text-gray-500" />
            <span>{step.model_used}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Clock className="w-3 h-3 text-gray-500" />
            <span>{(step.duration_ms || 0).toFixed(0)} ms</span>
          </div>
        </div>
      </div>

      {/* Thought / Privacy-Filtered Reasoning */}
      {step.thought && (
        <div className="bg-[#0B0F17] border border-gray-800/80 rounded-lg p-3 text-gray-300 leading-relaxed text-[11px]">
          <span className="text-gray-500 font-semibold block mb-1">REASONING TRACE:</span>
          <p>{step.thought}</p>
        </div>
      )}

      {/* Policy Engine Evaluation Gate */}
      {step.policy_decision && (
        <div className="flex items-center justify-between bg-[#1F2937]/40 px-3 py-2 rounded-lg border border-gray-800 text-[11px]">
          <div className="flex items-center space-x-2">
            <Shield className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-gray-400">Policy Gate Decision:</span>
            <div className="flex items-center space-x-1 font-semibold">
              {getPolicyIcon(step.policy_decision)}
              <span
                className={
                  step.policy_decision === 'ALLOW'
                    ? 'text-emerald-400'
                    : step.policy_decision === 'REQUIRE_APPROVAL'
                    ? 'text-amber-400'
                    : 'text-rose-400'
                }
              >
                {step.policy_decision}
              </span>
            </div>
          </div>
          {step.policy_reason && (
            <span className="text-gray-400 text-[10px] truncate max-w-md" title={step.policy_reason}>
              {step.policy_reason}
            </span>
          )}
        </div>
      )}

      {/* Tool Call Arguments & Observation Collapsible */}
      {(step.tool_arguments || step.observation) && (
        <div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 text-gray-400 hover:text-gray-200 text-[11px] pt-1 transition-colors"
          >
            {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            <span>{isExpanded ? 'Hide Raw Tool IO' : 'Show Tool Arguments & Observation'}</span>
          </button>

          {isExpanded && (
            <div className="mt-2 space-y-2 text-[10px] bg-[#0B0F17] p-3 rounded-lg border border-gray-800">
              {step.tool_arguments && (
                <div>
                  <span className="text-gray-500 font-semibold block mb-1">INPUT ARGUMENTS:</span>
                  <pre className="text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(step.tool_arguments, null, 2)}
                  </pre>
                </div>
              )}
              {step.observation && (
                <div className="pt-2 border-t border-gray-800">
                  <span className="text-gray-500 font-semibold block mb-1">TOOL OBSERVATION:</span>
                  <pre className="text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                    {typeof step.observation === 'string'
                      ? step.observation
                      : JSON.stringify(step.observation, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
