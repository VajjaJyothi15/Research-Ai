import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RotateCcw,
  Edit3,
  FileText,
  Activity,
  ArrowDown,
  AlertCircle,
  Loader2,
  ChevronDown,
  CheckCircle2,
  Play,
  Layers,
  Database,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';
import { ResearchPlan, ResearchRun } from '../types';
import { LiveProgressTimeline, StageEvent } from '../components/research/LiveProgressTimeline';

// Helper to determine short, meaningful step titles
function getStepTitle(sq: any, index: number): string {
  if (!sq) return `Step ${index + 1}: Key Investigation`;
  if (typeof sq === 'object' && sq.title && sq.title.trim()) {
    return sq.title.trim();
  }
  const text = typeof sq === 'string' ? sq : sq.question || '';
  if (!text) return `Step ${index + 1}: Key Investigation`;

  const lower = text.toLowerCase();
  if (lower.includes('foundation') || lower.includes('concept') || lower.includes('architect') || lower.includes('basic')) {
    return 'Understand Core Foundations';
  }
  if (lower.includes('metric') || lower.includes('benchmark') || lower.includes('performance') || lower.includes('empirical') || lower.includes('finding')) {
    return 'Evaluate Performance Benchmarks';
  }
  if (lower.includes('challenge') || lower.includes('security') || lower.includes('trade-off') || lower.includes('risk') || lower.includes('limitation')) {
    return 'Investigate Security & Trade-offs';
  }
  if (lower.includes('implement') || lower.includes('application') || lower.includes('case study') || lower.includes('real-world')) {
    return 'Examine Practical Implementations';
  }
  if (lower.includes('compare') || lower.includes('alternative') || lower.includes('compet') || lower.includes('versus')) {
    return 'Compare Alternative Solutions';
  }
  if (lower.includes('future') || lower.includes('trend') || lower.includes('roadmap') || lower.includes('recommend')) {
    return 'Identify Future Trends & Standards';
  }

  let cleaned = text
    .replace(/^what (are|is) (the|a)?/i, '')
    .replace(/^how (do|does|can|will)/i, '')
    .replace(/^identify (the|a)?/i, '')
    .replace(/^analyze (the|a)?/i, '')
    .replace(/\?$/g, '')
    .trim();

  if (cleaned.length > 0) {
    cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  }
  const words = cleaned.split(/\s+/);
  if (words.length > 6) {
    return words.slice(0, 5).join(' ');
  }
  return cleaned || `Step ${index + 1}: Research Investigation`;
}

function getStepQuestion(sq: any): string {
  if (!sq) return '';
  if (typeof sq === 'string') return sq;
  return sq.question || '';
}

const STAGE_TO_INDEX: Record<string, number> = {
  PLANNING: 1,
  SEARCHING: 2,
  EXTRACTING: 3,
  VERIFYING: 4,
  ANALYZING: 5,
  WRITING: 6,
  CITATION_AUDIT: 6,
  COMPLETED: 7,
};

