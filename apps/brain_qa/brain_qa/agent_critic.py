"""
agent_critic.py — Dedicated Critic Agent (Pilar 2 Closure)
============================================================

Per DIRECTION_LOCK_20260426 + Gemini 4-pilar architecture:
> "Pilar 2 Multi-Agent Adversarial Workflow:
>  Agen Periset (Observer), Agen Kreator (Innovator), Agen Kritikus (Evaluator).
>  Pertarungan iteratif antara Kreator dan Kritikus melahirkan kegeniusan."

SIDIX status sebelum vol 10:
- Innovator ✅ Burst mode (existing, 6-angle Pareto)
- Observer ✅ autonomous_researcher + learn_agent (existing)
- **Critic ❌ MISSING — gap kritis**

Critic = LLM dengan persona "destroy this output, find weakness". Dipanggil
SETELAH Innovator generate, BEFORE final return ke user. Hasil critique
→ Innovator refine atau langsung kasih ke user (kalau critique severity rendah).

Filosofi: kompetitor (ChatGPT/Claude) cuma single-pass — generate → return.
SIDIX double-pass: generate → critique → refine. **Quality compound seiring
iterasi**.

3 mode critique:
1. **devil_advocate** — find logic flaws + counter-arguments
2. **quality_check** — assess clarity, accuracy, completeness, factual claims
3. **destruction_test** — assume hostile reader, find every weakness

Output Critique dataclass: severity (info/warning/critical), specific issues,
suggested improvements, score 0-1.
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
class Critique:
    """Output dari Critic agent."""
    id: str
    ts: str
    target_output: str            # output yang dicritique (truncated 600 char)
    mode: str                      # "devil_advocate" | "quality_check" | "destruction_test"
    severity: str                  # "info" | "warning" | "critical"
    score: float                   # 0.0 (terburuk) - 1.0 (sempurna)
    issues: list[str]              # spesifik issue yang ditemukan
    suggested_improvements: list[str]
    counter_arguments: list[str]   # untuk devil_advocate mode
    overall_judgment: str          # 1-2 kalimat kesimpulan
    refined_output: str = ""       # kalau auto-refine, hasil revisi


# ── Path ───────────────────────────────────────────────────────────────────────

def _critiques_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "critiques.jsonl"


# ── LLM helper ─────────────────────────────────────────────────────────────────

def _call_llm(prompt: str, *, max_tokens: int = 600, temperature: float = 0.6) -> str:
    """Unified LLM call (sama pattern dengan modul cognitive lain)."""
    try:
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[critic] ollama_generate fail: %s", e)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text:
            return text
    except Exception as e:
        log.debug("[critic] generate_sidix fail: %s", e)
    return ""


# ── Critique generator ────────────────────────────────────────────────────────

_MODE_INSTRUCTIONS = {
    "devil_advocate": """Kamu Devil's Advocate. Tugas: cari logical flaw,
asumsi yang tidak terverifikasi, counter-argument yang valid. Tidak peduli
output kelihatan bagus — selalu ada yang bisa di-challenge. Jujur tajam.""",

    "quality_check": """Kamu Quality Inspector. Tugas: assess clarity,
accuracy, completeness, dan factual claims. Cek: ada klaim tanpa sumber?
ada ambiguity? ada gap penting? Output harus actionable improvement.""",

    "destruction_test": """Kamu hostile reader yang cari setiap kelemahan.
Tugas: destruct output ini. Pretend kamu kompetitor yang ingin debunk.
Tidak ada output yang sempurna — tugasmu cari weakness. Brutal jujur.""",
}


def critique_output(
    output: str,
    *,
    mode: str = "quality_check",
    context: str = "",
) -> Optional[Critique]:
    """
    Generate critique dari LLM output target.

    Args:
        output: text yang akan di-critique (e.g. jawaban Burst mode)
        mode: critique mode (devil_advocate | quality_check | destruction_test)
        context: original question or context untuk relevance assessment

    Returns Critique atau None kalau LLM gagal.
    """
    if not output or len(output.strip()) < 20:
        return None

    instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["quality_check"])
    target_truncated = output[:1500]
    context_section = f"\n\nKonteks/pertanyaan asli:\n{context[:400]}\n" if context else ""

    prompt = f"""{instruction}
{context_section}
OUTPUT YANG DI-CRITIQUE:
{target_truncated}

Berikan critique lengkap dalam JSON ONLY:
{{
  "severity": "info|warning|critical",
  "score": 0.0-1.0 (0=terburuk, 1=sempurna),
  "issues": ["issue 1 spesifik", "issue 2", ...],
  "suggested_improvements": ["saran konkret 1", "saran 2", ...],
  "counter_arguments": ["argumen tandingan kalau ada"],
  "overall_judgment": "1-2 kalimat kesimpulan akhir"
}}

