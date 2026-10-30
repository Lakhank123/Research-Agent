import datetime
import logging
import re
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from tavily import TavilyClient
from core.schemas import SourceRecord

logger = logging.getLogger(__name__)

class SearchError(RuntimeError):
    pass

# Known authoritative domain registries
GOV_EDU_PATTERNS = [r"\.gov(\.[a-z]{2})?$", r"\.edu(\.[a-z]{2})?$", r"\.ac\.[a-z]{2}$", r"\.org$"]

AUTHORITY_TIERS = {
    # Tier 1: Primary documentation, code, academia, regulatory (0.85 - 0.95)
    "high": {
        "domains": [
            "github.com", "arxiv.org", "nature.com", "sciencedirect.com", "ieee.org",
            "sec.gov", "sebi.gov.in", "rbi.org.in", "who.int", "worldbank.org",
            "docs.python.org", "cloud.google.com", "aws.amazon.com", "learn.microsoft.com",
            "postgresql.org", "redis.io", "qdrant.tech", "weaviate.io", "milvus.io", "pinecone.io"
        ],
        "score": 0.90,
        "type": "official_documentation"
    },
    # Tier 2: Reputable financial, technology & business journalism (0.70 - 0.82)
    "medium": {
        "domains": [
            "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "economictimes.indiatimes.com",
            "livemint.com", "thehindubusinessline.com", "techcrunch.com", "venturebeat.com",
            "wired.com", "theverge.com", "technologyreview.com", "forbes.com", "cnbc.com",
            "hbr.org", "mckinsey.com", "gartner.com", "statista.com", "crunchbase.com", "inc42.com", "yourstory.com"
        ],
        "score": 0.78,
        "type": "reputable_media"
    },
    # Tier 3: Known low-authority or content-farm platforms (0.30 - 0.45)
    "low": {
        "domains": [
            "medium.com", "substack.com", "quora.com", "reddit.com", "pinterest.com",
            "linkedin.com", "facebook.com", "twitter.com", "x.com", "instagram.com"
        ],
        "score": 0.40,
        "type": "secondary_media"
    }
}

def normalize_url(raw_url: str) -> str:
    """Canonicalize URLs by stripping query trackers (utm, ref) and fragments."""
    try:
        parsed = urlparse((raw_url or "").strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        
        # Remove tracking parameters
        query_dict = parse_qs(parsed.query)
        clean_params = {
            k: v for k, v in query_dict.items()
            if not k.lower().startswith("utm_") and k.lower() not in ("ref", "fbclid", "gclid", "source")
        }
        clean_query = urlencode(clean_params, doseq=True)
        return urlunparse((scheme, netloc, path, "", clean_query, ""))
    except Exception:
        return (raw_url or "").strip()

def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        return parsed.netloc.lower().removeprefix("www.")
    except Exception:
        return ""

def classify_source_authority(url: str, title: str, domain: str) -> tuple[str, float, bool]:
    """Determine source category, authority score, and primary/secondary status."""
    dom_lower = domain.lower()
    
    # Check Government / Educational TLDs
    for pattern in GOV_EDU_PATTERNS:
        if re.search(pattern, dom_lower):
            if ".gov" in dom_lower:
                return "regulatory_or_government", 0.95, True
            return "academic_or_research", 0.92, True

    # Check Tier 1
    for high_d in AUTHORITY_TIERS["high"]["domains"]:
        if high_d in dom_lower:
            stype = "official_documentation" if ("docs." in dom_lower or "github" in dom_lower or "cloud" in dom_lower) else "academic_or_research"
            return stype, 0.88, True

    # Check Tier 2
    for med_d in AUTHORITY_TIERS["medium"]["domains"]:
        if med_d in dom_lower:
            return "reputable_media", 0.78, False

    # Check Tier 3
    for low_d in AUTHORITY_TIERS["low"]["domains"]:
        if low_d in dom_lower:
            return "secondary_media", 0.40, False

    # Check title cues for official status
    title_lower = title.lower()
    if any(k in title_lower for k in ["official documentation", "official website", "whitepaper", "annual report"]):
        return "official_documentation", 0.82, True

    return "general_web", 0.55, False

def extract_published_date(raw_item: dict) -> tuple[str, float]:
    """Extract or infer publication date and calculate freshness score."""
    published_date = raw_item.get("published_date") or raw_item.get("date") or ""
    freshness_score = 0.5
    
    current_year = datetime.datetime.now().year
    
    if published_date:
        # Check if year is present
        year_match = re.search(r"\b(201\d|202\d)\b", str(published_date))
        if year_match:
            year = int(year_match.group(1))
            if year >= current_year - 1:
                freshness_score = 0.95
            elif year >= current_year - 3:
                freshness_score = 0.80
            else:
                freshness_score = 0.50
        return str(published_date)[:20], freshness_score

    # Check URL and snippet for year hints
    text_corpus = f"{raw_item.get('url', '')} {raw_item.get('title', '')} {raw_item.get('content', '')}"
    year_match = re.search(r"\b(202[4-6])\b", text_corpus)
    if year_match:
        return f"{year_match.group(1)} (inferred)", 0.85

    return "", freshness_score

def compute_relevance_score(query: str, title: str, snippet: str, base_score: float) -> float:
    """Compute lexical and topical relevance of candidate result to the query."""
    q_words = set(re.findall(r"\b[a-z0-9]{3,}\b", query.lower()))
    if not q_words:
        return round(float(base_score or 0.5), 3)

    target_words = set(re.findall(r"\b[a-z0-9]{3,}\b", f"{title} {snippet}".lower()))
    overlap = len(q_words & target_words) / max(1, len(q_words))
    
    # Title match bonus
    title_words = set(re.findall(r"\b[a-z0-9]{3,}\b", title.lower()))
    title_overlap = len(q_words & title_words) / max(1, len(q_words))
    
    score = 0.4 * overlap + 0.3 * title_overlap + 0.3 * min(1.0, float(base_score or 0.5))
    return round(score, 3)

class TavilySearchTool:
    def __init__(self, api_key: str):
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise SearchError("TAVILY_API_KEY is missing. Configure it in your .env file.")
        self.client = TavilyClient(api_key=clean_key)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            clamped = max(1, min(int(max_results), 20))
            result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=clamped,
                include_answer=False,
                include_raw_content=False,
            )
            return result.get("results", [])
        except Exception as exc:
            raise SearchError(f"Search failed for query '{query}': {exc}") from exc

