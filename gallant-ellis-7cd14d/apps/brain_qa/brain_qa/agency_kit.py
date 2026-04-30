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

import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

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
