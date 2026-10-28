"""
Load repo-root ``brain/typo/pipeline.py`` for ReAct without installing ``brain`` as a package.

Controlled by ``SIDIX_TYPO_PIPELINE`` (default: on). Set to ``0``, ``false``, ``off``, or ``no`` to disable.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# typo_bridge.py lives at apps/brain_qa/brain_qa/ → repo root is three levels up
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PIPELINE_PATH = _REPO_ROOT / "brain" / "typo" / "pipeline.py"
_MODULE_NAME = "sidix_typo_pipeline_runtime"
_loaded = None


def _pipeline_module():
    global _loaded
    if _loaded is not None:
        return _loaded
    if not _PIPELINE_PATH.is_file():
        raise FileNotFoundError(f"typo pipeline missing: {_PIPELINE_PATH}")
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load typo pipeline spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    _loaded = mod
    return mod


def typo_pipeline_enabled() -> bool:
    v = os.environ.get("SIDIX_TYPO_PIPELINE", "1").strip().lower()
    return v not in ("0", "false", "off", "no", "")


def normalize_for_react(text: str) -> tuple[str, str, int]:
    """
    Returns (normalized_question, script_hint, substitutions_applied).
    When disabled or on error, callers should fall back to raw text.
    """
    if not typo_pipeline_enabled():
        return text, "", 0
    mod = _pipeline_module()
    result = mod.normalize_query(text)
    return result.normalized, result.script_hint, int(result.substitutions_applied)
