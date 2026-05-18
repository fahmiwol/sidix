"""
cot_extractor.py — Extract and Validate CoT Output from LLM Responses

Tanggung jawab:
  - Parse <REASONING> dan <ANSWER> blocks dari raw LLM output
  - Extract epistemik labels [FACT], [OPINION], [SPECULATION], [UNKNOWN]
  - Score reasoning quality (weak/adequate/strong)
  - Compute confidence score (0.0-1.0)
  - Validate CoT structure
  - Return CoTOutput dataclass dengan metrics lengkap

Pattern:
  - Regex untuk block extraction
  - Multiline handling
  - Fallback: empty string bukan error
  - Safe parsing (tidak crash pada input invalid)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

REASONING_BLOCK_PATTERN = r"<REASONING>\s*(.*?)\s*</REASONING>"
ANSWER_BLOCK_PATTERN = r"<ANSWER>\s*(.*?)\s*</ANSWER>"

# Epistemik labels yang dikenali
EPISTEMIK_LABELS = {"FACT", "OPINION", "SPECULATION", "UNKNOWN"}
EPISTEMIK_PATTERN = r"\[(" + "|".join(EPISTEMIK_LABELS) + r")\]"

# Threshold untuk quality assessment
MIN_REASONING_CHARS = 50
MIN_ANSWER_CHARS = 20
MAX_REASONING_CHARS = 5000
WEAK_REASONING_CHARS = 100
ADEQUATE_REASONING_CHARS = 300


# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class CoTOutput:
    """
    Hasil ekstraksi dan validasi CoT output dari LLM.

    Attributes:
        reasoning: Extracted reasoning block content
        answer: Extracted answer block content
        epistemic_labels: Dict count per label type
        label_coverage: Ratio of labeled claims / total sentences
        confidence: Overall confidence score (0.0-1.0)
        reasoning_quality: Quality assessment (weak/adequate/strong)
        warnings: List of validation warnings
        is_valid: Whether output passes basic validation
    """
    reasoning: str
    answer: str
    epistemic_labels: dict[str, int] = field(default_factory=dict)
    label_coverage: float = 0.0
    confidence: float = 0.0
    reasoning_quality: str = "adequate"
    warnings: list[str] = field(default_factory=list)
    is_valid: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "reasoning": self.reasoning,
            "answer": self.answer,
            "epistemic_labels": self.epistemic_labels,
            "label_coverage": round(self.label_coverage, 3),
            "confidence": round(self.confidence, 3),
            "reasoning_quality": self.reasoning_quality,
            "warnings": self.warnings,
            "is_valid": self.is_valid,
        }


# ── Helper Functions ───────────────────────────────────────────────────────────

def _extract_reasoning_block(text: str) -> str:
    """
    Extract <REASONING>...</REASONING> block dari teks.

    Args:
        text: Raw LLM output

    Returns:
        Reasoning content (empty string jika tidak ada)
    """
    match = re.search(REASONING_BLOCK_PATTERN, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_answer_block(text: str) -> str:
    """
    Extract <ANSWER>...</ANSWER> block dari teks.

    Args:
        text: Raw LLM output

    Returns:
        Answer content (empty string jika tidak ada)
    """
    match = re.search(ANSWER_BLOCK_PATTERN, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_epistemik_labels(text: str) -> dict[str, int]:
    """
    Extract dan count epistemik labels dari teks.

    Args:
        text: Text yang mungkin berisi labels

    Returns:
        Dict dengan count per label type
    """
    labels: dict[str, int] = {label: 0 for label in EPISTEMIK_LABELS}
    matches = re.findall(EPISTEMIK_PATTERN, text)
    for match in matches:
        if match in labels:
            labels[match] += 1
    return labels


def _count_sentences(text: str) -> int:
    """
    Hitung approximate sentence count dari teks.

    Args:
        text: Text untuk dihitung

    Returns:
        Approximate sentence count
    """
    if not text:
        return 0
    # Simple heuristic: split pada . ! ? (bisa ada false positives)
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def _compute_label_coverage(text: str, labels: dict[str, int]) -> float:
    """
    Compute coverage ratio: # labeled claims / total claims.

    Args:
        text: Full text dengan labels
        labels: Dict dari extracted labels

    Returns:
        Coverage ratio (0.0-1.0)
    """
    total_sentences = _count_sentences(text)
    if total_sentences == 0:
        return 0.0

    total_labels = sum(labels.values())
    coverage = total_labels / total_sentences
    return min(coverage, 1.0)  # Cap at 1.0


def _score_reasoning_quality(reasoning: str, answer: str) -> str:
    """
    Score reasoning quality berdasarkan length, structure, dan coherence.

    Args:
        reasoning: Reasoning block content
        answer: Answer block content

    Returns:
        Quality assessment: "weak", "adequate", or "strong"
    """
    if not reasoning or len(reasoning) < WEAK_REASONING_CHARS:
        return "weak"

    if len(reasoning) > MAX_REASONING_CHARS:
        return "weak"  # Too verbose, likely hallucinating

    # Simple heuristics
    has_structure = len(re.split(r'\n', reasoning)) >= 3
    has_reasoning_markers = bool(re.search(
        r'(because|therefore|thus|step|reason|deduce|infer|conclude)',
        reasoning.lower()
    ))
    is_balanced = answer and len(answer) > MIN_ANSWER_CHARS

    if len(reasoning) >= ADEQUATE_REASONING_CHARS and has_structure and has_reasoning_markers:
        if is_balanced:
            return "strong"
        else:
            return "adequate"
    elif len(reasoning) >= WEAK_REASONING_CHARS:
        return "adequate"
    else:
        return "weak"


def _compute_confidence(
    reasoning_quality: str,
    label_coverage: float,
    epistemic_labels: dict[str, int],
) -> float:
    """
    Compute overall confidence score.

    Formula:
        confidence = quality_score * 0.5 + label_coverage * 0.3 + fact_bonus * 0.2

    Args:
        reasoning_quality: Quality assessment
        label_coverage: Coverage ratio
        epistemic_labels: Dict of label counts

    Returns:
        Confidence score (0.0-1.0)
    """
    # Quality score
    quality_scores = {"weak": 0.3, "adequate": 0.7, "strong": 1.0}
    quality_score = quality_scores.get(reasoning_quality, 0.5)

    # Coverage score
    coverage_score = min(label_coverage, 1.0)

    # Fact bonus: if > 0 FACT labels, boost confidence
    total_labels = sum(epistemic_labels.values())
    fact_count = epistemic_labels.get("FACT", 0)
    fact_bonus = min(fact_count / max(total_labels, 1), 1.0) if total_labels > 0 else 0.0

    confidence = (
        quality_score * 0.5 +
        coverage_score * 0.3 +
        fact_bonus * 0.2
    )
    return round(min(confidence, 1.0), 3)


def _validate_cot_output(
    reasoning: str,
    answer: str,
    epistemic_labels: dict[str, int],
    label_coverage: float,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    """
    Validate CoT output struktur dan content.

    Args:
        reasoning: Reasoning block
        answer: Answer block
        epistemic_labels: Dict of label counts
        label_coverage: Coverage ratio
        strict: If True, apply stricter validation

    Returns:
        Tuple (is_valid, warnings_list)
    """
    warnings: list[str] = []
    is_valid = True

    # Check reasoning existence
    if not reasoning or len(reasoning) < MIN_REASONING_CHARS:
        warnings.append(f"Reasoning too short (< {MIN_REASONING_CHARS} chars)")
        if strict:
            is_valid = False

    # Check answer existence
    if not answer or len(answer) < MIN_ANSWER_CHARS:
        warnings.append(f"Answer too short (< {MIN_ANSWER_CHARS} chars)")
        if strict:
            is_valid = False

    # Check label coverage
    if label_coverage < 0.3:
        warnings.append(f"Low epistemik label coverage ({label_coverage:.0%})")

    if strict and label_coverage < 0.6:
        is_valid = False

    # Check for hallucination signals
    if len(reasoning) > MAX_REASONING_CHARS:
        warnings.append(f"Reasoning extremely long (> {MAX_REASONING_CHARS} chars) — possible hallucination")
        is_valid = False

    return is_valid, warnings


# ── Main Extraction Function ───────────────────────────────────────────────────

def extract_cot_output(raw_text: str, strict: bool = False) -> CoTOutput:
    """
    Parse, validate, dan score CoT output dari raw LLM text.

    Args:
        raw_text: Raw LLM output (mungkin berisi blocks lain)
        strict: If True, apply stricter validation

    Returns:
        CoTOutput dengan metrics lengkap

    Examples:
        >>> raw = '<REASONING>Because A and B. Therefore C.</REASONING><ANSWER>[FACT] C is true.</ANSWER>'
        >>> output = extract_cot_output(raw)
        >>> output.confidence > 0.5
        True
        >>> output.is_valid
        True
    """
    # Extract blocks
    reasoning = _extract_reasoning_block(raw_text)
    answer = _extract_answer_block(raw_text)

    # Extract labels dari answer (main content)
    all_text = reasoning + " " + answer
    epistemic_labels = _extract_epistemik_labels(all_text)

    # Compute coverage
    label_coverage = _compute_label_coverage(answer, epistemic_labels)

    # Score reasoning
    reasoning_quality = _score_reasoning_quality(reasoning, answer)

    # Compute confidence
    confidence = _compute_confidence(reasoning_quality, label_coverage, epistemic_labels)

    # Validate
    is_valid, warnings = _validate_cot_output(
        reasoning, answer, epistemic_labels, label_coverage, strict=strict
    )

    return CoTOutput(
        reasoning=reasoning,
        answer=answer,
        epistemic_labels=epistemic_labels,
        label_coverage=label_coverage,
        confidence=confidence,
        reasoning_quality=reasoning_quality,
        warnings=warnings,
        is_valid=is_valid,
    )


if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Valid strong CoT
        """
        <REASONING>
        Langkah 1: Pahami pertanyaan.
        Langkah 2: Identifikasi premis.
        Langkah 3: Derive kesimpulan.
        </REASONING>
        <ANSWER>
        [FACT] Based on evidence, the conclusion is sound.
        [OPINION] In my assessment, this interpretation is reasonable.
        </ANSWER>
        """,
        # Weak reasoning
        """
        <REASONING>Yes.</REASONING>
        <ANSWER>Answer is yes.</ANSWER>
        """,
        # Missing blocks
        """
        Just a plain answer without structured blocks.
        """,
        # Extreme length
        """
        <REASONING>
        %s
        </REASONING>
        <ANSWER>[FACT] Answer.</ANSWER>
        """ % ("x" * 6000),
    ]

    for i, test in enumerate(test_cases):
        output = extract_cot_output(test)
        print(f"\nTest {i+1}:")
        print(f"  Reasoning len: {len(output.reasoning)}")
        print(f"  Answer len: {len(output.answer)}")
        print(f"  Quality: {output.reasoning_quality}")
        print(f"  Confidence: {output.confidence}")
        print(f"  Coverage: {output.label_coverage:.0%}")
        print(f"  Valid: {output.is_valid}")
        print(f"  Warnings: {output.warnings}")

    print("\n✓ CoT extraction tests completed!")
