import json
import logging
from typing import Optional
from core.schemas import DecisionBrief, Finding, SourceRecord

logger = logging.getLogger(__name__)

DECISION_BRIEF_PROMPT = """You are an Executive Strategic Advisor synthesizing a decision-support brief from evidence-grounded research findings.
Distinguish strictly between verifiable facts and strategic analysis/recommendations.

OUTPUT SCHEMA:
{
  "main_conclusion": string (concise, high-conviction bottom-line takeaway),
  "key_evidence": [string] (3-4 definitive data points or facts supporting the conclusion),
  "available_options": [
    {
      "name": string (option/technology/company/approach),
      "pros": [string],
      "cons": [string],
      "best_for": string
    }
  ],
  "comparative_advantages": [string],
  "disadvantages_and_tradeoffs": [string],
  "strategic_risks": [string] (execution, regulatory, lock-in, financial, or technical risks),
  "important_uncertainties": [string] (data points that could alter the decision),
  "recommendation": string or null (actionable recommendation ONLY when justified by evidence; do not manufacture false certainty),
  "next_practical_action": string (immediate concrete next step, e.g. run pilot benchmark, request vendor demo, verify balance sheet)
}
"""

def generate_decision_brief(
    llm,
    question: str,
    category: str,
    executive_summary: str,
    findings: list[Finding],
    sources: list[SourceRecord],
    confidence: str
) -> DecisionBrief:
    """Synthesize a high-utility decision brief for executive leadership."""
    if not llm:
        # Heuristic fallback
        return DecisionBrief(
            main_conclusion=executive_summary or "Research compiled from verified sources.",
            key_evidence=[f.finding for f in findings[:3]],
            available_options=[],
            comparative_advantages=[],
            disadvantages_and_tradeoffs=[l for f in findings for l in f.caveats][:3],
            strategic_risks=["Data points rely on third-party published documentation."],
            important_uncertainties=["Full proprietary commercial terms require direct validation."],
            recommendation="Review the source records and conduct a targeted trial." if confidence != "low" else None,
            next_practical_action="Evaluate primary documentation and conduct direct due diligence."
        )

    try:
        payload = {
            "question": question,
            "category": category,
            "executive_summary": executive_summary,
            "findings": [
                {"title": f.finding, "explanation": f.explanation, "citations": f.citations, "metrics": f.metrics_or_figures}
                for f in findings
            ],
            "confidence": confidence
        }
        user_prompt = f"Produce a Decision Brief for this investigation:\n{json.dumps(payload, ensure_ascii=False)}"
        raw = llm.generate_json(DECISION_BRIEF_PROMPT, user_prompt)

        return DecisionBrief.model_validate(raw)
    except Exception as exc:
        logger.error("Decision brief generation failed: %s", exc)
        return DecisionBrief(
            main_conclusion=executive_summary or "Investigation completed across verified evidence.",
            key_evidence=[f.finding for f in findings[:3]],
            available_options=[],
            comparative_advantages=[],
            disadvantages_and_tradeoffs=[],
            strategic_risks=["Detailed decision brief could not be synthesized via LLM."],
            important_uncertainties=[],
            recommendation=None,
            next_practical_action="Consult the Key Findings and Sources Explorer."
        )

