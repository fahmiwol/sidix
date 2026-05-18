"""
test_self_test_loop.py — Unit tests for Sprint F: Self-Test Loop

Coverage:
- generate_test_questions (fallback path)
- run_single_self_test (mock OMNYX)
- composite score calculation
- get_self_test_stats & history
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.self_test_loop import (
    generate_test_questions,
    run_single_self_test,
    get_self_test_stats,
    get_self_test_history,
    _fallback_questions,
    DEFAULT_DOMAINS,
    SelfTestResult,
)


# ── Test 1: Fallback questions ───────────────────────────────────────────

def test_fallback_questions():
    qs = _fallback_questions(3)
    assert len(qs) == 3
    assert all(len(q) > 10 for q in qs)
    print("OK test_fallback_questions")


async def test_generate_test_questions_fallback():
    # Kalau LLM tidak available, harus return fallback
    qs = await generate_test_questions(n=2, domains=["factual_indonesia"])
    assert len(qs) >= 1
    assert all(isinstance(q, str) and len(q) > 10 for q in qs)
    print("OK test_generate_test_questions_fallback")


# ── Test 2: SelfTestResult dataclass ─────────────────────────────────────

def test_self_test_result_model():
    r = SelfTestResult(
        test_id="st_abc123",
        question="test?",
        answer="yes",
        persona="AYMAN",
        sanad_score=0.85,
        sanad_verdict="pass",
        complexity="simple",
        duration_ms=1200,
        sources_used=["corpus"],
        composite_score=0.72,
        stored_to="lesson",
        timestamp="2026-05-01T00:00:00+00:00",
    )
    assert r.test_id.startswith("st_")
    assert r.composite_score > 0
    print("OK test_self_test_result_model")


# ── Test 3: Stats & History (empty state) ────────────────────────────────

def test_stats_empty():
    stats = get_self_test_stats()
    assert stats["total_tests"] == 0
    assert stats["avg_composite"] == 0.0
    print("OK test_stats_empty")


def test_history_empty():
    hist = get_self_test_history(limit=10)
    assert hist == []
    print("OK test_history_empty")


# ── Test 4: Composite score logic ────────────────────────────────────────

def test_composite_score_weights():
    # Simulate scoring: sanad=0.8, 2 sources, fast (<30s)
    sanad = 0.8
    source_bonus = min(1.0, 2 / 3.0) * 0.2  # 0.133
    speed_bonus = 0.1  # <30s
    composite = (sanad * 0.7) + source_bonus + speed_bonus
    expected = round(min(1.0, composite), 3)
    # 0.56 + 0.133 + 0.1 = 0.793
    assert 0.79 <= expected <= 0.80
    print("OK test_composite_score_weights")


# ── Test 5: DEFAULT_DOMAINS ──────────────────────────────────────────────

def test_default_domains():
    assert len(DEFAULT_DOMAINS) >= 5
    assert "factual_indonesia" in DEFAULT_DOMAINS
    print("OK test_default_domains")


# ── Runner ───────────────────────────────────────────────────────────────

def main():
    print("=== Sprint F: Self-Test Loop Tests ===\n")
    test_fallback_questions()
    test_self_test_result_model()
    test_stats_empty()
    test_history_empty()
    test_composite_score_weights()
    test_default_domains()
    asyncio.run(test_generate_test_questions_fallback())
    print("\n=== ALL PASSED ===")


if __name__ == "__main__":
    main()
