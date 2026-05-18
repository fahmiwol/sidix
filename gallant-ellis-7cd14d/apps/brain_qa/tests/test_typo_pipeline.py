"""Smoke tests for brain/typo/pipeline.py (loaded by file path)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_PIPELINE = _ROOT / "brain" / "typo" / "pipeline.py"


@pytest.fixture
def typo_mod():
    spec = importlib.util.spec_from_file_location("sidix_typo_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sidix_typo_pipeline"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_normalize_query_script_hint_latin(typo_mod) -> None:
    r = typo_mod.normalize_query("hello yuo there")
    assert r.script_hint == "latin"
    assert "you" in r.normalized.lower()


def test_normalize_query_mixed_arab_latin(typo_mod) -> None:
    r = typo_mod.normalize_query("hello السلام")
    assert r.script_hint == "mixed_arab_latin"
