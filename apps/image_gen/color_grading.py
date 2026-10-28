"""
Color Grading — Projek Badar Task 80 (G2)
Color grading / palet brand untuk output konsisten.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


@dataclass
class BrandPalette:
    """Definisi palet warna brand."""

    name: str
    primary_hex: str
    secondary_hex: str
    accent_hex: str
    background_hex: str


# Palet brand resmi SIDIX
SIDIX_PALETTE = BrandPalette(
    name="sidix-dark",
    primary_hex="#1a1a2e",
    secondary_hex="#16213e",
    accent_hex="#c9a96e",
    background_hex="#0f0e17",
)


class ColorGrader:
    """
    Aplikasi color grading berbasis palet brand.

    Saat ini berupa stub. Untuk implementasi:
    - Gunakan PIL ImageFilter atau matriks warna untuk color grading.
    - Gunakan scikit-image / OpenCV untuk histogram matching.
    """

    def apply_palette(
        self,
        image_path: str,
        palette: BrandPalette,
        output_path: str,
    ) -> bool:
        """
        Terapkan palet warna ke gambar output.

        STUB — TODO: implementasikan dengan PIL:
            1. Buka gambar.
            2. Terapkan color matrix atau histogram matching ke warna brand.
            3. Simpan ke output_path.

        Returns:
            False (belum diimplementasikan).
        """
        # TODO: wire PIL color matrix / LUT-based grading
        logger.info(
            "stub: apply_palette() belum diimplementasikan untuk palet '%s'. "
            "image: %s -> %s",
            palette.name,
            image_path,
            output_path,
        )
        return False

    def get_dominant_colors(self, image_path: str, n: int = 5) -> list[str]:
        """
        Ekstrak n warna dominan dari gambar.

        STUB — TODO: gunakan PIL quantize() atau sklearn KMeans clustering
        pada pixel array untuk mendapatkan warna dominan.

        Returns:
            list hex strings (stub: semua "#000000").
        """
        # TODO: wire PIL quantize / K-means clustering
        logger.info(
            "stub: get_dominant_colors() belum diimplementasikan. "
            "Mengembalikan %d placeholder '#000000'.",
            n,
        )
        return ["#000000"] * n
