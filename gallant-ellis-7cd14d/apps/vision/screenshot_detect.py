# -*- coding: utf-8 -*-
"""
UI Screenshot Detection — Projek Badar Task 114 (G3)
Surah Al-Ikhlas (#112) — Percepat path panas tanpa mengorbankan keamanan.

Deteksi apakah gambar adalah screenshot aplikasi UI dan ekstrak informasi
struktural: platform, komponen UI, teks visible, URL (jika browser screenshot).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ScreenshotPlatform(str, Enum):
    BROWSER = "browser"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    TERMINAL = "terminal"
    UNKNOWN = "unknown"


@dataclass
class UIElement:
    """Elemen UI yang terdeteksi di screenshot."""
    element_type: str    # "button", "input", "navbar", "modal", "text", "icon"
    text: str
    bbox: dict = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class ScreenshotInfo:
    """Informasi yang diekstrak dari screenshot UI."""
    image_path: str
    is_screenshot: bool
    platform: ScreenshotPlatform
    visible_url: str                        # URL dari address bar (jika browser)
    page_title: str
    ui_elements: list[UIElement] = field(default_factory=list)
    raw_ocr_text: str = ""
    model: str = "stub"
    confidence: float = 0.0
    error: str | None = None


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

_BROWSER_PATTERNS = [
    re.compile(r"https?://[^\s]+"),
    re.compile(r"www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"),
]

_TERMINAL_KEYWORDS = [
    "$", ">>>", ">>>", "bash", "zsh", "powershell", "cmd",
    "error:", "warning:", "traceback", "pip install",
]

_MOBILE_SIGNALS = [
    "9:41", "100%", "Wi-Fi", "LTE", "5G", "4G",  # status bar indicators
]


def _detect_platform(ocr_text: str, image_path: str) -> ScreenshotPlatform:
    """Deteksi platform berdasarkan teks OCR dan nama file."""
    lower_text = ocr_text.lower()
    lower_path = image_path.lower()

    # Cek nama file
    if any(kw in lower_path for kw in ("browser", "chrome", "firefox", "safari", "edge")):
        return ScreenshotPlatform.BROWSER
    if any(kw in lower_path for kw in ("android", "ios", "mobile", "iphone", "samsung")):
        return ScreenshotPlatform.MOBILE_APP
    if any(kw in lower_path for kw in ("terminal", "cmd", "powershell", "bash")):
        return ScreenshotPlatform.TERMINAL

    # Cek teks OCR
    if any(p.search(ocr_text) for p in _BROWSER_PATTERNS):
        return ScreenshotPlatform.BROWSER
    if any(kw in lower_text for kw in _TERMINAL_KEYWORDS):
        return ScreenshotPlatform.TERMINAL
    if any(sig in ocr_text for sig in _MOBILE_SIGNALS):
        return ScreenshotPlatform.MOBILE_APP

    return ScreenshotPlatform.UNKNOWN


def _extract_url(ocr_text: str) -> str:
    """Ekstrak URL dari teks OCR screenshot browser."""
    for pattern in _BROWSER_PATTERNS:
        match = pattern.search(ocr_text)
        if match:
            return match.group(0).strip()
    return ""


def _is_likely_screenshot(image_path: str) -> bool:
    """
    Heuristik sederhana: apakah ini screenshot?
    Berbasis aspek ratio dan ukuran gambar.
    """
    try:
        from PIL import Image  # type: ignore[import-not-found]
        img = Image.open(image_path)
        w, h = img.size
        # Screenshot biasanya aspek ratio layar umum: 16:9, 16:10, 4:3, 9:16
        ratio = w / h if h > 0 else 0
        common_ratios = [16/9, 16/10, 4/3, 9/16, 19.5/9, 21/9]
        return any(abs(ratio - r) < 0.15 for r in common_ratios)
    except Exception:
        return True  # Assume screenshot bila tidak bisa dicek


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def detect_screenshot(image_path: str) -> ScreenshotInfo:
    """
    Deteksi apakah gambar adalah screenshot UI dan ekstrak informasi.

    Pipeline:
    1. Heuristik: aspek ratio → kemungkinan screenshot
    2. OCR teks terlihat di layar
    3. Klasifikasi platform (browser/mobile/desktop/terminal)
    4. Ekstrak URL, judul halaman, elemen UI

    TODO (fast path sesuai surah Al-Ikhlas — percepat tanpa korbankan keamanan):
    - Cache hasil per SHA256 image hash
    - Jalankan OCR hanya pada region address bar (top 10% height) untuk browser
    - Gunakan VLM dengan prompt singkat: "Is this a UI screenshot? Platform? URL?"

    Args:
        image_path: Path ke gambar yang diduga screenshot.

    Returns:
        ScreenshotInfo dengan detail platform dan konten.
    """
    import os
    if not os.path.exists(image_path):
        return ScreenshotInfo(
            image_path=image_path,
            is_screenshot=False,
            platform=ScreenshotPlatform.UNKNOWN,
            visible_url="", page_title="",
            error=f"File tidak ditemukan: {image_path}",
        )

    is_screenshot = _is_likely_screenshot(image_path)

    # OCR untuk teks
    raw_ocr = ""
    try:
        from .caption import extract_text_ocr
        ocr = extract_text_ocr(image_path)
        raw_ocr = ocr.text
    except Exception:
        pass

    # Jika OCR stub (tidak ada teks nyata)
    if "[STUB]" in raw_ocr or not raw_ocr.strip():
        logger.warning(
            "[STUB] screenshot_detect.detect_screenshot() — OCR stub aktif. "
            "Aktifkan pytesseract atau VLM untuk deteksi nyata."
        )
        return ScreenshotInfo(
            image_path=image_path,
            is_screenshot=is_screenshot,
            platform=ScreenshotPlatform.UNKNOWN,
            visible_url="",
            page_title="[STUB]",
            raw_ocr_text=raw_ocr,
            model="stub",
            confidence=0.0,
            error="OCR stub aktif: aktifkan pytesseract atau VLM untuk deteksi nyata.",
        )

    platform = _detect_platform(raw_ocr, image_path)
    url = _extract_url(raw_ocr) if platform == ScreenshotPlatform.BROWSER else ""

    # Ekstrak judul halaman: ambil baris pertama yang bukan URL
    title = ""
    for line in raw_ocr.splitlines():
        line = line.strip()
        if line and not re.match(r"https?://", line) and len(line) < 100:
            title = line
            break

    return ScreenshotInfo(
        image_path=image_path,
        is_screenshot=is_screenshot,
        platform=platform,
        visible_url=url,
        page_title=title,
        raw_ocr_text=raw_ocr,
        model="ocr-heuristic",
        confidence=0.5,
    )


def format_screenshot_info(info: ScreenshotInfo) -> str:
    """Format ScreenshotInfo sebagai teks ringkas."""
    if info.error and not info.raw_ocr_text:
        return f"ERROR: {info.error}"
    lines = [
        f"Screenshot: {'Ya' if info.is_screenshot else 'Tidak'}",
        f"Platform: {info.platform.value}",
    ]
    if info.visible_url:
        lines.append(f"URL: {info.visible_url}")
    if info.page_title:
        lines.append(f"Judul: {info.page_title}")
    if info.error:
        lines.append(f"Catatan: {info.error}")
    return "\n".join(lines)
