"""
tadabbur_mode.py — 3 Persona Iterate → Konvergensi Pattern
=============================================================

Per DIRECTION_LOCK_20260426 P1 Q3 2026:
> "Tadabbur Mode: 3 persona iterate same query → konvergensi pattern"

Filosofi: pertanyaan mendalam jarang punya jawaban single-shot. Konvergensi
muncul saat 3+ perspektif berbeda meeting di common ground. Cocok untuk:
- Decision dengan multiple stakeholder concern
- Strategic question dengan tradeoff
- Complex problem yang butuh holistic view
- Topik mendalam yang tidak boleh shallow

Mekanisme:
1. **Round 1 — Diversification**: 3 persona (UTZ creative, ABOO engineer,
   OOMAR strategist) jawab same query independently
2. **Round 2 — Cross-evaluation**: tiap persona baca jawaban 2 persona lain,
   note point of agreement + disagreement
3. **Round 3 — Convergence**: AYMAN (general/synthesizer) baca semua,
   ekstrak konvergensi inti + remaining divergence
4. **Output**: convergence_summary + divergence_points + per-persona-view

Bukan trivializing spiritual concept (per DIRECTION_LOCK section 3 +
research note 228 acknowledge). Pure engineering pattern: multi-perspective
debate → consensus extraction. Pattern terbukti work di akademik (peer
review), legal (jury deliberation), engineering (design review).

Endpoint: POST /agent/tadabbur — body {prompt, personas?: [3 names]}
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class TadabburRound:
    """Satu round iterasi (diversification / cross-eval / convergence)."""
    round_n: int
    stage: str               # "diversification" | "cross_eval" | "convergence"
    persona: str
    output: str
    duration_ms: int = 0


@dataclass
class TadabburResult:
    """Output Tadabbur Mode complete."""
    id: str
    ts: str
    prompt: str
    rounds: list[TadabburRound] = field(default_factory=list)
    convergence_summary: str = ""    # apa yang 3 persona AGREE
    divergence_points: list[str] = field(default_factory=list)  # apa yang BEDA
    final_synthesis: str = ""         # output untuk user (synthesizer view)
    personas_used: list[str] = field(default_factory=list)
    total_duration_ms: int = 0


# ── Path ───────────────────────────────────────────────────────────────────────

def _tadabbur_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tadabbur_results.jsonl"


# ── Persona prompts ────────────────────────────────────────────────────────────

_PERSONA_LENS = {
    "UTZ": """Kamu UTZ — kreatif, visual, metaforis. Lihat pertanyaan dengan lens
inovasi + experience design. Cari angle out-of-the-box. Jawab dengan story
+ analogi visual.""",

    "ABOO": """Kamu ABOO — engineer, teknis, sistematis. Lihat pertanyaan dengan
lens implementasi + tradeoff teknis. Cari edge case + dependency. Jawab
dengan diagram mental + step konkret.""",

    "OOMAR": """Kamu OOMAR — strategist, market-aware, ROI-focused. Lihat
pertanyaan dengan lens cost-benefit + competitive landscape. Cari moat +
risk. Jawab dengan strategic framework + KPI.""",

    "ALEY": """Kamu ALEY — akademik, riset-driven, sumber primer. Lihat pertanyaan
dengan lens empirical evidence + literature. Cari paper / studi yang
support. Jawab dengan citation + bandingan teori.""",

    "AYMAN": """Kamu AYMAN — synthesizer, hangat, balanced. Lihat pertanyaan dengan
lens audience + clarity. Cari common ground antar perspektif. Jawab
dengan ringkasan jelas + actionable.""",
}


def _call_llm(prompt: str, *, max_tokens: int = 600, temperature: float = 0.7) -> str:
    try:
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[tadabbur] ollama_generate fail: %s", e)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text:
            return text
    except Exception as e:
        log.debug("[tadabbur] generate_sidix fail: %s", e)
    return ""


# ── Round 1: Diversification ──────────────────────────────────────────────────

def _round1_diversify(prompt: str, persona: str) -> str:
    """1 persona jawab query independently."""
    lens = _PERSONA_LENS.get(persona, _PERSONA_LENS["AYMAN"])
    full_prompt = f"""{lens}

