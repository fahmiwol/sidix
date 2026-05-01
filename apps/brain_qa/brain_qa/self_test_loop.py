"""
self_test_loop.py — Sprint F: Self-Test Loop (Cold Start Maturity)

Arsitektur:
  Self-Test Loop = closed-loop evaluation engine yang membuat SIDIX
  bisa "belajar sendiri" tanpa intervensi user.

Flow:
  1. Generate test questions (LLM + template domains)
  2. Execute each through OMNYX pipeline (holistic mode)
  3. Score result (Sanad + composite criteria)
  4. Store to Hafidz (Golden >= threshold, Lesson < threshold)
  5. Update stats & history

Trigger:
  - Manual: POST /agent/selftest/run
  - Scheduled: cron / background task (future)
  - Post-Pencipta: auto-run setelah creative output generated

Storage:
  - Results: brain/public/selftest/results.jsonl (append-only)
  - Stats: computed on-demand dari results.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("sidix.selftest")


# ── Storage Root ─────────────────────────────────────────────────────────

SELFTEST_ROOT = Path("brain/public/selftest")
RESULTS_PATH = SELFTEST_ROOT / "results.jsonl"


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class SelfTestResult:
    """Single self-test run result."""
    test_id: str
    question: str
    answer: str
    persona: str
    sanad_score: float
    sanad_verdict: str
    complexity: str
    duration_ms: int
    sources_used: list[str]
    composite_score: float
    stored_to: str  # "golden", "lesson", or "none"
    timestamp: str
    metadata: dict = field(default_factory=dict)


# ── Question Generation ──────────────────────────────────────────────────

DEFAULT_DOMAINS = [
    "factual_indonesia",      # sejarah, geografi, politik Indonesia
    "factual_science",        # sains, teknik, matematika
    "factual_islam",          # fiqih, tafsir, sejarah Islam
    "creative_writing",       # puisi, cerpen, copywriting
    "coding_python",          # Python, algorithm, data structure
    "business_strategy",      # marketing, finance, operations
    "ethical_dilemma",        # maqashid-aligned ethical reasoning
]

_QUESTION_PROMPT_TEMPLATE = """Kamu adalah evaluator kualitas AI. Buat {n} pertanyaan uji yang beragam untuk menguji kemampuan AI agent.

Domain yang tersedia: {domains}

Instruksi:
- Setiap pertanyaan harus jelas, spesifik, dan bisa diverifikasi jawabannya
- Variasikan tingkat kesulitan: 40% simple, 40% analytical, 20% creative
- Bahasa Indonesia
- Format: satu pertanyaan per baris, tanpa nomor, tanpa bullet
- Tidak ada penjelasan tambahan

Contoh pertanyaan bagus:
Siapa presiden Indonesia ke-4 dan apa program utamanya?
Bagaimana cara kerja algoritma Dijkstra dalam menemukan jalur terpendek?
Apa hukum zakat profesi menurut mazhab Syafi'i?

