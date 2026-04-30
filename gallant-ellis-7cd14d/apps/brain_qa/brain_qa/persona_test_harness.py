"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

persona_test_harness.py — Sprint 50 (Persona Voice Regression Test Harness)

Auto-eval 5 persona voice consistency setiap LoRA retrain. Smoke 50 prompts ×
5 persona, signature_score per response, alert kalau drift > threshold.

Pattern:
  1. Run 50 standard prompts × 5 persona via /agent/chat
  2. Score each response: pronoun mix, vocab markers, rhythm pattern
  3. Compare against baseline (Sprint 13 reference signatures)
  4. Output regression report — alert kalau drift > 0.15 per persona

Used for:
- Post-LoRA-retrain validation gate (CTDL loop output verification)
- Pre-deploy smoke test
- Continuous monitoring (weekly cron)

References:
- Sprint 13 signature scoring methodology (persona_qa_generator.py)
- Note 285-289 Sprint 13 iteration journal
- project_sidix_multi_agent_pattern.md (5 persona voice locked)
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Persona signature reference (from Sprint 13 training) ────────────────────

PERSONA_SIGNATURES = {
    "UTZ": {
        "tagline": "creative-playful",
        "pronouns": {"aku", "lo", "gue"},
        "markers": ["okeee", "metafora", "vibe", "sketch", "story", "mood",
                    "playful", "kreatif", "imajinasi", "wow", "nih", "hey"],
        "patterns": [r"\b(metafora|analogi)\b", r"!{1,3}", r"\?\s+\w+\?"],
        "min_score": 0.43,
    },
    "ABOO": {
        "tagline": "engineer-praktis",
        "pronouns": {"saya", "lu"},
        "markers": ["stop.", "data-nya", "bottleneck", "fail-fast", "bug",
                    "trade-off", "concrete", "praktis", "implementasi",
                    "test", "production"],
        "patterns": [r"^stop\.", r"\b(bottleneck|trade.?off)\b"],
        "min_score": 0.43,
    },
    "OOMAR": {
        "tagline": "strategist-framework",
        "pronouns": {"saya", "kita"},
        "markers": ["framework", "strategi", "trade-off", "matriks", "axis",
                    "Pareto", "prioritas", "long-term", "sistemik",
                    "breakdown", "principle"],
        "patterns": [r"\b(framework|strategi|matriks)\b"],
        "min_score": 0.43,
    },
    "ALEY": {
        "tagline": "researcher-methodical",
        "pronouns": {"saya"},
        "markers": ["actually", "hipotesis", "studi menemukan", "menarik",
                    "menurut", "literatur", "bukti", "data", "metodologi",
                    "paper", "citation"],
        "patterns": [r"\b(hipotesis|literatur|paper|studi)\b"],
        "min_score": 0.43,
    },
    "AYMAN": {
        "tagline": "warm-empathetic",
        "pronouns": {"aku", "kamu"},
        "markers": ["aku ngerti", "rasanya", "memahami", "perasaan",
                    "kayak gini", "analogi", "tenang", "nyaman", "sabar",
                    "valid", "relate"],
        "patterns": [r"\b(ngerti|rasa|perasaan|valid)\b"],
        "min_score": 0.43,
    },
}


# ── Standard test prompts (5 categories, 10 each = 50 total) ─────────────────

