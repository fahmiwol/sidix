"""
agent_integrated.py — Sprint 20: Integrated Wisdom Output Mode

Per note 248 line 473 EXPLICIT: "Sprint 20: Integrated wisdom output mode"

Pre-Execution Alignment Check (per CLAUDE.md 6.4):
- Note 248 line 473 mandate ✓
- Pivot 2026-04-25: orchestrator only, no persona prompt change ✓
- 10 hard rules: own LLM, 5 persona reinforce, MIT, self-hosted ✓
- Anti-halusinasi: orchestrator = call existing endpoints, no new generation
- Budget consciousness: MVP smart caching (reuse existing artifacts)

Combine creative + wisdom dalam 1 unified call:
- Brief input → creative pipeline (5-stage UTZ) atau reuse cached
- + wisdom analysis (5-stage judgment + structured JSON)
- + visioner trending injected (existing pattern Sprint 14c + Sprint 16)
- → unified comprehensive report

Smart caching strategy:
- Slugify input → cek .data/creative_briefs/<slug>/report.md exists?
  YES → reuse (skip creative re-generate, hemat budget)
  NO → call creative_brief_pipeline
- Wisdom always fresh (judgment topical, context-dependent)

Public API:
  integrated_analysis(brief, context=None, force_regen=False) -> dict
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
CREATIVE_BRIEFS_DIR = DATA_DIR / "creative_briefs"
WISDOM_REPORTS_DIR = DATA_DIR / "wisdom_reports"
INTEGRATED_DIR = DATA_DIR / "integrated_reports"


def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "topic"


# ── Smart cache check ───────────────────────────────────────────────────────

def _existing_creative(slug: str) -> Optional[dict[str, Any]]:
    """Check if creative_briefs/<slug>/ artifacts exist. Return summary + paths."""
    target = CREATIVE_BRIEFS_DIR / slug
    report_md = target / "report.md"
    metadata_json = target / "metadata.json"
    if not (report_md.exists() and metadata_json.exists()):
        return None
    try:
        meta = json.loads(metadata_json.read_text(encoding="utf-8"))
        return {
            "slug": slug,
            "cached": True,
            "report_path": str(report_md),
            "metadata_path": str(metadata_json),
            "stages_count": len(meta.get("stages", [])),
            "ts": meta.get("ts"),
            "report_size": report_md.stat().st_size,
        }
    except Exception:
        return None


def _existing_wisdom(slug: str) -> Optional[dict[str, Any]]:
    """Check if wisdom_reports/<slug>/ artifacts exist."""
    target = WISDOM_REPORTS_DIR / slug
    report_md = target / "report.md"
    metadata_json = target / "metadata.json"
    structured_json = target / "structured.json"
    if not (report_md.exists() and metadata_json.exists()):
        return None
    try:
        meta = json.loads(metadata_json.read_text(encoding="utf-8"))
        out = {
            "slug": slug,
            "cached": True,
            "report_path": str(report_md),
            "metadata_path": str(metadata_json),
            "stages_count": len(meta.get("stages", [])),
            "ts": meta.get("ts"),
        }
        if structured_json.exists():
            out["structured_path"] = str(structured_json)
            out["structured"] = json.loads(structured_json.read_text(encoding="utf-8"))
        return out
    except Exception:
        return None


# ── Orchestrator ────────────────────────────────────────────────────────────

def integrated_analysis(
    brief: str,
    context: Optional[str] = None,
    *,
    force_regen: bool = False,
    creative_skip_stages: Optional[list[str]] = None,
    wisdom_skip_capabilities: Optional[list[str]] = None,
    enrich_personas: Optional[list[str]] = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Sprint 20: integrated creative + wisdom dalam 1 call dengan smart caching.

    Args:
      brief: input brief atau topic
      context: konteks tambahan untuk wisdom analysis
      force_regen: paksa regenerate creative (skip cache)
      creative_skip_stages: skip stages creative pipeline (cost control)
      wisdom_skip_capabilities: skip stages wisdom analysis
      enrich_personas: untuk creative pipeline (default ["OOMAR","ALEY"])
      persist: save unified report
    """
    if not (brief or "").strip():
        raise ValueError("brief kosong")

    slug = _slugify(brief)
    ts = datetime.now(timezone.utc).isoformat()

    result: dict[str, Any] = {
        "brief": brief,
        "context": context,
        "slug": slug,
        "ts": ts,
        "creative": None,
        "wisdom": None,
        "cache_hits": [],
        "paths": {},
    }

    # ─ Step 1: CREATIVE — reuse cached or generate
    cached_creative = None if force_regen else _existing_creative(slug)
    if cached_creative:
        result["creative"] = cached_creative
        result["cache_hits"].append("creative")
    else:
        try:
            from .creative_pipeline import creative_brief_pipeline
            creative = creative_brief_pipeline(
                brief,
                skip_stages=creative_skip_stages,
                persist=True,
                enrich_personas=enrich_personas,
            )
            # Compact summary (full data ada di file)
            result["creative"] = {
                "slug": creative.get("slug"),
                "cached": False,
                "stages_count": len(creative.get("stages", [])),
                "asset_prompts_count": len(creative.get("asset_prompts", [])),
                "report_path": creative.get("paths", {}).get("report"),
                "metadata_path": creative.get("paths", {}).get("metadata"),
            }
        except Exception as e:
            result["creative"] = {"error": f"creative pipeline failed: {e}"}

    # ─ Step 2: WISDOM — selalu fresh (judgment context-dependent)
    cached_wisdom = None if force_regen else _existing_wisdom(slug)
    if cached_wisdom and not context:
        # Reuse hanya kalau context sama (no new context provided)
        result["wisdom"] = cached_wisdom
        result["cache_hits"].append("wisdom")
    else:
        try:
            from .agent_wisdom import wisdom_analyze
            wisdom = wisdom_analyze(
                brief,
                context=context,
                skip_capabilities=wisdom_skip_capabilities,
                persist=True,
            )
            result["wisdom"] = {
                "slug": wisdom.get("slug"),
                "cached": False,
                "stages_count": len(wisdom.get("stages", [])),
                "trending_keywords": wisdom.get("trending_keywords", []),
                "structured": wisdom.get("structured", {}),
                "report_path": wisdom.get("paths", {}).get("report"),
                "structured_path": wisdom.get("paths", {}).get("structured"),
            }
        except Exception as e:
            result["wisdom"] = {"error": f"wisdom analyze failed: {e}"}

    # ─ Step 3: PERSIST unified report
    if persist:
        target = INTEGRATED_DIR / slug
        target.mkdir(parents=True, exist_ok=True)
        unified_md = _render_unified_md(result)
        report_path = target / "comprehensive_report.md"
        report_path.write_text(unified_md, encoding="utf-8")
        bundle_path = target / "bundle.json"
        bundle_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
        result["paths"] = {
            "comprehensive_report": str(report_path),
            "bundle": str(bundle_path),
        }

    return result


