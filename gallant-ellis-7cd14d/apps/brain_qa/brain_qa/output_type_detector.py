"""
output_type_detector.py — Sprint 5 (Adaptive Output / Pencipta)

Visi bos: SIDIX bukan execute perintah saja, tapi CIPTAKAN. Output bisa
adaptive: text / code / image_prompt / video_storyboard / 3d_prompt / audio.

Foundation Adobe-of-Indonesia: setiap query → detect intent → pilih output
modality yang paling appropriate. SIDIX tidak harus selalu jawab text.

Pattern:
  query → detect_output_type() → enum
  - "text"           — plain answer (default)
  - "code"           — programming task
  - "image_prompt"   — wants visual generation
  - "video_storyboard" — multi-scene video planning
  - "audio_tts"      — wants spoken response
  - "3d_prompt"      — 3D asset generation
  - "structured"     — table/list/dataframe

Implementasi awal: heuristic regex (no LLM, fast). Phase 2: ML classifier
trained on user feedback.

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OutputType(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE_PROMPT = "image_prompt"
    VIDEO_STORYBOARD = "video_storyboard"
    AUDIO_TTS = "audio_tts"
    THREE_D_PROMPT = "3d_prompt"
    STRUCTURED = "structured"


@dataclass
class OutputDetection:
    output_type: OutputType
    confidence: float  # 0.0 - 1.0
    reason: str
    suggested_tools: list[str]


# ── Heuristic patterns (Phase 1) ──────────────────────────────────────

_IMAGE_INTENT_RE = re.compile(
    r"\b(buat|bikin|generate|create|gambar(kan)?|render|lukis(kan)?|design|"
    r"sketsa|illustrate|paint|draw)\b.*?\b(gambar|foto|ilustrasi|image|picture|"
    r"visual|artwork|poster|lukisan|desain|illustration|painting|sketch|logo)\b"
    r"|"
    r"\b(gambar|foto|ilustrasi|image|artwork|logo|poster)\b.*?\b(buat|bikin|generate|create)\b",
    re.IGNORECASE,
)

_VIDEO_INTENT_RE = re.compile(
    r"\b(buat|bikin|generate|create)\b.*?\b(video|film|reel|tiktok|youtube|storyboard|"
    r"animasi|animation|movie)\b",
    re.IGNORECASE,
)

_AUDIO_TTS_RE = re.compile(
    r"\b(baca(kan)?|read aloud|tts|text.to.speech|voice over|narasi|audio|suara)\b",
    re.IGNORECASE,
)

_3D_INTENT_RE = re.compile(
    r"\b(model 3d|3d model|three.?dimensional|blender|sketchup|maya|unreal|unity|"
    r"3d asset|mesh|geometry|sculpting|3d render)\b",
    re.IGNORECASE,
)

_CODE_INTENT_RE = re.compile(
    r"\b(tulis|buat|bikin|write|create|implement)\b.*?\b(fungsi|function|kode|code|"
    r"script|algoritma|algorithm|class|method|component|api|endpoint|sql|query)\b"
    r"|"
    r"\b(def |class |function |const |async |import |from |#include)\b"
    r"|"
    r"```",
    re.IGNORECASE,
)

_STRUCTURED_INTENT_RE = re.compile(
    r"\b(tabel|table|list|daftar|spreadsheet|csv|json|comparison|bandingkan).*?"
    r"\b(berapa|kolom|baris|item|attribute|field)\b"
    r"|"
    r"\b(buat|bikin|generate|create)\b.*?\b(tabel|table|list|matriks|matrix|chart)\b",
    re.IGNORECASE,
)


def detect_output_type(query: str) -> OutputDetection:
    """Detect output type yang paling sesuai untuk query.

    Args:
        query: pertanyaan/perintah user

    Returns:
        OutputDetection dengan type + confidence + reason + suggested_tools.
    """
    if not query or not query.strip():
        return OutputDetection(
            output_type=OutputType.TEXT,
            confidence=1.0,
            reason="empty_query",
            suggested_tools=[],
        )

    q = query.strip()

    # Order matters: more specific first

    # 1. 3D (specific, less ambiguous)
    if _3D_INTENT_RE.search(q):
        return OutputDetection(
            output_type=OutputType.THREE_D_PROMPT,
            confidence=0.85,
            reason="3d_keywords_detected",
            suggested_tools=["mighan_3d_prompt", "image_gen_with_depth"],
        )

    # 2. Video storyboard
    if _VIDEO_INTENT_RE.search(q):
        return OutputDetection(
            output_type=OutputType.VIDEO_STORYBOARD,
            confidence=0.8,
            reason="video_keywords_detected",
            suggested_tools=["video_storyboard_planner", "scene_decomposer"],
        )

    # 3. Image (relatively common)
    if _IMAGE_INTENT_RE.search(q):
        return OutputDetection(
            output_type=OutputType.IMAGE_PROMPT,
            confidence=0.85,
            reason="image_keywords_detected",
            suggested_tools=["image_gen", "prompt_engineer_for_sdxl"],
        )

    # 4. Audio/TTS
    if _AUDIO_TTS_RE.search(q):
        return OutputDetection(
            output_type=OutputType.AUDIO_TTS,
            confidence=0.75,
            reason="audio_keywords_detected",
            suggested_tools=["tts_generator"],
        )

    # 5. Code
    if _CODE_INTENT_RE.search(q):
        return OutputDetection(
            output_type=OutputType.CODE,
            confidence=0.8,
            reason="code_keywords_detected",
            suggested_tools=["code_sandbox", "syntax_validator"],
        )

    # 6. Structured (table/list)
    if _STRUCTURED_INTENT_RE.search(q):
        return OutputDetection(
            output_type=OutputType.STRUCTURED,
            confidence=0.7,
            reason="structured_keywords_detected",
            suggested_tools=["table_generator"],
        )

    # Default: text
    return OutputDetection(
        output_type=OutputType.TEXT,
        confidence=0.95,
        reason="default_text",
        suggested_tools=[],
    )


# ── Public API ────────────────────────────────────────────────────────


def adaptive_output_hint_for_synthesizer(detection: OutputDetection) -> str:
    """Generate hint untuk cognitive_synthesizer berdasarkan detected output type.

    Synthesizer akan format output sesuai modality yang appropriate.
    """
    hints = {
        OutputType.TEXT: "",
        OutputType.CODE: (
            "User minta KODE. Output kode dalam markdown code block dengan "
            "language tag eksplisit. Tambahkan complexity Big-O dan edge cases "
            "checklist (per ABOO deliverable format)."
        ),
        OutputType.IMAGE_PROMPT: (
            "User minta GAMBAR. Output:\n"
            "1. Brief image prompt yang optimized untuk SDXL/FLUX (subject + style + "
            "lighting + composition + technical params).\n"
            "2. Tag <SIDIX_IMAGE_PROMPT>...</SIDIX_IMAGE_PROMPT> wrapper supaya "
            "frontend bisa detect + invoke image_gen tool.\n"
            "3. Tambahan: 2 alternatif prompt dengan style berbeda."
        ),
        OutputType.VIDEO_STORYBOARD: (
            "User minta VIDEO. Output multi-scene storyboard:\n"
            "Scene 1: [duration] - [visual description] - [audio/dialog]\n"
            "Scene 2: ...\n"
            "Tag <SIDIX_VIDEO_STORYBOARD>...</SIDIX_VIDEO_STORYBOARD> wrapper."
        ),
        OutputType.AUDIO_TTS: (
            "User minta AUDIO/TTS. Output text yang akan di-speech-synthesize. "
            "Gunakan natural punctuation untuk pacing. Tag <SIDIX_TTS>...</SIDIX_TTS>."
        ),
        OutputType.THREE_D_PROMPT: (
            "User minta 3D. Output:\n"
            "1. Mesh description (geometry + topology)\n"
            "2. Material/shader spec\n"
            "3. Animation rig hint (kalau ada)\n"
            "Tag <SIDIX_3D_PROMPT>...</SIDIX_3D_PROMPT>."
        ),
        OutputType.STRUCTURED: (
            "User minta STRUCTURED data (tabel/list). Output dalam markdown table "
            "atau bullet list yang scannable. Header eksplisit."
        ),
    }
    return hints.get(detection.output_type, "")


__all__ = [
    "OutputType",
    "OutputDetection",
    "detect_output_type",
    "adaptive_output_hint_for_synthesizer",
]
