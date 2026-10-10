import {
  Contradiction,
  CoverageResponse,
  EvidenceItem,
  Report,
  ResearchPlan,
  ResearchRun,
  Source,
  ToolCallLog,
} from '../types';

const API_BASE = '/api/v1';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData?.error?.message ||
      (typeof errorData?.detail === 'string'
        ? errorData.detail
        : Array.isArray(errorData?.detail)
        ? errorData.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join('; ')
        : errorData?.message) ||
      `API Error (${res.status}): Request failed`;
    throw new Error(message);
  }

  return res.json();
}

export const api = {
  // Research Runs
  createResearch: (data: {
    question: string;
    objective?: string;
    domain?: string;
    mode?: string;
    recency_months?: number;
  }) => fetchJSON<ResearchRun>('/research', { method: 'POST', body: JSON.stringify(data) }),

  listResearchRuns: () => fetchJSON<ResearchRun[]>('/research'),

  getResearchRun: (id: string) => fetchJSON<ResearchRun>(`/research/${id}`),

  clearResearchHistory: () =>
    fetchJSON<{ message: string; deleted_count: number }>('/research', { method: 'DELETE' }),

  deleteResearchRun: (id: string) =>
    fetchJSON<{ message: string; research_id: string }>(`/research/${id}`, { method: 'DELETE' }),

  cancelResearch: (id: string) => fetchJSON<{ message: string }>(`/research/${id}/cancel`, { method: 'POST' }),

  rerunResearch: (id: string) => fetchJSON<ResearchRun>(`/research/${id}/rerun`, { method: 'POST' }),

  // Research Plan
  getPlan: (researchId: string) => fetchJSON<ResearchPlan>(`/research/${researchId}/plan`),

  regeneratePlan: (researchId: string, userFeedback: string) =>
    fetchJSON<ResearchPlan>(`/research/${researchId}/plan/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ user_feedback: userFeedback }),
    }),

  editPlan: (researchId: string, data: { main_question?: string; subquestions?: any[] }) =>
    fetchJSON<ResearchPlan>(`/research/${researchId}/plan`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  approvePlan: (researchId: string) =>
    fetchJSON<ResearchRun>(`/research/${researchId}/plan/approve`, { method: 'POST' }),

  // Evidence & Sources
  getSources: (researchId: string) => fetchJSON<Source[]>(`/research/${researchId}/sources`),

  getEvidence: (researchId: string) => fetchJSON<EvidenceItem[]>(`/research/${researchId}/evidence`),

  getCoverage: (researchId: string) => fetchJSON<CoverageResponse>(`/research/${researchId}/coverage`),

  getContradictions: (researchId: string) => fetchJSON<Contradiction[]>(`/research/${researchId}/contradictions`),

  getToolCalls: (researchId: string) => fetchJSON<ToolCallLog[]>(`/research/${researchId}/tool-calls`),

  // Reports
  getReport: (researchId: string) => fetchJSON<Report>(`/research/${researchId}/report`),

  validateCitations: (reportId: string) =>
    fetchJSON<{ is_valid: boolean; total_citations: number; resolved_citations: number }>(
      `/reports/${reportId}/validate-citations`,
      { method: 'POST' }
    ),

  summarizeReport: (reportId: string, summaryType: string) =>
    fetchJSON<{ summary_type: string; summary_text: string }>(`/reports/${reportId}/summarize`, {
      method: 'POST',
      body: JSON.stringify({ summary_type: summaryType }),
    }),

  // File Upload
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/uploads`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('File upload failed');
    return res.json();
  },
};
