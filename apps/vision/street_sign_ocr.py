# -*- coding: utf-8 -*-
"""
Street Sign OCR — Projek Badar Task 113 (G3)
Surah Al-Ma'un (#107) — Batasi fitur agar tidak 'merembet' tanpa spesifikasi.

Baca teks dari papan nama jalan / rambu jalanan.
Fokus: street sign, plat nama jalan, papan informasi publik.
BUKAN untuk plat nomor kendaraan (use-case terpisah, privasi berbeda).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SCOPE DEFINITION (batasi agar tidak merembet)
# ---------------------------------------------------------------------------
SCOPE_NOTE = (
    "Street Sign OCR fokus pada: nama jalan, rambu informasi, papan tempat. "
    "TIDAK mencakup: plat nomor kendaraan (privasi), wajah, KTP/dokumen pribadi."
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class SignText:
    """Teks yang terdeteksi dari satu papan/rambu."""
    text: str
    confidence: float
    sign_type: str = "unknown"  # "street_name", "direction", "info", "warning", "unknown"
    language: str = "id"
    bbox: dict = field(default_factory=dict)


@dataclass
class StreetSignResult:
    """Hasil OCR papan nama jalan."""
    image_path: str
    signs: list[SignText] = field(default_factory=list)
    combined_text: str = ""
    primary_street_name: str = ""
    model: str = "stub"
    error: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STREET_PATTERNS = [
    re.compile(r"\b(jl|jln|jalan)\.?\s+\w+", re.IGNORECASE),
    re.compile(r"\b(gang|gg)\.?\s+\w+", re.IGNORECASE),
    re.compile(r"\b(perumahan|komplek|blok)\s+\w+", re.IGNORECASE),
]


def _classify_sign(text: str) -> str:
    """Klasifikasi jenis papan berdasarkan konten teks."""
    lower = text.lower()
    if any(kw in lower for kw in ("jl.", "jalan", "gang", "gg.")):
        return "street_name"
    if any(kw in lower for kw in ("km", "m →", "↑", "←", "→")):
        return "direction"
    if any(kw in lower for kw in ("dilarang", "stop", "hati-hati", "bahaya")):
        return "warning"
    return "info"


def _extract_street_name(text: str) -> str:
    """Ekstrak nama jalan dari teks mentah."""
    for pattern in _STREET_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return ""


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def read_street_sign(image_path: str) -> StreetSignResult:
    """
    Baca teks dari papan nama jalan / rambu jalanan.

    Pipeline:
    1. OCR teks dari gambar (pytesseract atau model VLM)
    2. Klasifikasi jenis papan
    3. Ekstrak nama jalan utama

    Args:
        image_path: Path ke gambar papan/rambu.

    Returns:
        StreetSignResult dengan teks yang terdeteksi.
    """
    import os
    logger.info(f"[SCOPE] {SCOPE_NOTE}")

    if not os.path.exists(image_path):
        return StreetSignResult(
            image_path=image_path,
            error=f"File tidak ditemukan: {image_path}",
        )

    raw_text = ""

    # Coba pytesseract
    try:
        import pytesseract  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]
        img = Image.open(image_path)
        # Config khusus papan jalan: PSM 6 = Uniform block of text
        raw_text = pytesseract.image_to_string(img, lang="ind+eng", config="--psm 6").strip()
        if raw_text:
            sign_type = _classify_sign(raw_text)
            primary = _extract_street_name(raw_text)
            return StreetSignResult(
                image_path=image_path,
                signs=[SignText(
                    text=raw_text,
                    confidence=0.7,
                    sign_type=sign_type,
                    language="id",
                )],
                combined_text=raw_text,
                primary_street_name=primary,
                model="pytesseract-ind+eng",
            )
    except ImportError:
        logger.warning("pytesseract tidak terinstall. pip install pytesseract (+ Tesseract-OCR)")
    except Exception as exc:
        logger.warning(f"pytesseract error: {exc}")

    # Fallback: caption model
    try:
        from .caption import extract_text_ocr
        ocr = extract_text_ocr(image_path)
        if ocr.text and "[STUB]" not in ocr.text:
            sign_type = _classify_sign(ocr.text)
            primary = _extract_street_name(ocr.text)
            return StreetSignResult(
                image_path=image_path,
                signs=[SignText(
                    text=ocr.text, confidence=ocr.confidence,
                    sign_type=sign_type,
                )],
                combined_text=ocr.text,
                primary_street_name=primary,
                model="caption-ocr",
            )
    except Exception:
        pass

    logger.warning(
        "[STUB] street_sign_ocr.read_street_sign() — tidak ada OCR engine tersedia. "
        "Install pytesseract (+ Tesseract-OCR with ind language pack) untuk pembacaan nyata."
    )
    return StreetSignResult(
        image_path=image_path,
        signs=[],
        combined_text="",
        primary_street_name="",
        model="stub",
        error="Tidak ada OCR engine tersedia. Install pytesseract.",
    )