Buat {n} pertanyaan sekarang:"""


async def generate_test_questions(
    n: int = 5,
    domains: list[str] | None = None,
) -> list[str]:
    """Generate diverse test questions via LLM."""
    domains = domains or DEFAULT_DOMAINS[:5]
    prompt = _QUESTION_PROMPT_TEMPLATE.format(n=n, domains=", ".join(domains))

    try:
        from .ollama_llm import ollama_generate
        response, _mode = await asyncio.to_thread(
            ollama_generate,
            prompt,
            system="",
            model="qwen2.5:1.5b",  # light model untuk generation
            max_tokens=800,
            temperature=0.8,
        )
    except Exception as e:
        log.warning("[selftest] LLM question generation failed: %s", e)
        # Fallback: template-based questions
        return _fallback_questions(n)

    # Parse questions — satu per baris, filter kosong
    questions = [
        line.strip("-• \t0123456789.")
        for line in response.splitlines()
        if line.strip() and len(line.strip()) > 15 and not line.strip().lower().startswith(("contoh", "buat", "domain", "instruksi", "format"))
    ]
    return questions[:n] if questions else _fallback_questions(n)


def _fallback_questions(n: int) -> list[str]:
    """Template fallback questions kalau LLM gagal."""
    pool = [
        "Siapa presiden Indonesia pertama dan tahun berapa menjabat?",
        "Jelaskan cara kerja mesin jet engine dalam bahasa sederhana.",
        "Apa hukum puasa Ramadhan bagi orang yang sedang sakit?",
        "Tulis sebuah pantun 4 baris tentang teknologi dan alam.",
        "Bagaimana cara mengimplementasikan binary search di Python?",
        "Apa strategi marketing yang paling efektif untuk startup SaaS?",
        "Jika sebuah perusahaan AI bisa menggantikan 50% pekerjaan, apa tanggung jawab etisnya?",
        "Berapa luas Indonesia dan berapa jumlah provinsinya saat ini?",
        "Jelaskan teori relativitas Einstein dalam satu paragraf.",
        "Apa perbedaan zakat fitrah dan zakat mal?",
    ]
    return pool[:n]


# ── Single Test Execution ────────────────────────────────────────────────

async def run_single_self_test(
    question: str,
    persona: str = "AYMAN",
) -> SelfTestResult:
    """Run one question through OMNYX pipeline and evaluate."""
    from .omnyx_direction import omnyx_process
    from .sanad_orchestra import get_threshold

    t0 = time.monotonic()
    log.info("[selftest] Running: %r", question[:60])

    try:
        result = await omnyx_process(question, persona=persona)
    except Exception as e:
        log.error("[selftest] OMNYX failed: %s", e)
        return SelfTestResult(
            test_id=f"st_{uuid.uuid4().hex[:8]}",
            question=question,
            answer="",
            persona=persona,
            sanad_score=0.0,
            sanad_verdict="fail",
            complexity="unknown",
            duration_ms=0,
            sources_used=[],
            composite_score=0.0,
            stored_to="none",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"error": str(e)},
        )

    duration_ms = int((time.monotonic() - t0) * 1000)
    sanad_score = result.get("sanad_score", 0.0)
    sanad_verdict = result.get("sanad_verdict", "unknown")
    complexity = result.get("complexity", "analytical")
    sources_used = result.get("sources_used", [])

    # Composite score: Sanad (70%) + source diversity (20%) + speed (10%)
    source_bonus = min(1.0, len(set(sources_used)) / 3.0) * 0.2
    speed_bonus = 0.1 if duration_ms < 30000 else (0.05 if duration_ms < 60000 else 0.0)
    composite = (sanad_score * 0.7) + source_bonus + speed_bonus
    composite = round(min(1.0, composite), 3)

    # Determine threshold untuk storage
    threshold = get_threshold(complexity, sources_used)
    stored_to = "golden" if composite >= threshold else "lesson"

    # Store ke Hafidz
    try:
        from .hafidz_injector import HafidzInjector
        hafidz = HafidzInjector()
        store_result = await hafidz.store_result(
            query=question,
            answer=result.get("answer", ""),
            persona=persona,
            sanad_score=composite,  # use composite sebagai sanad_score
            threshold=threshold,
            sources_used=sources_used,
            tools_used=result.get("tools_used", []),
            failure_context="" if composite >= threshold else f"Self-test composite {composite:.2f} below threshold {threshold:.2f}",
            metadata={
                "test_type": "self_test",
                "complexity": complexity,
                "duration_ms": duration_ms,
            },
        )
        stored_to = store_result.get("store", stored_to)
    except Exception as e:
        log.warning("[selftest] Hafidz store failed: %s", e)
        stored_to = "none"

    test_result = SelfTestResult(
        test_id=f"st_{uuid.uuid4().hex[:8]}",
        question=question,
        answer=result.get("answer", ""),
        persona=persona,
        sanad_score=sanad_score,
        sanad_verdict=sanad_verdict,
        complexity=complexity,
        duration_ms=duration_ms,
        sources_used=sources_used,
        composite_score=composite,
        stored_to=stored_to,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata={
            "synth_model": result.get("synth_model", ""),
            "hafidz_injected": result.get("hafidz_injected", False),
            "hafidz_stored": result.get("hafidz_stored", False),
        },
    )

    # Persist ke JSONL
    _persist_result(test_result)
    log.info("[selftest] Done: %s | composite=%.2f | stored=%s | %dms",
             test_result.test_id, composite, stored_to, duration_ms)
    return test_result


# ── Batch Execution ──────────────────────────────────────────────────────

async def run_batch_self_test(
    n: int = 5,
    domains: list[str] | None = None,
    persona: str = "AYMAN",
) -> list[SelfTestResult]:
    """Generate n questions and run self-test on each."""
    questions = await generate_test_questions(n, domains)
    log.info("[selftest] Batch started: %d questions", len(questions))

    results: list[SelfTestResult] = []
    for q in questions:
        result = await run_single_self_test(q, persona=persona)
        results.append(result)
        # Small delay untuk tidak overwhelm CPU
        await asyncio.sleep(0.5)

    log.info("[selftest] Batch complete: %d tests, avg composite=%.2f",
             len(results),
             sum(r.composite_score for r in results) / max(len(results), 1))
    return results


# ── Persistence ──────────────────────────────────────────────────────────

def _persist_result(result: SelfTestResult) -> None:
    """Append result to results.jsonl."""
    try:
        SELFTEST_ROOT.mkdir(parents=True, exist_ok=True)
        with RESULTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.__dict__, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[selftest] Persist failed: %s", e)


# ── Stats & History ──────────────────────────────────────────────────────

def get_self_test_history(limit: int = 20) -> list[dict]:
    """Read recent self-test results."""
    if not RESULTS_PATH.exists():
        return []
    lines = RESULTS_PATH.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines[-limit:]:
        try:
            results.append(json.loads(line))
        except Exception:
            continue
    return list(reversed(results))


def get_self_test_stats() -> dict:
    """Aggregate stats dari semua results."""
    if not RESULTS_PATH.exists():
        return {
            "total_tests": 0,
            "golden": 0,
            "lesson": 0,
            "avg_composite": 0.0,
            "avg_sanad": 0.0,
            "avg_duration_ms": 0,
            "by_complexity": {},
            "by_persona": {},
        }

    total = 0
    golden = 0
    lesson = 0
    composites = []
    sanads = []
    durations = []
    by_complexity: dict[str, list[float]] = {}
    by_persona: dict[str, list[float]] = {}

    for line in RESULTS_PATH.read_text(encoding="utf-8").strip().splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        total += 1
        comp = r.get("composite_score", 0.0)
        sanad = r.get("sanad_score", 0.0)
        dur = r.get("duration_ms", 0)
        composites.append(comp)
        sanads.append(sanad)
        durations.append(dur)

        if r.get("stored_to") == "golden":
            golden += 1
        elif r.get("stored_to") == "lesson":
            lesson += 1

        cx = r.get("complexity", "unknown")
        by_complexity.setdefault(cx, []).append(comp)
        pr = r.get("persona", "unknown")
        by_persona.setdefault(pr, []).append(comp)

    n = max(total, 1)
    return {
        "total_tests": total,
        "golden": golden,
        "lesson": lesson,
        "avg_composite": round(sum(composites) / n, 3),
        "avg_sanad": round(sum(sanads) / n, 3),
        "avg_duration_ms": int(sum(durations) / n),
        "by_complexity": {k: {"n": len(v), "avg": round(sum(v) / len(v), 3)} for k, v in by_complexity.items()},
        "by_persona": {k: {"n": len(v), "avg": round(sum(v) / len(v), 3)} for k, v in by_persona.items()},
    }
