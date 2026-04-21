"""
generate_og_image.py — Generate og-image.png 1200x630 untuk SIDIX

Menghasilkan branded preview image untuk Threads/Twitter/LinkedIn cards.
Pakai PIL (Pillow) — biasanya sudah ada di env Python server.

Output: /www/wwwroot/sidixlab.com/og-image.png
"""

from __future__ import annotations

import sys
from pathlib import Path


def generate_og_image(output_path: str = "/www/wwwroot/sidixlab.com/og-image.png") -> dict:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {"ok": False, "error": "Pillow not installed (pip install Pillow)"}

    # Canvas 1200x630 dengan background gradient warm-dark
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), color=(20, 17, 13))   # warm-950
    draw = ImageDraw.Draw(img)

    # Gradient overlay (top dark, bottom slightly lighter)
    for y in range(H):
        ratio = y / H
        r = int(20 + 15 * ratio)
        g = int(17 + 12 * ratio)
        b = int(13 + 10 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Gold accent line
    GOLD = (212, 168, 83)
    draw.rectangle([(0, 0), (W, 6)], fill=GOLD)
    draw.rectangle([(0, H - 6), (W, H)], fill=GOLD)

    # Try load font, fallback to default
    title_font = None
    sub_font = None
    small_font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    body_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                title_font = ImageFont.truetype(fp, 80)
                sub_font = ImageFont.truetype(fp, 36)
                break
            except Exception:
                continue
    for fp in body_font_paths:
        if Path(fp).exists():
            try:
                small_font = ImageFont.truetype(fp, 26)
                break
            except Exception:
                continue

    if not title_font:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Free Open Source badge (top-right area)
    BADGE_BG = (30, 90, 40)  # dark green
    draw.rounded_rectangle([(W - 360, 50), (W - 60, 110)], radius=8, fill=BADGE_BG)
    draw.text((W - 340, 63), "FREE  OPEN SOURCE", fill=(120, 230, 130), font=small_font)

    # Logo / brand mark (top-left)
    draw.text((60, 50), "SIDIX", fill=GOLD, font=title_font)
    draw.text((60, 148), "by Mighan Lab", fill=(200, 195, 178), font=small_font)

    # Tagline tengah — main pitch
    PARCH = (245, 240, 220)   # parchment-100
    draw.text(
        (60, 240),
        "Free & Open Source",
        fill=GOLD,
        font=title_font,
    )
    draw.text(
        (60, 340),
        "AI Agent",
        fill=PARCH,
        font=title_font,
    )
    draw.text(
        (60, 435),
        "Self-Hosted · Self-Learning · No Vendor API",
        fill=PARCH,
        font=sub_font,
    )

    # Subtitle bawah
    draw.text(
        (60, 490),
        "Qwen2.5-7B + LoRA · 35 tools · 100% Local Inference",
        fill=(180, 175, 158),
        font=small_font,
    )
    draw.text(
        (60, 530),
        "Built on Islamic Epistemology (IHOS) · MIT License",
        fill=(180, 175, 158),
        font=small_font,
    )

    # Domain bottom right
    draw.text(
        (W - 280, H - 60),
        "sidixlab.com",
        fill=GOLD,
        font=small_font,
    )

    # Pattern decorative (3 dots gold di kanan atas)
    for i, dx in enumerate([0, 30, 60]):
        x = W - 100 + dx
        y = 80
        draw.ellipse([(x - 6, y - 6), (x + 6, y + 6)], fill=GOLD)

    # Save
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)

    return {
        "ok":         True,
        "output":     output_path,
        "size_bytes": out_p.stat().st_size,
        "dimensions": f"{W}x{H}",
    }


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "/www/wwwroot/sidixlab.com/og-image.png"
    result = generate_og_image(output)
    print(result)
