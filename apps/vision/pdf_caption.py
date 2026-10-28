# -*- coding: utf-8 -*-
"""
PDF Page → Image → Caption Pipeline — Projek Badar Task 106 (G3)
Surah Al-Jinn (#72) — Jembatan celah antara tim data dan tim produk.

Konversi halaman PDF ke gambar, lalu jalankan caption/OCR.
Status: STUB — butuh pdf2image (poppler) atau PyMuPDF untuk konversi PDF.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class PageResult:
    """Hasil pemrosesan satu halaman PDF."""
    page_number: int
    image_path: str | None
    caption: str
    ocr_text: str
    confidence: float = 0.0
    error: str | None = None


@dataclass
class PDFCaptionResult:
    """Hasil caption seluruh dokumen PDF."""
    pdf_path: str
    total_pages: int
    processed_pages: int
    pages: list[PageResult] = field(default_factory=list)
    model: str = "stub"
    error: str | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 150) -> list[str]:
    """
    Konversi halaman PDF ke file gambar (PNG per halaman).

    Args:
        pdf_path: Path ke file PDF.
        output_dir: Direktori output untuk file gambar.
        dpi: Resolusi konversi (default 150 DPI = kualitas layar cukup).

    Returns:
        List path file gambar hasil konversi.

    TODO: Wire ke salah satu library:
        - pdf2image (butuh poppler): `from pdf2image import convert_from_path`
        - PyMuPDF (fitz): `import fitz; doc = fitz.open(pdf_path)`
        - pymupdf4llm: khusus untuk LLM pipeline
    """
    # Coba pdf2image
    try:
        from pdf2image import convert_from_path  # type: ignore[import-not-found]
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        images = convert_from_path(pdf_path, dpi=dpi, output_folder=str(out), fmt="png")
        paths = []
        for i, img in enumerate(images):
            p = str(out / f"page_{i+1:04d}.png")
            img.save(p, "PNG")
            paths.append(p)
        logger.info(f"pdf2image: {len(paths)} halaman dikonversi dari {pdf_path}")
        return paths
    except ImportError:
        pass

    # Coba PyMuPDF
    try:
        import fitz  # type: ignore[import-not-found]
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(pdf_path)
        paths = []
        for i in range(len(doc)):
            page = doc[i]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            p = str(out / f"page_{i+1:04d}.png")
            pix.save(p)
            paths.append(p)
        logger.info(f"PyMuPDF: {len(paths)} halaman dikonversi dari {pdf_path}")
        return paths
    except ImportError:
        pass

    logger.warning(
        "[STUB] pdf_to_images: pdf2image dan PyMuPDF tidak terinstall. "
        "Jalankan: pip install pdf2image PyMuPDF"
    )
    return []


def caption_pdf(
    pdf_path: str,
    output_dir: str | None = None,
    max_pages: int = 20,
    dpi: int = 150,
) -> PDFCaptionResult:
    """
    Pipeline lengkap: PDF → gambar per halaman → caption + OCR.

    Args:
        pdf_path: Path ke file PDF.
        output_dir: Direktori sementara untuk gambar (default: /tmp/pdf_caption/<nama_file>).
        max_pages: Batas halaman yang diproses (hindari PDF besar).
        dpi: Resolusi konversi halaman.

    Returns:
        PDFCaptionResult dengan caption tiap halaman.
    """
    from pathlib import Path as _Path

    if not os.path.exists(pdf_path):
        return PDFCaptionResult(
            pdf_path=pdf_path, total_pages=0, processed_pages=0,
            error=f"File tidak ditemukan: {pdf_path}",
        )

    if output_dir is None:
        stem = _Path(pdf_path).stem
        output_dir = str(_Path(pdf_path).parent / f".pdf_cache_{stem}")

    image_paths = pdf_to_images(pdf_path, output_dir=output_dir, dpi=dpi)
    if not image_paths:
        return PDFCaptionResult(
            pdf_path=pdf_path, total_pages=0, processed_pages=0,
            model="stub",
            error="Gagal konversi PDF ke gambar. Install pdf2image atau PyMuPDF.",
        )

    total = len(image_paths)
    to_process = image_paths[:max_pages]
    pages = []

    for i, img_path in enumerate(to_process, start=1):
        try:
            # Import caption dari modul G3 yang sudah ada
            from .caption import generate_caption, extract_text_ocr
            cap = generate_caption(img_path)
            ocr = extract_text_ocr(img_path)
            pages.append(PageResult(
                page_number=i,
                image_path=img_path,
                caption=cap.caption,
                ocr_text=ocr.text,
                confidence=cap.confidence,
            ))
        except ImportError as exc:
            logger.error("[pdf_caption] Gagal import caption module: %s", exc)
            pages.append(PageResult(
                page_number=i, image_path=img_path,
                caption="", ocr_text="",
                error=f"ImportError: {exc}",
            ))
        except Exception as exc:
            logger.error("[pdf_caption] Gagal memproses halaman %d: %s", i, exc)
            pages.append(PageResult(
                page_number=i,
                image_path=img_path,
                caption="",
                ocr_text="",
                error=str(exc),
            ))

    return PDFCaptionResult(
        pdf_path=pdf_path,
        total_pages=total,
        processed_pages=len(pages),
        pages=pages,
        model="stub",
    )


def format_pdf_caption_report(result: PDFCaptionResult) -> str:
    """Format PDFCaptionResult sebagai teks human-readable."""
    lines = [
        f"PDF: {result.pdf_path}",
        f"Total halaman: {result.total_pages}, diproses: {result.processed_pages}",
        f"Model: {result.model}",
        "",
    ]
    if result.error:
        lines.append(f"ERROR: {result.error}")
        return "\n".join(lines)

    for p in result.pages:
        lines.append(f"--- Halaman {p.page_number} ---")
        if p.error:
            lines.append(f"  ERROR: {p.error}")
        else:
            lines.append(f"  Caption: {p.caption[:120]}")
            if p.ocr_text.strip():
                lines.append(f"  OCR: {p.ocr_text[:120]}")
        lines.append("")

    return "\n".join(lines)
