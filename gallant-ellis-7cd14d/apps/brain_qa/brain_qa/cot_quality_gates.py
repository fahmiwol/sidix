"""
cot_quality_gates.py — Quality Gate Evaluation for CoT Outputs

Tanggung jawab:
  - Define 5 quality gates untuk validasi CoT output
  - Configurable thresholds per mode (strict/standard/relaxed)
  - Evaluate output against gates
  - Suggest fallback strategies kalau ada gate failures
  - Return structured gate evaluation result

5 Gates:
  1. Reasoning exists (min 50 chars)
  2. Epistemik label coverage >= min_label_coverage
  3. Confidence >= min_confidence
  4. Reasoning quality != "weak"
  5. No hallucination (reasoning < 5000 chars)

Fallback strategies:
  - "re_prompt_cot": Re-prompt dengan explicit CoT instruction
  - "auto_inject_labels": Automatically label claims dalam answer
  - "corpus_only_mode": Fallback ke corpus search tanpa LLM generation
  - "retry_with_higher_temp": Retry dengan temperature > 0.7
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from cot_extractor import CoTOutput

logger = logging.getLogger(__name__)

# ── Mode Enum ──────────────────────────────────────────────────────────────────

class GateMode(str, Enum):
    """Quality gate configuration mode."""
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


# ── Gate Configuration ─────────────────────────────────────────────────────────

@dataclass
class GateConfig:
    """Configuration untuk quality gates."""
    min_reasoning_chars: int = 50
    max_reasoning_chars: int = 5000
    min_label_coverage: float = 0.6
    min_confidence: float = 0.5
    allow_weak_reasoning: bool = False

    @classmethod
    def for_mode(cls, mode: str) -> GateConfig:
        """Get default config untuk mode."""
        mode = mode.lower()
        if mode == "strict":
            return cls(
                min_reasoning_chars=200,
                max_reasoning_chars=5000,
                min_label_coverage=0.7,
                min_confidence=0.7,
                allow_weak_reasoning=False,
            )
        elif mode == "relaxed":
            return cls(
                min_reasoning_chars=30,
                max_reasoning_chars=5000,
                min_label_coverage=0.3,
                min_confidence=0.4,
                allow_weak_reasoning=True,
            )
        else:  # standard
            return cls(
                min_reasoning_chars=50,
                max_reasoning_chars=5000,
                min_label_coverage=0.6,
                min_confidence=0.5,
                allow_weak_reasoning=False,
            )


# ── Gate Result ────────────────────────────────────────────────────────────────

@dataclass
class GateResult:
    """Hasil evaluasi satu gate."""
    gate_id: str
    gate_name: str
    passed: bool
    reason: str
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class QualityGateEvaluation:
    """Hasil evaluasi semua quality gates."""
    passed: bool  # True jika semua gates passed
    failing_gates: list[GateResult] = field(default_factory=list)
    passing_gates: list[GateResult] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    fallback_strategies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert ke dict untuk serialization."""
        return {
            "passed": self.passed,
            "failing_gates": [
                {
                    "gate_id": g.gate_id,
                    "gate_name": g.gate_name,
                    "reason": g.reason,
                    "severity": g.severity,
                }
                for g in self.failing_gates
            ],
            "passing_gates": [
                {
                    "gate_id": g.gate_id,
                    "gate_name": g.gate_name,
                }
                for g in self.passing_gates
            ],
            "recommendations": self.recommendations,
            "fallback_strategies": self.fallback_strategies,
        }


# ── Quality Gate Class ─────────────────────────────────────────────────────────