def _render_unified_md(result: dict[str, Any]) -> str:
    lines = [
        f"# SIDIX Comprehensive Analysis — {result['slug']}",
        "",
        f"_Generated_: {result['ts']}",
        f"_Brief_: {result['brief']}",
        f"_Context_: {result.get('context') or '(none)'}",
        f"_Cache hits_: {', '.join(result.get('cache_hits', [])) or '(none — full regenerate)'}",
        f"_Pipeline_: SIDIX Sprint 20 / Integrated Wisdom Output Mode",
        "",
        "---",
        "",
        "## 🎨 Creative Output (UTZ + multi-persona)",
        "",
    ]
    creative = result.get("creative") or {}
    if creative.get("error"):
        lines.append(f"❌ {creative['error']}")
    elif creative.get("report_path"):
        lines.append(f"**Stages**: {creative.get('stages_count', 0)} · **Asset prompts**: {creative.get('asset_prompts_count', 0)}")
        lines.append(f"**Cache**: {'✅ reused' if creative.get('cached') else '🔄 fresh generate'}")
        lines.append(f"**Full report**: [`{creative['report_path']}`]({creative['report_path']})")
    lines.append("")
    lines.append("## 🧠 Wisdom Analysis (5-persona judgment)")
    lines.append("")
    wisdom = result.get("wisdom") or {}
    if wisdom.get("error"):
        lines.append(f"❌ {wisdom['error']}")
    else:
        lines.append(f"**Stages**: {wisdom.get('stages_count', 0)}")
        lines.append(f"**Trending injected**: {', '.join(wisdom.get('trending_keywords', [])) or '(none)'}")
        lines.append(f"**Cache**: {'✅ reused' if wisdom.get('cached') else '🔄 fresh generate'}")
        lines.append(f"**Full report**: [`{wisdom.get('report_path','?')}`]({wisdom.get('report_path','')})")
        structured = wisdom.get("structured") or {}
        if structured:
            lines.append("")
            lines.append("### 📊 Structured Output Summary")
            if "risk_register" in structured:
                lines.append(f"- **Risks identified**: {len(structured['risk_register'])}")
            if "impact_map" in structured:
                lines.append(f"- **Impact stakeholders**: {len(structured['impact_map'])}")
            if "scenario_tree" in structured:
                lines.append(f"- **Scenario paths**: {len(structured['scenario_tree'])}")
            if "optimal_path" in structured:
                op = structured["optimal_path"]
                lines.append(f"- **Optimal path**: `{op.get('path_id','?')}` — {op.get('reasoning','')[:200]}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🎯 Comprehensive Bundle")
    lines.append("")
    lines.append("Customer/dev workflow:")
    lines.append("1. Read this `comprehensive_report.md` untuk overview")
    lines.append("2. Drill-down ke creative `report.md` untuk asset details (prompts, brand, copy)")
    lines.append("3. Drill-down ke wisdom `report.md` untuk judgment narrative")
    lines.append("4. Parse `structured.json` (wisdom) untuk machine-readable risk/impact/scenario")
    lines.append("5. Audio: kalau gen_voice=true di creative, lihat audio/brand_voice.mp3")
    lines.append("6. Visual: kalau gen_images=true di creative, lihat images/*.png")
    lines.append("7. 3D: kalau gen_3d=true di creative, lihat 3d/*.glb")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    brief = " ".join(sys.argv[1:]) or "Launch SIDIX creative pipeline ke pasar UMKM Indonesia"
    result = integrated_analysis(brief)
    print(json.dumps({
        "slug": result["slug"],
        "cache_hits": result["cache_hits"],
        "creative_cached": (result.get("creative") or {}).get("cached"),
        "wisdom_cached": (result.get("wisdom") or {}).get("cached"),
        "paths": result.get("paths"),
    }, indent=2))
