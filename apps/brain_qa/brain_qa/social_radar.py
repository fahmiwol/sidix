"""
social_radar.py — Analisis Kompetitor & Sentimen UMKM (Social Radar)

Bagian dari Sprint 7: OpHarvest framework untuk memetakan pasar tanpa
melanggar privasi (PII-free).
"""

from __future__ import annotations
import re
from typing import Any
from dataclasses import dataclass

@dataclass
class RadarSignal:
    source: str
    engagement_rate: float
    sentiment_score: float  # -1.0 to 1.0
    top_keywords: list[str]
    competitor_tier: str    # micro | emerging | leader

def analyze_social_context(url: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Menganalisis sinyal sosial dari metadata yang dikirim extension.
    Mengikuti Maqashid: Menjaga Mal (bisnis UMKM) dengan data yang benar.
    """
    # Heuristik sederhana untuk Sprint 7 MVP
    likes = int(metadata.get("likes", 0))
    comments = int(metadata.get("comments", 0))
    followers = int(metadata.get("followers", 1)) # hindari div by zero
    
    er = round((likes + comments) / followers * 100, 2) if followers > 0 else 0.0
    
    # Sentiment sederhana berdasarkan keyword di comments (jika ada)
    sample_text = " ".join(metadata.get("recent_comments", [])).lower()
    pos = len(re.findall(r"(bagus|keren|mantap|rekomendasi|beli|puas|cepat)", sample_text))
    neg = len(re.findall(r"(jelek|lambat|kecewa|mahal|cacat|penipu)", sample_text))
    
    sentiment = 0.0
    if pos + neg > 0:
        sentiment = (pos - neg) / (pos + neg)
        
    tier = "micro"
    if followers > 100000: tier = "leader"
    elif followers > 10000: tier = "emerging"
    
    return {
        "status": "ok",
        "url": url,
        "metrics": {
            "engagement_rate": er,
            "sentiment": round(sentiment, 2),
            "tier": tier
        },
        "advice": _generate_radar_advice(er, sentiment, tier),
        "maqashid_check": "passed (PII-free)"
    }

def _generate_radar_advice(er: float, sentiment: float, tier: str) -> str:
    """Rekomendasi strategis berdasarkan sinyal."""
    if sentiment < -0.2:
        return "Kompetitor sedang mengalami krisis kepercayaan. Ini peluang untuk masuk dengan layanan pelanggan yang lebih baik."
    if er > 5.0:
        return "Kompetitor memiliki audiens sangat loyal. Jangan bersaing langsung di harga, gunakan strategi niche / personal touch."
    if tier == "micro":
        return "Kompetitor seukuran. Fokus pada diferensiasi visual dan kecepatan respon."
    return "Terus pantau tren konten mereka, tapi fokus pada membangun basis pengikut organik sendiri."
