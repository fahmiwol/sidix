"""
context_triple.py — Zaman / Makan / Haal Vector (Personalized Context)
=========================================================================

Per DIRECTION_LOCK_20260426 P1 Q3 2026:
> "Context Triple Vector: zaman/makan/haal injection ke ReAct prompt"

Filosofi (engineering interpretation, BUKAN spiritual claim — per
DIRECTION_LOCK section 3 acknowledge):
- **Zaman** (waktu): kapan user tanya — pagi/malam, hari/musim,
  current events
- **Makan** (tempat): di mana user berada — geo, locale, cultural context
- **Haal** (kondisi): bagaimana state user — recent history, emotional
  tone, persona dominant, urgency

Pattern proven di engineering: **personalized response dengan context-aware
prompt > generic response**. Wikipedia tau musim hujan/kemarau di
Indonesia beda dengan winter/summer di US — sama untuk AI yang answer
"baju cocok untuk hari ini?".

Mekanisme:
1. Derive triple vector dari signal yang available:
   - Server time → zaman (UTC + WIB conversion)
   - Request IP → makan (geo lookup, conservative privacy)
   - User_id history → haal (recent N message → tone/topic/urgency)
2. Format jadi prompt prefix yang bisa di-inject ke ReAct
3. LLM output sekarang aware konteks user, bukan generik

Privacy: TIDAK store IP raw atau geo precise. Hanya derive bucket
("Asia/Jakarta", "morning peak hour", "calm tone") yang anonymized.

Output ContextTriple: ringkas, bisa langsung di-prefix ke prompt LLM.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class ContextTriple:
    """Zaman + Makan + Haal vector untuk personalize ReAct prompt."""
    # Zaman (waktu)
    iso_timestamp: str
    time_of_day: str              # "morning" | "afternoon" | "evening" | "night"
    timezone_label: str            # "Asia/Jakarta" (ID default), or detected
    weekend: bool
    season_id: str                 # ID-specific: "musim_hujan" | "musim_kemarau" | "transisi"

    # Makan (tempat)
    locale_hint: str               # "id-ID" | "en-US" (dari header / IP geo bucket)
    geo_bucket: str                # "Indonesia" | "SE Asia" | "Other" (NO precise location)
    cultural_context: str          # "Islamic context likely" | "general"

    # Haal (kondisi)
    recent_topic_focus: list[str] = field(default_factory=list)  # last 5 message topic
    recent_persona_dominant: str = ""
    emotional_tone_estimate: str = "neutral"  # "neutral" | "urgent" | "calm" | "frustrated"
    session_length_signal: str = "fresh"      # "fresh" | "extended"


# ── Time helpers ───────────────────────────────────────────────────────────────

def _derive_zaman(now_utc: datetime) -> dict:
    """Derive zaman bucket dari UTC time + Asia/Jakarta convert."""
    # WIB = UTC+7
    wib_hour = (now_utc + timedelta(hours=7)).hour
    if 5 <= wib_hour < 11:
        tod = "morning"
    elif 11 <= wib_hour < 15:
        tod = "afternoon"
    elif 15 <= wib_hour < 18:
        tod = "late_afternoon"
    elif 18 <= wib_hour < 22:
        tod = "evening"
    else:
        tod = "night"

    # Day of week (WIB)
    wib_now = now_utc + timedelta(hours=7)
    weekend = wib_now.weekday() >= 5  # Sat=5, Sun=6

    # Indonesian season (rough heuristic, NO climate API yet)
    month = wib_now.month
    if month in (11, 12, 1, 2, 3):
        season = "musim_hujan"
    elif month in (5, 6, 7, 8, 9):
        season = "musim_kemarau"
    else:
        season = "transisi"

    return {
        "iso_timestamp": now_utc.isoformat(),
        "time_of_day": tod,
        "timezone_label": "Asia/Jakarta",
        "weekend": weekend,
        "season_id": season,
    }


# ── Geo helpers (privacy-conscious bucketing) ─────────────────────────────────

def _derive_makan(request_metadata: Optional[dict] = None) -> dict:
    """
    Derive makan bucket. Conservative privacy:
    - Tidak store IP raw
    - Hanya bucket besar (Indonesia / SE Asia / Other)
    - Locale dari Accept-Language header kalau ada
    """
    locale = "id-ID"  # default Indonesia
    geo_bucket = "Indonesia"
    cultural_context = "Islamic context likely"

    if request_metadata:
        # Accept-Language header
        al = (request_metadata.get("accept_language") or "").lower()
        if al:
            if al.startswith("id"):
                locale = "id-ID"
            elif al.startswith("en"):
                locale = "en-US"
                geo_bucket = "Other"
                cultural_context = "general"
            elif al.startswith(("ms", "jv", "su")):
                locale = al[:5]
                geo_bucket = "SE Asia"
                cultural_context = "Islamic context likely"

        # IP geo hint (kalau ada — paling banyak deriv dari nginx Cloudflare-IP-Country header)
        country = (request_metadata.get("country") or "").upper()
        if country == "ID":
            geo_bucket = "Indonesia"
        elif country in ("MY", "SG", "BN", "TH", "PH"):
            geo_bucket = "SE Asia"
        elif country:
            geo_bucket = "Other"
            if country in ("US", "CA", "AU", "GB"):
                cultural_context = "general"

    return {
        "locale_hint": locale,
        "geo_bucket": geo_bucket,
        "cultural_context": cultural_context,
    }


# ── User state helpers (haal) ─────────────────────────────────────────────────

def _derive_haal(user_id: str = "") -> dict:
    """
    Derive haal bucket dari user activity log:
    - Recent topic focus (last 5 message)
    - Dominant persona pattern
    - Emotional tone estimate (heuristic)
    - Session length (fresh vs extended chatter)
    """
    out = {
        "recent_topic_focus": [],
        "recent_persona_dominant": "",
        "emotional_tone_estimate": "neutral",
        "session_length_signal": "fresh",
    }

    if not user_id:
        return out

    try:
        from . import auth_google
        entries = auth_google.list_activity(limit=10, user_id=user_id)
    except Exception:
        return out

    if not entries:
        return out

    # Recent persona dominant
    from collections import Counter
    personas = [e.get("persona", "") for e in entries if e.get("persona")]
    if personas:
        top, count = Counter(personas).most_common(1)[0]
        if top and top != "?":
            out["recent_persona_dominant"] = top

    # Topic focus (extract dari question first 30 char)
    topics = []
    for e in entries[:5]:
        q = (e.get("question") or "")[:60]
        if q:
            topics.append(q.strip())
    out["recent_topic_focus"] = topics

    # Emotional tone heuristic — kalau ada error rate tinggi atau urgency keyword
    error_count = sum(1 for e in entries if (e.get("error", "") or "").strip())
    if error_count >= 3:
        out["emotional_tone_estimate"] = "frustrated"

    urgency_keywords = ["cepat", "buruan", "urgent", "asap", "sekarang", "tolong"]
    recent_text = " ".join((e.get("question") or "").lower() for e in entries[:3])
    if any(kw in recent_text for kw in urgency_keywords):
        out["emotional_tone_estimate"] = "urgent"

    # Session length: kalau >5 msg dalam 30 menit terakhir → extended
    now = datetime.now(timezone.utc)
    recent_30m = 0
    for e in entries:
        try:
            ts = datetime.fromisoformat((e.get("ts") or "").replace("Z", "+00:00"))
            if (now - ts).total_seconds() < 1800:
                recent_30m += 1
        except Exception:
            continue
    if recent_30m >= 5:
        out["session_length_signal"] = "extended"

    return out


# ── Main: derive_context_triple ───────────────────────────────────────────────

def derive_context_triple(
    user_id: str = "",
    request_metadata: Optional[dict] = None,
) -> ContextTriple:
    """
    Generate ContextTriple lengkap dari signal yang available.

    Args:
        user_id: SIDIX user_id (untuk haal dari activity log)
        request_metadata: dict dengan {accept_language?, country?, ip?}
                          (gracefully handle missing — privacy default)

    Returns ContextTriple ready untuk inject ke prompt.
    """
    now = datetime.now(timezone.utc)
    zaman = _derive_zaman(now)
    makan = _derive_makan(request_metadata)
    haal = _derive_haal(user_id)

    return ContextTriple(
        iso_timestamp=zaman["iso_timestamp"],
        time_of_day=zaman["time_of_day"],
        timezone_label=zaman["timezone_label"],
        weekend=zaman["weekend"],
        season_id=zaman["season_id"],
        locale_hint=makan["locale_hint"],
        geo_bucket=makan["geo_bucket"],
        cultural_context=makan["cultural_context"],
        recent_topic_focus=haal["recent_topic_focus"],
        recent_persona_dominant=haal["recent_persona_dominant"],
        emotional_tone_estimate=haal["emotional_tone_estimate"],
        session_length_signal=haal["session_length_signal"],
    )


# ── Format as prompt prefix ───────────────────────────────────────────────────

def format_for_prompt(triple: ContextTriple, *, verbose: bool = False) -> str:
    """
    Format ContextTriple jadi compact prompt prefix untuk inject ke ReAct.

    Verbose mode untuk debugging; non-verbose untuk production (singkat,
    hemat token).
    """
    if verbose:
        return f"""[CONTEXT_TRIPLE]
zaman: {triple.time_of_day} ({triple.timezone_label}, weekend={triple.weekend}, season={triple.season_id})
makan: {triple.geo_bucket} (locale={triple.locale_hint}, culture={triple.cultural_context})
haal: tone={triple.emotional_tone_estimate}, session={triple.session_length_signal}
recent_persona={triple.recent_persona_dominant or 'none'}
recent_topics: {', '.join(triple.recent_topic_focus[:3]) if triple.recent_topic_focus else 'none'}
[/CONTEXT_TRIPLE]
"""

    # Compact production mode (~30-50 token)
    parts = [
        f"Konteks user saat ini: {triple.time_of_day} ({triple.timezone_label})",
        f"di {triple.geo_bucket}",
    ]
    if triple.weekend:
        parts.append("(weekend)")
    if triple.emotional_tone_estimate != "neutral":
        parts.append(f"tone={triple.emotional_tone_estimate}")
    if triple.session_length_signal == "extended":
        parts.append("(continuing conversation)")
    return ", ".join(parts) + "."


__all__ = ["ContextTriple", "derive_context_triple", "format_for_prompt"]
