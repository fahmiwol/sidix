# -*- coding: utf-8 -*-
"""Sprint 7b tests: response balance + corpus scope filter."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.agent_react import _rule_based_plan
from brain_qa.learn_agent import (
    _estimate_cqf_score,
    _is_sidix_relevant_item,
    _should_store_in_static_corpus,
)


def test_rule_based_plan_prefers_model_for_general_topic() -> None:
    thought, action, args = _rule_based_plan(
        "Apa itu cloud GPU dan kapan dipakai?",
        "INAN",
        [],
        0,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action == ""
    assert args == {}
    assert "model" in thought.lower()


def test_rule_based_plan_prefers_corpus_for_sidix_topic() -> None:
    _thought, action, args = _rule_based_plan(
        "Jelaskan Maqashid dalam konteks SIDIX",
        "INAN",
        [],
        0,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action == "search_corpus"
    assert args.get("k") == 5


def test_rule_based_plan_force_corpus_if_user_requests_sources() -> None:
    _thought, action, _args = _rule_based_plan(
        "Jawab berdasarkan corpus dan sertakan sanad sumber",
        "INAN",
        [],
        0,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action in {"search_corpus", "list_sources"}


def test_rule_based_plan_honors_corpus_only_mode() -> None:
    _thought, action, _args = _rule_based_plan(
        "Apa itu cloud GPU?",
        "INAN",
        [],
        0,
        corpus_only=True,
        allow_web_fallback=True,
    )
    assert action == "search_corpus"


def test_sidix_relevance_filter_rejects_general_tech_item() -> None:
    item = {
        "title": "Cloud GPU pricing overview",
        "domain": "technology",
        "content": "harga gpu cloud terbaru " * 40,
        "url": "https://example.com/cloud-gpu",
        "sanad_tier": "aggregator",
    }
    assert _is_sidix_relevant_item(item) is False
    assert _should_store_in_static_corpus(item) is False


def test_sidix_relevance_filter_accepts_sidix_item_with_good_quality() -> None:
    item = {
        "title": "Maqashid filter mode untuk SIDIX",
        "domain": "sidix/internal",
        "content": "maqashid sanad naskh ihos " * 80,
        "url": "https://sidix.local/maqashid-filter",
        "sanad_tier": "peer_review",
    }
    assert _is_sidix_relevant_item(item) is True
    assert _estimate_cqf_score(item) >= 8.0
    assert _should_store_in_static_corpus(item) is True
