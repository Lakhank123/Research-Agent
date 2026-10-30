import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from agents.planner import create_plan
from agents.synthesizer import synthesize_report
from agents.decision_brief import generate_decision_brief
from core.completeness import extract_research_contract, evaluate_completeness_gate
from core.evidence import evaluate_multi_dimensional_confidence, verify_and_ground_citations
from core.gap_analyzer import analyze_research_gaps
from core.retrieval import chunk_text, rank_and_build_evidence_ledger, EvidenceLedger
from core.schemas import ResearchReport, ResearchPlan, SourceRecord, Finding
from tools.web_search import TavilySearchTool, rank_and_filter_sources, SearchError
from tools.page_reader import PageReader

logger = logging.getLogger(__name__)

class ResearchOrchestrator:
    """
    Research Integrity Engine orchestrating the complete 6-stage evidence pipeline:
    Understanding -> Planning -> Discovery -> Extraction -> BM25 Ledgering -> Completeness Gate -> Decision Synthesis.
    """

    def __init__(self, settings: dict, llm=None, search_tool=None, page_reader=None):
        self.settings = settings
        self.llm = llm
        self.search_tool = search_tool
        self.page_reader = page_reader

    def run(self, question: str, depth: str = "standard", progress_callback: Optional[Callable] = None) -> dict:
        clean_question = (question or "").strip()
        if len(clean_question) < 5:
            raise ValueError("Please provide a research question of at least 5 characters.")

        trace = []
        started_at = time.time()

        def log_event(stage: str, status: str, detail: str, duration: Optional[float] = None, data: Optional[dict] = None):
            event = {
                "stage": stage,
                "status": status,
                "detail": detail,
                "duration_seconds": round(duration, 2) if duration is not None else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data or {},
            }
            trace.append(event)
            if progress_callback:
                progress_callback(event)

        # -------------------------------------------------------------------------
        # STAGE 1 & 2: INTENT UNDERSTANDING, CONTRACT & PLANNING
        # -------------------------------------------------------------------------
        t_plan = time.time()
        log_event("planning", "running", f"Formulating research contract and {depth} execution plan...")

        contract = extract_research_contract(clean_question)
        plan = create_plan(self.llm, clean_question, depth=depth)
        plan.intent.contract = contract

        plan_duration = time.time() - t_plan
        intent = plan.intent

        log_event(
            "planning",
            "completed",
            f"Formulated {intent.research_category} plan. Target: {contract.required_entities_count or 'Comprehensive'} entities across {len(plan.search_queries)} queries.",
            duration=plan_duration,
            data={
                "category": intent.research_category,
                "target_entities": contract.required_entities_count,
                "queries": [q.query for q in plan.search_queries]
            }
        )

        # Search budgets
        depth_configs = {
            "quick": {"queries": 3, "sources": 5, "chunks": 8},
            "standard": {"queries": 4, "sources": 8, "chunks": 12},
            "deep": {"queries": 5, "sources": 10, "chunks": 16},
        }
        limits = depth_configs.get(depth, depth_configs["standard"])
        max_q = min(limits["queries"], self.settings.get("max_search_queries", 5))
        max_src = min(limits["sources"], self.settings.get("max_sources", 8))
        max_chk = min(limits["chunks"], self.settings.get("max_chunks_in_context", 14))

        queries_to_run = plan.search_queries[:max_q]

        # -------------------------------------------------------------------------
        # STAGE 3: WEB DISCOVERY & SOURCE QUALITY RANKING
        # -------------------------------------------------------------------------
        t_search = time.time()
        log_event("web_search", "running", f"Executing {len(queries_to_run)} targeted queries across authoritative sources...")

        search_tool = self.search_tool
        if not search_tool:
            try:
                search_tool = TavilySearchTool(self.settings.get("tavily_api_key", ""))
            except Exception as exc:
                search_tool = None
                log_event("web_search", "failed", f"Search tool unavailable: {exc}", 0)

        candidate_results = []
        search_errors = []
        queries_executed_count = 0

        if search_tool:
            for q_plan in queries_to_run:
                try:
                    results = search_tool.search(q_plan.query, max_results=5)
                    queries_executed_count += 1
                    for r in results:
                        r["_query"] = q_plan.query
                        r["_aspect"] = q_plan.target_aspect
                        candidate_results.append(r)
                except Exception as exc:
                    search_errors.append(f"Query '{q_plan.query}': {exc}")
                    logger.warning("Search query failed (%s): %s", q_plan.query, exc)

        search_duration = time.time() - t_search

        if not candidate_results:
            log_event(
                "web_search",
                "completed" if not search_errors else "failed",
                f"Discovered 0 results across {queries_executed_count} queries.",
                duration=search_duration
            )
            final_report = ResearchReport(
                user_question=clean_question,
                status="FAILED",
                contract=contract,
                executive_summary="No web sources could be discovered for this research question.",
                short_answer="No web sources could be discovered for this research question.",
                confidence="low",
                confidence_reason="No web search results were retrieved.",
                limitations=["Search returned zero results. Verify API credentials, query parameters, and network status."],
                suggested_next_steps=["Check your Tavily API configuration and quota.", "Try rephrasing the question."]
            )
            return {
                "plan": plan.model_dump(),
                "report": final_report.model_dump(),
                "trace": trace,
                "metrics": {
                    "total_duration_seconds": round(time.time() - started_at, 2),
                    "queries_planned": len(queries_to_run),
                    "queries_executed": queries_executed_count,
                    "candidates_discovered": 0,
                    "sources_selected": 0,
                    "sources_extracted": 0,
                    "chunks_selected": 0,
                }
            }

        # Deduplicate, score authority, rank, enforce domain diversity
        selected_sources = rank_and_filter_sources(
            candidate_results=candidate_results,
            main_question=clean_question,
            target_count=max_src,
            max_per_domain=2
        )

        log_event(
            "web_search",
            "completed",
            f"Executed {queries_executed_count} queries. Filtered {len(candidate_results)} candidates into {len(selected_sources)} top-ranked sources.",
            duration=search_duration,
            data={"sources_found": len(selected_sources), "candidates": len(candidate_results)}
        )

        # -------------------------------------------------------------------------
        # STAGE 4: EXTRACTION & BOILERPLATE REMOVAL
        # -------------------------------------------------------------------------
        t_extract = time.time()
        log_event("extracting", "running", f"Extracting full content from {len(selected_sources)} sources with boilerplate stripping...")

        reader = self.page_reader or PageReader(self.settings.get("timeout", 15))
        all_raw_chunks = []
        extracted_count = 0

        for src in selected_sources:
            t_doc = time.time()
            text, status, meta = reader.fetch(src.url)
            src.extraction_status = status

            if meta.get("published_date") and not src.published_date:
                src.published_date = meta["published_date"]
            if meta.get("author") and not src.publisher:
                src.publisher = meta["author"]

            if text and status in ("success", "partial"):
                src.extracted = (status == "success")
                if src.extracted:
                    extracted_count += 1
                doc_chunks = chunk_text(
                    text=text,
                    source_id=src.source_id,
                    title=src.title,
                    url=src.url,
                    source_type=src.source_type
                )
                all_raw_chunks.extend(doc_chunks)
            else:
                snippet = src.snippet or ""
                if len(snippet) >= 30:
                    src.extraction_status = "snippet_only"
                    snippet_chunks = chunk_text(
                        text=snippet,
                        source_id=src.source_id,
                        title=src.title,
                        url=src.url,
                        source_type=src.source_type
                    )
                    all_raw_chunks.extend(snippet_chunks)

            doc_dur = time.time() - t_doc
            log_event(
                "extracting",
                "completed" if src.extracted else "partial",
                f"{src.source_id} ({src.domain}): {src.extraction_status}",
                duration=doc_dur
            )

        extract_duration = time.time() - t_extract
        log_event(
            "extracting",
            "completed",
            f"Extracted {extracted_count}/{len(selected_sources)} full web pages; produced {len(all_raw_chunks)} evidence chunks.",
            duration=extract_duration
        )

        # -------------------------------------------------------------------------
        # STAGE 5: RETRIEVAL, EVIDENCE LEDGER & CONFIDENCE BREAKDOWN
        # -------------------------------------------------------------------------
        t_eval = time.time()
        log_event("evaluating_evidence", "running", "Ranking evidence with Okapi BM25 and constructing Evidence Ledger...")

        evidence_ledger = rank_and_build_evidence_ledger(
            chunks=all_raw_chunks,
            main_question=clean_question,
            subtasks=plan.subtasks,
            entities=intent.entities,
            sources=selected_sources,
            top_k=max_chk,
            max_chunks_per_source=3
        )

        eval_duration = time.time() - t_eval
        log_event(
            "evaluating_evidence",
            "completed",
            f"Built Evidence Ledger with {len(evidence_ledger.chunks)} prioritized chunks.",
            duration=eval_duration
        )

        # -------------------------------------------------------------------------
        # STAGE 6: GROUNDED SYNTHESIS, COMPLETENESS GATE & DECISION BRIEF
        # -------------------------------------------------------------------------
        t_synth = time.time()
        log_event("generating_report", "running", "Synthesizing intelligence report and verifying claims against Evidence Ledger...")

        limitations = []
        if search_errors:
            limitations.append(f"{len(search_errors)} search query operations encountered issues.")
        if any(not s.extracted for s in selected_sources):
            limitations.append("Some sources could not be fully scraped; snippet-level evidence was utilized where available.")

        final_report: Optional[ResearchReport] = None
        execution_status = "COMPLETED"

        if not self.llm or not evidence_ledger.chunks:
            execution_status = "PARTIALLY_COMPLETED" if evidence_ledger.chunks else "FAILED"
            conf_label, conf_score, breakdown, conf_reason = evaluate_multi_dimensional_confidence(
                sources=selected_sources,
                ledger=evidence_ledger,
                subtasks=plan.subtasks,
                findings=[]
            )
            completeness = evaluate_completeness_gate(contract, [], selected_sources, intent.research_category)
            gaps = analyze_research_gaps(clean_question, contract, plan.subtasks, [], selected_sources, intent.research_category)
            decision = generate_decision_brief(None, clean_question, intent.research_category, "", [], selected_sources, conf_label)

            final_report = ResearchReport(
                user_question=clean_question,
                status=execution_status,
                contract=contract,
                completeness=completeness,
                executive_summary="Evidence was compiled from web sources, but LLM synthesis was unavailable.",
                short_answer="Evidence was compiled from web sources, but LLM synthesis was unavailable.",
                coverage_matrix=gaps,
                decision_brief=decision,
                sources_used=selected_sources,
                confidence=conf_label,
                confidence_score=conf_score,
                confidence_breakdown=breakdown,
                confidence_reason=conf_reason,
                limitations=limitations or ["LLM synthesis was unavailable."],
                suggested_next_steps=["Inspect the collected sources and execution trace."]
            )
            log_event("generating_report", "partial", "Report compiled without LLM synthesis.", time.time() - t_synth)
        else:
            try:
                # Preliminary confidence assessment for synthesis context
                conf_label, conf_score, breakdown, conf_reason = evaluate_multi_dimensional_confidence(
                    sources=selected_sources,
                    ledger=evidence_ledger,
                    subtasks=plan.subtasks,
                    findings=[]
                )

                raw_report = synthesize_report(
                    llm=self.llm,
                    question=clean_question,
                    plan=plan.model_dump(),
                    ledger=evidence_ledger,
                    source_records=[s.model_dump() for s in selected_sources],
                    assessment={"confidence": conf_label, "confidence_reason": conf_reason}
                )

                # Citation validation and claim-level verification
                valid_source_ids = {s.source_id for s in selected_sources}
                grounded_dict = verify_and_ground_citations(
                    report_dict=raw_report.model_dump(),
                    ledger=evidence_ledger,
                    valid_source_ids=valid_source_ids
                )

                grounded_findings = [Finding.model_validate(f) for f in grounded_dict.get("key_findings", [])]

                # Full multi-dimensional confidence calculation with verified findings
                conf_label, conf_score, breakdown, conf_reason = evaluate_multi_dimensional_confidence(
                    sources=selected_sources,
                    ledger=evidence_ledger,
                    subtasks=plan.subtasks,
                    findings=grounded_findings
                )

                # Research Completeness Gate Audit
                completeness = evaluate_completeness_gate(
                    contract=contract,
                    findings=grounded_findings,
                    sources=selected_sources,
                    category=intent.research_category
                )

                # If contract required N entities and we got fewer, execution state MUST be PARTIALLY_COMPLETED
                if not completeness.is_complete and completeness.missing_count > 0:
                    execution_status = "PARTIALLY_COMPLETED"
                    limitations.append(completeness.gap_explanation)
                else:
                    execution_status = "COMPLETED"

                # Research Gap Analyzer
                gaps = analyze_research_gaps(
                    question=clean_question,
                    contract=contract,
                    subtasks=plan.subtasks,
                    findings=grounded_findings,
                    sources=selected_sources,
                    category=intent.research_category
                )

                # Decision Brief Synthesis
                decision = generate_decision_brief(
                    llm=self.llm,
                    question=clean_question,
                    category=intent.research_category,
                    executive_summary=grounded_dict.get("executive_summary", ""),
                    findings=grounded_findings,
                    sources=selected_sources,
                    confidence=conf_label
                )

                # Merge limitations
                existing_lims = grounded_dict.get("limitations", [])
                grounded_dict["limitations"] = list(dict.fromkeys(existing_lims + limitations))
                grounded_dict["status"] = execution_status
                grounded_dict["contract"] = contract.model_dump()
                grounded_dict["completeness"] = completeness.model_dump()
                grounded_dict["coverage_matrix"] = gaps.model_dump()
                grounded_dict["decision_brief"] = decision.model_dump()
                grounded_dict["confidence"] = conf_label
                grounded_dict["confidence_score"] = conf_score
                grounded_dict["confidence_breakdown"] = breakdown.model_dump()
                grounded_dict["confidence_reason"] = conf_reason

                final_report = ResearchReport.model_validate(grounded_dict)

                log_event(
                    "generating_report",
                    "completed" if execution_status == "COMPLETED" else "partial",
                    f"Generated report ({execution_status}): {len(final_report.key_findings)} grounded findings. Completeness: {completeness.verified_count}/{completeness.target_count or len(grounded_findings)}.",
                    time.time() - t_synth
                )

            except Exception as exc:
                logger.error("Synthesis failed: %s", exc, exc_info=True)
                execution_status = "PARTIALLY_COMPLETED"
                log_event("generating_report", "failed", f"LLM synthesis issue: {exc}", time.time() - t_synth)
                completeness = evaluate_completeness_gate(contract, [], selected_sources, intent.research_category)
                gaps = analyze_research_gaps(clean_question, contract, plan.subtasks, [], selected_sources, intent.research_category)
                decision = generate_decision_brief(None, clean_question, intent.research_category, "", [], selected_sources, "low")

                final_report = ResearchReport(
                    user_question=clean_question,
                    status=execution_status,
                    contract=contract,
                    completeness=completeness,
                    executive_summary="Web evidence was successfully gathered, but synthesis encountered an issue.",
                    short_answer="Web evidence was successfully gathered, but synthesis encountered an issue.",
                    coverage_matrix=gaps,
                    decision_brief=decision,
                    sources_used=selected_sources,
                    confidence="low",
                    confidence_score=0.3,
                    confidence_reason=f"Synthesis degraded: {type(exc).__name__}",
                    limitations=limitations + [f"Synthesis error: {type(exc).__name__}."],
                    suggested_next_steps=["Review the collected sources in the Explorer."]
                )

        total_duration = time.time() - started_at

        return {
            "plan": plan.model_dump(),
            "report": final_report.model_dump(),
            "trace": trace,
            "metrics": {
                "total_duration_seconds": round(total_duration, 2),
                "queries_planned": len(queries_to_run),
                "queries_executed": queries_executed_count,
                "candidates_discovered": len(candidate_results),
                "sources_found": len(selected_sources),
                "sources_extracted": extracted_count,
                "chunks_considered": len(all_raw_chunks),
                "chunks_selected": len(evidence_ledger.chunks),
                "confidence_score": final_report.confidence_score,
                "execution_status": execution_status,
                "completeness_verified": final_report.completeness.verified_count,
                "completeness_target": final_report.completeness.target_count,
            }
        }
