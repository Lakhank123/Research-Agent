import re
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# CONTRACT & INTENT SCHEMAS
# ---------------------------------------------------------------------------

class ResearchContract(BaseModel):
    """Structured contract defining completeness targets extracted from the user query."""
    required_entities_count: Optional[int] = None
    geography: str = "Global"
    industry: str = ""
    timeframe: str = "Current"
    required_attributes: list[str] = Field(default_factory=list)
    comparison_criteria: list[str] = Field(default_factory=list)
    target_output_format: str = "structured_report"

class CompletenessEvaluation(BaseModel):
    """Audit of discovered & verified entities against the ResearchContract."""
    target_count: Optional[int] = None
    verified_count: int = 0
    missing_count: int = 0
    verified_entities: list[str] = Field(default_factory=list)
    missing_entities: list[str] = Field(default_factory=list)
    completion_ratio: float = 1.0
    is_complete: bool = True
    gap_explanation: str = ""
    recommended_remedy: list[str] = Field(default_factory=list)

class SearchQueryPlan(BaseModel):
    query: str
    target_aspect: str = "general_overview"
    priority: int = 1

    @field_validator("query", mode="before")
    @classmethod
    def clean_query_string(cls, v):
        if isinstance(v, str):
            return " ".join(v.split()).strip()
        return str(v)

class ResearchIntent(BaseModel):
    research_objective: str = ""
    research_category: Literal[
        "company",
        "industry",
        "market",
        "competitor",
        "technology_comparison",
        "startup_discovery",
        "trend",
        "product",
        "general"
    ] = "general"
    entities: list[str] = Field(default_factory=list)
    geographic_scope: str = "Global"
    industry_or_domain: str = ""
    timeframe: str = ""
    key_metrics: list[str] = Field(default_factory=list)
    comparison_criteria: list[str] = Field(default_factory=list)
    contract: ResearchContract = Field(default_factory=ResearchContract)
    ambiguity_detected: bool = False
    ambiguity_level: Literal["none", "minor", "significant"] = "none"
    ambiguity_details: str = ""
    clarification_options: list[str] = Field(default_factory=list)
    working_assumptions: list[str] = Field(default_factory=list)

class ResearchPlan(BaseModel):
    research_goal: str
    depth: Literal["quick", "basic", "standard", "moderate", "deep"] = "standard"
    intent: ResearchIntent = Field(default_factory=ResearchIntent)
    subtasks: list[str] = Field(default_factory=list)
    search_queries: list[SearchQueryPlan] = Field(default_factory=list)
    comparison_criteria: list[str] = Field(default_factory=list)

    @property
    def query_strings(self) -> list[str]:
        return [sq.query for sq in self.search_queries]

# ---------------------------------------------------------------------------
# EVIDENCE, SOURCES & CLAIM LEDGER SCHEMAS
# ---------------------------------------------------------------------------

class SourceRecord(BaseModel):
    source_id: str
    title: str = ""
    url: str = ""
    domain: str = ""
    publisher: str = ""
    published_date: str = ""
    retrieved_date: str = ""
    source_type: Literal[
        "official_documentation",
        "regulatory_or_government",
        "academic_or_research",
        "reputable_media",
        "industry_analysis",
        "secondary_media",
        "general_web"
    ] = "general_web"
    is_primary_source: bool = False
    authority_score: float = 0.5
    freshness_score: float = 0.5
    relevance_score: float = 0.0
    composite_score: float = 0.0
    snippet: str = ""
    extracted: bool = False
    extraction_status: Literal[
        "success",
        "partial",
        "snippet_only",
        "failed",
        "blocked_or_invalid_url",
        "not_attempted"
    ] = "not_attempted"
    reason_for_selection: str = ""

class EvidenceChunk(BaseModel):
    chunk_id: str
    source_id: str
    title: str = ""
    url: str = ""
    text: str
    subtask: str = ""
    score: float = 0.0
    source_type: str = "general_web"

class ClaimEvidenceRecord(BaseModel):
    """Granular verification ledger connecting individual claims to audited evidence."""
    claim_id: str
    claim_text: str
    supporting_source_ids: list[str] = Field(default_factory=list)
    supporting_chunk_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    relevant_excerpts: list[str] = Field(default_factory=list)
    evidence_strength: float = 0.7  # 0.0 to 1.0
    verification_status: Literal[
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONFLICTING",
        "UNVERIFIED"
    ] = "SUPPORTED"
    contradictory_evidence: list[str] = Field(default_factory=list)

