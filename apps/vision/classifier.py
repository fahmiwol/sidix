"""
Image Classifier — Projek Badar Task 95 (G3)
Klasifikasi jenis gambar (diagram/foto/sketsa) untuk routing model.
Status: STUB — heuristik sederhana; wire ke model klasifikasi lokal untuk akurasi penuh.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ImageType(Enum):
    """Jenis-jenis gambar yang dikenali."""
    PHOTO = "photo"
    DIAGRAM = "diagram"
    SKETCH = "sketch"
    CHART = "chart"
    SCREENSHOT = "screenshot"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Hasil klasifikasi jenis gambar."""
    image_type: ImageType
    confidence: float
    route_to: str
    reasoning: str


# Peta routing: setiap jenis gambar diarahkan ke handler yang sesuai
ROUTING_MAP: dict[ImageType, str] = {
    ImageType.PHOTO: "caption",
    ImageType.DIAGRAM: "flowchart_ocr",
    ImageType.SKETCH: "line_art",
    ImageType.CHART: "table_extract",
    ImageType.SCREENSHOT: "ocr",
    ImageType.UNKNOWN: "caption",
}

# Kata kunci nama file untuk heuristik cepat
_FILENAME_HINTS: dict[str, ImageType] = {
    "diagram": ImageType.DIAGRAM,
    "chart": ImageType.CHART,
    "graph": ImageType.CHART,
    "sketch": ImageType.SKETCH,
    "screenshot": ImageType.SCREENSHOT,
    "screen": ImageType.SCREENSHOT,
    "photo": ImageType.PHOTO,
    "foto": ImageType.PHOTO,
    "flowchart": ImageType.DIAGRAM,
    "flow": ImageType.DIAGRAM,
    "table": ImageType.CHART,
    "tabel": ImageType.CHART,
}


def _heuristic_from_filename(image_path: str) -> ImageType | None:
    """Tebak jenis gambar dari nama file (heuristik sederhana)."""
    basename = os.path.basename(image_path).lower()
    for keyword, img_type in _FILENAME_HINTS.items():
        if keyword in basename:
            return img_type
    return None


def _heuristic_from_pil(image_path: str) -> tuple[ImageType | None, str]:
    """
    Heuristik ringan berbasis analisis PIL:
    - Gambar grayscale dengan sedikit warna → kemungkinan sketsa/diagram
    - Rasio aspek sangat lebar → kemungkinan screenshot
    Mengembalikan (ImageType|None, alasan).
    """
    try:
        from PIL import Image

        img = Image.open(image_path)
        width, height = img.size
        mode = img.mode

        # Screenshot: rasio sangat lebar (>2.5) atau portrait sempit (<0.4)
        ratio = width / height if height > 0 else 1.0
        if ratio > 2.5 or (mode == "RGB" and ratio < 0.4 and width < 800):
            return ImageType.SCREENSHOT, f"Rasio aspek {ratio:.2f} menyerupai screenshot."

        # Sketsa: gambar grayscale / hitam-putih
        if mode in ("L", "1"):
            return ImageType.SKETCH, "Gambar grayscale/monochrome → kemungkinan sketsa."

        # Konversi ke grayscale untuk analisis warna
        gray = img.convert("L")
        pixels = list(gray.getdata())
        avg_bright = sum(pixels) / len(pixels)

        # Diagram/chart: banyak piksel putih (latar terang) + variasi rendah
        white_ratio = sum(1 for p in pixels if p > 230) / len(pixels)
        if white_ratio > 0.6:
            return ImageType.DIAGRAM, f"Latar terang ({white_ratio:.0%} putih) → kemungkinan diagram."

        return None, ""

    except ImportError:
        return None, "PIL tidak tersedia untuk analisis gambar."
    except Exception as exc:
        return None, f"Analisis PIL gagal: {exc}"


def classify_image(image_path: str) -> ClassificationResult:
    """
    Klasifikasikan jenis gambar untuk routing ke handler yang tepat.

    Urutan pengecekan:
    1. Heuristik nama file
    2. Analisis PIL ringan
    3. Fallback stub

    Args:
        image_path: Path absolut ke file gambar.

    Returns:
        ClassificationResult dengan jenis gambar dan handler tujuan.

    Notes:
        # TODO: wire ke model klasifikasi lokal (ViT, EfficientNet, dll.)
        # TODO: tambahkan threshold confidence yang dapat dikonfigurasi
    """
    # 1. Heuristik nama file
    filename_type = _heuristic_from_filename(image_path)
    if filename_type:
        logger.info("[Classifier] Heuristik nama file → %s", filename_type.value)
        return ClassificationResult(
            image_type=filename_type,
            confidence=0.5,
            route_to=ROUTING_MAP[filename_type],
            reasoning=f"Heuristik nama file mendeteksi keyword terkait '{filename_type.value}'.",
        )

    # 2. Analisis PIL
    pil_type, pil_reason = _heuristic_from_pil(image_path)
    if pil_type:
        logger.info("[Classifier] Analisis PIL → %s: %s", pil_type.value, pil_reason)
        return ClassificationResult(
            image_type=pil_type,
            confidence=0.4,
            route_to=ROUTING_MAP[pil_type],
            reasoning=pil_reason,
        )

    # 3. Fallback stub
    logger.warning(
        "[STUB] classify_image: tidak dapat menentukan jenis '%s'. "
        "Wire ke model klasifikasi lokal untuk akurasi penuh.",
        image_path,
    )
    return ClassificationResult(
        image_type=ImageType.UNKNOWN,
        confidence=0.0,
        route_to="caption",
        reasoning="Stub: model tidak dimuat, fallback ke caption handler.",
    )


def route_to_handler(classification: ClassificationResult) -> str:
    """
    Kembalikan nama handler berdasarkan hasil klasifikasi.

    Args:
        classification: Hasil dari classify_image().

    Returns:
        Nama handler sebagai string (misalnya 'caption', 'flowchart_ocr', dll.).
    """
    return ROUTING_MAP.get(classification.image_type, "caption")
