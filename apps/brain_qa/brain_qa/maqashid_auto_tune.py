"""
maqashid_auto_tune.py — Sprint G: Maqashid Auto-Tune + Self-Evaluation Middleware

Arsitektur:
  Maqashid Auto-Tune = closed-loop optimizer untuk 5-sumbu Maqashid filter.
  Data driver: self-test results (brain/public/selftest/results.jsonl)
  Output: tuned weight profile yang bisa di-apply ke evaluator.

  Maqashid Auto-Tune Middleware = self-evaluation layer yang intercept output
  SEBELUM dikirim ke user. Heuristic-only (no LLM API calls). Fail-open.

Flow:
  1. Read self-test history
  2. For each result, run Maqashid evaluation on (question, answer)
  3. Track per-axis fail/warn/pass rates
  4. Compute adjusted weights (axes with high fail rate → increase weight)
  5. Store tuned profile
  6. Apply tuned profile to future evaluations

Storage:
  - Tuned profile: brain/public/maqashid/tuned_profile.json
  - History: brain/public/maqashid/tune_history.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel
    _PYDANTIC_OK = True
except Exception:
    _PYDANTIC_OK = False
    BaseModel = object  # type: ignore[assignment, misc]

log = logging.getLogger("sidix.maqashid_tune")


# ── Storage ──────────────────────────────────────────────────────────────

TUNE_ROOT = Path("brain/public/maqashid")
TUNED_PROFILE_PATH = TUNE_ROOT / "tuned_profile.json"
TUNE_HISTORY_PATH = TUNE_ROOT / "tune_history.jsonl"
SELFTEST_RESULTS_PATH = Path("brain/public/selftest/results.jsonl")

# ── Default Weights (baseline from IHOS) ─────────────────────────────────

DEFAULT_WEIGHTS = {
    "life": 1.0,
    "intellect": 1.0,
    "faith": 0.8,
    "lineage": 0.6,
    "wealth": 0.7,
}


# ════════════════════════════════════════════════════════════════════════
# SELF-EVALUATION MIDDLEWARE (Sprint G+ — Maqashid Auto-Tune)
# ════════════════════════════════════════════════════════════════════════

class AutoTuneResult(BaseModel if _PYDANTIC_OK else object):
    """Hasil evaluasi auto-tune terhadap output teks."""
    score: float = 0.0
    passed: bool = True
    violations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    corrected_output: str | None = None

    if not _PYDANTIC_OK:
        def __init__(
            self,
            score: float = 0.0,
            passed: bool = True,
            violations: list[str] | None = None,
            suggestions: list[str] | None = None,
            corrected_output: str | None = None,
        ):
            self.score = score
            self.passed = passed
            self.violations = violations or []
            self.suggestions = suggestions or []
            self.corrected_output = corrected_output


class AutoTuneConfig(BaseModel if _PYDANTIC_OK else object):
    """Konfigurasi auto-tune middleware."""
    threshold: float = 0.6
    mode: str = "general"
    auto_correct: bool = False
    enabled: bool = True

    if not _PYDANTIC_OK:
        def __init__(
            self,
            threshold: float = 0.6,
            mode: str = "general",
            auto_correct: bool = False,
            enabled: bool = True,
        ):
            self.threshold = threshold
            self.mode = mode
            self.auto_correct = auto_correct
            self.enabled = enabled


# ── Global stats (in-memory, non-blocking) ───────────────────────────────

_AUTO_TUNE_STATS: dict[str, Any] = {
    "total_evaluated": 0,
    "total_passed": 0,
    "total_corrected": 0,
    "score_sum": 0.0,
}


def _bump_stats(passed: bool, corrected: bool, score: float) -> None:
    _AUTO_TUNE_STATS["total_evaluated"] += 1
    if passed:
        _AUTO_TUNE_STATS["total_passed"] += 1
    if corrected:
        _AUTO_TUNE_STATS["total_corrected"] += 1
    _AUTO_TUNE_STATS["score_sum"] += score


def get_global_stats() -> dict[str, Any]:
    total = _AUTO_TUNE_STATS["total_evaluated"] or 1
    return {
        "total_evaluated": _AUTO_TUNE_STATS["total_evaluated"],
        "total_passed": _AUTO_TUNE_STATS["total_passed"],
        "total_corrected": _AUTO_TUNE_STATS["total_corrected"],
        "average_score": round(_AUTO_TUNE_STATS["score_sum"] / total, 3),
    }


# ── Heuristic evaluators (fast, <50ms, no LLM API) ───────────────────────

_HATE_SPEECH_KEYWORDS = {
    "bunuh", "bacok", "tusuk", "bakar", "hancurkan", "habisi", "musnahkan",
    "anjing", "babi", "monyet", "kampret", "bangsat", "tolol", "goblok",
    "bodoh", "idiot", " retard ", "biadab", "jahannam", "laknat",
}

_MISINFO_MARKERS = {
    "pasti", "100%", "seratus persen", "tanpa keraguan", "pasti benar",
    "pasti salah", "jelas sekali", "sudah pasti", "pasti tidak",
    "tidak mungkin salah", "pasti fakta", "fakta mutlak",
}

_ATTRIBUTION_MARKERS = {
    "menurut", "sumber", "kutipan", "dikutip", "berdasarkan",
    "referensi", "bibliografi", "link", "url", "jurnal", "studi",
    "penelitian", "riset", "laporan", "dokumen", "official",
    "kata ", "menyatakan", "mengatakan",
}

_AD_HOMINEM_PATTERNS = [
    re.compile(r"\b(kamu|anda|lu|loe|dia|mereka)\s+(yang|itu|ini)\s+(bodoh|tolol|goblok|idiot|bebal|dungu)\b", re.IGNORECASE),
    re.compile(r"\b(kamu|anda|lu|loe)\s+(tidak|nggak|gak)\s+(ngerti|paham|mengerti|tahu)\b", re.IGNORECASE),
    re.compile(r"\b(si|orang)\s+\w+\s+(yang|itu|ini)\s+(bodoh|tolol|goblok|idiot)\b", re.IGNORECASE),
]

_BRAND_CANON: dict[str, str] = {
    "sidix": "SIDIX adalah AI agent open-source self-hosted dengan prinsip Sidq, Sanad, Tabayyun.",
    "ihos": "IHOS (Islamic Holistic Ontological System) adalah framework epistemologi SIDIX.",
    "maqashid": "Maqashid al-Syariah = objective function ethical AI SIDIX (5 sumbu: jiwa, akal, agama, keturunan, harta).",
}


def _check_hate_speech(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for kw in _HATE_SPEECH_KEYWORDS:
        if kw in lower:
            found.append(f"Kandungan ujaran kebencian / diskriminasi: '{kw}'")
            break  # max 1 violation of this type to keep list short
    return found


def _check_misinformation(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for marker in _MISINFO_MARKERS:
        if marker in lower:
            # Cek apakah ada evidence marker juga
            has_evidence = any(ev in lower for ev in _ATTRIBUTION_MARKERS)
            if not has_evidence:
                found.append(f"Marker keyakinan mutlak ('{marker}') tanpa evidensi — risiko misinformasi")
                break
    return found


def _check_attribution(text: str) -> list[str]:
    lower = text.lower()
    # Hanya flag untuk klaim faktual (angka, tanggal, "adalah", "merupakan")
    has_factual_claim = bool(re.search(r"\b(adalah|merupakan|sebanyak|sekitar\s+\d|\d{4}|tahun\s+\d{4})\b", lower))
    if not has_factual_claim:
        return []
    has_attribution = any(att in lower for att in _ATTRIBUTION_MARKERS)
    if not has_attribution:
        return ["Klaim faktual tanpa atribusi sumber — tambahkan 'menurut ...' atau referensi"]
    return []


def _check_ad_hominem(text: str) -> list[str]:
    found = []
    for pattern in _AD_HOMINEM_PATTERNS:
        if pattern.search(text):
            found.append("Potensi serangan personal (ad hominem) terdeteksi")
            break
    return found


def _check_brand_contradiction(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for term, canon in _BRAND_CANON.items():
        if term in lower:
            # Heuristic sederhana: kalau teks mengandung term tapi juga negasi kuat terhadap canon
            # Ini basic — tidak menangkap semua nuansa tapi cukup untuk backstop
            negation_patterns = [r"bukan\s+.*" + re.escape(term), r"tidak\s+.*" + re.escape(term)]
            for pat in negation_patterns:
                if re.search(pat, lower):
                    found.append(f"Potensi kontradiksi dengan brand canon untuk '{term}'")
                    break
    return found


def evaluate_output(text: str, mode: str = "general") -> AutoTuneResult:
    """
    Evaluasi output berbasis heuristic (no LLM API call).

    Pipeline:
      1. Coba panggil evaluate_maqashid() dari maqashid_profiles kalau tersedia
      2. Fallback ke heuristic evaluator (keyword + pattern)
      3. Return score 0.0–1.0 + violations + suggestions

    Target latency: <50ms.
    Fail-open: kalau error → return passed=True dengan score=0.0.
    """
    t0 = time.time()
    text = (text or "").strip()
    if not text:
        return AutoTuneResult(score=1.0, passed=True)

    violations: list[str] = []
    suggestions: list[str] = []

    # ── Layer 1: existing maqashid_profiles integration ───────────────────
    try:
        from .maqashid_profiles import evaluate_maqashid, maqashid_score_from_content
        mp_result = evaluate_maqashid(user_query="", generated_output=text, persona_name="UTZ")
        mp_status = str(mp_result.get("status", "pass"))
        mp_reasons = mp_result.get("reasons") or []

        if mp_status == "block":
            violations.extend(str(r) for r in mp_reasons)
            suggestions.append("Output diblokir oleh Maqashid gate — revisi total diperlukan")
        elif mp_status == "warn":
            for r in mp_reasons:
                rstr = str(r)
                if "sanad missing" in rstr.lower():
                    suggestions.append("Tambahkan label epistemik [FAKTA]/[OPINI] untuk klaim akademik")
                else:
                    violations.append(rstr)

        base_score = maqashid_score_from_content(text)
    except Exception:
        base_score = 0.5
        mp_status = "pass"

    # ── Layer 2: heuristic checks ─────────────────────────────────────────
    violations.extend(_check_hate_speech(text))
    violations.extend(_check_misinformation(text))
    violations.extend(_check_attribution(text))
    violations.extend(_check_ad_hominem(text))
    violations.extend(_check_brand_contradiction(text))

    # Generate suggestions dari violations
    if any("kebencian" in v or "diskriminasi" in v for v in violations):
        suggestions.append("Hindari bahasa yang menghina atau mendiskriminasi kelompok/individual")
    if any("misinformasi" in v or "keyakinan mutlak" in v for v in violations):
        suggestions.append("Gunakan bahasa yang menunjukkan ketidakpastian ('kemungkinan', 'menurut data ...')")
    if any("atribusi" in v for v in violations):
        suggestions.append("Cantumkan sumber untuk klaim faktual, misalnya 'menurut studi X (2024)'")
    if any("ad hominem" in v for v in violations):
        suggestions.append("Fokuskan argumen pada ide, bukan pada karakter personal")

    # ── Scoring ───────────────────────────────────────────────────────────
    # Start dari base_score (0.0–1.0 dari maqashid_score_from_content)
    # Kurangi 0.15 per violation, floor 0.0
    penalty = len(violations) * 0.15
    score = max(0.0, min(1.0, base_score - penalty))

    # Boost kalau tidak ada violation dan ada attribution
    if not violations and any(a in text.lower() for a in _ATTRIBUTION_MARKERS):
        score = min(1.0, score + 0.1)

    passed = score >= 0.6 and mp_status != "block"

    latency_ms = (time.time() - t0) * 1000
    if latency_ms > 50:
        log.debug("[auto_tune] slow evaluation: %.1fms", latency_ms)

    return AutoTuneResult(
        score=round(score, 3),
        passed=passed,
        violations=violations,
        suggestions=suggestions,
        corrected_output=None,
    )


def auto_tune_response(
    text: str,
    mode: str = "general",
    auto_correct: bool = False,
    config: AutoTuneConfig | None = None,
) -> str:
    """
    Evaluasi output secara internal tanpa membocorkan review ke jawaban publik.

    Auto-Tune adalah evaluator/guardrail, bukan formatter jawaban user. Kalau
    auto_correct=False, return teks asli agar UI chat tetap natural. Jika
    auto_correct=True, apply rewrite ringan tanpa prefix review/debug.
    Non-blocking: kalau evaluation error -> return original text.
    """
    cfg = config or AutoTuneConfig()
    if not cfg.enabled:
        return text

    try:
        result = evaluate_output(text, mode=mode or cfg.mode)
    except Exception as e:
        log.debug("[auto_tune] evaluation error (fail-open): %s", e)
        return text

    _bump_stats(passed=result.passed, corrected=False, score=result.score)

    if result.passed:
        return text

    if not (auto_correct or cfg.auto_correct):
        return text

    tuned = _apply_simple_rewrite(text)
    if tuned != text:
        _AUTO_TUNE_STATS["total_corrected"] += 1
        result.corrected_output = tuned
    return tuned

def _apply_simple_rewrite(text: str) -> str:
    """Rewrite sederhana: ganti over-confidence marker dengan yang lebih lembut."""
    replacements = [
        (r"\bpasti(nya)?\b", "kemungkinan besar"),
        (r"\b100%\b", "sebagian besar"),
        (r"\btanpa keraguan\b", "dengan dukungan data yang cukup"),
        (r"\btidak mungkin salah\b", "kemungkinan besar benar"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ════════════════════════════════════════════════════════════════════════
# SPRINT G: Closed-Loop Auto-Tune (existing — preserved)
# ════════════════════════════════════════════════════════════════════════

@dataclass
class TunedProfile:
    """Tuned Maqashid weight profile."""
    weights: dict[str, float]
    tuned_at: str
    sample_size: int
    fail_rates: dict[str, float]
    version: str = "1.0"


# ── Analysis ─────────────────────────────────────────────────────────────

def _read_selftest_results(limit: int = 100) -> list[dict]:
    """Read recent self-test results."""
    if not SELFTEST_RESULTS_PATH.exists():
        return []
    lines = SELFTEST_RESULTS_PATH.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines[-limit:]:
        try:
            results.append(json.loads(line))
        except Exception:
            continue
    return results


def _evaluate_pair(question: str, answer: str, persona: str = "AYMAN") -> dict:
    """Run Maqashid evaluation on a Q&A pair."""
    try:
        from .maqashid_profiles import evaluate_maqashid
        return evaluate_maqashid(question, answer, persona_name=persona)
    except Exception as e:
        log.debug("[maqashid_tune] Eval failed: %s", e)
        return {"status": "pass", "reasons": [], "mode": "general"}


def _analyze_failures(results: list[dict]) -> dict[str, dict]:
    """Analyze per-axis failure patterns dari self-test results."""
    axis_counts: dict[str, dict[str, int]] = {
        ax: {"fail": 0, "warn": 0, "pass": 0, "total": 0}
        for ax in DEFAULT_WEIGHTS
    }

    for r in results:
        q = r.get("question", "")
        a = r.get("answer", "")
        persona = r.get("persona", "AYMAN")
        if not q or not a:
            continue

        eval_result = _evaluate_pair(q, a, persona)
        status = eval_result.get("status", "pass")
        reasons = eval_result.get("reasons", [])

        # Map reasons ke axis (heuristic dari keyword dalam reason)
        reason_text = " ".join(reasons).lower()
        for axis in DEFAULT_WEIGHTS:
            axis_counts[axis]["total"] += 1
            if axis in reason_text:
                axis_counts[axis][status] += 1
            else:
                # Kalau tidak ada axis-specific reason, distribusikan ke status global
                axis_counts[axis][status] += 0  # tidak increment — nanti normalisasi

        # Fallback: kalau status global bukan pass, distribusikan ke SEMUA axis
        # secara proportional (ini heuristic kasar tapi cukup untuk auto-tune)
        if status != "pass":
            for axis in DEFAULT_WEIGHTS:
                if axis not in reason_text:
                    axis_counts[axis][status] += 1

    # Hitung fail rate per axis
    fail_rates = {}
    for axis, counts in axis_counts.items():
        total = counts["total"] or 1
        fail_rates[axis] = round((counts["fail"] + counts["warn"] * 0.5) / total, 3)

    return fail_rates


# ── Tuning Engine ────────────────────────────────────────────────────────

def compute_tuned_weights(
    fail_rates: dict[str, float],
    baseline: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute adjusted weights dari fail rates.

    Logic:
    - Fail rate > 0.3 → increase weight (lebih strict)
    - Fail rate < 0.1 → decrease weight (lebih lenient)
    - Clamp 0.3–2.0
    """
    baseline = baseline or DEFAULT_WEIGHTS.copy()
    tuned = {}
    for axis, base in baseline.items():
        rate = fail_rates.get(axis, 0.0)
        if rate > 0.3:
            # Increase weight: lebih strict
            tuned[axis] = round(min(2.0, base * (1 + rate)), 2)
        elif rate < 0.1:
            # Decrease weight: lebih lenient
            tuned[axis] = round(max(0.3, base * (1 - (0.1 - rate))), 2)
        else:
            tuned[axis] = base
    return tuned


