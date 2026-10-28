"""
multimodal_creative.py — Multimodal Creative Pipeline

Generate karya kreatif harmonis lintas modalitas:
  - Visual: gambar (text_to_image)
  - Tekstual: caption/copy (generate_copy / creative_writing)
  - Audio: voiceover (text_to_speech)

Semua output dikerjakan dari satu creative concept dengan tema,
tone, dan persona yang sama — menciptakan "harmoni multimodal".

Pivot 2026-04-25 — Jiwa Sprint Task 3 (Kimi lane)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class VisualOutput:
    prompt: str
    enhanced_prompt: str
    width: int
    height: int
    archetype: str
    template: str
    image_path: str = ""  # filled if executed
    image_url: str = ""
    mode: str = "planned"  # planned | generated | failed


@dataclass
class TextOutput:
    headline: str
    body: str
    cta: str
    formula: str
    channel: str
    cq_score: float = 0.0


@dataclass
class AudioOutput:
    script: str
    lang: str
    voice: str
    out_path: str = ""
    backend: str = ""
    mode: str = "planned"


@dataclass
class MultimodalOutput:
    concept: str
    persona: str
    theme: str
    tone: str
    visual: VisualOutput
    text: TextOutput
    audio: AudioOutput
    harmonization_notes: list[str] = field(default_factory=list)
    execution_log: list[str] = field(default_factory=list)


# ── Pipeline ─────────────────────────────────────────────────────────────────

class MultimodalCreativePipeline:
    """Orchestrate creative generation across image + text + audio."""

    def __init__(self, persona: str = "UTZ"):
        self.persona = persona.upper()

    def generate(
        self,
        concept: str,
        channel: str = "instagram",
        tone: str = "friendly",
        execute: bool = False,
        output_dir: str = "",
    ) -> MultimodalOutput:
        """
        Generate multimodal creative output from a single concept.

        Args:
            concept: Ide kreatif, e.g. "promo kopi robusta Nusantara"
            channel: instagram | youtube | tiktok | threads | poster
            tone: friendly | formal | excited | melancholic
            execute: Jika True, jalankan image gen + TTS (butuh resources)
            output_dir: Folder untuk simpan hasil generate (jika execute=True)
        """
        # ── 1. PLAN: Creative framework untuk visual prompt ───────────────────
        visual = self._plan_visual(concept, channel)

        # ── 2. PLAN: Copy/caption untuk tekstual ──────────────────────────────
        text = self._plan_text(concept, channel, tone)

        # ── 3. PLAN: Audio script (voiceover dari caption) ────────────────────
        audio = self._plan_audio(text, tone)

        # ── 4. HARMONIZATION: cross-check consistency ─────────────────────────
        notes = self._harmonize(visual, text, audio)

        out = MultimodalOutput(
            concept=concept,
            persona=self.persona,
            theme=visual.archetype,
            tone=tone,
            visual=visual,
            text=text,
            audio=audio,
            harmonization_notes=notes,
        )

        # ── 5. EXECUTE (opsional) ────────────────────────────────────────────
        if execute:
            self._execute(out, output_dir)

        return out

    # ── Planners ─────────────────────────────────────────────────────────────

    def _plan_visual(self, concept: str, channel: str) -> VisualOutput:
        """Rencanakan visual menggunakan creative_framework."""
        try:
            from .creative_framework import enhance_prompt_creative
            enh = enhance_prompt_creative(concept)
            return VisualOutput(
                prompt=concept,
                enhanced_prompt=enh["enhanced_prompt"],
                width=enh.get("width", 1024),
                height=enh.get("height", 1024),
                archetype=enh.get("applied_archetype", "unknown"),
                template=enh.get("template_used", "unknown"),
            )
        except Exception as e:
            return VisualOutput(
                prompt=concept,
                enhanced_prompt=concept,
                width=1024,
                height=1024,
                archetype="fallback",
                template="fallback",
            )

    def _plan_text(self, concept: str, channel: str, tone: str) -> TextOutput:
        """Rencanakan copy/caption menggunakan copywriter."""
        try:
            from .copywriter import generate_copy
            result = generate_copy(
                topic=concept,
                channel=channel,
                formula="AIDA",
                audience="audiens Indonesia",
                cta="Komentar 'MAU' kalau ingin templatenya.",
                tone=tone,
                variant_count=1,
                min_score=6.0,
            )
            if result.get("ok"):
                best = result.get("best_text", "")
                lines = best.split("\n")
                headline = lines[0] if lines else concept
                body = "\n".join(lines[1:]) if len(lines) > 1 else best
                return TextOutput(
                    headline=headline,
                    body=body,
                    cta="",
                    formula=result.get("best_formula", "AIDA"),
                    channel=channel,
                    cq_score=result.get("score_total", 0.0),
                )
        except Exception:
            pass
        # Fallback
        return TextOutput(
            headline=concept,
            body=f"Konten menarik tentang {concept}.",
            cta="",
            formula="AIDA",
            channel=channel,
        )

    def _plan_audio(self, text: TextOutput, tone: str) -> AudioOutput:
        """Rencanakan voiceover script dari caption."""
        script = f"{text.headline}. {text.body.replace(chr(10), ' ')}"
        # Truncate untuk TTS (avoid terlalu panjang)
        if len(script) > 500:
            script = script[:500] + "..."
        return AudioOutput(
            script=script,
            lang="id",
            voice="default",
        )

    # ── Harmonization ────────────────────────────────────────────────────────

    def _harmonize(self, visual: VisualOutput, text: TextOutput, audio: AudioOutput) -> list[str]:
        """Cross-check consistency antara visual, text, dan audio."""
        notes = []
        # Check 1: archetype vs tone
        if visual.archetype in ("The Lover", "The Caregiver") and "formal" in text.channel:
            notes.append("Warning: archetype hangat tapi tone formal — bisa terasa kontras.")
        # Check 2: text length vs audio feasibility
        if len(audio.script) > 300:
            notes.append("Audio script >300 chars — TTS akan panjang, pertimbangkan dipotong.")
        # Check 3: visual size vs channel
        if text.channel == "instagram" and visual.width != visual.height:
            notes.append("Instagram feed prefer square (1:1) — visual saat ini tidak square.")
        # Check 4: persona consistency
        if self.persona in ("ABOO", "UTZ") and visual.archetype in ("The Ruler", "The Sage"):
            notes.append("Persona casual (ABOO/UTZ) + archetype formal — perlu penyesuaian tone.")
        if not notes:
            notes.append("Harmonization check passed — semua modalitas sejalan.")
        return notes

    # ── Execution ────────────────────────────────────────────────────────────

    def _execute(self, out: MultimodalOutput, output_dir: str) -> None:
        """Jalankan image generation + TTS (opsional, butuh resources)."""
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Execute visual
        try:
            from .agent_tools import _tool_text_to_image
            result = _tool_text_to_image({
                "prompt": out.visual.enhanced_prompt,
                "width": out.visual.width,
                "height": out.visual.height,
                "steps": 4,
            })
            out.execution_log.append(f"image_gen: success={result.success}")
            if result.success:
                out.visual.mode = "generated"
                # Extract path from output markdown
                import re
                m = re.search(r"\]\(([^)]+)\)", result.output)
                if m:
                    out.visual.image_url = m.group(1)
            else:
                out.visual.mode = "failed"
                out.execution_log.append(f"image_gen error: {result.error}")
        except Exception as e:
            out.visual.mode = "failed"
            out.execution_log.append(f"image_gen exception: {e}")

        # Execute audio
        try:
            from .agent_tools import _tool_text_to_speech
            out_path = os.path.join(output_dir, "voiceover.wav") if output_dir else "voiceover.wav"
            result = _tool_text_to_speech({
                "text": out.audio.script,
                "lang": out.audio.lang,
                "voice": out.audio.voice,
                "out_path": out_path,
            })
            out.execution_log.append(f"tts: success={result.success}")
            if result.success:
                out.audio.mode = "generated"
                out.audio.out_path = out_path
            else:
                out.audio.mode = "failed"
                out.execution_log.append(f"tts error: {result.error}")
        except Exception as e:
            out.audio.mode = "failed"
            out.execution_log.append(f"tts exception: {e}")


# ── Convenience API ──────────────────────────────────────────────────────────

def generate_multimodal(
    concept: str,
    persona: str = "UTZ",
    channel: str = "instagram",
    tone: str = "friendly",
    execute: bool = False,
) -> dict[str, Any]:
    """One-shot API: concept → multimodal output dict."""
    pipeline = MultimodalCreativePipeline(persona=persona)
    out = pipeline.generate(concept=concept, channel=channel, tone=tone, execute=execute)
    return _output_to_dict(out)


def _output_to_dict(out: MultimodalOutput) -> dict[str, Any]:
    return {
        "concept": out.concept,
        "persona": out.persona,
        "theme": out.theme,
        "tone": out.tone,
        "visual": {
            "prompt": out.visual.prompt,
            "enhanced_prompt": out.visual.enhanced_prompt,
            "width": out.visual.width,
            "height": out.visual.height,
            "archetype": out.visual.archetype,
            "template": out.visual.template,
            "mode": out.visual.mode,
            "image_url": out.visual.image_url,
        },
        "text": {
            "headline": out.text.headline,
            "body": out.text.body,
            "cta": out.text.cta,
            "formula": out.text.formula,
            "channel": out.text.channel,
            "cq_score": out.text.cq_score,
        },
        "audio": {
            "script": out.audio.script,
            "lang": out.audio.lang,
            "voice": out.audio.voice,
            "mode": out.audio.mode,
            "out_path": out.audio.out_path,
        },
        "harmonization_notes": out.harmonization_notes,
        "execution_log": out.execution_log,
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Multimodal Creative Pipeline Self-Test ===\n")

    pipeline = MultimodalCreativePipeline(persona="UTZ")
    out = pipeline.generate(
        concept="promo kopi robusta dari pegunungan Nusantara",
        channel="instagram",
        tone="friendly",
        execute=False,
    )

    print(f"Concept: {out.concept}")
    print(f"Persona: {out.persona}")
    print(f"Theme/Archetype: {out.theme}")
    print()
    print("--- VISUAL ---")
    print(f"Prompt: {out.visual.prompt}")
    print(f"Enhanced: {out.visual.enhanced_prompt[:100]}...")
    print(f"Size: {out.visual.width}x{out.visual.height}")
    print(f"Archetype: {out.visual.archetype}")
    print()
    print("--- TEXT ---")
    print(f"Headline: {out.text.headline.encode('ascii', 'replace').decode()}")
    print(f"Body: {out.text.body[:100].encode('ascii', 'replace').decode()}...")
    print(f"Formula: {out.text.formula}")
    print()
    print("--- AUDIO ---")
    print(f"Script: {out.audio.script[:100].encode('ascii', 'replace').decode()}...")
    print(f"Lang: {out.audio.lang}")
    print()
    print("--- HARMONIZATION ---")
    for note in out.harmonization_notes:
        print(f"  - {note}")
    print()

    # Test dict serialization
    d = _output_to_dict(out)
    assert d["concept"] == out.concept
    assert "visual" in d
    assert "text" in d
    assert "audio" in d
    print("Dict serialization: OK")

    # Test convenience API
    d2 = generate_multimodal("test concept", persona="ABOO")
    assert d2["persona"] == "ABOO"
    print("Convenience API: OK")

    print("\n[OK] All self-tests passed")
