"""
Style Transfer — Projek Badar Task 84 (G2, optional)
Style transfer ringan menggunakan OSS tools.
Status: STUB — opsional, aktifkan bila stack mendukung.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

AVAILABLE_STYLES: list[str] = ["none", "watercolor", "oil_paint", "sketch"]


@dataclass
class StyleTransferRequest:
    """Request payload untuk style transfer."""

    content_image_path: str
    style_name: str = "none"
    strength: float = 0.5  # 0.0 = tidak ada efek, 1.0 = efek penuh


def apply_style_transfer(request: StyleTransferRequest) -> dict:
    """
    Terapkan style transfer ke gambar konten.

    Bila style_name == "none": passthrough (kembalikan path asli).
    Selain itu: stub — kembalikan pesan error informatif.

    TODO: Implementasikan dengan OSS tools:
    - Watercolor / Oil Paint: gunakan PIL ImageFilter + blending
    - Neural style: gunakan pytorch-neural-style atau fast-neural-style lokal
    - Sketch: konversi ke grayscale + edge detection (OpenCV / PIL)

    Returns:
        dict berisi status dan output_path (atau error).
    """
    if request.style_name not in AVAILABLE_STYLES:
        logger.warning(
            "Style '%s' tidak ada di AVAILABLE_STYLES: %s",
            request.style_name,
            AVAILABLE_STYLES,
        )

    if request.style_name == "none":
        logger.info("Style transfer passthrough: %s", request.content_image_path)
        return {
            "status": "passthrough",
            "output_path": request.content_image_path,
        }

    # Semua style selain "none" adalah stub saat ini
    # TODO: wire style-specific OSS model / filter pipeline
    logger.warning(
        "apply_style_transfer() stub untuk style '%s'. OSS model belum dimuat.",
        request.style_name,
    )
    return {
        "status": "stub",
        "error": (
            f"Style '{request.style_name}' not implemented: OSS model not loaded"
        ),
    }
