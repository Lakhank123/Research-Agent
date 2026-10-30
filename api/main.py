import asyncio
import io
import json
import logging
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("researchpilot.api")

from core.config import get_settings
from core.llm import GroqProvider
from core.storage import (
    save_research_run,
    list_recent_runs,
    get_research_run,
    save_challenge_record,
    get_challenges_for_run
)
from orchestrator import ResearchOrchestrator
from agents.challenger import FindingChallenger

app = FastAPI(
    title="ResearchPilot AI 3.0 API",
    description="The Research Integrity Engine — Evidence-Driven Autonomous Research API",
    version="3.0.0"
)

# Enable CORS for React development server & local hosts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory event queues for live SSE streaming per run_id
# run_id -> asyncio.Queue
ACTIVE_EVENT_QUEUES: dict[str, asyncio.Queue] = {}
ACTIVE_RUN_RESULTS: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# REQUEST & RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class StartResearchRequest(BaseModel):
    question: str
    depth: str = "standard"

class StartResearchResponse(BaseModel):
    run_id: str
    question: str
    depth: str
    status: str = "started"

class ChallengeFindingRequest(BaseModel):
    run_id: str
    finding_id: str
    claim_text: str
    supporting_excerpts: list[str] = Field(default_factory=list)
    supporting_urls: list[str] = Field(default_factory=list)

class InvestigateGapsRequest(BaseModel):
    run_id: str
    gap_queries: list[str]

# ---------------------------------------------------------------------------
# BACKGROUND WORKER
# ---------------------------------------------------------------------------

def run_research_pipeline_sync(run_id: str, question: str, depth: str, loop: asyncio.AbstractEventLoop):
    queue = ACTIVE_EVENT_QUEUES.get(run_id)
    settings = get_settings()

    def progress_callback(event: dict):
        if queue and not loop.is_closed():
            # Safely put event onto async queue from sync thread
            loop.call_soon_threadsafe(queue.put_nowait, event)

    try:
        llm = GroqProvider(
            api_key=settings["groq_api_key"],
            model=settings["groq_model"],
            fallback_model=settings.get("groq_fallback_model")
        )
        orchestrator = ResearchOrchestrator(settings=settings, llm=llm)
        result = orchestrator.run(question, depth=depth, progress_callback=progress_callback)

        ACTIVE_RUN_RESULTS[run_id] = result
        save_research_run(run_id, question, depth, result)

        # Send completion event
        if queue and not loop.is_closed():
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"stage": "done", "status": "completed", "detail": "Research completed successfully."}
            )

    except Exception as exc:
        logger.exception("Research pipeline error for run %s: %s", run_id, exc)
        err_event = {
            "stage": "error",
            "status": "failed",
            "detail": f"Investigation error: {type(exc).__name__}: {str(exc)}"
        }
        if queue and not loop.is_closed():
            loop.call_soon_threadsafe(queue.put_nowait, err_event)
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"stage": "done", "status": "failed", "detail": str(exc)}
            )

# ---------------------------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/health")
def get_health():
    settings = get_settings()
    has_groq = bool(settings.get("groq_api_key"))
    has_tavily = bool(settings.get("tavily_api_key"))

    active_model = settings.get("groq_model", "openai/gpt-oss-120b")
    model_status = "unverified"

    if has_groq:
        try:
            prov = GroqProvider(settings["groq_api_key"], active_model, settings.get("groq_fallback_model"))
            active_model = prov.preflight_model()
            model_status = "verified_online"
        except Exception as e:
            model_status = f"error: {type(e).__name__}"

    return {
        "status": "online",
        "version": "3.0.0",
        "active_model": active_model,
        "model_status": model_status,
        "groq_configured": has_groq,
        "tavily_configured": has_tavily,
        "ranking_engine": "Okapi BM25",
        "integrity_engine": "Claim Ledger + Completeness Gate + Counter-Research"
    }

@app.post("/api/research/start", response_model=StartResearchResponse)
async def start_research(req: StartResearchRequest, background_tasks: BackgroundTasks):
    clean_q = req.question.strip()
    if len(clean_q) < 5:
        raise HTTPException(status_code=400, detail="Question must be at least 5 characters.")

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    ACTIVE_EVENT_QUEUES[run_id] = asyncio.Queue()

    loop = asyncio.get_running_loop()
    background_tasks.add_task(run_research_pipeline_sync, run_id, clean_q, req.depth, loop)

    return StartResearchResponse(run_id=run_id, question=clean_q, depth=req.depth, status="started")

@app.get("/api/research/stream/{run_id}")
async def stream_research_events(run_id: str):
    """Server-Sent Events streaming live pipeline stage transitions."""
    if run_id not in ACTIVE_EVENT_QUEUES:
        # Check if already completed and stored
        run_data = get_research_run(run_id)
        if run_data:
            async def single_event():
                yield {"data": json.dumps({"stage": "done", "status": "completed", "detail": "Already completed."})}
            return EventSourceResponse(single_event())
        raise HTTPException(status_code=404, detail="Run ID not found or already expired.")

    queue = ACTIVE_EVENT_QUEUES[run_id]

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield {"data": json.dumps(event)}
                if event.get("stage") == "done":
                    break
            except asyncio.TimeoutError:
                # Keep-alive heartbeat
                yield {"data": json.dumps({"stage": "heartbeat", "status": "running", "detail": "still processing..."})}

    return EventSourceResponse(event_generator())

