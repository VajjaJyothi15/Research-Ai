import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  History,
  RotateCcw,
  ArrowRight,
  Loader2,
  Trash2,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  X,
} from 'lucide-react';
import { api } from '../services/api';

export const ResearchHistory: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [confirmClearOpen, setConfirmClearOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: runs, isLoading } = useQuery({
    queryKey: ['researchRuns'],
    queryFn: api.listResearchRuns,
  });

  const rerunMutation = useMutation({
    mutationFn: (id: string) => api.rerunResearch(id),
    onSuccess: (data) => {
      navigate(`/workspace/${data.id}`);
    },
    onError: (err: any) => {
      setErrorMessage(err?.message || 'Failed to rerun research.');
    },
  });

  const clearHistoryMutation = useMutation({
    mutationFn: api.clearResearchHistory,
    onSuccess: (data) => {
      setConfirmClearOpen(false);
      setSuccessMessage(data.message || 'Successfully cleared all research history.');
      queryClient.invalidateQueries({ queryKey: ['researchRuns'] });
      setTimeout(() => setSuccessMessage(null), 5000);
    },
    onError: (err: any) => {
      setConfirmClearOpen(false);
      setErrorMessage(err?.message || 'Failed to clear research history.');
      setTimeout(() => setErrorMessage(null), 5000);
    },
  });

  const formatMode = (m?: string) => {
    if (!m) return 'STANDARD';
    const lower = m.toLowerCase();
    if (lower === 'quick') return 'QUICK';
    if (lower.includes('depth') || lower === 'deep' || lower === 'academic') return 'IN-DEPTH';
    return 'STANDARD';
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header with Title and Clear History Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#312E81] flex items-center space-x-2.5">
            <History className="w-6 h-6 text-[#635BFF]" />
            <span>Research History</span>
          </h1>
          <p className="text-[#334155] text-xs sm:text-sm mt-0.5">
            Reopen past research reports, inspect verified sources, or rerun investigations with fresh evidence.
          </p>
        </div>

        <div>
          <button
            onClick={() => setConfirmClearOpen(true)}
            disabled={isLoading || !runs || runs.length === 0 || clearHistoryMutation.isPending}
            className="px-3.5 py-2 rounded-lg bg-[#FEE2E2] hover:bg-[#FECACA] text-[#991B1B] border border-[#FECACA] text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
            title="Delete all saved research sessions"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Research History</span>
          </button>
        </div>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="p-3.5 bg-[#DDF7F0] border border-[#A7F3D0] text-[#065F46] text-xs rounded-lg flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-[#0F9D91] shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-[#065F46] hover:text-[#047857]">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="p-3.5 bg-[#FEE2E2] border border-[#FECACA] text-[#991B1B] text-xs rounded-lg flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-[#991B1B] hover:text-[#7F1D1D]">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-8 text-center text-[#334155] text-xs shadow-xs">
          <Loader2 className="w-5 h-5 animate-spin mx-auto text-[#635BFF] mb-2" />
          <p>Loading research history...</p>
        </div>
      ) : !runs || runs.length === 0 ? (
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-10 text-center text-[#334155] text-xs shadow-xs space-y-2">
          <p className="font-semibold text-[#312E81]">No saved research projects found.</p>
          <p className="text-[11px] text-[#334155]/70">
            Submit a research question from the Dashboard to generate your first verified report.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <div
              key={run.id}
              className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs hover:border-[#635BFF] transition-colors"
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] px-2 py-0.5 rounded bg-[#DCEBFF] text-[#312E81] border border-[#BFDBFE] font-mono font-bold">
                    {formatMode(run.mode)}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                      run.status === 'COMPLETED' || run.status === 'PARTIAL'
                        ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                        : run.status === 'PENDING_APPROVAL'
                        ? 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
                        : 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
                    }`}
                  >
                    {run.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-[#312E81] leading-snug">{run.question}</h3>
                <p className="text-xs text-[#334155]">
                  Domain: {run.domain} • Submitted on {new Date(run.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                </p>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <button
                  onClick={() => rerunMutation.mutate(run.id)}
                  disabled={rerunMutation.isPending}
                  className="px-3 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1.5 transition-colors disabled:opacity-50 shadow-xs"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-[#334155]" />
                  <span>Research again</span>
                </button>

                <button
                  onClick={() =>
                    navigate(
                      run.status === 'COMPLETED' || run.status === 'PARTIAL'
                        ? `/report/${run.id}`
                        : `/workspace/${run.id}`
                    )
                  }
                  className="px-3.5 py-1.5 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white font-medium text-xs shadow-xs transition-colors flex items-center space-x-1"
                >
                  <span>{run.status === 'COMPLETED' || run.status === 'PARTIAL' ? 'Open Report' : 'Open Workspace'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Clear Research History Confirmation Modal */}
      {confirmClearOpen && (
        <div className="fixed inset-0 z-50 bg-[#312E81]/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 max-w-md w-full space-y-4 shadow-xl">
            <div className="flex items-center space-x-3 text-[#991B1B]">
              <div className="p-2 rounded-full bg-[#FEE2E2] border border-[#FECACA]">
                <AlertTriangle className="w-5 h-5 text-[#DC2626]" />
              </div>
              <h3 className="text-sm font-bold text-[#312E81]">Clear All Research History?</h3>
            </div>

            <p className="text-xs text-[#334155] leading-relaxed">
              This action will permanently delete all {runs?.length || 0} saved research sessions, generated reports, extracted evidence records, and primary sources from the database.
            </p>

            <div className="p-3 bg-[#FEE2E2] border border-[#FECACA] rounded-lg text-[11px] text-[#991B1B]">
              <strong>Warning:</strong> This action cannot be undone. Page refresh will reflect the cleared state.
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setConfirmClearOpen(false)}
                disabled={clearHistoryMutation.isPending}
                className="px-3.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] text-xs font-medium border border-[#C4B5FD]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => clearHistoryMutation.mutate()}
                disabled={clearHistoryMutation.isPending}
                className="px-4 py-1.5 rounded-lg bg-[#DC2626] hover:bg-[#B91C1C] text-white text-xs font-semibold shadow-xs flex items-center space-x-1.5 transition-colors disabled:opacity-50"
              >
                {clearHistoryMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Yes, Clear History</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

