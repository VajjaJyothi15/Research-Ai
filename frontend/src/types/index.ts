export type ResearchStage =
  | 'intake'
  | 'planning'
  | 'searching'
  | 'extracting'
  | 'verifying'
  | 'analyzing'
  | 'quality_gate'
  | 'writing'
  | 'citation_audit'
  | 'completed'
  | 'cancelled'
  | 'failed';

export interface ResearchRun {
  id: string;
  project_id?: string;
  question: string;
  objective?: string;
  domain: string;
  mode: string;
  status: string;
  current_stage: string;
  policy_json?: Record<string, any>;
  budget_json?: Record<string, any>;
  usage_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SubQuestion {
  id: string;
  title?: string;
  question: string;
  search_queries: string[];
  evidence_required: string;
  status: string;
}

export interface ResearchPlan {
  id: string;
  run_id: string;
  version: number;
  status: string; // DRAFT, PENDING_APPROVAL, APPROVED, REJECTED
  main_question: string;
  subquestions_json: SubQuestion[];
  plan_data_json: Record<string, any>;
  user_feedback?: string;
  created_at: string;
}

export interface Source {
  id: string;
  run_id: string;
  url: string;
  canonical_url?: string;
  title: string;
  author?: string;
  publication_date?: string;
  source_type: string;
  domain?: string;
  relevance_score: number;
  content_text?: string;
  created_at: string;
}

export interface EvidenceItem {
  id: string;
  run_id: string;
  source_id: string;
  claim_text: string;
  supporting_text: string;
  publication_date?: string;
  retrieval_timestamp: string;
  evidence_type: string;
  confidence_score: number;
  verification_status: string;
  relationship: string;
  created_at: string;
}

export interface Contradiction {
  id: string;
  run_id: string;
  topic: string;
  claim_a: string;
  claim_b: string;
  source_a_id?: string;
  source_b_id?: string;
  description: string;
  resolution_status: string;
  created_at: string;
}

export interface ToolCallLog {
  id: string;
  run_id: string;
  stage: string;
  tool_name: string;
  arguments_json: Record<string, any>;
  status: string;
  result_summary?: string;
  error_message?: string;
  duration_ms: number;
  retry_count: number;
  created_at: string;
}

export interface Report {
  id: string;
  run_id: string;
  title: string;
  executive_summary: string;
  full_markdown: string;
  methodology?: string;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CoverageItem {
  subquestion_id: string;
  question: string;
  status: 'SUFFICIENT' | 'PARTIAL' | 'CONFLICTING' | 'NO_EVIDENCE';
  evidence_count: number;
  primary_source_count: number;
}

export interface CoverageResponse {
  run_id: string;
  overall_score: number;
  items: CoverageItem[];
}
