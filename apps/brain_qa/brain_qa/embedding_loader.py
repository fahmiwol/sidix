"""
embedding_loader.py — 3-way Embedding Model Loader (Vol 20c)
==========================================================================

Companion untuk semantic_cache.py. Sekarang `embed_fn=None` (graceful
disable). Vol 20c wire ke startup: load embedding model + set ke
SemanticCache.

Strategy 3-way (decision matrix dari research note 235):

| Model               | Size  | Multilingual ID | Latency 4K | Notes                    |
|---------------------|-------|-----------------|------------|--------------------------|
| BGE-M3 @ 512 MRL    | ~0.5B | ✅ 100+ bahasa  | ~12ms CPU  | DEFAULT (safe pick)      |
| Codestral Mamba2 7B | 7B    | ✅ MTEB top     | constant   | Best quality, big VRAM   |
| Mamba2 1.3B         | 1.3B  | ✅              | constant   | Compromise               |
| MiniLM-L6-v2        | ~0.1B | ⚠️ weak         | ~3ms CPU   | Fastest, CPU-only fallback |

Selection logic:
1. ENV var `SIDIX_EMBED_MODEL` → explicit pick (paling tinggi prioritas)
2. Auto: try BGE-M3, fallback ke MiniLM kalau dependency missing
3. Graceful: return None kalau semua gagal → semantic cache stay dormant
   (Vol 20b safe behavior)

Reference:
- Research note 235 (game-changer Mamba2 finding)
- Research note 233 (BGE-M3 default rationale)
- HF: BAAI/bge-m3, sentence-transformers/all-MiniLM-L6-v2,
  dynatrace-oss/embed-mamba2

Anti-pattern dihindari:
- ❌ Vendor API (OpenAI text-embedding-3) — melanggar CLAUDE.md no-vendor
- ❌ Heavy load di import time — lazy load only when called
- ❌ Crash kalau dependency missing — return None, log warning
"""

from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


# ── Model registry ───────────────────────────────────────────────────────────

# Model name → (description, default for multilingual ID workload)
MODELS = {
    "bge-m3": {
        "hf_id": "BAAI/bge-m3",
        "dim_native": 1024,
        "dim_truncated": 512,  # MRL truncation
        "size_b": 0.5,
        "multilingual_id": True,
        "default": True,
    },
    "minilm": {
        "hf_id": "sentence-transformers/all-MiniLM-L6-v2",
        "dim_native": 384,
        "dim_truncated": 384,
        "size_b": 0.1,
        "multilingual_id": False,
        "default": False,  # CPU fallback only
    },
    "mamba2-1.3b": {
        # Confirmed via HF dynatrace-oss org page (2026-04-27 fetch)
        "hf_id": "dynatrace-oss/llama-embed-mamba2-1.3b",
        "dim_native": 2048,    # llama-1.3b standard hidden dim (verify on load)
        "dim_truncated": 2048,
        "size_b": 1.3,
        "multilingual_id": True,
        "default": False,
        "needs_trust_remote_code": True,
        "needs_extra_deps": ["kernels", "einops"],  # pip install
        "min_transformers_version": "5.5.0",
    },
    "mamba2-7b": {
        "hf_id": "dynatrace-oss/llama-embed-mamba2-7b",
        "dim_native": 4096,    # llama-7b standard hidden dim (verify on load)
        "dim_truncated": 1024,  # MRL truncate for cache key efficiency
        "size_b": 7.0,
        "multilingual_id": True,
        "default": False,
        "needs_trust_remote_code": True,
        "needs_extra_deps": ["kernels", "einops"],
        "min_transformers_version": "5.5.0",
    },
}


# ── Lazy loader registry ─────────────────────────────────────────────────────

_model_cache: dict[str, Any] = {}
_load_lock = Lock()
_active_model_name: Optional[str] = None


