"""
Low Light Detection — Projek Badar Task 104 (G3)
Deteksi gambar low-light → saran preprocessing untuk memperbaiki kualitas.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Threshold brightness (skala 0–255 grayscale)
BRIGHTNESS_THRESHOLDS: dict[str, int] = {
    "bright": 200,   # >= 200: terlalu terang
    "normal": 150,   # >= 150: normal
    "dim": 100,      # >= 100: redup
    "dark": 50,      # >= 50: gelap
    # < 50: very_dark
}

# Saran preprocessing per kategori brightness
_SUGGESTIONS: dict[str, list[str]] = {
    "very_dark": [
        "Apply histogram equalization",
        "Increase brightness by 30-50%",
        "Apply CLAHE algorithm",
        "Consider denoising before processing",
        "Gunakan Gamma Correction (γ > 1.0) untuk mencerahkan shadow",
    ],
    "dark": [
        "Apply histogram equalization",
        "Increase brightness by 30-50%",
        "Apply CLAHE algorithm",
        "Consider denoising before processing",
    ],
    "dim": [
        "Apply histogram equalization",
        "Increase brightness by 30-50%",
        "Apply CLAHE algorithm",
        "Consider denoising before processing",
    ],
    "normal": [
        "Image brightness is acceptable for processing",
    ],
    "bright": [
        "Consider reducing brightness to avoid overexposure artifacts",
        "Apply mild gamma correction (γ < 1.0) untuk mengurangi highlight",
    ],
}


@dataclass
class LightingAnalysis:
    """Hasil analisis pencahayaan gambar."""
    is_low_light: bool
    average_brightness: float
    brightness_grade: str   # bright | normal | dim | dark | very_dark
    suggestions: list[str] = field(default_factory=list)


def _classify_brightness(avg_brightness: float) -> str:
    """
    Klasifikasikan tingkat kecerahan berdasarkan nilai rata-rata.

    Args:
        avg_brightness: Nilai brightness rata-rata (0–255).

    Returns:
        Salah satu: 'bright', 'normal', 'dim', 'dark', 'very_dark'.
    """
    if avg_brightness >= BRIGHTNESS_THRESHOLDS["bright"]:
        return "bright"
    elif avg_brightness >= BRIGHTNESS_THRESHOLDS["normal"]:
        return "normal"
    elif avg_brightness >= BRIGHTNESS_THRESHOLDS["dim"]:
        return "dim"
    elif avg_brightness >= BRIGHTNESS_THRESHOLDS["dark"]:
        return "dark"
    else:
        return "very_dark"


def analyze_brightness(image_path: str) -> LightingAnalysis:
    """
    Analisis tingkat kecerahan gambar.

    Args:
        image_path: Path ke file gambar.

    Returns:
        LightingAnalysis berisi rata-rata brightness, grade, dan saran preprocessing.

    Notes:
        Memerlukan Pillow untuk analisis nyata.
        Fallback ke stub jika PIL tidak tersedia.
    """
    try:
        from PIL import Image, ImageStat

        with Image.open(image_path) as img:
            # Konversi ke grayscale untuk analisis brightness
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            avg_brightness = stat.mean[0]  # Rata-rata piksel grayscale (0–255)

        grade = _classify_brightness(avg_brightness)
        is_low_light = grade in ("dim", "dark", "very_dark")
        suggestions = suggest_preprocessing(
            LightingAnalysis(
                is_low_light=is_low_light,
                average_brightness=avg_brightness,
                brightness_grade=grade,
            )
        )

        logger.info(
            "[LowLight] '%s' → brightness=%.1f, grade='%s', low_light=%s.",
            image_path, avg_brightness, grade, is_low_light,
        )
        return LightingAnalysis(
            is_low_light=is_low_light,
            average_brightness=round(avg_brightness, 2),
            brightness_grade=grade,
            suggestions=suggestions,
        )

    except ImportError:
        logger.warning(
            "[STUB] PIL tidak tersedia untuk analisis brightness '%s'. "
            "Install Pillow: pip install Pillow",
            image_path,
        )
        return LightingAnalysis(
            is_low_light=False,
            average_brightness=128.0,
            brightness_grade="normal",
            suggestions=["PIL required for brightness analysis"],
        )
    except Exception as exc:
        logger.error("[LowLight] Gagal analisis brightness '%s': %s", image_path, exc)
        return LightingAnalysis(
            is_low_light=False,
            average_brightness=128.0,
            brightness_grade="normal",
            suggestions=[f"Analisis gagal: {exc}"],
        )


def suggest_preprocessing(analysis: LightingAnalysis) -> list[str]:
    """
    Berikan saran preprocessing berdasarkan hasil analisis brightness.

    Args:
        analysis: LightingAnalysis dari analyze_brightness().

    Returns:
        Daftar saran preprocessing sebagai list of string.
    """
    grade = analysis.brightness_grade
    suggestions = _SUGGESTIONS.get(grade, ["Tidak ada saran spesifik."])

    logger.debug(
        "[LowLight] suggest_preprocessing: grade='%s', %d saran.",
        grade, len(suggestions),
    )
    return suggestions
