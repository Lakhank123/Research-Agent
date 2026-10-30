import pytest
from tools.page_reader import PageReader
from orchestrator import ResearchOrchestrator

def test_page_reader_ssrf_blocking():
    reader = PageReader()
    blocked_urls = [
        "http://localhost:8000",
        "http://127.0.0.1/admin",
        "http://192.168.1.1/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "ftp://example.com/file",
        "",
        "not_a_url",
    ]
    for url in blocked_urls:
        text, status, meta = reader.fetch(url)
        assert text == ""
        assert status == "blocked_or_invalid_url"

def test_empty_search_results_produces_failed_status():
    settings = {
        "groq_api_key": "dummy_key",
        "tavily_api_key": "dummy_key",
        "max_search_queries": 2,
        "max_sources": 3,
        "max_chunks_in_context": 5,
        "timeout": 5,
    }

    class MockEmptySearch:
        def search(self, query, max_results=5):
            return []

    orchestrator = ResearchOrchestrator(
        settings=settings,
        llm=None,
        search_tool=MockEmptySearch(),
        page_reader=PageReader()
    )

    result = orchestrator.run("Obscure question with zero web results")
    report = result["report"]
    assert report["status"] == "FAILED"
    assert report["confidence"] == "low"
    assert len(report["key_findings"]) == 0
    assert "No web sources could be discovered" in report["executive_summary"]
