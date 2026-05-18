"""Unit tests for sanad-tier retrieval weighting (Sprint 1 T1.2)."""

from __future__ import annotations

import pytest

from brain_qa.sanad_ranking import (
    SANAD_WEIGHTS,
    apply_sanad_weight,
    extract_sanad_tier_from_markdown,
    normalize_sanad_tier,
)


def test_primer_weight_greater_than_peer_review_at_equal_bm25() -> None:
    base = 10.0
    assert apply_sanad_weight("primer", base) > apply_sanad_weight("peer_review", base)
    assert apply_sanad_weight("primer", base) == pytest.approx(base * SANAD_WEIGHTS["primer"])
    assert apply_sanad_weight("peer_review", base) == pytest.approx(base * SANAD_WEIGHTS["peer_review"])


def test_ranking_stability_tiebreak_prefers_higher_bm25() -> None:
    """When weighted scores tie, secondary key should prefer stronger raw BM25."""
    scores = [3.0, 2.0]
    tiers = ["unknown", "unknown"]
    weighted = [apply_sanad_weight(t, scores[i]) for i, t in enumerate(tiers)]
    ranked = sorted(range(2), key=lambda i: (-weighted[i], -scores[i]))
    assert ranked[0] == 0


def test_unknown_default_for_missing_or_invalid_tier() -> None:
    assert normalize_sanad_tier(None) == "unknown"
    assert normalize_sanad_tier("") == "unknown"
    assert normalize_sanad_tier("not-a-real-tier") == "unknown"
    assert apply_sanad_weight("bogus", 5.0) == pytest.approx(5.0 * SANAD_WEIGHTS["unknown"])


def test_frontmatter_extracts_peer_review() -> None:
    md = """---
sanad_tier: peer-review
---
# Hello
body
"""
    assert extract_sanad_tier_from_markdown(md) == "peer_review"