class QualityGate:
    """
    Quality gate evaluator untuk CoT outputs.

    Configurable thresholds, semantic failure analysis, fallback suggestions.
    """

    def __init__(self, mode: str = "standard"):
        """
        Initialize quality gate.

        Args:
            mode: "strict", "standard", atau "relaxed"
        """
        self.mode = mode.lower()
        self.config = GateConfig.for_mode(self.mode)
        logger.info(f"QualityGate initialized with mode={self.mode}")

    def evaluate(self, cot: CoTOutput) -> QualityGateEvaluation:
        """
        Evaluate CoT output terhadap semua gates.

        Args:
            cot: CoT output dari extractor

        Returns:
            QualityGateEvaluation dengan hasil semua gates
        """
        failing = []
        passing = []

        # Gate 1: Reasoning exists
        gate1 = self._evaluate_gate_reasoning_exists(cot)
        if gate1.passed:
            passing.append(gate1)
        else:
            failing.append(gate1)

        # Gate 2: Label coverage
        gate2 = self._evaluate_gate_label_coverage(cot)
        if gate2.passed:
            passing.append(gate2)
        else:
            failing.append(gate2)

        # Gate 3: Confidence
        gate3 = self._evaluate_gate_confidence(cot)
        if gate3.passed:
            passing.append(gate3)
        else:
            failing.append(gate3)

        # Gate 4: Reasoning quality
        gate4 = self._evaluate_gate_reasoning_quality(cot)
        if gate4.passed:
            passing.append(gate4)
        else:
            failing.append(gate4)

        # Gate 5: No hallucination
        gate5 = self._evaluate_gate_no_hallucination(cot)
        if gate5.passed:
            passing.append(gate5)
        else:
            failing.append(gate5)

        # Determine overall pass/fail
        all_passed = len(failing) == 0

        # Generate recommendations
        recommendations = self._generate_recommendations(cot, failing)

        # Suggest fallback strategies
        fallback_strategies = self._get_fallback_strategies(failing, cot)

        return QualityGateEvaluation(
            passed=all_passed,
            failing_gates=failing,
            passing_gates=passing,
            recommendations=recommendations,
            fallback_strategies=fallback_strategies,
        )

    def _evaluate_gate_reasoning_exists(self, cot: CoTOutput) -> GateResult:
        """Gate 1: Reasoning block exists and sufficient length."""
        reasoning_len = len(cot.reasoning)
        passed = reasoning_len >= self.config.min_reasoning_chars

        if passed:
            return GateResult(
                gate_id="G1",
                gate_name="Reasoning Exists",
                passed=True,
                reason=f"Reasoning length: {reasoning_len} chars (min: {self.config.min_reasoning_chars})",
                severity="low",
            )
        else:
            return GateResult(
                gate_id="G1",
                gate_name="Reasoning Exists",
                passed=False,
                reason=f"Reasoning too short: {reasoning_len} chars (min: {self.config.min_reasoning_chars})",
                severity="high",
            )

    def _evaluate_gate_label_coverage(self, cot: CoTOutput) -> GateResult:
        """Gate 2: Epistemik label coverage >= threshold."""
        coverage = cot.label_coverage
        passed = coverage >= self.config.min_label_coverage

        if passed:
            return GateResult(
                gate_id="G2",
                gate_name="Epistemik Label Coverage",
                passed=True,
                reason=f"Coverage: {coverage:.0%} (min: {self.config.min_label_coverage:.0%})",
                severity="low",
            )
        else:
            return GateResult(
                gate_id="G2",
                gate_name="Epistemik Label Coverage",
                passed=False,
                reason=f"Coverage too low: {coverage:.0%} (min: {self.config.min_label_coverage:.0%})",
                severity="medium",
            )

    def _evaluate_gate_confidence(self, cot: CoTOutput) -> GateResult:
        """Gate 3: Overall confidence >= threshold."""
        confidence = cot.confidence
        passed = confidence >= self.config.min_confidence

        if passed:
            return GateResult(
                gate_id="G3",
                gate_name="Confidence Score",
                passed=True,
                reason=f"Confidence: {confidence:.2f} (min: {self.config.min_confidence:.2f})",
                severity="low",
            )
        else:
            return GateResult(
                gate_id="G3",
                gate_name="Confidence Score",
                passed=False,
                reason=f"Confidence too low: {confidence:.2f} (min: {self.config.min_confidence:.2f})",
                severity="medium",
            )

    def _evaluate_gate_reasoning_quality(self, cot: CoTOutput) -> GateResult:
        """Gate 4: Reasoning quality != weak."""
        quality = cot.reasoning_quality
        passed = quality != "weak" or self.config.allow_weak_reasoning

        if passed:
            return GateResult(
                gate_id="G4",
                gate_name="Reasoning Quality",
                passed=True,
                reason=f"Quality level: {quality}",
                severity="low",
            )
        else:
            return GateResult(
                gate_id="G4",
                gate_name="Reasoning Quality",
                passed=False,
                reason=f"Reasoning quality is weak (detected shallow thinking)",
                severity="high",
            )

    def _evaluate_gate_no_hallucination(self, cot: CoTOutput) -> GateResult:
        """Gate 5: No hallucination signals."""
        reasoning_len = len(cot.reasoning)
        passed = reasoning_len <= self.config.max_reasoning_chars

        if passed:
            return GateResult(
                gate_id="G5",
                gate_name="No Hallucination",
                passed=True,
                reason=f"Reasoning length within bounds: {reasoning_len} chars",
                severity="low",
            )
        else:
            return GateResult(
                gate_id="G5",
                gate_name="No Hallucination",
                passed=False,
                reason=f"Reasoning extremely long: {reasoning_len} chars (max: {self.config.max_reasoning_chars}) — possible hallucination",
                severity="critical",
            )

    def _generate_recommendations(
        self,
        cot: CoTOutput,
        failing_gates: list[GateResult],
    ) -> list[str]:
        """Generate user-friendly recommendations based on failures."""
        recommendations = []

        for gate in failing_gates:
            if gate.gate_id == "G1":
                recommendations.append(
                    "Reasoning is too brief. Request model to show detailed step-by-step reasoning."
                )
            elif gate.gate_id == "G2":
                recommendations.append(
                    f"Add epistemik labels (e.g., [FACT], [OPINION]) to claims. Current coverage: {cot.label_coverage:.0%}"
                )
            elif gate.gate_id == "G3":
                recommendations.append(
                    f"Confidence is low ({cot.confidence:.2f}). Consider: (a) re-prompting, (b) using more corpus context, (c) increasing temperature."
                )
            elif gate.gate_id == "G4":
                recommendations.append(
                    "Reasoning quality is weak. Request explicit step-by-step CoT with intermediate conclusions."
                )
            elif gate.gate_id == "G5":
                recommendations.append(
                    "Reasoning is excessively long — possible hallucination or token limit issue. Retry with temperature control."
                )

        return recommendations

    def _get_fallback_strategies(
        self,
        failing_gates: list[GateResult],
        cot: CoTOutput,
    ) -> list[str]:
        """Suggest fallback strategies untuk gate failures."""
        strategies = []

        critical_failures = [g for g in failing_gates if g.severity == "critical"]
        high_failures = [g for g in failing_gates if g.severity == "high"]
        medium_failures = [g for g in failing_gates if g.severity == "medium"]

        # If critical failures, suggest strongest fallback
        if critical_failures:
            strategies.append("corpus_only_mode")  # Fallback ke corpus search
            strategies.append("retry_with_higher_temp")

        # If high failures, suggest re-prompt
        if high_failures:
            strategies.append("re_prompt_cot")
            if any(g.gate_id == "G2" for g in high_failures):
                strategies.append("auto_inject_labels")

        # If medium failures, suggest lighter retry
        if medium_failures:
            if any(g.gate_id in ["G2", "G3"] for g in medium_failures):
                strategies.append("retry_with_higher_temp")

        # Remove duplicates, maintain order
        seen = set()
        unique_strategies = []
        for s in strategies:
            if s not in seen:
                unique_strategies.append(s)
                seen.add(s)

        return unique_strategies

    def adjust_config(
        self,
        min_label_coverage: Optional[float] = None,
        min_confidence: Optional[float] = None,
    ) -> None:
        """
        Adjust configuration thresholds dynamically.

        Args:
            min_label_coverage: New minimum label coverage threshold
            min_confidence: New minimum confidence threshold
        """
        if min_label_coverage is not None:
            self.config.min_label_coverage = min_label_coverage
            logger.info(f"Updated min_label_coverage to {min_label_coverage}")

        if min_confidence is not None:
            self.config.min_confidence = min_confidence
            logger.info(f"Updated min_confidence to {min_confidence}")


