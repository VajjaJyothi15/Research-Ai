import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  FileText,
  Sparkles,
  TrendingUp,
  ShieldAlert,
  GitCompare,
  Layers,
  Award,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  ListChecks,
  HelpCircle,
} from 'lucide-react';
import { Source } from '../../types';

interface ReportRendererProps {
  markdown: string;
  sources?: Source[];
  onCitationClick?: (citationNum: number) => void;
}

interface ParsedSection {
  id: string;
  title: string;
  type: 'overview' | 'objectives' | 'methodology' | 'background' | 'findings' | 'metrics' | 'security' | 'comparison' | 'gaps' | 'implications' | 'conclusion' | 'sources' | 'general';
  content: string;
}

function getSectionType(title: string): ParsedSection['type'] {
  const lower = title.toLowerCase();
  if (lower.includes('overview') || lower.includes('introduction') || lower.includes('executive summary')) {
    return 'overview';
  }
  if (lower.includes('objective') || lower.includes('scope')) {
    return 'objectives';
  }
  if (lower.includes('methodology') || lower.includes('search approach')) {
    return 'methodology';
  }
  if (lower.includes('background') || lower.includes('concept') || lower.includes('foundation')) {
    return 'background';
  }
  if (lower.includes('finding') || lower.includes('key insight') || lower.includes('discovery')) {
    return 'findings';
  }
  if (lower.includes('metric') || lower.includes('benchmark') || lower.includes('performance') || lower.includes('evaluation')) {
    return 'metrics';
  }
  if (lower.includes('security') || lower.includes('risk') || lower.includes('trade-off') || lower.includes('challenge')) {
    return 'security';
  }
  if (lower.includes('compare') || lower.includes('comparison') || lower.includes('versus') || lower.includes('alternative') || lower.includes('table')) {
    return 'comparison';
  }
  if (lower.includes('gap') || lower.includes('limitation') || lower.includes('future work') || lower.includes('critical analysis')) {
    return 'gaps';
  }
  if (lower.includes('practical') || lower.includes('implication') || lower.includes('recommendation') || lower.includes('implementation')) {
    return 'implications';
  }
  if (lower.includes('conclusion') || lower.includes('summary') || lower.includes('takeaway')) {
    return 'conclusion';
  }
  if (lower.includes('source') || lower.includes('reference') || lower.includes('resource') || lower.includes('bibliography')) {
    return 'sources';
  }
  return 'general';
}

function getSectionIcon(type: ParsedSection['type']) {
  switch (type) {
    case 'overview':
      return <BookOpen className="w-4 h-4 text-[#635BFF]" />;
    case 'objectives':
      return <ListChecks className="w-4 h-4 text-[#635BFF]" />;
    case 'methodology':
      return <Layers className="w-4 h-4 text-[#0F9D91]" />;
    case 'background':
      return <BookOpen className="w-4 h-4 text-[#312E81]" />;
    case 'findings':
      return <Sparkles className="w-4 h-4 text-[#635BFF]" />;
    case 'metrics':
      return <TrendingUp className="w-4 h-4 text-[#0F9D91]" />;
    case 'security':
      return <ShieldAlert className="w-4 h-4 text-[#D97706]" />;
    case 'comparison':
      return <GitCompare className="w-4 h-4 text-[#635BFF]" />;
    case 'gaps':
      return <HelpCircle className="w-4 h-4 text-[#D97706]" />;
    case 'implications':
      return <Layers className="w-4 h-4 text-[#0F9D91]" />;
    case 'conclusion':
      return <Award className="w-4 h-4 text-[#0F9D91]" />;
    case 'sources':
      return <FileText className="w-4 h-4 text-[#312E81]" />;
    default:
      return <CheckCircle2 className="w-4 h-4 text-[#635BFF]" />;
  }
}

