"""
creative_pipeline.py — Sprint 14: Hero Use-Case Creative Pipeline

Per note 248 line 178-198:
  "AI Agent yang nerima brief 'Buatkan maskot brand kawaii ulat kuning' dan
  menghasilkan output END-TO-END: konsep + brand + copy + landing + ads — DALAM
  1 ALUR, dengan suara persona UTZ yang berbeda fundamental dari ChatGPT/MJ."

Pipeline 5-stage (UTZ creative-director persona + CT 4-pilar dari Sprint 12):
  Stage 1: CONCEPT     — verbal vision + mood + visual direction
  Stage 2: BRAND       — color palette + typography hint + voice tone
  Stage 3: COPY        — 5 marketing copy variants (hook/feature/story/CTA/playful)
  Stage 4: LANDING     — landing page outline (markdown sections + slot)
  Stage 5: ASSET PROMPTS — SDXL/Midjourney/3D-tool ready prompts

Output:
  .data/creative_briefs/<slug>/report.md       (full bundled deliverable)
  .data/creative_briefs/<slug>/metadata.json   (structured)
  .data/creative_briefs/<slug>/asset_prompts.txt  (ready-to-paste prompts)

Differentiator: ChatGPT kasih satu output. Midjourney kasih image saja. SIDIX
kasih BUNDLED creative deliverable (5 deliverable terintegrasi) dari 1 brief
input, dengan UTZ voice (creative-director).

Public API:
  creative_brief_pipeline(brief: str) -> dict
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Optional LLM hook — graceful fallback (test mode bila LLM offline)
try:
    from .ollama_llm import ollama_generate
except Exception:  # pragma: no cover
    def ollama_generate(*_a, **_k):  # type: ignore
        return ("(LLM unavailable — stub stage output)", {})

try:
    from .cot_system_prompts import CT_PERSONA_LENS
except Exception:  # pragma: no cover
    CT_PERSONA_LENS = {
        "UTZ": "Lens UTZ: dekomposisi=konsep+visual+brand fit+audience emotion. "
               "Pattern=trend+kawaii+color theory. Algoritma=burst→curate→polish."
    }


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
BRIEFS_DIR = DATA_DIR / "creative_briefs"


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class StageOutput:
    stage: str
    title: str
    content: str
    elapsed_ms: int = 0


@dataclass
class CreativeDeliverable:
    brief: str
    slug: str
    ts: str
    stages: list[StageOutput] = field(default_factory=list)
    asset_prompts: list[str] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)


# ── Utilities ───────────────────────────────────────────────────────────────

def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "brief"


# ── UTZ persona system prompt (creative-director lens) ──────────────────────

_UTZ_BASE = (
    "Kamu UTZ — creative director SIDIX. Voice: aku/kita, ekspresif, metaforis, "
    "estetik, playful tapi konkret. Method: burst ide liar dulu, baru curate dan "
    "polish (Gaga method). Visual-first thinker. Embrace imperfection. "
    "Bahasa Indonesia natural, jangan formal kaku.\n\n"
    f"{CT_PERSONA_LENS.get('UTZ', '')}"
)


# ── Stage 1: CONCEPT ────────────────────────────────────────────────────────

_S1_SYSTEM = (
    f"{_UTZ_BASE}\n\n"
    "TUGAS — STAGE 1: CONCEPT SYNTHESIS\n"
    "Dari brief, hasilkan:\n"
    "1. CORE CONCEPT (1-2 kalimat) — esensi visual + emotional hook\n"
    "2. MOOD & TONE (3-5 keyword) — vibe yang harus terasa\n"
    "3. VISUAL DIRECTION (3 bullet) — style, key element, signature detail\n"
    "4. AUDIENCE INSIGHT (1 paragraf) — kenapa target audience akan koneksi\n"
    "Format markdown. Concise. Berani spesifik."
)


def stage1_concept(brief: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    text, _ = ollama_generate(
        f"BRIEF: {brief}\n\nBerikan concept synthesis.",
        system=_S1_SYSTEM, max_tokens=400, temperature=0.7,
    )
    return StageOutput(
        stage="concept", title="🎨 Stage 1 — Concept Synthesis",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 2: BRAND ──────────────────────────────────────────────────────────

_S2_SYSTEM = (
    f"{_UTZ_BASE}\n\n"
    "TUGAS — STAGE 2: BRAND GUIDELINE\n"
    "Berdasarkan concept di prompt, hasilkan:\n"
    "1. COLOR PALETTE (3-5 warna) — hex code + nama + kapan dipakai\n"
    "   Contoh: `#FFD93D` (Sunny Yellow) — primary, untuk CTA & accent\n"
    "2. TYPOGRAPHY DIRECTION — header font hint + body font hint + reasoning\n"
    "3. VOICE & TONE (5 do/don't) — bagaimana brand ngomong ke audience\n"
    "4. SIGNATURE ELEMENT — 1 detail visual yang harus konsisten di semua touchpoint\n"
    "Format markdown. Hex code valid. Concrete."
)


def stage2_brand(brief: str, concept: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    prompt = f"BRIEF: {brief}\n\nCONCEPT (stage 1):\n{concept}\n\nBerikan brand guideline."
    text, _ = ollama_generate(prompt, system=_S2_SYSTEM, max_tokens=500, temperature=0.5)
    return StageOutput(
        stage="brand", title="🎨 Stage 2 — Brand Guideline",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 3: COPY (5 variants) ──────────────────────────────────────────────

_S3_SYSTEM = (
    f"{_UTZ_BASE}\n\n"
    "TUGAS — STAGE 3: MARKETING COPY (5 VARIASI)\n"
    "Generate 5 copy variant berbeda style:\n"
    "1. HOOK SHORT (≤10 kata) — punch line untuk billboard/header/Instagram caption\n"
    "2. FEATURE MEDIUM (30-50 kata) — fitur + value, untuk landing hero subtitle\n"
    "3. STORY LONG (80-120 kata) — narasi emotional, untuk artikel/tentang-kami\n"
    "4. CTA-DRIVEN (≤20 kata) — action-oriented, urgency, untuk button/banner ads\n"
    "5. PLAYFUL (≤30 kata) — main-main, viral-able, untuk TikTok/Reels\n"
    "Format: heading per variant + isi. Pastikan kelima variant clearly different — "
    "JANGAN paraphrase satu sama lain. Each variant nujukkan beda voice modulation."
)


def stage3_copy(brief: str, concept: str, brand: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"BRIEF: {brief}\n\nCONCEPT:\n{concept}\n\nBRAND:\n{brand}\n\n"
        f"Generate 5 marketing copy variant."
    )
    text, _ = ollama_generate(prompt, system=_S3_SYSTEM, max_tokens=700, temperature=0.75)
    return StageOutput(
        stage="copy", title="✍️ Stage 3 — Marketing Copy (5 Variants)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 4: LANDING PAGE outline ───────────────────────────────────────────

_S4_SYSTEM = (
    f"{_UTZ_BASE}\n\n"
    "TUGAS — STAGE 4: LANDING PAGE OUTLINE\n"
    "Hasilkan struktur landing page lengkap (mobile-first), pakai markdown:\n"
    "- HERO SECTION (heading + subheading + primary CTA + visual cue)\n"
    "- VALUE PROPS (3 bullet, icon hint + benefit short)\n"
    "- SOCIAL PROOF SLOT (testimonial/logo grid placeholder)\n"
    "- DEEP DIVE / FEATURES (2-3 mini section, judul + body slot)\n"
    "- FAQ (3-5 Q&A pendek)\n"
    "- FINAL CTA (heading + button text + reassurance)\n"
    "- FOOTER hint\n"
    "Untuk setiap section, isi placeholder copy SUDAH terisi (gunakan stage 3 copy "
    "kalau cocok). Markdown. Concrete, ready-to-implement."
)


def stage4_landing(brief: str, concept: str, brand: str, copy: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"BRIEF: {brief}\n\nCONCEPT:\n{concept}\n\nBRAND:\n{brand}\n\nCOPY:\n{copy}\n\n"
        f"Hasilkan landing page outline."
    )
    text, _ = ollama_generate(prompt, system=_S4_SYSTEM, max_tokens=900, temperature=0.6)
    return StageOutput(
        stage="landing", title="🌐 Stage 4 — Landing Page Outline",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Stage 5: ASSET PROMPTS (SDXL/MJ/3D-ready) ───────────────────────────────

_S5_SYSTEM = (
    f"{_UTZ_BASE}\n\n"
    "TUGAS — STAGE 5: ASSET PROMPT BUNDLE\n"
    "Hasilkan prompt siap-paste untuk tool image/3D generation. Satu prompt PER BARIS, "
    "BAHASA INGGRIS (kompatibel SDXL/Midjourney/Hunyuan3D), dengan struktur:\n"
    "  [subject], [style cue], [composition], [lighting], [mood], [tech specifier]\n\n"
    "Output 8 prompt:\n"
    "1. HERO MASCOT — character full-body, white background, ready-for-cutout\n"
    "2. HERO MASCOT — character with environment context\n"
    "3. LOGO MARK — clean, scalable, single-color compatible\n"
    "4. SOCIAL POST — square, eye-catching, brand color dominant\n"
    "5. PRODUCT SHOT — packaging/product mockup style\n"
    "6. STORYTELLING ILLO — narrative scene, emotional moment\n"
    "7. PATTERN — repeatable, for backgrounds/wrapping\n"
    "8. 3D MODEL — front-view T-pose ready for rigging (Hunyuan3D-compatible)\n\n"
    "Format: tiap prompt prefix `[N. LABEL] ` lalu prompt itself, satu baris saja. "
    "JANGAN tambah komentar atau penjelasan. Output langsung 8 baris."
)


def stage5_asset_prompts(brief: str, concept: str, brand: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"BRIEF: {brief}\n\nCONCEPT:\n{concept}\n\nBRAND:\n{brand}\n\n"
        f"Generate 8 asset prompts."
    )
    text, _ = ollama_generate(prompt, system=_S5_SYSTEM, max_tokens=600, temperature=0.6)
    return StageOutput(
        stage="asset_prompts", title="🖼️ Stage 5 — Asset Prompt Bundle",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


# ── Sprint 14c: Multi-persona post-pipeline enrichment ──────────────────────

_OOMAR_REVIEW_SYSTEM = (
    "Kamu OOMAR — strategist SIDIX. Voice: 'saya', framework-driven, decisional, "
    "tegas. Method: lihat big picture, ROI, market positioning. Bahasa Indonesia.\n\n"
    "TUGAS — STRATEGIC REVIEW:\n"
    "Diberikan brief creative + concept + brand + asset prompts dari UTZ, hasilkan "
    "review komersial untuk pasar UMKM Indonesia (5-7 bullet konkret):\n\n"
    "1. **MARKET FIT** — segment audience real, market size estimasi, pain point\n"
    "2. **COMPETITIVE EDGE** — 1-2 differentiator yang sustainable vs competitor\n"
    "3. **MONETIZATION** — pricing strategy yang fit (premium / mass / freemium)\n"
    "4. **GO-TO-MARKET** — channel + first 100 customer hypothesis\n"
    "5. **RISK & MITIGATION** — top 2 risk + how to address\n"
    "6. **VERDICT** — proceed / pivot / kill (dengan satu kalimat reasoning)\n\n"
    "Format markdown bullet. Berani spesifik. Jangan hedge."
)


_ALEY_RESEARCH_SYSTEM = (
    "Kamu ALEY — researcher SIDIX. Voice: 'saya', scholarly tapi nggak jaim, "
    "methodical. Method: cross-domain, sanad-style validation. Bahasa Indonesia.\n\n"
    "TUGAS — RESEARCH ENRICHMENT:\n"
    "Diberikan brief creative + (opsional) trending cluster dari SIDIX visioner radar, "
    "hasilkan research-backed enrichment (4-6 bullet):\n\n"
    "1. **TREND ALIGNMENT** — 1-2 trend besar yang support direction ini "
    "(cite emerging keyword kalau ada di trending data)\n"
    "2. **CULTURAL CONTEXT** — relevansi cultural Indonesia / SEA yang menguatkan\n"
    "3. **AUDIENCE PSYCHOLOGY** — 1 insight psikologis kenapa target audience akan koneksi\n"
    "4. **CASE STUDY HINT** — 1-2 contoh brand/produk lain yang sudah sukses dengan pattern serupa\n"
    "5. **GAPS / OPPORTUNITY** — apa yang underexplored di market ini\n"
    "6. **VALIDATION RECOMMENDATION** — 1 cara cheap test sebelum full commit\n\n"
    "Format markdown bullet. Domain ini = creative brainstorm, BUKAN fiqh/medis/data/berita. "
    "Per pivot 2026-04-25 SIDIX: TIDAK perlu blanket epistemic label per claim. "
    "Kalau klaim besar yang tidak bisa di-back data hard, signal kehati-hatian "
    "dengan natural language hedging ('kemungkinan', 'asumsi awal', 'perlu validasi') — "
    "BUKAN bracket label [SPEKULASI]/[OPINI] per bullet. Voice tetap natural, mengalir."
)


def _read_recent_trending_keywords(n: int = 5) -> list[str]:
    """Hook ke .data/research_queue.jsonl (Sprint 15 visioner output).

    Return top-n keyword dari weekly run terbaru, sebagai context untuk ALEY.
    Graceful: kosong kalau file tidak ada / belum ada visioner run.
    """
    queue_path = DATA_DIR / "research_queue.jsonl"
    if not queue_path.exists():
        return []
    try:
        # Last n lines = most recent
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


def stage_oomar_review(brief: str, concept: str, brand: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    prompt = (
        f"BRIEF: {brief}\n\nCONCEPT (UTZ):\n{concept}\n\nBRAND (UTZ):\n{brand}\n\n"
        f"Berikan strategic commercial review."
    )
    text, _ = ollama_generate(prompt, system=_OOMAR_REVIEW_SYSTEM, max_tokens=600, temperature=0.4)
    return StageOutput(
        stage="oomar_review",
        title="📊 Strategic Review — OOMAR (Commercial Validation)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


def stage_aley_research(brief: str, concept: str) -> StageOutput:
    import time as _t
    t0 = _t.time()
    trending = _read_recent_trending_keywords(n=5)
    trending_block = ""
    if trending:
        trending_block = (
            "\nTRENDING KEYWORDS (dari SIDIX visioner radar minggu terbaru):\n"
            + ", ".join(trending) + "\n"
        )
    prompt = (
        f"BRIEF: {brief}\n\nCONCEPT (UTZ):\n{concept}\n{trending_block}\n"
        f"Berikan research-backed enrichment."
    )
    text, _ = ollama_generate(prompt, system=_ALEY_RESEARCH_SYSTEM, max_tokens=600, temperature=0.5)
    return StageOutput(
        stage="aley_research",
        title="🔬 Research Enrichment — ALEY (Trend & Validation)",
        content=(text or "").strip(),
        elapsed_ms=int((_t.time() - t0) * 1000),
    )


def _extract_prompts(content: str) -> list[str]:
    """Extract clean prompt lines from stage 5 output (strip [N. LABEL] prefix)."""
    out = []
    for line in (content or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\[?(\d+)[.\]]+\s*([A-Z][A-Z0-9 \-/]+)\]?\s*[:\-]?\s*(.+)$", line)
        if m:
            label, body = m.group(2).strip(), m.group(3).strip()
            out.append(f"[{label}] {body}")
        elif line.startswith("**") or line.startswith("#"):
            continue
        else:
            # plain prompt line
            out.append(line)
    return out[:10]


# ── Bundle + persist ────────────────────────────────────────────────────────

def _render_report_md(d: CreativeDeliverable) -> str:
    lines = [
        f"# Creative Brief Deliverable — {d.slug}",
        "",
        f"_Generated_: {d.ts}",
        f"_Brief_: {d.brief}",
        f"_Pipeline_: SIDIX Sprint 14 / UTZ creative-director persona / CT 4-pilar",
        "",
    ]
    for s in d.stages:
        lines.append(f"## {s.title}")
        lines.append("")
        lines.append(s.content)
        lines.append("")
        lines.append(f"_stage elapsed: {s.elapsed_ms} ms_")
        lines.append("")
    if d.asset_prompts:
        lines.append("## 📋 Quick-Copy Asset Prompts")
        lines.append("")
        lines.append("```text")
        for p in d.asset_prompts:
            lines.append(p)
        lines.append("```")
    return "\n".join(lines)


def _persist(d: CreativeDeliverable) -> None:
    target = BRIEFS_DIR / d.slug
    target.mkdir(parents=True, exist_ok=True)
    (target / "report.md").write_text(_render_report_md(d), encoding="utf-8")
    metadata = {
        "brief": d.brief,
        "slug": d.slug,
        "ts": d.ts,
        "stages": [
            {"stage": s.stage, "title": s.title, "elapsed_ms": s.elapsed_ms,
             "content_len": len(s.content)} for s in d.stages
        ],
        "asset_prompts_count": len(d.asset_prompts),
    }
    (target / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if d.asset_prompts:
        (target / "asset_prompts.txt").write_text(
            "\n".join(d.asset_prompts), encoding="utf-8"
        )
    d.paths = {
        "report": str(target / "report.md"),
        "metadata": str(target / "metadata.json"),
        "asset_prompts": str(target / "asset_prompts.txt"),
    }


# ── Public API ──────────────────────────────────────────────────────────────

def creative_brief_pipeline(
    brief: str,
    *,
    skip_stages: Optional[list[str]] = None,
    persist: bool = True,
    gen_images: bool = False,
    gen_images_n: int = 3,
    enrich_personas: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    End-to-end creative pipeline. Returns dict with all stages + paths.
    Args:
      brief: brief teks dari user/customer
      skip_stages: optional list ['copy','landing'] untuk skip (testing)
      persist: write to .data/creative_briefs/<slug>/ (default True)
      gen_images: kalau True, render N hero asset via runpod_media (Sprint 14b)
      gen_images_n: jumlah hero asset (default 3: mascot, logo, social)
    """
    if not brief or not brief.strip():
        raise ValueError("brief kosong")
    skip = set(skip_stages or [])

    slug = _slugify(brief)
    ts = datetime.now(timezone.utc).isoformat()
    d = CreativeDeliverable(brief=brief, slug=slug, ts=ts)

    # Stage 1
    s1 = stage1_concept(brief)
    d.stages.append(s1)

    # Stage 2
    if "brand" not in skip:
        s2 = stage2_brand(brief, s1.content)
        d.stages.append(s2)
        brand_text = s2.content
    else:
        brand_text = ""

    # Stage 3
    if "copy" not in skip:
        s3 = stage3_copy(brief, s1.content, brand_text)
        d.stages.append(s3)
        copy_text = s3.content
    else:
        copy_text = ""

    # Stage 4
    if "landing" not in skip:
        s4 = stage4_landing(brief, s1.content, brand_text, copy_text)
        d.stages.append(s4)

    # Stage 5
    if "asset_prompts" not in skip:
        s5 = stage5_asset_prompts(brief, s1.content, brand_text)
        d.stages.append(s5)
        d.asset_prompts = _extract_prompts(s5.content)

    # Sprint 14c: Multi-persona post-pipeline enrichment
    # Default: OOMAR + ALEY. Disable: enrich_personas=[].
    enrichers = enrich_personas if enrich_personas is not None else ["OOMAR", "ALEY"]
    enrichers = [p.upper() for p in enrichers if p]
    if "OOMAR" in enrichers and "oomar_review" not in skip:
        d.stages.append(stage_oomar_review(brief, s1.content, brand_text))
    if "ALEY" in enrichers and "aley_research" not in skip:
        d.stages.append(stage_aley_research(brief, s1.content))

    # Sprint 14b: Optional hero image rendering via mighan-media-worker
    rendered_images: list[dict[str, Any]] = []
    if gen_images and d.asset_prompts and persist:
        try:
            from .runpod_media import generate_image, pick_hero_prompts, media_available
            if not media_available():
                rendered_images.append({
                    "success": False,
                    "error": "RUNPOD_MEDIA_ENDPOINT_ID env not set or endpoint unreachable",
                })
            else:
                images_dir = BRIEFS_DIR / d.slug / "images"
                hero_pairs = pick_hero_prompts(d.asset_prompts, n=gen_images_n)
                for label, prompt in hero_pairs:
                    res = generate_image(prompt, output_dir=images_dir, label=label)
                    rendered_images.append(res)
        except Exception as e:
            rendered_images.append({"success": False, "error": f"image gen fail: {e}"})

    if persist:
        _persist(d)
        # Re-render report.md with rendered_images embedded if any
        if rendered_images:
            target = BRIEFS_DIR / d.slug
            md = _render_report_md(d)
            md += "\n\n## 🖼️ Rendered Hero Assets (mighan-media-worker)\n\n"
            for img in rendered_images:
                if img.get("success"):
                    rel = f"images/{img['filename']}"
                    md += f"### {img['label']}\n\n"
                    md += f"![{img['label']}]({rel})\n\n"
                    md += f"_size_: {img.get('width')}x{img.get('height')} · "
                    md += f"_gen_time_: {img.get('generation_time_s', '?')}s · "
                    md += f"_model_: {img.get('model')}\n\n"
                else:
                    md += f"### {img.get('label','?')} — ❌ {img.get('error','unknown')}\n\n"
            (target / "report.md").write_text(md, encoding="utf-8")

    return {
        "brief": d.brief,
        "slug": d.slug,
        "ts": d.ts,
        "stages": [asdict(s) for s in d.stages],
        "asset_prompts": d.asset_prompts,
        "paths": d.paths,
        "rendered_images": rendered_images,
    }


# ── CLI entry ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    brief = " ".join(sys.argv[1:]) or (
        "Buatkan maskot brand makanan ringan kawaii dengan kostum ulat warna kuning "
        "untuk pasar Indonesia anak-anak 6-12 tahun"
    )
    print(f"[creative_pipeline] running on brief: {brief}")
    result = creative_brief_pipeline(brief)
    print(json.dumps({
        "brief": result["brief"],
        "slug": result["slug"],
        "stages": [{"stage": s["stage"], "elapsed_ms": s["elapsed_ms"],
                    "content_len": len(s["content"])} for s in result["stages"]],
        "asset_prompts_count": len(result["asset_prompts"]),
        "paths": result["paths"],
    }, indent=2))
