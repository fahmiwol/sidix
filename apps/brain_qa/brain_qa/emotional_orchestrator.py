"""
emotional_orchestrator.py — Emotional Orchestrator for Parallel Senses

Saat multiple senses aktif bersamaan (text + voice + image context),
orchestrator ini meng-aggregate emotional state dari tiap sense
menjadi satu global tone directive.

Prinsip:
- Conflicting emotions → voice tone wins (lebih autentik)
- Negative high-arousal (angry/frustrated) overrides everything
- Anxious gets priority over sad
- All positive → match the highest enthusiasm

Pivot 2026-04-25 — Jiwa Sprint Task 4 (Kimi lane)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .emotional_tone_engine import EmotionalState, ToneAdaptation, adapt_tone, Valence, Arousal


# ── Priority hierarchy for conflict resolution ───────────────────────────────

_EMOTION_PRIORITY = {
    "angry": 10,
    "frustrated": 9,
    "anxious": 8,
    "sad": 7,
    "confused": 6,
    "excited": 5,
    "grateful": 4,
    "curious": 3,
    "neutral": 0,
}

# Source weight — voice lebih autentik dari text
_SOURCE_WEIGHT = {
    "voice": 1.5,
    "text": 1.0,
    "image_context": 0.8,
    "sensor_hub": 1.0,
    "default": 1.0,
}


@dataclass
class SenseEmotion:
    """Emotional state dari satu sense dengan metadata."""
    source: str  # voice | text | image_context | sensor_hub
    state: EmotionalState
    weight: float = 1.0


class EmotionalOrchestrator:
    """Aggregate multiple sense emotions → global tone directive."""

    def __init__(self):
        self.sense_inputs: list[SenseEmotion] = []

    def add(self, source: str, state: EmotionalState) -> None:
        """Tambahkan emotional state dari satu sense."""
        weight = _SOURCE_WEIGHT.get(source, 1.0)
        self.sense_inputs.append(SenseEmotion(source=source, state=state, weight=weight))

    def clear(self) -> None:
        self.sense_inputs = []

    def orchestrate(self) -> ToneAdaptation:
        """
        Aggregate semua sense inputs → single global ToneAdaptation.

        Logic:
        1. Weighted scoring per emotion
        2. Negative high-arousal override check
        3. Source authenticity tie-break (voice wins)
        4. Return ToneAdaptation dengan priority disesuaikan
        """
        if not self.sense_inputs:
            return ToneAdaptation(tone_hint="", style_modifier={}, priority="low")

        if len(self.sense_inputs) == 1:
            return adapt_tone(self.sense_inputs[0].state)

        # Step 1: Weighted emotion scoring
        scores: dict[str, float] = {}
        for se in self.sense_inputs:
            emotion = se.state.dominant_emotion
            base_score = _EMOTION_PRIORITY.get(emotion, 0)
            weighted = base_score * se.weight * se.state.confidence
            scores[emotion] = scores.get(emotion, 0) + weighted

        # Step 2: Pick dominant emotion
        dominant_emotion = max(scores, key=scores.get)
        dominant_state = self._find_representative_state(dominant_emotion)

        # Step 3: Override check — negative high-arousal always wins
        for se in self.sense_inputs:
            if se.state.dominant_emotion in ("angry", "frustrated"):
                dominant_emotion = se.state.dominant_emotion
                dominant_state = se.state
                break
            if se.state.dominant_emotion == "anxious":
                # Anxious overrides unless angry/frustrated exists
                if dominant_emotion not in ("angry", "frustrated"):
                    dominant_emotion = "anxious"
                    dominant_state = se.state

        # Step 4: Build global adaptation
        base_adapt = adapt_tone(dominant_state)

        # Step 5: Priority — angry/frustrated always high, then negative count
        has_angry_frustrated = any(
            se.state.dominant_emotion in ("angry", "frustrated")
            for se in self.sense_inputs
        )
        negative_count = sum(
            1 for se in self.sense_inputs
            if se.state.valence == Valence.NEGATIVE
        )
        if has_angry_frustrated or negative_count >= 2:
            priority = "high"
        elif negative_count == 1:
            priority = "medium"
        else:
            priority = base_adapt.priority

        # Step 6: Merge style modifiers (weighted average)
        merged_modifiers = self._merge_modifiers()

        # Step 7: Build global hint
        sources_str = ", ".join(se.source for se in self.sense_inputs)
        hint = (
            f"[Global Tone] {dominant_emotion.upper()} detected across {len(self.sense_inputs)} senses "
            f"({sources_str}). {base_adapt.tone_hint}"
        )

        return ToneAdaptation(
            tone_hint=hint,
            style_modifier=merged_modifiers,
            priority=priority,
        )

    def _find_representative_state(self, emotion: str) -> EmotionalState:
        """Cari EmotionalState yang paling representative untuk emotion ini."""
        candidates = [se.state for se in self.sense_inputs if se.state.dominant_emotion == emotion]
        if not candidates:
            return EmotionalState(
                valence=Valence.NEUTRAL,
                arousal=Arousal.CALM,
                dominant_emotion=emotion,
                confidence=0.0,
                matched_keywords=[],
            )
        # Pick highest confidence
        return max(candidates, key=lambda s: s.confidence)

    def _merge_modifiers(self) -> dict[str, Any]:
        """Weighted average dari style modifiers semua inputs."""
        totals: dict[str, float] = {}
        weights: dict[str, float] = {}
        for se in self.sense_inputs:
            adapt = adapt_tone(se.state)
            for dim, val in adapt.style_modifier.items():
                w = se.weight * se.state.confidence
                totals[dim] = totals.get(dim, 0.0) + val * w
                weights[dim] = weights.get(dim, 0.0) + w
        merged = {}
        for dim in totals:
            if weights[dim] > 0:
                merged[dim] = round(totals[dim] / weights[dim], 2)
        return merged

    def summary(self) -> dict[str, Any]:
        """Debug summary dari semua inputs + orchestration result."""
        adapt = self.orchestrate()
        return {
            "inputs_count": len(self.sense_inputs),
            "inputs": [
                {
                    "source": se.source,
                    "emotion": se.state.dominant_emotion,
                    "confidence": se.state.confidence,
                    "valence": se.state.valence.value,
                    "weight": se.weight,
                }
                for se in self.sense_inputs
            ],
            "global_emotion": adapt.tone_hint.split("]")[0].replace("[Global Tone] ", "").strip() if adapt.tone_hint else "neutral",
            "global_priority": adapt.priority,
            "global_style_modifier": adapt.style_modifier,
        }


# ── Convenience API ──────────────────────────────────────────────────────────

def orchestrate_emotions(inputs: list[dict[str, Any]]) -> dict[str, Any]:
    """
    One-shot: list of {source, emotion_text} → global tone dict.

    Example:
        inputs = [
            {"source": "text", "emotion_text": "aku sangat marah"},
            {"source": "voice", "emotion_text": "tenang ya"},
        ]
    """
    from .emotional_tone_engine import detect_emotion

    orch = EmotionalOrchestrator()
    for inp in inputs:
        text = inp.get("emotion_text", "")
        source = inp.get("source", "default")
        state = detect_emotion(text)
        orch.add(source, state)

    adapt = orch.orchestrate()
    return {
        "tone_hint": adapt.tone_hint,
        "priority": adapt.priority,
        "style_modifier": adapt.style_modifier,
        "summary": orch.summary(),
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Emotional Orchestrator Self-Test ===\n")

    # Test 1: Single input
    orch1 = EmotionalOrchestrator()
    from .emotional_tone_engine import detect_emotion
    orch1.add("text", detect_emotion("aku sangat marah"))
    adapt1 = orch1.orchestrate()
    print(f"[1] Single angry text -> priority={adapt1.priority}")
    assert adapt1.priority == "high"
    print("  OK\n")

    # Test 2: Conflicting — text happy, voice angry (voice wins)
    orch2 = EmotionalOrchestrator()
    orch2.add("text", detect_emotion("wow hebat!"))
    orch2.add("voice", detect_emotion("aku kesel banget"))
    adapt2 = orch2.orchestrate()
    print(f"[2] Text happy + voice angry -> priority={adapt2.priority}")
    assert adapt2.priority == "high"
    assert "angry" in adapt2.tone_hint.lower() or "kesel" in adapt2.tone_hint.lower()
    print("  OK\n")

    # Test 3: Multiple negative — priority boost
    orch3 = EmotionalOrchestrator()
    orch3.add("text", detect_emotion("sedih rasanya"))
    orch3.add("voice", detect_emotion("aku cemas nih"))
    adapt3 = orch3.orchestrate()
    print(f"[3] Sad + anxious -> priority={adapt3.priority}")
    assert adapt3.priority in ("high", "medium")
    print("  OK\n")

    # Test 4: All positive
    orch4 = EmotionalOrchestrator()
    orch4.add("text", detect_emotion("wow keren banget"))
    orch4.add("voice", detect_emotion("makasih banyak ya"))
    adapt4 = orch4.orchestrate()
    print(f"[4] Excited + grateful -> priority={adapt4.priority}")
    assert adapt4.priority in ("low", "medium")
    print("  OK\n")

    # Test 5: Convenience API
    result = orchestrate_emotions([
        {"source": "text", "emotion_text": "aku bingung nih"},
    ])
    assert result["priority"] in ("high", "medium", "low")
    print(f"[5] Convenience API -> priority={result['priority']}")
    print("  OK\n")

    print("[OK] All self-tests passed")
