"""
Caption & OCR — Projek Badar Task 94 (G3)
Unggah gambar → deskripsi/caption + ekstraksi teks (OCR opsional).
Status: STUB — wire ke LLaVA/BLIP/Qwen-VL ketika model tersedia.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CaptionResult:
    """Hasil caption/deskripsi gambar."""
    caption: str
    confidence: float
    language: str = "id"
    model: str = "stub"


@dataclass
class OCRResult:
    """Hasil ekstraksi teks OCR dari gambar."""
    text: str
    blocks: list = field(default_factory=list)
    confidence: float = 0.0
    language: str = "id"


def generate_caption(image_path: str) -> CaptionResult:
    """
    Generate caption/deskripsi untuk gambar yang diberikan.

    Args:
        image_path: Path absolut ke file gambar.

    Returns:
        CaptionResult berisi caption dan metadata.

    Notes:
        # TODO: load LLaVA/BLIP model, run inference
        # TODO: wire ke transformers pipeline, contoh:
        #   from transformers import BlipProcessor, BlipForConditionalGeneration
        #   processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        #   model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    """
    logger.warning(
        "[STUB] generate_caption dipanggil untuk '%s'. "
        "Model vision belum terpasang. Wire ke LLaVA/BLIP/Qwen-VL.",
        image_path,
    )
    return CaptionResult(
        caption=(
            "[STUB] Gambar memuat konten visual. "
            "Caption akan tersedia setelah model vision diaktifkan."
        ),
        confidence=0.0,
    )


def extract_text_ocr(image_path: str) -> OCRResult:
    """
    Ekstraksi teks dari gambar menggunakan OCR.

    Args:
        image_path: Path absolut ke file gambar.

    Returns:
        OCRResult berisi teks yang diekstrak dan metadata blok.

    Notes:
        Mencoba pytesseract terlebih dahulu; fallback ke stub jika tidak tersedia.
        # pip install pytesseract (requires Tesseract-OCR installed on system)
        # Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
        # TODO: alternatif wire ke PaddleOCR atau model OCR lokal lainnya
    """
    try:
        import pytesseract  # pip install pytesseract (requires Tesseract-OCR installed on system)
        from PIL import Image  # pip install Pillow

        img = Image.open(image_path)
        raw_text = pytesseract.image_to_string(img, lang="ind+eng")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        blocks: list[dict] = []
        for i, word in enumerate(data.get("text", [])):
            if word.strip():
                blocks.append({
                    "text": word,
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "confidence": float(data["conf"][i]) / 100.0,
                })

        avg_conf = (
            sum(b["confidence"] for b in blocks) / len(blocks) if blocks else 0.0
        )
        logger.info("[OCR] pytesseract berhasil. %d blok teks ditemukan.", len(blocks))
        return OCRResult(
            text=raw_text.strip(),
            blocks=blocks,
            confidence=avg_conf,
            language="id",
        )

    except ImportError:
        logger.warning(
            "[STUB] pytesseract tidak tersedia. "
            "Install: pip install pytesseract (dan Tesseract-OCR di sistem)."
        )
        return OCRResult(
            text="[STUB] OCR memerlukan pytesseract atau model OCR lokal.",
            blocks=[],
            confidence=0.0,
        )
    except Exception as exc:
        logger.error("[OCR] Gagal memproses '%s': %s", image_path, exc)
        return OCRResult(
            text=f"[ERROR] OCR gagal: {exc}",
            blocks=[],
            confidence=0.0,
        )
