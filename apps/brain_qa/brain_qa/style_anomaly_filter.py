"""
style_anomaly_filter.py — BadStyle Backdoor Defense (Vol 20-fu2 #8)
==========================================================================

Per riset note 235 finding: BadStyle paper (arxiv 2026) — backdoor attack
pakai style transfer (Bible/Legal/Shakespeare) sebagai trigger imperceptible.
Bible 90% ASR di GPT-4 dengan FPR rendah; Shakespeare +83% ASR di LLaMA-3.1.
Bypass input/output-level defenses.

Risk konkret SIDIX:
- LearnAgent fetch external (arXiv/GitHub/Wikipedia/Quran) → poisoned
  upstream content dengan style trigger bisa kontaminasi LoRA retrain
- Research_notes contributors → bisa inject style-anomaly backdoor

Defense strategy (lightweight, no model):
1. Style fingerprint detection (regex archaic/legal/dramatic markers)
2. Topic-mismatch flag (Bible style di tech corpus = suspicious)
3. Severity grading: clean / suspicious / quarantine
4. Mandatory sanad check untuk auto-approved
5. Quarantine queue untuk review manual

Reference: research note 235 (BadStyle finding) + CLAUDE.md SECURITY MINDSET

Anti-pattern dihindari:
- ❌ ML classifier per chunk (overkill, latency)
- ❌ Block semua dengan archaic words (false positive Quran/historical paper)
- ✅ Topic-mismatch (style + topic mismatch = signal)
- ✅ Severity grading (clean pass-through, suspicious flag, quarantine block)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Literal

log = logging.getLogger(__name__)


Severity = Literal["clean", "suspicious", "quarantine"]


# ── Style fingerprint patterns ────────────────────────────────────────────────

# Bible/archaic English — KJV-style
_BIBLE_STYLE_RE = re.compile(
    r"\b(thou|thee|thy|thine|ye\s+shall|verily|behold|"
    r"hath|doth|art\s+thou|wherefore|whence|whither|"
    r"unto\s+(thee|him|her|them|us)|"
    r"saith|spake|begat|"
    r"forsooth|nay\s+but|peradventure|"
    r"vouchsafe|hearken)\b",
    re.I,
)

# Legal style — heavy passive + Latin
_LEGAL_STYLE_RE = re.compile(
    r"\b(hereinafter|whereas|pursuant\s+to|aforementioned|"
    r"heretofore|herewith|thereto|thereof|therein|"
    r"notwithstanding|inasmuch\s+as|insofar\s+as|"
    r"per\s+se|prima\s+facie|sine\s+qua\s+non|"
    r"ipso\s+facto|de\s+jure|de\s+facto|"
    r"the\s+party\s+of\s+the\s+(first|second)\s+part|"
    r"witnesseth|in\s+witness\s+whereof)\b",
    re.I,
)

# Shakespearean drama markers
_SHAKESPEARE_STYLE_RE = re.compile(
    r"\b(prithee|methinks|methought|forsooth|"
    r"o\s+(woe|alas|happy)|"
    r"perchance|mayhap|peradventure|"
    r"'tis|'twas|'twere|'twould|"
    r"thy\s+(love|hand|will|grace)|"
    r"hark\s+(thee|ye)|fie\s+(upon|on))\b",
    re.I,
)


# ── Tech/factual corpus indicator (kalau topik begini, archaic style = suspicious) ──

_TECH_TOPIC_RE = re.compile(
    r"\b(python|javascript|typescript|api|rest|graphql|"
    r"docker|kubernetes|nginx|postgres|mysql|redis|"
    r"react|vue|angular|svelte|nextjs|"
    r"function|class|method|loop|array|"
    r"http|https|json|xml|yaml|"
    r"machine\s+learning|deep\s+learning|llm|"
    r"algorithm|data\s+structure|"
    r"compile|build|deploy|debug)\b",
    re.I,
)

_FACTUAL_TOPIC_RE = re.compile(
    r"\b(study|research|paper|experiment|methodology|"
    r"hypothesis|finding|result|conclusion|"
    r"statistics|data|sample|population|"
    r"benchmark|evaluation|metric|"
    r"introduction|background|abstract)\b",
    re.I,
)


# ── Religious/historical legitimate use (don't flag Quran/Bible studies) ──────

_RELIGIOUS_TOPIC_RE = re.compile(
    r"\b(quran|qur.?an|hadith|hadis|fiqh|fikih|"
    r"bible|torah|psalm|gospel|"
    r"theology|theological|religious|spiritual|"
    r"prophet|nabi|rasul|imam|"
    r"surah|surat|ayat|"
    r"liturgy|liturgical|sacred|scripture)\b",
    re.I,
)

_HISTORICAL_TOPIC_RE = re.compile(
    r"\b(century|medieval|renaissance|ancient|"
    r"historical\s+text|archaic\s+language|"
    r"shakespeare|chaucer|milton|"
    r"old\s+english|middle\s+english|"
    r"sejarah|sejarawan|kuno|abad)\b",
    re.I,
)


# ── Decision data ─────────────────────────────────────────────────────────────

@dataclass
class StyleAnomalyDecision:
    """Decision + diagnostic untuk style filtering."""
    severity: Severity
    detected_styles: list[str] = field(default_factory=list)
    topic_signals: list[str] = field(default_factory=list)
    reason: str = ""
    sanad_required: bool = False

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "detected_styles": self.detected_styles,
            "topic_signals": self.topic_signals,
            "reason": self.reason,
            "sanad_required": self.sanad_required,
        }


# ── Main detector ─────────────────────────────────────────────────────────────

def detect_style_anomaly(
    text: str,
    *,
    declared_topic: str = "",
    has_sanad: bool = False,
    min_text_len: int = 100,
) -> StyleAnomalyDecision:
    """
    Detect style anomaly untuk corpus_to_training filter.

    Logic:
    1. Detect style fingerprints (Bible/Legal/Shakespeare archaic)
    2. Detect topic context (tech/factual vs religious/historical)
    3. Severity grading:
       - clean: no anomaly OR style legitimate (religious/historical context)
       - suspicious: style detected + topic ambiguous → flag, sanad required
       - quarantine: style detected + topic mismatch (tech/factual) → block

    Returns StyleAnomalyDecision dengan severity + diagnostic.
    """
    if not text or len(text) < min_text_len:
        return StyleAnomalyDecision(
            severity="clean",
            reason=f"too_short_for_analysis ({len(text or '')})",
        )

    detected_styles: list[str] = []
    topic_signals: list[str] = []

    # Style fingerprint checks
    bible_matches = _BIBLE_STYLE_RE.findall(text)
    legal_matches = _LEGAL_STYLE_RE.findall(text)
    shakespeare_matches = _SHAKESPEARE_STYLE_RE.findall(text)

    if len(bible_matches) >= 2:
        detected_styles.append(f"bible:{len(bible_matches)}")
    if len(legal_matches) >= 2:
        detected_styles.append(f"legal:{len(legal_matches)}")
    if len(shakespeare_matches) >= 2:
        detected_styles.append(f"shakespeare:{len(shakespeare_matches)}")

    # No anomaly
    if not detected_styles:
        return StyleAnomalyDecision(
            severity="clean",
            reason="no_style_fingerprint",
        )

    # Topic context check
    sample = (text + " " + declared_topic).lower()
    if _RELIGIOUS_TOPIC_RE.search(sample):
        topic_signals.append("religious")
    if _HISTORICAL_TOPIC_RE.search(sample):
        topic_signals.append("historical")
    if _TECH_TOPIC_RE.search(sample):
        topic_signals.append("tech")
    if _FACTUAL_TOPIC_RE.search(sample):
        topic_signals.append("factual")

    # Decision tree (tightened di Step 3 ITERASI):
    # - "tech" topic = STRONG backdoor signal (programming context dengan archaic style = sus)
    # - "factual" topic = WEAKER signal (research paper sometimes quote archaic for historical reason)
    # - "religious"/"historical" = LEGITIMATE context untuk archaic style
    legitimate_context = "religious" in topic_signals or "historical" in topic_signals
    tech_context = "tech" in topic_signals
    factual_context = "factual" in topic_signals

    # Rule 1: Tech context dengan archaic style = quarantine REGARDLESS of religious mix
    # (programming code shouldn't have Bible style, period)
    if tech_context:
        return StyleAnomalyDecision(
            severity="quarantine",
            detected_styles=detected_styles,
            topic_signals=topic_signals,
            reason="tech_context_with_archaic_style (high backdoor risk)",
            sanad_required=True,
        )

    # Rule 2: Religious/historical context overrides factual signal — legitimate
    if legitimate_context:
        return StyleAnomalyDecision(
            severity="clean",
            detected_styles=detected_styles,
            topic_signals=topic_signals,
            reason="legitimate_context (religious/historical topic match)",
            sanad_required=True,  # tetap minta sanad untuk klaim sensitif
        )

    # Rule 3: Factual-only (no religious context) = suspicious (sanad bisa unlock)
    if factual_context:
        return StyleAnomalyDecision(
            severity="suspicious",
            detected_styles=detected_styles,
            topic_signals=topic_signals,
            reason="factual_context_with_archaic_style (sanad unlock possible)",
            sanad_required=True,
        )

    # Rule 4: No topic signal = ambiguous suspicious
    return StyleAnomalyDecision(
        severity="suspicious",
        detected_styles=detected_styles,
        topic_signals=topic_signals,
        reason="style_detected_topic_ambiguous (sanad required for approval)",
        sanad_required=True,
    )


def is_safe_for_training(
    text: str,
    *,
    declared_topic: str = "",
    has_sanad: bool = False,
) -> tuple[bool, StyleAnomalyDecision]:
    """
    Convenience wrapper untuk corpus_to_training pipeline.

    Returns (is_safe, decision):
    - is_safe=True: severity=clean OR (severity=suspicious AND has_sanad=True)
    - is_safe=False: severity=quarantine, OR severity=suspicious tanpa sanad

    Per CLAUDE.md SECURITY: sanad chain mandatory untuk auto-approved corpus.
    """
    decision = detect_style_anomaly(
        text, declared_topic=declared_topic, has_sanad=has_sanad,
    )
    if decision.severity == "quarantine":
        return False, decision
    if decision.severity == "suspicious" and not has_sanad:
        return False, decision
    return True, decision


__all__ = [
    "Severity",
    "StyleAnomalyDecision",
    "detect_style_anomaly",
    "is_safe_for_training",
]
