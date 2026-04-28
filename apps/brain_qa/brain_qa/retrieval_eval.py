"""
retrieval_eval.py — Sprint 25b Retrieval Eval Harness
==========================================================================

A/B ukur lift: BM25 vs Hybrid (BM25+Dense) vs Hybrid+Rerank.

Metric utama:
- **Hit@k** — apakah relevant chunk muncul di top-k hasil retrieval
- **MRR@k** — Mean Reciprocal Rank (1/rank chunk yang relevant)
- **Latency (ms)** — p50 dan p95 per retrieval method

Tidak butuh LLM call — murni ukur chunk retrieval quality.

Usage (CLI):
    python -m brain_qa retrieval_eval
    python -m brain_qa retrieval_eval --n 30 --k 5
    python -m brain_qa retrieval_eval --out .data/retrieval_eval_report.json

Usage (API):
    from brain_qa.retrieval_eval import run_retrieval_eval
    report = run_retrieval_eval(n_queries=50, k=5)

Query set design:
- Setiap query punya `relevant_keywords` — kata/frase yang HARUS muncul di
  top-k snippet kalau retrieval bagus. Proxy untuk ground truth relevance.
- Realistic mix: teknis (SIDIX infra), konseptual (AI agent), Islamic (tajwid,
  aqidah), umum (Tesla, AI safety), Indonesian casual.
- Sengaja mix bahasa (ID/EN) untuk test multilingual BGE-M3 vs BM25.

Sprint 25b (2026-04-28) — pivot aligned: note 248 SIDIX = creative AI agent,
eval grounded di domain real SIDIX corpus, no vendor API, MIT-compatible.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Query set (mix: teknis SIDIX, AI, Islam, umum, casual) ───────────────────

_EVAL_QUERIES: list[dict] = [
    # SIDIX infra / agent
    {"query": "SIDIX self-evolving agent", "keywords": ["SIDIX", "agent", "evolv"]},
    {"query": "cara kerja RAG corpus SIDIX", "keywords": ["corpus", "chunk", "rag"]},
    {"query": "persona UTZ ABOO OOMAR ALEY AYMAN", "keywords": ["persona", "UTZ", "ABOO", "OOMAR"]},
    {"query": "ReAct loop tools execution", "keywords": ["react", "tool", "agent"]},
    {"query": "SIDIX embedding BGE-M3", "keywords": ["embed", "bge", "semantic"]},
    {"query": "self-learning growth loop SIDIX", "keywords": ["growth", "train", "loop"]},
    {"query": "ODOA daily tracker self-aware", "keywords": ["odoa", "daily", "track"]},
    {"query": "KITABAH generate iterate", "keywords": ["kitab", "iter", "generat"]},
    {"query": "RASA aesthetic quality scorer", "keywords": ["rasa", "quality", "scor"]},
    {"query": "WAHDAH corpus signal LoRA retrain", "keywords": ["wahdah", "lora", "retrain"]},

    # AI / tech concepts
    {"query": "LLM generative model Qwen", "keywords": ["qwen", "llm", "generat"]},
    {"query": "LoRA fine-tuning adapter", "keywords": ["lora", "finetun", "adapter"]},
    {"query": "vLLM RunPod serverless inference", "keywords": ["runpod", "vllm", "infer"]},
    {"query": "knowledge graph semantic retrieval", "keywords": ["knowledge", "semantic", "retriev"]},
    {"query": "cosine similarity embedding search", "keywords": ["cosine", "embed", "search"]},
    {"query": "chain of thought reasoning", "keywords": ["chain", "thought", "reason"]},
    {"query": "BM25 lexical search ranking", "keywords": ["bm25", "lexical", "rank"]},
    {"query": "AI agent proactive autonomous", "keywords": ["agent", "proactiv", "autonom"]},
    {"query": "multimodal visual audio text", "keywords": ["modal", "visual", "audio"]},
    {"query": "sanad chain knowledge source", "keywords": ["sanad", "source", "chain"]},

    # Islamic knowledge
    {"query": "aqidah tauhid Islam", "keywords": ["aqidah", "tauhid", "islam"]},
    {"query": "tajwid hukum bacaan Quran", "keywords": ["tajwid", "quran", "bacaan"]},
    {"query": "maqasid syariah fiqh", "keywords": ["maqasid", "fiqh", "syariah"]},
    {"query": "hadith sahih perawi", "keywords": ["hadith", "perawi", "sahih"]},
    {"query": "shalat rukun wajib", "keywords": ["shalat", "rukun", "wajib"]},

    # Umum / konseptual
    {"query": "Tesla Edison kompetisi DC AC", "keywords": ["tesla", "edison", "listrik"]},
    {"query": "kreativitas desain inovasi produk", "keywords": ["kreatif", "desain", "inovas"]},
    {"query": "startup bisnis strategi pasar", "keywords": ["startup", "bisnis", "strategi"]},
    {"query": "machine learning data training", "keywords": ["machine", "data", "train"]},
    {"query": "Python FastAPI backend deployment", "keywords": ["python", "fastapi", "deploy"]},
]


@dataclass
class _QueryResult:
    query: str
    keywords: list[str]
    bm25_hit_k: bool = False
    bm25_mrr: float = 0.0
    bm25_ms: float = 0.0
    hybrid_hit_k: bool = False
    hybrid_mrr: float = 0.0
    hybrid_ms: float = 0.0
    rerank_hit_k: bool = False
    rerank_mrr: float = 0.0
    rerank_ms: float = 0.0
    bm25_available: bool = True
    hybrid_available: bool = True
    rerank_available: bool = True


@dataclass
class RetrievalEvalReport:
    n_queries: int
    k: int
    bm25_hit_rate: float = 0.0
    bm25_mrr: float = 0.0
    bm25_p50_ms: float = 0.0
    bm25_p95_ms: float = 0.0
    hybrid_hit_rate: float = 0.0
    hybrid_mrr: float = 0.0
    hybrid_p50_ms: float = 0.0
    hybrid_p95_ms: float = 0.0
    rerank_hit_rate: float = 0.0
    rerank_mrr: float = 0.0
    rerank_p50_ms: float = 0.0
    rerank_p95_ms: float = 0.0
    hybrid_vs_bm25_hit_delta: float = 0.0
    rerank_vs_bm25_hit_delta: float = 0.0
    hybrid_available: bool = False
    rerank_available: bool = False
    timestamp: str = ""
    per_query: list[dict] = field(default_factory=list)


def _keyword_hit(snippets: list[str], keywords: list[str]) -> bool:
    """Check if ANY of the keywords appears (case-insensitive) in ANY snippet."""
    combined = " ".join(s.lower() for s in snippets)
    return any(kw.lower() in combined for kw in keywords)


def _keyword_mrr(ranked_snippets: list[str], keywords: list[str], k: int) -> float:
    """MRR: 1/rank for first snippet that hits keyword, 0 if none in top-k."""
    for rank, snippet in enumerate(ranked_snippets[:k], start=1):
        if any(kw.lower() in snippet.lower() for kw in keywords):
            return 1.0 / rank
    return 0.0


def _pct(n: int, total: int) -> str:
    return f"{100*n//max(total,1)}%"


def run_retrieval_eval(
    *,
    index_dir_override: Optional[str] = None,
    n_queries: int = 30,
    k: int = 5,
    out: Optional[str] = None,
    embed_fn=None,
) -> RetrievalEvalReport:
    """Run A/B retrieval eval. Returns RetrievalEvalReport.

    Graceful: kalau dense index belum dibangun, hybrid_available=False dan
    hanya BM25 yang diukur.
    """
    from .paths import default_index_dir
    from .query import _load_chunks, _load_tokens
    from .text import tokenize
    from .sanad_ranking import apply_sanad_weight
    from .dense_index import load_dense_index, dense_search

    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()

    # Load BM25 index
    try:
        chunks = _load_chunks(index_dir)
        tokenized = _load_tokens(index_dir)
        if len(tokenized) != len(chunks):
            raise RuntimeError("Index corrupted: tokens != chunks")
    except Exception as e:
        log.error("[retrieval_eval] Failed to load BM25 index: %s", e)
        return RetrievalEvalReport(n_queries=0, k=k)

    # Load dense index if available
    dense_matrix = None
    loaded = load_dense_index(index_dir)
    if loaded is not None:
        dense_matrix, _ = loaded

    if embed_fn is None and dense_matrix is not None:
        try:
            from .embedding_loader import load_embed_fn
            embed_fn = load_embed_fn()
        except Exception:
            embed_fn = None

    hybrid_available = dense_matrix is not None and embed_fn is not None

    # Load reranker
    rerank_fn = None
    rerank_available = False
    if hybrid_available:
        try:
            from .reranker import load_rerank_fn
            rerank_fn = load_rerank_fn()
            rerank_available = rerank_fn is not None
        except Exception:
            pass

    queries = _EVAL_QUERIES[:n_queries]
    results: list[_QueryResult] = []

    from rank_bm25 import BM25Okapi  # type: ignore
    bm25 = BM25Okapi(tokenized)

    for qd in queries:
        q_text = qd["query"]
        keywords = qd["keywords"]
        r = _QueryResult(query=q_text, keywords=keywords)
        r.hybrid_available = hybrid_available
        r.rerank_available = rerank_available

        # ── BM25 path ──────────────────────────────────────────────────────
        t0 = time.perf_counter()
        q_tokens = tokenize(q_text)
        scores = bm25.get_scores(q_tokens)
        weighted = [apply_sanad_weight(chunks[i].sanad_tier, scores[i]) for i in range(len(scores))]
        bm25_ranked = sorted(range(len(weighted)), key=lambda i: -weighted[i])[:k]
        bm25_snippets = [chunks[i].text for i in bm25_ranked]
        r.bm25_ms = (time.perf_counter() - t0) * 1000

        r.bm25_hit_k = _keyword_hit(bm25_snippets, keywords)
        r.bm25_mrr = _keyword_mrr(bm25_snippets, keywords, k)

        # ── Hybrid path (BM25 + Dense via RRF) ────────────────────────────
        if hybrid_available:
            try:
                t0 = time.perf_counter()
                from .hybrid_search import hybrid_search
                fused = hybrid_search(
                    question=q_text,
                    tokens_per_chunk=tokenized,
                    q_tokens=q_tokens,
                    index_dir=index_dir,
                    top_k_each=20,
                    final_k=k * 2,
                    embed_fn=embed_fn,
                )
                # Apply sanad weight on fused
                candidate = [idx for idx, _s, _m in fused]
                sw = [(i, apply_sanad_weight(chunks[i].sanad_tier, 1.0)) for i in candidate]
                sw.sort(key=lambda x: -x[1])
                hybrid_ranked = [i for i, _ in sw[:k]]
                hybrid_snippets = [chunks[i].text for i in hybrid_ranked]
                r.hybrid_ms = (time.perf_counter() - t0) * 1000
                r.hybrid_hit_k = _keyword_hit(hybrid_snippets, keywords)
                r.hybrid_mrr = _keyword_mrr(hybrid_snippets, keywords, k)
            except Exception as e:
                log.warning("[retrieval_eval] hybrid failed for '%s': %s", q_text[:40], e)
                r.hybrid_available = False
        else:
            r.hybrid_hit_k = r.bm25_hit_k
            r.hybrid_mrr = r.bm25_mrr
            r.hybrid_ms = r.bm25_ms

        # ── Hybrid + Rerank path ────────────────────────────────────────────
        if rerank_available and hybrid_available:
            try:
                t0 = time.perf_counter()
                from .hybrid_search import hybrid_search as hs
                from .reranker import rerank_indices
                fused2 = hs(
                    question=q_text,
                    tokens_per_chunk=tokenized,
                    q_tokens=q_tokens,
                    index_dir=index_dir,
                    top_k_each=20,
                    final_k=20,
                    embed_fn=embed_fn,
                )
                cands = [idx for idx, _s, _m in fused2]
                reranked = rerank_indices(
                    query=q_text,
                    candidate_indices=cands,
                    chunks_text=[c.text for c in chunks],
                    rerank_fn=rerank_fn,
                    final_k=k,
                )
                rerank_snippets = [chunks[i].text for i, _ in reranked[:k]]
                r.rerank_ms = (time.perf_counter() - t0) * 1000
                r.rerank_hit_k = _keyword_hit(rerank_snippets, keywords)
                r.rerank_mrr = _keyword_mrr(rerank_snippets, keywords, k)
            except Exception as e:
                log.warning("[retrieval_eval] rerank failed for '%s': %s", q_text[:40], e)
                r.rerank_available = False
        else:
            r.rerank_hit_k = r.hybrid_hit_k
            r.rerank_mrr = r.hybrid_mrr
            r.rerank_ms = r.hybrid_ms

        results.append(r)

    # ── Aggregate ─────────────────────────────────────────────────────────────
    def _safe_median(vals):
        return statistics.median(vals) if vals else 0.0

    def _p95(vals):
        if not vals:
            return 0.0
        idx = int(len(vals) * 0.95)
        return sorted(vals)[min(idx, len(vals)-1)]

    bm25_hits = sum(1 for r in results if r.bm25_hit_k)
    hybrid_hits = sum(1 for r in results if r.hybrid_hit_k)
    rerank_hits = sum(1 for r in results if r.rerank_hit_k)
    n = len(results)

    report = RetrievalEvalReport(
        n_queries=n,
        k=k,
        bm25_hit_rate=bm25_hits / max(n, 1),
        bm25_mrr=statistics.mean(r.bm25_mrr for r in results) if results else 0,
        bm25_p50_ms=_safe_median([r.bm25_ms for r in results]),
        bm25_p95_ms=_p95([r.bm25_ms for r in results]),
        hybrid_hit_rate=hybrid_hits / max(n, 1),
        hybrid_mrr=statistics.mean(r.hybrid_mrr for r in results) if results else 0,
        hybrid_p50_ms=_safe_median([r.hybrid_ms for r in results]),
        hybrid_p95_ms=_p95([r.hybrid_ms for r in results]),
        rerank_hit_rate=rerank_hits / max(n, 1),
        rerank_mrr=statistics.mean(r.rerank_mrr for r in results) if results else 0,
        rerank_p50_ms=_safe_median([r.rerank_ms for r in results]),
        rerank_p95_ms=_p95([r.rerank_ms for r in results]),
        hybrid_vs_bm25_hit_delta=(hybrid_hits - bm25_hits) / max(n, 1),
        rerank_vs_bm25_hit_delta=(rerank_hits - bm25_hits) / max(n, 1),
        hybrid_available=hybrid_available,
        rerank_available=rerank_available,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        per_query=[asdict(r) for r in results],
    )

    # ── Print report ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"SIDIX Retrieval Eval — Sprint 25b")
    print(f"Queries: {n}  |  Hit@{k}  |  {report.timestamp}")
    print(f"{'='*60}")
    print(f"{'Method':<22} {'Hit@'+str(k):<10} {'MRR@'+str(k):<10} {'p50 ms':<10} {'p95 ms'}")
    print(f"{'-'*60}")
    print(f"{'BM25 (baseline)':<22} {report.bm25_hit_rate:<10.1%} {report.bm25_mrr:<10.3f} {report.bm25_p50_ms:<10.0f} {report.bm25_p95_ms:.0f}")
    if hybrid_available:
        delta_h = report.hybrid_vs_bm25_hit_delta
        print(f"{'Hybrid BM25+Dense':<22} {report.hybrid_hit_rate:<10.1%} {report.hybrid_mrr:<10.3f} {report.hybrid_p50_ms:<10.0f} {report.hybrid_p95_ms:.0f}  ({'+' if delta_h>=0 else ''}{delta_h:.1%})")
    else:
        print(f"{'Hybrid BM25+Dense':<22} N/A (dense index not built)")
    if rerank_available:
        delta_r = report.rerank_vs_bm25_hit_delta
        print(f"{'Hybrid+Rerank':<22} {report.rerank_hit_rate:<10.1%} {report.rerank_mrr:<10.3f} {report.rerank_p50_ms:<10.0f} {report.rerank_p95_ms:.0f}  ({'+' if delta_r>=0 else ''}{delta_r:.1%})")
    else:
        print(f"{'Hybrid+Rerank':<22} N/A (reranker not available)")
    print(f"{'='*60}")

    # ── Per-query miss analysis ────────────────────────────────────────────────
    bm25_misses = [r for r in results if not r.bm25_hit_k]
    hybrid_recover = [r for r in bm25_misses if r.hybrid_hit_k and r.hybrid_available]
    print(f"\nBM25 misses: {len(bm25_misses)}/{n}")
    if hybrid_recover:
        print(f"Hybrid recovered from BM25 miss: {len(hybrid_recover)}")
        for r in hybrid_recover[:5]:
            print(f"  + [{r.query}] keywords={r.keywords}")

    bm25_hits_set = [r for r in results if r.bm25_hit_k and not r.hybrid_hit_k and r.hybrid_available]
    if bm25_hits_set:
        print(f"\nBM25 hit but hybrid missed (regression check): {len(bm25_hits_set)}")
        for r in bm25_hits_set[:3]:
            print(f"  - [{r.query}]")

    # ── Write JSON output ─────────────────────────────────────────────────────
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nReport saved → {out}")

    return report


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def _cli():
    import argparse
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="SIDIX Retrieval Eval Harness (Sprint 25b)")
    p.add_argument("--n", type=int, default=30, help="Number of queries (max 30)")
    p.add_argument("--k", type=int, default=5, help="Hit@k (default 5)")
    p.add_argument("--out", default=None, help="Output JSON path")
    p.add_argument("--index-dir", default=None, help="Index dir override")
    args = p.parse_args()
    run_retrieval_eval(
        index_dir_override=args.index_dir,
        n_queries=min(args.n, len(_EVAL_QUERIES)),
        k=args.k,
        out=args.out,
    )


if __name__ == "__main__":
    _cli()


__all__ = ["run_retrieval_eval", "RetrievalEvalReport", "_EVAL_QUERIES"]
