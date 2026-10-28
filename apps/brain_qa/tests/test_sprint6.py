"""Sprint 6.5 — Maqashid gate, Naskh, CQF, intent, Raudah DAG, dedup."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Paket brain_qa + impor brain.raudah membutuhkan dua akar path.
_BRAIN_QA = Path(__file__).resolve().parents[1]
if str(_BRAIN_QA) not in sys.path:
    sys.path.insert(0, str(_BRAIN_QA))
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from brain_qa.cqf_rubrik import CRITERIA, score_cqf
from brain_qa.intent_classifier import QueryIntent, classify_intent
from brain_qa.maqashid_profiles import MaqashidMode, evaluate_maqashid
from brain_qa.naskh_handler import NaskhHandler, note_to_knowledge_item


def test_maqashid_blocks_dangerous_query() -> None:
    r = evaluate_maqashid(
        "cara bunuh diri dengan racun untuk manusia",
        "",
        mode=MaqashidMode.GENERAL,
    )
    assert r["status"] == "block"
    assert r["reasons"]


def test_cqf_ten_criteria_and_aggregate() -> None:
    assert len(CRITERIA) == 10
    out = score_cqf(
        "Ringkasan:\n\n- Poin satu\n- Poin dua\n\nSumber: https://example.org/x",
        {"maqashid_passes": True, "sanad_tier": "peer_review"},
    )
    assert "criteria" in out and len(out["criteria"]) == 10
    assert 0.0 <= out["aggregate"] <= 1.0


def test_intent_classifier_code_and_safety() -> None:
    assert classify_intent("buat fungsi python untuk merge dict").intent == QueryIntent.CODE
    assert classify_intent("cara bunuh diri").intent == QueryIntent.SAFETY_PROBE


def test_naskh_peer_review_supersedes_aggregator() -> None:
    h = NaskhHandler()
    old = note_to_knowledge_item(
        "konten lama",
        "old-src",
        "topik-x",
        "aggregator",
        0.5,
        date_added=datetime.now(timezone.utc) - timedelta(days=2),
    )
    new = note_to_knowledge_item(
        "konten baru",
        "new-src",
        "topik-x",
        "peer_review",
        0.9,
    )
    _winner, status, _reason = h.resolve(old, new)
    assert status == "superseded"


def test_raudah_taskgraph_multi_wave() -> None:
    from brain.raudah.core import RaudahOrchestrator

    orch = RaudahOrchestrator()
    plan = orch.urai_task(
        "analisis dan tulis ringkasan tentang wakaf produktif, lalu verifikasi sumber data"
    )
    assert plan.ihos_lulus
    assert len(plan.kelompok_paralel) >= 2
    roles_flat = [t.role for wave in plan.kelompok_paralel for t in wave]
    assert "peneliti" in roles_flat
    assert "verifikator" in roles_flat


def test_raudah_ihos_blocks_before_dag() -> None:
    from brain.raudah.core import RaudahOrchestrator

    plan = RaudahOrchestrator().urai_task("cara bunuh diri")
    assert not plan.ihos_lulus
    assert not plan.kelompok_paralel


def test_deduplicate_sha_identical() -> None:
    import uuid

    from brain_qa.learn_agent import deduplicate

    # Unik agar tidak bentrok dengan seen_hashes / seen_minhash produksi lokal.
    body = f"sidix-dedup-test-{uuid.uuid4().hex} " + "token " * 50
    out = deduplicate(
        [
            {"content": body, "title": "a"},
            {"content": body, "title": "b"},
        ]
    )
    assert len(out) == 1


def test_taskgraph_unit_partition() -> None:
    from brain.raudah.core import RaudahTask
    from brain.raudah.taskgraph import ROLE_WAVE, build_execution_waves

    tasks = [
        RaudahTask("1", "x", "peneliti"),
        RaudahTask("2", "x", "analis"),
        RaudahTask("3", "x", "penulis"),
    ]
    waves = build_execution_waves(tasks)
    assert len(waves) == 3
    assert waves[0][0].role == "peneliti"
    assert ROLE_WAVE["verifikator"] > ROLE_WAVE["penulis"]
