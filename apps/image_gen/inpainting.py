"""
Inpainting — Projek Badar Task 90 (G2)
Inpainting mask — fase 2 roadmap.
Status: STUB — belum diimplementasikan. Target: Q2 2026.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class InpaintRequest:
    """Request payload untuk inpainting."""

    image_path: str
    mask_path: str      # Mask hitam-putih: putih = area yang akan diisi
    prompt: str
    seed: Optional[int] = None


def inpaint(request: InpaintRequest) -> dict:
    """
    Jalankan inpainting pada area yang ditandai oleh mask.

    STUB — belum diimplementasikan. Target roadmap: Q2 2026.

    TODO (Q2 2026): implementasikan dengan pipeline lokal:
        from diffusers import StableDiffusionInpaintPipeline
        pipe = StableDiffusionInpaintPipeline.from_pretrained("model_path")
        image = Image.open(request.image_path).convert("RGB")
        mask = Image.open(request.mask_path).convert("RGB")
        result = pipe(
            prompt=request.prompt,
            image=image,
            mask_image=mask,
            generator=torch.Generator().manual_seed(request.seed or 0),
        )
        result.images[0].save(output_path)

    Returns:
        dict berisi status roadmap dan pesan error.
    """
    logger.info(
        "inpaint() dipanggil (stub). image=%s, mask=%s, prompt='%s...'",
        request.image_path,
        request.mask_path,
        request.prompt[:40],
    )
    return {
        "status": "roadmap",
        "target": "Q2 2026",
        "error": "Inpainting not implemented yet",
    }
