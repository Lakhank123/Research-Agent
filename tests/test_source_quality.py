from tools.web_search import (
    normalize_url,
    classify_source_authority,
    rank_and_filter_sources
)

def test_url_normalization_removes_trackers():
    url = "https://example.com/page?utm_source=twitter&utm_medium=cpc&ref=homepage&id=123"
    clean = normalize_url(url)
    assert "utm_source" not in clean
    assert "utm_medium" not in clean
    assert "ref" not in clean
    assert "id=123" in clean

def test_classify_source_authority():
    # Regulatory / Gov
    stype, score, is_primary = classify_source_authority("https://rbi.org.in/circulars", "RBI Circular", "rbi.org.in")
    assert stype == "regulatory_or_government" or is_primary
    assert score >= 0.85

    # Tech Documentation / GitHub
    stype, score, is_primary = classify_source_authority("https://github.com/qdrant/qdrant", "Qdrant Repo", "github.com")
    assert is_primary
    assert score >= 0.85

    # Secondary media
    stype, score, is_primary = classify_source_authority("https://medium.com/some-post", "My Blog", "medium.com")
    assert not is_primary
    assert score <= 0.50

def test_rank_and_filter_domain_diversity():
    candidates = [
        {"url": f"https://domain-a.com/article-{i}", "title": f"Article {i}", "content": "Text", "score": 0.9}
        for i in range(5)
    ]
    candidates.append({"url": "https://domain-b.com/post", "title": "Other", "content": "Text", "score": 0.8})

    # max_per_domain = 2
    filtered = rank_and_filter_sources(candidates, "Test query", target_count=5, max_per_domain=2)
    a_count = sum(1 for s in filtered if "domain-a.com" in s.domain)
    assert a_count <= 2

