"""
aesthetic_judgment.py — Aesthetic Judgment for Multimodal Output

Evaluasi harmoni antara visual (gambar) dan tekstual (caption/copy)
sebagai satu kesatuan estetika.

Dimensi:
  1. Visual-Tekstual Alignment — apakah gambar dan teks membicarakan hal yang sama?
  2. Tone Harmony — apakah mood visual (archetype/template) cocok dengan tone caption?
  3. Channel Fit — apakah format visual sesuai dengan channel target?

Pivot 2026-04-25 — Jiwa Sprint Task 5 (Kimi lane)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class AestheticScore:
    overall: float  # 0.0–1.0
    visual_textual_alignment: float
    tone_harmony: float
    channel_fit: float
    feedback: list[str] = field(default_factory=list)
    passes_threshold: bool = False


# ── Scoring rubric ───────────────────────────────────────────────────────────

# Archetype → compatible tones
_ARCHETYPE_TONE_COMPAT = {
    "caregiver": {"warm", "friendly", "gentle", "empathetic"},
    "hero": {"excited", "energetic", "bold", "confident"},
    "sage": {"formal", "scholarly", "neutral", "analytical"},
    "explorer": {"curious", "excited", "friendly", "adventurous"},
    "rebel": {"bold", "excited", "edgy", "provocative"},
    "lover": {"warm", "friendly", "romantic", "gentle"},
    "jester": {"funny", "humorous", "excited", "playful"},
    "ruler": {"formal", "authoritative", "neutral", "professional"},
    "creator": {"creative", "excited", "curious", "friendly"},
    "innocent": {"warm", "gentle", "friendly", "calm"},
    "magician": {"mysterious", "creative", "excited", "curious"},
    "everyman": {"friendly", "neutral", "warm", "casual"},
    # fallback
    "unknown": set(),
    "fallback": set(),
}

# Template → preferred channel
_TEMPLATE_CHANNEL_COMPAT = {
    "ig_feed": {"instagram", "threads"},
    "ig_story": {"instagram", "threads"},
    "yt_thumbnail": {"youtube", "tiktok"},
    "poster_event": {"poster", "instagram"},
    "product_shot": {"instagram", "shopee", "tokopedia", "ecommerce"},
    "food_shot": {"instagram", "threads", "tiktok"},
    "banner_web": {"website", "landing", "blog"},
    "unknown": set(),
    "fallback": set(),
}

# Aspect ratio → channel expectation
_CHANNEL_ASPECT = {
    "instagram": (1.0, 1.0),      # square preferred
    "threads": (1.0, 1.0),
    "youtube": (16.0, 9.0),
    "tiktok": (9.0, 16.0),
    "poster": (3.0, 4.0),
    "website": (16.0, 9.0),
}

# Tone keywords extraction
_TONE_KEYWORDS = {
    "warm", "friendly", "gentle", "empathetic",
    "excited", "energetic", "bold", "confident",
    "formal", "scholarly", "neutral", "analytical",
    "curious", "adventurous", "edgy", "provocative",
    "romantic", "funny", "humorous", "playful",
    "authoritative", "professional", "creative",
    "mysterious", "calm", "casual", "melancholic",
}


# ── Scorer ───────────────────────────────────────────────────────────────────

class AestheticJudgment:
    """Score harmony antara visual dan tekstual output."""

    THRESHOLD = 0.6

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else self.THRESHOLD

    def judge(
        self,
        visual: dict[str, Any],
        text: dict[str, Any],
    ) -> AestheticScore:
        """
        Judge multimodal harmony.

        Args:
            visual: dict dengan keys: prompt, archetype, template, width, height
            text: dict dengan keys: headline, body, tone, channel
        """
        feedback: list[str] = []

        # Dimensi 1: Visual-Tekstual Alignment
        align_score = self._score_alignment(visual, text, feedback)

        # Dimensi 2: Tone Harmony
        tone_score = self._score_tone_harmony(visual, text, feedback)

        # Dimensi 3: Channel Fit
        channel_score = self._score_channel_fit(visual, text, feedback)

        # Overall: weighted average
        overall = round(align_score * 0.4 + tone_score * 0.35 + channel_score * 0.25, 2)
        passes = overall >= self.threshold

        if passes and not feedback:
            feedback.append("Aesthetic harmony passed — visual and text are well-aligned.")

        return AestheticScore(
            overall=overall,
            visual_textual_alignment=align_score,
            tone_harmony=tone_score,
            channel_fit=channel_score,
            feedback=feedback,
            passes_threshold=passes,
        )

    # ── Dimension scorers ──────────────────────────────────────────────────

    def _score_alignment(self, visual: dict, text: dict, feedback: list) -> float:
        """Cek apakah visual prompt dan teks membicarakan hal yang sama."""
        v_prompt = visual.get("prompt", "").lower()
        t_headline = text.get("headline", "").lower()
        t_body = text.get("body", "").lower()

        # Extract keywords (simple word overlap)
        v_words = set(v_prompt.split())
        t_words = set((t_headline + " " + t_body).split())
        # Filter to meaningful words (length > 3)
        v_words = {w for w in v_words if len(w) > 3}
        t_words = {w for w in t_words if len(w) > 3}

        if not v_words or not t_words:
            feedback.append("Warning: cannot extract keywords for alignment check.")
            return 0.5

        overlap = v_words & t_words
        total_unique = v_words | t_words
        if not total_unique:
            return 0.5

        ratio = len(overlap) / len(total_unique)
        score = min(1.0, ratio * 3.0)  # boost because overlap is usually small

        if score < 0.3:
            feedback.append(f"Visual-textual alignment weak ({score:.2f}) — image and text seem unrelated.")
        elif score > 0.7:
            feedback.append(f"Visual-textual alignment strong ({score:.2f}).")

        return round(score, 2)

    def _score_tone_harmony(self, visual: dict, text: dict, feedback: list) -> float:
        """Cek apakah archetype visual cocok dengan tone teks."""
        archetype = visual.get("archetype", "unknown").lower()
        tone = text.get("tone", "neutral").lower()

        # Normalize archetype
        archetype_key = archetype if archetype in _ARCHETYPE_TONE_COMPAT else "unknown"
        compatible_tones = _ARCHETYPE_TONE_COMPAT.get(archetype_key, set())

        if not compatible_tones:
            # Unknown archetype — neutral score
            return 0.5

        if tone in compatible_tones:
            feedback.append(f"Tone harmony good — '{tone}' matches archetype '{archetype}'.")
            return 1.0

        # Partial match: check if any word in tone matches
        tone_words = set(tone.split()) & _TONE_KEYWORDS
        overlap = tone_words & compatible_tones
        if overlap:
            feedback.append(f"Tone harmony partial — '{tone}' partially matches archetype '{archetype}'.")
            return 0.7

        feedback.append(f"Tone harmony weak — '{tone}' clashes with archetype '{archetype}'.")
        return 0.3

    def _score_channel_fit(self, visual: dict, text: dict, feedback: list) -> float:
        """Cek apakah visual format sesuai channel."""
        template = visual.get("template", "unknown").lower()
        channel = text.get("channel", "instagram").lower()
        width = visual.get("width", 1024)
        height = visual.get("height", 1024)

        # Template-channel compatibility
        template_key = template if template in _TEMPLATE_CHANNEL_COMPAT else "unknown"
        compat_channels = _TEMPLATE_CHANNEL_COMPAT.get(template_key, set())

        template_score = 1.0 if channel in compat_channels else 0.5
        if not compat_channels:
            template_score = 0.5

        # Aspect ratio check
        aspect = width / height if height > 0 else 1.0
        expected = _CHANNEL_ASPECT.get(channel)
        if expected:
            expected_aspect = expected[0] / expected[1]
            ratio_diff = abs(aspect - expected_aspect) / expected_aspect
            if ratio_diff < 0.1:
                aspect_score = 1.0
            elif ratio_diff < 0.3:
                aspect_score = 0.7
                feedback.append(f"Aspect ratio close but not ideal for {channel}.")
            else:
                aspect_score = 0.4
                feedback.append(f"Aspect ratio mismatch for {channel} — expected {expected[0]}:{expected[1]}.")
        else:
            aspect_score = 0.5

        return round((template_score * 0.5 + aspect_score * 0.5), 2)


# ── Convenience API ──────────────────────────────────────────────────────────

def judge_multimodal(visual: dict[str, Any], text: dict[str, Any], threshold: float = 0.6) -> dict[str, Any]:
    """One-shot API: visual dict + text dict → score dict."""
    scorer = AestheticJudgment(threshold=threshold)
    result = scorer.judge(visual, text)
    return {
        "overall": result.overall,
        "visual_textual_alignment": result.visual_textual_alignment,
        "tone_harmony": result.tone_harmony,
        "channel_fit": result.channel_fit,
        "feedback": result.feedback,
        "passes_threshold": result.passes_threshold,
        "threshold": threshold,
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Aesthetic Judgment Self-Test ===\n")

    scorer = AestheticJudgment()

    # Test 1: Strong alignment
    result1 = scorer.judge(
        visual={"prompt": "kopi robusta pegunungan", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
        text={"headline": "Kopi Robusta", "body": "Nikmati kopi robusta dari pegunungan.", "tone": "warm", "channel": "instagram"},
    )
    print(f"[1] Strong alignment: overall={result1.overall}, pass={result1.passes_threshold}")
    assert result1.passes_threshold is True
    print("  OK\n")

    # Test 2: Weak alignment (mismatch topic)
    result2 = scorer.judge(
        visual={"prompt": "kopi robusta", "archetype": "hero", "template": "ig_feed", "width": 1024, "height": 1024},
        text={"headline": "Teknologi AI", "body": "AI mengubah dunia.", "tone": "formal", "channel": "instagram"},
    )
    print(f"[2] Weak alignment: overall={result2.overall}, pass={result2.passes_threshold}")
    assert result2.passes_threshold is False
    print("  OK\n")

    # Test 3: Aspect ratio mismatch
    result3 = scorer.judge(
        visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1920, "height": 1080},
        text={"headline": "Kopi", "body": "Kopi enak.", "tone": "warm", "channel": "instagram"},
    )
    print(f"[3] Aspect mismatch: overall={result3.overall}, channel_fit={result3.channel_fit}")
    assert result3.channel_fit < 1.0
    print("  OK\n")

    # Test 4: Convenience API
    d = judge_multimodal(
        visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
        text={"headline": "Kopi", "body": "Enak", "tone": "warm", "channel": "instagram"},
    )
    assert "overall" in d
    assert "passes_threshold" in d
    print(f"[4] Convenience API: overall={d['overall']}")
    print("  OK\n")

    print("[OK] All self-tests passed")