export const ReportRenderer: React.FC<ReportRendererProps> = ({
  markdown,
  sources = [],
  onCitationClick,
}) => {
  const { title, sections } = useMemo(() => {
    if (!markdown) return { title: '', sections: [] };

    const lines = markdown.split('\n');
    let reportTitle = '';
    const sectionList: ParsedSection[] = [];
    let currentSection: ParsedSection | null = null;
    let currentBuffer: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.startsWith('# ') && !reportTitle) {
        reportTitle = line.replace(/^#\s+/, '').trim();
        continue;
      }

      if (line.startsWith('## ')) {
        if (currentSection) {
          currentSection.content = currentBuffer.join('\n').trim();
          sectionList.push(currentSection);
          currentBuffer = [];
        }

        const secTitle = line.replace(/^##\s+/, '').trim();
        const type = getSectionType(secTitle);
        currentSection = {
          id: `sec-${secTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
          title: secTitle,
          type,
          content: '',
        };
        continue;
      }

      currentBuffer.push(line);
    }

    if (currentSection) {
      currentSection.content = currentBuffer.join('\n').trim();
      sectionList.push(currentSection);
    } else if (currentBuffer.length > 0 && !sectionList.length) {
      sectionList.push({
        id: 'sec-content',
        title: 'Report Content',
        type: 'general',
        content: currentBuffer.join('\n').trim(),
      });
    }

    return { title: reportTitle, sections: sectionList };
  }, [markdown]);

  const markdownComponents = {
    h3: ({ children }: any) => (
      <h3 className="text-sm font-bold text-[#312E81] mt-4 mb-2 flex items-center space-x-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[#635BFF]" />
        <span>{children}</span>
      </h3>
    ),
    h4: ({ children }: any) => (
      <h4 className="text-xs font-semibold text-[#312E81] mt-3 mb-1.5">{children}</h4>
    ),
    p: ({ children }: any) => {
      return (
        <p className="text-xs sm:text-sm text-[#334155] leading-relaxed mb-3.5 font-normal">
          {children}
        </p>
      );
    },
    strong: ({ children }: any) => (
      <strong className="font-semibold text-[#312E81] bg-[#DCEBFF] px-1 py-0.5 rounded border border-[#BFDBFE]">
        {children}
      </strong>
    ),
    ul: ({ children }: any) => (
      <ul className="space-y-2 my-3 list-none pl-1">{children}</ul>
    ),
    ol: ({ children }: any) => (
      <ol className="space-y-2 my-3 list-decimal pl-5 text-[#334155] text-xs sm:text-sm">{children}</ol>
    ),
    li: ({ children }: any) => (
      <li className="text-xs sm:text-sm text-[#334155] leading-relaxed flex items-start space-x-2.5">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#635BFF] mt-1.5 shrink-0" />
        <span className="flex-1">{children}</span>
      </li>
    ),
    blockquote: ({ children }: any) => (
      <div className="p-3.5 my-3 rounded-lg bg-[#E5E7F9] border-l-4 border-[#635BFF] text-[#334155] text-xs italic">
        {children}
      </div>
    ),
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-4 rounded-lg border border-[#C4B5FD] bg-[#E9E4FF]">
        <table className="w-full text-left text-xs border-collapse">{children}</table>
      </div>
    ),
    thead: ({ children }: any) => (
      <thead className="bg-[#DCD6FA] border-b border-[#C4B5FD] text-[#312E81] font-bold uppercase tracking-wider text-[11px]">
        {children}
      </thead>
    ),
    tbody: ({ children }: any) => (
      <tbody className="divide-y divide-[#C4B5FD]/40 text-[#334155]">{children}</tbody>
    ),
    tr: ({ children }: any) => (
      <tr className="hover:bg-[#E5E7F9]/70 transition-colors">{children}</tr>
    ),
    th: ({ children }: any) => <th className="py-2.5 px-3.5 font-semibold text-[#312E81]">{children}</th>,
    td: ({ children }: any) => <td className="py-2.5 px-3.5">{children}</td>,
    a: ({ href, children }: any) => {
      const text = String(children);
      const isCitation = /^\[?\d+\]?$/.test(text.trim());

      if (isCitation) {
        const num = parseInt(text.replace(/\D/g, ''), 10);
        return (
          <button
            type="button"
            onClick={() => onCitationClick?.(num)}
            className="inline-flex items-center justify-center px-1.5 py-0.2 mx-0.5 rounded bg-[#DCEBFF] text-[#312E81] hover:bg-[#635BFF] hover:text-white border border-[#BFDBFE] text-[11px] font-mono font-bold transition-colors cursor-pointer shadow-xs"
            title={`View source [${num}]`}
          >
            [{num}]
          </button>
        );
      }

      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#635BFF] hover:underline inline-flex items-center space-x-0.5"
        >
          <span>{children}</span>
          <ExternalLink className="w-3 h-3 inline ml-0.5 opacity-70" />
        </a>
      );
    },
    code: ({ children }: any) => (
      <code className="px-1 py-0.5 rounded bg-[#E5E7F9] border border-[#C4B5FD] text-[#312E81] text-xs font-mono">
        {children}
      </code>
    ),
  };

  return (
    <div className="space-y-6 max-w-none">
      {sections.map((sec, idx) => {
        const isFindings = sec.type === 'findings';
        const isMetrics = sec.type === 'metrics';
        const isSecurity = sec.type === 'security';
        const isConclusion = sec.type === 'conclusion';
        const isSources = sec.type === 'sources';

        return (
          <section
            key={sec.id || idx}
            id={sec.id}
            className={`transition-colors rounded-xl p-6 ${
              isFindings
                ? 'bg-[#E9E4FF] border border-[#C4B5FD] shadow-xs'
                : isMetrics
                ? 'bg-[#DDF7F0] border border-[#A7F3D0] shadow-xs'
                : isSecurity
                ? 'bg-[#DCEBFF] border border-[#C4B5FD] shadow-xs'
                : isConclusion
                ? 'bg-[#E5E7F9] border border-[#C4B5FD] shadow-xs'
                : isSources
                ? 'bg-[#E9E4FF] border border-[#C4B5FD] mt-8 shadow-xs'
                : 'bg-[#E9E4FF] border border-[#C4B5FD] shadow-xs'
            }`}
          >
            {/* Section Header */}
            <div className="flex items-center space-x-2.5 pb-3 mb-3.5 border-b border-[#C4B5FD]">
              <div
                className={`p-1.5 rounded-lg shrink-0 ${
                  isFindings
                    ? 'bg-[#DCEBFF] text-[#635BFF]'
                    : isMetrics
                    ? 'bg-[#DDF7F0] text-[#0F9D91]'
                    : isSecurity
                    ? 'bg-[#FEF3C7] text-[#D97706]'
                    : isConclusion
                    ? 'bg-[#DDF7F0] text-[#0F9D91]'
                    : isSources
                    ? 'bg-[#DCD6FA] text-[#312E81]'
                    : 'bg-[#DCEBFF] text-[#635BFF]'
                }`}
              >
                {getSectionIcon(sec.type)}
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#312E81]/60 font-mono">
                  Section 0{idx + 1}
                </span>
                <h2 className="text-base font-bold text-[#312E81] leading-tight">
                  {sec.title}
                </h2>
              </div>
            </div>

            {/* Section Content */}
            {isSources && sources.length > 0 ? (
              <div className="space-y-2.5 pt-1">
                {sources.map((src, sIdx) => (
                  <div
                    key={src.id || sIdx}
                    id={`source-card-${sIdx + 1}`}
                    className="p-3.5 rounded-lg bg-[#E5E7F9] border border-[#C4B5FD] hover:border-[#635BFF] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold px-1.5 py-0.2 rounded bg-[#DCEBFF] text-[#312E81] border border-[#BFDBFE]">
                          [{sIdx + 1}]
                        </span>
                        <span className="text-[11px] font-mono text-[#334155]/70">
                          {src.domain || 'web'} • {src.publication_date || '2026'}
                        </span>
                        <span className="text-[10px] uppercase font-bold text-[#0F9D91] px-1.5 py-0.2 rounded bg-[#DDF7F0] border border-[#A7F3D0]">
                          Verified Source
                        </span>
                      </div>
                      <h4 className="text-xs sm:text-sm font-bold text-[#312E81]">{src.title}</h4>
                      {src.content_text && (
                        <p className="text-xs text-[#334155] line-clamp-2">{src.content_text}</p>
                      )}
                    </div>

                    {src.url && (
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-[#E9E4FF] hover:bg-[#DCD6FA] text-[#635BFF] border border-[#C4B5FD] text-xs font-medium flex items-center space-x-1 shrink-0 self-start sm:self-auto transition-colors shadow-xs"
                      >
                        <span>Open source</span>
                        <ExternalLink className="w-3.5 h-3.5 ml-0.5" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="prose max-w-none text-[#334155]">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {sec.content}
                </ReactMarkdown>
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
};
