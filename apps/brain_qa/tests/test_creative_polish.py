"""
test_creative_polish.py — Unit tests for Sprint H: Creative Output Polish

Coverage:
- _parse_eval_response
- QualityScore dataclass
- PolishResult dataclass
- get_polish_stats (empty state)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.creative_polish import (
    _parse_eval_response,
    QualityScore,
    PolishResult,
    get_polish_stats,
)


# ── Test 1: Parse eval response ──────────────────────────────────────────

def test_parse_eval_response():
    text = """Originality: 0.8 | cukup unik
Clarity: 0.7 | struktur bagus
Usefulness: 0.6 | actionable
Maqashid: 0.9 | sangat selaras
Composite: 0.74"""
    score = _parse_eval_response(text)
    assert score.originality == 0.8
    assert score.clarity == 0.7
    assert score.usefulness == 0.6
    assert score.maqashid == 0.9
    assert 0.73 <= score.composite <= 0.75
    print("OK test_parse_eval_response")


# ── Test 2: Parse eval response partial ──────────────────────────────────

def test_parse_eval_response_partial():
    text = "Originality: 0.5 | biasa saja"
    score = _parse_eval_response(text)
    assert score.originality == 0.5
    # defaults for missing
    assert score.clarity == 0.5
    assert score.usefulness == 0.5
    assert score.maqashid == 0.5
    print("OK test_parse_eval_response_partial")


# ── Test 3: QualityScore model ───────────────────────────────────────────

def test_quality_score_model():
    s = QualityScore(
        originality=0.8, clarity=0.7, usefulness=0.6, maqashid=0.9,
        composite=0.74, feedback="bagus",
    )
    assert s.composite > 0
    print("OK test_quality_score_model")


# ── Test 4: PolishResult model ───────────────────────────────────────────

def test_polish_result_model():
    before = QualityScore(0.5, 0.5, 0.5, 0.5, 0.5, "before")
    after = QualityScore(0.7, 0.7, 0.7, 0.7, 0.7, "after")
    r = PolishResult(
        iteration=1, input_content="a", output_content="b",
        scores_before=before, scores_after=after,
        improvement=0.2, converged=False,
    )
    assert r.iteration == 1
    assert r.improvement == 0.2
    print("OK test_polish_result_model")


# ── Test 5: get_polish_stats empty ───────────────────────────────────────

def test_get_polish_stats_empty():
    stats = get_polish_stats()
    assert stats["total_polishes"] == 0
    print("OK test_get_polish_stats_empty")


# ── Runner ───────────────────────────────────────────────────────────────

def main():
    print("=== Sprint H: Creative Output Polish Tests ===\n")
    test_parse_eval_response()
    test_parse_eval_response_partial()
    test_quality_score_model()
    test_polish_result_model()
    test_get_polish_stats_empty()
    print("\n=== ALL PASSED ===")


if __name__ == "__main__":
    main()
