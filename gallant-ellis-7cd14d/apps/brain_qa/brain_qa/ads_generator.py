"""
ads_generator.py — Sprint 4 P0 ads copy generator.
"""

from __future__ import annotations

from .creative_quality import rank_variants, quality_gate


def _platform_constraints(platform: str) -> dict[str, str]:
    p = (platform or "").lower()
    if p == "google":
        return {"headline_limit": "30 chars", "desc_limit": "90 chars", "style": "intent-driven"}
    if p == "tiktok":
        return {"headline_limit": "short hook", "desc_limit": "snappy", "style": "casual + fast"}
    return {"headline_limit": "40 chars", "desc_limit": "125 chars", "style": "benefit-led"}


def generate_ads(
    *,
    product: str,
    audience: str,
    platform: str = "facebook",
    objective: str = "conversion",
    n_variants: int = 3,
) -> dict:
    prod = (product or "").strip()
    aud = (audience or "").strip()
    if not prod:
        return {"ok": False, "error": "product wajib diisi"}
    if not aud:
        return {"ok": False, "error": "audience wajib diisi"}

    count = max(1, min(int(n_variants), 5))
    rules = _platform_constraints(platform)
    hooks = [
        f"{aud} butuh solusi {prod} yang cepat?",
        f"Stop buang waktu. {prod} bantu kerja lebih efektif.",
        f"{prod}: langkah praktis untuk hasil nyata.",
        f"Upgrade cara kerja {aud} mulai hari ini.",
        f"Dari bingung jadi terarah dengan {prod}.",
    ]
    ctas = [
        "Coba sekarang",
        "Lihat detailnya",
        "Mulai gratis",
        "Ambil templatenya",
        "Klik untuk mulai",
    ]

    variants: list[dict] = []
    for index in range(count):
        headline = hooks[index % len(hooks)]
        description = (
            f"Objective {objective}. "
            f"Fokus ke manfaat utama: hemat waktu, lebih terukur, lebih konsisten."
        )
        image_prompt = (
            f"Ad visual for {prod}, target {aud}, platform {platform}, "
            "clean composition, high contrast, clear focal point, marketing-ready"
        )
        variants.append(
            {
                "headline": headline,
                "description": description,
                "cta": ctas[index % len(ctas)],
                "image_prompt": image_prompt,
            }
        )

    scored = rank_variants(
        [f"{v['headline']} {v['description']}" for v in variants],
        brief=f"{prod} ads {platform} {aud} {objective}",
        domain="marketing",
        top_k=1,
    )
    best_idx, best_score = scored[0]
    best_variant = variants[best_idx]
    gate = quality_gate(
        f"{best_variant['headline']} {best_variant['description']}",
        brief=f"ads {prod} {platform}",
        domain="marketing",
        use_llm=False,
    )

    return {
        "ok": True,
        "product": prod,
        "audience": aud,
        "platform": platform,
        "objective": objective,
        "platform_constraints": rules,
        "best_variant": best_variant,
        "variants": variants,
        "cqf": gate,
        "ranking_preview": {
            "selected_variant_index": best_idx,
            "selected_variant_score": round(best_score.total, 2),
        },
        "next_action": "publish_ads" if gate["passed"] else "refine_ads_copy",
    }

