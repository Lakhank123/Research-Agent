import math
import re
from collections import Counter
from typing import Optional
from core.schemas import EvidenceChunk, SourceRecord

# Standard BM25 hyperparameters
BM25_K1 = 1.5
BM25_B = 0.75

def tokenize(text: str) -> list[str]:
    """Tokenize lowercase alphanumeric terms with length >= 2."""
    return re.findall(r"\b[a-z0-9_]{2,}\b", (text or "").lower())

def extract_metric_and_entity_tokens(text: str) -> set[str]:
    """Extract numbers, currency, percentages, and capitalized entity tokens."""
    tokens = set()
    # Metrics, numbers, percentages, currency
    metrics = re.findall(r"\b(?:\$|€|₹)?\d+(?:\.\d+)?%?(?:k|m|b|t|gb|mb|tb|ms|s)?\b", text.lower())
    tokens.update(m for m in metrics if len(m) >= 2)
    # Acronyms or technical words
    acronyms = re.findall(r"\b[A-Z0-9]{2,}\b", text)
    tokens.update(a.lower() for a in acronyms)
    return tokens

def chunk_text(
    text: str,
    source_id: str,
    title: str,
    url: str,
    chunk_chars: int = 1000,
    overlap: int = 150,
    min_chunk_len: int = 40,
    source_type: str = "general_web"
) -> list[EvidenceChunk]:
    """
    Split text into overlapping character windows while preserving paragraph integrity.
    """
    clean = re.sub(r"[ \t]+", " ", text or "").strip()
    if not clean:
        return []

    # If small single text snippet
    if len(clean) < chunk_chars:
        if len(clean) >= min_chunk_len:
            return [EvidenceChunk(
                chunk_id=f"{source_id}-C1",
                source_id=source_id,
                title=title or url,
                url=url,
                text=clean,
                source_type=source_type
            )]
        return []

    chunks = []
    paragraphs = clean.split("\n\n")
    current_piece = []
    current_len = 0
    c_index = 1

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        # If adding paragraph exceeds chunk_chars, emit current chunk
        if current_len + len(para_clean) > chunk_chars and current_piece:
            piece_text = "\n\n".join(current_piece).strip()
            if len(piece_text) >= min_chunk_len:
                chunks.append(EvidenceChunk(
                    chunk_id=f"{source_id}-C{c_index}",
                    source_id=source_id,
                    title=title or url,
                    url=url,
                    text=piece_text,
                    source_type=source_type
                ))
                c_index += 1

            # Retain overlap from end of previous piece
            last_para = current_piece[-1]
            if len(last_para) < chunk_chars // 2:
                current_piece = [last_para, para_clean]
                current_len = len(last_para) + len(para_clean) + 2
            else:
                current_piece = [para_clean]
                current_len = len(para_clean)
        else:
            current_piece.append(para_clean)
            current_len += len(para_clean) + 2

    # Emit trailing piece
    if current_piece:
        piece_text = "\n\n".join(current_piece).strip()
        if len(piece_text) >= min_chunk_len:
            chunks.append(EvidenceChunk(
                chunk_id=f"{source_id}-C{c_index}",
                source_id=source_id,
                title=title or url,
                url=url,
                text=piece_text,
                source_type=source_type
            ))

    return chunks

class BM25Retriever:
    """Okapi BM25 implementation with entity boosting and subtask relevance scoring."""

    def __init__(self, chunks: list[EvidenceChunk]):
        self.chunks = chunks
        self.doc_count = len(chunks)
        self.doc_tokens = [tokenize(c.text) for c in chunks]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.doc_count)

        # Compute document frequencies
        self.df: dict[str, int] = Counter()
        for tokens in self.doc_tokens:
            for term in set(tokens):
                self.df[term] += 1

        # Compute IDF
        self.idf: dict[str, float] = {}
        for term, freq in self.df.items():
            # Standard Lucene/Okapi formula with +1 smoothing
            self.idf[term] = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0)

    def score_document(self, doc_idx: int, query_tokens: list[str], bonus_tokens: set[str]) -> float:
        """Compute BM25 score for a document index against a query."""
        if not query_tokens:
            return 0.0

        d_tokens = self.doc_tokens[doc_idx]
        d_len = self.doc_lengths[doc_idx]
        if d_len == 0:
            return 0.0

        tf_counts = Counter(d_tokens)
        score = 0.0

        for q in query_tokens:
            if q not in tf_counts:
                continue
            tf = tf_counts[q]
            idf = self.idf.get(q, 0.0)
            numerator = tf * (BM25_K1 + 1.0)
            denominator = tf + BM25_K1 * (1.0 - BM25_B + BM25_B * (d_len / max(1, self.avg_doc_len)))
            score += idf * (numerator / max(0.001, denominator))

        # Metric & Entity bonus (+15% per matched metric/entity up to 1.5x)
        entity_matches = sum(1 for b in bonus_tokens if b in tf_counts)
        if entity_matches > 0:
            multiplier = min(1.5, 1.0 + (entity_matches * 0.15))
            score *= multiplier

        return score

