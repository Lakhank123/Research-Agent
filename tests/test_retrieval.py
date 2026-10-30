from core.retrieval import chunk_text, rank_and_build_evidence_ledger
from core.schemas import SourceRecord

def test_chunking_and_bm25_ranking():
    s1 = SourceRecord(source_id="S1", title="Vector DBs", url="https://example.com/vdb")
    s2 = SourceRecord(source_id="S2", title="General Web", url="https://example.com/other")

    text1 = "Vector databases provide high performance nearest-neighbor vector search for LLM RAG pipelines. " * 10
    text2 = "Baking artisan sourdough bread requires organic flour and hydration control. " * 10

    c1 = chunk_text(text1, "S1", "Vector DBs", "https://example.com/vdb")
    c2 = chunk_text(text2, "S2", "General Web", "https://example.com/other")

    assert c1
    assert c2

    ledger = rank_and_build_evidence_ledger(
        chunks=c1 + c2,
        main_question="What are the best vector databases for RAG pipelines?",
        subtasks=["Evaluate nearest-neighbor performance"],
        entities=["Vector", "RAG"],
        sources=[s1, s2],
        top_k=3
    )

    assert len(ledger.chunks) >= 1
    # Top chunk must be from S1 (vector db topic)
    assert ledger.chunks[0].source_id == "S1"
    assert ledger.chunks[0].score > 0
