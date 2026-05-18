"""
Line Art Mode — Projek Badar Task 93 (G2)
Mode line art untuk output gambar.
Status: STUB.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage, ImageFilter as _ImageFilter

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning(
        "Pillow tidak tersedia. Line art conversion tidak dapat dijalankan. "
        "Install dengan: pip install Pillow"
    )


@dataclass
class LineArtRequest:
    """Request payload untuk konversi line art."""

    image_path: str
    thickness: int = 2
    color: str = "#000000"      # Warna garis (hex)
    background: str = "#ffffff"  # Warna latar (hex)


def convert_to_line_art(request: LineArtRequest) -> dict:
    """
    Konversi gambar ke mode line art menggunakan edge detection.

    Implementasi dengan PIL ImageFilter.CONTOUR:
    1. Buka gambar, konversi ke grayscale.
    2. Terapkan ImageFilter.CONTOUR untuk deteksi tepi.
    3. Invert bila perlu (CONTOUR menghasilkan tepi putih di latar hitam).
    4. Simpan ke path yang sama (overwrite) atau path baru.

    TODO: untuk kontrol ketebalan garis, gunakan cv2.Canny + dilate
          (OpenCV) setelah PIL tersedia.

    Returns:
        dict berisi status dan output_path atau error.
    """
    if not _PIL_AVAILABLE:
        logger.error("PIL tidak tersedia. Tidak dapat menjalankan line art conversion.")
        return {
            "status": "stub",
            "error": "PIL required for line art conversion",
        }

    src = Path(request.image_path)
    if not src.exists():
        logger.error("Source file tidak ditemukan: %s", request.image_path)
        return {
            "status": "error",
            "error": f"File tidak ditemukan: {request.image_path}",
        }

    try:
        with _PILImage.open(str(src)) as img:
            # Konversi ke grayscale
            gray = img.convert("L")

            # Edge detection menggunakan CONTOUR filter
            edges = gray.filter(_ImageFilter.CONTOUR)

            # TODO: terapkan thickness via morphological dilation
            # TODO: terapkan warna garis dan background dari request

            # Simpan ke file output (suffix _lineart)
            out_path = src.with_stem(src.stem + "_lineart")
            edges.save(str(out_path))

        logger.info("Line art dibuat: %s -> %s", request.image_path, out_path)
        return {
            "status": "ok",
            "output_path": str(out_path),
            "note": "Thickness/color customization: TODO via OpenCV morphology",
        }

    except Exception as exc:
        logger.error("Gagal konversi line art: %s", exc)
        return {
            "status": "error",
            "error": str(exc),
        }
