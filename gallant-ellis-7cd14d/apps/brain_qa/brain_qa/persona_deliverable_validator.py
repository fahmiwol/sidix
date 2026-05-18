"""
persona_deliverable_validator.py — Sprint Creative 90%→100%

Inline validator untuk 5 persona output sesuai deliverable format yang
locked di cot_system_prompts.py (Sigma-3D + research note 309 adoption).

Pattern check:
- UTZ: METAFORA VISUAL + KEJUTAN SEMANTIK + MIN 3 ALT (≥3 alternatives)
- ABOO: kode block + Big-O + edge cases checklist
- OOMAR: framework named + tradeoff + KPI + timeline
- ALEY: ≥3 sumber + counterargument + epistemic confidence tag
- AYMAN: empathic mirror + analogi + actionable next

Returns DeliverableScore (compliant/non-compliant + flags + score).

Pakai untuk:
- Runtime quality gate post-synthesis
- Persona drift detection
- Continual training data filter (Tumbuh integration)

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DeliverableScore:
    persona: str
    compliant: bool
    score: float  # 0.0 - 1.0
    rules_passed: list[str]
    rules_failed: list[str]


# Generic pattern detectors
_CODE_BLOCK_RE = re.compile(r"```[\w]*\n.*?\n```", re.DOTALL)
_BIG_O_RE = re.compile(r"\bO\([^)]+\)|big.?o|complexity|kompleksitas", re.IGNORECASE)
_LIST_3PLUS_RE = re.compile(r"(?:^[\d\-\*•]\s.*\n){3,}|(?:\b\d+\.\s.*\n){3,}", re.MULTILINE)
_FRAMEWORK_NAMES = ("swot", "porter", "lean canvas", "jtbd", "okr", "5 forces", "mvp", "moat", "tam")
_TIMELINE_RE = re.compile(r"\b(7\s*hari|30\s*hari|90\s*hari|q[1-4]|kuartal|7-30-90|day\s*\d+)\b", re.IGNORECASE)
_CITATION_RE = re.compile(r"\(\d{4}\)|\[\d+\]|et\s*al\.?|menurut\s+\w+|berdasarkan\s+\w+", re.IGNORECASE)
_CONFIDENCE_TAG_RE = re.compile(r"\[(TINGGI|SEDANG|RENDAH|HIGH|MEDIUM|LOW)\s*confidence\]|confidence:\s*(tinggi|sedang|rendah)", re.IGNORECASE)
_ANALOGY_RE = re.compile(r"\b(seperti|kayak|ibarat|mirip|analoginya)\b", re.IGNORECASE)
_EMPATHIC_RE = re.compile(r"\b(wajar|saya paham|mengerti|stuck|capek|frustasi|bingung)\b", re.IGNORECASE)
_ACTIONABLE_RE = re.compile(r"\b(coba|bisa\s+kamu|langkah|step|next:?|action:?|berikutnya)\b", re.IGNORECASE)


def _has_alternatives_3plus(text: str) -> bool:
    """Check ≥3 numbered/bulleted alternatives."""
    # Count numbered "1.", "2.", "3." pattern
    numbered = re.findall(r"^\s*\d+\.\s", text, re.MULTILINE)
    bulleted = re.findall(r"^\s*[\-\*•]\s", text, re.MULTILINE)
    return len(numbered) >= 3 or len(bulleted) >= 3


def _has_metafora_visual(text: str) -> bool:
    """Check for visual/sensorik metaphor language."""
    # Keywords that suggest visual/sensorik metaphor
    visual_kw = ("warna", "cahaya", "bentuk", "tekstur", "rasa", "bunyi", "seperti", "ibarat")
    text_lower = text.lower()
    return sum(1 for kw in visual_kw if kw in text_lower) >= 2


def _has_kejutan_semantik(text: str) -> bool:
    """Heuristic for unexpected/creative word combinations."""
    # Look for unusual juxtapositions (rough heuristic)
    return any(phrase in text.lower() for phrase in ("yang ngomong kayak", "skip iklan", "perfect-fit", "tabrak konteks", "tak-expected"))


def validate_utz(text: str) -> DeliverableScore:
    rules = {
        "min_3_alternatives": _has_alternatives_3plus(text),
        "metafora_visual": _has_metafora_visual(text),
        "kejutan_semantik": _has_kejutan_semantik(text),
        "min_length": len(text) > 200,
    }
    passed = [k for k, v in rules.items() if v]
    failed = [k for k, v in rules.items() if not v]
    score = len(passed) / len(rules)
    return DeliverableScore(persona="UTZ", compliant=score >= 0.5, score=score,
                            rules_passed=passed, rules_failed=failed)


def validate_aboo(text: str) -> DeliverableScore:
    rules = {
        "code_block": bool(_CODE_BLOCK_RE.search(text)),
        "complexity_explicit": bool(_BIG_O_RE.search(text)),
        "list_or_checklist": _has_alternatives_3plus(text) or "edge case" in text.lower(),
        "min_length": len(text) > 150,
    }
    passed = [k for k, v in rules.items() if v]
    failed = [k for k, v in rules.items() if not v]
    score = len(passed) / len(rules)
    return DeliverableScore(persona="ABOO", compliant=score >= 0.5, score=score,
                            rules_passed=passed, rules_failed=failed)


def validate_oomar(text: str) -> DeliverableScore:
    text_lower = text.lower()
    rules = {
        "framework_named": any(fw in text_lower for fw in _FRAMEWORK_NAMES),
        "tradeoff_or_alternative": "trade" in text_lower or "alternatif" in text_lower or "namun" in text_lower,
        "kpi_or_metric": "kpi" in text_lower or "metric" in text_lower or "metrik" in text_lower or "%" in text,
        "timeline": bool(_TIMELINE_RE.search(text)),
    }
    passed = [k for k, v in rules.items() if v]
    failed = [k for k, v in rules.items() if not v]
    score = len(passed) / len(rules)
    return DeliverableScore(persona="OOMAR", compliant=score >= 0.5, score=score,
                            rules_passed=passed, rules_failed=failed)


def validate_aley(text: str) -> DeliverableScore:
    citations = len(_CITATION_RE.findall(text))
    rules = {
        "min_3_sources": citations >= 3,
        "confidence_tag": bool(_CONFIDENCE_TAG_RE.search(text)),
        "counterargument": any(kw in text.lower() for kw in ("namun", "tapi", "counterargument", "sisi lain", "argumen lawan")),
        "min_length": len(text) > 200,
    }
    passed = [k for k, v in rules.items() if v]
    failed = [k for k, v in rules.items() if not v]
    score = len(passed) / len(rules)
    return DeliverableScore(persona="ALEY", compliant=score >= 0.5, score=score,
                            rules_passed=passed, rules_failed=failed)


def validate_ayman(text: str) -> DeliverableScore:
    rules = {
        "empathic_mirror": bool(_EMPATHIC_RE.search(text)),
        "analogy": bool(_ANALOGY_RE.search(text)),
        "actionable_next": bool(_ACTIONABLE_RE.search(text)),
        "warm_tone": "kita" in text.lower() or "aku" in text.lower(),
    }
    passed = [k for k, v in rules.items() if v]
    failed = [k for k, v in rules.items() if not v]
    score = len(passed) / len(rules)
    return DeliverableScore(persona="AYMAN", compliant=score >= 0.5, score=score,
                            rules_passed=passed, rules_failed=failed)


_VALIDATOR_MAP = {
    "UTZ": validate_utz,
    "ABOO": validate_aboo,
    "OOMAR": validate_oomar,
    "ALEY": validate_aley,
    "AYMAN": validate_ayman,
}


def validate_persona_output(persona: str, text: str) -> DeliverableScore:
    """Public entry point — validate text dari persona spesifik."""
    persona = (persona or "").upper()
    validator = _VALIDATOR_MAP.get(persona)
    if not validator:
        return DeliverableScore(persona=persona, compliant=False, score=0.0,
                                rules_passed=[], rules_failed=["unknown_persona"])
    return validator(text or "")


__all__ = [
    "DeliverableScore",
    "validate_persona_output",
    "validate_utz",
    "validate_aboo",
    "validate_oomar",
    "validate_aley",
    "validate_ayman",
]
