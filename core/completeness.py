import re
from typing import Optional
from core.schemas import ResearchContract, CompletenessEvaluation, Finding, SourceRecord

def extract_research_contract(question: str, intent_contract: Optional[ResearchContract] = None) -> ResearchContract:
    """
    Translates user question into an auditable research contract.
    Detects target count, geographic scope, industry, and required attributes.
    """
    contract = intent_contract or ResearchContract()
    q_lower = (question or "").lower()

    # Detect entity count (e.g., "find 10 startups", "top 3 databases", "compare 5 companies")
    count_match = re.search(r"\b(?:top|find|list|identify|analyze|compare)\s+(\d{1,2})\b", q_lower)
    if not count_match:
        count_match = re.search(r"\b(\d{1,2})\s+(?:startups|companies|tools|databases|competitors|businesses|products|vendors)\b", q_lower)
    
    if count_match:
        contract.required_entities_count = int(count_match.group(1))

    # Detect geography
    if any(k in q_lower for k in ["india", "indian", "bengaluru", "mumbai", "delhi"]):
        contract.geography = "India"
    elif any(k in q_lower for k in ["us", "usa", "united states", "american", "silicon valley"]):
        contract.geography = "United States"
    elif any(k in q_lower for k in ["europe", "european", "uk", "germany", "france"]):
        contract.geography = "Europe"

    # Detect required attributes
    attrs = []
    if any(k in q_lower for k in ["business model", "monetization", "how they make money"]):
        attrs.append("business_model")
    if any(k in q_lower for k in ["funding", "valuation", "investors", "raised"]):
        attrs.append("funding_valuation")
    if any(k in q_lower for k in ["revenue", "profit", "ebitda", "turnover", "financial"]):
        attrs.append("financial_metrics")
    if any(k in q_lower for k in ["competitor", "rival", "positioning", "vs"]):
        attrs.append("competitors_and_positioning")
    if any(k in q_lower for k in ["architecture", "benchmark", "latency", "scalability"]):
        attrs.append("technical_benchmarks")

    contract.required_attributes = list(dict.fromkeys(contract.required_attributes + attrs))
    return contract

def evaluate_completeness_gate(
    contract: ResearchContract,
    findings: list[Finding],
    sources: list[SourceRecord],
    category: str = "general"
) -> CompletenessEvaluation:
    """
    Audits actual verified findings against the contract.
    If 10 entities were requested and only 7 are verified, explicitly flags missing items.
    """
    target = contract.required_entities_count
    
    # Extract distinct verified entities from findings and sources
    discovered_entities = []
    seen = set()

    for f in findings:
        # Check if finding headline mentions specific entities or companies
        text = f.finding
        # Look for leading names e.g. "Darwinbox: ...", "Qdrant: ..."
        prefix_match = re.match(r"^([A-Z][a-zA-Z0-9\.\s\-]{2,25})[:\—\–\-]", text)
        if prefix_match:
            entity_name = prefix_match.group(1).strip()
            if entity_name.lower() not in seen and len(entity_name) > 2:
                discovered_entities.append(entity_name)
                seen.add(entity_name.lower())

    # Fallback to source publisher/entities if findings didn't use prefix syntax
    if not discovered_entities:
        for s in sources:
            pub = s.publisher or s.domain.split(".")[0].capitalize()
            if pub and pub.lower() not in seen and pub.lower() not in ("github", "reuters", "bloomberg", "medium", "techcrunch", "docs"):
                discovered_entities.append(pub)
                seen.add(pub.lower())

    verified_count = len(discovered_entities)
    
    # If no specific number was requested, base completeness on evidence depth
    if target is None or target <= 0:
        is_complete = len(findings) >= 2 and len(sources) >= 3
        return CompletenessEvaluation(
            target_count=None,
            verified_count=verified_count,
            missing_count=0,
            verified_entities=discovered_entities,
            missing_entities=[],
            completion_ratio=1.0 if is_complete else 0.7,
            is_complete=is_complete,
            gap_explanation="General open-ended inquiry completed with multi-source coverage." if is_complete else "Limited evidence available to fully satisfy all subtasks.",
            recommended_remedy=[]
        )

    # When explicit count was requested:
    missing_count = max(0, target - verified_count)
    completion_ratio = round(verified_count / target, 2)
    is_complete = (missing_count == 0)

    missing_entities = [f"Entity Slot #{i}" for i in range(verified_count + 1, target + 1)] if missing_count > 0 else []
    
    explanation = ""
    remedy = []
    if missing_count > 0:
        explanation = (
            f"User contract requested {target} verified items. "
            f"Only {verified_count} unique entities could be authoritatively verified from retrieved primary/secondary sources. "
            f"{missing_count} requested entities remain unconfirmed without reliable citations."
        )
        remedy = [
            f"Run targeted follow-up query focusing on secondary market directories in {contract.geography}.",
            f"Expand search query budget beyond top {len(sources)} candidate sources."
        ]
    else:
        explanation = f"Successfully identified and verified all {target} requested entities with evidence citations."

    return CompletenessEvaluation(
        target_count=target,
        verified_count=verified_count,
        missing_count=missing_count,
        verified_entities=discovered_entities,
        missing_entities=missing_entities,
        completion_ratio=completion_ratio,
        is_complete=is_complete,
        gap_explanation=explanation,
        recommended_remedy=remedy
    )