Jangan kasih opini umum. Spesifik. Konstruktif. Output JSON:"""

    response = _call_llm(prompt, max_tokens=700, temperature=0.5)
    if not response:
        return None

    try:
        from .llm_json_robust import robust_json_parse
        data = robust_json_parse(response)
        if not data:
            raise ValueError("robust_json_parse returned None")

        severity = (data.get("severity") or "info").strip().lower()
        if severity not in ("info", "warning", "critical"):
            severity = "info"

        return Critique(
            id=f"crit_{uuid.uuid4().hex[:10]}",
            ts=datetime.now(timezone.utc).isoformat(),
            target_output=output[:600],
            mode=mode,
            severity=severity,
            score=max(0.0, min(1.0, float(data.get("score", 0.5)))),
            issues=[s for s in (data.get("issues") or []) if s][:8],
            suggested_improvements=[s for s in (data.get("suggested_improvements") or []) if s][:6],
            counter_arguments=[s for s in (data.get("counter_arguments") or []) if s][:5],
            overall_judgment=(data.get("overall_judgment") or "")[:300],
        )
    except json.JSONDecodeError:
        log.debug("[critic] JSON parse fail: %s", response[:200])
        return None
    except Exception as e:
        log.warning("[critic] critique fail: %s", e)
        return None


# ── Refine via critique ────────────────────────────────────────────────────────

def refine_with_critique(
    output: str,
    critique: Critique,
    *,
    context: str = "",
) -> str:
    """
    Apply critique → generate revised output. Critique-driven self-refine.

    Returns revised text atau output asli kalau refine gagal.
    """
    if not critique.issues and not critique.suggested_improvements:
        return output  # nothing to refine

    issues_str = "\n".join(f"- {i}" for i in critique.issues)
    suggestions_str = "\n".join(f"- {s}" for s in critique.suggested_improvements)

    prompt = f"""Output sebelumnya:
{output[:1500]}

Critique yang ditemukan:
ISSUES:
{issues_str}

SUGGESTED IMPROVEMENTS:
{suggestions_str}

Tugas: revisi output di atas dengan address SEMUA issue + apply improvements.
{"Konteks asli: " + context[:300] if context else ""}

Output revisi (langsung text final, tanpa preamble):"""

    refined = _call_llm(prompt, max_tokens=900, temperature=0.5)
    return refined.strip() if refined else output


# ── Innovator + Critic loop (closes Pilar 2) ───────────────────────────────────

def innovator_critic_loop(
    prompt: str,
    *,
    max_iterations: int = 2,
    critic_mode: str = "quality_check",
    persona: str = "AYMAN",
) -> dict:
    """
    Multi-agent adversarial workflow:
    1. Innovator (Burst mode existing) → 6-angle Pareto
    2. Critic critique winner → severity+score
    3. Kalau critical/warning: refine → loop (max 2x)
    4. Return final + critique trail

    Closes Pilar 2 dari 50% → 80% coverage (per DIRECTION_LOCK).
    """
    iterations = []
    current_output = ""

    # Iteration 1: Innovator (Burst)
    try:
        from .agent_burst import burst_refine
        burst_result = burst_refine(prompt, n=4, top_k=2, fast_mode=True)
        if isinstance(burst_result, dict):
            current_output = burst_result.get("final", "")
        else:
            current_output = str(burst_result)
    except Exception as e:
        log.warning("[critic_loop] Burst fail, fallback to direct LLM: %s", e)
        current_output = _call_llm(prompt, max_tokens=600, temperature=0.7)

    if not current_output:
        return {"error": "no initial output", "iterations": []}

    iterations.append({
        "stage": "innovator_initial",
        "output_preview": current_output[:300],
        "output_full": current_output,
    })

    # Iteration 2-N: Critic + Refine loop
    for iter_n in range(max_iterations):
        critique = critique_output(current_output, mode=critic_mode, context=prompt)
        if not critique:
            break

        iterations.append({
            "stage": f"critique_round_{iter_n + 1}",
            "severity": critique.severity,
            "score": critique.score,
            "issues_count": len(critique.issues),
            "judgment": critique.overall_judgment,
        })

        # Stop kalau severity info dan score >0.8 (good enough)
        if critique.severity == "info" and critique.score >= 0.8:
            break

        # Refine
        refined = refine_with_critique(current_output, critique, context=prompt)
        if not refined or refined == current_output:
            break

        current_output = refined
        iterations.append({
            "stage": f"refine_round_{iter_n + 1}",
            "output_preview": refined[:300],
        })

    # Final critique untuk return
    final_critique = critique_output(current_output, mode=critic_mode, context=prompt)

    # Persist
    try:
        with _critiques_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "prompt": prompt[:200],
                "iterations_count": len(iterations),
                "final_score": final_critique.score if final_critique else 0.0,
                "final_severity": final_critique.severity if final_critique else "unknown",
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return {
        "ok": True,
        "final_output": current_output,
        "iterations": iterations,
        "final_critique": asdict(final_critique) if final_critique else None,
        "iteration_count": len(iterations),
    }


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Read tail dari critiques log untuk admin dashboard."""
    path = _critiques_log()
    if not path.exists():
        return {"total": 0, "avg_score": 0.0}

    scores: list[float] = []
    sevs: dict[str, int] = {"info": 0, "warning": 0, "critical": 0, "unknown": 0}
    iter_counts: list[int] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("final_score"):
                        scores.append(float(e["final_score"]))
                    sev = e.get("final_severity", "unknown")
                    sevs[sev] = sevs.get(sev, 0) + 1
                    if e.get("iterations_count"):
                        iter_counts.append(int(e["iterations_count"]))
                except Exception:
                    continue
    except Exception:
        return {"total": 0, "avg_score": 0.0}

    return {
        "total": len(scores),
        "avg_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "avg_iterations": round(sum(iter_counts) / len(iter_counts), 2) if iter_counts else 0.0,
        "by_severity": sevs,
    }


__all__ = [
    "Critique",
    "critique_output",
    "refine_with_critique",
    "innovator_critic_loop",
    "stats",
]
