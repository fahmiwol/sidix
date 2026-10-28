"""
Img2Img — Projek Badar Task 81 (G2)
Img2img atau variasi gambar.
Status: STUB — aktifkan bila stack mendukung model diffusion lokal.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Img2ImgRequest:
    """Request payload untuk img2img generation."""

    source_image_path: str
    prompt: str
    strength: float = 0.75  # 0.0 = identik dengan source, 1.0 = bebas sepenuhnya
    seed: Optional[int] = None


@dataclass
class Img2ImgResult:
    """Hasil img2img generation."""

    job_id: str
    output_path: Optional[str]
    status: str
    error: Optional[str] = None


def img2img_generate(request: Img2ImgRequest) -> Img2ImgResult:
    """
    Jalankan img2img generation.

    STUB — TODO: load diffusion model, apply img2img pipeline:
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained("model_path")
        init_image = Image.open(request.source_image_path).convert("RGB")
        result = pipe(
            prompt=request.prompt,
            image=init_image,
            strength=request.strength,
            generator=torch.Generator().manual_seed(request.seed or 0),
        )
        output_path = f".data/image_gen/img2img_{job_id}.png"
        result.images[0].save(output_path)

    Returns:
        Img2ImgResult dengan status="stub" dan pesan error informatif.
    """
    job_id = str(uuid.uuid4())
    logger.warning(
        "img2img_generate() dipanggil tapi model diffusion belum dimuat. "
        "job_id=%s, prompt='%s...'",
        job_id,
        request.prompt[:40],
    )

    # TODO: load diffusion model, apply img2img pipeline
    return Img2ImgResult(
        job_id=job_id,
        output_path=None,
        status="stub",
        error="img2img not implemented: no model loaded",
    )
