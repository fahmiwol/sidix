"""
agent_rasa.py — Sprint 21: 🎭 RASA Aesthetic/Quality Scorer

Per note 248 line 50 EKSPLISIT (Embodiment whole-body):
  "🎭 RASA = aesthetic/quality scorer (relevance, taste, brand fit)"

Pre-Execution Alignment Check (per CLAUDE.md 6.4):
- Note 248 line 50 mandate ✓
- Pivot 2026-04-25: scoring dimension-based (1-5), BUKAN blanket epistemic label ✓
- 10 hard rules: own LLM, 5 persona reinforce, MIT, self-hosted ✓
- Anti-halusinasi: scoring grounded di output existing (input → score), no fabrication
- Budget: LLM-only, 1-2 calls per scoring run
- Compound: enhance creative_briefs/<slug>/ artifacts, BUKAN replace

4 dimension scoring (persona delegation):
  1. ALEY    RELEVANCE     — kesesuaian dengan brief
  2. UTZ     AESTHETIC     — color/style/composition harmony
  3. OOMAR   BRAND_FIT     — brand consistency + commercial positioning
  4. AYMAN   AUDIENCE_FIT  — target demographic resonance

Score 1-5 per dimension + reasoning + 1 improvement suggestion per dim.

Public API:
  rasa_score(slug, brief=None, *, persist=True) -> dict
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from .ollama_llm import ollama_generate
except Exception:  # pragma: no cover
    def ollama_generate(*_a, **_k):  # type: ignore
        return ("(LLM unavailable)", {})

try:
    from .agent_wisdom import _extract_json_block  # reuse Sprint 18
except Exception:
    def _extract_json_block(text, key):  # fallback
        return None


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
CREATIVE_BRIEFS_DIR = DATA_DIR / "creative_briefs"
RASA_REPORTS_DIR = DATA_DIR / "rasa_reports"


def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "topic"


def _read_creative_artifact(slug: str) -> Optional[dict[str, Any]]:
    """Read creative_briefs/<slug>/report.md + metadata.json. Return summary."""
    target = CREATIVE_BRIEFS_DIR / slug
    report_md = target / "report.md"
    metadata_json = target / "metadata.json"
    if not (report_md.exists() and metadata_json.exists()):
        return None
    try:
        meta = json.loads(metadata_json.read_text(encoding="utf-8"))
        report_text = report_md.read_text(encoding="utf-8")
        # Truncate to manageable size for LLM context
        return {
            "slug": slug,
            "brief": meta.get("brief", ""),
            "stages_count": len(meta.get("stages", [])),
            "report_excerpt": report_text[:3000],  # first 3KB
            "report_full_size": len(report_text),
        }
    except Exception:
        return None


# ── Single-stage 4-dimension RASA scorer (1 LLM call, all dimensions) ───────
#
# Why single call (BUKAN 4 separate persona calls):
# - Budget: 1 call vs 4 = 4x cheaper, ~75s vs 300s
# - Coherence: same context, all dimensions consistent
# - Pivot 2026-04-25 OK: scoring dimension-based, BUKAN per-persona prompt
#
# Persona voice still hadir di prose reasoning (per dimension UTZ/OOMAR/dll
# voice marker), tapi LLM single instance handle all.

_RASA_SCORER_SYSTEM = (
    "Kamu RASA — aesthetic/quality scorer SIDIX. Voice: balanced multi-persona, "
    "scholarly tapi accessible. Bahasa Indonesia.\n\n"
    "TUGAS — Score creative artifact 4 dimension (skala 1-5):\n\n"
    "1. **RELEVANCE** (lens ALEY researcher) — kesesuaian dengan brief original\n"
    "2. **AESTHETIC** (lens UTZ creative director) — color/style/composition harmony, kawaii fit\n"
    "3. **BRAND_FIT** (lens OOMAR strategist) — brand consistency, commercial positioning\n"
    "4. **AUDIENCE_FIT** (lens AYMAN general) — target demographic resonance, accessibility\n\n"
    "Format markdown: setiap dimension dengan:\n"
    "- Score 1-5\n"
    "- Reasoning (1-2 kalimat konkret cite specific element dari artifact)\n"
    "- Improvement suggestion (1 kalimat actionable)\n\n"
    "Domain creative scoring, BUKAN sensitive (fiqh/medis/data) — natural language "
    "hedging, BUKAN bracket [SPEKULASI] tag per claim.\n\n"
    "**SETELAH markdown analysis di atas**, sertakan blok JSON parseable "
    "(WAJIB exact format, gunakan triple-backtick json fence). REPLACE setiap "
    "<placeholder> dengan content KONKRET, JANGAN echo literal:\n\n"
    "```json\n"
    "{\"scores\": {\n"
    "  \"relevance\": {\"score\": <1-5 integer>, \"reasoning\": \"<1 kalimat reasoning>\", \"improvement\": \"<1 kalimat actionable>\"},\n"
    "  \"aesthetic\": {\"score\": <1-5>, \"reasoning\": \"<...>\", \"improvement\": \"<...>\"},\n"
    "  \"brand_fit\": {\"score\": <1-5>, \"reasoning\": \"<...>\", \"improvement\": \"<...>\"},\n"
    "  \"audience_fit\": {\"score\": <1-5>, \"reasoning\": \"<...>\", \"improvement\": \"<...>\"}\n"
    "},\n"
    "\"overall_score\": <average 1-5 dengan 1 desimal>,\n"
    "\"verdict\": \"<approve / iterate / pivot>\",\n"
    "\"top_priority_improvement\": \"<1 kalimat improvement paling impactful>\"}\n"
    "```\n\n"
    "JSON valid, scores integer 1-5, no trailing commas. Reasoning konkret cite "
    "element artifact, BUKAN vague."
)


@dataclass
class RasaResult:
    slug: str
    ts: str
    creative_summary: dict[str, Any]
    prose: str
    structured: dict[str, Any]
    elapsed_ms: int = 0
    paths: dict[str, str] = field(default_factory=dict)


def rasa_score(
    slug_or_brief: str,
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Sprint 21 RASA scoring untuk creative_briefs/<slug>/.

    Args:
      slug_or_brief: slug langsung atau brief teks (akan di-slugify)
    """
    if not (slug_or_brief or "").strip():
        raise ValueError("slug_or_brief kosong")

    # Detect slug vs brief
    if "/" in slug_or_brief or " " in slug_or_brief or any(c.isupper() for c in slug_or_brief):
        slug = _slugify(slug_or_brief)
    else:
        slug = slug_or_brief.lower().strip()

    creative = _read_creative_artifact(slug)
    if not creative:
        return {
            "success": False,
            "slug": slug,
            "error": f"creative_briefs/{slug}/ not found. Run /creative/brief first.",
        }

    import time as _t
    t0 = _t.time()
    prompt = (
        f"BRIEF original: {creative.get('brief','(no brief)')}\n\n"
        f"CREATIVE ARTIFACT excerpt (first 3KB dari report.md):\n\n"
        f"{creative['report_excerpt']}\n\n"
        f"Score 4 dimension creative artifact ini sesuai instruksi system."
    )
    text, _ = ollama_generate(
        prompt, system=_RASA_SCORER_SYSTEM,
        max_tokens=1100, temperature=0.4,
    )
    elapsed_ms = int((_t.time() - t0) * 1000)

    prose = (text or "").strip()
    structured: dict[str, Any] = {}
    score_obj = _extract_json_block(prose, "scores")
    if score_obj:
        structured = {
            "scores": score_obj.get("scores", {}),
            "overall_score": score_obj.get("overall_score"),
            "verdict": score_obj.get("verdict"),
            "top_priority_improvement": score_obj.get("top_priority_improvement"),
        }

    ts = datetime.now(timezone.utc).isoformat()
    result = {
        "success": True,
        "slug": slug,
        "ts": ts,
        "creative_summary": creative,
        "prose": prose,
        "structured": structured,
        "elapsed_ms": elapsed_ms,
        "paths": {},
    }

    if persist:
        target = RASA_REPORTS_DIR / slug
        target.mkdir(parents=True, exist_ok=True)
        report_md = _render_report_md(result)
        (target / "report.md").write_text(report_md, encoding="utf-8")
        if structured:
            (target / "structured.json").write_text(
                json.dumps(structured, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            result["paths"]["structured"] = str(target / "structured.json")
        result["paths"]["report"] = str(target / "report.md")

    return result


def _render_report_md(r: dict[str, Any]) -> str:
    lines = [
        f"# RASA Score Report — {r['slug']}",
        "",
        f"_Generated_: {r['ts']}",
        f"_Brief_: {r['creative_summary'].get('brief','(none)')}",
        f"_Pipeline_: SIDIX Sprint 21 / 🎭 RASA Aesthetic/Quality Scorer",
        "",
        "---",
        "",
        "## Scoring Analysis (4-dimension, 1-5 scale)",
        "",
        r["prose"],
        "",
        "---",
        "",
        f"_Elapsed_: {r['elapsed_ms']}ms",
    ]
    structured = r.get("structured") or {}
    if structured:
        lines.append("")
        lines.append("## Quick Reference (machine-parseable)")
        lines.append("")
        scores = structured.get("scores", {})
        if scores:
            lines.append("| Dimension | Score | Verdict |")
            lines.append("|---|---|---|")
            for dim in ["relevance", "aesthetic", "brand_fit", "audience_fit"]:
                s = scores.get(dim, {})
                lines.append(f"| {dim.replace('_',' ').title()} | {s.get('score','?')}/5 | {s.get('improvement','(no suggestion)')[:80]} |")
        if "overall_score" in structured:
            lines.append("")
            lines.append(f"**Overall**: {structured.get('overall_score','?')}/5 · **Verdict**: `{structured.get('verdict','?')}`")
        if "top_priority_improvement" in structured:
            lines.append("")
            lines.append(f"**Top Priority Improvement**: {structured['top_priority_improvement']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    inp = " ".join(sys.argv[1:]) or "maskot-brand-makanan-ringan-kawaii-ulat-kuning-untuk-anak-in"
    result = rasa_score(inp)
    if result.get("success"):
        print(json.dumps({
            "slug": result["slug"],
            "structured": result.get("structured"),
            "paths": result["paths"],
            "elapsed_ms": result["elapsed_ms"],
        }, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2))
