"""
Confidence Score — Projek Badar Task 101 (G3)
Skor kepercayaan deskripsi vs model vision.
Agregasi dan grading kepercayaan dari berbagai komponen pipeline vision.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Threshold untuk grading (nilai minimum untuk setiap grade)
GRADE_THRESHOLDS: dict[str, float] = {
    "A": 0.9,
    "B": 0.75,
    "C": 0.6,
    "D": 0.4,
    # F: di bawah 0.4
}

# Bobot tiap komponen dalam agregasi (total = 1.0)
_WEIGHTS = {
    "caption": 0.50,
    "ocr": 0.25,
    "classification": 0.25,
}

# Rekomendasi per grade
_RECOMMENDATIONS: dict[str, str] = {
    "A": "Hasil analisis sangat dapat diandalkan. Siap untuk digunakan.",
    "B": "Hasil analisis cukup baik. Verifikasi manual disarankan untuk kasus kritis.",
    "C": "Hasil analisis perlu ditinjau. Pertimbangkan preprocessing gambar atau model yang lebih baik.",
    "D": "Hasil analisis kurang andal. Disarankan periksa kualitas gambar dan model.",
    "F": "Hasil analisis tidak dapat diandalkan. Gambar mungkin tidak memadai atau model stub aktif.",
}


@dataclass
class ConfidenceReport:
    """Laporan agregat kepercayaan dari pipeline vision."""
    overall: float
    caption_confidence: float
    ocr_confidence: float
    classification_confidence: float
    grade: str        # A / B / C / D / F
    recommendation: str


def compute_grade(score: float) -> str:
    """
    Hitung grade (A-F) berdasarkan skor kepercayaan.

    Args:
        score: Skor kepercayaan (0.0–1.0).

    Returns:
        Grade sebagai string: 'A', 'B', 'C', 'D', atau 'F'.
    """
    score = max(0.0, min(1.0, score))  # Clamp ke [0, 1]
    for grade, threshold in GRADE_THRESHOLDS.items():
        if score >= threshold:
            return grade
    return "F"


def aggregate_confidence(
    caption_conf: float,
    ocr_conf: float,
    class_conf: float,
) -> ConfidenceReport:
    """
    Agregasi skor kepercayaan dari tiga komponen vision pipeline.

    Bobot:
    - Caption:        50%
    - OCR:            25%
    - Klasifikasi:    25%

    Args:
        caption_conf: Kepercayaan hasil caption (0.0–1.0).
        ocr_conf: Kepercayaan hasil OCR (0.0–1.0).
        class_conf: Kepercayaan hasil klasifikasi gambar (0.0–1.0).

    Returns:
        ConfidenceReport dengan skor keseluruhan dan grade.
    """
    # Clamp semua input ke [0, 1]
    cap = max(0.0, min(1.0, caption_conf))
    ocr = max(0.0, min(1.0, ocr_conf))
    cls = max(0.0, min(1.0, class_conf))

    overall = (
        cap * _WEIGHTS["caption"]
        + ocr * _WEIGHTS["ocr"]
        + cls * _WEIGHTS["classification"]
    )

    grade = compute_grade(overall)
    recommendation = _RECOMMENDATIONS[grade]

    logger.debug(
        "[Confidence] Caption=%.2f(×%.0f%%) + OCR=%.2f(×%.0f%%) + "
        "Class=%.2f(×%.0f%%) → Overall=%.2f (Grade %s).",
        cap, _WEIGHTS["caption"] * 100,
        ocr, _WEIGHTS["ocr"] * 100,
        cls, _WEIGHTS["classification"] * 100,
        overall, grade,
    )

    return ConfidenceReport(
        overall=round(overall, 4),
        caption_confidence=cap,
        ocr_confidence=ocr,
        classification_confidence=cls,
        grade=grade,
        recommendation=recommendation,
    )


def format_report(report: ConfidenceReport) -> str:
    """
    Format ConfidenceReport menjadi tampilan teks yang mudah dibaca.

    Args:
        report: ConfidenceReport dari aggregate_confidence().

    Returns:
        String laporan yang diformat.
    """
    bar_len = 20
    filled = int(report.overall * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    lines = [
        "┌─ LAPORAN KEPERCAYAAN VISION ─────────────────────┐",
        f"│  Skor Keseluruhan : {report.overall:.1%}  [{bar}]  Grade: {report.grade}",
        "│─────────────────────────────────────────────────────│",
        f"│  Caption           : {report.caption_confidence:.1%}  (bobot 50%)",
        f"│  OCR               : {report.ocr_confidence:.1%}  (bobot 25%)",
        f"│  Klasifikasi       : {report.classification_confidence:.1%}  (bobot 25%)",
        "│─────────────────────────────────────────────────────│",
        f"│  Rekomendasi: {report.recommendation}",
        "└─────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)
