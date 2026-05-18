# -*- coding: utf-8 -*-
"""
Icon/Logo Detection — Projek Badar Task 105 (G3)
Surah Al-Mulk (#67) — Tilik izin yang bisa disempitkan.

Deteksi icon dan logo pada gambar untuk keperluan branding check.
Status: STUB — wire ke model deteksi lokal (YOLO/CLIP/DINO).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class LogoMatch:
    """Hasil pencocokan logo/icon pada gambar."""
    label: str
    confidence: float
    bbox: dict  # {"x": int, "y": int, "width": int, "height": int}
    brand: str = ""
    is_known: bool = False


@dataclass
class IconDetectionResult:
    """Hasil deteksi icon/logo dari sebuah gambar."""
    image_path: str
    logos: list[LogoMatch] = field(default_factory=list)
    icon_count: int = 0
    model: str = "stub"
    branding_issues: list[str] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Known brand registry (stub — expand per kebutuhan)
# ---------------------------------------------------------------------------

KNOWN_BRANDS: dict[str, str] = {
    "sidix": "SIDIX Platform",
    "mighan": "Mighan Brain Pack",
    # Tambahkan brand lain di sini
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def detect_icons(image_path: str, min_confidence: float = 0.5) -> IconDetectionResult:
    """
    Deteksi icon dan logo pada gambar.

    Args:
        image_path: Path ke file gambar.
        min_confidence: Threshold confidence minimum (0.0–1.0).

    Returns:
        IconDetectionResult dengan daftar logo yang terdeteksi.

    TODO: Wire ke model deteksi icon/logo lokal:
        - CLIP zero-shot (OpenCLIP): encode template brand + compare ke crop
        - YOLO + custom logo dataset
        - DINO features + kNN over brand embeddings
    """
    logger.warning(
        "[STUB] icon_detect.detect_icons() — model tidak dimuat. "
        "Wire ke CLIP/YOLO lokal untuk deteksi nyata."
    )
    return IconDetectionResult(
        image_path=image_path,
        logos=[],
        icon_count=0,
        model="stub",
        error="Icon detection not implemented: no model loaded",
    )


def check_branding_compliance(
    result: IconDetectionResult,
    required_brands: list[str] | None = None,
    forbidden_brands: list[str] | None = None,
) -> dict:
    """
    Periksa kepatuhan branding berdasarkan hasil deteksi.

    Args:
        result: Hasil dari detect_icons().
        required_brands: Brand yang harus ada di gambar.
        forbidden_brands: Brand yang tidak boleh ada.

    Returns:
        dict dengan keys: compliant (bool), missing (list), forbidden_found (list), notes (list).
    """
    found_labels = {logo.label.lower() for logo in result.logos}
    missing = []
    forbidden_found = []
    notes = []

    if required_brands:
        for brand in required_brands:
            if brand.lower() not in found_labels:
                missing.append(brand)

    if forbidden_brands:
        for brand in forbidden_brands:
            if brand.lower() in found_labels:
                forbidden_found.append(brand)

    if result.model == "stub":
        notes.append("Stub mode: hasil tidak dapat diandalkan. Aktifkan model deteksi.")

    return {
        "compliant": len(missing) == 0 and len(forbidden_found) == 0,
        "missing": missing,
        "forbidden_found": forbidden_found,
        "notes": notes,
    }
