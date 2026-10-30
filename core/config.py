import os
from dotenv import load_dotenv

load_dotenv(override=True)

def _int_env(key: str, default: int) -> int:
    val = os.getenv(key, "")
    try:
        return int(val) if val.strip() else default
    except ValueError:
        return default

def get_settings():
    load_dotenv(override=True)
    return {
        "groq_api_key": os.getenv("GROQ_API_KEY", "").strip(),
        "groq_model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip() or "openai/gpt-oss-120b",
        "groq_fallback_model": os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b").strip() or "openai/gpt-oss-20b",
        "tavily_api_key": os.getenv("TAVILY_API_KEY", "").strip(),
        "max_search_queries": _int_env("MAX_SEARCH_QUERIES", 5),
        "max_sources": _int_env("MAX_SOURCES", 8),
        "max_chunks_in_context": _int_env("MAX_CHUNKS_IN_CONTEXT", 14),
        "timeout": _int_env("REQUEST_TIMEOUT_SECONDS", 15),
        "max_research_passes": _int_env("MAX_RESEARCH_PASSES", 2),
    }