def run_auto_tune(
    sample_size: int = 50,
    baseline: dict[str, float] | None = None,
) -> TunedProfile:
    """Full auto-tune pipeline."""
    results = _read_selftest_results(limit=sample_size)
    if not results:
        log.warning("[maqashid_tune] No self-test data, returning default")
        return TunedProfile(
            weights=baseline or DEFAULT_WEIGHTS.copy(),
            tuned_at=datetime.now(timezone.utc).isoformat(),
            sample_size=0,
            fail_rates={k: 0.0 for k in DEFAULT_WEIGHTS},
        )

    fail_rates = _analyze_failures(results)
    tuned_weights = compute_tuned_weights(fail_rates, baseline)

    profile = TunedProfile(
        weights=tuned_weights,
        tuned_at=datetime.now(timezone.utc).isoformat(),
        sample_size=len(results),
        fail_rates=fail_rates,
    )

    # Persist
    _persist_profile(profile)
    log.info("[maqashid_tune] Tuned with %d samples: %s", len(results), tuned_weights)
    return profile


def _persist_profile(profile: TunedProfile) -> None:
    """Save tuned profile to disk."""
    try:
        TUNE_ROOT.mkdir(parents=True, exist_ok=True)
        TUNED_PROFILE_PATH.write_text(
            json.dumps(profile.__dict__, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with TUNE_HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(profile.__dict__, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[maqashid_tune] Persist failed: %s", e)


# ── Profile Management ───────────────────────────────────────────────────

def load_tuned_profile() -> dict[str, float] | None:
    """Load active tuned profile, or None kalau belum ada."""
    if not TUNED_PROFILE_PATH.exists():
        return None
    try:
        data = json.loads(TUNED_PROFILE_PATH.read_text(encoding="utf-8"))
        return data.get("weights")
    except Exception as e:
        log.warning("[maqashid_tune] Load failed: %s", e)
        return None


def reset_to_default() -> TunedProfile:
    """Reset profile ke default weights."""
    profile = TunedProfile(
        weights=DEFAULT_WEIGHTS.copy(),
        tuned_at=datetime.now(timezone.utc).isoformat(),
        sample_size=0,
        fail_rates={k: 0.0 for k in DEFAULT_WEIGHTS},
        version="default",
    )
    _persist_profile(profile)
    log.info("[maqashid_tune] Reset to default")
    return profile


# ── Stats ────────────────────────────────────────────────────────────────

def get_tune_stats() -> dict:
    """Aggregate tune history stats."""
    if not TUNE_HISTORY_PATH.exists():
        return {"tune_count": 0, "latest": None, "avg_sample_size": 0}

    entries = []
    for line in TUNE_HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            continue

    if not entries:
        return {"tune_count": 0, "latest": None, "avg_sample_size": 0}

    latest = entries[-1]
    return {
        "tune_count": len(entries),
        "latest": {
            "tuned_at": latest.get("tuned_at"),
            "weights": latest.get("weights"),
            "sample_size": latest.get("sample_size"),
            "fail_rates": latest.get("fail_rates"),
        },
        "avg_sample_size": round(sum(e.get("sample_size", 0) for e in entries) / len(entries), 1),
    }
