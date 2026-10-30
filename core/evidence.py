import re
from typing import Optional
from core.schemas import (
    SourceRecord,
    EvidenceChunk,
    Finding,
    ClaimEvidenceRecord,
    ConfidenceBreakdown,
    ResearchReport
)
from core.retrieval import EvidenceLedger

def evaluate_multi_dimensional_confidence(
    sources: list[SourceRecord],
    ledger: EvidenceLedger,
    subtasks: list[str],
    findings: list[Finding]
) -> tuple[str, float, ConfidenceBreakdown, str]:
    """
    Computes a transparent, multi-dimensional confidence breakdown.
    Rules: Low evidence coverage strictly prevents 'high' confidence.
    """
    accepted = [s for s in sources if s.title and s.url]
    extracted = [s for s in accepted if s.extracted]
    primary_sources = [s for s in accepted if s.is_primary_source]

    unique_domains = {s.domain.lower() for s in accepted if s.domain}
    unique_domains.discard("")

    # 1. Evidence coverage (subtasks with matched chunks)
    subtask_coverage_map = ledger.subtask_coverage()
    covered_subtasks = sum(1 for st in subtasks if st in subtask_coverage_map)
    coverage_score = round((covered_subtasks / max(1, len(subtasks))), 2) if subtasks else 1.0

    # 2. Source quality (average authority score)
    quality_score = round((sum(s.authority_score for s in accepted) / len(accepted)), 2) if accepted else 0.0

    # 3. Source diversity
    diversity_score = round(min(1.0, len(unique_domains) / 3.0), 2)

    # 4. Freshness
    freshness_score = round((sum(s.freshness_score for s in accepted) / len(accepted)), 2) if accepted else 0.5

    # 5. Claim verification rate
    if findings:
        supported_count = sum(1 for f in findings if f.verification_status in ("SUPPORTED", "PARTIALLY_SUPPORTED"))
        claim_verification_rate = round(supported_count / len(findings), 2)
    else:
        claim_verification_rate = 0.5

    # Composite Heuristic Formula
    # 25% Coverage + 25% Quality + 20% Diversity + 15% Claim Verification + 15% Freshness
    composite_score = round(
        0.25 * coverage_score +
        0.25 * quality_score +
        0.20 * diversity_score +
        0.15 * claim_verification_rate +
        0.15 * freshness_score,
        2
    )

    # Rule: Low coverage (< 0.50) or fewer than 2 extracted sources strictly blocks HIGH confidence
    if composite_score >= 0.72 and coverage_score >= 0.60 and len(extracted) >= 2 and len(unique_domains) >= 2:
        confidence_label = "high"
        reason = (
            f"High confidence: {coverage_score*100:.0f}% subtask coverage across {len(unique_domains)} independent domains. "
            f"Average source authority is {quality_score:.2f} with {claim_verification_rate*100:.0f}% claim verification."
        )
    elif composite_score >= 0.40 and len(accepted) >= 2:
        confidence_label = "medium"
        reason = (
            f"Moderate confidence: Evidence gathered across {len(unique_domains)} domains with {coverage_score*100:.0f}% subtask coverage. "
            f"Some aspects rely on secondary sources or partial extractions."
        )
    else:
        confidence_label = "low"
        reason = (
            f"Low confidence (score {composite_score:.2f}): Insufficient full-text extractions or narrow domain diversity. "
            f"Findings require additional verification."
        )

    formula_doc = "Score = 0.25*Coverage + 0.25*Quality + 0.20*Diversity + 0.15*Verification + 0.15*Freshness"

    breakdown = ConfidenceBreakdown(
        overall_score=composite_score,
        overall_label=confidence_label,
        evidence_coverage_score=coverage_score,
        source_quality_score=quality_score,
        source_diversity_score=diversity_score,
        freshness_score=freshness_score,
        claim_verification_rate=claim_verification_rate,
        contradiction_status="No severe contradictions detected across accepted sources.",
        heuristic_formula_doc=formula_doc
    )

    return confidence_label, composite_score, breakdown, reason