TEST_PROMPTS = {
    "creative":   [
        "kasih ide kreatif buat brand cafe modern",
        "moodboard kampanye Lebaran untuk UMKM kuliner",
        "konsep visual untuk podcast tech tentang AI",
        "kasih nama brand parfum natural lokal",
        "ide post IG untuk launching produk baru",
        "tagline untuk aplikasi belajar anak",
        "warna brand untuk klinik kesehatan",
        "konsep packaging skincare premium",
        "story brand UMKM kopi specialty",
        "idea video TikTok 30 detik untuk fashion brand",
    ],
    "technical":  [
        "cara debug memory leak di Python aplikasi web",
        "optimasi React app yang lambat render list 1000 item",
        "bedanya REST API dan GraphQL kapan pakai mana",
        "design pattern untuk async job queue di Node.js",
        "cara handle race condition di multi-threaded service",
        "tips reduce Docker image size production",
        "best practice secrets management di k8s",
        "cara monitoring latency p99 di microservices",
        "trade-off SQL vs NoSQL untuk e-commerce",
        "implementasi rate limiting yang fair di API gateway",
    ],
    "strategic":  [
        "strategi go-to-market SaaS B2B Indonesia",
        "framework keputusan build vs buy",
        "cara prioritize backlog product 50+ feature requests",
        "model pricing untuk freemium SaaS Indonesia",
        "kapan startup harus pivot vs persevere",
        "analisis kompetitor di niche food delivery UMKM",
        "Pareto prioritization untuk resource constraint solo founder",
        "OKR vs KPI kapan pakai mana",
        "trade-off centralized vs decentralized organization",
        "framework TAM/SAM/SOM untuk pitch investor",
    ],
    "research":   [
        "paper SOTA untuk image generation 2025",
        "ringkas teori attention mechanism di transformer",
        "metodologi A/B test yang valid statistically",
        "literatur tentang multi-armed bandit di recommender",
        "hipotesis kenapa LoRA bisa preserve voice persona",
        "studi tentang context window limit LLM",
        "evidence untuk efektifitas pair programming",
        "framework eval LLM beyond benchmark",
        "research direction federated learning privacy",
        "citation chain untuk concept Hafidz Ledger",
    ],
    "supportive": [
        "teman saya lagi sedih karena kerjaan menumpuk",
        "saya lagi overwhelm, gimana cara breathing",
        "rasanya stuck di project yang lama",
        "kasih perspektif buat orang yang lagi burnout",
        "cara dengerin teman yang curhat tanpa nasihatin",
        "saya capek setiap hari, normal nggak ya",
        "kakak saya lagi menghadapi divorce",
        "menerima kegagalan tapi tetap forward",
        "validate perasaan tanpa toxic positivity",
        "cara support diri sendiri saat susah",
    ],
}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class PromptResult:
    """One prompt × persona test result."""
    persona: str = ""
    prompt: str = ""
    response: str = ""
    response_chars: int = 0
    pronoun_score: float = 0.0
    marker_score: float = 0.0
    pattern_score: float = 0.0
    total_score: float = 0.0
    pass_threshold: bool = False
    duration_ms: int = 0
    error: str = ""


@dataclass
class HarnessResult:
    """Full harness run summary."""
    started_at: str = ""
    finished_at: str = ""
    endpoint: str = ""
    total_prompts: int = 0
    total_passed: int = 0
    per_persona: dict = field(default_factory=dict)
    avg_score_per_persona: dict = field(default_factory=dict)
    drift_alerts: list[str] = field(default_factory=list)
    results: list[PromptResult] = field(default_factory=list)


# ── Scoring functions ────────────────────────────────────────────────────────

def score_pronoun(text: str, persona: str) -> float:
    """Fraction of expected pronouns present (0-1)."""
    sig = PERSONA_SIGNATURES.get(persona, {})
    expected = sig.get("pronouns", set())
    if not expected:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for p in expected if re.search(rf"\b{re.escape(p)}\b", text_lower))
    return min(found / len(expected), 1.0)