PERTANYAAN:
{prompt}

Jawab dari sudut pandang persona-mu (max 250 kata). Spesifik, bukan generic.
Jangan reference persona lain (mereka jawab independently)."""

    return _call_llm(full_prompt, max_tokens=500, temperature=0.7)


# ── Round 2: Cross-Evaluation ─────────────────────────────────────────────────

def _round2_cross_eval(persona_self: str, output_self: str, others: dict) -> str:
    """Persona baca jawaban 2 persona lain → note agreement/disagreement."""
    others_text = "\n\n".join(
        f"=== {name} ===\n{text[:600]}" for name, text in others.items()
    )

    full_prompt = f"""Kamu {persona_self}. Jawabanmu sebelumnya:
{output_self[:500]}

Sekarang baca jawaban 2 persona lain:

{others_text}

Tugas: identifikasi (max 200 kata):
1. **Point of agreement** — di mana ketiga jawaban convergent?
2. **Point of disagreement** — di mana view berbeda?
3. **Yang kamu setuju dari mereka** — apa yang miss di jawaban-mu?

Jujur tajam. Bukan diplomatis."""

    return _call_llm(full_prompt, max_tokens=400, temperature=0.5)


# ── Round 3: Convergence (synthesizer) ────────────────────────────────────────

def _round3_converge(prompt: str, all_outputs: dict, cross_evals: dict) -> dict:
    """Synthesizer (AYMAN) ekstrak convergence + divergence + final synthesis."""
    outputs_text = "\n\n".join(
        f"=== {name} (Round 1) ===\n{text[:500]}" for name, text in all_outputs.items()
    )
    evals_text = "\n\n".join(
        f"=== {name} (Round 2 cross-eval) ===\n{text[:400]}" for name, text in cross_evals.items()
    )

    full_prompt = f"""Kamu AYMAN — synthesizer balanced. Pertanyaan asli:
{prompt}

3 persona sudah jawab + cross-evaluate:

{outputs_text}

CROSS-EVALUATIONS:
{evals_text}

Tugas: ekstrak konvergensi. Output ONLY JSON:
{{
  "convergence_summary": "1-2 paragraf: apa yang ketiga persona AGREE — inti truth yang stabil",
  "divergence_points": ["point di mana view berbeda 1", "point 2"],
  "final_synthesis": "Final answer untuk user — bahasa hangat, action-oriented, max 300 kata. Integrate konvergensi + acknowledge divergence relevan."
}}

