import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, Search, ShieldAlert, CheckCircle2, ExternalLink } from 'lucide-react';
import { api } from '../services/api';

export const EvidenceExplorer: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: runs } = useQuery({
    queryKey: ['researchRuns'],
    queryFn: api.listResearchRuns,
  });

  const latestRunId = runs?.[0]?.id;

  const { data: sources } = useQuery({
    queryKey: ['sources', latestRunId],
    queryFn: () => api.getSources(latestRunId!),
    enabled: !!latestRunId,
  });

  const { data: evidence } = useQuery({
    queryKey: ['evidence', latestRunId],
    queryFn: () => api.getEvidence(latestRunId!),
    enabled: !!latestRunId,
  });

  const filteredSources = sources?.filter((s) => {
    return (
      s.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.domain || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-[#312E81] flex items-center space-x-2.5">
          <Database className="w-6 h-6 text-[#635BFF]" />
          <span>Sources & Evidence Repository</span>
        </h1>
        <p className="text-[#334155] text-xs sm:text-sm mt-0.5">
          Explore verified primary sources, web citations, and extracted claims from your research investigations.
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xs">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 text-[#334155]/60 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search sources by title or domain..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#E5E7F9] border border-[#C4B5FD] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#312E81] placeholder-[#334155]/60 focus:outline-none focus:border-[#635BFF] focus:bg-[#EDE9FE]"
          />
        </div>

        <div className="text-xs text-[#334155]">
          <span>{filteredSources?.length || 0} Sources Retrieved</span>
        </div>
      </div>

      {/* Primary Sources List */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81]">
          Discovered Sources
        </h3>

        {!filteredSources || filteredSources.length === 0 ? (
          <div className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-8 text-center text-[#334155] text-xs shadow-xs">
            No sources found. Submit a research inquiry to discover web and academic sources.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {filteredSources.map((src) => (
              <div
                key={src.id}
                className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-4 sm:p-5 space-y-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs hover:border-[#635BFF] transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#DCEBFF] text-[#312E81] border border-[#BFDBFE]">
                      {src.source_type.toUpperCase()}
                    </span>
                    <span className="text-xs text-[#334155]/80 font-mono">{src.domain}</span>
                    <span className="text-xs text-[#334155]/60">• {src.publication_date || '2026'}</span>
                  </div>
                  <h4 className="text-xs sm:text-sm font-bold text-[#312E81]">{src.title}</h4>
                  {src.content_text && (
                    <p className="text-xs text-[#334155] line-clamp-2 leading-relaxed">
                      {src.content_text}
                    </p>
                  )}
                </div>

                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3.5 py-1.5 rounded-lg bg-[#E5E7F9] hover:bg-[#DCD6FA] text-[#635BFF] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1.5 transition-colors shrink-0 self-start sm:self-auto shadow-xs"
                  >
                    <span>Open URL</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extracted Evidence Claims */}
      {evidence && evidence.length > 0 && (
        <div className="space-y-3 pt-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#312E81]">
            Extracted Factual Claims ({evidence.length})
          </h3>
          <div className="grid grid-cols-1 gap-2.5">
            {evidence.map((ev) => (
              <div
                key={ev.id}
                className="bg-[#E9E4FF] border border-[#C4B5FD] rounded-xl p-4 space-y-1.5 shadow-xs"
              >
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#0F9D91]" />
                  <span className="text-[11px] font-bold text-[#312E81]">
                    Confidence: {Math.round(ev.confidence_score * 100)}%
                  </span>
                  <span className="text-[10px] text-[#334155]/70 uppercase font-mono">
                    {ev.evidence_type}
                  </span>
                </div>
                <p className="text-xs text-[#312E81] font-medium">{ev.claim_text}</p>
                {ev.supporting_text && (
                  <p className="text-xs text-[#334155] italic bg-[#E5E7F9] p-2 rounded border border-[#C4B5FD]/70">
                    "{ev.supporting_text}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
