from core.evidence import verify_and_ground_citations
from core.retrieval import EvidenceLedger
from core.schemas import SourceRecord, EvidenceChunk, Finding, ResearchReport

def test_grounding_and_invalid_citations_removal():
    s1 = SourceRecord(source_id="S1", title="Official Vector Docs", url="https://example.com/docs")
    chunk1 = EvidenceChunk(chunk_id="S1-C1", source_id="S1", title="Docs", url="https://example.com/docs", text="Qdrant supports HNSW indexing with payload filters.")
    ledger = EvidenceLedger([chunk1], [s1])

    report = {
        "key_findings": [
            {
                "finding": "Qdrant utilizes HNSW indexing",
                "explanation": "Supported by documentation",
                "citations": ["S1", "S99"]
            }
        ],
        "sources_used": [{"source_id": "S1"}, {"source_id": "S99"}],
    }

    grounded = verify_and_ground_citations(report, ledger, {"S1"})
    
    # Valid source S1 remains; invalid S99 removed
    f0 = grounded["key_findings"][0]
    assert f0["citations"] == ["S1"]
    assert len(f0["verified_evidence_excerpts"]) == 1
    assert "HNSW indexing" in f0["verified_evidence_excerpts"][0]["excerpt"]
    assert [s["source_id"] for s in grounded["sources_used"]] == ["S1"]
    assert any("Removed 1 unverified citation" in lim for lim in grounded["limitations"])
