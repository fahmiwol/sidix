"""
nafs_bridge.py — Load brain/nafs/response_orchestrator.py untuk ReAct (Layer B Nafs).

Mirip pola typo_bridge.py: dynamic load tanpa install brain/ sebagai package.
Dikontrol oleh SIDIX_NAFS_LAYER_B (default: on).

Layer priority di _response_blend_profile:
  A) jiwa/orchestrator.py (thin adapter, production)
  B) brain/nafs/response_orchestrator.py (3-layer NafsOrchestrator, ini)
  C) Heuristik lama (fallback statis)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NAFS_PATH = _REPO_ROOT / "brain" / "nafs" / "response_orchestrator.py"
_MODULE_NAME = "sidix_nafs_orchestrator_runtime"
_loaded = None


def _nafs_module():
    global _loaded
    if _loaded is not None:
        return _loaded
    if not _NAFS_PATH.is_file():
        raise FileNotFoundError(f"nafs orchestrator tidak ditemukan: {_NAFS_PATH}")
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _NAFS_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("tidak dapat load nafs orchestrator spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    _loaded = mod
    return mod


def nafs_layer_b_enabled() -> bool:
    v = os.environ.get("SIDIX_NAFS_LAYER_B", "1").strip().lower()
    return v not in ("0", "false", "off", "no", "")


def blend_from_nafs(
    question: str, persona: str = "UTZ", *, corpus_only: bool = False
) -> dict[str, Any]:
    """
    Return blend profile dict dari NafsOrchestrator (Layer B).
    Kembalikan dict kosong jika disabled atau error (caller pakai fallback).

    Fields yang dikembalikan:
      name, max_obs_blocks, system_hint, skip_corpus, hayat_enabled,
      topic, nafs_layers_used, nafs_parametric_weight,
      nafs_dynamic_weight, nafs_static_weight
    """
    if not nafs_layer_b_enabled():
        return {}
    try:
        mod = _nafs_module()
        nafs = mod.NafsOrchestrator()
        nr = nafs.respond(question, persona, corpus_only=corpus_only)
        return {
            "name": f"nafs_{nr.topic}",
            "max_obs_blocks": 1 if nr.skip_corpus else 2,
            "system_hint": "",
            "skip_corpus": nr.skip_corpus,
            "hayat_enabled": nr.hayat_enabled,
            "topic": nr.topic,
            "nafs_layers_used": ",".join(nr.layers_used),
            "nafs_parametric_weight": nr.parametric_weight,
            "nafs_dynamic_weight": nr.dynamic_weight,
            "nafs_static_weight": nr.static_weight,
        }
    except Exception:
        return {}
