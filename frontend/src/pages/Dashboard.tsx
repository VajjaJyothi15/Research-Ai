import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Sparkles,
  FileText,
  ArrowRight,
  ShieldCheck,
  Clock,
  Loader2,
  AlertCircle,
  PlusCircle,
  Search,
} from 'lucide-react';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const [question, setQuestion] = useState('');
  const [depth, setDepth] = useState<'quick' | 'standard' | 'indepth'>('standard');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: runs, isLoading } = useQuery({
    queryKey: ['researchRuns'],
    queryFn: api.listResearchRuns,
  });

  const createMutation = useMutation({
    mutationFn: api.createResearch,
    onMutate: () => {
      setErrorMessage(null);
    },
    onSuccess: (data) => {
      navigate(`/workspace/${data.id}`);
    },
    onError: (err: any) => {
      setErrorMessage(
        err?.response?.data?.detail || err?.message || 'Failed to create research plan.'
      );
    },
  });

  const handleStartResearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || question.trim().length < 5) {
      setErrorMessage('Please enter a research question with at least 5 characters.');
      return;
    }

    createMutation.mutate({
      question: question.trim(),
      mode: depth,
      domain: 'general',
    });
  };

  const handleTryDemo = () => {
    setQuestion('What are the latest developments in quantum error correction for 2026?');
    setDepth('standard');
    setErrorMessage(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Header */}
      <div className="text-center space-y-2.5 pt-2">
        <div className="inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full bg-[#DCEBFF] border border-[#BFDBFE] text-[#312E81] text-xs font-semibold shadow-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-[#635BFF]" />
          <span>Evidence-Grounded AI Research</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#312E81] tracking-tight">
          Ask a research question. Get a verified report.
        </h1>
        <p className="text-[#334155] text-xs sm:text-sm max-w-xl mx-auto">
          ResAI builds a research plan for your approval, searches real web and academic sources, checks for contradictions, and writes an evidence-backed report with citations.
        </p>
      </div>

      {/* Main Research Form Card */}
      <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 sm:p-8 space-y-6 shadow-xs">
        <form onSubmit={handleStartResearch} className="space-y-5">
          {errorMessage && (
            <div className="p-3 bg-[#FEE2E2] border border-[#FECACA] text-[#991B1B] text-xs rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Question Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold uppercase tracking-wider text-[#312E81]">
                Research Question <span className="text-[#635BFF]">*</span>
              </label>
              <button
                type="button"
                onClick={handleTryDemo}
                className="text-xs text-[#635BFF] hover:text-[#4F46E5] flex items-center space-x-1 font-medium"
              >
                <Sparkles className="w-3 h-3" />
                <span>Try an example</span>
              </button>
            </div>

            <textarea
              required
              rows={3}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                if (errorMessage) setErrorMessage(null);
              }}
              placeholder="e.g. What are the key performance metrics and security trade-offs of autonomous AI agents?"
              className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg p-3.5 text-[#312E81] placeholder-[#334155]/60 focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE] text-xs sm:text-sm leading-relaxed"
            />
          </div>

          {/* Depth Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-[#312E81]">
              Investigation Depth
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'quick', label: 'Quick', desc: 'Fast overview with 2 targeted subquestions.' },
                { id: 'standard', label: 'Standard', desc: 'Balanced multi-source web & academic search.' },
                { id: 'indepth', label: 'In-depth', desc: 'Comprehensive literature review and verification.' },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => setDepth(item.id as 'quick' | 'standard' | 'indepth')}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    depth === item.id
                      ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                      : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#312E81]">{item.label}</span>
                    {depth === item.id && (
                      <span className="w-2 h-2 rounded-full bg-[#635BFF]" />
                    )}
                  </div>
                  <p className="text-[11px] text-[#334155] mt-0.5 leading-snug">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Submit CTA */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={createMutation.isPending || !question.trim()}
              className="w-full py-2.5 px-4 rounded-lg text-xs sm:text-sm font-semibold bg-[#635BFF] hover:bg-[#4F46E5] text-white shadow-xs transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Formulating Research Plan...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Create Research Plan</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Recent Research Runs */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#312E81]/80">
            Recent Research
          </h2>
          <Link to="/history" className="text-xs text-[#635BFF] hover:underline font-medium">
            View all
          </Link>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-[#334155]/70 text-xs bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl">
            Loading recent research...
          </div>
        ) : runs && runs.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {runs.slice(0, 4).map((r) => (
              <div
                key={r.id}
                onClick={() => navigate(r.status === 'COMPLETED' || r.status === 'PARTIAL' ? `/report/${r.id}` : `/workspace/${r.id}`)}
                className="p-4 bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl hover:border-[#635BFF] cursor-pointer transition-colors space-y-2 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      r.status === 'COMPLETED' || r.status === 'PARTIAL'
                        ? 'bg-[#DDF7F0] text-[#0F9D91] border-[#A7F3D0]'
                        : r.status === 'PENDING_APPROVAL'
                        ? 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
                        : 'bg-[#DCEBFF] text-[#312E81] border-[#BFDBFE]'
                    }`}
                  >
                    {r.status === 'PENDING_APPROVAL' ? 'Needs Review' : r.status === 'COMPLETED' ? 'Report Ready' : 'In Progress'}
                  </span>
                  <span className="text-[11px] text-[#334155]/70 font-mono">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
                <h3 className="text-xs font-bold text-[#312E81] line-clamp-2 leading-snug">
                  {r.question}
                </h3>
                <div className="flex items-center text-xs text-[#635BFF] font-medium pt-1">
                  <span>Open workspace</span>
                  <ArrowRight className="w-3 h-3 ml-1" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 text-center text-[#334155] text-xs bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl">
            No research sessions yet. Enter your question above to begin.
          </div>
        )}
      </div>
    </div>
  );
};
