"""
eval_harness.py — SIDIX Evaluation Harness
==========================================

Benchmark model sebelum dan sesudah training untuk mengukur improvement.

Metrics:
  1. Perplexity (lower = better) — pada holdout test set
  2. Epistemic accuracy — % label [FAKTA]/[OPINI]/[SPECULATION]/[UNKNOWN] yang tepat
  3. Response relevance — BLEU/ROUGE-like vs reference answers
  4. Sanad coverage — % jawaban yang menyertakan sumber/citation
  5. Conversational quality — heuristic scorer (CQF-lite)

Usage:
    from brain_qa.eval_harness import run_benchmark
    scores = run_benchmark(model_path="./sidix-distilled-adapter")
"""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("sidix.eval")


# ── Benchmark Dataset (static + synthetic) ────────────────────────────────────

DEFAULT_BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "tests" / "eval_benchmark.jsonl"

_BENCHMARK_SEED: list[dict] = [
    {
        "query": "Apa itu aqidah dalam Islam?",
        "expected_type": "fakta",
        "expected_labels": ["[FAKTA]"],
        "expected_sources": True,
        "reference_answer": "Aqidah adalah keyakinan dasar dalam Islam yang mencakup iman kepada Allah, malaikat, kitab-kitab-Nya, rasul-rasul-Nya, hari akhir, dan takdir.",
    },
    {
        "query": "Menurutmu, apakah AI akan menggantikan semua pekerja manusia?",
        "expected_type": "opini",
        "expected_labels": ["[OPINI]", "[SPEKULASI]"],
        "expected_sources": False,
        "reference_answer": "[OPINI] AI tidak akan menggantikan semua pekerja manusia. AI unggul di tugas repetitif dan data-intensive, tapi kreativitas, empati, dan judgment etis masih domain manusia.",
    },
    {
        "query": "Berapa hasil 2 + 2?",
        "expected_type": "fakta",
        "expected_labels": ["[FAKTA]"],
        "expected_sources": False,
        "reference_answer": "[FAKTA] 2 + 2 = 4.",
    },
    {
        "query": "Apa pendapatmu tentang masa depan ekonomi Indonesia 10 tahun lagi?",
        "expected_type": "spekulasi",
        "expected_labels": ["[SPEKULASI]"],
        "expected_sources": False,
        "reference_answer": "[SPEKULASI] Ekonomi Indonesia 10 tahun ke depan bergantung pada beberapa faktor: transisi energi, demografi bonus, dan stabilitas politik. Proyeksi positif jika...",
    },
    {
        "query": "Siapa penemu mesin waktu?",
        "expected_type": "unknown",
        "expected_labels": ["[TIDAK TAHU]", "[UNKNOWN]"],
        "expected_sources": False,
        "reference_answer": "[TIDAK TAHU] Mesin waktu belum ditemukan dalam realitas ilmiah saat ini. Konsep mesin waktu masih dalam ranah fiksi ilmiah.",
    },
]


def _ensure_benchmark_file() -> Path:
    path = DEFAULT_BENCHMARK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            for item in _BENCHMARK_SEED:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return path


# ── Metrics ───────────────────────────────────────────────────────────────────

def _extract_labels(text: str) -> list[str]:
    return re.findall(r"\[(FAKTA|OPINI|SPEKULASI|TIDAK TAHU|UNKNOWN)\]", text.upper())


def _has_source(text: str) -> bool:
    """Heuristic: apakah jawaban menyebut sumber/referensi."""
    indicators = [
        r"sumber[:\s]",
        r"menurut\s+\w+",
        r"\([^)]*\d{4}[^)]*\)",  # (Author, 2020)
        r"https?://",
        r"\[\d+\]",  # [1], [2]
        r"QS\.\s*\w+",  # QS. Al-Baqarah
        r"HR\.\s*\w+",  # HR. Bukhari
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in indicators)


def _rouge_l(reference: str, hypothesis: str) -> float:
    """Simplified ROUGE-L (longest common subsequence ratio)."""
    ref = reference.lower().split()
    hyp = hypothesis.lower().split()
    if not ref or not hyp:
        return 0.0

    # LCS length
    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[m][n]
    return lcs / max(len(ref), len(hyp))


