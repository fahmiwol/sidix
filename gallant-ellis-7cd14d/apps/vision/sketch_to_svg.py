# -*- coding: utf-8 -*-
"""
Sketch → Technical SVG — Projek Badar Task 109 (G3)
Surah Al-A'la (#87) — Matikan jalur eksperimen yang mengganggu stabilitas.

Bantu konversi sketsa tangan → SVG teknis (manual assist, bukan klaim sempurna).
BUKAN AI otomatis; ini pipeline berbantuan: edge detect → potrace → SVG output.
Disclaimer: Hasil perlu review manual. Kualitas tergantung kualitas sketsa asli.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "PERINGATAN: Sketch-to-SVG adalah manual assist pipeline, bukan konversi otomatis sempurna. "
    "Hasil SVG perlu review dan koreksi manual sebelum digunakan secara profesional."
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class SketchToSVGResult:
    """Hasil konversi sketsa ke SVG."""
    input_path: str
    svg_path: str | None
    method: str               # "potrace", "inkscape", atau "stub"
    success: bool
    notes: list[str]
    error: str | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _preprocess_sketch(image_path: str, output_path: str) -> bool:
    """
    Preprocessing sketsa: grayscale → threshold → biner.
    Hasilnya lebih bersih untuk input potrace.
    """
    try:
        from PIL import Image, ImageFilter, ImageOps  # type: ignore[import-not-found]
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.SHARPEN)
        # Adaptive threshold sederhana: otsu-like via PIL
        img = img.point(lambda x: 0 if x < 128 else 255, "1")
        img = img.convert("L")
        img.save(output_path)
        return True
    except ImportError:
        logger.warning("PIL tidak terinstall: preprocessing dilewati. pip install Pillow")
        return False


def sketch_to_svg(
    image_path: str,
    output_path: str | None = None,
    threshold: int = 128,
) -> SketchToSVGResult:
    """
    Konversi sketsa (PNG/JPG) → SVG via potrace atau Inkscape.

    Pipeline:
    1. Preprocessing: grayscale + threshold (via PIL)
    2. Konversi ke SVG via potrace (CLI) jika tersedia
    3. Fallback: Inkscape CLI jika tersedia
    4. Fallback: stub (kembalikan error dengan instruksi install)

    Args:
        image_path: Path ke file sketsa.
        output_path: Path output SVG. Default: <input>.svg
        threshold: Nilai threshold untuk binerisasi (0–255).

    Returns:
        SketchToSVGResult.
    """
    notes = [DISCLAIMER]

    if not os.path.exists(image_path):
        return SketchToSVGResult(
            input_path=image_path, svg_path=None,
            method="stub", success=False, notes=notes,
            error=f"File tidak ditemukan: {image_path}",
        )

    if output_path is None:
        output_path = str(Path(image_path).with_suffix(".svg"))

    # Preprocessing
    bw_path = str(Path(image_path).with_suffix(".bw.png"))
    _preprocess_sketch(image_path, bw_path)
    source = bw_path if os.path.exists(bw_path) else image_path

    # Coba potrace
    try:
        result = subprocess.run(
            ["potrace", "--svg", source, "-o", output_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            notes.append("Dikonversi menggunakan potrace.")
            return SketchToSVGResult(
                input_path=image_path, svg_path=output_path,
                method="potrace", success=True, notes=notes,
            )
        notes.append(f"potrace error: {result.stderr.strip()}")
    except FileNotFoundError:
        notes.append("potrace tidak ditemukan. Install: https://potrace.sourceforge.net")
    except subprocess.TimeoutExpired:
        notes.append("potrace timeout.")

    # Coba Inkscape CLI
    try:
        result = subprocess.run(
            ["inkscape", "--export-type=svg", source, f"--export-filename={output_path}"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            notes.append("Dikonversi menggunakan Inkscape.")
            return SketchToSVGResult(
                input_path=image_path, svg_path=output_path,
                method="inkscape", success=True, notes=notes,
            )
        notes.append(f"Inkscape error: {result.stderr.strip()[:200]}")
    except FileNotFoundError:
        notes.append("Inkscape tidak ditemukan. Install: https://inkscape.org")
    except subprocess.TimeoutExpired:
        notes.append("Inkscape timeout.")

    # Fallback stub
    notes.append(
        "STUB: Tidak ada tool konversi tersedia. "
        "Install potrace (rekomendasi) atau Inkscape untuk konversi nyata."
    )
    return SketchToSVGResult(
        input_path=image_path, svg_path=None,
        method="stub", success=False, notes=notes,
        error="Konversi gagal: potrace dan Inkscape tidak tersedia.",
    )
