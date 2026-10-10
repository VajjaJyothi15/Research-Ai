import React from 'react';
import {
  CheckCircle2,
  Loader2,
  AlertCircle,
  FileText,
  Clock,
  ExternalLink,
  Ban,
  ChevronRight,
} from 'lucide-react';

export interface StageEvent {
  stage: string;
  stage_label: string;
  stage_index: number;
  total_stages: number;
  progress_percent: number;
  message: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  timestamp: string;
  details?: Record<string, any>;
}

interface LiveProgressTimelineProps {
  currentStageIndex: number;
  progressPercent: number;
  status: string;
  events: StageEvent[];
  liveLog: string[];
  errorMessage?: string | null;
  onViewReport?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
  isCancelling?: boolean;
  isRetrying?: boolean;
}

const STAGES_METADATA = [
  {
    code: 'PLANNING',
    index: 1,
    title: 'Research planning',
    description: 'Decomposing inquiry into bounded, verifiable subquestions.',
  },
  {
    code: 'SEARCHING',
    index: 2,
    title: 'Web and academic search',
    description: 'Querying external web and academic knowledge repositories.',
  },
  {
    code: 'EXTRACTING',
    index: 3,
    title: 'Evidence extraction',
    description: 'Extracting factual claims, publication metadata, and quotations.',
  },
  {
    code: 'VERIFYING',
    index: 4,
    title: 'Cross-source verification',
    description: 'Auditing multi-source consistency and flagging contradictions.',
  },
  {
    code: 'ANALYZING',
    index: 5,
    title: 'Comparison and analysis',
    description: 'Generating statistical benchmarks and comparative metrics.',
  },
  {
    code: 'WRITING',
    index: 6,
    title: 'Report generation',
    description: 'Synthesizing evidence into an 8-part cited research report.',
  },
  {
    code: 'COMPLETED',
    index: 7,
    title: 'Completed',
    description: 'Research report compiled, verified, and saved.',
  },
];

