# -*- coding: utf-8 -*-
"""
gepa_optimizer.py — GEPA-lite: Genetic-Eval-Pareto Auto-Optimizer (Jiwa Sprint 4+)

Konsep: Self-improving agent tanpa training — cukup iterasi prompt + eval.
Inspired by: GEPA (Genetic-Pareto Optimization, 2026) — 35x lebih efisien dari RL.

Pipeline SIDIX-native:
  1. COLLECT — gather poor responses (thumbs_down, low score, failed eval)
  2. ANALYZE — extract failure patterns (mis: "kurang sanad", "terlalu panjang")
  3. MUTATE — generate prompt variations yang memperbaiki pattern
  4. EVAL — A/B test pada held-out benchmark subset
  5. SELECT — Pareto: pilih winner berdasarkan accuracy vs token efficiency

Domain: Kimi (Jiwa) — judgment, taste, creativity.
Zero overlap dengan Claude (deploy/core).
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("sidix.gepa")

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_DATA_DIR = _BASE.parent / ".data"
_GEPA_DIR = _DATA_DIR / "gepa"
_GEPA_DIR.mkdir(parents=True, exist_ok=True)

# ── Config ───────────────────────────────────────────────────────────────────
MUTATION_COUNT = 4          # berapa variasi prompt yang di-generate per iterasi
HELD_OUT_RATIO = 0.2        # 20% benchmark untuk eval
MIN_FAILURES_TO_RUN = 3     # minimum failed responses sebelum optimasi
TOKEN_EFF_WEIGHT = 0.3      # bobot token efficiency di Pareto score
ACCURACY_WEIGHT = 0.7       # bobot accuracy di Pareto score


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class FailurePattern:
    """Pola kegagalan yang diekstrak dari response buruk."""
    pattern_id: str
    description: str          # mis: "kurang sanad", "terlalu panjang", "tidak relevan"
    frequency: int = 1        # berapa kali muncul
    affected_domains: list[str] = field(default_factory=list)
    suggested_fix: str = ""   # hint untuk mutasi prompt


@dataclass
class PromptVariant:
    """Satu variasi system prompt yang di-generate."""
    variant_id: str
    system_prompt: str
    mutations_applied: list[str] = field(default_factory=list)
    generation_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EvalResult:
    """Hasil evaluasi satu variant pada held-out set."""
    variant_id: str
    accuracy_score: float     # 0.0–1.0 (dari eval_harness atau llm_judge)
    avg_tokens: float         # rata-rata token per response
    token_efficiency: float   # 1.0 = paling efisien (rendah token, high accuracy)
    pareto_score: float       # composite: ACCURACY_WEIGHT*acc + TOKEN_EFF_WEIGHT*eff
    benchmark_size: int = 0
    elapsed_s: float = 0.0


@dataclass
class GEPARun:
    """Satu run lengkap GEPA-lite."""
    run_id: str
    base_prompt: str
    failure_patterns: list[FailurePattern] = field(default_factory=list)
    variants: list[PromptVariant] = field(default_factory=list)
    eval_results: list[EvalResult] = field(default_factory=list)
    winner_variant_id: str = ""
    improvement_delta: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Failure Pattern Extractor (heuristic) ────────────────────────────────────

_FAILURE_KEYWORDS: dict[str, tuple[str, str]] = {
    "kurang_sanad": (
        r"\b(tidak ada sumber|tanpa sanad|kurang rujukan|tidak menyebutkan sumber|tidak ada referensi)\b",
        "Tambahkan instruksi eksplisit untuk selalu menyertakan sanad/sumber."
    ),
    "terlalu_panjang": (
        r"\b(terlalu panjang|bertele-tele|bisa lebih ringkas|terlalu banyak kata)\b",
        "Tambahkan instruksi untuk jawaban ringkas dan langsung ke poin."
    ),
    "tidak_relevan": (
        r"\b(tidak relevan|kurang tepat|menyimpang|tidak menjawab pertanyaan)\b",
        "Perkuat instruksi untuk fokus pada pertanyaan user, hindari tangensial."
    ),
    "terlalu_umum": (
        r"\b(terlalu umum|terlalu umum|kurang spesifik|perlu lebih detail)\b",
        "Tambahkan instruksi untuk jawaban spesifik dengan contoh konkret."
    ),
    "tone_tidak_sesuai": (
        r"\b(tone|nada|terlalu formal|terlalu santai|kurang sopan)\b",
        "Tambahkan instruksi untuk menyesuaikan tone dengan konteks user."
    ),
    "epistemik_tidak_jelas": (
        r"\b(tidak jelas fakta|opini|spekulasi|tidak ada label)\b",
        "Perkuat instruksi epistemik: label [FACT]/[OPINION]/[SPECULATION] wajib."
    ),
}


def extract_failure_patterns(feedback_items: list[dict]) -> list[FailurePattern]:
    """
    Ekstrak pola kegagalan dari feedback items (thumbs_down + komentar).

    Args:
        feedback_items: list dict dengan keys: query, response, rating, comment (optional)

    Returns:
        list FailurePattern yang terurut by frequency desc
    """
    patterns: dict[str, FailurePattern] = {}

    for item in feedback_items:
        text = f"{item.get('query', '')} {item.get('response', '')} {item.get('comment', '')}"
        text_lower = text.lower()

        for pattern_id, (regex, suggested_fix) in _FAILURE_KEYWORDS.items():
            if re.search(regex, text_lower, re.IGNORECASE):
                if pattern_id in patterns:
                    patterns[pattern_id].frequency += 1
                else:
                    patterns[pattern_id] = FailurePattern(
                        pattern_id=pattern_id,
                        description=pattern_id.replace("_", " ").title(),
                        frequency=1,
                        suggested_fix=suggested_fix,
                    )

    return sorted(patterns.values(), key=lambda p: p.frequency, reverse=True)


# ── Prompt Mutator (genetic-style) ───────────────────────────────────────────

_MUTATION_TEMPLATES: list[tuple[str, str]] = [
    (
        "ADD_CONSTRAINT",
        "Tambahkan constraints berikut ke system prompt:\n{fix}",
    ),
    (
        "REORDER_EMPHASIS",
        "Pindahkan kalimat paling penting ke awal paragraph. Prioritaskan: {fix}",
    ),
    (
        "SPECIFY_FORMAT",
        "Tambahkan contoh format output yang diharapkan. Fokus: {fix}",
    ),
    (
        "STRENGTHEN_RULE",
        "Perkuat rule existing dengan ALL-CAPS emphasis. Pesan: {fix}",
    ),
    (
        "ADD_EXAMPLE",
        "Tambahkan one-shot example yang menunjukkan {fix}",
    ),
    (
        "NEGATIVE_PROMPT",
        "Tambahkan negative prompt: 'Hindari: {anti_pattern}'",
    ),
]


def _generate_variant_id() -> str:
    return f"v{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"


def mutate_prompt(base_prompt: str, failure_patterns: list[FailurePattern], count: int = MUTATION_COUNT) -> list[PromptVariant]:
    """
    Generate prompt variations berdasarkan failure patterns.

    Args:
        base_prompt: system prompt dasar
        failure_patterns: pola kegagalan yang terdeteksi
        count: berapa variasi yang di-generate

    Returns:
        list PromptVariant
    """
    variants: list[PromptVariant] = []
    fixes = [p.suggested_fix for p in failure_patterns[:3] if p.suggested_fix]  # top-3 fixes

    if not fixes:
        # Kalau tidak ada pattern spesifik, generate variasi generic
        fixes = [
            "Jawaban harus ringkas, akurat, dan selalu menyertakan sanad bila ada.",
            "Gunakan format terstruktur dengan pemisah yang jelas antar poin.",
            "Sesuaikan depth penjelasan dengan tingkat literasi user.",
        ]

    for i in range(count):
        mutation_type, mutation_desc = random.choice(_MUTATION_TEMPLATES)
        fix = fixes[i % len(fixes)]

        if mutation_type == "ADD_CONSTRAINT":
            mutated = base_prompt + f"\n\n[CONSTRAINT] {fix}"
        elif mutation_type == "REORDER_EMPHASIS":
            mutated = f"[PRIORITY] {fix}\n\n{base_prompt}"
        elif mutation_type == "SPECIFY_FORMAT":
            mutated = base_prompt + f"\n\n[FORMAT] Pastikan output mengikuti: {fix}"
        elif mutation_type == "STRENGTHEN_RULE":
            mutated = base_prompt + f"\n\n[WAJIB] {fix.upper()}"
        elif mutation_type == "ADD_EXAMPLE":
            mutated = base_prompt + f"\n\n[CONTOH] Berikut contoh yang benar: {fix}"
        elif mutation_type == "NEGATIVE_PROMPT":
            anti = fix.replace("Tambahkan", "Kurangi").replace("Perkuat", "Hindari")
            mutated = base_prompt + f"\n\n[HINDARI] {anti}"
        else:
            mutated = base_prompt

        variants.append(PromptVariant(
            variant_id=_generate_variant_id(),
            system_prompt=mutated,
            mutations_applied=[mutation_type, fix[:50]],
        ))

    return variants


# ── Evaluator (lightweight A/B test) ─────────────────────────────────────────

def evaluate_variant(
    variant: PromptVariant,
    benchmark_items: list[dict],
    mock_eval: bool = True,
) -> EvalResult:
    """
    Evaluasi satu prompt variant pada held-out benchmark subset.

    Args:
        variant: PromptVariant yang akan di-test
        benchmark_items: list dict dengan keys: question, expected_answer, domain
        mock_eval: jika True, gunakan heuristic scoring (tidak perlu LLM call)

    Returns:
        EvalResult dengan accuracy, token efficiency, pareto score
    """
    t0 = time.time()

    if not benchmark_items:
        return EvalResult(variant_id=variant.variant_id, accuracy_score=0.0, avg_tokens=0.0, token_efficiency=0.0, pareto_score=0.0)

    scores = []
    tokens = []

    for item in benchmark_items:
        question = item.get("question", "")
        expected = item.get("expected_answer", "")
        domain = item.get("domain", "general")

        if mock_eval:
            # Heuristic: score berdasarkan keyword overlap + length ratio
            # Ini adalah mock — di production, gunakan eval_harness.py atau llm_judge.py
            q_words = set(re.findall(r"\w+", question.lower()))
            e_words = set(re.findall(r"\w+", expected.lower()))
            overlap = len(q_words & e_words) / max(len(q_words), 1)

            # Simulasi: variant dengan constraint lebih spesifik = score lebih tinggi
            # (asumsi: mutasi yang menambah constraint meningkatkan relevansi)
            constraint_bonus = 0.1 if "[CONSTRAINT]" in variant.system_prompt else 0.0
            format_bonus = 0.05 if "[FORMAT]" in variant.system_prompt else 0.0

            score = min(1.0, overlap + constraint_bonus + format_bonus + 0.3)
            token_count = len(variant.system_prompt.split()) + len(expected.split())
        else:
            # Production: panggil eval_harness.evaluate_response() atau llm_judge
            # Ini placeholder untuk integration
            score = 0.5
            token_count = 100

        scores.append(score)
        tokens.append(token_count)

    avg_accuracy = sum(scores) / len(scores)
    avg_tokens = sum(tokens) / len(tokens)

    # Token efficiency: higher accuracy with fewer tokens = better
    # Normalized: ideal_token ~ 200, lebih sedikit = lebih efisien
    ideal_token = 200.0
    token_eff = min(1.0, ideal_token / max(avg_tokens, 1.0))

    pareto = ACCURACY_WEIGHT * avg_accuracy + TOKEN_EFF_WEIGHT * token_eff

    return EvalResult(
        variant_id=variant.variant_id,
        accuracy_score=round(avg_accuracy, 3),
        avg_tokens=round(avg_tokens, 1),
        token_efficiency=round(token_eff, 3),
        pareto_score=round(pareto, 3),
        benchmark_size=len(benchmark_items),
        elapsed_s=round(time.time() - t0, 2),
    )


# ── Pareto Selector ──────────────────────────────────────────────────────────

def select_pareto_winner(eval_results: list[EvalResult]) -> EvalResult | None:
    """
    Pilih winner berdasarkan Pareto dominance.
    Winner = eval result dengan pareto_score tertinggi.
    """
    if not eval_results:
        return None
    return max(eval_results, key=lambda r: r.pareto_score)


# ── Main API ─────────────────────────────────────────────────────────────────

def run_gepa_lite(
    base_prompt: str,
    feedback_items: list[dict],
    benchmark_items: list[dict] | None = None,
    mock_eval: bool = True,
) -> GEPARun:
    """
    Jalankan satu iterasi GEPA-lite lengkap.

    Args:
        base_prompt: system prompt dasar SIDIX
        feedback_items: list feedback (thumbs_down, komentar, dll)
        benchmark_items: held-out benchmark (jika None, generate synthetic)
        mock_eval: True untuk heuristic eval, False untuk eval_harness integration

    Returns:
        GEPARun dengan winner variant dan improvement delta
    """
    run_id = _generate_variant_id()
    logger.info(f"[GEPA] Starting run {run_id} with {len(feedback_items)} feedback items")

    # 1. COLLECT + ANALYZE
    patterns = extract_failure_patterns(feedback_items)
    logger.info(f"[GEPA] Extracted {len(patterns)} failure patterns")

    if len(patterns) < MIN_FAILURES_TO_RUN and len(feedback_items) < MIN_FAILURES_TO_RUN:
        logger.info(f"[GEPA] Too few failures ({len(feedback_items)}), skipping optimization")
        return GEPARun(
            run_id=run_id,
            base_prompt=base_prompt,
            failure_patterns=patterns,
            winner_variant_id="",
            improvement_delta=0.0,
        )

    # 2. MUTATE
    variants = mutate_prompt(base_prompt, patterns, count=MUTATION_COUNT)
    logger.info(f"[GEPA] Generated {len(variants)} prompt variants")

    # 3. EVAL
    if benchmark_items is None:
        # Generate synthetic benchmark dari feedback items
        benchmark_items = [
            {"question": f["query"], "expected_answer": f.get("expected", ""), "domain": "general"}
            for f in feedback_items[:10]
        ]

    # Split benchmark: held-out subset
    held_out_size = max(1, int(len(benchmark_items) * HELD_OUT_RATIO))
    held_out = benchmark_items[:held_out_size]

    eval_results = []
    for variant in variants:
        result = evaluate_variant(variant, held_out, mock_eval=mock_eval)
        eval_results.append(result)
        logger.info(f"[GEPA] Variant {variant.variant_id}: accuracy={result.accuracy_score}, "
                    f"tokens={result.avg_tokens}, pareto={result.pareto_score}")

    # 4. SELECT
    winner = select_pareto_winner(eval_results)
    base_result = evaluate_variant(
        PromptVariant(variant_id="base", system_prompt=base_prompt),
        held_out,
        mock_eval=mock_eval,
    )

    improvement = 0.0
    if winner:
        improvement = round(winner.pareto_score - base_result.pareto_score, 3)
        logger.info(f"[GEPA] Winner: {winner.variant_id} with pareto={winner.pareto_score}, "
                    f"improvement={improvement:+.3f}")
    else:
        logger.info("[GEPA] No winner selected")

    gepa_run = GEPARun(
        run_id=run_id,
        base_prompt=base_prompt,
        failure_patterns=patterns,
        variants=variants,
        eval_results=eval_results,
        winner_variant_id=winner.variant_id if winner else "",
        improvement_delta=improvement,
    )

    # Persist
    _persist_run(gepa_run)
    return gepa_run


def _persist_run(run: GEPARun) -> Path:
    """Simpan GEPARun ke JSON."""
    path = _GEPA_DIR / f"run_{run.run_id}.json"
    path.write_text(json.dumps(asdict(run), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _dict_to_gepa_run(data: dict) -> GEPARun:
    """Rekonstruksi GEPARun dari dict (nested dataclass conversion)."""
    patterns = [FailurePattern(**p) for p in data.get("failure_patterns", [])]
    variants = [PromptVariant(**v) for v in data.get("variants", [])]
    eval_results = [EvalResult(**e) for e in data.get("eval_results", [])]
    return GEPARun(
        run_id=data["run_id"],
        base_prompt=data["base_prompt"],
        failure_patterns=patterns,
        variants=variants,
        eval_results=eval_results,
        winner_variant_id=data.get("winner_variant_id", ""),
        improvement_delta=data.get("improvement_delta", 0.0),
        timestamp=data.get("timestamp", ""),
    )


def list_recent_runs(n: int = 5) -> list[GEPARun]:
    """List N GEPARun terbaru."""
    runs = []
    for path in sorted(_GEPA_DIR.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]:
        data = json.loads(path.read_text(encoding="utf-8"))
        runs.append(_dict_to_gepa_run(data))
    return runs


def get_best_prompt(run_id: str | None = None) -> str:
    """
    Ambil system prompt terbaik dari GEPA run.
    Jika run_id None, ambil dari run terbaru yang punya winner.
    """
    if run_id:
        path = _GEPA_DIR / f"run_{run_id}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            run = _dict_to_gepa_run(data)
            for v in run.variants:
                if v.variant_id == run.winner_variant_id:
                    return v.system_prompt
        return ""

    # Ambil dari run terbaru dengan winner
    for run in list_recent_runs(n=10):
        if run.winner_variant_id:
            for v in run.variants:
                if v.variant_id == run.winner_variant_id:
                    return v.system_prompt
    return ""


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== GEPA-lite Self-Test ===\n")

    # Test 1: Extract failure patterns
    feedback = [
        {"query": "q1", "response": "r1", "rating": -1, "comment": "tidak ada sumbernya"},
        {"query": "q2", "response": "r2", "rating": -1, "comment": "terlalu panjang jawabannya"},
        {"query": "q3", "response": "r3", "rating": -1, "comment": "kurang rujukan"},
    ]
    patterns = extract_failure_patterns(feedback)
    print(f"[1] Patterns: {len(patterns)}")
    for p in patterns:
        print(f"    - {p.pattern_id}: freq={p.frequency}, fix={p.suggested_fix[:50]}")
    assert len(patterns) >= 1
    print("    OK\n")

    # Test 2: Mutate prompt
    base = "Kamu adalah SIDIX. Jawab dengan akurat dan beradab."
    variants = mutate_prompt(base, patterns, count=3)
    print(f"[2] Variants: {len(variants)}")
    for v in variants:
        print(f"    - {v.variant_id}: mutations={v.mutations_applied}")
    assert len(variants) == 3
    print("    OK\n")

    # Test 3: Full run (mock eval)
    benchmark = [
        {"question": "Apa itu SIDIX?", "expected_answer": "SIDIX adalah AI assistant.", "domain": "general"},
        {"question": "Jelaskan Maqashid.", "expected_answer": "Maqashid adalah tujuan syariah.", "domain": "islamic"},
    ]
    run = run_gepa_lite(base, feedback, benchmark, mock_eval=True)
    print(f"[3] GEPA Run: {run.run_id}")
    print(f"    Winner: {run.winner_variant_id}")
    print(f"    Improvement: {run.improvement_delta:+.3f}")
    assert run.run_id
    print("    OK\n")

    # Test 4: Persist + retrieve
    recent = list_recent_runs(n=1)
    print(f"[4] Recent runs: {len(recent)}")
    if recent:
        best = get_best_prompt(recent[0].run_id)
        print(f"    Best prompt length: {len(best)} chars")
    print("    OK\n")

    print("[OK] All GEPA-lite self-tests passed")
