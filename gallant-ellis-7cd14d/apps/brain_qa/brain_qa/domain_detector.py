"""
domain_detector.py — Auto-detect Domain dari Question + Persona (Vol 20c)
==========================================================================

Companion untuk semantic_cache.py. Sekarang `agent_serve.py` hardcoded
`domain="casual"` saat lookup/store — tidak optimal karena per-domain
threshold + TTL yang sudah didefinisikan tidak terpakai.

Detection strategy (urut prioritas):
1. **Regex keyword override** (paling spesifik wins)
   - Current events keyword → "current_events" (skip cache)
   - Fiqh/medis/data trigger → conservative threshold 0.96
   - Coding indicator → 0.92 threshold
2. **Persona mapping** (default per persona)
   - UTZ creative → casual (drift OK)
   - ABOO engineer → coding
   - OOMAR strategist → factual
   - ALEY akademik → fiqh/medis/data (high threshold)
   - AYMAN general → casual
3. **Fallback**: "default" (threshold 0.95)

Reference: research note 235 (decision matrix) + 233 (per-domain config).

Anti-pattern dihindari:
- ❌ ML classifier (overkill untuk routing → embed bottleneck)
- ❌ LLM-as-classifier (cost + latency)
- ✅ Regex + persona heuristik (target <1ms, no model load)
"""

from __future__ import annotations

import logging
import re
from typing import Literal

log = logging.getLogger(__name__)


Domain = Literal[
    "fiqh", "medis", "data", "coding",
    "factual", "casual", "current_events", "default",
]


# ── Regex keyword patterns (paling spesifik wins) ────────────────────────────

# Current events — skip cache entirely (TTL=0)
_CURRENT_EVENTS_RE = re.compile(
    r"\b("
    r"hari ini|kemarin|sekarang|today|yesterday|now|"
    r"berita|trending|live|terkini|"
    r"harga.*sekarang|kurs.*sekarang|saham.*hari|"
    r"jam berapa|tanggal berapa|bulan apa|"
    r"latest|recent news|breaking"
    r")\b",
    re.I,
)

# Fiqh/spiritual — high threshold (0.96)
_FIQH_RE = re.compile(
    r"\b("
    r"hukum|halal|haram|riba|fiqh|fikih|sunnah|hadis|hadits|"
    r"sholat|salat|shalat|wudhu|wudu|puasa|zakat|haji|umrah|"
    r"akidah|aqidah|tauhid|syariah|syariat|ibadah|"
    r"imam|ustadz|kyai|"
    r"nikah|talak|warisan|mahram|"
    r"halalkah|bolehkah.*menurut|sahkah|batalkah|"
    r"quran|qur.?an|surah|surat al|ayat|tafsir"
    r")\b",
    re.I,
)

# Medis — high threshold (0.96)
_MEDIS_RE = re.compile(
    r"\b("
    r"penyakit|gejala|diagnos|obat|dosis|terapi|"
    r"diabetes|hipertensi|kanker|jantung|stroke|"
    r"vaksin|imunisasi|antibiotik|antiviral|"
    r"kehamilan|kelahiran|menstruasi|menopause|"
    r"bagaimana cara mengobati|sakit.*obat|berobat|"
    r"dokter spesialis|rumah sakit|klinik|"
    r"medical|disease|symptom|diagnosis|treatment"
    r")\b",
    re.I,
)

# Data/statistik — high threshold (0.95)
_DATA_RE = re.compile(
    r"\b("
    r"statistik|data populasi|sensus|persentase|"
    r"berapa jumlah|berapa banyak|"
    r"pdb|gdp|inflasi|pengangguran|kemiskinan|"
    r"survey|riset|penelitian.*menunjukkan|"
    r"according to|berdasarkan data|laporan resmi"
    r")\b",
    re.I,
)