if __name__ == "__main__":
    from cot_extractor import extract_cot_output

    # Test dengan sample CoT outputs
    test_output_strong = """
    <REASONING>
    Langkah 1: Pahami pertanyaan tentang strategi.
    Langkah 2: Identifikasi faktor-faktor penting.
    Langkah 3: Evaluasi pro dan kontra.
    Langkah 4: Derive rekomendasi yang balanced.
    </REASONING>
    <ANSWER>
    [FACT] Historical data shows X strategy increased revenue by 20%.
    [OPINION] I believe this approach is most effective for your case.
    [SPECULATION] The future impact might be Y, pending market conditions.
    </ANSWER>
    """

    test_output_weak = """
    <REASONING>Hmm, yes.</REASONING>
    <ANSWER>Sure, that's good.</ANSWER>
    """

    for i, mode in enumerate(["strict", "standard", "relaxed"]):
        print(f"\n{'='*60}")
        print(f"Mode: {mode.upper()}")
        print(f"{'='*60}")

        gate = QualityGate(mode)

        for j, raw_output in enumerate([test_output_strong, test_output_weak]):
            cot = extract_cot_output(raw_output)
            eval_result = gate.evaluate(cot)

            print(f"\nTest {j+1}:")
            print(f"  Overall passed: {eval_result.passed}")
            print(f"  Failing gates: {len(eval_result.failing_gates)}")
            print(f"  Recommendations: {eval_result.recommendations[:2]}")  # First 2
            print(f"  Fallback strategies: {eval_result.fallback_strategies}")

    print("\n✓ Quality gate tests completed!")
