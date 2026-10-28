# -*- coding: utf-8 -*-
"""
Image Comparison (Before/After) — Projek Badar Task 108 (G3)
Surah Al-Infitar (#82) — Satu PR kecil yang merapikan dan mengurangi risiko.

Bandingkan dua gambar (before vs after): pixel diff, histogram similarity,
structural similarity (SSIM jika tersedia).
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class ComparisonResult:
    """Hasil perbandingan dua gambar."""
    image_a: str
    image_b: str
    identical: bool                     # True jika hash identik
    pixel_diff_ratio: float             # 0.0 = sama persis, 1.0 = seluruh pixel berbeda
    ssim_score: float | None = None     # Structural Similarity Index (butuh scikit-image)
    histogram_similarity: float | None = None  # 0.0–1.0
    size_match: bool = True
    notes: list[str] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_images(image_a: str, image_b: str) -> ComparisonResult:
    """
    Bandingkan dua gambar secara menyeluruh.

    Metode (berurutan, dari yang paling ringan):
    1. Hash SHA-256 — cepat, exact match
    2. Pixel difference ratio — via PIL
    3. Histogram similarity — via PIL
    4. SSIM — via scikit-image (opsional)

    Args:
        image_a: Path gambar pertama (before).
        image_b: Path gambar kedua (after).

    Returns:
        ComparisonResult dengan berbagai metrik perbandingan.
    """
    for p in (image_a, image_b):
        if not os.path.exists(p):
            return ComparisonResult(
                image_a=image_a, image_b=image_b,
                identical=False, pixel_diff_ratio=1.0,
                error=f"File tidak ditemukan: {p}",
            )

    notes: list[str] = []

    # 1. Hash check (cepat)
    hash_a = _sha256_file(image_a)
    hash_b = _sha256_file(image_b)
    if hash_a == hash_b:
        return ComparisonResult(
            image_a=image_a, image_b=image_b,
            identical=True, pixel_diff_ratio=0.0,
            ssim_score=1.0, histogram_similarity=1.0,
            notes=["Hash identik: kedua gambar byte-for-byte sama."],
        )

    pixel_diff_ratio = 1.0
    histogram_similarity: float | None = None
    ssim_score: float | None = None
    size_match = True

    try:
        from PIL import Image, ImageChops  # type: ignore[import-not-found]
        import math

        img_a = Image.open(image_a).convert("RGB")
        img_b = Image.open(image_b).convert("RGB")

        if img_a.size != img_b.size:
            size_match = False
            notes.append(
                f"Ukuran berbeda: {img_a.size} vs {img_b.size}. "
                "Resize gambar B ke ukuran gambar A untuk perbandingan."
            )
            img_b = img_b.resize(img_a.size, Image.LANCZOS)

        # Pixel diff ratio
        diff = ImageChops.difference(img_a, img_b)
        total_pixels = img_a.size[0] * img_a.size[1]
        nonzero = sum(1 for px in diff.getdata() if any(c > 0 for c in px))
        pixel_diff_ratio = nonzero / total_pixels if total_pixels > 0 else 1.0

        # Histogram similarity (per channel, cosine-like)
        def _hist_sim(h1: list, h2: list) -> float:
            dot = sum(a * b for a, b in zip(h1, h2))
            mag1 = math.sqrt(sum(a * a for a in h1))
            mag2 = math.sqrt(sum(b * b for b in h2))
            if mag1 == 0 or mag2 == 0:
                return 0.0
            return dot / (mag1 * mag2)

        sims = []
        for ch in range(3):
            h1 = img_a.split()[ch].histogram()
            h2 = img_b.split()[ch].histogram()
            sims.append(_hist_sim(h1, h2))
        histogram_similarity = sum(sims) / len(sims)

    except ImportError:
        notes.append("PIL tidak terinstall: pixel diff dan histogram tidak dihitung. pip install Pillow")

    # SSIM via scikit-image (opsional)
    try:
        import numpy as np
        from skimage.metrics import structural_similarity  # type: ignore[import-not-found]
        from PIL import Image as PILImage

        a_arr = np.array(PILImage.open(image_a).convert("L"))
        b_arr = np.array(PILImage.open(image_b).convert("L"))
        if a_arr.shape != b_arr.shape:
            from PIL import Image as PI
            b_arr = np.array(PI.open(image_b).convert("L").resize(
                (a_arr.shape[1], a_arr.shape[0]), PI.LANCZOS
            ))
        ssim_score = float(structural_similarity(a_arr, b_arr, data_range=255))
    except ImportError:
        notes.append("scikit-image tidak terinstall: SSIM tidak dihitung. pip install scikit-image")

    return ComparisonResult(
        image_a=image_a,
        image_b=image_b,
        identical=False,
        pixel_diff_ratio=pixel_diff_ratio,
        ssim_score=ssim_score,
        histogram_similarity=histogram_similarity,
        size_match=size_match,
        notes=notes,
    )


def diff_summary(result: ComparisonResult) -> str:
    """Ringkasan perbandingan dalam satu kalimat."""
    if result.error:
        return f"ERROR: {result.error}"
    if result.identical:
        return "Identik: kedua gambar sama persis."
    pct = result.pixel_diff_ratio * 100
    ssim_str = f", SSIM={result.ssim_score:.3f}" if result.ssim_score is not None else ""
    hist_str = f", Hist={result.histogram_similarity:.3f}" if result.histogram_similarity is not None else ""
    return f"Berbeda: {pct:.1f}% pixel berubah{ssim_str}{hist_str}"