export const LiveProgressTimeline: React.FC<LiveProgressTimelineProps> = ({
  currentStageIndex,
  progressPercent,
  status,
  events,
  liveLog,
  errorMessage,
  onViewReport,
  onCancel,
  onRetry,
  isCancelling,
  isRetrying,
}) => {
  const isCompleted = status === 'COMPLETED' || status === 'PARTIAL';
  const isFailed = status === 'FAILED';
  const isCancelled = status === 'CANCELLED';

  const getStageLatestMessage = (code: string, fallbackDesc: string) => {
    const matched = events.filter((e) => e.stage === code);
    if (matched.length > 0) {
      return matched[matched.length - 1].message;
    }
    return fallbackDesc;
  };

  return (
    <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 sm:p-8 space-y-6 shadow-xs">
      {/* Progress Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#C4B5FD]">
        <div>
          <div className="flex items-center space-x-2">
            <span
              className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                isCompleted
                  ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                  : isFailed
                  ? 'bg-[#FEE2E2] text-[#991B1B] border-[#FECACA]'
                  : isCancelled
                  ? 'bg-[#E5E7F9] text-[#334155] border-[#C4B5FD]'
                  : 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
              }`}
            >
              {isCompleted
                ? 'Research Finished'
                : isFailed
                ? 'Execution Failed'
                : isCancelled
                ? 'Research Cancelled'
                : `Stage ${Math.min(currentStageIndex, 6)} of 6 In Progress`}
            </span>
          </div>
          <h2 className="text-base font-bold text-[#312E81] mt-1">Live Research Progress</h2>
          <p className="text-xs text-[#334155]">
            Real-time backend execution stream with multi-source verification.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Progress Percent Badge */}
          <div className="text-right">
            <div className="text-xl font-bold font-mono text-[#312E81]">
              {isCompleted ? 100 : progressPercent}%
            </div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-[#312E81]/60">
              {isCompleted ? 'Complete' : 'Progress'}
            </div>
          </div>

          {/* Action Buttons */}
          {isCompleted && onViewReport && (
            <button
              onClick={onViewReport}
              className="px-4 py-2 bg-[#635BFF] hover:bg-[#4F46E5] text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>View Full Report</span>
            </button>
          )}

          {isFailed && onRetry && (
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="px-4 py-2 bg-[#635BFF] hover:bg-[#4F46E5] text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{isRetrying ? 'Retrying...' : 'Retry Research'}</span>
            </button>
          )}

          {!isCompleted && !isFailed && !isCancelled && onCancel && (
            <button
              onClick={onCancel}
              disabled={isCancelling}
              className="px-3 py-1.5 bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] rounded-lg text-xs font-medium transition-colors flex items-center space-x-1 disabled:opacity-50"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>{isCancelling ? 'Cancelling...' : 'Cancel'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-[#E5E7F9] rounded-full h-2 overflow-hidden border border-[#C4B5FD]/50">
        <div
          className={`h-full transition-all duration-500 ease-out ${
            isCompleted
              ? 'bg-[#0F9D91]'
              : isFailed
              ? 'bg-[#DC2626]'
              : isCancelled
              ? 'bg-[#94A3B8]'
              : 'bg-[#635BFF]'
          }`}
          style={{ width: `${isCompleted ? 100 : progressPercent}%` }}
        />
      </div>

      {/* Error Banner */}
      {isFailed && (
        <div className="p-4 bg-[#FEE2E2] border border-[#FECACA] rounded-lg text-[#991B1B] text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold">Research execution encountered an error:</span>
              <p>{errorMessage || 'An unexpected server error occurred during pipeline execution.'}</p>
            </div>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="px-3 py-1.5 bg-[#991B1B] hover:bg-[#7F1D1D] text-white rounded-md text-xs font-medium shrink-0 self-start sm:self-auto transition-colors disabled:opacity-50"
            >
              {isRetrying ? 'Retrying...' : 'Retry Now'}
            </button>
          )}
        </div>
      )}

      {/* Vertical Stepper Timeline */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#C4B5FD]">
        {STAGES_METADATA.map((stage) => {
          const isStageCompleted =
            isCompleted || currentStageIndex > stage.index;
          const isStageCurrent =
            !isCompleted && !isFailed && !isCancelled && currentStageIndex === stage.index;
          const isStageFailed = isFailed && currentStageIndex === stage.index;
          const isStagePending = !isStageCompleted && !isStageCurrent && !isStageFailed;

          const stageMessage = getStageLatestMessage(stage.code, stage.description);

          return (
            <div key={stage.code} className="relative flex items-start space-x-3.5">
              {/* Step Marker */}
              <div
                className={`absolute -left-6 flex items-center justify-center w-6 h-6 rounded-full border text-xs font-semibold transition-colors ${
                  isStageCompleted
                    ? 'border-[#0F9D91] text-[#0F9D91] bg-[#DDF7F0]'
                    : isStageCurrent
                    ? 'border-[#635BFF] text-[#635BFF] bg-[#DCEBFF]'
                    : isStageFailed
                    ? 'border-[#DC2626] text-[#DC2626] bg-[#FEE2E2]'
                    : 'border-[#C4B5FD] text-[#334155]/60 bg-[#E9E4FF]'
                }`}
              >
                {isStageCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-[#0F9D91]" />
                ) : isStageCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 text-[#635BFF] animate-spin" />
                ) : isStageFailed ? (
                  <AlertCircle className="w-3.5 h-3.5 text-[#DC2626]" />
                ) : (
                  <span>{stage.index}</span>
                )}
              </div>

              {/* Stage Content */}
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3
                    className={`text-xs font-bold ${
                      isStageCompleted
                        ? 'text-[#312E81]'
                        : isStageCurrent
                        ? 'text-[#635BFF]'
                        : isStageFailed
                        ? 'text-[#DC2626]'
                        : 'text-[#334155]/60'
                    }`}
                  >
                    {stage.index}. {stage.title}
                  </h3>

                  {isStageCompleted && (
                    <span className="text-[10px] text-[#0F9D91] font-medium bg-[#DDF7F0] px-2 py-0.5 rounded-full border border-[#A7F3D0]">
                      Done
                    </span>
                  )}
                  {isStageCurrent && (
                    <span className="text-[10px] text-[#635BFF] font-medium bg-[#DCEBFF] px-2 py-0.5 rounded-full border border-[#BFDBFE] flex items-center space-x-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#635BFF] animate-ping" />
                      <span>Active</span>
                    </span>
                  )}
                  {isStagePending && (
                    <span className="text-[10px] text-[#334155]/50 font-medium">Pending</span>
                  )}
                </div>

                <p
                  className={`text-xs leading-relaxed ${
                    isStageCurrent
                      ? 'text-[#312E81] font-medium'
                      : isStageCompleted
                      ? 'text-[#334155]'
                      : 'text-[#334155]/60'
                  }`}
                >
                  {stageMessage}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Activity Stream Console */}
      <div className="bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg p-4 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-semibold text-[#312E81] uppercase tracking-wider">
          <span>Backend Event Activity</span>
          <span className="font-mono text-[#334155]/70">{liveLog.length} events logged</span>
        </div>

        <div className="bg-[#EDE9FE] border border-[#C4B5FD] rounded p-3 text-xs text-[#334155] font-mono space-y-1.5 max-h-36 overflow-y-auto">
          {liveLog.length === 0 ? (
            <p className="text-[#334155]/60 italic font-sans">Connecting to live execution stream...</p>
          ) : (
            liveLog.map((logItem, idx) => (
              <div key={idx} className="flex items-start space-x-2">
                <span className="text-[#635BFF] shrink-0 select-none">→</span>
                <span className="break-words">{logItem}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