class Finding(BaseModel):
    finding_id: str = ""
    finding: str
    explanation: str = ""
    metrics_or_figures: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    verification_status: Literal[
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONFLICTING",
        "UNVERIFIED"
    ] = "SUPPORTED"
    evidence_records: list[ClaimEvidenceRecord] = Field(default_factory=list)
    verified_evidence_excerpts: list[dict] = Field(default_factory=list)

    @field_validator("citations", mode="before")
    @classmethod
    def clean_citations(cls, values):
        if values is None:
            return []
        if isinstance(values, str):
            matches = re.findall(r"\bS\d+\b", values)
            return matches if matches else ([values.strip()] if values.strip() else [])
        if isinstance(values, list):
            cleaned = []
            for item in values:
                if isinstance(item, str):
                    matches = re.findall(r"\bS\d+\b", item)
                    if matches:
                        cleaned.extend(matches)
                    elif item.strip():
                        cleaned.append(item.strip())
                elif item:
                    cleaned.append(str(item).strip())
            return list(dict.fromkeys(cleaned))
        return []

# ---------------------------------------------------------------------------
# COUNTER-RESEARCH & CHALLENGE SCHEMAS
# ---------------------------------------------------------------------------

class ChallengeResult(BaseModel):
    """Outcome of an active counter-evidence investigation on a claim."""
    claim_id: str
    original_claim: str
    outcome: Literal[
        "Claim remains supported",
        "Claim needs qualification",
        "Conflicting evidence discovered",
        "Claim is not adequately supported"
    ] = "Claim remains supported"
    supporting_evidence: list[dict] = Field(default_factory=list)
    counter_evidence: list[dict] = Field(default_factory=list)
    source_disagreements: list[str] = Field(default_factory=list)
    updated_verification_status: Literal[
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONFLICTING",
        "UNVERIFIED"
    ] = "SUPPORTED"
    explanation: str = ""
    counter_queries_executed: list[str] = Field(default_factory=list)
    timestamp: str = ""

# ---------------------------------------------------------------------------
# RESEARCH GAPS & DECISION BRIEF SCHEMAS
# ---------------------------------------------------------------------------

class ResearchGapItem(BaseModel):
    requirement: str
    evidence_status: Literal["complete", "partial", "missing"] = "missing"
    supporting_sources: list[str] = Field(default_factory=list)
    missing_information: str = ""
    recommended_next_query: str = ""
    impact_level: Literal["high", "medium", "low"] = "medium"

class ResearchCoverageMatrix(BaseModel):
    total_requirements: int = 0
    met_count: int = 0
    gap_count: int = 0
    coverage_percentage: float = 100.0
    gap_items: list[ResearchGapItem] = Field(default_factory=list)

class DecisionBrief(BaseModel):
    """Executive decision-support summary translating evidence into actions."""
    main_conclusion: str = ""
    key_evidence: list[str] = Field(default_factory=list)
    available_options: list[dict[str, Any]] = Field(default_factory=list)
    comparative_advantages: list[str] = Field(default_factory=list)
    disadvantages_and_tradeoffs: list[str] = Field(default_factory=list)
    strategic_risks: list[str] = Field(default_factory=list)
    important_uncertainties: list[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    next_practical_action: str = ""

class ConfidenceBreakdown(BaseModel):
    overall_score: float = 0.5
    overall_label: Literal["high", "medium", "low"] = "medium"
    evidence_coverage_score: float = 0.5
    source_quality_score: float = 0.5
    source_diversity_score: float = 0.5
    freshness_score: float = 0.5
    claim_verification_rate: float = 1.0
    contradiction_status: str = "None detected"
    heuristic_formula_doc: str = ""

# ---------------------------------------------------------------------------
# MAIN REPORT SCHEMA
# ---------------------------------------------------------------------------

class ComparisonTable(BaseModel):
    headers: list[str] = Field(default_factory=list)
    rows: list[dict[str, str]] = Field(default_factory=list)

class ResearchReport(BaseModel):
    user_question: str
    status: Literal["COMPLETED", "PARTIALLY_COMPLETED", "FAILED"] = "COMPLETED"
    research_overview: dict[str, Any] = Field(default_factory=dict)
    contract: ResearchContract = Field(default_factory=ResearchContract)
    completeness: CompletenessEvaluation = Field(default_factory=CompletenessEvaluation)
    executive_summary: str = ""
    short_answer: str = ""
    key_findings: list[Finding] = Field(default_factory=list)
    detailed_analysis: dict[str, Any] = Field(default_factory=dict)
    comparison_table: Optional[ComparisonTable] = None
    coverage_matrix: ResearchCoverageMatrix = Field(default_factory=ResearchCoverageMatrix)
    decision_brief: DecisionBrief = Field(default_factory=DecisionBrief)
    sources_used: list[SourceRecord] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    confidence_breakdown: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)
    confidence_score: float = 0.5
    confidence_reason: str = ""
    uncertainties: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
