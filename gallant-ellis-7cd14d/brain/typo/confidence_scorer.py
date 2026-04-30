"""
Layer 3: Confidence Scorer
Combine normalization confidence (40%) + intent confidence (60%) → routing decision.
Output: action tier yang menentukan cara SIDIX merespons.
"""

from __future__ import annotations

from dataclasses import dataclass

from brain.typo.normalizer import NormalizationMeta
from brain.typo.semantic_matcher import IntentResult


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WEIGHT_NORM = 0.40
WEIGHT_INTENT = 0.60

# Threshold tiers
TIER_DIRECT = 0.85        # respond langsung tanpa mention koreksi
TIER_NOTE = 0.60          # respond + subtle note tentang interpretasi
TIER_DISCLAIMER = 0.40    # respond + disclaimer eksplisit
# < TIER_DISCLAIMER       # minta klarifikasi (gentle, tidak mempermalukan)


# ---------------------------------------------------------------------------
# Message templates per tier
# ---------------------------------------------------------------------------
MESSAGE_TEMPLATES: dict[str, str] = {
    "respond_directly": "",  # kosong — SIDIX jawab langsung
    "respond_with_note": (
        "Saya pahami kamu bertanya tentang {topic}. Berikut jawabannya:"
    ),
    "respond_with_disclaimer": (
        "Kalau saya tidak salah tangkap, kamu menanyakan tentang {topic}. "
        "Tolong koreksi kalau saya keliru ya."
    ),
    "ask_clarification": (
        "Bisa diperjelas sedikit? Saya ingin memastikan saya membantu dengan tepat 😊 "
        "Apa yang kamu maksud dengan pertanyaan ini?"
    ),
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class ConfidenceResult:
    combined_score: float
    action: str
    norm_confidence: float
    intent_confidence: float
    message_template: str
    intent: str = ""
    norm_corrections: int = 0


# ---------------------------------------------------------------------------
# ConfidenceScorer
# ---------------------------------------------------------------------------
class ConfidenceScorer:
    """
    Layer 3 — scoring dan routing.
    Formula: combined = 0.4 * norm_confidence + 0.6 * intent_confidence
    """

    def score(
        self,
        norm_meta: NormalizationMeta,
        intent_result: IntentResult,
    ) -> ConfidenceResult:
        """
        Hitung combined score dan tentukan action tier.

        Returns
        -------
        ConfidenceResult
            combined_score, action, dan template pesan yang sesuai.
        """
        norm_conf = norm_meta.confidence
        intent_conf = intent_result.confidence

        combined = WEIGHT_NORM * norm_conf + WEIGHT_INTENT * intent_conf
        combined = round(combined, 4)

        action = self._determine_action(combined)
        template = MESSAGE_TEMPLATES[action]

        return ConfidenceResult(
            combined_score=combined,
            action=action,
            norm_confidence=norm_conf,
            intent_confidence=intent_conf,
            message_template=template,
            intent=intent_result.intent,
            norm_corrections=len(norm_meta.corrections_made),
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------
    @staticmethod
    def _determine_action(score: float) -> str:
        """Map score ke action tier."""
        if score >= TIER_DIRECT:
            return "respond_directly"
        elif score >= TIER_NOTE:
            return "respond_with_note"
        elif score >= TIER_DISCLAIMER:
            return "respond_with_disclaimer"
        else:
            return "ask_clarification"
