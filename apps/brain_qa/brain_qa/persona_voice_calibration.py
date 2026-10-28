"""
persona_voice_calibration.py — Persona Voice Calibration Engine

SIDIX learns user taste/preferences on voice/tone per persona.

Konsep:
- Setiap user punya VoiceProfile per persona (AYMAN, ABOO, OOMAR, ALEY, UTZ)
- 6 dimensi kalibrasi: warmth, formality, depth, humor, religiosity, nusantara_flavor
- Setiap dimensi: float [-1.0, 1.0], 0 = default persona
- Sumber signal: explicit text feedback, thumbs up/down, Jariyah pairs
- Output: modifier dict + voice hint untuk inject ke system prompt / response blend

Pivot 2026-04-25 — Jiwa Sprint Phase 1 (Kimi lane)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────

# Delta per feedback type
_EXPLICIT_DELTA = 0.15
_THUMBS_UP_DELTA = 0.05
_THUMBS_DOWN_DELTA = -0.05
_JARIYAH_DELTA = 0.03

# Damping: implicit feedback di-distribusi ke semua dimension dengan faktor ini
_IMPLICIT_DIM_FACTOR = 0.3

# Clamp range
_MIN_VAL = -1.0
_MAX_VAL = 1.0


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class VoiceProfile:
    """Kalibrasi voice per (user_id, persona)."""

    user_id: str
    persona: str
    warmth: float = 0.0  # -1=cold, +1=warm
    formality: float = 0.0  # -1=casual, +1=formal
    depth: float = 0.0  # -1=brief, +1=deep
    humor: float = 0.0  # -1=serious, +1=humorous
    religiosity: float = 0.0  # -1=secular, +1=religious
    nusantara_flavor: float = 0.0  # -1=neutral, +1=strong local
    sample_count: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VoiceFeedback:
    """Satu record feedback voice."""

    user_id: str
    persona: str
    feedback_type: str  # explicit | thumbs_up | thumbs_down | jariyah
    dimension: str | None = None
    delta: float = 0.0
    raw_text: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Explicit feedback parser ─────────────────────────────────────────────────

_EXPLICIT_PATTERNS: list[tuple[str, str, float]] = [
    # (regex, dimension, delta)
    (r"lebih\s+(formal|serius)", "formality", _EXPLICIT_DELTA),
    (r"terlalu\s+(santai|informal|casual|nyantai)", "formality", _EXPLICIT_DELTA),
    (r"lebih\s+(santai|informal|casual|nyantai)", "formality", -_EXPLICIT_DELTA),
    (r"terlalu\s+(formal|kaku)", "formality", -_EXPLICIT_DELTA),
    (r"lebih\s+(panjang|detail|mendalam|elaborat)", "depth", _EXPLICIT_DELTA),
    (r"terlalu\s+(singkat|pendek|ringkas|kurang)", "depth", _EXPLICIT_DELTA),
    (r"lebih\s+(singkat|pendek|ringkas|to\s+the\s+point)", "depth", -_EXPLICIT_DELTA),
    (r"terlalu\s+(panjang|banyak|lebay|bertele-tele)", "depth", -_EXPLICIT_DELTA),
    (r"lebih\s+(hangat|ramah|manusiawi|empati)", "warmth", _EXPLICIT_DELTA),
    (r"terlalu\s+(dingin|kaku|robot|mesin)", "warmth", _EXPLICIT_DELTA),
    (r"lebih\s+(dingin|tegas|profesional)", "warmth", -_EXPLICIT_DELTA),
    (r"lebih\s+(lucu|jenaka|humor|funny)", "humor", _EXPLICIT_DELTA),
    (r"terlalu\s+(serius|membosankan|flat)", "humor", -_EXPLICIT_DELTA),
    (r"lebih\s+(religius|islami|syar\.i|spiritual)", "religiosity", _EXPLICIT_DELTA),
    (r"lebih\s+(lokal|nusantara|indonesia|jawa|melayu)", "nusantara_flavor", _EXPLICIT_DELTA),
]


def _parse_explicit_feedback(text: str) -> tuple[str | None, float]:
    """Parse explicit text feedback → (dimension, delta)."""
    text_lower = text.lower()
    for pattern, dimension, delta in _EXPLICIT_PATTERNS:
        if re.search(pattern, text_lower):
            return dimension, delta
    return None, 0.0


def _clamp(val: float) -> float:
    return max(_MIN_VAL, min(_MAX_VAL, val))


# ── Store ────────────────────────────────────────────────────────────────────

class VoiceCalibrationStore:
    """Storage + business logic untuk voice calibration."""

    _DIMENSIONS = ["warmth", "formality", "depth", "humor", "religiosity", "nusantara_flavor"]

    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self.profile_path = os.path.join(self.data_dir, "voice_profiles.jsonl")
        self.feedback_path = os.path.join(self.data_dir, "voice_feedback.jsonl")
        self._profiles: dict[tuple[str, str], VoiceProfile] = {}
        self._load_profiles()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_profiles(self) -> None:
        if not os.path.exists(self.profile_path):
            return
        with open(self.profile_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    profile = VoiceProfile(**data)
                    self._profiles[(profile.user_id, profile.persona)] = profile
                except Exception:
                    continue

    def _save_profiles(self) -> None:
        with open(self.profile_path, "w", encoding="utf-8") as f:
            for profile in self._profiles.values():
                f.write(json.dumps(profile.__dict__, ensure_ascii=False) + "\n")

    def _append_feedback(self, feedback: VoiceFeedback) -> None:
        with open(self.feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback.__dict__, ensure_ascii=False) + "\n")

    # ── Core API ─────────────────────────────────────────────────────────────

    def get_profile(self, user_id: str, persona: str) -> VoiceProfile:
        key = (user_id, persona)
        if key not in self._profiles:
            self._profiles[key] = VoiceProfile(user_id=user_id, persona=persona)
        return self._profiles[key]

    def record_explicit(self, user_id: str, persona: str, text: str) -> VoiceProfile:
        """User kasih explicit feedback teks, e.g. 'kurang formal', 'terlalu panjang'."""
        dimension, delta = _parse_explicit_feedback(text)
        profile = self.get_profile(user_id, persona)

        if dimension:
            current = getattr(profile, dimension, 0.0)
            setattr(profile, dimension, _clamp(current + delta))
            profile.sample_count += 1
            profile.updated_at = datetime.now(timezone.utc).isoformat()

        self._append_feedback(
            VoiceFeedback(
                user_id=user_id,
                persona=persona,
                feedback_type="explicit",
                dimension=dimension,
                delta=delta,
                raw_text=text,
            )
        )
        self._save_profiles()
        return profile

    def record_thumbs(self, user_id: str, persona: str, vote: str) -> VoiceProfile:
        """vote = 'up' | 'down'. Distribusi kecil ke semua dimensi."""
        delta = _THUMBS_UP_DELTA if vote == "up" else _THUMBS_DOWN_DELTA
        profile = self.get_profile(user_id, persona)

        for dim in self._DIMENSIONS:
            current = getattr(profile, dim)
            setattr(profile, dim, _clamp(current + delta * _IMPLICIT_DIM_FACTOR))

        profile.sample_count += 1
        profile.updated_at = datetime.now(timezone.utc).isoformat()

        self._append_feedback(
            VoiceFeedback(
                user_id=user_id,
                persona=persona,
                feedback_type=f"thumbs_{vote}",
                delta=delta,
            )
        )
        self._save_profiles()
        return profile

    def record_jariyah(self, user_id: str, persona: str) -> VoiceProfile:
        """High CQF + masuk Jariyah = voice diterima, reinforce arah saat ini."""
        profile = self.get_profile(user_id, persona)

        for dim in self._DIMENSIONS:
            current = getattr(profile, dim)
            if current > 0:
                new_val = min(_MAX_VAL, current + _JARIYAH_DELTA)
            elif current < 0:
                new_val = max(_MIN_VAL, current - _JARIYAH_DELTA)
            else:
                new_val = 0.0
            setattr(profile, dim, new_val)

        profile.sample_count += 1
        profile.updated_at = datetime.now(timezone.utc).isoformat()

        self._append_feedback(
            VoiceFeedback(
                user_id=user_id,
                persona=persona,
                feedback_type="jariyah",
                delta=_JARIYAH_DELTA,
            )
        )
        self._save_profiles()
        return profile

    # ── Query ────────────────────────────────────────────────────────────────

    def get_modifiers(self, user_id: str, persona: str) -> dict[str, Any]:
        """Modifier dict untuk inject ke response blend / system prompt."""
        profile = self.get_profile(user_id, persona)
        return {
            "warmth": profile.warmth,
            "formality": profile.formality,
            "depth": profile.depth,
            "humor": profile.humor,
            "religiosity": profile.religiosity,
            "nusantara_flavor": profile.nusantara_flavor,
            "sample_count": profile.sample_count,
        }

    def get_voice_hint(self, user_id: str, persona: str) -> str:
        """Generate human-readable voice hint untuk system prompt injection."""
        profile = self.get_profile(user_id, persona)
        hints: list[str] = []

        if profile.warmth > 0.3:
            hints.append("hangat dan ramah")
        elif profile.warmth < -0.3:
            hints.append("tegas dan profesional")

        if profile.formality > 0.3:
            hints.append("formal")
        elif profile.formality < -0.3:
            hints.append("santai dan informal")

        if profile.depth > 0.3:
            hints.append("mendalam dan detail")
        elif profile.depth < -0.3:
            hints.append("ringkas dan to the point")

        if profile.humor > 0.3:
            hints.append("dengan sentuhan humor")

        if profile.religiosity > 0.3:
            hints.append("dengan nuansa religius Islami")

        if profile.nusantara_flavor > 0.3:
            hints.append("dengan sentuhan budaya Nusantara")

        if not hints:
            return ""
        return f"Preferensi user: gunakan tone {' dan '.join(hints)}."

    def reset_profile(self, user_id: str, persona: str) -> None:
        """Reset profile ke default (0)."""
        key = (user_id, persona)
        if key in self._profiles:
            del self._profiles[key]
            self._save_profiles()


# ── Singleton + convenience ──────────────────────────────────────────────────

_store: VoiceCalibrationStore | None = None


def get_voice_store(data_dir: str | None = None) -> VoiceCalibrationStore:
    global _store
    if _store is None:
        _store = VoiceCalibrationStore(data_dir=data_dir)
    return _store


def get_voice_modifiers(user_id: str, persona: str) -> dict[str, Any]:
    return get_voice_store().get_modifiers(user_id, persona)


def get_voice_hint(user_id: str, persona: str) -> str:
    return get_voice_store().get_voice_hint(user_id, persona)


def record_explicit_feedback(user_id: str, persona: str, text: str) -> VoiceProfile:
    return get_voice_store().record_explicit(user_id, persona, text)


def record_thumbs_feedback(user_id: str, persona: str, vote: str) -> VoiceProfile:
    return get_voice_store().record_thumbs(user_id, persona, vote)


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        store = VoiceCalibrationStore(data_dir=tmpdir)

        # Test explicit feedback
        store.record_explicit("user1", "ABOO", "lebih formal dong")
        store.record_explicit("user1", "ABOO", "terlalu panjang")
        store.record_explicit("user1", "ABOO", "lebih hangat")

        profile = store.get_profile("user1", "ABOO")
        print("Profile after explicit:")
        print(f"  formality={profile.formality:.2f} (expected +0.15)")
        print(f"  depth={profile.depth:.2f} (expected -0.15)")
        print(f"  warmth={profile.warmth:.2f} (expected +0.15)")
        print(f"  sample_count={profile.sample_count} (expected 3)")

        # Test thumbs up
        store.record_thumbs("user1", "ABOO", "up")
        profile2 = store.get_profile("user1", "ABOO")
        print(f"\nAfter thumbs up: sample_count={profile2.sample_count} (expected 4)")

        # Test voice hint
        hint = store.get_voice_hint("user1", "ABOO")
        print(f"\nVoice hint: {hint}")

        # Test modifiers
        mods = store.get_modifiers("user1", "ABOO")
        print(f"\nModifiers: {mods}")

        # Test reset
        store.reset_profile("user1", "ABOO")
        profile3 = store.get_profile("user1", "ABOO")
        print(f"\nAfter reset: formality={profile3.formality} (expected 0.0)")

        print("\n[OK] All self-tests passed")
