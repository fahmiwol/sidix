"""
blind_ab_test.py — Sprint 13 Phase 3c quality gate scaffold.

Persona blind A/B test: 50 prompts × 5 persona × {base_lora, dora_persona}
→ score persona accuracy (auto + human-grader optional).

Auto-grader pakai PERSONA_MARKERS dari persona_qa_generator.py — sama scorer
yang dipakai untuk training data filter, jadi konsisten.

Quality gate Phase 3c (per ROADMAP_DORA_SPRINT13.md):
- DoRA accuracy ≥80% (DoRA voice match expected persona ≥80% of time)
- Base LoRA accuracy harus < DoRA (sanity check that DoRA actually adds signal)
- Regression: corpus answer accuracy delta < 5% (DoRA tidak boleh hancurin
  generative ability)

Reference:
- research note 285 (signature scoring methodology)
- ROADMAP_DORA_SPRINT13.md Phase 4 quality gates
"""
from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Test prompts (5 categories × 10 prompts = 50 total) ──────────────────────
# Topic mix sesuai persona signature domain — supaya test fair (bukan
# all-creative atau all-engineer).

BLIND_TEST_PROMPTS = [
    # Tech/coding (lebih cocok ABOO)
    "Bagaimana cara debug memory leak di Python production?",
    "Kapan harus pakai async vs threading?",
    "Trade-off monolith vs microservices untuk startup early-stage?",
    "Bagaimana implementasi rate limiting tanpa Redis?",
    "Best practice handling race condition di FastAPI?",
    # Strategy/business (lebih cocok OOMAR)
    "Framework prioritisasi feature backlog yang valid?",
    "Cara validasi product-market fit cepat?",
    "Kapan startup harus pivot vs persevere?",
    "Bagaimana pricing strategy untuk SaaS B2B?",
    "Metric apa yang matter untuk seed-stage startup?",
    # Creative/design (lebih cocok UTZ)
    "Cara bikin landing page yang convert tinggi?",
    "Color palette untuk brand AI spiritual tech?",
    "Storyboarding untuk demo video produk?",
    "Visual hierarchy di dashboard data-heavy?",
    "Naming convention buat fitur baru yang catchy?",
    # Research/academic (lebih cocok ALEY)
    "Perbedaan transformer dan state-space model?",
    "Kenapa attention mechanism better dari LSTM?",
    "Metodologi A/B test yang valid statistically?",
    "Bagaimana validate hypothesis tanpa control group?",
    "Interpretasi p-value dalam ML eval?",
    # Casual/wellbeing (lebih cocok AYMAN)
    "Bagaimana atur work-life balance pas WFH?",
    "Kenapa sulit fokus belajar hal baru?",
    "Tips bangun pagi konsisten?",
    "Cara hadapi feedback negatif dari atasan?",
    "Cara ngomong ke diri sendiri pas burnout?",
    # Cross-domain (semua persona harus bisa jawab dengan voice masing-masing)
    "Apa pendapatmu soal AI menggantikan pekerjaan creative?",
    "Bagaimana approach belajar skill baru di umur 30+?",
    "Trade-off antara speed vs correctness di engineering?",
    "Kenapa first principle thinking sulit dipraktikkan?",
    "Bagaimana cara tetap kreatif saat under deadline?",
    # Edge: ambigu (test persona consistency under ambiguity)
    "Aku bingung harus mulai dari mana, ada saran?",
    "Tolong bantu, aku lagi stuck di project.",
    "Gimana ya cara bikin keputusan yang sulit?",
    "Aku ngerasa burnout, what should I do?",
    "Hmm, ada perspektif lain soal ini?",
    # Domain-mixed (persona dimanasin, harus tetap consistent)
    "Coding sambil jaga mental health — gimana caranya?",
    "Bisnis vs passion — pilih yang mana?",
    "Riset vs eksekusi — kapan switch fokus?",
    "Idealisme vs pragmatisme di startup?",
    "Kompromi vs kompromi — bedanya?",
    # Practical: real user query patterns
    "Kasih panduan setup CI/CD yang gak ribet.",
    "Tolong rangkumkan trade-off PostgreSQL vs MongoDB.",
    "Saran growth strategy untuk tools developer?",
    "Buatin rencana belajar machine learning 3 bulan.",
    "Review architecture decision: pakai Kafka atau Redis Pub/Sub?",
    # Emotional/human (persona response harus distinct empathy level)
    "Aku kehilangan motivasi, gak tau kenapa.",
    "Boss aku micro-manage banget, gimana cope?",
    "Tim aku broken trust, recovery-nya gimana?",
    "Aku doubt diri sendiri terus, ini normal?",
    "Gimana cara restart hidup tanpa drama?",
]
assert len(BLIND_TEST_PROMPTS) == 50, f"expect 50 prompts, got {len(BLIND_TEST_PROMPTS)}"


