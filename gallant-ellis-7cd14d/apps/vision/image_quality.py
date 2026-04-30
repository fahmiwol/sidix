# -*- coding: utf-8 -*-
"""
Image Quality Score — Projek Badar Task 111 (G3)
Surah Al-Qadr (#97) — Rapatkan definisi 'selesai' vs 'belum'.

Hitung skor kualitas gambar: blur/sharpness, noise, exposure, contrast.
Digunakan untuk memutuskan apakah gambar layak diproses oleh pipeline vision.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QualityGrade(str, Enum):
    EXCELLENT = "excellent"   # ≥ 0.85
    GOOD = "good"             # ≥ 0.70
    ACCEPTABLE = "acceptable" # ≥ 0.50
    POOR = "poor"             # ≥ 0.30
    UNUSABLE = "unusable"     # < 0.30


@dataclass
class QualityReport:
    """Laporan kualitas gambar."""
    image_path: str
    sharpness_score: float        # 0.0 (blur) – 1.0 (sangat tajam)
    noise_score: float            # 0.0 (noisy) – 1.0 (bersih)
    exposure_score: float         # 0.0 (terlalu gelap/terang) – 1.0 (pas)
    contrast_score: float         # 0.0 (flat) – 1.0 (kontras bagus)
    overall_score: float          # rata-rata berbobot
    grade: QualityGrade
    is_processable: bool          # True jika grade >= ACCEPTABLE
    recommendations: list[str] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

GRADE_THRESHOLDS = {
    QualityGrade.EXCELLENT: 0.85,
    QualityGrade.GOOD: 0.70,
    QualityGrade.ACCEPTABLE: 0.50,
    QualityGrade.POOR: 0.30,
}

WEIGHTS = {
    "sharpness": 0.40,
    "noise": 0.20,
    "exposure": 0.25,
    "contrast": 0.15,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_grade(score: float) -> QualityGrade:
    # Sort descending by threshold so highest grade is checked first.
    # Defensive against accidental reordering of GRADE_THRESHOLDS.
    for grade, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
        if score >= threshold:
            return grade
    return QualityGrade.UNUSABLE


def _recommendations(report: QualityReport) -> list[str]:
    recs = []
    if report.sharpness_score < 0.4:
        recs.append("Gambar terlalu blur — gunakan foto yang lebih tajam atau terapkan sharpening.")
    if report.noise_score < 0.4:
        recs.append("Noise tinggi — terapkan denoising (bilateral filter atau NLMeans).")
    if report.exposure_score < 0.4:
        recs.append("Exposure buruk — terapkan histogram equalization atau CLAHE.")
    if report.contrast_score < 0.4:
        recs.append("Kontras rendah — tingkatkan contrast sebelum analisis.")
    if not recs:
        recs.append("Kualitas gambar baik, siap diproses.")
    return recs


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def score_image_quality(image_path: str) -> QualityReport:
    """
    Hitung skor kualitas gambar secara menyeluruh.

    Metode:
    - Sharpness: Variance of Laplacian (makin tinggi = makin tajam)
    - Noise: estimasi via high-pass filter residual
    - Exposure: distribusi histogram (terlalu gelap/terang = score rendah)
    - Contrast: RMS contrast (standar deviasi intensitas pixel)

    Semua metode menggunakan PIL + numpy (opsional).
    Fallback: skor 0.5 (neutral) jika library tidak tersedia.

    Args:
        image_path: Path ke file gambar.

    Returns:
        QualityReport dengan berbagai skor dan rekomendasi.
    """
    import os
    if not os.path.exists(image_path):
        return QualityReport(
            image_path=image_path,
            sharpness_score=0.0, noise_score=0.0,
            exposure_score=0.0, contrast_score=0.0,
            overall_score=0.0, grade=QualityGrade.UNUSABLE,
            is_processable=False,
            error=f"File tidak ditemukan: {image_path}",
        )

    sharpness = 0.5
    noise = 0.5
    exposure = 0.5
    contrast = 0.5

    try:
        from PIL import Image, ImageFilter  # type: ignore[import-not-found]
        import math

        img = Image.open(image_path).convert("L")  # grayscale
        pixels = list(img.getdata())
        total = len(pixels)

        # --- Sharpness: Variance of Laplacian ---
        laplacian = img.filter(ImageFilter.FIND_EDGES)
        lap_pixels = list(laplacian.getdata())
        mean_lap = sum(lap_pixels) / total
        var_lap = sum((p - mean_lap) ** 2 for p in lap_pixels) / total
        # Normalize: var_lap=0 → 0.0, var_lap=5000 → 1.0
        sharpness = min(1.0, var_lap / 5000.0)

        # --- Exposure: histogram distribution ---
        hist = img.histogram()  # 256 bins
        # Ideal: pixels spread across mid-range (not all dark or all bright)
        dark = sum(hist[:64]) / total
        bright = sum(hist[192:]) / total
        mid = sum(hist[64:192]) / total
        exposure = mid  # makin banyak pixel di tengah = exposure makin baik
        # Penalti untuk ekstrem
        if dark > 0.6:
            exposure *= 0.5
        if bright > 0.6:
            exposure *= 0.5

        # --- Contrast: RMS contrast ---
        mean_px = sum(pixels) / total
        rms = math.sqrt(sum((p - mean_px) ** 2 for p in pixels) / total)
        contrast = min(1.0, rms / 64.0)  # normalize: 64 → 1.0

        # --- Noise: residual setelah blur ---
        blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
        blur_px = list(blurred.getdata())
        residual = [abs(p - b) for p, b in zip(pixels, blur_px)]
        mean_res = sum(residual) / total
        noise = max(0.0, 1.0 - (mean_res / 20.0))  # residual rendah = noise rendah

    except ImportError:
        logger.warning(
            "PIL tidak terinstall: skor kualitas menggunakan nilai default 0.5. "
            "pip install Pillow"
        )

    # Overall score (berbobot)
    overall = (
        sharpness * WEIGHTS["sharpness"]
        + noise * WEIGHTS["noise"]
        + exposure * WEIGHTS["exposure"]
        + contrast * WEIGHTS["contrast"]
    )

    grade = _compute_grade(overall)
    is_processable = grade not in (QualityGrade.POOR, QualityGrade.UNUSABLE)

    report = QualityReport(
        image_path=image_path,
        sharpness_score=round(sharpness, 3),
        noise_score=round(noise, 3),
        exposure_score=round(exposure, 3),
        contrast_score=round(contrast, 3),
        overall_score=round(overall, 3),
        grade=grade,
        is_processable=is_processable,
    )
    report.recommendations = _recommendations(report)
    return report


def format_quality_report(report: QualityReport) -> str:
    """Format QualityReport sebagai teks human-readable."""
    if report.error:
        return f"ERROR: {report.error}"
    bar = lambda s: "█" * int(s * 20) + "░" * (20 - int(s * 20))
    lines = [
        f"Kualitas Gambar: {report.image_path}",
        f"Grade: {report.grade.value.upper()} (skor={report.overall_score:.3f})",
        f"Layak diproses: {'Ya' if report.is_processable else 'Tidak'}",
        "",
        f"  Ketajaman  [{bar(report.sharpness_score)}] {report.sharpness_score:.3f}",
        f"  Kebersihan [{bar(report.noise_score)}] {report.noise_score:.3f}",
        f"  Exposure   [{bar(report.exposure_score)}] {report.exposure_score:.3f}",
        f"  Kontras    [{bar(report.contrast_score)}] {report.contrast_score:.3f}",
        "",
        "Rekomendasi:",
    ]
    for rec in report.recommendations:
        lines.append(f"  - {rec}")
    return "\n".join(lines)
