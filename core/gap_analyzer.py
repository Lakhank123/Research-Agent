import re
from typing import Optional
from core.schemas import ResearchCoverageMatrix, ResearchGapItem, ResearchContract, Finding, SourceRecord

def analyze_research_gaps(
    question: str,
    contract: ResearchContract,
    subtasks: list[str],
    findings: list[Finding],
    sources: list[SourceRecord],
    category: str = "general"
) -> ResearchCoverageMatrix:
    """
    Audits the current evidence base against all required attributes and subtasks,
    identifying critical gaps, single-source dependencies, and missing metrics.
    """
    gap_items: list[ResearchGapItem] = []

    # 1. Audit Subtask Coverage
    all_finding_text = " ".join([f"{f.finding} {f.explanation}" for f in findings]).lower()
    
    for st in subtasks:
        st_words = [w for w in re.findall(r"\b[a-z0-9]{3,}\b", st.lower()) if w not in ("find", "extract", "synthesize", "analyze", "identify")]
        matched_words = sum(1 for w in st_words if w in all_finding_text)
        
        ratio = (matched_words / max(1, len(st_words))) if st_words else 1.0
        
        if ratio >= 0.60:
            status = "complete"
            missing = ""
            rec_q = ""
        elif ratio >= 0.25:
            status = "partial"
            missing = "Partial coverage; specific metrics or deep operational details missing."
            rec_q = f"{st} detailed breakdown case study data"
        else:
            status = "missing"
            missing = "No verified evidence chunk directly addresses this planned subtask."
            rec_q = f"{st} authoritative analysis official report"

        # Find supporting sources for this subtask
        matching_sids = set()
        for f in findings:
            if any(w in f.finding.lower() for w in st_words[:3]):
                matching_sids.update(f.citations)

        gap_items.append(ResearchGapItem(
            requirement=st,
            evidence_status=status,
            supporting_sources=sorted(list(matching_sids)),
            missing_information=missing,
            recommended_next_query=rec_q,
            impact_level="high" if status == "missing" else ("medium" if status == "partial" else "low")
        ))

    # 2. Check for Financial Metric Depth (if financial research)
    if "financial_metrics" in contract.required_attributes or any(k in question.lower() for k in ["revenue", "profit", "profitable", "valuation"]):
        has_revenue = bool(re.search(r"\brevenue|turnover|arr|gmv\b", all_finding_text))
        has_profit = bool(re.search(r"\bprofit|ebitda|margin|net income\b", all_finding_text))

        if has_revenue and not has_profit:
            gap_items.append(ResearchGapItem(
                requirement="Financial Performance: Profitability & Margins",
                evidence_status="partial",
                supporting_sources=[],
                missing_information="Topline revenue figures were identified, but bottom-line net profit/EBITDA margins remain undisclosed in verified sources.",
                recommended_next_query=f"{question} net profit EBITDA margins filings",
                impact_level="high"
            ))

    # 3. Check for Single-Source Vulnerability
    single_source_findings = [f for f in findings if len(f.citations) == 1]
    if len(single_source_findings) >= 2:
        gap_items.append(ResearchGapItem(
            requirement="Independent Source Corroboration",
            evidence_status="partial",
            supporting_sources=[c for f in single_source_findings for c in f.citations],
            missing_information=f"{len(single_source_findings)} findings currently rely on only a single publisher; secondary verification recommended.",
            recommended_next_query=f"{question} independent audit analysis review",
            impact_level="medium"
        ))

    # 4. Check for Outdated Sources
    recent_sources = [s for s in sources if s.freshness_score >= 0.75]
    if len(recent_sources) == 0 and len(sources) >= 2:
        gap_items.append(ResearchGapItem(
            requirement="Evidence Recency & Freshness",
            evidence_status="partial",
            supporting_sources=[],
            missing_information="Retrieved sources lack verifiable 2024-2026 timestamps; findings may reflect historical conditions.",
            recommended_next_query=f"{question} 2025 2026 update announcements",
            impact_level="medium"
        ))

    total = len(gap_items)
    met = sum(1 for g in gap_items if g.evidence_status == "complete")
    gaps = total - met
    cov_pct = round((met / max(1, total)) * 100, 1)

    return ResearchCoverageMatrix(
        total_requirements=total,
        met_count=met,
        gap_count=gaps,
        coverage_percentage=cov_pct,
        gap_items=gap_items
    )