def _try_import_sentence_transformers():
    """Try import sentence-transformers. Return module or None."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        return SentenceTransformer
    except ImportError:
        log.debug("[embedding_loader] sentence-transformers not installed")
        return None


def _try_import_numpy():
    try:
        import numpy as np  # type: ignore
        return np
    except ImportError:
        log.warning("[embedding_loader] numpy not installed")
        return None


def _l2_normalize(vec):
    """L2-normalize numpy vector (in place safe)."""
    np = _try_import_numpy()
    if np is None:
        return vec
    norm = np.linalg.norm(vec)
    if norm > 0:
        return (vec / norm).astype(np.float32)
    return vec.astype(np.float32)


def _build_st_embed_fn(
    model_name: str,
    hf_id: str,
    truncate_dim: Optional[int] = None,
    *,
    trust_remote_code: bool = False,
    vertical_chunk_size: Optional[int] = None,
) -> Optional[Callable]:
    """Build callable(text) -> np.ndarray dari sentence-transformers model.

    Mamba2 models butuh trust_remote_code=True dan opsional vertical_chunk_size
    untuk long input efficiency.
    """
    ST = _try_import_sentence_transformers()
    np = _try_import_numpy()
    if ST is None or np is None:
        return None

    with _load_lock:
        if model_name in _model_cache:
            model = _model_cache[model_name]
        else:
            try:
                log.info(
                    "[embedding_loader] loading %s from HF (%s) trust_remote_code=%s...",
                    model_name, hf_id, trust_remote_code,
                )
                if trust_remote_code:
                    model = ST(hf_id, trust_remote_code=True)
                else:
                    model = ST(hf_id)
                _model_cache[model_name] = model
                log.info("[embedding_loader] loaded %s OK", model_name)
            except Exception as e:
                log.warning("[embedding_loader] failed load %s: %s", model_name, e)
                return None

    def embed(text: str):
        try:
            encode_kwargs = {
                "convert_to_numpy": True,
                "show_progress_bar": False,
            }
            # Mamba2: vertical_chunk_size untuk constant-memory long input
            if vertical_chunk_size:
                encode_kwargs["vertical_chunk_size"] = vertical_chunk_size
            v = model.encode(text or "", **encode_kwargs)
            if truncate_dim and v.shape[0] > truncate_dim:
                v = v[:truncate_dim]
            return _l2_normalize(v)
        except Exception as e:
            log.warning("[embedding_loader] embed fn error: %s", e)
            np_local = _try_import_numpy()
            if np_local is not None:
                # Return zero vector → similarity 0 → safe miss
                dim = truncate_dim or 384
                return np_local.zeros(dim, dtype=np_local.float32)
            raise

    return embed


# ── Public API ────────────────────────────────────────────────────────────────

def load_embed_fn(model_name: Optional[str] = None) -> Optional[Callable[[str], Any]]:
    """
    Load embedding function untuk SemanticCache.set_embed_fn().

    Selection (priority):
    1. `model_name` arg eksplisit (kalau diberikan)
    2. ENV var `SIDIX_EMBED_MODEL` (bge-m3 / minilm / mamba2-1.3b / mamba2-7b)
    3. Auto: try bge-m3 → fallback minilm → None

    Returns Callable[[str], np.ndarray] atau None (kalau semua gagal).
    None = graceful disable, semantic_cache stay dormant.
    """
    global _active_model_name

    # Resolve model name
    name = (model_name or os.environ.get("SIDIX_EMBED_MODEL", "")).lower().strip()

    if name and name in MODELS:
        candidates = [name]
    elif name:
        log.warning("[embedding_loader] unknown model '%s', falling back to auto", name)
        candidates = ["bge-m3", "minilm"]
    else:
        # Auto: prefer bge-m3 (multilingual ID), fallback minilm
        candidates = ["bge-m3", "minilm"]

    # Try each in order
    for candidate in candidates:
        spec = MODELS[candidate]
        truncate = spec["dim_truncated"] if spec["dim_truncated"] != spec["dim_native"] else None
        # Mamba2 specifics
        trust_rc = spec.get("needs_trust_remote_code", False)
        # Mamba2 supports vertical_chunk_size untuk long input (multiple of 256)
        vchunk = 512 if candidate.startswith("mamba2") else None
        fn = _build_st_embed_fn(
            candidate, spec["hf_id"],
            truncate_dim=truncate,
            trust_remote_code=trust_rc,
            vertical_chunk_size=vchunk,
        )
        if fn is not None:
            _active_model_name = candidate
            log.info(
                "[embedding_loader] active model: %s (%s, %sB params, dim=%d)",
                candidate, spec["hf_id"], spec["size_b"], spec["dim_truncated"],
            )
            return fn

    log.warning("[embedding_loader] no embedding model loaded — semantic_cache stay dormant")
    _active_model_name = None
    return None


def get_active_model_info() -> dict:
    """Status info untuk admin endpoint."""
    if _active_model_name is None:
        return {
            "active": False,
            "model": None,
            "reason": "no model loaded (sentence-transformers not installed atau load failed)",
            "deploy_hint": (
                "Run on VPS: pip install sentence-transformers numpy. "
                "Untuk Mamba2: tambah pip install kernels einops, transformers>=5.5.0. "
                "Set ENV SIDIX_EMBED_MODEL=bge-m3 (default) atau mamba2-1.3b atau mamba2-7b."
            ),
        }
    spec = MODELS[_active_model_name]
    return {
        "active": True,
        "model": _active_model_name,
        "hf_id": spec["hf_id"],
        "dim": spec["dim_truncated"],
        "size_b": spec["size_b"],
        "multilingual_id": spec["multilingual_id"],
        "needs_trust_remote_code": spec.get("needs_trust_remote_code", False),
        "needs_extra_deps": spec.get("needs_extra_deps", []),
    }


def list_available_models() -> list[dict]:
    """Untuk admin: list semua opsi + status."""
    return [
        {
            "name": name,
            "hf_id": spec["hf_id"],
            "size_b": spec["size_b"],
            "dim": spec["dim_truncated"],
            "multilingual_id": spec["multilingual_id"],
            "default": spec["default"],
            "active": name == _active_model_name,
            "needs_trust_remote_code": spec.get("needs_trust_remote_code", False),
            "needs_extra_deps": spec.get("needs_extra_deps", []),
        }
        for name, spec in MODELS.items()
    ]


__all__ = [
    "MODELS",
    "load_embed_fn",
    "get_active_model_info",
    "list_available_models",
]