@dataclass
class BlindTestResult:
    """Hasil 1 prompt × 1 persona."""
    prompt_id: int
    prompt: str
    expected_persona: str
    response: str
    auto_score_own: float = 0.0  # signature_score against expected persona
    auto_score_cross: dict = field(default_factory=dict)  # score against other personas
    auto_voice_match: bool = False  # own > cross by margin ≥0.20
    human_grade: Optional[str] = None  # "match" | "weak" | "wrong" — optional


def auto_grade_response(response: str, expected_persona: str) -> dict:
    """Auto-grader pakai PERSONA_MARKERS scoring.

    Returns dict {own_score, cross_scores, voice_match}.
    """
    from .persona_qa_generator import _signature_score, PERSONA_MARKERS

    own = _signature_score(response, expected_persona)
    cross_scores = {}
    others = [p for p in PERSONA_MARKERS.keys() if p != expected_persona]
    for p in others:
        cross_scores[p] = _signature_score(response, p)

    cross_avg = sum(cross_scores.values()) / len(cross_scores) if cross_scores else 0.0
    voice_match = (own - cross_avg) >= 0.20  # gap ≥0.20 = clearly persona-distinct

    return {
        "own_score": round(own, 3),
        "cross_scores": {p: round(s, 3) for p, s in cross_scores.items()},
        "cross_avg": round(cross_avg, 3),
        "voice_match": voice_match,
    }


def run_blind_test(
    persona_responder,  # callable(prompt, persona) → str
    out_path: Optional[str] = None,
    sample_n: Optional[int] = None,
) -> dict:
    """Run blind A/B test 50 prompts × 5 persona.

    Args:
        persona_responder: function (prompt, persona) → response_text.
            Phase 3c akan inject `local_llm.generate_sidix(persona=persona)`.
        out_path: simpan detail results (JSON) — default skip
        sample_n: kalau set, sampling N prompts dari 50 (untuk quick smoke test)

    Returns:
        dict summary {persona_accuracy, total, voice_match_count,
                       avg_own_score, regression_check}
    """
    from .persona_qa_generator import PERSONA_MARKERS

    prompts = BLIND_TEST_PROMPTS
    if sample_n:
        prompts = random.sample(prompts, min(sample_n, len(prompts)))

    personas = list(PERSONA_MARKERS.keys())
    results: list[BlindTestResult] = []

    log.info("[blind_test] running %d prompts × %d personas = %d responses",
             len(prompts), len(personas), len(prompts) * len(personas))

    for pid, prompt in enumerate(prompts):
        for persona in personas:
            try:
                response = persona_responder(prompt, persona)
            except Exception as e:
                log.warning("[blind_test] responder error: %s", e)
                response = ""

            grade = auto_grade_response(response, persona)
            results.append(BlindTestResult(
                prompt_id=pid,
                prompt=prompt,
                expected_persona=persona,
                response=response,
                auto_score_own=grade["own_score"],
                auto_score_cross=grade["cross_scores"],
                auto_voice_match=grade["voice_match"],
            ))

    # Aggregate
    by_persona: dict[str, list[BlindTestResult]] = {p: [] for p in personas}
    for r in results:
        by_persona[r.expected_persona].append(r)

    persona_accuracy = {}
    for p, rs in by_persona.items():
        if not rs:
            persona_accuracy[p] = {"total": 0, "voice_match": 0, "accuracy": 0.0}
            continue
        match = sum(1 for r in rs if r.auto_voice_match)
        persona_accuracy[p] = {
            "total": len(rs),
            "voice_match": match,
            "accuracy": round(match / len(rs), 3),
            "avg_own_score": round(sum(r.auto_score_own for r in rs) / len(rs), 3),
        }

    overall = sum(p["voice_match"] for p in persona_accuracy.values()) / max(
        sum(p["total"] for p in persona_accuracy.values()), 1)

    summary = {
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "total_responses": len(results),
        "overall_accuracy": round(overall, 3),
        "quality_gate_80": overall >= 0.80,
        "per_persona": persona_accuracy,
    }

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "results": [asdict(r) for r in results],
            }, f, ensure_ascii=False, indent=2)
        log.info("[blind_test] saved → %s", out_path)

    return summary


def stub_responder(prompt: str, persona: str) -> str:
    """Phase 3a stub responder — pakai persona_qa_generator template untuk
    smoke test (verify blind_test pipeline jalan tanpa LLM real).
    Phase 3c real responder = `local_llm.generate_sidix(prompt, persona=persona)`.
    """
    from .persona_qa_generator import _PERSONA_GENERATORS
    gen = _PERSONA_GENERATORS.get(persona.upper())
    if gen is None:
        return ""
    # Reuse template generator with prompt as topic seed
    return gen(prompt[:60])


__all__ = [
    "BLIND_TEST_PROMPTS",
    "BlindTestResult",
    "auto_grade_response",
    "run_blind_test",
    "stub_responder",
]
