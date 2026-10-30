export type VerificationStatus = 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'CONFLICTING' | 'UNVERIFIED';

export type ChallengeOutcome =
  | 'Claim remains supported'
  | 'Claim needs qualification'
  | 'Conflicting evidence discovered'
  | 'Claim is not adequately supported';

export interface SourceRecord {
  source_id: string;
  title: string;
  url: string;
  domain: string;
  publisher?: string;
  published_date?: string;
  source_type: string;
  is_primary_source: boolean;
  authority_score: number;
  freshness_score: number;
  relevance_score: number;
  composite_score: number;
  snippet?: string;
  extracted: boolean;
  extraction_status: string;
  reason_for_selection?: string;
}

export interface ClaimEvidenceRecord {
  claim_id: string;
  claim_text: string;
  supporting_source_ids: string[];
  supporting_chunk_ids: string[];
  source_urls: string[];
  relevant_excerpts: string[];
  evidence_strength: number;
  verification_status: VerificationStatus;
  contradictory_evidence: string[];
}

export interface Finding {
  finding_id: string;
  finding: string;
  explanation: string;
  metrics_or_figures: string[];
  citations: string[];
  caveats: string[];
  verification_status: VerificationStatus;
  evidence_records?: ClaimEvidenceRecord[];
  verified_evidence_excerpts?: Array<{
    source_id: string;
    chunk_id: string;
    url: string;
    excerpt: string;
  }>;
}

export interface ChallengeResult {
  claim_id: string;
  original_claim: string;
  outcome: ChallengeOutcome;
  supporting_evidence: Array<{ text: string }>;
  counter_evidence: Array<{
    title?: string;
    url?: string;
    domain?: string;
    snippet?: string;
  }>;
  source_disagreements: string[];
  updated_verification_status: VerificationStatus;
  explanation: string;
  counter_queries_executed: string[];
  timestamp: string;
}

export interface ResearchContract {
  required_entities_count?: number | null;
  geography: string;
  industry: string;
  timeframe: string;
  required_attributes: string[];
  comparison_criteria: string[];
}

export interface CompletenessEvaluation {
  target_count?: number | null;
  verified_count: number;
  missing_count: number;
  verified_entities: string[];
  missing_entities: string[];
  completion_ratio: number;
  is_complete: boolean;
  gap_explanation: string;
  recommended_remedy: string[];
}

export interface ResearchGapItem {
  requirement: string;
  evidence_status: 'complete' | 'partial' | 'missing';
  supporting_sources: string[];
  missing_information: string;
  recommended_next_query: string;
  impact_level: 'high' | 'medium' | 'low';
}

export interface ResearchCoverageMatrix {
  total_requirements: number;
  met_count: number;
  gap_count: number;
  coverage_percentage: number;
  gap_items: ResearchGapItem[];
}

export interface DecisionOption {
  name: string;
  pros: string[];
  cons: string[];
  best_for?: string;
}

export interface DecisionBrief {
  main_conclusion: string;
  key_evidence: string[];
  available_options: DecisionOption[];
  comparative_advantages: string[];
  disadvantages_and_tradeoffs: string[];
  strategic_risks: string[];
  important_uncertainties: string[];
  recommendation?: string | null;
  next_practical_action: string;
}

export interface ConfidenceBreakdown {
  overall_score: number;
  overall_label: 'high' | 'medium' | 'low';
  evidence_coverage_score: number;
  source_quality_score: number;
  source_diversity_score: number;
  freshness_score: number;
  claim_verification_rate: number;
  contradiction_status: string;
  heuristic_formula_doc: string;
}

export interface ComparisonTable {
  headers: string[];
  rows: Array<Record<string, string>>;
}

export interface ResearchReport {
  user_question: string;
  status: 'COMPLETED' | 'PARTIALLY_COMPLETED' | 'FAILED';
  research_overview?: {
    original_question?: string;
    intent_category?: string;
    scope?: string;
    timeframe?: string;
    working_assumptions?: string[];
  };
  contract?: ResearchContract;
  completeness?: CompletenessEvaluation;
  executive_summary: string;
  short_answer?: string;
  key_findings: Finding[];
  detailed_analysis?: {
    section_title?: string;
    subsections?: Array<{
      title: string;
      content?: string;
      bullet_points?: string[];
    }>;
  };
  comparison_table?: ComparisonTable | null;
  coverage_matrix?: ResearchCoverageMatrix;
  decision_brief?: DecisionBrief;
  sources_used: SourceRecord[];
  confidence: 'high' | 'medium' | 'low';
  confidence_score: number;
  confidence_breakdown?: ConfidenceBreakdown;
  confidence_reason: string;
  uncertainties: string[];
  assumptions: string[];
  limitations: string[];
  suggested_next_steps: string[];
}

export interface ResearchPlan {
  research_goal: string;
  depth: 'quick' | 'standard' | 'deep';
  subtasks: string[];
  search_queries: Array<{
    query: string;
    target_aspect: string;
    priority: number;
  }>;
  comparison_criteria: string[];
  intent?: {
    research_category: string;
    geographic_scope: string;
    ambiguity_detected: boolean;
    ambiguity_level: string;
    ambiguity_details?: string;
    clarification_options?: string[];
    working_assumptions?: string[];
  };
}

export interface ResearchResult {
  run_id?: string;
  plan: ResearchPlan;
  report: ResearchReport;
  metrics: {
    total_duration_seconds: number;
    queries_planned: number;
    queries_executed: number;
    candidates_discovered: number;
    sources_found: number;
    sources_extracted: number;
    chunks_considered: number;
    chunks_selected: number;
    confidence_score: number;
    execution_status: string;
    completeness_verified?: number;
    completeness_target?: number | null;
  };
  trace?: Array<{
    stage: string;
    status: string;
    detail: string;
    duration_seconds?: number;
  }>;
  challenges?: ChallengeResult[];
}
