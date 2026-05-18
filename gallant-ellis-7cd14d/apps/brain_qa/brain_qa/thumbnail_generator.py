"""
thumbnail_generator.py — Sprint 4 P0 thumbnail planning generator.
"""

from __future__ import annotations

from .creative_framework import enhance_prompt_creative
from .creative_quality import quality_gate


def generate_thumbnail(
    *,
    title: str,
    style: str = "bold",
    platform: str = "youtube",
    brand_hint: str = "",
) -> dict:
    clean_title = (title or "").strip()
    if not clean_title:
        return {"ok": False, "error": "title wajib diisi"}

    prompt_seed = f"thumbnail {platform}: {clean_title}, style {style}, {brand_hint}".strip()
    enhanced = enhance_prompt_creative(prompt_seed, template="yt_thumbnail")
    overlay_text = clean_title[:64].upper()
    visual_notes = [
        "Gunakan kontras tinggi antara subjek vs background",
        "Taruh fokus utama di area tengah-kiri (aman untuk crop)",
        "Sisakan ruang teks overlay max 4 kata",
        "Warna dominan ikuti archetype brand",
    ]

    quality_brief = f"thumbnail {platform} {clean_title} {style}"
    gate = quality_gate(
        output=f"{overlay_text} | {enhanced['enhanced_prompt']}",
        brief=quality_brief,
        domain="design",
        use_llm=False,
    )

    return {
        "ok": True,
        "platform": platform,
        "title": clean_title,
        "style": style,
        "overlay_text": overlay_text,
        "enhanced_prompt": enhanced["enhanced_prompt"],
        "negative_prompt": enhanced["negative_prompt"],
        "width": enhanced["width"],
        "height": enhanced["height"],
        "template_used": enhanced["template_used"],
        "applied_archetype": enhanced["applied_archetype"],
        "detected_contexts": enhanced["detected_contexts"],
        "visual_notes": visual_notes,
        "cqf": gate,
        "next_action": "render_thumbnail" if gate["passed"] else "refine_thumbnail_prompt",
    }