Output JSON only:"""

    response = _call_llm(full_prompt, max_tokens=900, temperature=0.5)
    if not response:
        return {"convergence_summary": "", "divergence_points": [], "final_synthesis": ""}

    try:
        from .llm_json_robust import robust_json_parse
        data = robust_json_parse(response)
        if not data:
            raise ValueError("robust_json_parse returned None")
        return {
            "convergence_summary": (data.get("convergence_summary") or "")[:1000],
            "divergence_points": [s for s in (data.get("divergence_points") or []) if s][:6],
            "final_synthesis": (data.get("final_synthesis") or "")[:1500],
        }
    except Exception as e:
        log.debug("[tadabbur] converge JSON parse fail: %s", e)
        return {"convergence_summary": "", "divergence_points": [], "final_synthesis": response[:1500]}


# ── Main orchestrator ──────────────────────────────────────────────────────────

def tadabbur(
    prompt: str,
    *,
    personas: Optional[list[str]] = None,
) -> TadabburResult:
    """
    3-round tadabbur mode: diversification → cross-eval → convergence.

    Args:
        prompt: pertanyaan user (deep question, butuh holistic view)
        personas: list 3 persona (default: ["UTZ", "ABOO", "OOMAR"])

    Returns TadabburResult lengkap.

    Cost: 3 LLM call (round 1) + 3 LLM call (round 2) + 1 LLM call (round 3)
    = 7 LLM call. Mahal, hanya untuk pertanyaan yang butuh depth. Tidak
    untuk casual chat (gunakan /ask biasa).
    """
    import time

    t_start = time.time()

    if not personas or len(personas) != 3:
        personas = ["UTZ", "ABOO", "OOMAR"]
    # Validate personas
    valid = [p for p in personas if p in _PERSONA_LENS]
    if len(valid) != 3:
        valid = ["UTZ", "ABOO", "OOMAR"]
    personas = valid

    result = TadabburResult(
        id=f"tdb_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        prompt=prompt[:600],
        personas_used=personas,
    )

    # Round 1: Diversification
    round1_outputs: dict[str, str] = {}
    for p in personas:
        t0 = time.time()
        out = _round1_diversify(prompt, p)
        dur_ms = int((time.time() - t0) * 1000)
        round1_outputs[p] = out
        result.rounds.append(TadabburRound(
            round_n=1, stage="diversification", persona=p,
            output=out[:1500], duration_ms=dur_ms,
        ))

    # Filter out empty outputs (LLM fail)
    round1_outputs = {k: v for k, v in round1_outputs.items() if v.strip()}
    if len(round1_outputs) < 2:
        result.final_synthesis = "Tadabbur mode butuh minimal 2 persona menjawab. LLM tidak respond."
        result.total_duration_ms = int((time.time() - t_start) * 1000)
        return result

    # Round 2: Cross-Evaluation
    round2_evals: dict[str, str] = {}
    for p in personas:
        if p not in round1_outputs:
            continue
        others = {k: v for k, v in round1_outputs.items() if k != p}
        if len(others) < 1:
            continue
        t0 = time.time()
        eval_out = _round2_cross_eval(p, round1_outputs[p], others)
        dur_ms = int((time.time() - t0) * 1000)
        if eval_out.strip():
            round2_evals[p] = eval_out
            result.rounds.append(TadabburRound(
                round_n=2, stage="cross_eval", persona=p,
                output=eval_out[:1500], duration_ms=dur_ms,
            ))

    # Round 3: Convergence (AYMAN synthesizer)
    t0 = time.time()
    converge = _round3_converge(prompt, round1_outputs, round2_evals)
    dur_ms = int((time.time() - t0) * 1000)
    result.convergence_summary = converge["convergence_summary"]
    result.divergence_points = converge["divergence_points"]
    result.final_synthesis = converge["final_synthesis"]
    result.rounds.append(TadabburRound(
        round_n=3, stage="convergence", persona="AYMAN",
        output=result.final_synthesis[:1500], duration_ms=dur_ms,
    ))

    result.total_duration_ms = int((time.time() - t_start) * 1000)

    # Persist
    try:
        with _tadabbur_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": result.id,
                "ts": result.ts,
                "prompt": result.prompt[:200],
                "personas": personas,
                "rounds_count": len(result.rounds),
                "duration_ms": result.total_duration_ms,
                "convergence_len": len(result.convergence_summary),
                "divergence_count": len(result.divergence_points),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return result


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    path = _tadabbur_log()
    if not path.exists():
        return {"total": 0, "avg_duration_ms": 0}
    durations: list[int] = []
    rounds: list[int] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("duration_ms"):
                        durations.append(int(e["duration_ms"]))
                    if e.get("rounds_count"):
                        rounds.append(int(e["rounds_count"]))
                except Exception:
                    continue
    except Exception:
        return {"total": 0, "avg_duration_ms": 0}
    return {
        "total": len(durations),
        "avg_duration_ms": int(sum(durations) / len(durations)) if durations else 0,
        "avg_rounds": round(sum(rounds) / len(rounds), 1) if rounds else 0,
    }


__all__ = ["TadabburResult", "TadabburRound", "tadabbur", "stats"]
