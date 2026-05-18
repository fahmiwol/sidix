"""
Multilingual typo-resilience pipeline — local heuristics only.

Stages: unicode normalize → script hint → light word-level substitutions → trim.
No external API required.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_ARABIC_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
_LATINISH = re.compile(r"[A-Za-z\u00C0-\u024F]")

# Expand via brain/typo/locales/*.json in a follow-up sprint
_SUBS_COMMON: dict[str, str] = {
    "teh": "the",
    "adn": "and",
    "waht": "what",
    "yuo": "you",
    "yg": "yang",
    "klo": "kalau",
    "gak": "tidak",
    "ga": "tidak",
    "dgn": "dengan",
    "utk": "untuk",
}


@dataclass
class TypoPipelineResult:
    original: str
    normalized: str
    script_hint: str
    substitutions_applied: int


def _script_hint(text: str) -> str:
    if not text.strip():
        return "empty"
    arab = len(_ARABIC_RANGE.findall(text))
    lat = len(_LATINISH.findall(text))
    if arab and lat:
        return "mixed_arab_latin"
    if arab:
        return "arabic"
    return "latin"


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _sub_word(match: re.Match[str]) -> str:
    w = match.group(0)
    low = w.lower()
    return _SUBS_COMMON.get(low, w)


def _light_substitutions(text: str) -> tuple[str, int]:
    before = text
    after = re.sub(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", _sub_word, text)
    return after, 1 if before != after else 0


def normalize_query(text: str) -> TypoPipelineResult:
    """Run MVP pipeline on a single user query string."""
    original = text or ""
    step1 = _normalize_unicode(original)
    step2, n_sub = _light_substitutions(step1)
    hint = _script_hint(step2)
    step3 = re.sub(r"\s+", " ", step2).strip()
    return TypoPipelineResult(
        original=original,
        normalized=step3,
        script_hint=hint,
        substitutions_applied=n_sub,
    )