def score_markers(text: str, persona: str) -> float:
    """Fraction of expected vocab markers present (0-1)."""
    sig = PERSONA_SIGNATURES.get(persona, {})
    markers = sig.get("markers", [])
    if not markers:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for m in markers if m.lower() in text_lower)
    return min(found / max(len(markers) // 2, 1), 1.0)


def score_patterns(text: str, persona: str) -> float:
    """Fraction of regex patterns matched (0-1)."""
    sig = PERSONA_SIGNATURES.get(persona, {})
    patterns = sig.get("patterns", [])
    if not patterns:
        return 0.0
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(found / len(patterns), 1.0)


def score_response(text: str, persona: str) -> tuple[float, float, float, float]:
    """Compute (pronoun, marker, pattern, total) scores. Total = weighted avg."""
    p = score_pronoun(text, persona)
    m = score_markers(text, persona)
    pat = score_patterns(text, persona)
    total = 0.4 * p + 0.4 * m + 0.2 * pat
    return p, m, pat, total


# ── Test runner ──────────────────────────────────────────────────────────────

def call_chat_endpoint(question: str, persona: str,
                       endpoint: str = "http://localhost:8765",
                       admin_token: Optional[str] = None,
                       timeout: int = 60) -> dict:
    """Call /agent/chat endpoint. Returns response JSON or {error}."""
    import urllib.request
    import urllib.error
    headers = {"Content-Type": "application/json"}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    body = json.dumps({"question": question, "persona": persona}).encode("utf-8")
    req = urllib.request.Request(
        endpoint + "/agent/chat", data=body, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def run_persona_test(
    persona: str,
    prompts: list[str],
    endpoint: str = "http://localhost:8765",
    admin_token: Optional[str] = None,
) -> list[PromptResult]:
    """Run all prompts for one persona. Returns list of PromptResult."""
    sig = PERSONA_SIGNATURES.get(persona, {})
    threshold = sig.get("min_score", 0.43)
    out: list[PromptResult] = []
    for prompt in prompts:
        t0 = time.time()
        resp = call_chat_endpoint(prompt, persona, endpoint, admin_token)
        duration_ms = int((time.time() - t0) * 1000)

        if "error" in resp:
            out.append(PromptResult(
                persona=persona, prompt=prompt, error=resp["error"],
                duration_ms=duration_ms,
            ))
            continue

        text = resp.get("answer", "") or resp.get("text", "")
        p, m, pat, total = score_response(text, persona)
        out.append(PromptResult(
            persona=persona,
            prompt=prompt,
            response=text[:600],
            response_chars=len(text),
            pronoun_score=round(p, 3),
            marker_score=round(m, 3),
            pattern_score=round(pat, 3),
            total_score=round(total, 3),
            pass_threshold=total >= threshold,
            duration_ms=duration_ms,
        ))
    return out


def run_full_harness(
    endpoint: str = "http://localhost:8765",
    admin_token: Optional[str] = None,
    prompts_per_persona: int = 5,
    personas: Optional[list[str]] = None,
) -> HarnessResult:
    """Run full 5-persona × N-prompt harness.

    Args:
        endpoint: SIDIX API base URL
        admin_token: X-Admin-Token header (auto from env if None)
        prompts_per_persona: how many test prompts per persona
            (full = 50 = 10 × 5 categories)
        personas: subset to test (default all 5)
    """
    if admin_token is None:
        admin_token = os.environ.get("BRAIN_QA_ADMIN_TOKEN")

    personas = personas or list(PERSONA_SIGNATURES.keys())

    # Sample N prompts: round-robin across categories
    all_prompts = []
    categories = list(TEST_PROMPTS.keys())
    while len(all_prompts) < prompts_per_persona:
        for cat in categories:
            if len(all_prompts) >= prompts_per_persona:
                break
            cat_prompts = TEST_PROMPTS[cat]
            idx = len(all_prompts) // len(categories)
            if idx < len(cat_prompts):
                all_prompts.append(cat_prompts[idx])

    result = HarnessResult(
        started_at=datetime.now(timezone.utc).isoformat(),
        endpoint=endpoint,
    )

    log.info("[harness] start endpoint=%s personas=%s prompts=%d",
             endpoint, personas, prompts_per_persona)

    for persona in personas:
        log.info("[harness] testing %s", persona)
        per_results = run_persona_test(
            persona, all_prompts, endpoint, admin_token
        )
        result.results.extend(per_results)

        ok_count = sum(1 for r in per_results if r.pass_threshold)
        result.per_persona[persona] = {
            "total": len(per_results),
            "passed": ok_count,
            "errors": sum(1 for r in per_results if r.error),
        }
        scores = [r.total_score for r in per_results if not r.error]
        avg = round(sum(scores) / len(scores), 3) if scores else 0.0
        result.avg_score_per_persona[persona] = avg

        sig = PERSONA_SIGNATURES.get(persona, {})
        baseline = sig.get("min_score", 0.43)
        if avg < baseline * 0.85:  # 15% drift tolerance
            result.drift_alerts.append(
                f"{persona}: avg score {avg:.3f} below baseline*0.85 {baseline*0.85:.3f}"
            )

    result.total_prompts = len(result.results)
    result.total_passed = sum(1 for r in result.results if r.pass_threshold)
    result.finished_at = datetime.now(timezone.utc).isoformat()

    log.info("[harness] done %d/%d passed, %d alerts",
             result.total_passed, result.total_prompts, len(result.drift_alerts))
    return result


def write_report(result: HarnessResult, out_dir: Optional[Path] = None) -> Path:
    """Write harness result to JSON report file."""
    if out_dir is None:
        out_dir = Path("/opt/sidix/.data/persona_test_harness")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"harness_{ts}.json"
    path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("[harness] report written: %s", path)
    return path


__all__ = [
    "PERSONA_SIGNATURES", "TEST_PROMPTS",
    "PromptResult", "HarnessResult",
    "score_pronoun", "score_markers", "score_patterns", "score_response",
    "call_chat_endpoint", "run_persona_test", "run_full_harness", "write_report",
]