# Coding — mid threshold (0.92)
_CODING_RE = re.compile(
    r"\b("
    r"python|javascript|typescript|java|golang|rust|"
    r"react|vue|angular|svelte|nextjs|"
    r"docker|kubernetes|nginx|postgres|mysql|mongodb|redis|"
    r"git\b|github|gitlab|"
    r"function|class|method|loop|array|dict|hashmap|"
    r"error|exception|stack trace|debug|"
    r"api|rest|graphql|websocket|"
    r"cara coding|cara koding|cara nge.?code|cara bikin.*aplikasi|"
    r"algoritma|algorithm|data structure|"
    r"compile|build|deploy|"
    r"\.py\b|\.js\b|\.ts\b|\.go\b|\.rs\b|\.html\b"
    r")\b",
    re.I,
)

# Factual/explanatory — mid threshold (0.92)
_FACTUAL_RE = re.compile(
    r"\b("
    r"apa itu|apa yang dimaksud|jelaskan|definisi|pengertian|"
    r"sejarah|kapan|siapa yang|dimana|"
    r"cara kerja|bagaimana cara kerja|how does.*work|"
    r"perbedaan antara|bandingkan|"
    r"what is|explain|definition|history of"
    r")\b",
    re.I,
)


# ── Persona → default domain mapping ──────────────────────────────────────────

PERSONA_DEFAULT_DOMAIN: dict[str, Domain] = {
    "UTZ":   "casual",   # creative/visual, drift OK
    "ABOO":  "coding",   # engineer/technical
    "OOMAR": "factual",  # strategist/business
    "ALEY":  "fiqh",     # akademik (default ke fiqh, akan be overridden)
    "AYMAN": "casual",   # general chat
}


# ── Main detector ─────────────────────────────────────────────────────────────

def detect_domain(question: str, persona: str = "AYMAN") -> Domain:
    """
    Detect domain dari question + persona.

    Priority:
    1. Regex keyword override (paling spesifik wins, tested order)
    2. Persona default mapping
    3. Fallback "default"

    Returns one of: fiqh, medis, data, coding, factual, casual,
    current_events, default
    """
    if not question or not question.strip():
        return PERSONA_DEFAULT_DOMAIN.get(persona.upper(), "default")

    q = question.strip()

    # Priority 1: regex override (specific → general)
    if _CURRENT_EVENTS_RE.search(q):
        return "current_events"

    if _FIQH_RE.search(q):
        return "fiqh"

    if _MEDIS_RE.search(q):
        return "medis"

    if _DATA_RE.search(q):
        return "data"

    if _CODING_RE.search(q):
        return "coding"

    if _FACTUAL_RE.search(q):
        return "factual"

    # Priority 2: persona default
    persona_key = (persona or "AYMAN").upper()
    if persona_key in PERSONA_DEFAULT_DOMAIN:
        return PERSONA_DEFAULT_DOMAIN[persona_key]

    return "default"


def explain_detection(question: str, persona: str = "AYMAN") -> dict:
    """Debug helper — return matched rule + final domain."""
    q = (question or "").strip()
    matched_rule = None
    if _CURRENT_EVENTS_RE.search(q):
        matched_rule = "current_events_regex"
    elif _FIQH_RE.search(q):
        matched_rule = "fiqh_regex"
    elif _MEDIS_RE.search(q):
        matched_rule = "medis_regex"
    elif _DATA_RE.search(q):
        matched_rule = "data_regex"
    elif _CODING_RE.search(q):
        matched_rule = "coding_regex"
    elif _FACTUAL_RE.search(q):
        matched_rule = "factual_regex"
    else:
        matched_rule = f"persona_default[{persona}]"

    return {
        "question": q[:80],
        "persona": persona,
        "matched_rule": matched_rule,
        "domain": detect_domain(question, persona),
    }


__all__ = [
    "Domain",
    "PERSONA_DEFAULT_DOMAIN",
    "detect_domain",
    "explain_detection",
]
