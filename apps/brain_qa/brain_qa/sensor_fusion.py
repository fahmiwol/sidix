"""
sensor_fusion.py — Sensor Fusion Engine

Gabungkan input dari multiple senses jadi satu "unified perception"
yang masuk ke ReAct loop.

Late fusion — rule-based, no LLM needed:
  1. Text query = primary input
  2. Emotional tone = context modifier
  3. Vision caption = appended as [USER SHARED IMAGE: ...]
  4. Audio transcript = appended as [USER SAID VIA VOICE: ...]
  5. Conflict detection: vision vs text mismatch → flag

Modern reference: Sensor Fusion (late fusion), Embodied Cognition.
Jiwa Sprint 3 Fase C (Kimi)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SenseInput:
    """Satu input dari satu sense."""
    source: str  # text | vision | audio | emotional | sensor_hub
    data: str
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedContext:
    """Hasil fusion — unified perception untuk ReAct loop."""
    primary_query: str
    unified_prompt: str  # gabungan semua input untuk inject ke ReAct
    emotional_modifier: str = ""  # tone hint dari emotional sense
    vision_context: str = ""  # image caption
    audio_context: str = ""  # voice transcript
    cross_modal_conflict: bool = False
    conflict_details: list[str] = field(default_factory=list)
    fused_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sources: list[str] = field(default_factory=list)


# ── Fusion engine ────────────────────────────────────────────────────────────

class SensorFusionEngine:
    """Late fusion: combine sense inputs → unified context."""

    def fuse(self, inputs: list[SenseInput]) -> FusedContext:
        """
        Fuse multiple sense inputs into unified context.

        Priority:
        1. text → primary query
        2. emotional → tone modifier
        3. vision → image context
        4. audio → voice context
        """
        if not inputs:
            return FusedContext(
                primary_query="",
                unified_prompt="",
                sources=[],
            )

        # Sort by confidence (descending) within source type
        inputs_sorted = sorted(inputs, key=lambda x: (x.source, -x.confidence))

        # Extract primary query (text source with highest confidence)
        text_inputs = [i for i in inputs_sorted if i.source == "text"]
        primary = text_inputs[0].data if text_inputs else inputs[0].data

        # Extract emotional modifier
        emotional_inputs = [i for i in inputs_sorted if i.source == "emotional"]
        emotional_mod = ""
        if emotional_inputs:
            emotional_mod = self._extract_tone_hint(emotional_inputs[0])

        # Extract vision context
        vision_inputs = [i for i in inputs_sorted if i.source == "vision"]
        vision_ctx = ""
        if vision_inputs:
            vision_ctx = vision_inputs[0].data

        # Extract audio context
        audio_inputs = [i for i in inputs_sorted if i.source == "audio"]
        audio_ctx = ""
        if audio_inputs:
            audio_ctx = audio_inputs[0].data

        # Build unified prompt
        parts: list[str] = []
        if emotional_mod:
            parts.append(f"[KONTEKS EMOSIONAL] {emotional_mod}")
        if vision_ctx:
            parts.append(f"[GAMBAR YANG DI-SHARE USER] {vision_ctx}")
        if audio_ctx:
            parts.append(f"[PESAN SUARA USER] {audio_ctx}")
        parts.append(f"[PERTANYAAN UTAMA] {primary}")

        unified = "\n\n".join(parts)

        # Conflict detection
        conflicts = self._detect_conflicts(primary, vision_ctx, audio_ctx)

        return FusedContext(
            primary_query=primary,
            unified_prompt=unified,
            emotional_modifier=emotional_mod,
            vision_context=vision_ctx,
            audio_context=audio_ctx,
            cross_modal_conflict=len(conflicts) > 0,
            conflict_details=conflicts,
            sources=[i.source for i in inputs],
        )

    def _extract_tone_hint(self, emotional_input: SenseInput) -> str:
        """Extract tone hint dari emotional sense input."""
        data = emotional_input.data.lower()
        hints = []
        if any(w in data for w in ["marah", "angry", "kesel", "frustrated"]):
            hints.append("User sedang emosi/marah — respon dengan tenang")
        if any(w in data for w in ["sedih", "sad", "kecewa", "disappointed"]):
            hints.append("User sedih — respon dengan empati")
        if any(w in data for w in ["cemas", "anxious", "takut", "khawatir"]):
            hints.append("User cemas — respon dengan meyakinkan")
        if any(w in data for w in ["senang", "happy", "excited", "semangat"]):
            hints.append("User senang/semangat — respon dengan energik")
        if any(w in data for w in ["bingung", "confused", "gak ngerti"]):
            hints.append("User bingung — respon dengan sabar dan jelas")
        return "; ".join(hints) if hints else ""

    def _detect_conflicts(self, primary: str, vision: str, audio: str) -> list[str]:
        """Detect cross-modal conflicts."""
        conflicts = []
        if vision and primary:
            # Simple keyword overlap check
            v_words = set(vision.lower().split())
            p_words = set(primary.lower().split())
            meaningful_v = {w for w in v_words if len(w) > 4}
            meaningful_p = {w for w in p_words if len(w) > 4}
            if meaningful_v and meaningful_p:
                overlap = meaningful_v & meaningful_p
                if not overlap:
                    conflicts.append("Vision caption and text query have no keyword overlap — possible mismatch.")
        if audio and primary:
            a_words = set(audio.lower().split())
            p_words = set(primary.lower().split())
            meaningful_a = {w for w in a_words if len(w) > 4}
            meaningful_p = {w for w in p_words if len(w) > 4}
            if meaningful_a and meaningful_p:
                overlap = meaningful_a & meaningful_p
                if not overlap:
                    conflicts.append("Audio transcript and text query have no keyword overlap — possible mismatch.")
        return conflicts


# ── Convenience API ──────────────────────────────────────────────────────────

def fuse_sense_inputs(inputs: list[dict[str, Any]]) -> dict[str, Any]:
    """One-shot: list of dict → fused context dict."""
    engine = SensorFusionEngine()
    sense_inputs = [
        SenseInput(
            source=inp.get("source", "text"),
            data=inp.get("data", ""),
            confidence=inp.get("confidence", 1.0),
            metadata=inp.get("metadata", {}),
        )
        for inp in inputs
    ]
    fused = engine.fuse(sense_inputs)
    return {
        "primary_query": fused.primary_query,
        "unified_prompt": fused.unified_prompt,
        "emotional_modifier": fused.emotional_modifier,
        "vision_context": fused.vision_context,
        "audio_context": fused.audio_context,
        "cross_modal_conflict": fused.cross_modal_conflict,
        "conflict_details": fused.conflict_details,
        "sources": fused.sources,
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Sensor Fusion Engine Self-Test ===\n")

    engine = SensorFusionEngine()

    # Test 1: Text only
    inputs1 = [SenseInput(source="text", data="Apa itu machine learning?")]
    fused1 = engine.fuse(inputs1)
    print(f"[1] Text only: primary='{fused1.primary_query}'")
    assert fused1.primary_query == "Apa itu machine learning?"
    assert not fused1.cross_modal_conflict
    print("  OK\n")

    # Test 2: Text + emotional
    inputs2 = [
        SenseInput(source="text", data="Apa itu ML?"),
        SenseInput(source="emotional", data="User marah karena penjelasan sebelumnya tidak jelas"),
    ]
    fused2 = engine.fuse(inputs2)
    print(f"[2] Text + emotional: modifier='{fused2.emotional_modifier[:50]}...'")
    assert "marah" in fused2.emotional_modifier.lower() or "emosi" in fused2.emotional_modifier.lower()
    print("  OK\n")

    # Test 3: Text + vision
    inputs3 = [
        SenseInput(source="text", data="Jelaskan grafik ini"),
        SenseInput(source="vision", data="Grafik batang menunjukkan penjualan naik 50% di Q3"),
    ]
    fused3 = engine.fuse(inputs3)
    print(f"[3] Text + vision: vision_ctx='{fused3.vision_context[:50]}...'")
    assert "Grafik" in fused3.unified_prompt
    assert not fused3.cross_modal_conflict  # "grafik" overlap
    print("  OK\n")

    # Test 4: Cross-modal conflict
    inputs4 = [
        SenseInput(source="text", data="Apa itu photosynthesis?"),
        SenseInput(source="vision", data="Seekor kucing tidur di sofa merah"),
    ]
    fused4 = engine.fuse(inputs4)
    print(f"[4] Conflict: conflict={fused4.cross_modal_conflict}")
    assert fused4.cross_modal_conflict is True
    assert len(fused4.conflict_details) > 0
    print("  OK\n")

    # Test 5: Convenience API
    d = fuse_sense_inputs([
        {"source": "text", "data": "Halo"},
        {"source": "audio", "data": "Halo SIDIX"},
    ])
    assert d["primary_query"] == "Halo"
    assert "audio" in d["sources"]
    print("[5] Convenience API: OK\n")

    print("[OK] All self-tests passed")
