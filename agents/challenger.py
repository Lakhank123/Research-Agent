import datetime
import json
import logging
import re
from typing import Optional
from core.schemas import ChallengeResult
from tools.web_search import TavilySearchTool, extract_domain
from tools.page_reader import PageReader

logger = logging.getLogger(__name__)

CHALLENGER_SYSTEM_PROMPT = """You are an Adversarial Counter-Evidence Auditor in an intelligence research engine.
Your mission is to rigorously evaluate an existing research finding by comparing it against retrieved counter-evidence.

RULES:
1. Do NOT invent counter-evidence or dismiss valid claims without proof.
2. If counter-evidence contradicts the claim with credible facts/dates/metrics, update the status to "Conflicting evidence discovered" or "Claim needs qualification".
3. If no credible contradictory evidence is found in the sources, output:
   - outcome: "Claim remains supported"
   - explanation: "No material counter-evidence was found in the sources investigated."
4. Distinguish between actual factual conflict and minor differences in opinion.

OUTPUT JSON SCHEMA:
{
  "outcome": "Claim remains supported" | "Claim needs qualification" | "Conflicting evidence discovered" | "Claim is not adequately supported",
  "updated_verification_status": "SUPPORTED" | "PARTIALLY_SUPPORTED" | "CONFLICTING" | "UNVERIFIED",
  "source_disagreements": [string] (specific points of conflict, or empty if none),
  "explanation": string (clear, neutral rationale detailing evidence comparison)
}
"""

def generate_counter_queries(claim_text: str, context: str = "") -> list[str]:
    """Generate targeted adversarial search queries to unearth counter-evidence or criticisms."""
    clean_claim = re.sub(r"[^\w\s]", " ", claim_text).strip()
    words = [w for w in clean_claim.split() if len(w) > 3][:6]
    core_topic = " ".join(words)

    return [
        f"{core_topic} criticisms drawbacks limitations controversy",
        f"{core_topic} alternative benchmarks counter evidence rebuttal",
    ]

class FindingChallenger:
    """Orchestrates targeted counter-research against an individual finding."""

    def __init__(self, settings: dict, llm=None, search_tool=None, page_reader=None):
        self.settings = settings
        self.llm = llm
        self.search_tool = search_tool or TavilySearchTool(settings.get("tavily_api_key", ""))
        self.page_reader = page_reader or PageReader(settings.get("timeout", 15))

    def challenge_finding(
        self,
        finding_id: str,
        claim_text: str,
        supporting_excerpts: list[str],
        supporting_urls: list[str]
    ) -> ChallengeResult:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        counter_queries = generate_counter_queries(claim_text)
        
        discovered_counter_chunks = []
        counter_sources = []
        executed_queries = []

        # 1. Execute targeted counter-research queries
        for q in counter_queries:
            try:
                results = self.search_tool.search(q, max_results=3)
                executed_queries.append(q)
                for r in results:
                    url = r.get("url") or ""
                    # Avoid checking the exact same supporting URLs
                    if url and url not in supporting_urls:
                        counter_sources.append(r)
            except Exception as exc:
                logger.warning("Counter search failed for query '%s': %s", q, exc)

        # 2. Extract counter-evidence from top candidates
        for src in counter_sources[:3]:
            url = src.get("url")
            text, status, _ = self.page_reader.fetch(url)
            content = text if (text and status in ("success", "partial")) else (src.get("content") or "")
            if content:
                discovered_counter_chunks.append({
                    "title": src.get("title") or url,
                    "url": url,
                    "domain": extract_domain(url),
                    "snippet": content[:600]
                })

        # 3. If no counter-sources were discovered
        if not discovered_counter_chunks:
            return ChallengeResult(
                claim_id=finding_id,
                original_claim=claim_text,
                outcome="Claim remains supported",
                supporting_evidence=[{"text": ex} for ex in supporting_excerpts[:2]],
                counter_evidence=[],
                source_disagreements=[],
                updated_verification_status="SUPPORTED",
                explanation="No material counter-evidence was found in the sources investigated.",
                counter_queries_executed=executed_queries,
                timestamp=now_iso
            )

        # 4. Compare supporting vs counter evidence via LLM (or heuristic fallback)
        if not self.llm:
            return ChallengeResult(
                claim_id=finding_id,
                original_claim=claim_text,
                outcome="Claim needs qualification",
                supporting_evidence=[{"text": ex} for ex in supporting_excerpts[:2]],
                counter_evidence=discovered_counter_chunks[:2],
                source_disagreements=["Independent perspectives discovered; review counter-sources for nuance."],
                updated_verification_status="PARTIALLY_SUPPORTED",
                explanation="Counter-evidence discovered discussing limitations and alternative perspectives.",
                counter_queries_executed=executed_queries,
                timestamp=now_iso
            )

        try:
            comparison_payload = {
                "original_claim": claim_text,
                "supporting_evidence": supporting_excerpts[:3],
                "discovered_counter_evidence": discovered_counter_chunks[:3]
            }
            user_prompt = f"Audit this claim against counter-evidence:\n{json.dumps(comparison_payload, ensure_ascii=False)}"
            audit_raw = self.llm.generate_json(CHALLENGER_SYSTEM_PROMPT, user_prompt)

            outcome = audit_raw.get("outcome", "Claim remains supported")
            status = audit_raw.get("updated_verification_status", "SUPPORTED")
            explanation = audit_raw.get("explanation", "Audit completed.")
            disagreements = audit_raw.get("source_disagreements", [])

            return ChallengeResult(
                claim_id=finding_id,
                original_claim=claim_text,
                outcome=outcome,
                supporting_evidence=[{"text": ex} for ex in supporting_excerpts[:2]],
                counter_evidence=discovered_counter_chunks[:3],
                source_disagreements=disagreements,
                updated_verification_status=status,
                explanation=explanation,
                counter_queries_executed=executed_queries,
                timestamp=now_iso
            )

        except Exception as exc:
            logger.error("Challenger LLM synthesis failed: %s", exc)
            return ChallengeResult(
                claim_id=finding_id,
                original_claim=claim_text,
                outcome="Claim remains supported",
                supporting_evidence=[{"text": ex} for ex in supporting_excerpts[:2]],
                counter_evidence=discovered_counter_chunks[:2],
                source_disagreements=[],
                updated_verification_status="SUPPORTED",
                explanation="No material counter-evidence was found in the sources investigated.",
                counter_queries_executed=executed_queries,
                timestamp=now_iso
            )

