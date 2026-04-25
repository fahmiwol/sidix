# -*- coding: utf-8 -*-
"""Unit tests: GEPA-lite optimizer."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.gepa_optimizer import (
    extract_failure_patterns,
    mutate_prompt,
    evaluate_variant,
    select_pareto_winner,
    run_gepa_lite,
    FailurePattern,
    PromptVariant,
    EvalResult,
)


def test_extract_failure_patterns_detects_kurang_sanad():
    feedback = [
        {"query": "q", "response": "r", "rating": -1, "comment": "tidak ada sumbernya"},
        {"query": "q", "response": "r", "rating": -1, "comment": "kurang rujukan"},
    ]
    patterns = extract_failure_patterns(feedback)
    ids = [p.pattern_id for p in patterns]
    assert "kurang_sanad" in ids


def test_extract_failure_patterns_detects_terlalu_panjang():
    feedback = [
        {"query": "q", "response": "r", "rating": -1, "comment": "terlalu panjang"},
    ]
    patterns = extract_failure_patterns(feedback)
    ids = [p.pattern_id for p in patterns]
    assert "terlalu_panjang" in ids


def test_mutate_prompt_generates_variants():
    patterns = [
        FailurePattern("p1", "test", suggested_fix="Tambahkan constraint X."),
    ]
    variants = mutate_prompt("Base prompt.", patterns, count=3)
    assert len(variants) == 3
    for v in variants:
        assert v.variant_id
        assert v.system_prompt != "Base prompt."
        assert len(v.mutations_applied) == 2


def test_mutate_prompt_fallback_when_no_patterns():
    variants = mutate_prompt("Base prompt.", [], count=2)
    assert len(variants) == 2


def test_evaluate_variant_mock():
    variant = PromptVariant(variant_id="v1", system_prompt="Test prompt.")
    benchmark = [
        {"question": "Q1?", "expected_answer": "A1.", "domain": "general"},
        {"question": "Q2?", "expected_answer": "A2.", "domain": "islamic"},
    ]
    result = evaluate_variant(variant, benchmark, mock_eval=True)
    assert 0.0 <= result.accuracy_score <= 1.0
    assert result.avg_tokens > 0
    assert 0.0 <= result.pareto_score <= 1.0
    assert result.benchmark_size == 2


def test_evaluate_variant_empty_benchmark():
    variant = PromptVariant(variant_id="v1", system_prompt="Test.")
    result = evaluate_variant(variant, [], mock_eval=True)
    assert result.accuracy_score == 0.0
    assert result.benchmark_size == 0


def test_select_pareto_winner():
    results = [
        EvalResult(variant_id="v1", accuracy_score=0.8, avg_tokens=100, token_efficiency=0.5, pareto_score=0.75),
        EvalResult(variant_id="v2", accuracy_score=0.9, avg_tokens=100, token_efficiency=0.5, pareto_score=0.85),
    ]
    winner = select_pareto_winner(results)
    assert winner is not None
    assert winner.variant_id == "v2"


def test_select_pareto_winner_empty():
    assert select_pareto_winner([]) is None


def test_run_gepa_lite_skips_when_too_few_failures():
    result = run_gepa_lite("Base.", [], benchmark_items=[], mock_eval=True)
    assert result.winner_variant_id == ""
    assert result.improvement_delta == 0.0


def test_run_gepa_lite_full_run():
    feedback = [
        {"query": "q", "response": "r", "rating": -1, "comment": "tidak ada sumber"},
        {"query": "q", "response": "r", "rating": -1, "comment": "terlalu panjang"},
        {"query": "q", "response": "r", "rating": -1, "comment": "kurang rujukan"},
    ]
    benchmark = [
        {"question": "Q?", "expected_answer": "A.", "domain": "general"},
    ]
    run = run_gepa_lite("Base prompt.", feedback, benchmark, mock_eval=True)
    assert run.run_id
    assert len(run.variants) == 4  # MUTATION_COUNT default
    assert len(run.eval_results) == 4
    # Improvement bisa positif, negatif, atau nol