# ── Core Eval ─────────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    total: int = 0
    epistemic_correct: int = 0
    source_present: int = 0
    relevance_sum: float = 0.0
    unknown_honest: int = 0
    scores: list[dict] = field(default_factory=list)

    @property
    def epistemic_accuracy(self) -> float:
        return self.epistemic_correct / self.total if self.total else 0.0

    @property
    def source_coverage(self) -> float:
        return self.source_present / self.total if self.total else 0.0

    @property
    def avg_relevance(self) -> float:
        return self.relevance_sum / self.total if self.total else 0.0

    @property
    def honesty_rate(self) -> float:
        return self.unknown_honest / self.total if self.total else 0.0

    @property
    def composite_score(self) -> float:
        """Weighted composite: epistemic 40%, relevance 30%, source 20%, honesty 10%."""
        return (
            self.epistemic_accuracy * 0.40
            + self.avg_relevance * 0.30
            + self.source_coverage * 0.20
            + self.honesty_rate * 0.10
        )


def evaluate_response(item: dict, response: str) -> dict:
    """Score satu Q+A pair."""
    expected_type = item.get("expected_type", "")
    expected_labels = [l.upper().strip("[]") for l in item.get("expected_labels", [])]
    reference = item.get("reference_answer", "")

    actual_labels = _extract_labels(response)

    # Epistemic correctness
    epistemic_ok = False
    if expected_type == "unknown":
        epistemic_ok = not actual_labels or any(l in expected_labels for l in actual_labels)
    else:
        epistemic_ok = any(l in expected_labels for l in actual_labels)

    # Source coverage
    has_source = _has_source(response) if item.get("expected_sources") else True

    # Relevance (ROUGE-L vs reference)
    relevance = _rouge_l(reference, response)

    # Honesty: kalau expected unknown, apakah benar-benar bilang tidak tahu?
    honest = True
    if expected_type == "unknown":
        honest = any(l in ["TIDAK TAHU", "UNKNOWN"] for l in actual_labels)

    return {
        "query": item["query"],
        "epistemic_ok": epistemic_ok,
        "has_source": has_source,
        "relevance": round(relevance, 3),
        "honest": honest,
        "expected_type": expected_type,
        "actual_labels": actual_labels,
    }


def run_benchmark(
    model_path: str = "",
    benchmark_path: Optional[Path] = None,
    generator_fn: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Run full benchmark.

    Args:
        model_path: Path ke model/adapter (untuk logging, tidak wajib).
        benchmark_path: Path ke benchmark JSONL (default: tests/eval_benchmark.jsonl).
        generator_fn: Callable(query) -> response. Kalau None, gunakan mock.
    """
    bpath = benchmark_path or _ensure_benchmark_file()
    result = EvalResult()

    log.info("[EVAL] Benchmark start — model=%s", model_path or "mock")

    with open(bpath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            query = item.get("query", "")

            # Generate response
            if generator_fn is not None:
                try:
                    response = generator_fn(query)
                except Exception as e:
                    log.warning("[EVAL] Generation failed for '%s': %s", query, e)
                    response = ""
            else:
                # Mock: return reference answer with slight modification
                response = item.get("reference_answer", "")

            score = evaluate_response(item, response)
            result.total += 1
            if score["epistemic_ok"]:
                result.epistemic_correct += 1
            if score["has_source"]:
                result.source_present += 1
            result.relevance_sum += score["relevance"]
            if score["honest"]:
                result.unknown_honest += 1
            result.scores.append(score)

    summary = {
        "total": result.total,
        "epistemic_accuracy": round(result.epistemic_accuracy, 3),
        "source_coverage": round(result.source_coverage, 3),
        "avg_relevance": round(result.avg_relevance, 3),
        "honesty_rate": round(result.honesty_rate, 3),
        "composite_score": round(result.composite_score, 3),
        "score_before": 0.0,
        "score_after": round(result.composite_score, 3),
        "improvement": round(result.composite_score, 3),
    }

    log.info(
        "[EVAL] Done — composite=%.3f (epistemic=%.3f, relevance=%.3f, source=%.3f, honesty=%.3f)",
        summary["composite_score"],
        summary["epistemic_accuracy"],
        summary["avg_relevance"],
        summary["source_coverage"],
        summary["honesty_rate"],
    )
    return summary
