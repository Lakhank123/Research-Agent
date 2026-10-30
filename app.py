import json
import os
import streamlit as st
from dotenv import load_dotenv

from core.config import get_settings
from core.llm import GroqProvider, LLMAuthenticationError, LLMModelNotFoundError
from orchestrator import ResearchOrchestrator

# Force reload of environment
load_dotenv(override=True)

st.set_page_config(
    page_title="ResearchPilot AI — Autonomous Research Intelligence",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# PROFESSIONAL SAAS STYLESHEET
# -----------------------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
  
  html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  }
  
  /* App header */
  .brand-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 0 1.5rem 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 1.5rem;
  }
  .brand-title {
    font-size: 1.65rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
  }
  .brand-subtitle {
    font-size: 0.92rem;
    color: #475569;
    margin-top: 0.25rem;
  }
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
  }
  .status-pill.online {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
  }
  .status-pill.offline {
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
  }
  
  /* Metric cards */
  .metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    text-align: center;
  }
  .metric-card-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #64748b;
  }
  .metric-card-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0.2rem;
  }
  
  /* Stage progress timeline */
  .stage-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
  }
  .stage-box.running {
    border-color: #0f766e;
    background: #f0fdfa;
  }
  .stage-box.completed {
    border-color: #cbd5e1;
    background: #ffffff;
  }
  .stage-box.failed {
    border-color: #fca5a5;
    background: #fef2f2;
  }
  
  /* Finding cards */
  .finding-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #0f766e;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  }
  .finding-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }
  .citation-tag {
    display: inline-block;
    background: #f1f5f9;
    color: #0f766e;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.15rem 0.45rem;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 0.35rem;
    margin-top: 0.35rem;
  }
  
  /* Source card */
  .source-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .source-card:hover {
    box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08);
  }
  .source-badge {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
  }
  .badge-official { background: #e0f2fe; color: #0369a1; }
  .badge-media { background: #fef3c7; color: #b45309; }
  .badge-academic { background: #ede9fe; color: #6d28d9; }
  .badge-general { background: #f1f5f9; color: #475569; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# APPLICATION STATE & PREFLIGHT
# -----------------------------------------------------------------------------
settings = get_settings()

if "latest_result" not in st.session_state:
    st.session_state["latest_result"] = None
if "active_question" not in st.session_state:
    st.session_state["active_question"] = ""

# Preflight Groq and Tavily
groq_status = "unconfigured"
tavily_status = "unconfigured"
active_model_name = settings["groq_model"]
preflight_note = ""

if settings["groq_api_key"]:
    try:
        preflight_provider = GroqProvider(settings["groq_api_key"], settings["groq_model"], settings.get("groq_fallback_model"))
        active_model_name = preflight_provider.preflight_model()
        groq_status = "online"
        preflight_note = preflight_provider.model_status_note
    except Exception as exc:
        groq_status = "error"
        preflight_note = str(exc)

if settings["tavily_api_key"]:
    tavily_status = "online"

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & CONFIGURATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 System Diagnostics")
    
    # Model connection
    if groq_status == "online":
        st.markdown(f"**Groq Status:** `Verified Online`")
        st.markdown(f"**Active Model:** `{active_model_name}`")
        if "Switched" in preflight_note:
            st.info(preflight_note)
    elif groq_status == "error":
        st.error(f"Groq Model Error:\n{preflight_note}")
    else:
        st.warning("GROQ_API_KEY is not configured in .env")

    # Search connection
    if tavily_status == "online":
        st.markdown("**Search Tool:** `Tavily Verified`")
    else:
        st.warning("TAVILY_API_KEY is not configured in .env")

    st.divider()
    st.markdown("### ⚙️ Engine Parameters")
    st.markdown(f"- **Max Search Queries:** `{settings['max_search_queries']}`")
    st.markdown(f"- **Target Sources:** `{settings['max_sources']}`")
    st.markdown(f"- **Evidence Context Chunks:** `{settings['max_chunks_in_context']}`")
    st.markdown(f"- **Ranking Engine:** `Okapi BM25 Lexical`")
    st.markdown(f"- **Extraction Engine:** `Trafilatura + LXML`")
    
    st.divider()
    st.caption("🔒 All credentials are kept private in `.env`. Retrieved webpage content is strictly treated as untrusted data.")

# -----------------------------------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div class="brand-header">
      <div>
        <h1 class="brand-title">🧭 ResearchPilot AI</h1>
        <div class="brand-subtitle">Autonomous evidence-first intelligence engine • Plan → Discover → Extract → BM25 Rank → Synthesize</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    if groq_status == "online" and tavily_status == "online":
        st.markdown('<div style="text-align: right; margin-top: 1.5rem;"><span class="status-pill online">● Systems Operational</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align: right; margin-top: 1.5rem;"><span class="status-pill offline">● Configuration Needed</span></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# RESEARCH QUERY INPUT CARD
# -----------------------------------------------------------------------------
with st.container(border=True):
    col_input, col_ctrl = st.columns([3, 1])
    
    with col_input:
        default_q = st.session_state.get("active_question", "")
        question = st.text_area(
            "Research Query or Investigation Target",
            value=default_q,
            placeholder="e.g., Compare the top 3 open-source vector databases for an enterprise startup building RAG products.",
            height=95,
            help="Enter any technology, industry, company, or market inquiry."
        )

    with col_ctrl:
        depth = st.selectbox(
            "Research Depth",
            options=["standard", "quick", "deep"],
            index=0,
            help="Quick (3 queries, 5 sources) • Standard (4 queries, 8 sources) • Deep (5 queries, 10 sources)"
        )
        run_button = st.button("🚀 Start Autonomous Research", type="primary", use_container_width=True)

    # Clickable Example Chips
    st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #475569; margin-bottom: 0.4rem;'>💡 Explore verified scenarios:</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("⚡ Compare Top 3 Open-Source Vector DBs", use_container_width=True):
        st.session_state["active_question"] = "Compare the top 3 open-source vector databases for a startup building RAG products."
        st.rerun()
    if c2.button("🇮🇳 Indian B2B SaaS HR Tech Startups", use_container_width=True):
        st.session_state["active_question"] = "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning."
        st.rerun()
    if c3.button("🤖 Multi-Agent Architecture for Customer Support", use_container_width=True):
        st.session_state["active_question"] = "Research the pros and cons of using a multi-agent architecture for customer support automation."
        st.rerun()

# -----------------------------------------------------------------------------
# EXECUTION ORCHESTRATION PIPELINE
# -----------------------------------------------------------------------------
if run_button:
    if not settings["groq_api_key"] or not settings["tavily_api_key"]:
        st.error("Missing credentials. Please configure GROQ_API_KEY and TAVILY_API_KEY in your `.env` file.")
    elif not question.strip():
        st.warning("Please enter a research question first.")
    else:
        st.session_state["active_question"] = question
        
        # Stages tracker visual
        stages_ui = {
            "planning": st.empty(),
            "web_search": st.empty(),
            "extracting": st.empty(),
            "evaluating_evidence": st.empty(),
            "generating_report": st.empty(),
        }

        stage_labels = {
            "planning": ("1. Intent Understanding & Planning", "Analyzing research scope, entities, and search strategy"),
            "web_search": ("2. Web Discovery & Source Ranking", "Executing targeted queries across authoritative domains"),
            "extracting": ("3. Content Extraction & Boilerplate Stripping", "Scraping full text, cleaning navigation, and parsing tables"),
            "evaluating_evidence": ("4. BM25 Evidence Scoring & Ledgering", "Lexical ranking across subtasks and assembling evidence ledger"),
            "generating_report": ("5. Grounded Report Synthesis", "Verifying citations and generating structured report"),
        }

        def render_stage(stage_key, state, detail=""):
            title, desc = stage_labels.get(stage_key, (stage_key, ""))
            icon = "⏳" if state == "running" else ("✅" if state == "completed" else ("⚠️" if state == "partial" else "❌"))
            css_class = state
            html = f"""
            <div class="stage-box {css_class}">
              <div>
                <strong>{icon} {title}</strong>
                <div style="font-size: 0.8rem; color: #475569; margin-top: 0.15rem;">{detail or desc}</div>
              </div>
              <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #0f766e;">{state}</div>
            </div>
            """
            if stage_key in stages_ui:
                stages_ui[stage_key].markdown(html, unsafe_allow_html=True)

        for s in stages_ui:
            render_stage(s, "pending")

        def on_progress(event):
            stage = event.get("stage")
            status = event.get("status")
            detail = event.get("detail", "")
            if stage in stages_ui:
                render_stage(stage, status, detail)

        with st.spinner("Conducting evidence-first investigation..."):
            try:
                llm = GroqProvider(
                    api_key=settings["groq_api_key"],
                    model=settings["groq_model"],
                    fallback_model=settings.get("groq_fallback_model")
                )
                orchestrator = ResearchOrchestrator(settings=settings, llm=llm)
                result = orchestrator.run(question, depth=depth, progress_callback=on_progress)
                st.session_state["latest_result"] = result
                st.success("Investigation complete.")
            except Exception as exc:
                st.error(f"Research pipeline encountered an error: {exc}")

# -----------------------------------------------------------------------------
# DISPLAY RESEARCH RESULTS DASHBOARD
# -----------------------------------------------------------------------------
result = st.session_state.get("latest_result")

if result:
    report = result["report"]
    plan = result["plan"]
    metrics = result["metrics"]
    intent = plan.get("intent", {})

    st.markdown("---")

    # 1. AMBIGUITY NOTICE (If detected by Planner)
    if intent.get("ambiguity_level") == "significant":
        st.warning(
            f"**Ambiguity Notice:** The research question has multiple distinct interpretations: "
            f"{intent.get('ambiguity_details', '')}\n\n"
            f"**Considered Interpretations:** " + ", ".join(intent.get("clarification_options", []))
        )

    # 2. EXECUTIVE METRIC SUMMARY DASHBOARD
    status_label = report.get("status", "COMPLETED")
    status_color = "#047857" if status_label == "COMPLETED" else ("#b45309" if status_label == "PARTIALLY_COMPLETED" else "#b91c1c")
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Run Status</div><div class="metric-card-value" style="color: {status_color}; font-size: 1.15rem;">{status_label}</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Confidence</div><div class="metric-card-value" style="color: #0f766e;">{report.get('confidence', 'MED').upper()}</div></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Sources Discovered</div><div class="metric-card-value">{metrics.get('candidates_discovered', 0)}</div></div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Pages Extracted</div><div class="metric-card-value">{metrics.get('sources_extracted', 0)}/{metrics.get('sources_found', 0)}</div></div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">BM25 Chunks</div><div class="metric-card-value">{metrics.get('chunks_selected', 0)}</div></div>""", unsafe_allow_html=True)
    with m6:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Total Duration</div><div class="metric-card-value">{metrics.get('total_duration_seconds', 0)}s</div></div>""", unsafe_allow_html=True)

    st.caption(f"**Confidence Heuristic Rationale:** {report.get('confidence_reason', 'Grounded in retrieved sources.')}")

    # 3. EXECUTIVE SUMMARY CARD
    st.markdown("### 📋 Executive Summary")
    with st.container(border=True):
        st.markdown(report.get("executive_summary") or report.get("short_answer") or "Summary not available.")

    # 4. KEY FINDINGS WITH VERIFIED EVIDENCE
    st.markdown("### 🔍 Key Findings & Grounded Evidence")
    findings = report.get("key_findings", [])
    if findings:
        for idx, f in enumerate(findings, 1):
            finding_text = f.get("finding", "")
            explanation = f.get("explanation", "")
            citations = f.get("citations", [])
            figures = f.get("metrics_or_figures", [])
            excerpts = f.get("verified_evidence_excerpts", [])

            citation_chips = "".join([f'<span class="citation-tag">[{c}]</span>' for c in citations])
            
            with st.container(border=True):
                st.markdown(f"**{idx}. {finding_text}** {citation_chips}", unsafe_allow_html=True)
                st.write(explanation)
                
                if figures:
                    st.caption("📊 **Key Figures / Metrics:** " + " • ".join(figures))

                # Expandable Verified Chunk Drawer
                if excerpts:
                    with st.expander(f"🔎 View {len(excerpts)} Verified Evidence Excerpts for Finding #{idx}", expanded=False):
                        for ex in excerpts:
                            st.markdown(f"**Source [{ex['source_id']}] ({ex['chunk_id']}):**")
                            st.info(f"\"{ex['excerpt']}\"")
                            st.caption(f"Original Reference: [{ex['url']}]({ex['url']})")
    else:
        st.info("No findings met the strict evidence validation requirements.")

    # 5. COMPARISON TABLE (If present)
    comp_table = report.get("comparison_table")
    if comp_table and comp_table.get("headers") and comp_table.get("rows"):
        st.markdown("### ⚖️ Comparative Analysis")
        with st.container(border=True):
            headers = comp_table["headers"]
            rows = comp_table["rows"]
            
            # Format markdown table
            header_line = "| " + " | ".join(headers) + " |"
            sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
            table_lines = [header_line, sep_line]
            
            for r in rows:
                row_vals = [str(r.get(h, "—")) for h in headers]
                table_lines.append("| " + " | ".join(row_vals) + " |")
                
            st.markdown("\n".join(table_lines))

    # 6. DETAILED ANALYSIS (Domain/Category specific)
    detailed = report.get("detailed_analysis")
    if detailed and detailed.get("subsections"):
        st.markdown(f"### 📑 {detailed.get('section_title', 'Detailed Analysis')}")
        with st.container(border=True):
            for sub in detailed.get("subsections", []):
                st.markdown(f"#### {sub.get('title', '')}")
                if sub.get("content"):
                    st.write(sub.get("content"))
                if sub.get("bullet_points"):
                    for bp in sub.get("bullet_points", []):
                        st.markdown(f"- {bp}")

    # 7. SOURCE EXPLORER
    st.markdown("### 🌐 Source Explorer & Authority Ledger")
    sources = report.get("sources_used", [])
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        st.caption(f"Retrieved and evaluated {len(sources)} unique domain sources:")
    with col_f2:
        source_filter = st.selectbox("Filter by Source Type", ["All Sources", "Official / Primary", "Reputable Media", "Academic / Research"], index=0)

    for s in sources:
        stype = s.get("source_type", "general_web")
        is_primary = s.get("is_primary_source", False)

        if source_filter == "Official / Primary" and not is_primary:
            continue
        elif source_filter == "Reputable Media" and "media" not in stype:
            continue
        elif source_filter == "Academic / Research" and "academic" not in stype:
            continue

        badge_class = "badge-official" if is_primary else ("badge-media" if "media" in stype else "badge-general")
        
        with st.container(border=True):
            c_s1, c_s2 = st.columns([4, 1])
            with c_s1:
                st.markdown(f"**[{s.get('source_id')}] [{s.get('title')}]({s.get('url')})**")
                st.markdown(
                    f"<span class='source-badge {badge_class}'>{stype.replace('_', ' ')}</span> &nbsp; "
                    f"**Domain:** `{s.get('domain')}` &nbsp;•&nbsp; "
                    f"**Extraction:** `{s.get('extraction_status')}` &nbsp;•&nbsp; "
                    f"**Authority Score:** `{s.get('authority_score', 0.5):.2f}`",
                    unsafe_allow_html=True
                )
                if s.get("reason_for_selection"):
                    st.caption(f"Reason: {s.get('reason_for_selection')}")
            with c_s2:
                st.link_button("Open Webpage ↗", s.get("url"), use_container_width=True)

    # 8. ASSUMPTIONS, LIMITATIONS & NEXT STEPS
    st.markdown("### 🛡️ Methodology, Limitations & Next Steps")
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        with st.container(border=True):
            st.markdown("**Assumptions**")
            for a in report.get("assumptions", []) or ["No explicit assumptions."]:
                st.markdown(f"- {a}")
    with col_l2:
        with st.container(border=True):
            st.markdown("**Limitations & Uncertainties**")
            lims = report.get("limitations", []) + report.get("uncertainties", [])
            for l in lims or ["None identified."]:
                st.markdown(f"- {l}")
    with col_l3:
        with st.container(border=True):
            st.markdown("**Suggested Next Steps**")
            for ns in report.get("suggested_next_steps", []) or ["No additional steps."]:
                st.markdown(f"- {ns}")

    # 9. EXPANDABLE DIAGNOSTICS & RAW DATA
    with st.expander("🛠️ Developer Diagnostics, Research Plan & Trace", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Research Plan", "Execution Trace", "Raw JSON Payload"])
        with tab1:
            st.json(plan)
        with tab2:
            st.json(result["trace"])
        with tab3:
            st.json(result)

    # 10. EXPORT REPORT
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        # Generate Markdown Report
        md_report = f"# Research Report: {report.get('user_question')}\n\n"
        md_report += f"**Execution Status:** {report.get('status')}\n"
        md_report += f"**Confidence:** {report.get('confidence', '').upper()} ({report.get('confidence_reason')})\n\n"
        md_report += f"## Executive Summary\n{report.get('executive_summary')}\n\n"
        md_report += "## Key Findings\n"
        for idx, f in enumerate(report.get("key_findings", []), 1):
            md_report += f"### {idx}. {f.get('finding')}\n"
            md_report += f"{f.get('explanation')}\n"
            if f.get("citations"):
                md_report += f"**Sources:** {', '.join(f.get('citations'))}\n\n"
        md_report += "## Sources Used\n"
        for s in report.get("sources_used", []):
            md_report += f"- **[{s.get('source_id')}] [{s.get('title')}]({s.get('url')})** ({s.get('source_type')})\n"
        
        st.download_button(
            "📥 Download Report (Markdown)",
            data=md_report,
            file_name="researchpilot_report.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col_dl2:
        st.download_button(
            "📦 Download Full Report (JSON)",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="researchpilot_report.json",
            mime="application/json",
            use_container_width=True
        )

st.markdown("---")
st.caption("ResearchPilot AI • Evidence-First Autonomous Research Assistant • Powered by Groq and Tavily")
