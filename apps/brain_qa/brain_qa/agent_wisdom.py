"""
agent_wisdom.py — Sprint 16: Wisdom Layer MVP

Per note 248 line 416-481 (DIMENSI INTUISI & WISDOM).
User directive: "SIDIX harus punya INTUISI + JUDGMENT layer beyond just knowledge."

Pre-Execution Alignment Check (per CLAUDE.md 6.4):
- Note 248 line 469 EXPLICITLY mandate Sprint 16: "Judgment synthesizer module"
- Per-persona judgment style line 446-451 (reuse 5 persona Sprint 12)
- Pivot 2026-04-25: epistemik kontekstual — judgment domain BUKAN sensitive
  → use natural language hedging, BUKAN [SPEKULASI] tag per claim
- 10 hard rules: own LLM, 5 persona preserved, MIT, self-hosted ✓

5 capability stages (sequential, persona-distributed):
  1. UTZ      — AHA MOMENT (creative cross-domain pattern recognition)
  2. OOMAR    — DAMPAK / IMPACT analysis (multi-stakeholder, 2-5 langkah)
  3. ABOO     — RISIKO / RISK analysis (failure modes, mitigation)
  4. ALEY     — SPEKULASI / SCENARIO speculation (best/realistic/worst)
  5. AYMAN    — SYNTHESIZE natural language untuk user

Differentiator vs ChatGPT/Claude:
- Reactive AI (chatgpt/claude): jawab pertanyaan dengan info terkait
- SIDIX wisdom: jawab + warn + suggest + speculate + synthesize
- AI partner advisor, BUKAN AI assistant

Public API:
  wisdom_analyze(topic, context=None, *, persist=True) -> dict
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
        return ("(LLM unavailable — wisdom stub)", {})


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
WISDOM_DIR = DATA_DIR / "wisdom_reports"


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class WisdomStage:
    capability: str    # aha | impact | risk | speculation | synthesis
    persona: str       # UTZ | OOMAR | ABOO | ALEY | AYMAN
    title: str
    content: str
    elapsed_ms: int = 0


@dataclass
class WisdomAnalysis:
    topic: str
    context: str
    slug: str
    ts: str
    stages: list[WisdomStage] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)


def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "topic"


# ── Sprint 18: structured JSON extractor (risk_register + impact_map) ───────

def _extract_json_block(text: str, key: str) -> Optional[dict]:
    """Extract first valid JSON block dari LLM output that contains given top-key.

    Format target: ```json\n{"<key>": [...]}\n```
    Graceful: return None kalau tidak parseable atau key tidak ada.
    """
    if not text:
        return None
    # Find ```json ... ``` blocks
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", re.DOTALL)
    for m in fence_pattern.finditer(text):
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, dict) and key in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    # Fallback: try parse standalone JSON dict that mentions key
    brace_pattern = re.compile(r"(\{[^{}]*\"" + re.escape(key) + r"\"\s*:\s*\[.*?\]\s*\})", re.DOTALL)
    for m in brace_pattern.finditer(text):
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, dict) and key in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    return None


# ── Visioner trending hook (compound Sprint 14c pattern) ────────────────────

def _read_recent_trending(n: int = 5) -> list[str]:
    """Reuse pattern dari creative_pipeline Sprint 14c — auto-pickup trending
    keyword dari Sprint 15 visioner.
    """
    queue_path = DATA_DIR / "research_queue.jsonl"
    if not queue_path.exists():
        return []
    try:
        with open(queue_path, encoding="utf-8") as f:
            lines = f.readlines()
        keywords: list[str] = []
        for line in reversed(lines[-50:]):
            try:
                d = json.loads(line)
                kw = (d.get("topic") or "").strip()
                if kw and kw not in keywords:
                    keywords.append(kw)
                if len(keywords) >= n:
                    break
            except Exception:
                continue
        return keywords
    except Exception:
        return []


# ── Stage 1: AHA MOMENT (UTZ creative cross-domain) ─────────────────────────

_UTZ_AHA_SYSTEM = (
    "Kamu UTZ — creative director SIDIX. Voice: 'aku', metaforis, ekspresif, "
    "playful. Method: burst koneksi liar lintas domain (Gaga method). "
    "Bahasa Indonesia.\n\n"
    "TUGAS — AHA MOMENT (Eureka):\n"
    "Diberikan topik/keputusan, hasilkan 2-3 koneksi UNEXPECTED dari domain "
    "berbeda yang bisa membuka angle baru:\n\n"
    "1. **Koneksi A** — bridge ke domain X (creative, biology, music, history, dll)\n"
    "2. **Koneksi B** — bridge ke domain Y\n"
    "3. **Pattern emergent** — kalau A + B digabung, apa yang baru muncul?\n\n"
    "Format: pendek (3-5 kalimat per koneksi), spesifik, BUKAN abstrak. "
    "Pakai natural language ('mirip seperti', 'paralel dengan'), BUKAN bracket "
    "tag epistemik per claim. Voice mengalir."
)


def stage_aha_moment(topic: str, context: str, trending: list[str]) -> WisdomStage:
    import time as _t
    t0 = _t.time()
    trend_block = (
        f"\nTRENDING DATA (visioner radar):\n{', '.join(trending)}\n"
        if trending else ""
    )
    prompt = f"TOPIK: {topic}\n\nKONTEKS: {context}\n{trend_block}\nBerikan 2-3 aha moment koneksi unexpected lintas domain."
    text, _ = ollama_generate(prompt, system=_UTZ_AHA_SYSTEM, max_tokens=500, temperature=0.85)
    return WisdomStage(
        capability="aha",
        persona="UTZ",
        title="✨ Aha Moment — UTZ (Creative Cross-Domain)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 2: IMPACT analysis (OOMAR business, multi-stakeholder) ────────────

_OOMAR_IMPACT_SYSTEM = (
    "Kamu OOMAR — strategist SIDIX. Voice: 'saya', framework-driven, decisional. "
    "Bahasa Indonesia.\n\n"
    "TUGAS — DAMPAK ANALYSIS (Impact Foresight):\n"
    "Project consequence dari topik/keputusan ini 2-5 langkah ke depan. "
    "Multi-stakeholder view:\n\n"
    "1. **USER/CUSTOMER** — dampak jangka pendek (3 bulan) + panjang (1-2 tahun)\n"
    "2. **AUDIENCE/MARKET** — perception shift, market dynamics\n"
    "3. **BRAND/PRODUCT** — positioning impact, competitive consequence\n"
    "4. **EKOSISTEM/PARTNER** — ripple effect ke partner/supplier/ecosystem\n\n"
    "Format markdown. Berani spesifik. Quantitative kalau bisa (estimasi range). "
    "Hedging via natural language ('cenderung', 'kemungkinan besar'), BUKAN "
    "bracket tag per claim.\n\n"
    "**SETELAH markdown analysis di atas**, sertakan blok JSON parseable di akhir "
    "(WAJIB exact format ini, gunakan triple-backtick json fence):\n\n"
    "```json\n"
    "{\"impact_map\": [\n"
    "  {\"stakeholder\": \"User/Customer\", \"short_term\": \"...\", \"long_term\": \"...\", \"severity\": \"high|medium|low\"},\n"
    "  {\"stakeholder\": \"Audience/Market\", \"short_term\": \"...\", \"long_term\": \"...\", \"severity\": \"...\"},\n"
    "  {\"stakeholder\": \"Brand/Product\", \"short_term\": \"...\", \"long_term\": \"...\", \"severity\": \"...\"},\n"
    "  {\"stakeholder\": \"Ekosistem/Partner\", \"short_term\": \"...\", \"long_term\": \"...\", \"severity\": \"...\"}\n"
    "]}\n"
    "```\n\n"
    "JSON harus valid — pastikan strings escaped, no trailing commas. "
    "Fields short_term/long_term: 1 kalimat singkat per stakeholder."
)


def stage_impact_analysis(topic: str, context: str, aha_summary: str) -> WisdomStage:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"TOPIK: {topic}\n\nKONTEKS: {context}\n\nAHA MOMENT (UTZ):\n{aha_summary}\n\n"
        f"Berikan multi-stakeholder impact analysis 2-5 langkah ke depan."
    )
    text, _ = ollama_generate(prompt, system=_OOMAR_IMPACT_SYSTEM, max_tokens=600, temperature=0.4)
    return WisdomStage(
        capability="impact",
        persona="OOMAR",
        title="📊 Dampak Analysis — OOMAR (Multi-Stakeholder)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 3: RISK analysis (ABOO technical adversarial) ─────────────────────

_ABOO_RISK_SYSTEM = (
    "Kamu ABOO — engineer SIDIX. Voice: 'gue', presisi, nyelekit, fail-fast. "
    "Bahasa Indonesia.\n\n"
    "TUGAS — RISIKO ANALYSIS (Risk Sensing):\n"
    "Adversarial thinking: kalau salah, gimana? Identify failure modes "
    "SEBELUM eksekusi:\n\n"
    "1. **TOP 3 RISK** — masing-masing dengan:\n"
    "   - probability (low/medium/high)\n"
    "   - impact severity (low/medium/high)\n"
    "   - failure mode konkret\n"
    "2. **MITIGATION** — untuk tiap risk, 1 langkah konkret\n"
    "3. **HIDDEN DEPENDENCIES** — apa yang bisa break tapi gak obvious\n"
    "4. **COST ANALYSIS** — waktu/compute/reputasi/opportunity cost\n\n"
    "Format markdown. JANGAN sugar coat. Berani brutal honest. Hedging via "
    "natural language ('berisiko tinggi kalau', 'gampang gagal saat'), BUKAN "
    "bracket tag epistemik.\n\n"
    "**SETELAH markdown analysis di atas**, sertakan blok JSON parseable di akhir "
    "(WAJIB exact format ini, gunakan triple-backtick json fence):\n\n"
    "```json\n"
    "{\"risk_register\": [\n"
    "  {\"risk\": \"failure mode singkat\", \"probability\": \"high|medium|low\", \"impact\": \"high|medium|low\", \"mitigation\": \"langkah konkret\", \"reasoning\": \"kenapa ini risiko nyata\"},\n"
    "  {\"risk\": \"...\", \"probability\": \"...\", \"impact\": \"...\", \"mitigation\": \"...\", \"reasoning\": \"...\"},\n"
    "  {\"risk\": \"...\", \"probability\": \"...\", \"impact\": \"...\", \"mitigation\": \"...\", \"reasoning\": \"...\"}\n"
    "]}\n"
    "```\n\n"
    "JSON harus valid — strings escaped, no trailing commas. Top 3 risk paling "
    "kritikal. Reasoning konkret (1 kalimat), bukan vague."
)


def stage_risk_analysis(topic: str, context: str) -> WisdomStage:
    import time as _t
    t0 = _t.time()
    prompt = f"TOPIK: {topic}\n\nKONTEKS: {context}\n\nBerikan risk register adversarial."
    text, _ = ollama_generate(prompt, system=_ABOO_RISK_SYSTEM, max_tokens=600, temperature=0.45)
    return WisdomStage(
        capability="risk",
        persona="ABOO",
        title="⚠️ Risiko Analysis — ABOO (Adversarial Risk Register)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 4: SPECULATION tree (ALEY scenario, multi-path) ───────────────────

_ALEY_SCENARIO_SYSTEM = (
    "Kamu ALEY — researcher SIDIX. Voice: 'saya', methodical, scholarly. "
    "Bahasa Indonesia.\n\n"
    "TUGAS — SPEKULASI TERBAIK (Best-Case Speculation):\n"
    "Generate scenario tree dengan 3 jalur untuk topik ini:\n\n"
    "1. **JALUR A — BEST CASE** (probability ~25%, optimistic plausible)\n"
    "   - outcome konkret 1-2 paragraf\n"
    "   - trigger event yang harus terjadi\n"
    "   - leading indicator yang bisa di-monitor\n\n"
    "2. **JALUR B — REALISTIC CASE** (~50%, paling mungkin)\n"
    "   - outcome konkret\n"
    "   - asumsi inti yang dijaga\n\n"
    "3. **JALUR C — WORST CASE** (~25%, pessimistic plausible)\n"
    "   - outcome konkret\n"
    "   - failure trigger\n\n"
    "4. **OPTIMAL PATH RECOMMENDATION** — jalur mana yang sebaiknya dikejar + reasoning singkat\n\n"
    "Format markdown. Berani spesifik. Domain ini = scenario speculation, "
    "BUKAN data sensitif — pakai natural hedging ('kemungkinan besar', "
    "'asumsi awal'), BUKAN bracket [SPEKULASI] tag per claim."
)


def stage_speculation_tree(topic: str, context: str, impact_summary: str, risk_summary: str) -> WisdomStage:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"TOPIK: {topic}\n\nKONTEKS: {context}\n\n"
        f"IMPACT (OOMAR):\n{impact_summary}\n\nRISK (ABOO):\n{risk_summary}\n\n"
        f"Generate scenario tree 3 jalur + optimal path recommendation."
    )
    text, _ = ollama_generate(prompt, system=_ALEY_SCENARIO_SYSTEM, max_tokens=800, temperature=0.5)
    return WisdomStage(
        capability="speculation",
        persona="ALEY",
        title="🌳 Spekulasi Terbaik — ALEY (3-Path Scenario Tree)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 5: SYNTHESIS (AYMAN natural language untuk user) ──────────────────

_AYMAN_SYNTH_SYSTEM = (
    "Kamu AYMAN — pendengar hangat SIDIX. Voice: 'aku' atau 'kita', empati, "
    "analogi sederhana, accessible untuk audience awam. Bahasa Indonesia.\n\n"
    "TUGAS — SYNTHESIZE wisdom analysis dari 4 persona ke dalam **1 closing "
    "statement** yang user bisa langsung pakai (5-7 kalimat):\n\n"
    "1. Highlight 1 aha moment paling impactful (dari UTZ)\n"
    "2. Risiko paling kritikal yang harus diperhatikan (dari ABOO)\n"
    "3. Optimal path recommendation (dari ALEY)\n"
    "4. Verdict: proceed / pivot / wait — dengan 1 kalimat reasoning\n"
    "5. 1 langkah aksi konkret HARI INI\n\n"
    "Format: prose mengalir, BUKAN bullet list. Voice hangat tapi decisional. "
    "Natural hedging, BUKAN bracket tag."
)


def stage_synthesis(topic: str, aha: str, impact: str, risk: str, speculation: str) -> WisdomStage:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"TOPIK: {topic}\n\n"
        f"AHA (UTZ):\n{aha}\n\nIMPACT (OOMAR):\n{impact}\n\n"
        f"RISK (ABOO):\n{risk}\n\nSPECULATION (ALEY):\n{speculation}\n\n"
        f"Synthesize jadi closing statement actionable."
    )
    text, _ = ollama_generate(prompt, system=_AYMAN_SYNTH_SYSTEM, max_tokens=400, temperature=0.6)
    return WisdomStage(
        capability="synthesis",
        persona="AYMAN",
        title="🎯 Synthesis — AYMAN (Actionable Closing)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Bundle + persist ────────────────────────────────────────────────────────

def _render_report_md(w: WisdomAnalysis) -> str:
    lines = [
        f"# SIDIX Wisdom Analysis — {w.slug}",
        "",
        f"_Generated_: {w.ts}",
        f"_Topic_: {w.topic}",
        f"_Context_: {w.context or '(none)'}",
        f"_Pipeline_: SIDIX Sprint 16 / 5-persona judgment synthesizer",
        "",
        "---",
        "",
    ]
    for s in w.stages:
        lines.append(f"## {s.title}")
        lines.append("")
        lines.append(s.content)
        lines.append("")
        lines.append(f"_persona: {s.persona} · capability: {s.capability} · elapsed: {s.elapsed_ms}ms_")
        lines.append("")
    return "\n".join(lines)


def _persist(w: WisdomAnalysis) -> None:
    target = WISDOM_DIR / w.slug
    target.mkdir(parents=True, exist_ok=True)
    (target / "report.md").write_text(_render_report_md(w), encoding="utf-8")
    metadata = {
        "topic": w.topic,
        "context": w.context,
        "slug": w.slug,
        "ts": w.ts,
        "stages": [
            {"capability": s.capability, "persona": s.persona,
             "elapsed_ms": s.elapsed_ms, "content_len": len(s.content)}
            for s in w.stages
        ],
    }
    (target / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    w.paths = {
        "report": str(target / "report.md"),
        "metadata": str(target / "metadata.json"),
    }


# ── Public API ──────────────────────────────────────────────────────────────

def wisdom_analyze(
    topic: str,
    context: Optional[str] = None,
    *,
    skip_capabilities: Optional[list[str]] = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Sprint 16 wisdom analysis pipeline.

    Args:
      topic: topik/keputusan yang ingin dianalisis
      context: konteks tambahan (opsional)
      skip_capabilities: list ['aha','impact','risk','speculation','synthesis']
      persist: write to .data/wisdom_reports/<slug>/
    """
    if not topic or not topic.strip():
        raise ValueError("topic kosong")
    skip = set((skip_capabilities or []))
    ctx = (context or "").strip()
    slug = _slugify(topic)
    ts = datetime.now(timezone.utc).isoformat()
    w = WisdomAnalysis(topic=topic, context=ctx, slug=slug, ts=ts)
    trending = _read_recent_trending(n=5)

    # Stage 1: AHA (UTZ)
    if "aha" not in skip:
        w.stages.append(stage_aha_moment(topic, ctx, trending))
    aha_text = next((s.content for s in w.stages if s.capability == "aha"), "")

    # Stage 2: IMPACT (OOMAR) — depends on aha
    if "impact" not in skip:
        w.stages.append(stage_impact_analysis(topic, ctx, aha_text))
    impact_text = next((s.content for s in w.stages if s.capability == "impact"), "")

    # Stage 3: RISK (ABOO) — independent
    if "risk" not in skip:
        w.stages.append(stage_risk_analysis(topic, ctx))
    risk_text = next((s.content for s in w.stages if s.capability == "risk"), "")

    # Stage 4: SPECULATION (ALEY) — depends on impact + risk
    if "speculation" not in skip:
        w.stages.append(stage_speculation_tree(topic, ctx, impact_text, risk_text))
    spec_text = next((s.content for s in w.stages if s.capability == "speculation"), "")

    # Stage 5: SYNTHESIS (AYMAN) — depends on all
    if "synthesis" not in skip:
        w.stages.append(stage_synthesis(topic, aha_text, impact_text, risk_text, spec_text))

    # Sprint 18: extract structured JSON from ABOO + OOMAR prose stages
    structured: dict[str, Any] = {}
    risk_stage = next((s for s in w.stages if s.capability == "risk"), None)
    impact_stage = next((s for s in w.stages if s.capability == "impact"), None)
    if risk_stage:
        risk_obj = _extract_json_block(risk_stage.content, "risk_register")
        if risk_obj:
            structured["risk_register"] = risk_obj.get("risk_register", [])
    if impact_stage:
        impact_obj = _extract_json_block(impact_stage.content, "impact_map")
        if impact_obj:
            structured["impact_map"] = impact_obj.get("impact_map", [])

    if persist:
        _persist(w)
        # Save structured.json bila ada structured data
        if structured:
            target = WISDOM_DIR / w.slug
            (target / "structured.json").write_text(
                json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            w.paths["structured"] = str(target / "structured.json")

    return {
        "topic": w.topic,
        "context": w.context,
        "slug": w.slug,
        "ts": w.ts,
        "trending_keywords": trending,
        "stages": [asdict(s) for s in w.stages],
        "structured": structured,  # Sprint 18: machine-readable risk_register + impact_map
        "paths": w.paths,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) or "Launch SIDIX creative pipeline ke pasar UMKM Indonesia Q3 2026"
    result = wisdom_analyze(topic)
    print(json.dumps({
        "slug": result["slug"],
        "stages": [{"capability": s["capability"], "persona": s["persona"],
                    "elapsed_ms": s["elapsed_ms"], "len": len(s["content"])}
                   for s in result["stages"]],
        "paths": result["paths"],
    }, indent=2))