@app.get("/api/research/report/{run_id}")
def get_report(run_id: str):
    """Retrieve full research report, plan, metrics, and associated challenges."""
    data = ACTIVE_RUN_RESULTS.get(run_id) or get_research_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Report for run '{run_id}' not found.")

    challenges = get_challenges_for_run(run_id)
    return {
        "run_id": run_id,
        "plan": data.get("plan"),
        "report": data.get("report"),
        "metrics": data.get("metrics"),
        "challenges": challenges
    }

@app.post("/api/research/challenge")
def challenge_finding(req: ChallengeFindingRequest):
    """Active counter-research: generates counter-queries, hunts contradictory evidence, reassesses claim."""
    settings = get_settings()
    llm = GroqProvider(
        api_key=settings["groq_api_key"],
        model=settings["groq_model"],
        fallback_model=settings.get("groq_fallback_model")
    )
    challenger = FindingChallenger(settings=settings, llm=llm)

    result = challenger.challenge_finding(
        finding_id=req.finding_id,
        claim_text=req.claim_text,
        supporting_excerpts=req.supporting_excerpts,
        supporting_urls=req.supporting_urls
    )

    save_challenge_record(req.run_id, req.finding_id, req.claim_text, result.model_dump())
    return result.model_dump()

@app.post("/api/research/investigate-gaps")
def investigate_gaps(req: InvestigateGapsRequest):
    """Targeted follow-up search for specific missing dimensions identified in the Gap Analyzer."""
    settings = get_settings()
    from tools.web_search import TavilySearchTool
    from core.retrieval import chunk_text

    search = TavilySearchTool(settings.get("tavily_api_key", ""))
    discovered_gap_chunks = []

    for q in req.gap_queries[:3]:
        try:
            results = search.search(q, max_results=3)
            for r in results:
                chunks = chunk_text(r.get("content", ""), "GAP-S", r.get("title", ""), r.get("url", ""))
                for c in chunks:
                    discovered_gap_chunks.append({
                        "query": q,
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": c.text[:300]
                    })
        except Exception as exc:
            logger.warning("Gap investigation query failed: %s", exc)

    return {
        "run_id": req.run_id,
        "investigated_queries": req.gap_queries[:3],
        "discovered_evidence": discovered_gap_chunks
    }

@app.get("/api/history")
def get_history(limit: int = Query(25, ge=1, le=100)):
    return list_recent_runs(limit=limit)

@app.get("/api/history/{run_id}")
def get_history_item(run_id: str):
    item = get_research_run(run_id)
    if not item:
        raise HTTPException(status_code=404, detail="Investigation not found in history.")
    challenges = get_challenges_for_run(run_id)
    item["challenges"] = challenges
    return item

@app.get("/api/export/{run_id}")
def export_report(run_id: str, format: str = Query("markdown", pattern="^(markdown|json|csv)$")):
    data = ACTIVE_RUN_RESULTS.get(run_id) or get_research_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail="Run not found.")

    report = data.get("report", {})
    question = report.get("user_question", "Research Report")

    if format == "json":
        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="researchpilot_{run_id}.json"'}
        )

    elif format == "csv":
        comp = report.get("comparison_table")
        if not comp or not comp.get("headers"):
            raise HTTPException(status_code=400, detail="No comparison table found in this report to export as CSV.")
        
        headers = comp["headers"]
        rows = comp.get("rows", [])
        
        output = io.StringIO()
        output.write(",".join(f'"{h}"' for h in headers) + "\n")
        for r in rows:
            line = [f'"{r.get(h, "")}"' for h in headers]
            output.write(",".join(line) + "\n")
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="comparison_{run_id}.csv"'}
        )

    else:
        # Markdown export
        md = f"# Research Report: {question}\n\n"
        md += f"**Execution Status:** {report.get('status')}\n"
        md += f"**Confidence:** {report.get('confidence', '').upper()} ({report.get('confidence_reason')})\n\n"
        
        completeness = report.get("completeness", {})
        if completeness.get("target_count"):
            md += f"**Completeness:** {completeness.get('verified_count')}/{completeness.get('target_count')} verified entities\n\n"

        md += f"## Executive Summary\n{report.get('executive_summary')}\n\n"
        
        decision = report.get("decision_brief", {})
        if decision.get("main_conclusion"):
            md += f"## Decision Brief\n**Conclusion:** {decision.get('main_conclusion')}\n"
            if decision.get("recommendation"):
                md += f"**Recommendation:** {decision.get('recommendation')}\n"
            if decision.get("next_practical_action"):
                md += f"**Next Action:** {decision.get('next_practical_action')}\n\n"

        md += "## Key Findings & Verification Status\n"
        for idx, f in enumerate(report.get("key_findings", []), 1):
            md += f"### {idx}. {f.get('finding')} [{f.get('verification_status')}]\n"
            md += f"{f.get('explanation')}\n"
            if f.get("citations"):
                md += f"**Sources:** {', '.join(f.get('citations'))}\n\n"

        md += "## Sources Used\n"
        for s in report.get("sources_used", []):
            md += f"- **[{s.get('source_id')}] [{s.get('title')}]({s.get('url')})** (Authority: {s.get('authority_score', 0.5):.2f})\n"

        return Response(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="research_{run_id}.md"'}
        )

# Mount React production build if available
import os
from fastapi.staticfiles import StaticFiles

_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(_dist_path):
    app.mount("/", StaticFiles(directory=_dist_path, html=True), name="frontend")

