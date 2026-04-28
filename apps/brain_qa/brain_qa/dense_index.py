"""
dense_index.py — Sprint 25 Dense Embedding Index untuk RAG Chunk Retrieval
==========================================================================

Companion baru untuk `indexer.py` (BM25) dan `query.py` (BM25 search).
Sprint 25 (2026-04-28) — Sprint B Hybrid Retrieval foundation.

Goal: tiap chunk corpus juga punya BGE-M3 embedding (default) yang di-persist
sebagai numpy float32 matrix. Query time dot-product = cosine similarity
(asumsi L2-normalized). Hybrid scoring di `hybrid_search.py` merge BM25 + dense
via RRF.

Pivot alignment (CLAUDE.md 6.4 Pre-Exec Check):
- Note 248: SIDIX = AI Agent yang tumbuh, retrieval foundation = compound win
- Pivot 2026-04-25 LIBERATION: tool-aggressive — better retrieval = less halu
- 10 hard rules: own model (BGE-M3 self-hosted via sentence-transformers) ✓
  no vendor API ✓ MIT-compatible ✓
- Re-use `embedding_loader.py` (Vol 20c) — DRY, BGE-M3 default sudah ada

Anti-pattern dihindari:
- ❌ Force build dense saat embedding_loader tidak available → graceful skip,
  fallback BM25 only
- ❌ Heavy load di import time → lazy
- ❌ Duplicate embedding model load → reuse global singleton dari Vol 20c
- ❌ Vendor API (OpenAI text-embedding) → tetap self-hosted

File output:
- `<index_dir>/embeddings.npy` — float32 (N, D) L2-normalized
- `<index_dir>/dense_meta.json` — model_name, dim, chunk_count, hf_id

Reference: research note 233 BGE-M3 default + note 248 LOCK.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

DENSE_FILENAME = "embeddings.npy"
DENSE_META = "dense_meta.json"


def _try_numpy():
    try:
        import numpy as np  # type: ignore
        return np
    except ImportError:
        return None


def build_dense_index(
    chunks: list[Any],
    *,
    out_dir: Path,
    embed_fn: Optional[Callable[[str], Any]] = None,
    model_name: Optional[str] = None,
    batch_log_every: int = 200,
) -> bool:
    """Build dense embedding index untuk list[Chunk]. Return True kalau sukses.

    Graceful: kalau embed_fn=None coba load via `embedding_loader.load_embed_fn()`.
    Kalau masih None → return False, fallback caller tetap pakai BM25 only.
    """
    np = _try_numpy()
    if np is None:
        log.warning("[dense_index] numpy not available, skip dense build")
        return False

    if embed_fn is None:
        try:
            from .embedding_loader import load_embed_fn, get_active_model_info
            embed_fn = load_embed_fn(model_name)
            info = get_active_model_info()
            if embed_fn is None:
                log.warning("[dense_index] no embed_fn available — skip dense build")
                return False
            model_name = info.get("model") or "unknown"
            dim_hint = info.get("dim") or 0
        except Exception as e:
            log.warning("[dense_index] embedding_loader unavailable: %s", e)
            return False
    else:
        dim_hint = 0
        model_name = model_name or "external"

    if not chunks:
        log.warning("[dense_index] no chunks to index")
        return False

    vectors = []
    expected_dim: Optional[int] = None
    for i, c in enumerate(chunks):
        text = getattr(c, "text", "") or ""
        try:
            v = embed_fn(text)
        except Exception as e:
            log.warning("[dense_index] embed failed at chunk %d: %s", i, e)
            return False
        if v is None:
            log.warning("[dense_index] embed returned None at chunk %d", i)
            return False
        v = np.asarray(v, dtype=np.float32).reshape(-1)
        if expected_dim is None:
            expected_dim = int(v.shape[0])
        elif v.shape[0] != expected_dim:
            log.warning(
                "[dense_index] dim mismatch at %d: got %d expected %d",
                i, v.shape[0], expected_dim,
            )
            return False
        # Defensive L2 normalize (embedding_loader sudah normalize, but cheap insurance)
        norm = float(np.linalg.norm(v))
        if norm > 0:
            v = (v / norm).astype(np.float32)
        vectors.append(v)
        if (i + 1) % batch_log_every == 0:
            log.info("[dense_index] embedded %d/%d chunks", i + 1, len(chunks))

    matrix = np.vstack(vectors).astype(np.float32)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / DENSE_FILENAME, matrix, allow_pickle=False)
    meta = {
        "version": 1,
        "model_name": model_name,
        "dim": int(expected_dim or 0),
        "chunk_count": int(matrix.shape[0]),
    }
    (out_dir / DENSE_META).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(
        "[dense_index] built %d vectors dim=%d model=%s → %s",
        matrix.shape[0], expected_dim, model_name, out_dir / DENSE_FILENAME,
    )
    return True


def load_dense_index(index_dir: Path) -> Optional[tuple[Any, dict]]:
    """Return (matrix, meta) atau None kalau belum di-build / unreadable."""
    np = _try_numpy()
    if np is None:
        return None
    p = Path(index_dir) / DENSE_FILENAME
    m = Path(index_dir) / DENSE_META
    if not p.exists() or not m.exists():
        return None
    try:
        matrix = np.load(p, allow_pickle=False)
        meta = json.loads(m.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("[dense_index] load failed: %s", e)
        return None
    return matrix, meta


def dense_search(
    query_text: str,
    matrix: Any,
    *,
    embed_fn: Optional[Callable[[str], Any]] = None,
    top_k: int = 20,
) -> list[tuple[int, float]]:
    """Return list[(chunk_idx, cosine_score)] sorted desc by score, len ≤ top_k.

    Cosine = dot product (assumes both query and matrix L2-normalized).
    Empty list kalau embed_fn None / numpy unavailable / matrix empty.
    """
    np = _try_numpy()
    if np is None or matrix is None or matrix.shape[0] == 0:
        return []
    if embed_fn is None:
        try:
            from .embedding_loader import load_embed_fn
            embed_fn = load_embed_fn()
        except Exception:
            return []
    if embed_fn is None:
        return []
    try:
        q = embed_fn(query_text or "")
    except Exception as e:
        log.warning("[dense_index] query embed failed: %s", e)
        return []
    q = np.asarray(q, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(q))
    if norm > 0:
        q = (q / norm).astype(np.float32)
    if q.shape[0] != matrix.shape[1]:
        log.warning(
            "[dense_index] query dim %d != index dim %d, abort",
            q.shape[0], matrix.shape[1],
        )
        return []
    scores = matrix @ q  # (N,)
    k = min(int(top_k), int(scores.shape[0]))
    if k <= 0:
        return []
    # argpartition for top-k, then sort that subset
    idx = np.argpartition(-scores, k - 1)[:k]
    idx_sorted = idx[np.argsort(-scores[idx])]
    return [(int(i), float(scores[i])) for i in idx_sorted]


def is_enabled_via_env() -> bool:
    """Sprint 25 gating flag. Default OFF until corpus dense index built + tested."""
    return os.environ.get("SIDIX_HYBRID_RETRIEVAL", "").strip().lower() in ("1", "true", "on", "yes")


__all__ = [
    "build_dense_index",
    "load_dense_index",
    "dense_search",
    "is_enabled_via_env",
    "DENSE_FILENAME",
    "DENSE_META",
]
