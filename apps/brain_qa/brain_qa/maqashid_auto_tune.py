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

import hashlib
import json
import logging
import os
import re
import threading
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

# Phase 2: Historical feedback store (user thumbs up/down) — lightweight JSONL
_FEEDBACK_PATH = TUNE_ROOT / "feedback_history.jsonl"
_FEEDBACK_LOCK = threading.Lock()
_FEEDBACK_CACHE: list[dict] = []


def _load_feedback_history() -> list[dict]:
    """Load user feedback history for judge calibration."""
    global _FEEDBACK_CACHE
    if _FEEDBACK_CACHE:
        return _FEEDBACK_CACHE
    if not _FEEDBACK_PATH.exists():
        return []
    entries = []
    for line in _FEEDBACK_PATH.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
    _FEEDBACK_CACHE = entries
    return entries


def record_feedback(
    query: str,
    output: str,
    thumbs_up: bool,
    persona: str = "AYMAN",
    trace: list[dict] | None = None,
) -> dict:
    """
    Phase 2: Record user feedback (thumbs up/down) untuk judge calibration.
    Called dari frontend/API saat user rate jawaban.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query[:500],
        "output": output[:1000],
        "thumbs_up": thumbs_up,
        "persona": persona,
        "trace_steps": len(trace) if trace else 0,
        "heuristic_score": 0.0,
    }
    # Pre-compute heuristic score untuk training data
    try:
        result = evaluate_output(output, mode="general")
        entry["heuristic_score"] = result.score
    except Exception:
        pass

    with _FEEDBACK_LOCK:
        TUNE_ROOT.mkdir(parents=True, exist_ok=True)
        with _FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _FEEDBACK_CACHE.append(entry)

    return {"ok": True, "feedback_id": hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:12]}


# Phase 2: Historical Judge — lightweight calibration dari feedback
class HistoricalJudge:
    """
    Lightweight judge yang adjust scoring weights berdasarkan historical feedback.
    Self-hosted, no LLM API calls. Rule-based dengan learned coefficients.
    """

    def __init__(self):
        self.feedback = _load_feedback_history()
        self._coeffs = self._compute_coeffs()

    def _compute_coeffs(self) -> dict[str, float]:
        """Compute adjustment coefficients dari feedback history."""
        if len(self.feedback) < 10:
            # Not enough data — return neutral coeffs
            return {"hate": 1.0, "misinfo": 1.0, "attribution": 1.0, "ad_hominem": 1.0, "brand": 1.0, "bias": 0.0}

        # Analyze: feedback yang thumbs_down tapi heuristic_score tinggi → heuristic terlalu lenient
        # feedback yang thumbs_up tapi heuristic_score rendah → heuristic terlalu strict
        false_negatives = 0  # thumbs_down tapi score > 0.6
        false_positives = 0  # thumbs_up tapi score < 0.6
        for fb in self.feedback:
            score = fb.get("heuristic_score", 0.5)
            if not fb.get("thumbs_up", True) and score > 0.6:
                false_negatives += 1
            if fb.get("thumbs_up", True) and score < 0.6:
                false_positives += 1

        total = len(self.feedback)
        fn_rate = false_negatives / total
        fp_rate = false_positives / total

        # Adjust: high FN → lebih strict (boost violation weights)
        # high FP → lebih lenient (reduce violation weights)
        bias = (fn_rate - fp_rate) * 0.5  # -0.5 to +0.5
        return {
            "hate": 1.0 + bias,
            "misinfo": 1.0 + bias,
            "attribution": 1.0 + bias * 0.5,
            "ad_hominem": 1.0 + bias,
            "brand": 1.0 + bias * 0.3,
            "bias": bias,
        }

    def adjust_score(self, base_score: float, violations: list[str]) -> float:
        """Apply learned adjustments ke heuristic score."""
        if not self.feedback or len(self.feedback) < 10:
            return base_score

        # Count violation types
        v_counts = {"hate": 0, "misinfo": 0, "attribution": 0, "ad_hominem": 0, "brand": 0}
        for v in violations:
            vl = v.lower()
            if "kebencian" in vl or "diskriminasi" in vl:
                v_counts["hate"] += 1
            elif "misinformasi" in vl or "keyakinan mutlak" in vl:
                v_counts["misinfo"] += 1
            elif "atribusi" in vl:
                v_counts["attribution"] += 1
            elif "ad hominem" in vl:
                v_counts["ad_hominem"] += 1
            elif "kontradiksi" in vl or "brand" in vl:
                v_counts["brand"] += 1

        # Apply weighted penalty
        penalty = 0.0
        for vtype, count in v_counts.items():
            if count > 0:
                penalty += count * 0.15 * self._coeffs.get(vtype, 1.0)

        adjusted = max(0.0, min(1.0, base_score - penalty + self._coeffs.get("bias", 0.0)))
        return round(adjusted, 3)


# Phase 2: Trace-aware evaluation models
class TraceStep(BaseModel if _PYDANTIC_OK else object):
    """Single step dalam reasoning chain untuk trace-aware eval."""
    step_number: int = 0
    step_type: str = ""  # "thought", "tool_call", "observation", "final_answer"
    content: str = ""
    tool_name: str = ""
    tool_result_success: bool = True
    citations: list[dict] = field(default_factory=list)

    if not _PYDANTIC_OK:
        def __init__(self, **kwargs):
            self.step_number = kwargs.get("step_number", 0)
            self.step_type = kwargs.get("step_type", "")
            self.content = kwargs.get("content", "")
            self.tool_name = kwargs.get("tool_name", "")
            self.tool_result_success = kwargs.get("tool_result_success", True)
            self.citations = kwargs.get("citations", [])


class TraceEvalResult(BaseModel if _PYDANTIC_OK else object):
    """Result of trace-aware evaluation."""
    overall_score: float = 0.0
    passed: bool = True
    step_scores: list[dict] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    if not _PYDANTIC_OK:
        def __init__(self, **kwargs):
            self.overall_score = kwargs.get("overall_score", 0.0)
            self.passed = kwargs.get("passed", True)
            self.step_scores = kwargs.get("step_scores", [])
            self.violations = kwargs.get("violations", [])
            self.suggestions = kwargs.get("suggestions", [])


def _score_trace_step(step: TraceStep) -> dict:
    """Score individual step dalam reasoning chain."""
    score = 1.0
    violations: list[str] = []

    if step.step_type == "tool_call":
        if not step.tool_result_success:
            score -= 0.2
            violations.append(f"Step {step.step_number}: tool '{step.tool_name}' failed")
        if not step.citations and step.tool_name in ("search_corpus", "read_chunk"):
            score -= 0.1
            violations.append(f"Step {step.step_number}: RAG tool without citations")

    elif step.step_type == "thought":
        # Check for over-confidence in reasoning
        lower = step.content.lower()
        if any(m in lower for m in _MISINFO_MARKERS):
            score -= 0.15
            violations.append(f"Step {step.step_number}: over-confident reasoning marker")

    elif step.step_type == "final_answer":
        # Run full heuristic on final answer
        result = evaluate_output(step.content, mode="general")
        score = result.score
        violations.extend(result.violations)

    return {
        "step_number": step.step_number,
        "step_type": step.step_type,
        "score": round(max(0.0, score), 3),
        "violations": violations,
    }


def evaluate_trace(steps: list[TraceStep], mode: str = "general") -> TraceEvalResult:
    """
    Phase 2: Trace-aware evaluation — score EVERY step, not just final output.
    Identifies exact step where reasoning went wrong.
    """
    if not steps:
        return TraceEvalResult(overall_score=1.0, passed=True)

    step_results = []
    all_violations = []
    total_score = 0.0

    for step in steps:
        sr = _score_trace_step(step)
        step_results.append(sr)
        total_score += sr["score"]
        all_violations.extend(sr["violations"])

    avg_score = total_score / len(steps) if steps else 1.0

    # Weight final answer more heavily
    final_steps = [s for s in step_results if s["step_type"] == "final_answer"]
    if final_steps:
        final_score = final_steps[0]["score"]
        overall = (avg_score * 0.4) + (final_score * 0.6)
    else:
        overall = avg_score

    # Generate suggestions
    suggestions = []
    if any("tool" in v and "failed" in v for v in all_violations):
        suggestions.append("Periksa kembali tool calls — ada yang gagal dieksekusi")
    if any("citations" in v for v in all_violations):
        suggestions.append("Pastikan setiap klaim faktual memiliki sanad/citation")
    if any("over-confident" in v for v in all_violations):
        suggestions.append("Gunakan bahasa yang menunjukkan tingkat keyakinan yang sesuai")

    # Apply historical judge calibration
    judge = HistoricalJudge()
    overall = judge.adjust_score(overall, all_violations)

    passed = overall >= 0.6

    return TraceEvalResult(
        overall_score=round(overall, 3),
        passed=passed,
        step_scores=step_results,
        violations=all_violations,
        suggestions=suggestions,
    )


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
    Evaluasi output dan inject warning/suggestion kalau perlu.

    Returns tuned text (original + prefix/suffix kalau violation).
    Non-blocking: kalau evaluation error → return original text.
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

    # Kalau lolos → return as-is
    if result.passed:
        return text

    # Kalau tidak lolos → inject warning prefix + suggestions
    tuned = text
    if result.violations or result.suggestions:
        warning_lines: list[str] = []
        if result.violations:
            warning_lines.append("[⚠️ Auto-Tune Review]")
            for v in result.violations:
                warning_lines.append(f"  • {v}")
        if result.suggestions:
            warning_lines.append("  Saran perbaikan:")
            for s in result.suggestions:
                warning_lines.append(f"    → {s}")
        warning_block = "\n".join(warning_lines)

        # Prepend ke output — jangan hapus konten asli (non-blocking / non-censor)
        tuned = f"{warning_block}\n\n---\n\n{tuned}"

    if auto_correct or cfg.auto_correct:
        # Attempt simple rewrite: ganti over-confidence markers
        tuned = _apply_simple_rewrite(tuned)
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
