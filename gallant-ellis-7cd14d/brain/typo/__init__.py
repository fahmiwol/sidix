"""
brain.typo — 4-Layer Typo Resilient Framework untuk SIDIX.

Layer 1 — TextNormalizer     : koreksi typo + ekspansi abbreviasi
Layer 2 — SemanticMatcher    : deteksi intent dari teks normalized
Layer 3 — ConfidenceScorer   : hitung combined confidence → routing action
Layer 4 — ContextResponder   : siapkan prefix/suffix respons yang empatik

Prinsip: pahami input typo-heavy/informal Indonesia tanpa mempermalukan user.
"""

from __future__ import annotations

from brain.typo.confidence_scorer import ConfidenceResult, ConfidenceScorer
from brain.typo.context_responder import ContextResponder, ResponseContext
from brain.typo.normalizer import NormalizationMeta, TextNormalizer
from brain.typo.semantic_matcher import IntentResult, SemanticMatcher

__all__ = [
    "TextNormalizer",
    "NormalizationMeta",
    "SemanticMatcher",
    "IntentResult",
    "ConfidenceScorer",
    "ConfidenceResult",
    "ContextResponder",
    "ResponseContext",
    "process_input",
]

# Singleton instances (lazy-init per module load)
_normalizer: TextNormalizer | None = None
_matcher: SemanticMatcher | None = None
_scorer: ConfidenceScorer | None = None
_responder: ContextResponder | None = None


def _get_pipeline() -> tuple[TextNormalizer, SemanticMatcher, ConfidenceScorer, ContextResponder]:
    global _normalizer, _matcher, _scorer, _responder
    if _normalizer is None:
        _normalizer = TextNormalizer()
    if _matcher is None:
        _matcher = SemanticMatcher()
    if _scorer is None:
        _scorer = ConfidenceScorer()
    if _responder is None:
        _responder = ContextResponder()
    return _normalizer, _matcher, _scorer, _responder


def process_input(raw_text: str) -> dict:
    """
    Full 4-layer pipeline. Entry point utama untuk semua komponen SIDIX.

    Parameters
    ----------
    raw_text : str
        Input mentah dari user (bisa typo-heavy, informal, singkatan).

    Returns
    -------
    dict dengan keys:
        - normalized_text : str
        - action          : str  (respond_directly / respond_with_note / etc.)
        - intent          : str
        - confidence      : float  (combined 0–1)
        - prefix          : str  (siap dipasang sebelum jawaban)
        - suffix          : str
        - corrections     : list[str]
        - abbrev_expanded : list[str]
        - context         : ResponseContext  (object lengkap)
        - norm_meta       : NormalizationMeta
        - intent_result   : IntentResult
        - confidence_result : ConfidenceResult
    """
    normalizer, matcher, scorer, responder = _get_pipeline()

    # Layer 1
    normalized_text, norm_meta = normalizer.normalize(raw_text)

    # Layer 2
    intent_result = matcher.match_intent(normalized_text)

    # Layer 3
    confidence_result = scorer.score(norm_meta, intent_result)

    # Layer 4
    context = responder.prepare_context(
        confidence_result,
        normalized_text,
        norm_meta.corrections_made,
    )

    return {
        "normalized_text": normalized_text,
        "action": confidence_result.action,
        "intent": intent_result.intent,
        "confidence": confidence_result.combined_score,
        "prefix": context.prefix,
        "suffix": context.suffix,
        "corrections": norm_meta.corrections_made,
        "abbrev_expanded": norm_meta.abbrev_expanded,
        "context": context,
        "norm_meta": norm_meta,
        "intent_result": intent_result,
        "confidence_result": confidence_result,
    }
