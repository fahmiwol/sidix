"""
hybrid_search.py — Sprint 25 Sprint B Hybrid BM25 + Dense via RRF
==========================================================================

Companion untuk `query.py`. Menggabungkan:
- BM25 lexical (existing, rank_bm25.BM25Okapi via tokens)
- Dense embedding (BGE-M3, via `dense_index.dense_search`)

Fusion strategy: **Reciprocal Rank Fusion (RRF)** — robust, no need for
score normalization, handles different score distributions:

    rrf_score(doc) = sum over methods of 1 / (k + rank_in_method)

Default k=60 (industry standard, paper Cormack 2009).

Pivot alignment (CLAUDE.md 6.4):
- Note 248: foundation retrieval = compound win → semua hilir improve
- 10 hard rules: own model, no vendor, MIT-compatible ✓
- Pivot 2026-04-25: tool-aggressive, less halu via better grounded chunks ✓

Behavior matrix:
- Kalau dense matrix tidak ada / embed_fn None → fallback BM25 only
- Kalau BM25 tokens tidak ada → fallback dense only
- Kalau dua-duanya available → RRF fusion
- Kalau dua-duanya tidak ada → return empty (caller handle)

Sanad weight tetap di-apply DI ATAS hybrid score (sebagaimana existing query.py),
biar separation of concerns: hybrid_search = relevance, sanad = trust tier.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

RRF_K = 60  # paper Cormack 2009 default


def _bm25_top(tokens_per_chunk: list[list[str]], q_tokens: list[str], top_k: int) -> list[tuple[int, float]]:
    """Return list[(idx, bm25_score)] sorted desc, len ≤ top_k."""
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        log.warning("[hybrid_search] rank_bm25 not installed")
        return []
    if not tokens_per_chunk or not q_tokens:
        return []
    bm25 = BM25Okapi(tokens_per_chunk)
    scores = bm25.get_scores(q_tokens)
    # Sort desc
    idx = sorted(range(len(scores)), key=lambda i: -scores[i])
    out: list[tuple[int, float]] = []
    for i in idx[: max(1, top_k)]:
        if scores[i] > 0:
            out.append((int(i), float(scores[i])))
    # If all zero, still return top_k (some queries match nothing literally)
    if not out:
        out = [(int(i), 0.0) for i in idx[: max(1, top_k)]]
    return out


def _rrf_fuse(
    rankings: list[list[tuple[int, float]]],
    *,
    k: int = RRF_K,
) -> dict[int, float]:
    """RRF fusion across multiple ranked lists. Returns dict[idx → fused_score]."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, (chunk_idx, _score) in enumerate(ranking, start=1):
            fused[chunk_idx] = fused.get(chunk_idx, 0.0) + (1.0 / (k + rank))
    return fused


def hybrid_search(
    *,
    question: str,
    tokens_per_chunk: list[list[str]],
    q_tokens: list[str],
    index_dir: Path,
    top_k_each: int = 20,
    final_k: int = 10,
    embed_fn: Optional[Callable[[str], Any]] = None,
) -> list[tuple[int, float, dict]]:
    """Hybrid retrieval. Returns list[(chunk_idx, fused_rrf_score, debug_meta)] desc.

    debug_meta = {"bm25_rank": int|None, "dense_rank": int|None,
                  "bm25_score": float|None, "dense_score": float|None}.
    Useful for observability / regression debug.

    Caller responsibility: apply sanad weight on top of fused score, then
    truncate to final desired k.
    """
    from .dense_index import load_dense_index, dense_search

    bm25_top = _bm25_top(tokens_per_chunk, q_tokens, top_k=top_k_each)

    dense_top: list[tuple[int, float]] = []
    loaded = load_dense_index(index_dir)
    if loaded is not None:
        matrix, _meta = loaded
        dense_top = dense_search(question, matrix, embed_fn=embed_fn, top_k=top_k_each)
    else:
        log.debug("[hybrid_search] dense index not found at %s, BM25-only path", index_dir)

    rankings: list[list[tuple[int, float]]] = []
    if bm25_top:
        rankings.append(bm25_top)
    if dense_top:
        rankings.append(dense_top)

    if not rankings:
        return []

    fused = _rrf_fuse(rankings)

    # Debug meta per chunk
    bm25_rank_map = {idx: r for r, (idx, _) in enumerate(bm25_top, start=1)}
    bm25_score_map = {idx: s for idx, s in bm25_top}
    dense_rank_map = {idx: r for r, (idx, _) in enumerate(dense_top, start=1)}
    dense_score_map = {idx: s for idx, s in dense_top}

    sorted_idx = sorted(fused.items(), key=lambda kv: -kv[1])
    out: list[tuple[int, float, dict]] = []
    for chunk_idx, fused_score in sorted_idx[: max(1, final_k)]:
        out.append((
            chunk_idx,
            fused_score,
            {
                "bm25_rank": bm25_rank_map.get(chunk_idx),
                "bm25_score": bm25_score_map.get(chunk_idx),
                "dense_rank": dense_rank_map.get(chunk_idx),
                "dense_score": dense_score_map.get(chunk_idx),
                "method": (
                    "hybrid" if (bm25_top and dense_top)
                    else ("bm25_only" if bm25_top else "dense_only")
                ),
            },
        ))
    return out


__all__ = ["hybrid_search", "RRF_K"]
