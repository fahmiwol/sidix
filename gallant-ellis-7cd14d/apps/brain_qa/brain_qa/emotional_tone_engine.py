"""
emotional_tone_engine.py — Emotional Tone Engine

Deteksi emosi user dari teks + adaptasi tone respons.

Konsep:
- Rule-based detection (ID + EN) — no model inference needed
- 3 dimensi: valence (positive/negative/neutral), arousal (calm/moderate/excited)
- 8 emosi spesifik: angry, frustrated, sad, anxious, excited, grateful, curious, confused
- Adaptasi: emotion → tone hint untuk inject ke system prompt / response blend

Pivot 2026-04-25 — Jiwa Sprint Phase 2 (Kimi lane)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


# ── Enums ────────────────────────────────────────────────────────────────────

class Valence(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Arousal(str, Enum):
    CALM = "calm"
    MODERATE = "moderate"
    EXCITED = "excited"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class EmotionalState:
    """Hasil deteksi emosi dari satu teks user."""

    valence: Valence
    arousal: Arousal
    dominant_emotion: str  # angry | frustrated | sad | anxious | excited | grateful | curious | confused | neutral
    confidence: float  # 0.0–1.0
    matched_keywords: list[str]


@dataclass
class ToneAdaptation:
    """Rekomendasi tone untuk respons."""

    tone_hint: str  # human-readable hint untuk system prompt
    style_modifier: dict[str, Any]  # structured modifier
    priority: str  # high | medium | low — seberapa kuat adaptasi perlu diterapkan


# ── Emotion detection patterns ───────────────────────────────────────────────

# Format: (emotion, valence, arousal, [patterns])
_EMOTION_PATTERNS: list[tuple[str, Valence, Arousal, list[str]]] = [
    # Negative high arousal
    (
        "angry",
        Valence.NEGATIVE,
        Arousal.EXCITED,
        [
            r"\b(marah|kesel|bete|naik\s+darah|emosi|murka|dendam|benci\s+begini)\b",
            r"\b(angry|pissed|furious|mad\s+at|raging|hate\s+this)\b",
            r"\b(dasar\s+lu|brengsek|tolol|bodoh|goblok|anjing|babi)\b",
        ],
    ),
    (
        "frustrated",
        Valence.NEGATIVE,
        Arousal.MODERATE,
        [
            r"\b(frustasi|stuck|buntu|gak\s+bisa-bisa|muter-muter|nyerah|serah|pusing)\b",
            r"\b(frustrated|stuck|blocked|giving\s+up|can't\s+figure|wasting\s+time)\b",
            r"\b(ribet|rumit|terlalu\s+susah|kenapa\s+gampang|gak\s+nyangka\s+susah)\b",
        ],
    ),
    # Negative low arousal
    (
        "sad",
        Valence.NEGATIVE,
        Arousal.CALM,
        [
            r"\b(sedih|kecewa|putus\s+asa|hancur|nangis|merasa\s+sendiri|kosong)\b",
            r"\b(sad|disappointed|heartbroken|empty|lonely|depressed|giving\s+up)\b",
            r"\b(gak\s+semangat|hilang\s+harapan|gak\s+ada\s+arti)\b",
        ],
    ),
    (
        "anxious",
        Valence.NEGATIVE,
        Arousal.MODERATE,
        [
            r"\b(cemas|khawatir|takut|gelisah|panik|overthinking|stress)\b",
            r"\b(anxious|worried|scared|nervous|panicking|overwhelmed|stressed)\b",
            r"\b(gimana\s+ya\s+kalau|takut\s+salah|apa\s+yang\s+terjadi)\b",
        ],
    ),
    # Positive high arousal
    (
        "excited",
        Valence.POSITIVE,
        Arousal.EXCITED,
        [
            r"\b(semangat|heboh|gak\s+sabar|mantap|keren\s+banget|wow|asyik)\b",
            r"\b(excited|can't\s+wait|awesome|amazing|pumped|thrilled|yay)\b",
            r"\b(akhirnya|yes|berhasil|yay|woohoo)\b",
        ],
    ),
    # Positive moderate arousal
    (
        "grateful",
        Valence.POSITIVE,
        Arousal.MODERATE,
        [
            r"\b(alhamdulillah|syukur|terima\s+kasih\s+banyak|berkah|jazakallah)\b",
            r"\b(grateful|thankful|blessed|appreciate\s+it|thanks\s+a\s+lot)\b",
            r"\b(makasih\s+banyak|thanks|terima\s+kasih)\b",
        ],
    ),
    (
        "curious",
        Valence.POSITIVE,
        Arousal.MODERATE,
        [
            r"\b(penasaran|mau\s+tahu|gimana\s+ya|kok\s+bisa|seru\s+juga|menarik)\b",
            r"\b(curious|wondering|how\s+does|why\s+is|interesting|fascinating)\b",
            r"\b(bisa\s+jelasin|gimana\s+caranya|kenapa\s+ya)\b",
        ],
    ),
    # Neutral / cognitive
    (
        "confused",
        Valence.NEUTRAL,
        Arousal.MODERATE,
        [
            r"\b(bingung|gak\s+ngerti|pusing|terlalu\s+ribet|apa\s+maksudnya)\b",
            r"\b(confused|don't\s+understand|lost|what\s+do\s+you\s+mean|huh\?)\b",
            r"\b(gak\s+paham|maksudnya\s+apa|kurang\s+jelas)\b",
        ],
    ),
]

# Intensifier words increase confidence
_INTENSIFIERS = [
    r"\b(sangat|banget|sekali|amat|terlalu|super|really|very|so|extremely)\b"
]


# ── Detection ────────────────────────────────────────────────────────────────

def detect_emotion(text: str) -> EmotionalState:
    """
    Deteksi emosi dominan dari teks user.

    Returns EmotionalState dengan valence, arousal, dominant_emotion, confidence.
    """
    if not text or not text.strip():
        return EmotionalState(
            valence=Valence.NEUTRAL,
            arousal=Arousal.CALM,
            dominant_emotion="neutral",
            confidence=0.0,
            matched_keywords=[],
        )

    text_lower = text.lower()
    scores: dict[str, tuple[int, list[str], Valence, Arousal]] = {}

    for emotion, valence, arousal, patterns in _EMOTION_PATTERNS:
        matched: list[str] = []
        for pattern in patterns:
            for m in re.finditer(pattern, text_lower):
                matched.append(m.group(0))
        if matched:
            scores[emotion] = (len(matched), matched, valence, arousal)

    # Check intensifiers
    intensifier_count = sum(
        1 for pat in _INTENSIFIERS for _ in re.finditer(pat, text_lower)
    )

    if not scores:
        return EmotionalState(
            valence=Valence.NEUTRAL,
            arousal=Arousal.CALM,
            dominant_emotion="neutral",
            confidence=0.0,
            matched_keywords=[],
        )

    # Pick dominant emotion by match count
    dominant = max(scores, key=lambda e: scores[e][0])
    count, matched, valence, arousal = scores[dominant]

    # Confidence: base on match count + intensifier boost, capped at 1.0
    base_conf = min(0.9, 0.3 + (count - 1) * 0.2)
    conf = min(1.0, base_conf + intensifier_count * 0.1)

    return EmotionalState(
        valence=valence,
        arousal=arousal,
        dominant_emotion=dominant,
        confidence=round(conf, 2),
        matched_keywords=matched,
    )


# ── Adaptation ───────────────────────────────────────────────────────────────

_TONE_ADAPTATIONS: dict[str, ToneAdaptation] = {
    "angry": ToneAdaptation(
        tone_hint="User sedang marah. Respon dengan tenang, singkat, dan fokus solusi. Jangan defensive.",
        style_modifier={"formality": +0.2, "depth": -0.3, "warmth": +0.1},
        priority="high",
    ),
    "frustrated": ToneAdaptation(
        tone_hint="User frustrasi. Respon dengan empati, akui kesulitan, berikan langkah konkret.",
        style_modifier={"formality": +0.1, "depth": +0.1, "warmth": +0.2},
        priority="high",
    ),
    "sad": ToneAdaptation(
        tone_hint="User sedih. Respon dengan hangat, supportive, dan lembut. Hindari tone yang terlalu enerjik.",
        style_modifier={"warmth": +0.4, "humor": -0.2, "formality": -0.1},
        priority="high",
    ),
    "anxious": ToneAdaptation(
        tone_hint="User cemas. Respon dengan meyakinkan, terstruktur, step-by-step. Hindari informasi yang overwhelming.",
        style_modifier={"depth": -0.1, "formality": +0.1, "warmth": +0.2},
        priority="high",
    ),
    "excited": ToneAdaptation(
        tone_hint="User excited. Respon dengan energik, elaboratif, dan cocokkan enthusiasm-nya.",
        style_modifier={"warmth": +0.2, "humor": +0.1, "depth": +0.1},
        priority="medium",
    ),
    "grateful": ToneAdaptation(
        tone_hint="User bersyukur. Respon dengan humble, menerima, dan tawarkan value tambah.",
        style_modifier={"warmth": +0.2, "formality": -0.1, "humor": 0.0},
        priority="low",
    ),
    "curious": ToneAdaptation(
        tone_hint="User penasaran. Respon exploratory, informatif, dan encouraging.",
        style_modifier={"depth": +0.2, "warmth": +0.1, "humor": 0.0},
        priority="medium",
    ),
    "confused": ToneAdaptation(
        tone_hint="User bingung. Respon dengan sabar, bahasa sederhana, dan cek pemahaman.",
        style_modifier={"depth": -0.2, "formality": -0.1, "warmth": +0.2},
        priority="high",
    ),
    "neutral": ToneAdaptation(
        tone_hint="",
        style_modifier={},
        priority="low",
    ),
}


def adapt_tone(emotion: EmotionalState) -> ToneAdaptation:
    """Dapatkan rekomendasi tone adaptation berdasarkan emotional state."""
    return _TONE_ADAPTATIONS.get(emotion.dominant_emotion, _TONE_ADAPTATIONS["neutral"])


def get_emotion_context(text: str) -> dict[str, Any]:
    """One-shot: detect + adapt → structured dict untuk inject ke session."""
    state = detect_emotion(text)
    adaptation = adapt_tone(state)
    return {
        "emotional_state": {
            "valence": state.valence.value,
            "arousal": state.arousal.value,
            "dominant_emotion": state.dominant_emotion,
            "confidence": state.confidence,
            "matched_keywords": state.matched_keywords,
        },
        "tone_adaptation": {
            "tone_hint": adaptation.tone_hint,
            "style_modifier": adaptation.style_modifier,
            "priority": adaptation.priority,
        },
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        ("aku sangat marah dengan jawaban ini", "angry"),
        ("gue stuck nih, frustasi banget", "frustrated"),
        ("sedih rasanya gagal terus", "sad"),
        ("aku cemas nih takut salah", "anxious"),
        ("wow keren banget, gak sabar coba!", "excited"),
        ("alhamdulillah, terima kasih banyak ya", "grateful"),
        ("penasaran gimana caranya", "curious"),
        ("aku bingung nih, gak ngerti", "confused"),
        ("jelaskan cara kerja docker", "neutral"),
        ("", "neutral"),
    ]

    print("=== Emotional Tone Engine Self-Test ===\n")
    all_ok = True
    for text, expected in test_cases:
        state = detect_emotion(text)
        ok = state.dominant_emotion == expected
        all_ok = all_ok and ok
        mark = "OK" if ok else "FAIL"
        print(f"[{mark}] {text!r:50} -> {state.dominant_emotion} (expected {expected})")
        if state.matched_keywords:
            print(f"       keywords: {state.matched_keywords}")
        print(f"       valence={state.valence.value} arousal={state.arousal.value} conf={state.confidence}")
        if not ok:
            print(f"       adaptation: {adapt_tone(state).tone_hint[:60]}...")
        print()

    print("=" * 50)
    print("[OK] All self-tests passed" if all_ok else "[FAIL] Some tests failed")