export const ResearchWorkspace: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showEditModal, setShowEditModal] = useState(false);
  const [editedMainQuestion, setEditedMainQuestion] = useState('');
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [liveLog, setLiveLog] = useState<string[]>([]);
  const [currentStageIndex, setCurrentStageIndex] = useState(1);
  const [progressPercent, setProgressPercent] = useState(15);
  const [regenError, setRegenError] = useState<string | null>(null);

  const { data: run, refetch: refetchRun } = useQuery({
    queryKey: ['researchRun', id],
    queryFn: () => api.getResearchRun(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data as ResearchRun | undefined;
      return data?.status === 'SEARCHING' || data?.status === 'EXTRACTING' || data?.status === 'VERIFYING' || data?.status === 'ANALYZING' || data?.status === 'WRITING'
        ? 2000
        : false;
    },
  });

  const { data: plan, refetch: refetchPlan } = useQuery({
    queryKey: ['researchPlan', id],
    queryFn: () => api.getPlan(id!),
    enabled: !!id,
  });

  const isRunning =
    run?.status === 'SEARCHING' ||
    run?.status === 'EXTRACTING' ||
    run?.status === 'VERIFYING' ||
    run?.status === 'ANALYZING' ||
    run?.status === 'WRITING';

  const { data: sources, refetch: refetchSources } = useQuery({
    queryKey: ['sources', id],
    queryFn: () => api.getSources(id!),
    enabled: !!id,
    refetchInterval: isRunning ? 2500 : false,
  });

  const { data: toolCalls, refetch: refetchToolCalls } = useQuery({
    queryKey: ['toolCalls', id],
    queryFn: () => api.getToolCalls(id!),
    enabled: !!id,
    refetchInterval: isRunning ? 2500 : false,
  });

  // Server-Sent Events (SSE) Listener for real-time backend updates
  useEffect(() => {
    if (!id) return;

    setEvents([]);
    setLiveLog([]);

    const es = new EventSource(`/api/v1/research/${id}/events`);

    es.addEventListener('stage_update', (e) => {
      try {
        const payload: StageEvent = JSON.parse(e.data);

        setEvents((prev) => {
          const exists = prev.some((item) => item.timestamp === payload.timestamp && item.message === payload.message);
          if (exists) return prev;
          return [...prev, payload];
        });

        if (payload.progress_percent !== undefined) {
          setProgressPercent(payload.progress_percent);
        }

        if (payload.stage_index) {
          setCurrentStageIndex(payload.stage_index);
        } else if (STAGE_TO_INDEX[payload.stage]) {
          setCurrentStageIndex(STAGE_TO_INDEX[payload.stage]);
        }

        if (payload.message) {
          setLiveLog((prev) => {
            if (prev.includes(payload.message)) return prev;
            return [...prev, payload.message];
          });
        }

        refetchRun();
        refetchSources();
        refetchToolCalls();
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    });

    es.onerror = (err) => {
      console.warn('SSE connection interrupted, retrying in background...', err);
    };

    return () => {
      es.close();
    };
  }, [id, refetchRun, refetchSources, refetchToolCalls]);

  const approveMutation = useMutation({
    mutationFn: () => api.approvePlan(id!),
    onSuccess: () => {
      refetchRun();
      queryClient.invalidateQueries({ queryKey: ['researchRun', id] });
    },
  });

  const regenMutation = useMutation({
    mutationFn: (userFeedback: string) => api.regeneratePlan(id!, userFeedback),
    onMutate: () => {
      setRegenError(null);
    },
    onSuccess: (updatedPlan) => {
      setRegenError(null);
      queryClient.setQueryData(['researchPlan', id], updatedPlan);
      queryClient.invalidateQueries({ queryKey: ['researchPlan', id] });
      queryClient.invalidateQueries({ queryKey: ['researchRun', id] });
      refetchPlan();
      refetchRun();
    },
    onError: (err: any) => {
      setRegenError(err?.response?.data?.detail || err?.message || 'Failed to generate alternative plan.');
    },
  });

  const editMutation = useMutation({
    mutationFn: () => api.editPlan(id!, { main_question: editedMainQuestion }),
    onSuccess: () => {
      setShowEditModal(false);
      refetchPlan();
      refetchRun();
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => api.cancelResearch(id!),
    onSuccess: () => {
      refetchRun();
    },
  });

  const isPendingApproval = run?.status === 'PENDING_APPROVAL';
  const isCompleted = run?.status === 'COMPLETED' || run?.status === 'PARTIAL';

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Workspace Header Card */}
      <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span
              className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                isCompleted
                  ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                  : isPendingApproval
                  ? 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
                  : 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
              }`}
            >
              {isPendingApproval ? 'Plan Review Required' : isCompleted ? 'Completed' : 'Running'}
            </span>
            <span className="text-xs text-[#334155]/70 font-mono">ID: {id?.slice(0, 8)}</span>
          </div>
          <h1 className="text-lg font-bold text-[#312E81] leading-snug">{run?.question}</h1>
        </div>

        <div className="flex items-center space-x-2">
          {isCompleted && (
            <button
              onClick={() => navigate(`/report/${id}`)}
              className="px-4 py-2 bg-[#635BFF] hover:bg-[#4F46E5] text-white rounded-lg text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>Read Report</span>
            </button>
          )}
        </div>
      </div>

      {/* Plan Review Flowchart (When Pending Approval) */}
      {isPendingApproval && plan && (
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 sm:p-8 space-y-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#C4B5FD]">
            <div>
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#DCEBFF] text-[#312E81] text-xs font-semibold border border-[#BFDBFE] mb-1">
                <Layers className="w-3.5 h-3.5 text-[#635BFF]" />
                <span>Proposed Research Plan</span>
              </div>
              <h2 className="text-base font-bold text-[#312E81]">Review Execution Steps</h2>
              <p className="text-xs text-[#334155]">
                ResAI will execute these investigation steps across primary sources.
              </p>
            </div>
            <div className="text-xs text-[#312E81] font-medium">
              Version {plan.version || 1}
            </div>
          </div>

          {/* Regenerate Error Alert */}
          {regenError && (
            <div className="p-3.5 rounded-lg bg-[#FEE2E2] border border-[#FECACA] text-[#991B1B] text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
              <span>{regenError}</span>
            </div>
          )}

          {/* Flowchart Diagram */}
          <div className="relative py-2 px-2 max-w-xl mx-auto">
            {regenMutation.isPending && (
              <div className="absolute inset-0 z-20 bg-[#E9E4FF]/90 backdrop-blur-xs rounded-xl flex flex-col items-center justify-center space-y-2 p-6">
                <Loader2 className="w-6 h-6 text-[#635BFF] animate-spin" />
                <span className="text-xs font-semibold text-[#312E81]">Generating alternative research plan...</span>
              </div>
            )}

            <div className="space-y-0">
              {/* Question Step */}
              <div className="w-full p-4 rounded-xl bg-[#DCEBFF] border border-[#C4B5FD] space-y-1 shadow-xs">
                <div className="text-[10px] font-bold text-[#635BFF] uppercase tracking-wider">
                  Primary Research Objective
                </div>
                <h3 className="text-xs font-semibold text-[#312E81] leading-relaxed">
                  {plan.main_question}
                </h3>
              </div>

              {/* Arrow */}
              <div className="flex justify-center py-1.5">
                <ArrowDown className="w-4 h-4 text-[#635BFF]" />
              </div>

              {/* Subquestions Steps */}
              {plan.subquestions_json?.map((sq: any, idx: number) => {
                const title = getStepTitle(sq, idx);
                const question = getStepQuestion(sq);
                return (
                  <React.Fragment key={idx}>
                    <div className="w-full p-4 rounded-xl bg-[#E5E7F9] border border-[#C4B5FD] space-y-1 hover:border-[#635BFF] transition-colors shadow-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-[#312E81]/70 uppercase tracking-wider">
                          Step {idx + 1}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-[#312E81]">
                        {title}
                      </h4>
                      {question && question !== title && (
                        <p className="text-xs text-[#334155] leading-relaxed pt-0.5">
                          {question}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-center py-1.5">
                      <ArrowDown className="w-4 h-4 text-[#635BFF]" />
                    </div>
                  </React.Fragment>
                );
              })}

              {/* Final Step */}
              <div className="w-full p-4 rounded-xl bg-[#DDF7F0] border border-[#A7F3D0] space-y-1 shadow-xs">
                <div className="text-[10px] font-bold text-[#0F9D91] uppercase tracking-wider">
                  Final Output
                </div>
                <h4 className="text-xs font-bold text-[#065F46]">
                  Generate Verified Evidence Report
                </h4>
                <p className="text-xs text-[#047857] leading-relaxed">
                  Synthesizes evidence claims, resolves cross-source contradictions, and compiles an 8-part report with cited sources.
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-end gap-2.5 pt-4 border-t border-[#C4B5FD]">
            <button
              onClick={() => {
                setEditedMainQuestion(plan.main_question);
                setShowEditModal(true);
              }}
              className="px-3.5 py-2 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] text-xs font-medium border border-[#C4B5FD] flex items-center space-x-1.5 transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit plan</span>
            </button>

            <button
              onClick={() =>
                regenMutation.mutate('Generate an alternative research plan with different analytical perspectives.')
              }
              disabled={regenMutation.isPending}
              className="px-3.5 py-2 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] text-xs font-medium border border-[#C4B5FD] flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              {regenMutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#635BFF]" />
                  <span>Regenerating...</span>
                </>
              ) : (
                <>
                  <RotateCcw className="w-3.5 h-3.5 text-[#635BFF]" />
                  <span>Try another plan</span>
                </>
              )}
            </button>

            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending || regenMutation.isPending}
              className="px-5 py-2 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white font-semibold text-xs shadow-xs flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              {approveMutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Starting research...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Looks good — start research</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Live Research Progress Stepper (When Approved / Executing / Completed) */}
      {!isPendingApproval && (
        <LiveProgressTimeline
          currentStageIndex={isCompleted ? 7 : currentStageIndex}
          progressPercent={isCompleted ? 100 : progressPercent}
          status={run?.status || 'SEARCHING'}
          events={events}
          liveLog={liveLog}
          errorMessage={run?.status === 'FAILED' ? (run?.policy_json?.error_message || 'Research pipeline encountered an error.') : null}
          onViewReport={() => navigate(`/report/${id}`)}
          onCancel={() => cancelMutation.mutate()}
          onRetry={() => approveMutation.mutate()}
          isCancelling={cancelMutation.isPending}
          isRetrying={approveMutation.isPending}
        />
      )}

      {/* Advanced Details Accordion */}
      <details className="group bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-5 shadow-xs transition-all" open>
        <summary className="text-xs font-semibold text-[#312E81] cursor-pointer flex items-center justify-between list-none">
          <span className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-[#635BFF]" />
            <span>Discovered Sources ({sources?.length || 0}) & Tool Call Audits ({toolCalls?.length || 0})</span>
          </span>
          <ChevronDown className="w-4 h-4 text-[#312E81]/60 group-open:rotate-180 transition-transform" />
        </summary>

        <div className="mt-4 space-y-6 pt-4 border-t border-[#C4B5FD] text-xs text-[#334155]">
          {/* Discovered Sources Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-[#312E81] flex items-center space-x-1.5">
                <Database className="w-4 h-4 text-[#635BFF]" />
                <span>Discovered Primary Sources ({sources?.length || 0})</span>
              </h4>
              <span className="text-[11px] text-[#334155]/70">
                Primary evidence retrieved from web and academic indexes
              </span>
            </div>

            {sources && sources.length > 0 ? (
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {sources.map((s, idx) => {
                  const isAcademic = s.source_type === 'academic' || s.domain?.includes('arxiv') || s.domain?.includes('crossref') || s.domain?.includes('openalex');
                  return (
                    <div
                      key={s.id || idx}
                      className="p-3.5 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] hover:border-[#635BFF] transition-colors flex flex-col sm:flex-row sm:items-start justify-between gap-3 shadow-xs"
                    >
                      <div className="space-y-1 flex-1">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-[#DCEBFF] text-[#312E81] border border-[#BFDBFE]">
                            [{idx + 1}]
                          </span>
                          <span
                            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                              isAcademic
                                ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                                : 'bg-[#DCEBFF] text-[#635BFF] border-[#BFDBFE]'
                            }`}
                          >
                            {isAcademic ? 'Academic' : 'Web'}
                          </span>
                          <span className="text-[11px] text-[#334155]/70 font-mono">
                            {s.domain || 'web'} {s.publication_date ? `• ${s.publication_date}` : ''}
                          </span>
                          {s.author && (
                            <span className="text-[11px] text-[#334155]/80 italic">
                              by {s.author}
                            </span>
                          )}
                        </div>
                        <p className="font-bold text-[#312E81] text-xs sm:text-sm">{s.title}</p>
                        {s.content_text && (
                          <p className="text-[11px] text-[#334155]/80 line-clamp-2 leading-relaxed">
                            {s.content_text}
                          </p>
                        )}
                      </div>

                      {s.url && (
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1.5 rounded-lg bg-[#E9E4FF] hover:bg-[#DCD6FA] text-[#635BFF] border border-[#C4B5FD] text-[11px] font-semibold flex items-center space-x-1 shrink-0 transition-colors shadow-xs self-start"
                        >
                          <span>Open source</span>
                        </a>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : isRunning ? (
              <div className="p-4 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] text-center space-y-1.5">
                <Loader2 className="w-4 h-4 text-[#635BFF] animate-spin mx-auto" />
                <p className="text-xs text-[#312E81] font-medium">Searching web and academic databases...</p>
                <p className="text-[11px] text-[#334155]/70">Primary sources will appear here as tool calls retrieve them.</p>
              </div>
            ) : (
              <div className="p-3.5 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] text-xs text-[#334155]/80">
                <p className="font-semibold text-[#312E81]">No external sources fetched yet.</p>
                <p className="text-[11px] text-[#334155]/70 pt-0.5">
                  Web search (Tavily/DDG) and academic indexes (arXiv/Crossref/OpenAlex) will populate discovered sources upon execution.
                </p>
              </div>
            )}
          </div>

          {/* Tool Call Audits Section */}
          <div className="space-y-3 pt-2 border-t border-[#C4B5FD]">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-[#312E81] flex items-center space-x-1.5">
                <Terminal className="w-4 h-4 text-[#0F9D91]" />
                <span>Tool Call Audits ({toolCalls?.length || 0})</span>
              </h4>
              <span className="text-[11px] text-[#334155]/70">
                Sandboxed tool dispatches logged with runtime parameters and execution latency
              </span>
            </div>

            {toolCalls && toolCalls.length > 0 ? (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {toolCalls.map((tc, idx) => {
                  const isSuccess = tc.status === 'SUCCESS';
                  const isFailed = tc.status === 'FAILED';
                  const queryText = tc.arguments_json?.query || tc.arguments_json?.url || tc.arguments_json?.markdown_text?.slice(0, 40);

                  return (
                    <div
                      key={tc.id || idx}
                      className="p-3 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] space-y-1 text-xs"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-1.5">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-[#312E81] px-2 py-0.5 rounded bg-[#DCEBFF] border border-[#BFDBFE] text-[11px]">
                            {tc.tool_name}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                              isSuccess
                                ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                                : isFailed
                                ? 'bg-[#FEE2E2] text-[#DC2626] border-[#FECACA]'
                                : 'bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]'
                            }`}
                          >
                            {tc.status}
                          </span>
                          {tc.stage && (
                            <span className="text-[10px] font-mono text-[#334155]/70">
                              [{tc.stage}]
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-2 text-[11px] font-mono text-[#334155]/70">
                          <span>{tc.duration_ms}ms</span>
                          {tc.retry_count > 0 && <span>(retry {tc.retry_count})</span>}
                        </div>
                      </div>

                      {queryText && (
                        <div className="text-[11px] text-[#334155] font-mono bg-[#E9E4FF] p-1.5 rounded border border-[#C4B5FD] truncate">
                          <span className="text-[#635BFF] font-semibold">arg:</span> {queryText}
                        </div>
                      )}

                      {tc.result_summary && (
                        <p className="text-[11px] text-[#334155]/80">
                          {tc.result_summary}
                        </p>
                      )}

                      {tc.error_message && (
                        <p className="text-[11px] text-[#DC2626] font-semibold bg-[#FEE2E2] p-1.5 rounded border border-[#FECACA]">
                          Error: {tc.error_message}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : isRunning ? (
              <div className="p-4 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] text-center space-y-1.5">
                <Loader2 className="w-4 h-4 text-[#0F9D91] animate-spin mx-auto" />
                <p className="text-xs text-[#312E81] font-medium">Executing sandboxed tool calls...</p>
                <p className="text-[11px] text-[#334155]/70">Audited tool dispatches will appear here with runtime parameters.</p>
              </div>
            ) : (
              <div className="p-3.5 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] text-xs text-[#334155]/80">
                <p className="font-semibold text-[#312E81]">No tool calls logged yet.</p>
                <p className="text-[11px] text-[#334155]/70 pt-0.5">
                  Sandboxed web search, academic query, and citation validation tools will be recorded during research runs.
                </p>
              </div>
            )}
          </div>
        </div>
      </details>

      {/* Edit Plan Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-[#312E81]/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 max-w-lg w-full space-y-4 shadow-lg">
            <h3 className="text-sm font-bold text-[#312E81]">Edit Research Plan Question</h3>
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-[#334155]">Primary Question</label>
              <textarea
                rows={3}
                value={editedMainQuestion}
                onChange={(e) => setEditedMainQuestion(e.target.value)}
                className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg p-3 text-xs text-[#312E81] focus:outline-none focus:border-[#635BFF]"
              />
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-3.5 py-2 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] text-xs font-medium border border-[#C4B5FD]"
              >
                Cancel
              </button>
              <button
                onClick={() => editMutation.mutate()}
                disabled={editMutation.isPending}
                className="px-4 py-2 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white text-xs font-semibold transition-colors"
              >
                {editMutation.isPending ? 'Saving...' : 'Save Edits'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
