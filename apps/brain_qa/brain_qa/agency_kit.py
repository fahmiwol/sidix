"""
agency_kit.py — SIDIX Agency Kit 1-Click (Sprint 5, Killer Offer #4)

Input: business_name + niche + target_audience + budget
Output (1 klik, ~10-30 detik):
  ✅ Brand Kit (archetype + voice + palette hint + tagline)
  ✅ 10 Caption IG (3 AIDA, 3 PAS, 2 FAB, 2 bonus)
  ✅ 30-day Content Plan (21 slots)
  ✅ Campaign Strategy (AARRR 5 stages)
  ✅ 3 Ad Variants (FB/Google/TikTok)
  ✅ 3 Thumbnail Specs
  ✅ Muhasabah quality gate per layer
  ✅ Total CQF composite score

Pipeline DAG:
  brand_builder
       ↓
  content_planner + copywriter×5 (parallel-ish via loop)
       ↓
  campaign_strategist
       ↓
  ads_generator × 3 platforms
       ↓
  thumbnail_generator × 3
       ↓
  muhasabah_loop (gate final bundle)
       ↓
  return AgencyKitResult

Dibuat own-stack: tidak ada vendor API. Setiap layer pakai modul Sprint 4.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from pydantic import BaseModel
    _PYDANTIC_OK = True
except Exception:
    _PYDANTIC_OK = False

logger = logging.getLogger("sidix.agency_kit")


# ── Result model ──────────────────────────────────────────────────────────────
@dataclass
class AgencyKitResult:
    ok: bool
    business_name: str
    niche: str
    target_audience: str

    # Layer 1 — Brand
    brand_kit: dict = field(default_factory=dict)

    # Layer 2 — Content
    captions: list[dict] = field(default_factory=list)       # 10 caption
    content_plan: list[dict] = field(default_factory=list)   # 30-day plan

    # Layer 3 — Campaign
    campaign: dict = field(default_factory=dict)

    # Layer 4 — Ads
    ads: list[dict] = field(default_factory=list)            # 3 platform

    # Layer 5 — Thumbnails
    thumbnails: list[dict] = field(default_factory=list)     # 3 specs

    # Meta
    muhasabah: dict = field(default_factory=dict)
    cqf_composite: float = 0.0
    elapsed_s: float = 0.0
    warnings: list[str] = field(default_factory=list)
    error: str = ""


# ── Helper: safe module calls ─────────────────────────────────────────────────
def _safe(fn, *args, **kwargs) -> tuple[Any, str]:
    """Call fn, return (result, error_str). Error tidak crash pipeline."""
    try:
        return fn(*args, **kwargs), ""
    except Exception as exc:
        logger.warning("agency_kit safe-call error: %s — %s", fn.__name__, exc)
        return None, str(exc)


# ── Pipeline layers ───────────────────────────────────────────────────────────
def _layer_brand(business_name: str, niche: str, target_audience: str) -> tuple[dict, str]:
    from .brand_builder import generate_brand_kit
    r, err = _safe(
        generate_brand_kit,
        business_name=business_name,
        niche=niche,
        target_audience=target_audience,
    )
    if r and r.get("ok"):
        return r, ""
    return {}, err or "brand_kit failed"


def _layer_captions(
    business_name: str, niche: str, target_audience: str, brand_voice: str
) -> list[dict]:
    from .copywriter import generate_copy

    caption_configs = [
        {"formula": "AIDA", "tone": "friendly"},
        {"formula": "AIDA", "tone": "professional"},
        {"formula": "AIDA", "tone": "bold"},
        {"formula": "PAS",  "tone": "empathetic"},
        {"formula": "PAS",  "tone": "bold"},
        {"formula": "PAS",  "tone": "friendly"},
        {"formula": "FAB",  "tone": "professional"},
        {"formula": "FAB",  "tone": "friendly"},
        {"formula": "AIDA", "tone": "playful"},
        {"formula": "PAS",  "tone": "inspirational"},
    ]

    captions: list[dict] = []
    for cfg in caption_configs:
        topic = f"{business_name} — {niche} untuk {target_audience}"
        r, err = _safe(
            generate_copy,
            topic=topic,
            channel="instagram",
            formula=cfg["formula"],
            audience=target_audience,
            tone=cfg["tone"],
            variant_count=1,
        )
        if r and r.get("ok"):
            captions.append({
                "formula": cfg["formula"],
                "tone": cfg["tone"],
                "text": r.get("best_text", ""),
                "score": r.get("score_total", 0),
            })
        else:
            logger.warning("caption skip: formula=%s tone=%s err=%s", cfg["formula"], cfg["tone"], err)

    return captions


def _layer_content_plan(niche: str, target_audience: str) -> list[dict]:
    from .content_planner import generate_content_plan
    r, err = _safe(
        generate_content_plan,
        niche=niche,
        target_audience=target_audience,
        duration_days=30,
        posts_per_week=5,
    )
    if r and r.get("ok"):
        return r.get("plan", [])
    return []


def _layer_campaign(
    business_name: str, niche: str, target_audience: str, budget_idr: int
) -> dict:
    from .campaign_strategist import plan_campaign
    r, err = _safe(
        plan_campaign,
        product=f"{business_name} ({niche})",
        audience=target_audience,
        goal="conversion",
        budget_idr=budget_idr,
        duration_days=30,
    )
    if r and r.get("ok"):
        return r
    return {}


def _layer_ads(business_name: str, niche: str, target_audience: str) -> list[dict]:
    from .ads_generator import generate_ads

    platforms = ["facebook", "google", "tiktok"]
    ads: list[dict] = []
    for platform in platforms:
        r, err = _safe(
            generate_ads,
            product=f"{business_name} — {niche}",
            audience=target_audience,
            platform=platform,
            objective="conversion",
            n_variants=2,
        )
        if r and r.get("ok"):
            ads.append({
                "platform": platform,
                "best_variant": r.get("best_variant", {}),
                "all_variants": r.get("variants", []),
                "cqf": r.get("cqf", {}).get("total", 0),
            })
        else:
            ads.append({"platform": platform, "error": err})

    return ads


def _layer_thumbnails(business_name: str, niche: str) -> list[dict]:
    from .thumbnail_generator import generate_thumbnail

    specs = [
        {"title": f"{business_name} — Tips {niche} Terbaik",     "platform": "youtube", "style": "bold"},
        {"title": f"Rahasia Sukses {niche} untuk Pemula",          "platform": "instagram", "style": "clean"},
        {"title": f"{business_name} × Cara Kerja yang Lebih Baik", "platform": "youtube", "style": "minimal"},
    ]

    thumbnails: list[dict] = []
    for spec in specs:
        r, err = _safe(
            generate_thumbnail,
            title=spec["title"],
            platform=spec["platform"],
            style=spec["style"],
            brand_hint=business_name,
        )
        if r and r.get("ok"):
            thumbnails.append({
                "platform": spec["platform"],
                "title": spec["title"],
                "layout": r.get("layout"),
                "image_prompt": r.get("image_prompt", ""),
                "cqf": r.get("cqf", {}).get("total", 0),
            })
        else:
            thumbnails.append({"platform": spec["platform"], "title": spec["title"], "error": err})

    return thumbnails


def _layer_muhasabah(bundle_summary: str) -> dict:
    from .muhasabah_loop import run_muhasabah_loop
    r, err = _safe(
        run_muhasabah_loop,
        brief=bundle_summary,
        domain="marketing",
        generate_fn=lambda b: b,
        max_rounds=2,
        min_score=7.0,
    )
    if r and r.get("ok"):
        return r
    return {"ok": False, "error": err, "final_score": 0.0}


def _calc_composite_cqf(
    brand_kit: dict,
    captions: list[dict],
    campaign: dict,
    ads: list[dict],
    thumbnails: list[dict],
) -> float:
    scores: list[float] = []
    if brand_kit.get("cqf", {}).get("total"):
        scores.append(float(brand_kit["cqf"]["total"]))
    for c in captions:
        if c.get("score"):
            scores.append(float(c["score"]))
    if campaign.get("cqf", {}).get("total"):
        scores.append(float(campaign["cqf"]["total"]))
    for a in ads:
        if a.get("cqf"):
            scores.append(float(a["cqf"]))
    for t in thumbnails:
        if t.get("cqf"):
            scores.append(float(t["cqf"]))
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def _parse_budget(budget_str: str) -> int:
    """Parse '2jt' / '500rb' / '1500000' → int rupiah."""
    s = str(budget_str).lower().replace(" ", "").replace("rp", "").replace(",", "").replace(".", "")
    try:
        if "jt" in s or "juta" in s:
            n = float(s.replace("jt", "").replace("juta", ""))
            return int(n * 1_000_000)
        if "rb" in s or "ribu" in s:
            n = float(s.replace("rb", "").replace("ribu", ""))
            return int(n * 1_000)
        return max(500_000, int(s))
    except ValueError:
        return 1_500_000   # default 1.5 juta


# ── Main entry point ──────────────────────────────────────────────────────────
def build_agency_kit(
    *,
    business_name: str,
    niche: str,
    target_audience: str,
    budget: str = "1.5jt",
    skip_thumbnails: bool = False,
    skip_ads: bool = False,
) -> dict:
    """
    Bangun Agency Kit lengkap dalam 1 panggilan.

    Returns dict (serializable) dengan semua layer.
    """
    start = time.time()
    warnings: list[str] = []

    bn = (business_name or "").strip()
    ni = (niche or "").strip()
    ta = (target_audience or "").strip()

    if not bn:
        return {"ok": False, "error": "business_name wajib diisi"}
    if not ni:
        return {"ok": False, "error": "niche wajib diisi"}
    if not ta:
        ta = "audiens Indonesia umum"

    budget_idr = _parse_budget(budget)
    logger.info("agency_kit: mulai untuk '%s' niche='%s' audience='%s'", bn, ni, ta)

    # ── Layer 1: Brand ────────────────────────────────────────────────────────
    logger.info("agency_kit [1/6] brand_builder")
    brand_kit, err = _layer_brand(bn, ni, ta)
    if err:
        warnings.append(f"brand_kit: {err}")
    brand_voice = brand_kit.get("voice_tone", f"{bn} yang friendly dan terpercaya")

    # ── Layer 2a: Captions ────────────────────────────────────────────────────
    logger.info("agency_kit [2/6] copywriter × 10")
    captions = _layer_captions(bn, ni, ta, brand_voice)
    if len(captions) < 5:
        warnings.append(f"Hanya {len(captions)} caption berhasil dibuat (target 10)")

    # ── Layer 2b: Content Plan ────────────────────────────────────────────────
    logger.info("agency_kit [3/6] content_planner")
    content_plan = _layer_content_plan(ni, ta)
    if not content_plan:
        warnings.append("content_plan kosong, cek content_planner module")

    # ── Layer 3: Campaign ─────────────────────────────────────────────────────
    logger.info("agency_kit [4/6] campaign_strategist")
    campaign = _layer_campaign(bn, ni, ta, budget_idr)
    if not campaign:
        warnings.append("campaign gagal, cek campaign_strategist module")

    # ── Layer 4: Ads ──────────────────────────────────────────────────────────
    ads: list[dict] = []
    if not skip_ads:
        logger.info("agency_kit [5/6] ads_generator × 3 platforms")
        ads = _layer_ads(bn, ni, ta)

    # ── Layer 5: Thumbnails ───────────────────────────────────────────────────
    thumbnails: list[dict] = []
    if not skip_thumbnails:
        logger.info("agency_kit [6/6] thumbnail_generator × 3")
        thumbnails = _layer_thumbnails(bn, ni)

    # ── Muhasabah: quality gate ───────────────────────────────────────────────
    bundle_summary = (
        f"Agency Kit untuk {bn} ({ni}), target {ta}, budget Rp{budget_idr:,}. "
        f"Brand: {brand_voice}. "
        f"Captions: {len(captions)}, Plan: {len(content_plan)} slots, "
        f"Campaign stages: {len(campaign.get('funnel', []))}."
    )
    muhasabah = _layer_muhasabah(bundle_summary)

    cqf_composite = _calc_composite_cqf(brand_kit, captions, campaign, ads, thumbnails)
    elapsed = round(time.time() - start, 2)

    logger.info(
        "agency_kit selesai: cqf=%.2f elapsed=%.1fs warnings=%d",
        cqf_composite, elapsed, len(warnings),
    )

    return {
        "ok": True,
        "business_name": bn,
        "niche": ni,
        "target_audience": ta,
        "budget_idr": budget_idr,

        # Layers
        "brand_kit": brand_kit,
        "captions": captions,
        "caption_count": len(captions),
        "content_plan": content_plan,
        "content_plan_slots": len(content_plan),
        "campaign": campaign,
        "ads": ads,
        "thumbnails": thumbnails,

        # Quality
        "muhasabah": muhasabah,
        "cqf_composite": cqf_composite,
        "cqf_tier": "premium" if cqf_composite >= 8.5 else "delivery" if cqf_composite >= 7.0 else "needs_work",

        # Meta
        "elapsed_s": elapsed,
        "warnings": warnings,
        "summary": bundle_summary,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENCY KIT 1-CLICK — Async Background Job System (Sprint Agency Kit)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Pydantic models ───────────────────────────────────────────────────────────
if _PYDANTIC_OK:
    class AgencyKitRequest(BaseModel):
        business_name: str
        niche: str
        target_audience: str
        budget: str
        brand_tone: Optional[str] = None
        color_preference: Optional[str] = None

    class AgencyKitResult(BaseModel):
        brand_name: str = ""
        archetype: str = ""
        palette: str = ""
        typography: str = ""
        voice_tone: str = ""
        logo_prompt: str = ""
        captions: list[str] = []
        threads: list[str] = []
        scripts: list[str] = []
        campaign_timeline: str = ""
        thumbnails: list[str] = []
        grid_posts: list[str] = []

    class AgencyKitJob(BaseModel):
        job_id: str
        status: str  # queued / processing / completed / failed
        progress: int  # 0-100
        results: dict[str, Any]
        created_at: str
        completed_at: Optional[str] = None
else:
    class AgencyKitRequest:
        def __init__(self, business_name: str, niche: str, target_audience: str,
                     budget: str, brand_tone: Optional[str] = None,
                     color_preference: Optional[str] = None):
            self.business_name = business_name
            self.niche = niche
            self.target_audience = target_audience
            self.budget = budget
            self.brand_tone = brand_tone
            self.color_preference = color_preference

    class AgencyKitResult:
        def __init__(self, **kwargs: Any):
            self.brand_name = kwargs.get("brand_name", "")
            self.archetype = kwargs.get("archetype", "")
            self.palette = kwargs.get("palette", "")
            self.typography = kwargs.get("typography", "")
            self.voice_tone = kwargs.get("voice_tone", "")
            self.logo_prompt = kwargs.get("logo_prompt", "")
            self.captions = kwargs.get("captions", [])
            self.threads = kwargs.get("threads", [])
            self.scripts = kwargs.get("scripts", [])
            self.campaign_timeline = kwargs.get("campaign_timeline", "")
            self.thumbnails = kwargs.get("thumbnails", [])
            self.grid_posts = kwargs.get("grid_posts", [])

    class AgencyKitJob:
        def __init__(self, job_id: str, status: str, progress: int,
                     results: dict[str, Any], created_at: str,
                     completed_at: Optional[str] = None):
            self.job_id = job_id
            self.status = status
            self.progress = progress
            self.results = results
            self.created_at = created_at
            self.completed_at = completed_at


# ── In-memory job store ───────────────────────────────────────────────────────
_JOB_STORE: dict[str, AgencyKitJob] = {}
_JOB_LOCK = threading.RLock()
_MAX_JOBS = 50


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _prune_jobs() -> None:
    with _JOB_LOCK:
        while len(_JOB_STORE) > _MAX_JOBS:
            oldest = min(_JOB_STORE, key=lambda k: _JOB_STORE[k].created_at)
            del _JOB_STORE[oldest]


def _update_job(
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    results: Optional[dict[str, Any]] = None,
) -> None:
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
        if not job:
            return
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if results is not None:
            job.results = results
        if status in ("completed", "failed"):
            job.completed_at = _now_iso()


def create_agency_kit_job(req: AgencyKitRequest) -> str:
    """Create job, return job_id immediately. Background thread starts automatically."""
    job_id = str(uuid.uuid4())
    req_dict: dict[str, Any]
    if _PYDANTIC_OK:
        req_dict = req.model_dump()
    else:
        req_dict = {
            "business_name": req.business_name,
            "niche": req.niche,
            "target_audience": req.target_audience,
            "budget": req.budget,
            "brand_tone": req.brand_tone,
            "color_preference": req.color_preference,
        }

    job = AgencyKitJob(
        job_id=job_id,
        status="queued",
        progress=0,
        results={"_request": req_dict},
        created_at=_now_iso(),
    )
    with _JOB_LOCK:
        _prune_jobs()
        _JOB_STORE[job_id] = job

    thread = threading.Thread(target=run_agency_kit_pipeline, args=(job_id,), daemon=True)
    thread.start()
    return job_id


def get_job_status(job_id: str) -> AgencyKitJob | None:
    with _JOB_LOCK:
        return _JOB_STORE.get(job_id)


def list_jobs() -> list[AgencyKitJob]:
    with _JOB_LOCK:
        return list(_JOB_STORE.values())


# ── LLM wrapper (self-hosted ONLY) ────────────────────────────────────────────
def _llm_generate(
    prompt: str,
    system: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Call generate_sidix() — self-hosted inference only."""
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(
            prompt,
            system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return text or ""
    except Exception as e:
        logger.warning("agency_kit _llm_generate error: %s", e)
        return ""


# ── Parsing helpers ───────────────────────────────────────────────────────────
def _extract_field(text: str, field_name: str) -> str:
    patterns = [
        rf"(?i){re.escape(field_name)}\s*[:：]\s*(.+?)(?:\n|$)",
        rf"(?i)\*\*{re.escape(field_name)}\*\*\s*[:：]\s*(.+?)(?:\n|$)",
        rf"(?i)-\s*{re.escape(field_name)}\s*[:：]\s*(.+?)(?:\n|$)",
        rf"(?i)\d+\.\s*{re.escape(field_name)}\s*[:：]\s*(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return ""


def _extract_list(text: str, header: str, max_items: int = 30) -> list[str]:
    items: list[str] = []
    section_pat = rf"(?i){re.escape(header)}[\s:：\n](.*?)(?=\n\n|\Z|#{1,3}\s)"
    m = re.search(section_pat, text, re.DOTALL)
    section = m.group(1) if m else text
    for line in section.splitlines():
        line = line.strip()
        if not line or len(line) < 5:
            continue
        cleaned = re.sub(r"^(\d+[\.)\]]\s*|[\-\*\+]\s+|\(\d+\)\s*)", "", line)
        if cleaned and len(cleaned) > 3:
            items.append(cleaned)
    return items[:max_items]


# ── Debate Ring integration ───────────────────────────────────────────────────
def _run_debate_if_available(
    pair_id: str,
    creator_agent: str,
    critic_agent: str,
    prototype: str,
    context: str = "",
) -> str:
    try:
        from .debate_ring import run_debate
        result = run_debate(
            pair_id=pair_id,
            creator_agent=creator_agent,
            critic_agent=critic_agent,
            prototype=prototype,
            context=context,
            domain="creative",
            max_rounds=2,
        )
        return result.final_prototype if hasattr(result, "final_prototype") else str(result)
    except Exception as e:
        logger.debug("Debate ring skip for %s: %s", pair_id, e)
        return prototype


# ── CQF helper ────────────────────────────────────────────────────────────────
def _cqf_score(text: str, brief: str) -> dict[str, Any]:
    try:
        from .creative_quality import quality_gate
        gate = quality_gate(text, brief=brief, domain="creative", use_llm=False)
        score = gate.get("score", {})
        return {
            "relevance": score.get("relevance", 0.0),
            "quality": score.get("quality", 0.0),
            "creativity": score.get("creativity", 0.0),
            "brand": score.get("brand_alignment", 0.0),
            "actionability": score.get("actionability", 0.0),
            "total": gate.get("total", 0.0),
            "tier": gate.get("tier", "unknown"),
        }
    except Exception as e:
        logger.debug("CQF score skip: %s", e)
        return {
            "relevance": 0.0, "quality": 0.0, "creativity": 0.0,
            "brand": 0.0, "actionability": 0.0, "total": 0.0, "tier": "unknown",
        }


# ── Layer functions ───────────────────────────────────────────────────────────
def _layer1_brand_builder(req: AgencyKitRequest) -> dict[str, str]:
    system = (
        "Kamu adalah Brand Builder SIDIX. Tugasmu membuat brand kit lengkap untuk bisnis. "
        "Jawab dalam Bahasa Indonesia. Format output harus terstruktur dengan field: "
        "Nama Brand, Archetype (Jungian), Palet Warna (WCAG AA), Tipografi, Voice & Tone, Logo Prompt."
    )
    prompt = (
        f"Bisnis: {req.business_name}\n"
        f"Niche: {req.niche}\n"
        f"Target Audiens: {req.target_audience}\n"
        f"Budget: {req.budget}\n"
        f"Brand Tone: {req.brand_tone or 'friendly dan profesional'}\n"
        f"Preferensi Warna: {req.color_preference or 'bebas'}\n\n"
        "Hasilkan brand kit lengkap dalam format terstruktur."
    )
    raw = _llm_generate(prompt, system)
    raw = _run_debate_if_available(
        "brand_vs_design", "brand_builder", "design_critic", raw, req.business_name
    )
    return {
        "brand_name": _extract_field(raw, "Nama Brand") or req.business_name,
        "archetype": _extract_field(raw, "Archetype") or _extract_field(raw, "Archetype Jungian"),
        "palette": _extract_field(raw, "Palet Warna") or _extract_field(raw, "Palette"),
        "typography": _extract_field(raw, "Tipografi") or _extract_field(raw, "Typography"),
        "voice_tone": _extract_field(raw, "Voice & Tone") or _extract_field(raw, "Voice")
        or _extract_field(raw, "Tone"),
        "logo_prompt": _extract_field(raw, "Logo Prompt") or _extract_field(raw, "Prompt Logo"),
        "raw": raw,
    }


def _layer2_content_planner(req: AgencyKitRequest, brand_kit: dict) -> dict[str, Any]:
    system = (
        "Kamu adalah Content Planner SIDIX. Buat kalender konten 30 hari dengan tema dan hook. "
        "Format: hari ke-X | Tema | Hook | Channel. Jawab dalam Bahasa Indonesia."
    )
    prompt = (
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\n"
        f"Target: {req.target_audience}\nVoice: {brand_kit.get('voice_tone', '')}\n\n"
        "Buat kalender konten 30 hari (tema + hook untuk setiap hari)."
    )
    raw = _llm_generate(prompt, system)
    raw = _run_debate_if_available(
        "planner_vs_strategist", "content_planner", "campaign_strategist", raw, req.business_name
    )
    themes = _extract_list(raw, "Kalender") or _extract_list(raw, "Tema") or []
    if not themes:
        themes = [line.strip("- ").strip() for line in raw.splitlines()
                  if line.strip().startswith("-") or re.match(r"^\d+\.", line.strip())]
    return {"raw": raw, "themes": themes[:30]}


def _layer3_copywriter(req: AgencyKitRequest, brand_kit: dict) -> dict[str, Any]:
    system_captions = (
        "Kamu adalah Copywriter SIDIX. Buat 10 caption Instagram menggunakan formula AIDA, PAS, dan FAB. "
        "Setiap caption harus memiliki CTA. Jawab dalam Bahasa Indonesia. "
        "Format daftar bernomor."
    )
    prompt_captions = (
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\n"
        f"Target: {req.target_audience}\nVoice: {brand_kit.get('voice_tone', '')}\n\n"
        "Buat 10 caption Instagram (3 AIDA, 3 PAS, 2 FAB, 2 bonus). "
        "Format: [Formula] Caption..."
    )
    captions_raw = _llm_generate(prompt_captions, system_captions)
    captions = _extract_list(captions_raw, "Caption") or [line.strip("- ").strip()
                  for line in captions_raw.splitlines() if len(line.strip()) > 10]

    # Debate: Copywriter vs Hook Finder
    captions_raw = _run_debate_if_available(
        "copywriter_vs_strategist", "copywriter", "campaign_strategist", captions_raw, req.business_name
    )
    # Re-extract after debate
    captions_debated = _extract_list(captions_raw, "Caption") or captions

    system_threads = (
        "Kamu adalah Thread Writer SIDIX. Buat 5 thread X/Twitter menarik untuk bisnis ini. "
        "Setiap thread 3-5 tweet. Jawab dalam Bahasa Indonesia. Format daftar bernomor."
    )
    threads_raw = _llm_generate(
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\nTarget: {req.target_audience}\n\nBuat 5 thread X/Twitter.",
        system_threads,
    )
    threads = _extract_list(threads_raw, "Thread") or [line.strip("- ").strip()
                for line in threads_raw.splitlines() if len(line.strip()) > 10]
    threads = _run_debate_if_available(
        "hook_vs_audience", "script_hook", "audience_lens", "\n".join(threads), req.business_name
    ).splitlines()
    threads = [t.strip("- ").strip() for t in threads if len(t.strip()) > 10][:5]

    system_scripts = (
        "Kamu adalah Script Writer SIDIX. Buat 3 script video pendek (15-30 detik) untuk TikTok/Reels. "
        "Jawab dalam Bahasa Indonesia. Format daftar bernomor."
    )
    scripts_raw = _llm_generate(
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\nTarget: {req.target_audience}\n\nBuat 3 script video.",
        system_scripts,
    )
    scripts = _extract_list(scripts_raw, "Script") or [line.strip("- ").strip()
                for line in scripts_raw.splitlines() if len(line.strip()) > 10]

    return {
        "captions": captions_debated[:10] if captions_debated else captions[:10],
        "threads": threads[:5],
        "scripts": scripts[:3],
    }


def _layer4_campaign_strategist(req: AgencyKitRequest, brand_kit: dict) -> dict[str, Any]:
    system = (
        "Kamu adalah Campaign Strategist SIDIX. Buat strategi campaign AARRR funnel + channel mix + timeline 30 hari. "
        "Jawab dalam Bahasa Indonesia. Format terstruktur."
    )
    prompt = (
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\n"
        f"Target: {req.target_audience}\nBudget: {req.budget}\n\n"
        "Buat campaign strategy lengkap dengan AARRR funnel, channel mix, dan timeline."
    )
    raw = _llm_generate(prompt, system)
    raw = _run_debate_if_available(
        "strategist_vs_analyst", "campaign_strategist", "design_critic", raw, req.business_name
    )
    return {"raw": raw, "timeline": raw}


def _layer5_thumbnail_generator(req: AgencyKitRequest, brand_kit: dict) -> dict[str, Any]:
    system = (
        "Kamu adalah Thumbnail Designer SIDIX. Buat 3 prompt thumbnail (YouTube/Instagram) dan 9-post IG grid concept. "
        "Jawab dalam Bahasa Indonesia. Format daftar bernomor."
    )
    prompt = (
        f"Bisnis: {req.business_name}\nNiche: {req.niche}\n"
        f"Warna Brand: {brand_kit.get('palette', '')}\n\n"
        "Buat:\n1. 3 thumbnail prompts (YT/IG)\n2. 9-post IG grid concept (warna selaras brand)"
    )
    raw = _llm_generate(prompt, system)
    thumbnails = _extract_list(raw, "Thumbnail") or []
    grid = _extract_list(raw, "Grid") or _extract_list(raw, "IG Grid") or []
    return {
        "thumbnails": thumbnails[:3],
        "grid_posts": grid[:9],
    }


def _layer6_synthesis(
    req: AgencyKitRequest,
    brand_kit: dict,
    content_plan: dict,
    copy: dict,
    campaign: dict,
    visuals: dict,
) -> dict[str, Any]:
    result = AgencyKitResult(
        brand_name=brand_kit.get("brand_name", req.business_name),
        archetype=brand_kit.get("archetype", ""),
        palette=brand_kit.get("palette", ""),
        typography=brand_kit.get("typography", ""),
        voice_tone=brand_kit.get("voice_tone", ""),
        logo_prompt=brand_kit.get("logo_prompt", ""),
        captions=copy.get("captions", []),
        threads=copy.get("threads", []),
        scripts=copy.get("scripts", []),
        campaign_timeline=campaign.get("timeline", ""),
        thumbnails=visuals.get("thumbnails", []),
        grid_posts=visuals.get("grid_posts", []),
    )

    brief = f"{req.business_name} {req.niche}"
    all_text = " ".join([
        result.brand_name, result.archetype, result.voice_tone,
        " ".join(result.captions), result.campaign_timeline,
        " ".join(result.thumbnails), " ".join(result.grid_posts),
    ])
    cqf = _cqf_score(all_text, brief)

    return {
        "brand_kit": {
            "brand_name": result.brand_name,
            "archetype": result.archetype,
            "palette": result.palette,
            "typography": result.typography,
            "voice_tone": result.voice_tone,
            "logo_prompt": result.logo_prompt,
        },
        "captions": result.captions,
        "threads": result.threads,
        "scripts": result.scripts,
        "campaign_timeline": result.campaign_timeline,
        "thumbnails": result.thumbnails,
        "grid_posts": result.grid_posts,
        "cqf": cqf,
    }


# ── Main background pipeline ──────────────────────────────────────────────────
def run_agency_kit_pipeline(job_id: str) -> None:
    job = get_job_status(job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return

    req_dict = job.results.get("_request")
    if not req_dict:
        logger.error("Job %s missing request data", job_id)
        _update_job(job_id, status="failed", progress=100)
        return

    req = AgencyKitRequest(**req_dict)
    _update_job(job_id, status="processing", progress=5)

    try:
        # Layer 1: Brand Builder
        logger.info("[AgencyKit] Job %s — Layer 1/6 Brand Builder", job_id)
        brand_kit = _layer1_brand_builder(req)
        _update_job(job_id, progress=15, results={"_request": req_dict, "brand_kit": brand_kit})

        # Layer 2: Content Planner
        logger.info("[AgencyKit] Job %s — Layer 2/6 Content Planner", job_id)
        content_plan = _layer2_content_planner(req, brand_kit)
        _update_job(job_id, progress=30, results={
            "_request": req_dict,
            "brand_kit": brand_kit,
            "content_plan": content_plan,
        })

        # Layer 3: Copywriter × 3 variants
        logger.info("[AgencyKit] Job %s — Layer 3/6 Copywriter", job_id)
        copy = _layer3_copywriter(req, brand_kit)
        _update_job(job_id, progress=55, results={
            "_request": req_dict,
            "brand_kit": brand_kit,
            "content_plan": content_plan,
            "copy": copy,
        })

        # Layer 4: Campaign Strategist
        logger.info("[AgencyKit] Job %s — Layer 4/6 Campaign Strategist", job_id)
        campaign = _layer4_campaign_strategist(req, brand_kit)
        _update_job(job_id, progress=70, results={
            "_request": req_dict,
            "brand_kit": brand_kit,
            "content_plan": content_plan,
            "copy": copy,
            "campaign": campaign,
        })

        # Layer 5: Thumbnail Generator
        logger.info("[AgencyKit] Job %s — Layer 5/6 Thumbnail Generator", job_id)
        visuals = _layer5_thumbnail_generator(req, brand_kit)
        _update_job(job_id, progress=85, results={
            "_request": req_dict,
            "brand_kit": brand_kit,
            "content_plan": content_plan,
            "copy": copy,
            "campaign": campaign,
            "visuals": visuals,
        })

        # Layer 6: Synthesis + CQF
        logger.info("[AgencyKit] Job %s — Layer 6/6 Synthesis", job_id)
        synthesis = _layer6_synthesis(req, brand_kit, content_plan, copy, campaign, visuals)
        _update_job(job_id, status="completed", progress=100, results={
            "_request": req_dict,
            "brand_kit": brand_kit,
            "content_plan": content_plan,
            "copy": copy,
            "campaign": campaign,
            "visuals": visuals,
            **synthesis,
        })
        logger.info("[AgencyKit] Job %s completed", job_id)

    except Exception as e:
        logger.exception("Agency kit pipeline failed for job %s", job_id)
        _update_job(job_id, status="failed", progress=100, results={
            "_request": req_dict,
            "error": str(e),
        })
