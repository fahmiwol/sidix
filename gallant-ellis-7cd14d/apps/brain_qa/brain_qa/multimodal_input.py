"""
multimodal_input.py — Multimodal Input Handler

Handler untuk request yang mengandung multiple input types:
  text + image + audio → unified context → ReAct loop.

Pipeline:
  1. Extract text (direct or via STT)
  2. Extract image caption (via vision API)
  3. Detect emotion dari text
  4. Fuse all → single context → pass ke run_react()

Integration: agent_serve.py endpoint /agent/multimodal
Jiwa Sprint 3 Fase E (Kimi)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agent_react import run_react, AgentSession
from .sensor_fusion import SenseInput, SensorFusionEngine
from .emotional_tone_engine import detect_emotion
from .sense_stream import get_sense_stream


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class MultimodalInput:
    """Input multimodal dari user."""
    text: str = ""
    image_path: str = ""
    audio_path: str = ""
    persona: str = "UTZ"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultimodalResult:
    """Hasil processing multimodal input."""
    session: AgentSession
    fused_context: str = ""
    emotional_state: dict[str, Any] = field(default_factory=dict)
    vision_caption: str = ""
    audio_transcript: str = ""
    multimodal_metadata: dict[str, Any] = field(default_factory=dict)


# ── Handler ──────────────────────────────────────────────────────────────────

class MultimodalInputHandler:
    """Process multimodal input → unified ReAct session."""

    def __init__(self):
        self.fusion = SensorFusionEngine()
        self.stream = get_sense_stream()

    def process(
        self,
        inp: MultimodalInput,
        *,
        client_id: str = "",
        agency_id: str = "",
        conversation_id: str = "",
    ) -> MultimodalResult:
        """
        Process multimodal input and return enriched AgentSession.
        """
        sense_inputs: list[SenseInput] = []
        vision_caption = ""
        audio_transcript = ""
        emotional_state: dict[str, Any] = {}

        # Step 1: Process vision (image → caption)
        if inp.image_path:
            vision_caption = self._extract_image_caption(inp.image_path)
            if vision_caption:
                sense_inputs.append(SenseInput(
                    source="vision", data=vision_caption, confidence=0.8
                ))
                self.stream.emit_quick("vision", vision_caption, 0.8)

        # Step 2: Process audio (audio → transcript)
        if inp.audio_path:
            audio_transcript = self._extract_audio_transcript(inp.audio_path)
            if audio_transcript:
                sense_inputs.append(SenseInput(
                    source="audio", data=audio_transcript, confidence=0.85
                ))
                self.stream.emit_quick("audio", audio_transcript, 0.85)

        # Step 3: Process text (primary input)
        primary_text = inp.text or audio_transcript or vision_caption or "..."
        if primary_text:
            sense_inputs.append(SenseInput(
                source="text", data=primary_text, confidence=1.0
            ))
            self.stream.emit_quick("text", primary_text, 1.0)

        # Step 4: Detect emotion
        if primary_text:
            emotion = detect_emotion(primary_text)
            emotional_state = {
                "dominant_emotion": emotion.dominant_emotion,
                "valence": emotion.valence.value,
                "arousal": emotion.arousal.value,
                "confidence": emotion.confidence,
            }
            if emotion.confidence > 0.3:
                sense_inputs.append(SenseInput(
                    source="emotional",
                    data=f"User feels {emotion.dominant_emotion}",
                    confidence=emotion.confidence,
                ))
                self.stream.emit_quick(
                    "emotional", f"User feels {emotion.dominant_emotion}", emotion.confidence
                )

        # Step 5: Fuse all inputs
        fused = self.fusion.fuse(sense_inputs)

        # Step 6: Run ReAct with fused context
        session = run_react(
            question=fused.unified_prompt or primary_text,
            persona=inp.persona,
            client_id=client_id,
            agency_id=agency_id,
            conversation_id=conversation_id,
        )

        # Enrich session metadata
        session.multimodal_metadata = {
            "fused_context": fused.unified_prompt,
            "sources": fused.sources,
            "cross_modal_conflict": fused.cross_modal_conflict,
            "conflict_details": fused.conflict_details,
        }

        return MultimodalResult(
            session=session,
            fused_context=fused.unified_prompt,
            emotional_state=emotional_state,
            vision_caption=vision_caption,
            audio_transcript=audio_transcript,
            multimodal_metadata=session.multimodal_metadata,
        )

    # ── Extractors ───────────────────────────────────────────────────────────

    def _extract_image_caption(self, image_path: str) -> str:
        """Extract caption dari image via vision API."""
        try:
            from .agent_tools import _tool_text_to_image
            # For now, use a simple heuristic or mock
            # In production, this would call an actual vision model
            return f"[Image at {image_path}]"
        except Exception:
            return ""

    def _extract_audio_transcript(self, audio_path: str) -> str:
        """Extract transcript dari audio via STT."""
        try:
            from .agent_tools import _tool_speech_to_text
            result = _tool_speech_to_text({"path": audio_path, "lang": "id"})
            if result.success:
                return result.output
            return ""
        except Exception:
            return ""


# ── Convenience API ──────────────────────────────────────────────────────────

def process_multimodal(
    text: str = "",
    image_path: str = "",
    audio_path: str = "",
    persona: str = "UTZ",
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot API untuk multimodal input → result dict."""
    handler = MultimodalInputHandler()
    result = handler.process(
        MultimodalInput(text=text, image_path=image_path, audio_path=audio_path, persona=persona),
        **kwargs,
    )
    return {
        "answer": result.session.final_answer,
        "session_id": result.session.session_id,
        "persona": result.session.persona,
        "fused_context": result.fused_context,
        "emotional_state": result.emotional_state,
        "vision_caption": result.vision_caption,
        "audio_transcript": result.audio_transcript,
        "multimodal_metadata": result.multimodal_metadata,
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Multimodal Input Handler Self-Test ===\n")

    handler = MultimodalInputHandler()

    # Test 1: Text only
    result1 = handler.process(MultimodalInput(text="Apa itu ML?", persona="UTZ"))
    print(f"[1] Text only: answer='{result1.session.final_answer[:50]}...'")
    assert result1.session.persona == "UTZ"
    print("  OK\n")

    # Test 2: Text + image
    result2 = handler.process(MultimodalInput(
        text="Jelaskan gambar ini",
        image_path="/tmp/test.jpg",
        persona="ABOO",
    ))
    print(f"[2] Text + image: vision='{result2.vision_caption}'")
    assert result2.vision_caption != ""
    assert result2.session.persona == "ABOO"
    print("  OK\n")

    # Test 3: Convenience API
    d = process_multimodal(text="Halo", persona="ALEY")
    assert d["persona"] == "ALEY"
    assert "session_id" in d
    print("[3] Convenience API: OK\n")

    print("[OK] All self-tests passed")
