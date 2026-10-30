from agents.planner import generate_heuristic_plan

def test_heuristic_plan_category_detection():
    # Technology comparison
    p1 = generate_heuristic_plan("Compare Qdrant vs Milvus vector databases for RAG")
    assert p1.intent.research_category == "technology_comparison"
    assert len(p1.search_queries) >= 3

    # Indian startup discovery
    p2 = generate_heuristic_plan("Find 5 Indian B2B SaaS startups in HR tech")
    assert p2.intent.research_category == "startup_discovery"
    assert p2.intent.geographic_scope == "India"

    # Company research
    p3 = generate_heuristic_plan("Research Databricks business model and revenue")
    assert p3.intent.research_category == "company"

def test_ambiguity_detection():
    # Short ambiguous query
    p = generate_heuristic_plan("Find the best businesses in India")
    assert p.intent.ambiguity_detected
    assert p.intent.working_assumptions

