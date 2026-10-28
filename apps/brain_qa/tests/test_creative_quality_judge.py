"""
Unit tests untuk creative_quality LLM-as-Judge parser dan fallback.
Tidak membutuhkan Ollama running.
"""

from __future__ import annotations

import pytest

from brain_qa.creative_quality import (
    CQFScore,
    _parse_judge_json,
    heuristic_score,
    llm_judge_score,
)


# ── _parse_judge_json ─────────────────────────────────────────────────────────

def test_parse_judge_json_valid():
    raw = (
        '{"relevance":{"score":8.5,"reason":"ok"},'
        '"quality":{"score":7.0,"reason":"ok"},'
        '"creativity":{"score":9.0,"reason":"ok"},'
        '"brand_alignment":{"score":6.5,"reason":"ok"},'
        '"actionability":{"score":7.5,"reason":"ok"}}'
    )
    s = _parse_judge_json(raw)
    assert s is not None
    assert s.relevance == 8.5
    assert s.quality == 7.0
    assert s.creativity == 9.0


def test_parse_judge_json_with_markdown_fences():
    raw = (
        "```json\n"
        '{"relevance":{"score":8.0,"reason":"ok"},'
        '"quality":{"score":7.5,"reason":"ok"},'
        '"creativity":{"score":7.0,"reason":"ok"},'
        '"brand_alignment":{"score":6.0,"reason":"ok"},'
        '"actionability":{"score":5.5,"reason":"ok"}}\n'
        "```"
    )
    s = _parse_judge_json(raw)
    assert s is not None
    assert s.relevance == 8.0


def test_parse_judge_json_invalid_returns_none():
    assert _parse_judge_json("not json") is None
    assert _parse_judge_json("") is None


# ── llm_judge_score fallback ──────────────────────────────────────────────────

def test_llm_judge_score_fallback_when_ollama_offline():
    """Tanpa Ollama, llm_judge_score harus fallback ke heuristic_score."""
    out = "Ini adalah output contoh untuk test."
    brief = "Buatkan caption Instagram tentang teknologi."
    score = llm_judge_score(out, brief, domain="content")
    # Fallback ke heuristic — semua dimensi harus punya nilai 0-10
    assert 0.0 <= score.relevance <= 10.0
    assert 0.0 <= score.quality <= 10.0
    assert 0.0 <= score.creativity <= 10.0


def test_llm_judge_score_preserves_domain_scores():
    out = "test"
    brief = "test"
    score = llm_judge_score(out, brief, domain="content")
    assert "hook_strength" in score.domain_scores
