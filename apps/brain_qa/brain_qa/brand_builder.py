"""
brand_builder.py — Sprint 4 P0 brand kit generator.
"""

from __future__ import annotations

from .creative_framework import ARCHETYPES
from .creative_quality import quality_gate


_PALETTE_PRESETS: dict[str, list[str]] = {
    "caregiver": ["#F2E8E4", "#DDA15E", "#6B705C", "#CB997E"],
    "ruler": ["#0B132B", "#1C2541", "#3A506B", "#FFD166"],
    "creator": ["#3A0CA3", "#7209B7", "#B5179E", "#F72585"],
    "jester": ["#FFB703", "#FB8500", "#8ECAE6", "#219EBC"],
    "everyman": ["#2D6A4F", "#40916C", "#95D5B2", "#D8F3DC"],
    "lover": ["#9D4EDD", "#C77DFF", "#FFAFCC", "#FF758F"],
    "hero": ["#D00000", "#F77F00", "#003049", "#EAE2B7"],
    "outlaw": ["#111111", "#2B2D42", "#8D99AE", "#EF233C"],
    "magician": ["#240046", "#5A189A", "#9D4EDD", "#E0AAFF"],
    "innocent": ["#F8F9FA", "#DEE2E6", "#A8DADC", "#457B9D"],
    "sage": ["#14213D", "#1D3557", "#457B9D", "#A8DADC"],
    "explorer": ["#264653", "#2A9D8F", "#E9C46A", "#F4A261"],
}


def _infer_archetype_from_niche(niche: str) -> str:
    n = (niche or "").lower()
    rules = [
        ("hero", ("fitness", "coach", "achievement", "sports")),
        ("caregiver", ("health", "parenting", "education", "care")),
        ("ruler", ("finance", "law", "consulting", "corporate")),
        ("creator", ("design", "art", "creative", "studio")),
        ("sage", ("research", "ai", "data", "science")),
        ("jester", ("entertainment", "fun", "meme", "comedy")),
        ("explorer", ("travel", "adventure", "outdoor", "nature")),
    ]
    for archetype, keywords in rules:
        if any(k in n for k in keywords):
            return archetype
    return "everyman"


def generate_brand_kit(
    *,
    business_name: str,
    niche: str,
    target_audience: str = "",
    vibe: str = "modern, warm, trustworthy",
    archetype: str | None = None,
) -> dict:
    name = (business_name or "").strip()
    domain = (niche or "").strip()
    audience = (target_audience or "").strip() or f"audiens {domain} Indonesia"
    if not name:
        return {"ok": False, "error": "business_name wajib diisi"}
    if not domain:
        return {"ok": False, "error": "niche wajib diisi"}

    selected_arch = (archetype or _infer_archetype_from_niche(domain)).lower()
    if selected_arch not in ARCHETYPES:
        selected_arch = "everyman"

    meta = ARCHETYPES[selected_arch]
    palette = _PALETTE_PRESETS.get(selected_arch, _PALETTE_PRESETS["everyman"])
    tone = meta["voice"]
    tagline = f"{name} membantu {domain} dengan gaya {vibe}."
    onlyness = f"Satu-satunya {domain} yang fokus pada hasil praktis untuk pasar Indonesia."
    golden_circle = {
        "why": f"Memberdayakan audiens {domain} agar lebih produktif dan percaya diri.",
        "how": "Framework praktis + konten konsisten + eksekusi bertahap.",
        "what": "Produk/layanan dengan nilai nyata dan mudah diadopsi.",
    }
    logo_prompts = [
        f"Minimalist logo for {name}, archetype {selected_arch}, clean vector mark, flat background",
        f"Premium emblem logo for {name}, {selected_arch} personality, strong contrast, modern typography",
        f"Monoline logo concept for {name}, {selected_arch} style, scalable icon, brand-ready",
    ]

    output = (
        f"{name} | niche {domain} | archetype {selected_arch} | tone {tone} | "
        f"palette {', '.join(palette)} | onlyness {onlyness}"
    )
    gate = quality_gate(output, brief=f"brand kit {name} {domain}", domain="marketing", use_llm=False)

    return {
        "ok": True,
        "business_name": name,
        "niche": domain,
        "target_audience": audience,
        "vibe": vibe,
        "archetype": selected_arch,
        "archetype_meta": meta,
        "palette": palette,
        "tone_of_voice": tone,
        "tagline": tagline,
        "onlyness_statement": onlyness,
        "golden_circle": golden_circle,
        "logo_prompts": logo_prompts,
        "cqf": gate,
        "next_action": "generate_logo_variants" if gate["passed"] else "refine_brand_kit",
    }

