# -*- coding: utf-8 -*-
"""
Slide Reader — Projek Badar Task 112 (G3)
Surah At-Takathur (#102) — Perbaiki pesan error yang membingungkan.

Konversi slide/peta visual → bullet points terstruktur.
Cocok untuk presentasi, slide deck, atau diagram mindmap.
Status: STUB — wire ke vision-language model lokal.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class BulletPoint:
    """Satu bullet point hasil ekstraksi dari slide."""
    level: int          # kedalaman (0 = top level, 1 = sub-bullet, dst.)
    text: str
    is_heading: bool = False


@dataclass
class SlideReaderResult:
    """Hasil pembacaan slide sebagai bullet points."""
    image_path: str
    slide_title: str
    bullet_points: list[BulletPoint] = field(default_factory=list)
    raw_ocr_text: str = ""
    model: str = "stub"
    confidence: float = 0.0
    error: str | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _parse_ocr_to_bullets(ocr_text: str) -> tuple[str, list[BulletPoint]]:
    """
    Parsing teks OCR kasar ke struktur bullet points.
    Heuristik sederhana: baris pertama = judul, sisanya = bullets.
    """
    if not ocr_text.strip():
        return "", []

    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
    if not lines:
        return "", []

    title = lines[0]
    bullets = []
    for line in lines[1:]:
        # Deteksi kedalaman dari indentasi karakter atau prefix
        level = 0
        if re.match(r"^[-•*]\s+", line):
            line = re.sub(r"^[-•*]\s+", "", line)
            level = 1
        elif re.match(r"^\s{2,}", line):
            level = 1
        elif re.match(r"^\d+\.\s+", line):
            line = re.sub(r"^\d+\.\s+", "", line)
            level = 0

        if line:
            bullets.append(BulletPoint(level=level, text=line))

    return title, bullets


def read_slide(image_path: str) -> SlideReaderResult:
    """
    Baca slide/peta visual → bullet points terstruktur.

    Pipeline:
    1. OCR teks dari slide (via caption.py yang sudah ada)
    2. Parsing teks ke struktur bullet points
    3. Opsional: wire ke VLM (Qwen-VL/LLaVA) dengan prompt
       "Convert this slide to structured bullet points"

    Args:
        image_path: Path ke gambar slide.

    Returns:
        SlideReaderResult dengan judul dan bullet points.
    """
    import os
    if not os.path.exists(image_path):
        return SlideReaderResult(
            image_path=image_path, slide_title="",
            error=f"File tidak ditemukan: {image_path}",
        )

    raw_ocr = ""
    try:
        from .caption import extract_text_ocr
        ocr_result = extract_text_ocr(image_path)
        raw_ocr = ocr_result.text
    except ImportError as exc:
        logger.error("[slide_reader] Gagal import caption module: %s", exc)
    except Exception as exc:
        logger.warning("[slide_reader] OCR gagal: %s", exc)

    if not raw_ocr.strip() or "[STUB]" in raw_ocr:
        logger.warning(
            "[STUB] slide_reader.read_slide() — OCR stub tidak menghasilkan teks nyata. "
            "Wire ke pytesseract atau model VLM untuk hasil nyata."
        )
        return SlideReaderResult(
            image_path=image_path,
            slide_title="[STUB] Judul tidak terdeteksi",
            bullet_points=[
                BulletPoint(level=0, text="[STUB] Bullet point 1"),
                BulletPoint(level=1, text="[STUB] Sub-point (model vision belum aktif)"),
            ],
            raw_ocr_text=raw_ocr,
            model="stub",
            confidence=0.0,
            error="Slide OCR stub: aktifkan pytesseract atau model VLM untuk hasil nyata.",
        )

    title, bullets = _parse_ocr_to_bullets(raw_ocr)
    return SlideReaderResult(
        image_path=image_path,
        slide_title=title,
        bullet_points=bullets,
        raw_ocr_text=raw_ocr,
        model="ocr-heuristic",
        confidence=0.4,
    )


def format_as_markdown(result: SlideReaderResult) -> str:
    """Format SlideReaderResult sebagai Markdown."""
    lines = []
    if result.slide_title:
        lines.append(f"## {result.slide_title}")
        lines.append("")
    for bp in result.bullet_points:
        indent = "  " * bp.level
        prefix = "###" if bp.is_heading else f"{indent}-"
        lines.append(f"{prefix} {bp.text}")
    if not result.bullet_points:
        lines.append("_Tidak ada bullet points terdeteksi._")
    return "\n".join(lines)


def format_as_plain(result: SlideReaderResult) -> str:
    """Format SlideReaderResult sebagai teks biasa."""
    lines = []
    if result.slide_title:
        lines.append(result.slide_title)
        lines.append("=" * len(result.slide_title))
    for bp in result.bullet_points:
        indent = "  " * bp.level
        lines.append(f"{indent}• {bp.text}")
    return "\n".join(lines)