class EvidenceLedger:
    """Structured ledger of verified evidence chunks with subtask coverage."""

    def __init__(self, selected_chunks: list[EvidenceChunk], sources: list[SourceRecord]):
        self.chunks = selected_chunks
        self.sources = {s.source_id: s for s in sources}
        self.chunk_map = {c.chunk_id: c for c in selected_chunks}

    def get_chunk(self, chunk_id: str) -> Optional[EvidenceChunk]:
        return self.chunk_map.get(chunk_id)

    def get_source(self, source_id: str) -> Optional[SourceRecord]:
        return self.sources.get(source_id)

    def get_chunks_for_source(self, source_id: str) -> list[EvidenceChunk]:
        return [c for c in self.chunks if c.source_id == source_id]

    def subtask_coverage(self) -> dict[str, int]:
        coverage = Counter()
        for c in self.chunks:
            if c.subtask:
                coverage[c.subtask] += 1
        return dict(coverage)

def rank_and_build_evidence_ledger(
    chunks: list[EvidenceChunk],
    main_question: str,
    subtasks: list[str],
    entities: list[str],
    sources: list[SourceRecord],
    top_k: int = 14,
    max_chunks_per_source: int = 3
) -> EvidenceLedger:
    """
    Ranks chunks using BM25 across main query and individual research subtasks.
    Enforces source diversity so no single source monopolizes the context window.
    """
    if not chunks:
        return EvidenceLedger([], sources)

    retriever = BM25Retriever(chunks)
    
    # Query tokenization
    main_tokens = tokenize(main_question)
    bonus_tokens = extract_metric_and_entity_tokens(f"{main_question} {' '.join(entities)}")

    subtask_tokens_list = [tokenize(st) for st in subtasks]

    # Score each chunk
    scored_chunks: list[tuple[float, EvidenceChunk, str]] = []

    for idx, chunk in enumerate(chunks):
        # 1. Main query score
        q_score = retriever.score_document(idx, main_tokens, bonus_tokens)

        # 2. Subtask scores
        best_subtask = ""
        best_subtask_score = 0.0

        for st_idx, st_tokens in enumerate(subtask_tokens_list):
            st_score = retriever.score_document(idx, st_tokens, bonus_tokens)
            if st_score > best_subtask_score:
                best_subtask_score = st_score
                best_subtask = subtasks[st_idx]

        # Composite retrieval score: 65% Main Question + 35% Subtask Match
        final_score = round(0.65 * q_score + 0.35 * best_subtask_score, 4)
        chunk.score = final_score
        chunk.subtask = best_subtask or "General context"
        scored_chunks.append((final_score, chunk, best_subtask))

    # Sort descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # Enforce source diversity in final chunk selection
    selected_chunks: list[EvidenceChunk] = []
    source_counts: dict[str, int] = Counter()

    # Pass 1: pick top chunks respecting diversity cap
    for score, chunk, _ in scored_chunks:
        if len(selected_chunks) >= top_k:
            break
        if source_counts[chunk.source_id] >= max_chunks_per_source:
            continue
        source_counts[chunk.source_id] += 1
        selected_chunks.append(chunk)

    # Pass 2: if diversity cap left slots open, fill with remaining highest scoring
    if len(selected_chunks) < min(top_k, len(chunks)):
        for score, chunk, _ in scored_chunks:
            if len(selected_chunks) >= top_k:
                break
            if chunk not in selected_chunks:
                selected_chunks.append(chunk)

    return EvidenceLedger(selected_chunks, sources)
