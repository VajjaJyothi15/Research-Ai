import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Sparkles, Layers, BookOpen, Cpu, BarChart3, Loader2, AlertCircle, Search } from 'lucide-react';
import { api } from '../services/api';

export const NewResearch: React.FC = () => {
  const navigate = useNavigate();

  const [question, setQuestion] = useState('');
  const [objective, setObjective] = useState('');
  const [domain, setDomain] = useState('technology');
  const [mode, setMode] = useState<'quick' | 'standard' | 'indepth'>('standard');
  const [recencyMonths, setRecencyMonths] = useState(24);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
        err?.response?.data?.detail || err?.message || 'Failed to initialize research task.'
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || question.trim().length < 5) {
      setErrorMessage('Please enter a research question with at least 5 characters.');
      return;
    }

    createMutation.mutate({
      question: question.trim(),
      objective: objective.trim() || undefined,
      domain,
      mode,
      recency_months: recencyMonths,
    });
  };

  const researchModes = [
    { id: 'quick', label: 'Quick Research', desc: 'Fast overview with exactly 2 targeted subquestions', icon: Sparkles },
    { id: 'standard', label: 'Standard Research', desc: 'Balanced multi-source web & academic investigation', icon: Layers },
    { id: 'indepth', label: 'In-depth Review', desc: 'Comprehensive literature review, cross-checking & contradictions', icon: BookOpen },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-[#312E81]">Create New Research Task</h1>
        <p className="text-[#334155] text-xs sm:text-sm mt-0.5">
          Specify your research question and objectives. ResAI will formulate a multi-step plan for your approval before executing tool search.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {errorMessage && (
          <div className="p-3.5 bg-[#FEE2E2] border border-[#FECACA] text-[#991B1B] text-xs rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-[#DC2626] shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Main Research Question */}
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 space-y-3 shadow-xs">
          <label className="block text-xs font-bold uppercase tracking-wider text-[#312E81]">
            Research Question <span className="text-[#635BFF]">*</span>
          </label>
          <textarea
            required
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What are the comparative performance metrics and security trade-offs of autonomous agent architectures?"
            className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg p-3.5 text-[#312E81] placeholder-[#334155]/60 focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE] text-xs sm:text-sm leading-relaxed"
          />

          <div className="space-y-1 pt-1">
            <label className="block text-xs font-semibold text-[#312E81]">
              Specific Objectives & Scope <span className="text-[#334155]/60 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="e.g. Focus on citation fidelity, latency overhead, and prompt injection risks."
              className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg px-3.5 py-2 text-xs text-[#312E81] focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE]"
            />
          </div>
        </div>

        {/* Mode Selector */}
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 space-y-3 shadow-xs">
          <label className="block text-xs font-bold uppercase tracking-wider text-[#312E81]">
            Research Mode & Workflow
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {researchModes.map((m) => {
              const Icon = m.icon;
              const isSelected = mode === m.id;
              return (
                <div
                  key={m.id}
                  onClick={() => setMode(m.id as 'quick' | 'standard' | 'indepth')}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-[#DCEBFF] border-[#635BFF] text-[#312E81] shadow-xs'
                      : 'bg-[#E5E7F9] border-[#C4B5FD] text-[#334155] hover:border-[#635BFF]'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 mb-1">
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-[#635BFF]' : 'text-[#334155]'}`} />
                    <span className="text-xs font-bold text-[#312E81]">{m.label}</span>
                  </div>
                  <p className="text-[11px] text-[#334155] leading-snug">{m.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Configuration Parameters */}
        <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 space-y-4 shadow-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81]">
            Domain & Recency Policies
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-[#312E81]">Research Domain</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg px-3 py-2 text-xs text-[#312E81] focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE]"
              >
                <option value="technology">Technology & AI</option>
                <option value="science">Scientific & Biomedical</option>
                <option value="finance">Finance & Economics</option>
                <option value="legal">Legal & Policy</option>
                <option value="general">General Knowledge</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-[#312E81]">
                Source Recency Window: {recencyMonths} months
              </label>
              <input
                type="range"
                min="6"
                max="60"
                step="6"
                value={recencyMonths}
                onChange={(e) => setRecencyMonths(Number(e.target.value))}
                className="w-full h-1.5 bg-[#C4B5FD] rounded-lg appearance-none cursor-pointer accent-[#635BFF]"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={createMutation.isPending || !question.trim()}
            className="px-6 py-2.5 rounded-lg text-xs sm:text-sm font-semibold bg-[#635BFF] hover:bg-[#4F46E5] text-white shadow-xs transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Research Plan...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Formulate Plan & Review</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
