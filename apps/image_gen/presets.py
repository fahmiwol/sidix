"""
Visual Prompt Presets — Projek Badar Task 73 (G2)
Preset prompt visual: gaya, rasio aspek, negatif prompt.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import ImageGenRequest


@dataclass
class StylePreset:
    """Definisi sebuah preset gaya visual."""

    name: str
    positive_suffix: str
    negative_prompt: str
    aspect_ratio: str
    description: str


STYLE_PRESETS: dict[str, StylePreset] = {
    "photorealistic": StylePreset(
        name="photorealistic",
        positive_suffix="hyperrealistic, 8k, sharp focus",
        negative_prompt="cartoon, anime, blur, painting, illustration",
        aspect_ratio="3:2",
        description="Foto realistik tajam dengan detail tinggi.",
    ),
    "anime": StylePreset(
        name="anime",
        positive_suffix="anime style, vibrant colors, cel shading",
        negative_prompt="realistic, photograph, 3d render",
        aspect_ratio="1:1",
        description="Gaya anime dengan warna cerah.",
    ),
    "sketch": StylePreset(
        name="sketch",
        positive_suffix="pencil sketch, detailed lines, hatching",
        negative_prompt="color, photography, painting",
        aspect_ratio="1:1",
        description="Sketsa pensil hitam-putih dengan detail garis.",
    ),
    "minimalist": StylePreset(
        name="minimalist",
        positive_suffix="minimalist, clean lines, white background, simple",
        negative_prompt="busy, complex, cluttered, noisy, photorealistic",
        aspect_ratio="1:1",
        description="Desain minimalis bersih dengan latar putih.",
    ),
    "brand": StylePreset(
        name="brand",
        positive_suffix="professional, brand consistent, corporate, polished",
        negative_prompt="amateur, cartoon, sketch, distorted",
        aspect_ratio="16:9",
        description="Visual profesional konsisten untuk keperluan brand.",
    ),
}

_DEFAULT_PRESET_NAME = "minimalist"


def get_preset(name: str) -> StylePreset:
    """
    Kembalikan StylePreset berdasarkan nama.
    Fallback ke preset 'minimalist' bila nama tidak dikenal.
    """
    return STYLE_PRESETS.get(name, STYLE_PRESETS[_DEFAULT_PRESET_NAME])


def apply_preset(request: ImageGenRequest, preset_name: str) -> ImageGenRequest:
    """
    Gabungkan preset ke dalam ImageGenRequest.
    positive_suffix ditambahkan ke prompt; negative_prompt digabung;
    aspect_ratio diatur sesuai preset (kecuali user sudah set non-default).
    """
    preset = get_preset(preset_name)

    merged_prompt = f"{request.prompt}, {preset.positive_suffix}"

    if request.negative_prompt:
        merged_negative = f"{request.negative_prompt}, {preset.negative_prompt}"
    else:
        merged_negative = preset.negative_prompt

    # Hanya override aspect_ratio bila masih default
    aspect = request.aspect_ratio if request.aspect_ratio != "1:1" else preset.aspect_ratio

    return request.model_copy(
        update={
            "prompt": merged_prompt,
            "negative_prompt": merged_negative,
            "aspect_ratio": aspect,
            "style": preset_name,
        }
    )


def list_presets() -> list[dict]:
    """Kembalikan daftar semua preset beserta nama dan deskripsinya."""
    return [
        {"name": p.name, "description": p.description, "aspect_ratio": p.aspect_ratio}
        for p in STYLE_PRESETS.values()
    ]
