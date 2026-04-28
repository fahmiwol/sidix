"""
reranker.py — Sprint 25 Sprint C Cross-Encoder Reranker
==========================================================================

Pasangan terakhir untuk pipeline retrieval:

    Query → Hybrid BM25+Dense (top-20) → Reranker (top-N) → LLM

Cross-encoder me-rerank lebih akurat daripada bi-encoder (dense alone) karena
melihat query+doc bersamaan dalam satu attention. Trade-off: lebih lambat
per pair (~10-30ms CPU per pair untuk MiniLM cross-encoder), tapi karena
hanya pada top-K (≤20 pairs) total overhead masih acceptable (~200-600ms).

Default model: `BAAI/bge-reranker-v2-m3` — multilingual (Indonesian friendly),
top tier MTEB. Fallback: `cross-encoder/ms-marco-MiniLM-L-6-v2` (English-leaning,
faster). Graceful disable kalau sentence-transformers tidak available.

Pivot alignment (CLAUDE.md 6.4):
- Note 248: foundation retrieval = compound win, reranker = quality jump terbesar
- 10 hard rules: own model, MIT-compatible (BAAI bge-reranker MIT, MS-MARCO Apache-2)
- Pivot 2026-04-25 LIBERATION: better grounding = less hallucination

Anti-pattern dihindari:
- ❌ Vendor API rerank (Cohere Rerank) → tetap self-hosted
- ❌ Heavy load di import → lazy
- ❌ Crash kalau dep missing → return None gracefully
- ❌ Rerank ALL chunks (O(N*latency)) → hanya top-K dari hybrid
"""

from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

RERANKER_MODELS = {
    "bge-reranker-v2-m3": {
        "hf_id": "BAAI/bge-reranker-v2-m3",
        "multilingual_id": True,
        "size_b": 0.5,
        "default": True,
    },
    "ms-marco-minilm": {
        "hf_id": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "multilingual_id": False,
        "size_b": 0.1,
        "default": False,
    },
}

_model_cache: dict[str, Any] = {}
_load_lock = Lock()
_active_model_name: Optional[str] = None


def _try_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder  # type: ignore
        return CrossEncoder
    except ImportError:
        log.debug("[reranker] sentence-transformers not installed")
        return None


def load_rerank_fn(model_name: Optional[str] = None) -> Optional[Callable[[str, list[str]], list[float]]]:
    """Load reranker callable(query, docs) -> list[float] (raw scores).

    Selection priority:
    1. Explicit `model_name` arg
    2. ENV `SIDIX_RERANK_MODEL`
    3. Auto: bge-reranker-v2-m3 → ms-marco-minilm fallback

    Returns None kalau semua gagal (graceful → caller skip rerank, pakai hybrid order).
    """
    global _active_model_name

    name = (model_name or os.environ.get("SIDIX_RERANK_MODEL", "")).lower().strip()
    if name and name in RERANKER_MODELS:
        candidates = [name]
    elif name:
        log.warning("[reranker] unknown model '%s', auto fallback", name)
        candidates = ["bge-reranker-v2-m3", "ms-marco-minilm"]
    else:
        candidates = ["bge-reranker-v2-m3", "ms-marco-minilm"]

    CE = _try_cross_encoder()
    if CE is None:
        log.warning("[reranker] CrossEncoder unavailable — skip rerank, fallback hybrid order")
        return None

    for candidate in candidates:
        spec = RERANKER_MODELS[candidate]
        with _load_lock:
            if candidate in _model_cache:
                model = _model_cache[candidate]
            else:
                try:
                    log.info("[reranker] loading %s (%s)...", candidate, spec["hf_id"])
                    model = CE(spec["hf_id"])
                    _model_cache[candidate] = model
                    log.info("[reranker] loaded %s OK", candidate)
                except Exception as e:
                    log.warning("[reranker] load %s failed: %s", candidate, e)
                    continue
        _active_model_name = candidate

        def rerank(query: str, docs: list[str], _m=model) -> list[float]:
            if not docs:
                return []
            pairs = [(query or "", d or "") for d in docs]
            try:
                scores = _m.predict(pairs, show_progress_bar=False)
            except Exception as e:
                log.warning("[reranker] predict failed: %s", e)
                return [0.0] * len(docs)
            return [float(s) for s in scores]

        return rerank

    log.warning("[reranker] no reranker loaded — caller will skip rerank step")
    _active_model_name = None
    return None


def rerank_indices(
    *,
    query: str,
    candidate_indices: list[int],
    chunks_text: list[str],
    rerank_fn: Optional[Callable[[str, list[str]], list[float]]] = None,
    final_k: Optional[int] = None,
) -> list[tuple[int, float]]:
    """Rerank candidate chunk indices given query. Return list[(idx, rerank_score)] desc.

    `chunks_text[i]` adalah teks dari chunk index i (caller-provided lookup).
    Kalau `rerank_fn=None` → load default. Kalau load gagal → return original order
    dengan score 0.0 (fallback safe).
    """
    if not candidate_indices:
        return []
    if rerank_fn is None:
        rerank_fn = load_rerank_fn()
    if rerank_fn is None:
        return [(int(i), 0.0) for i in candidate_indices]

    docs = [chunks_text[i] if 0 <= i < len(chunks_text) else "" for i in candidate_indices]
    scores = rerank_fn(query, docs)
    if len(scores) != len(candidate_indices):
        log.warning("[reranker] score len mismatch, fallback original order")
        return [(int(i), 0.0) for i in candidate_indices]
    paired = sorted(
        zip(candidate_indices, scores),
        key=lambda kv: -kv[1],
    )
    if final_k is not None and final_k > 0:
        paired = paired[:final_k]
    return [(int(i), float(s)) for i, s in paired]


def is_enabled_via_env() -> bool:
    """Default OFF; ON via ENV `SIDIX_RERANK=1`."""
    return os.environ.get("SIDIX_RERANK", "").strip().lower() in ("1", "true", "on", "yes")


def get_active_model() -> Optional[str]:
    return _active_model_name


__all__ = [
    "load_rerank_fn",
    "rerank_indices",
    "is_enabled_via_env",
    "get_active_model",
    "RERANKER_MODELS",
]
