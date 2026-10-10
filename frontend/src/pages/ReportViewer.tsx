import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Download,
  ShieldCheck,
  Sparkles,
  ExternalLink,
  RotateCcw,
  Database,
  X,
  Copy,
  Check,
  Clock,
  Layers,
  FileDown,
  Loader2,
} from 'lucide-react';
import { api } from '../services/api';
import { ReportRenderer } from '../components/reports/ReportRenderer';

export const ReportViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [summaryType, setSummaryType] = useState('executive');
  const [summaryResult, setSummaryResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => api.getReport(id!),
    enabled: !!id,
  });

  const { data: sources } = useQuery({
    queryKey: ['sources', id],
    queryFn: () => api.getSources(id!),
    enabled: !!id,
  });

  const { data: citationAudit } = useQuery({
    queryKey: ['citationAudit', report?.id],
    queryFn: () => api.validateCitations(report!.id),
    enabled: !!report?.id,
  });

  const summarizeMutation = useMutation({
    mutationFn: () => api.summarizeReport(report!.id, summaryType),
    onSuccess: (data) => {
      setSummaryResult(data.summary_text);
    },
  });

  const rerunMutation = useMutation({
    mutationFn: () => api.rerunResearch(id!),
    onSuccess: (newRun) => {
      navigate(`/workspace/${newRun.id}`);
    },
  });

  const handleCopyReport = async () => {
    if (!report?.full_markdown) return;
    try {
      await navigator.clipboard.writeText(report.full_markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (e) {
      console.error('Failed to copy report:', e);
    }
  };

  const handleExport = (format: string) => {
    if (!report?.id) return;
    window.open(`/api/v1/reports/${report.id}/export?format=${format}`, '_blank');
  };

  const handleCitationClick = (citationNum: number) => {
    const el = document.getElementById(`source-card-${citationNum}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('ring-2', 'ring-[#635BFF]');
      setTimeout(() => {
        el.classList.remove('ring-2', 'ring-[#635BFF]');
      }, 2000);
    } else {
      const sourcesSec = document.getElementById('sec-sources') || document.getElementById('sources-panel');
      sourcesSec?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const readingTimeMinutes = Math.max(
    1,
    Math.ceil((report?.full_markdown?.split(/\s+/).length || 200) / 200)
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Report Header Card */}
      <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 sm:p-8 space-y-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#DDF7F0] text-[#0F9D91] border border-[#A7F3D0] text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verified Evidence Report</span>
            </span>

            {citationAudit && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#DCEBFF] text-[#312E81] border border-[#BFDBFE] font-mono font-medium">
                Citations: {citationAudit.resolved_citations}/{citationAudit.total_citations} Verified
              </span>
            )}

            <span className="text-xs px-2 py-0.5 rounded-full bg-[#E5E7F9] text-[#334155] border border-[#C4B5FD] flex items-center space-x-1 font-mono">
              <Clock className="w-3 h-3 text-[#635BFF]" />
              <span>{readingTimeMinutes} min read</span>
            </span>
          </div>

          <p className="text-xs text-[#334155]/70 font-mono">
            {report?.created_at ? new Date(report.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : ''}
          </p>
        </div>

        <h1 className="text-xl sm:text-2xl font-bold text-[#312E81] tracking-tight leading-snug">
          {report?.title || (reportLoading ? 'Loading Report...' : 'Research Report')}
        </h1>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-[#C4B5FD]">
          <button
            onClick={handleCopyReport}
            className="px-3 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1.5 transition-colors shadow-xs"
            title="Copy full markdown report"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-[#0F9D91]" />
                <span className="text-[#0F9D91] font-semibold">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-[#334155]" />
                <span>Copy markdown</span>
              </>
            )}
          </button>

          <button
            onClick={() => setSummaryModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-[#DCEBFF] hover:bg-[#BFDBFE] text-[#312E81] border border-[#BFDBFE] text-xs font-medium flex items-center space-x-1.5 transition-colors shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#635BFF]" />
            <span>Summarize report</span>
          </button>

          <button
            onClick={() => {
              const el = document.getElementById('sec-sources') || document.getElementById('sources-panel');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="px-3 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1.5 transition-colors shadow-xs"
          >
            <Database className="w-3.5 h-3.5 text-[#334155]" />
            <span>Sources ({sources?.length || 0})</span>
          </button>

          <button
            onClick={() => rerunMutation.mutate()}
            disabled={rerunMutation.isPending}
            className="px-3 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1.5 transition-colors disabled:opacity-50 shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#334155]" />
            <span>{rerunMutation.isPending ? 'Re-running...' : 'Research again'}</span>
          </button>

          <div className="flex items-center space-x-1 ml-auto">
            <span className="text-xs text-[#334155]/70 mr-1 hidden md:inline">Download:</span>
            
            <button
              onClick={() => handleExport('pdf')}
              className="px-3 py-1.5 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white text-xs font-semibold shadow-xs transition-colors flex items-center space-x-1"
              title="Download formatted PDF"
            >
              <Download className="w-3.5 h-3.5" />
              <span>PDF</span>
            </button>

            <button
              onClick={() => handleExport('html')}
              className="px-2.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium transition-colors"
              title="Download standalone HTML document"
            >
              HTML
            </button>

            <button
              onClick={() => handleExport('md')}
              className="px-2.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium transition-colors"
              title="Download raw Markdown"
            >
              MD
            </button>

            <button
              onClick={() => handleExport('docx')}
              className="px-2.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] border border-[#C4B5FD] text-xs font-medium transition-colors"
              title="Download Word document"
            >
              DOCX
            </button>
          </div>
        </div>
      </div>

      {/* Main Report Body + Side Navigation/Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          {reportLoading ? (
            <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-12 text-center text-[#334155] text-xs shadow-xs space-y-3">
              <Loader2 className="w-6 h-6 animate-spin mx-auto text-[#635BFF]" />
              <p>Loading research report...</p>
            </div>
          ) : report?.full_markdown ? (
            <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 sm:p-8 shadow-xs">
              <ReportRenderer
                markdown={report.full_markdown}
                sources={sources || []}
                onCitationClick={handleCitationClick}
              />
            </div>
          ) : (
            <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-8 text-center text-[#334155] text-xs shadow-xs">
              No report content found for this research session.
            </div>
          )}
        </div>

        {/* Sidebar Sticky Panel: Sources Overview & Provenance */}
        <div id="sources-panel" className="space-y-5 lg:sticky lg:top-4">
          <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#C4B5FD]">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-[#635BFF]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81]">
                  Primary Sources ({sources?.length || 0})
                </h3>
              </div>
            </div>

            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {sources && sources.length > 0 ? (
                sources.map((s, idx) => (
                  <div
                    key={s.id || idx}
                    id={`source-card-${idx + 1}`}
                    className="p-3 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] space-y-1 transition-all text-xs hover:border-[#635BFF]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-[11px] text-[#635BFF]">
                        [{idx + 1}]
                      </span>
                      <span className="text-[10px] text-[#334155]/70 font-mono">
                        {s.domain || 'web'}
                      </span>
                    </div>
                    <h4 className="font-semibold text-[#312E81] leading-snug line-clamp-2">
                      {s.title}
                    </h4>
                    {s.url && (
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#635BFF] hover:underline text-[11px] inline-flex items-center space-x-1 pt-0.5"
                      >
                        <span>Inspect URL</span>
                        <ExternalLink className="w-3 h-3 ml-0.5" />
                      </a>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-[#334155]/60 italic text-xs">No external sources recorded.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Summarize Modal */}
      {summaryModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#312E81]/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-6 max-w-lg w-full space-y-4 shadow-lg">
            <div className="flex items-center justify-between pb-2 border-b border-[#C4B5FD]">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-[#635BFF]" />
                <h3 className="text-sm font-bold text-[#312E81]">Summarize Research Report</h3>
              </div>
              <button
                onClick={() => {
                  setSummaryModalOpen(false);
                  setSummaryResult(null);
                }}
                className="text-[#334155] hover:text-[#312E81]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-[#312E81]">Summary Format</label>
              <select
                value={summaryType}
                onChange={(e) => setSummaryType(e.target.value)}
                className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg px-3 py-2 text-xs text-[#312E81] focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE]"
              >
                <option value="executive">Executive Summary (2 paragraphs)</option>
                <option value="bullet_points">Key Bullet Points (5 bullets)</option>
                <option value="technical">Technical Takeaways & Trade-offs</option>
              </select>
            </div>

            {summaryResult ? (
              <div className="p-4 bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg text-xs text-[#334155] space-y-2 max-h-60 overflow-y-auto leading-relaxed">
                <div className="font-semibold text-[#312E81]">Generated Summary:</div>
                <p>{summaryResult}</p>
              </div>
            ) : null}

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => {
                  setSummaryModalOpen(false);
                  setSummaryResult(null);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#312E81] text-xs font-medium border border-[#C4B5FD]"
              >
                Close
              </button>
              <button
                onClick={() => summarizeMutation.mutate()}
                disabled={summarizeMutation.isPending}
                className="px-4 py-1.5 rounded-lg bg-[#635BFF] hover:bg-[#4F46E5] text-white text-xs font-semibold shadow-xs flex items-center space-x-1.5 disabled:opacity-50"
              >
                {summarizeMutation.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Generate summary</span>
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
