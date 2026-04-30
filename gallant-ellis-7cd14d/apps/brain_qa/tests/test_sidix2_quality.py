"""
test_sidix2_quality — Golden tests untuk SIDIX 2.0 Supermodel launch.

Bukan unit test atomic — ini smoke + integration test yang validate
behaviour end-to-end yang dijanjikan ke user:

  1. Casual chat  → bersih, no [EXPLORATORY], no boilerplate disclaimer
  2. Routing      → factual query trigger web_search action
  3. Supermodel   → 3 endpoint baru (burst, two-eyed, foresight) callable
  4. Filter logic → strict_mode opt-in fire pipeline; default bypass

Test ini designed supaya BISA jalan tanpa Ollama (mock LLM) — pure
logic check. Untuk live LLM check, jalankan smoke script terpisah.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── Casual gate (maqashid_profiles + epistemology) ──────────────────────────

def test_casual_query_detection() -> None:
    from brain_qa.maqashid_profiles import is_casual_query, is_sensitive_topic
    assert is_casual_query("halo") is True
    assert is_casual_query("hi") is True
    assert is_casual_query("test") is True
    assert is_casual_query("apa kabar") is True
    assert is_casual_query("jelaskan algoritma BFS dengan contoh kode python") is False
    assert is_casual_query("hukum trading crypto menurut MUI") is False

    # Sensitive: fiqh / medis / data eksplisit
    assert is_sensitive_topic("fatwa MUI tentang crypto") is True
    assert is_sensitive_topic("dosis obat untuk anak") is True
    assert is_sensitive_topic("halo") is False
    assert is_sensitive_topic("siapa nama presiden") is False  # bukan term sensitif core


def test_evaluate_maqashid_skip_tag_for_casual() -> None:
    """AYMAN persona casual greeting → no [EXPLORATORY] tag."""
    from brain_qa.maqashid_profiles import evaluate_maqashid
    r = evaluate_maqashid(
        "halooww",
        "Halo! Apa kabar?",
        persona_name="AYMAN",
    )
    assert "[EXPLORATORY" not in r["tagged_output"]
    assert "Berdasarkan referensi" not in r["tagged_output"]


# ── Web search trigger (current events regex) ────────────────────────────────

def test_current_events_regex_en_id_variants() -> None:
    from brain_qa.agent_react import _needs_web_search
    cases = [
        ("siapa president indonesia sekarang?", True),
        ("siapa presiden indonesia sekarang?", True),
        ("who is the president of usa", True),
        ("what is happening in palestine", True),
        ("harga bitcoin hari ini", True),
        ("berita teknologi terbaru", True),
        ("latest AI news", True),
        ("siapa juara liga champions 2024", True),
        ("halo", False),
        ("apa itu python", False),
        ("jelaskan algoritma BFS", False),
    ]
    for q, expected in cases:
        assert _needs_web_search(q) is expected, f"regex fail: {q!r}"


# ── Supermodel endpoints — modul callable ───────────────────────────────────

def test_burst_module_importable() -> None:
    from brain_qa.agent_burst import (
        burst_refine, burst, refine, pareto_select, _BURST_ANGLES,
    )
    # 8 angles defined
    assert len(_BURST_ANGLES) == 8
    angle_keys = [a[0] for a in _BURST_ANGLES]
    assert "contrarian" in angle_keys
    assert "first_principles" in angle_keys
    assert "future_back" in angle_keys


def test_pareto_select_picks_best_in_front() -> None:
    """Synthetic candidates — Pareto front selects non-dominated."""
    from brain_qa.agent_burst import pareto_select
    cands = [
        {"angle": "a", "ok": True, "text": "x" * 100, "mode": "test"},
        {"angle": "b", "ok": True, "text": "y" * 100, "mode": "test"},
        {"angle": "c", "ok": False, "text": "", "mode": "error"},  # filtered
    ]
    winners = pareto_select(cands, top_k=2)
    assert all(w.get("ok") for w in winners)
    assert all(w["angle"] in ("a", "b") for w in winners)


def test_two_eyed_module_importable() -> None:
    from brain_qa.agent_two_eyed import two_eyed_view, _LEFT_EYE_SYSTEM, _RIGHT_EYE_SYSTEM
    assert "scientific" in _LEFT_EYE_SYSTEM.lower()
    assert "maqashid" in _RIGHT_EYE_SYSTEM.lower()


def test_foresight_module_importable() -> None:
    from brain_qa.agent_foresight import foresight, scan, extract_signals, project_scenarios, synthesize
    assert callable(foresight)
    assert callable(scan)


# ── Web search multi-engine fallback ────────────────────────────────────────

def test_web_search_module_has_fallback_chain() -> None:
    """Pastikan _ddg_search, _ddg_lite_search, _wikipedia_search defined."""
    from brain_qa import agent_tools
    assert hasattr(agent_tools, "_ddg_search")
    assert hasattr(agent_tools, "_ddg_lite_search")
    assert hasattr(agent_tools, "_wikipedia_search")
    assert hasattr(agent_tools, "_tool_web_search")


# ── Persona mode mapping aligns with pivot ──────────────────────────────────

def test_persona_mode_map_aligns_with_pivot() -> None:
    """Pivot 2026-04-25/26: AYMAN=GENERAL (chat hangat), bukan IJTIHAD."""
    from brain_qa.maqashid_profiles import _PERSONA_MODE_MAP, MaqashidMode
    assert _PERSONA_MODE_MAP["AYMAN"] == MaqashidMode.GENERAL
    assert _PERSONA_MODE_MAP["OOMAR"] == MaqashidMode.GENERAL
    assert _PERSONA_MODE_MAP["ALEY"] == MaqashidMode.ACADEMIC  # researcher
    assert _PERSONA_MODE_MAP["ABOO"] == MaqashidMode.ACADEMIC
    assert _PERSONA_MODE_MAP["UTZ"] == MaqashidMode.CREATIVE


# ── Pydantic schemas top-level (FastAPI introspection) ──────────────────────

def test_supermodel_request_schemas_top_level() -> None:
    """BurstRequest / TwoEyedRequest / ForesightRequest harus di module top
    supaya FastAPI body-introspection berhasil (bukan query param)."""
    from brain_qa.agent_serve import BurstRequest, TwoEyedRequest, ForesightRequest
    # Default values ensure they're validated as body
    assert BurstRequest.model_fields["prompt"].is_required()
    assert TwoEyedRequest.model_fields["prompt"].is_required()
    assert ForesightRequest.model_fields["topic"].is_required()