def rank_and_filter_sources(
    candidate_results: list[dict],
    main_question: str,
    target_count: int = 8,
    max_per_domain: int = 2,
) -> list[SourceRecord]:
    """
    Transparently score, rank, deduplicate and balance candidate sources.
    Enforces domain diversity, prioritizes primary/authoritative sources.
    """
    retrieved_today = datetime.datetime.now().strftime("%Y-%m-%d")
    scored_candidates = []
    seen_canonical_urls = set()

    for item in candidate_results:
        raw_url = item.get("url") or ""
        norm_url = normalize_url(raw_url)
        if not norm_url or norm_url in seen_canonical_urls:
            continue
        seen_canonical_urls.add(norm_url)

        domain = extract_domain(norm_url)
        title = (item.get("title") or domain or norm_url).strip()
        snippet = (item.get("content") or item.get("snippet") or "").strip()
        query_context = item.get("_query", main_question)

        # 1. Authority classification
        source_type, authority_score, is_primary = classify_source_authority(norm_url, title, domain)

        # 2. Freshness
        pub_date, freshness_score = extract_published_date(item)

        # 3. Relevance
        rel_score = compute_relevance_score(query_context, title, snippet, item.get("score", 0.5))

        # 4. Composite Quality Score: 45% Relevance + 35% Authority + 20% Freshness
        composite = round(0.45 * rel_score + 0.35 * authority_score + 0.20 * freshness_score, 3)

        # Selection reason rationale
        reasons = []
        if is_primary:
            reasons.append("Primary/authoritative documentation")
        if authority_score >= 0.75:
            reasons.append(f"Reputable {source_type.replace('_', ' ')}")
        if rel_score >= 0.65:
            reasons.append("High contextual query relevance")
        if not reasons:
            reasons.append("Topical web reference")
        reason_str = "; ".join(reasons)

        record = SourceRecord(
            source_id="",  # Assigned after ranking
            title=title,
            url=norm_url,
            domain=domain,
            publisher=domain.split(".")[0].capitalize() if domain else "",
            published_date=pub_date,
            retrieved_date=retrieved_today,
            source_type=source_type,
            is_primary_source=is_primary,
            authority_score=authority_score,
            freshness_score=freshness_score,
            relevance_score=rel_score,
            composite_score=composite,
            snippet=snippet,
            extracted=False,
            extraction_status="not_attempted",
            reason_for_selection=reason_str,
        )
        scored_candidates.append(record)

    # Sort descending by composite score
    scored_candidates.sort(key=lambda s: s.composite_score, reverse=True)

    # Enforce domain diversity while building the final set
    final_sources: list[SourceRecord] = []
    domain_counts: dict[str, int] = {}

    for cand in scored_candidates:
        if len(final_sources) >= target_count:
            break
        d = cand.domain
        if domain_counts.get(d, 0) >= max_per_domain:
            continue
        domain_counts[d] = domain_counts.get(d, 0) + 1
        cand.source_id = f"S{len(final_sources)+1}"
        final_sources.append(cand)

    # Only backfill if we have critically few sources total (< 2)
    if len(final_sources) < min(2, len(scored_candidates)):
        for cand in scored_candidates:
            if len(final_sources) >= target_count:
                break
            if cand not in final_sources:
                cand.source_id = f"S{len(final_sources)+1}"
                final_sources.append(cand)

    return final_sources
