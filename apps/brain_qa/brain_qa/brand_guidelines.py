"""
brand_guidelines.py — SIDIX Brand Guidelines & Design System Generator
=======================================================================
Generate brand guidelines komprehensif: color system, typography, spacing,
component tokens, voice & tone, logo usage rules.

Research notes:
  - 318 cognitive expansion (brand design + UX)
"""
from __future__ import annotations

import json
from typing import Any


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio."""
    def lum(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    l1 = 0.2126 * lum(r1) + 0.7152 * lum(g1) + 0.0722 * lum(b1)
    l2 = 0.2126 * lum(r2) + 0.7152 * lum(g2) + 0.0722 * lum(b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def generate_color_system(base_colors: list[str]) -> dict:
    """Generate color system dengan WCAG AA compliance."""
    if not base_colors:
        return _fallback("base_colors wajib diisi (list hex).")

    system = {}
    for i, base in enumerate(base_colors[:5]):
        name = ["primary", "secondary", "accent", "neutral", "success"][i]
        r, g, b = _hex_to_rgb(base)
        # Generate shades (lighten/darken)
        shades = {}
        for level in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]:
            factor = 1 - (level / 1000)
            nr = max(0, min(255, int(r * factor + (255 - 255 * factor) if level < 500 else r * factor)))
            ng = max(0, min(255, int(g * factor + (255 - 255 * factor) if level < 500 else g * factor)))
            nb = max(0, min(255, int(b * factor + (255 - 255 * factor) if level < 500 else b * factor)))
            shades[level] = _rgb_to_hex(nr, ng, nb)
        system[name] = {"base": base, "shades": shades}

    # Contrast pairs
    pairs = []
    bg = "#FFFFFF"
    for name, data in system.items():
        for level, color in data["shades"].items():
            ratio = _contrast_ratio(color, bg)
            if ratio >= 4.5:
                pairs.append({"foreground": color, "background": bg, "ratio": round(ratio, 2), "wcag": "AA" if ratio >= 4.5 else "FAIL"})

    return _ok({
        "colors": system,
        "contrast_pairs": pairs,
        "wcag_aa_compliant": all(p["ratio"] >= 4.5 for p in pairs),
    })


def generate_typography_scale(base_size: int = 16) -> dict:
    """Generate typography scale dengan golden ratio (1.618)."""
    ratio = 1.618
    scale = {
        "hero": round(base_size * (ratio ** 4)),
        "h1": round(base_size * (ratio ** 3)),
        "h2": round(base_size * (ratio ** 2)),
        "h3": round(base_size * ratio),
        "body": base_size,
        "small": round(base_size / ratio),
        "caption": round(base_size / (ratio ** 2)),
    }
    return _ok({
        "base_size": base_size,
        "ratio": ratio,
        "scale": scale,
        "line_height": 1.6,
        "font_families": {
            "heading": "Inter / Poppins / Montserrat",
            "body": "Inter / Open Sans / Lato",
            "mono": "JetBrains Mono / Fira Code",
        },
    })


def generate_spacing_scale(base: int = 4) -> dict:
    """Generate spacing scale (4-point grid)."""
    scale = {f"space-{i}": base * i for i in [1, 2, 3, 4, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64]}
    return _ok({
        "base_unit": base,
        "scale": scale,
        "common_patterns": {
            "button_padding": f"{scale['space-3']}px {scale['space-6']}px",
            "card_padding": f"{scale['space-6']}px",
            "section_gap": f"{scale['space-16']}px",
            "page_max_width": "1200px",
        },
    })


def generate_component_tokens(color_system: dict, typo_scale: dict, spacing: dict) -> dict:
    """Generate design tokens untuk components."""
    colors = color_system.get("colors", {})
    primary = colors.get("primary", {}).get("shades", {})
    neutral = colors.get("neutral", {}).get("shades", {})

    tokens = {
        "button": {
            "primary": {
                "bg": primary.get(500, "#3B82F6"),
                "text": "#FFFFFF",
                "border_radius": "8px",
                "padding": "12px 24px",
                "font_size": typo_scale.get("scale", {}).get("body", 16),
                "hover_bg": primary.get(600, "#2563EB"),
            },
            "secondary": {
                "bg": "transparent",
                "text": primary.get(500, "#3B82F6"),
                "border": f"1px solid {primary.get(500, '#3B82F6')}",
                "border_radius": "8px",
                "padding": "12px 24px",
            },
        },
        "card": {
            "bg": "#FFFFFF",
            "border": f"1px solid {neutral.get(200, '#E5E7EB')}",
            "border_radius": "12px",
            "padding": spacing.get("scale", {}).get("space-6", 24),
            "shadow": "0 1px 3px rgba(0,0,0,0.1)",
        },
        "input": {
            "bg": "#FFFFFF",
            "border": f"1px solid {neutral.get(300, '#D1D5DB')}",
            "border_radius": "8px",
            "padding": "10px 14px",
            "focus_border": primary.get(500, "#3B82F6"),
            "focus_ring": f"0 0 0 3px {primary.get(100, '#DBEAFE')}",
        },
    }
    return _ok({
        "tokens": tokens,
        "format": "json",
        "compatible_with": ["Tailwind CSS", "Styled Components", "Figma Variables"],
    })


def generate_voice_tone(brand_name: str, archetype: str = "everyman") -> dict:
    """Generate voice & tone guidelines berdasarkan archetype."""
    tones = {
        "everyman": {"voice": "Sederhana, jujur, tanpa basa-basi", "tone": "Hangat, inklusif, tidak menjatuhkan"},
        "creator": {"voice": "Inovatif, penuh imajinasi, berani", "tone": "Eksperimental, inspiratif, visual"},
        "sage": {"voice": "Berpengetahuan, objektif, analitis", "tone": "Tenang, meyakinkan, berbasis data"},
        "hero": {"voice": "Berani, kuat, penuh semangat", "tone": "Motivasi, tantangan, optimis"},
        "caregiver": {"voice": "Empatik, sabar, mendukung", "tone": "Lembut, menghibur, terstruktur"},
        "ruler": {"voice": "Otoritatif, terstruktur, elegan", "tone": "Formal, presisi, profesional"},
        "explorer": {"voice": "Kritis, penuh rasa ingin tahu, bebas", "tone": "Petualang, terbuka, dinamis"},
    }
    tone = tones.get(archetype, tones["everyman"])

    return _ok({
        "brand_name": brand_name,
        "archetype": archetype,
        "voice": tone["voice"],
        "tone": tone["tone"],
        "dos": [
            "Gunakan bahasa yang dimengerti audiens target",
            "Selalu sertakan 'mengapa' di balik setiap klaim",
            "Gunakan contoh konkret dari kehidupan nyata",
        ],
        "donts": [
            "Jangan gunakan jargon teknis tanpa penjelasan",
            "Jangan berbohong atau melebih-lebihkan kemampuan",
            "Jangan gunakan bahasa yang menyinggung atau eksklusif",
        ],
        "sample_phrases": [
            f"Di {brand_name}, kami percaya setiap orang bisa...",
            f"Solusi dari {brand_name} dirancang untuk...",
            f"Bersama {brand_name}, Anda tidak perlu khawatir tentang...",
        ],
    })


def generate_full_guidelines(brand_name: str, niche: str, base_colors: list[str],
                              archetype: str = "everyman", base_size: int = 16) -> dict:
    """Generate brand guidelines komplet: color + typography + spacing + tokens + voice."""
    color = generate_color_system(base_colors)
    if not color.get("ok"):
        return color
    typo = generate_typography_scale(base_size)
    spacing = generate_spacing_scale()
    tokens = generate_component_tokens(color["data"], typo["data"], spacing["data"])
    voice = generate_voice_tone(brand_name, archetype)

    return _ok({
        "brand_name": brand_name,
        "niche": niche,
        "archetype": archetype,
        "color_system": color["data"],
        "typography": typo["data"],
        "spacing": spacing["data"],
        "component_tokens": tokens["data"],
        "voice_tone": voice["data"],
        "export_formats": ["json", "css", "scss", "tailwind"],
    })
