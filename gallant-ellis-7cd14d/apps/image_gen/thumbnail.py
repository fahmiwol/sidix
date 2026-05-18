"""
Thumbnail & Compression — Projek Badar Task 77 (G2)
Thumbnail dan kompresi hasil gambar untuk UI.
Menggunakan Pillow (opsional). Fallback: copy file jika Pillow tidak ada.

# pip install Pillow
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning(
        "Pillow tidak tersedia. Thumbnail akan menggunakan fallback copy. "
        "Install dengan: pip install Pillow"
    )


@dataclass
class ThumbnailConfig:
    """Konfigurasi thumbnail generation."""

    max_width: int = 256
    max_height: int = 256
    quality: int = 85
    format: str = "JPEG"


def generate_thumbnail(
    source_path: str,
    dest_path: str,
    config: Optional[ThumbnailConfig] = None,
) -> bool:
    """
    Buat thumbnail dari gambar sumber.

    Bila Pillow tersedia: resize dengan mempertahankan aspek rasio, simpan JPEG.
    Fallback: copy file asli ke dest_path.

    Returns:
        True bila berhasil, False bila gagal.
    """
    if config is None:
        config = ThumbnailConfig()

    src = Path(source_path)
    dst = Path(dest_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        logger.error("Source file tidak ditemukan: %s", source_path)
        return False

    if _PIL_AVAILABLE:
        try:
            with _PILImage.open(src) as img:
                img.thumbnail((config.max_width, config.max_height))
                # Konversi ke RGB bila perlu (untuk JPEG)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.save(str(dst), format=config.format, quality=config.quality)
            logger.info("Thumbnail dibuat: %s -> %s", source_path, dest_path)
            return True
        except Exception as exc:
            logger.error("Gagal membuat thumbnail dengan PIL: %s", exc)
            return False
    else:
        # Fallback: copy file
        try:
            shutil.copy2(str(src), str(dst))
            logger.info(
                "Thumbnail fallback (copy): %s -> %s", source_path, dest_path
            )
            return True
        except Exception as exc:
            logger.error("Gagal fallback copy thumbnail: %s", exc)
            return False


def compress_image(
    source_path: str,
    dest_path: str,
    quality: int = 85,
) -> dict:
    """
    Kompres gambar dan simpan ke dest_path.

    Returns:
        dict berisi original_size, compressed_size, dan ratio kompresi.
    """
    src = Path(source_path)
    dst = Path(dest_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        logger.error("Source file tidak ditemukan: %s", source_path)
        return {"error": f"File tidak ditemukan: {source_path}"}

    original_size = src.stat().st_size

    if _PIL_AVAILABLE:
        try:
            with _PILImage.open(src) as img:
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.save(str(dst), format="JPEG", quality=quality, optimize=True)
        except Exception as exc:
            logger.error("Gagal kompresi dengan PIL: %s", exc)
            shutil.copy2(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))

    compressed_size = dst.stat().st_size
    ratio = compressed_size / original_size if original_size > 0 else 1.0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "ratio": round(ratio, 4),
    }
