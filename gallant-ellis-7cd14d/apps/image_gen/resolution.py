"""
Resolution Enforcement — Projek Badar Task 83 (G2)
Resolusi max & aspect ratio enforced untuk semua job gambar.
"""
from __future__ import annotations

import logging

from .models import ImageGenRequest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanta batas resolusi
# ---------------------------------------------------------------------------

MAX_WIDTH: int = 1024
MAX_HEIGHT: int = 1024
MAX_PIXELS: int = 786432  # 1024 * 768

ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "1:1": (512, 512),
    "16:9": (896, 512),
    "9:16": (512, 896),
    "4:3": (640, 480),
    "3:4": (480, 640),
    "3:2": (768, 512),
}

_DEFAULT_RESOLUTION: tuple[int, int] = (512, 512)


def clamp_resolution(width: int, height: int) -> tuple[int, int]:
    """
    Clamp width & height ke batas maksimum yang diizinkan.

    Bila total pixel melebihi MAX_PIXELS, scale down secara proporsional.
    """
    w = min(width, MAX_WIDTH)
    h = min(height, MAX_HEIGHT)

    if w * h > MAX_PIXELS:
        # Scale down proporsional
        ratio = (MAX_PIXELS / (w * h)) ** 0.5
        w = int(w * ratio)
        h = int(h * ratio)
        # Pastikan kelipatan 8 (diperlukan oleh sebagian besar model diffusion)
        w = (w // 8) * 8
        h = (h // 8) * 8
        logger.info(
            "Resolusi di-clamp ke %dx%d (dari %dx%d) karena melebihi MAX_PIXELS=%d",
            w, h, width, height, MAX_PIXELS,
        )

    return max(w, 8), max(h, 8)


def resolve_aspect_ratio(ratio: str) -> tuple[int, int]:
    """
    Kembalikan resolusi (width, height) untuk aspect ratio yang diminta.
    Default ke (512, 512) bila ratio tidak dikenal.
    """
    result = ASPECT_RATIOS.get(ratio)
    if result is None:
        logger.warning(
            "Aspect ratio '%s' tidak dikenal. Menggunakan default 512x512.", ratio
        )
        return _DEFAULT_RESOLUTION
    return result


def validate_resolution(width: int, height: int) -> tuple[bool, str]:
    """
    Periksa apakah resolusi berada dalam batas yang diizinkan.

    Returns:
        (True, "") bila valid.
        (False, pesan_error) bila tidak valid.
    """
    if width <= 0 or height <= 0:
        return False, f"Resolusi tidak valid: {width}x{height} (harus > 0)"
    if width > MAX_WIDTH:
        return False, f"Width {width} melebihi maksimum {MAX_WIDTH}"
    if height > MAX_HEIGHT:
        return False, f"Height {height} melebihi maksimum {MAX_HEIGHT}"
    if width * height > MAX_PIXELS:
        return (
            False,
            f"Total pixel {width * height} melebihi maksimum {MAX_PIXELS} "
            f"({width}x{height})",
        )
    return True, ""


def enforce_resolution(request: ImageGenRequest) -> ImageGenRequest:
    """
    Terapkan batas resolusi ke ImageGenRequest.

    - Bila aspect_ratio diatur (bukan default), gunakan resolusi dari ASPECT_RATIOS.
    - Clamp ke MAX_WIDTH/MAX_HEIGHT/MAX_PIXELS.

    Returns:
        ImageGenRequest baru dengan resolusi yang sudah divalidasi.
    """
    # Bila aspect_ratio bukan default, override width/height
    if request.aspect_ratio in ASPECT_RATIOS:
        w, h = resolve_aspect_ratio(request.aspect_ratio)
    else:
        w, h = request.width, request.height

    w, h = clamp_resolution(w, h)

    return request.model_copy(update={"width": w, "height": h})
