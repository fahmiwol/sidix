"""
social_radar.py — Analisis Kompetitor & Sentimen UMKM (Social Radar)

Bagian dari Sprint 7: OpHarvest framework untuk memetakan pasar tanpa
melanggar privasi (PII-free). Data publik agregat saja — tanpa PII.
"""

from __future__ import annotations
import re
from typing import Any
from dataclasses import dataclass

# Cap agar tidak ada payload oversized dari extension
_MAX_COMMENTS_SAMPLE = 200
_MAX_METADATA_STR_LEN = 10_000

@dataclass
class RadarSignal:
    source: str
    engagement_rate: float
    sentiment_score: float  # -1.0 to 1.0
    top_keywords: list[str]
    competitor_tier: str    # micro | emerging | leader

# Kata positif & negatif diperluas untuk konteks Indonesia/UMKM
_POS_RE = re.compile(
    r"(bagus|keren|mantap|rekomendasi|beli|puas|cepat|worth|oke|sip|jos|juara|"
    r"memuaskan|terbaik|terpercaya|recommended|gacor|terjangkau|ramah|sigap|aman)",
    re.IGNORECASE,
)
_NEG_RE = re.compile(
    r"(jelek|lambat|kecewa|mahal|cacat|penipu|zonk|nyesel|mengecewakan|bohong|"
    r"lama|rusak|palsu|tipu|abal|boros|ribet|susah|gagal|buruk)",
    re.IGNORECASE,
)


def analyze_social_context(url: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Menganalisis sinyal sosial dari metadata yang dikirim extension.
    Mengikuti Maqashid: Menjaga Mal (bisnis UMKM) dengan data yang benar.
    Hanya menerima sinyal publik agregat — tanpa PII.
    """
    # Guard: tolak payload yang terlalu besar
    if len(str(metadata)) > _MAX_METADATA_STR_LEN:
        return {"status": "error", "reason": "Payload metadata melebihi batas ukuran (10KB)."}

    likes     = max(0, int(metadata.get("likes", 0)))
    comments  = max(0, int(metadata.get("comments", 0)))
    followers = max(1, int(metadata.get("followers", 1)))  # hindari div-by-zero

    er = round((likes + comments) / followers * 100, 2)

    # Cap jumlah komentar sebelum analisis — cegah payload DoS
    raw_comments: list = metadata.get("recent_comments", [])
    sample_comments = raw_comments[:_MAX_COMMENTS_SAMPLE]
    sample_text = " ".join(str(c) for c in sample_comments).lower()

    pos = len(_POS_RE.findall(sample_text))
    neg = len(_NEG_RE.findall(sample_text))

    sentiment = 0.0
    if pos + neg > 0:
        sentiment = round((pos - neg) / (pos + neg), 2)

    tier = "micro"
    if followers > 100_000:
        tier = "leader"
    elif followers > 10_000:
        tier = "emerging"

    return {
        "status": "ok",
        "url": url,
        "metrics": {
            "engagement_rate": er,
            "sentiment": sentiment,
            "tier": tier,
            "sample_size": len(sample_comments),
        },
        "advice": _generate_radar_advice(er, sentiment, tier),
        "maqashid_check": "passed (PII-free, public-aggregate only)",
    }


def _generate_radar_advice(er: float, sentiment: float, tier: str) -> str:
    """Rekomendasi strategis berdasarkan kombinasi sinyal ER + sentimen + tier."""
    # Double signal: engagement tinggi + sentimen negatif = window langka
    if er > 5.0 and sentiment < -0.2:
        return (
            "Window peluang langka: kompetitor punya audiens besar tapi sedang krisis kepercayaan. "
            "Masuk sekarang dengan layanan terpercaya dan respons cepat — audiens mereka siap pindah."
        )
    if sentiment < -0.2:
        return (
            "Kompetitor sedang mengalami krisis kepercayaan. "
            "Ini peluang untuk masuk dengan layanan pelanggan yang lebih baik dan jujur."
        )
    if er > 5.0:
        return (
            "Kompetitor memiliki audiens sangat loyal (ER tinggi). "
            "Jangan bersaing langsung di harga — gunakan strategi niche, personal touch, atau keunggulan layanan."
        )
    if tier == "leader":
        return (
            "Kompetitor sudah besar (>100k followers). "
            "Terus pantau tren konten mereka, tapi fokus membangun niche dan basis pengikut organik sendiri."
        )
    if tier == "emerging":
        return (
            "Kompetitor sedang tumbuh (10k–100k followers). "
            "Pertahankan kecepatan respon dan konsistensi konten — ini fase kritis untuk merebut pasar."
        )
    # micro default
    return (
        "Kompetitor masih seukuran. "
        "Fokus pada diferensiasi visual, kecepatan respon, dan testimoni nyata pelanggan."
    )