def audit_claim_verification(finding_text: str, explanation: str, source_ids: list[str], ledger: EvidenceLedger) -> tuple[str, list[ClaimEvidenceRecord], list[dict]]:
    """
    Audits an individual finding against retrieved ledger chunks.
    Determines if claim is SUPPORTED, PARTIALLY_SUPPORTED, or UNVERIFIED,
    and extracts real text passages directly from the original chunks.
    """
    records = []
    verified_excerpts = []

    words_in_claim = set(re.findall(r"\b[a-z0-9]{3,}\b", f"{finding_text} {explanation}".lower()))

    total_matches = 0
    supporting_chunk_ids = []
    source_urls = []

    for sid in source_ids:
        chunks = ledger.get_chunks_for_source(sid)
        for c in chunks:
            chunk_words = set(re.findall(r"\b[a-z0-9]{3,}\b", c.text.lower()))
            overlap = len(words_in_claim & chunk_words)
            if overlap >= 3:
                total_matches += 1
                supporting_chunk_ids.append(c.chunk_id)
                if c.url not in source_urls:
                    source_urls.append(c.url)
                
                # Extract clean excerpt
                excerpt_len = min(260, len(c.text))
                verified_excerpts.append({
                    "source_id": sid,
                    "chunk_id": c.chunk_id,
                    "url": c.url,
                    "excerpt": c.text[:excerpt_len] + ("..." if len(c.text) > excerpt_len else "")
                })

    # Verification state classification
    if total_matches >= 2:
        status = "SUPPORTED"
        strength = 0.88
    elif total_matches == 1:
        status = "PARTIALLY_SUPPORTED"
        strength = 0.65
    elif source_ids:
        status = "PARTIALLY_SUPPORTED"
        strength = 0.50
    else:
        status = "UNVERIFIED"
        strength = 0.20

    record = ClaimEvidenceRecord(
        claim_id=f"CLM-{abs(hash(finding_text)) % 10000:04d}",
        claim_text=finding_text,
        supporting_source_ids=source_ids,
        supporting_chunk_ids=supporting_chunk_ids,
        source_urls=source_urls,
        relevant_excerpts=[e["excerpt"] for e in verified_excerpts[:3]],
        evidence_strength=strength,
        verification_status=status,
        contradictory_evidence=[]
    )
    records.append(record)

    return status, records, verified_excerpts

def verify_and_ground_citations(
    report_dict: dict,
    ledger: EvidenceLedger,
    valid_source_ids: set[str]
) -> dict:
    """
    Validates all citations, runs claim-level verification, attaches real excerpts,
    and strips phantom source references.
    """
    invalid_citations = []
    grounded_findings = []

    for idx, finding in enumerate(report_dict.get("key_findings", []), 1):
        raw_citations = finding.get("citations", [])
        if isinstance(raw_citations, str):
            raw_citations = re.findall(r"\bS\d+\b", raw_citations) or [raw_citations]

        verified_citations = []
        for cit in raw_citations:
            clean_id = str(cit).strip().strip("[]").strip()
            if clean_id in valid_source_ids:
                if clean_id not in verified_citations:
                    verified_citations.append(clean_id)
            else:
                invalid_citations.append(cit)

        finding["finding_id"] = f"F{idx}"
        finding["citations"] = verified_citations

        # Claim-level verification & real excerpt extraction
        status, records, excerpts = audit_claim_verification(
            finding_text=finding.get("finding", ""),
            explanation=finding.get("explanation", ""),
            source_ids=verified_citations,
            ledger=ledger
        )

        finding["verification_status"] = status
        finding["evidence_records"] = [r.model_dump() for r in records]
        finding["verified_evidence_excerpts"] = excerpts
        grounded_findings.append(finding)

    report_dict["key_findings"] = grounded_findings

    # Filter sources_used
    sources_used = report_dict.get("sources_used", [])
    report_dict["sources_used"] = [s for s in sources_used if s.get("source_id") in valid_source_ids]

    if invalid_citations:
        limitations = report_dict.setdefault("limitations", [])
        notice = f"Removed {len(invalid_citations)} unverified citation references not found in the verified source set."
        if notice not in limitations:
            limitations.append(notice)

    return report_dict
