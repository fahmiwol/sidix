"""
sensor_hub.py — Registry semua INDRA SIDIX (Embodied AI direction, 2026-04-25)

Metafora manusia:
  - Telinga (audio_in): mendengar user via microphone/STT
  - Mata (vision_in): melihat via screenshot/image analyze/OCR
  - Mulut (audio_out): berbicara via TTS/Piper
  - Tangan kanan/kiri (action): call tools paralel, multi-agent spawn
  - Membaca (text_read): corpus BM25, web_fetch, pdf_extract
  - Menulis (text_write): workspace_write, code_sandbox execution
  - Perasaan (emotional): emotional_tone_engine (Kimi paralel)
  - Kesadaran diri (self): constitution, hygiene, CSC

Non-destructive: tidak menduplikasi fungsi, hanya registry + status aggregator.
Digunakan oleh endpoint `/sidix/senses/status` untuk real-time dashboard.
"""

from __future__ import annotations

import concurrent.futures
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

log = logging.getLogger("sidix.sensor_hub")


class SenseStatus(str, Enum):
    ACTIVE = "active"       # siap pakai, fungsi terpasang
    INACTIVE = "inactive"   # terpasang tapi tidak di-enable (e.g., no mic)
    BROKEN = "broken"       # error terdeteksi
    UNKNOWN = "unknown"     # belum di-probe


@dataclass
class Sense:
    """Satu indra SIDIX — metadata + probe function."""
    slug: str
    body_part: str          # "ear" | "eye" | "mouth" | "hand_left" | ...
    description: str
    check_fn: Optional[Callable[[], tuple[bool, str]]] = None
    capabilities: list[str] = field(default_factory=list)
    status: SenseStatus = SenseStatus.UNKNOWN
    last_used_iso: str = ""
    notes: str = ""

    def probe(self) -> dict[str, Any]:
        """Jalankan check_fn, update status + notes, return snapshot."""
        if self.check_fn is None:
            self.status = SenseStatus.UNKNOWN
            self.notes = "no probe function registered"
        else:
            try:
                ok, detail = self.check_fn()
                self.status = SenseStatus.ACTIVE if ok else SenseStatus.INACTIVE
                self.notes = detail
            except Exception as e:
                self.status = SenseStatus.BROKEN
                self.notes = f"probe error: {type(e).__name__}: {str(e)[:100]}"
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "body_part": self.body_part,
            "description": self.description,
            "status": self.status.value,
            "capabilities": list(self.capabilities),
            "last_used_iso": self.last_used_iso,
            "notes": self.notes,
        }


# ── Default probe functions (non-blocking) ────────────────────────────────────

def _probe_tts() -> tuple[bool, str]:
    """Check TTS availability (Piper/gTTS)."""
    try:
        from .tts_piper import is_available as piper_ok
        if piper_ok():
            return True, "Piper TTS ready"
    except Exception:
        pass
    try:
        import gtts  # noqa: F401
        return True, "gTTS fallback ready"
    except Exception:
        pass
    return False, "no TTS backend"


def _probe_stt() -> tuple[bool, str]:
    """Check STT availability."""
    try:
        from .audio_listen import is_listener_available
        return (is_listener_available(), "audio listen module")
    except Exception as e:
        return False, f"stt module unavailable: {type(e).__name__}"


def _probe_vision_analyze() -> tuple[bool, str]:
    """Check image analyze / OCR."""
    try:
        from .image_analyze import is_available as img_ok
        return (img_ok(), "image analyze + OCR")
    except Exception:
        return False, "image_analyze module missing"


def _probe_vision_gen() -> tuple[bool, str]:
    """Check image generation."""
    try:
        from .image_generate import is_available as gen_ok
        return (gen_ok(), "image generation")
    except Exception:
        return False, "image_generate module missing"


def _probe_corpus_read() -> tuple[bool, str]:
    """Check corpus search capability."""
    try:
        from .corpus import get_corpus_stats
        stats = get_corpus_stats()
        count = stats.get("doc_count", 0) if isinstance(stats, dict) else 0
        return (count > 0, f"corpus ready, {count} docs")
    except Exception as e:
        return False, f"corpus probe: {type(e).__name__}"


def _probe_web_read() -> tuple[bool, str]:
    """Check web_search + web_fetch tool availability."""
    try:
        from .agent_tools import TOOL_REGISTRY
        has_search = "web_search" in TOOL_REGISTRY
        has_fetch = "web_fetch" in TOOL_REGISTRY
        if has_search and has_fetch:
            return True, "web_search + web_fetch registered"
        return False, f"partial: search={has_search} fetch={has_fetch}"
    except Exception as e:
        return False, f"tool registry probe: {type(e).__name__}"


def _probe_workspace_write() -> tuple[bool, str]:
    """Check workspace write + code sandbox."""
    try:
        from .agent_tools import TOOL_REGISTRY
        has_write = "workspace_write" in TOOL_REGISTRY
        has_code = "code_sandbox" in TOOL_REGISTRY
        if has_write and has_code:
            return True, "workspace + code sandbox ready"
        return False, f"partial: write={has_write} code={has_code}"
    except Exception as e:
        return False, f"workspace probe: {type(e).__name__}"


def _probe_tool_action() -> tuple[bool, str]:
    """Check tool registry (tangan SIDIX)."""
    try:
        from .agent_tools import TOOL_REGISTRY
        n = len(TOOL_REGISTRY)
        return (n >= 20, f"{n} tools registered")
    except Exception as e:
        return False, f"tool registry: {type(e).__name__}"


def _probe_self_awareness() -> tuple[bool, str]:
    """Check constitution + hygiene + CSC (kesadaran diri)."""
    try:
        from .agent_react import _apply_hygiene, _cognitive_self_check, _self_critique_lite
        from .sidix_constitution import critique_response
        return True, "constitution + hygiene + CSC + critique ready"
    except Exception as e:
        return False, f"self-awareness: {type(e).__name__}"


def _probe_emotional_tone() -> tuple[bool, str]:
    """Check emotional tone engine (Jiwa Sprint Phase 2, Kimi)."""
    try:
        from .emotional_tone_engine import detect_emotion, adapt_tone
        # Quick functional check
        state = detect_emotion("wow keren banget, akhirnya berhasil!")
        adapt = adapt_tone(state)
        assert state.dominant_emotion == "excited"
        return True, f"emotional tone engine ready ({state.dominant_emotion})"
    except Exception as e:
        return False, f"emotional_tone_engine: {type(e).__name__}"


def _probe_persona_voice() -> tuple[bool, str]:
    """Check persona voice calibration (Jiwa Sprint Phase 2, Kimi)."""
    try:
        from .persona_voice_calibration import get_voice_store, get_voice_hint
        store = get_voice_store()
        hint = store.get_voice_hint("anon", "UTZ")
        return True, "persona voice calibration ready"
    except Exception as e:
        return False, f"persona_voice_calibration: {type(e).__name__}"


def _probe_creative_imagination() -> tuple[bool, str]:
    """Check creative writing engine (Jiwa Sprint Phase 2, Kimi)."""
    try:
        from .creative_writing import CreativeWritingEngine, CreativeForm
        engine = CreativeWritingEngine(persona="UTZ")
        brief = engine.generate(
            form=CreativeForm.POETRY,
            prompt="haiku tentang senja",
        )
        assert brief.poetry_spec is not None
        return True, f"creative imagination ready ({brief.poetry_spec.form.value})"
    except Exception as e:
        return False, f"creative_writing: {type(e).__name__}"


# ── Canonical registry — ini peta tubuh SIDIX ─────────────────────────────────

_REGISTRY: dict[str, Sense] = {
    # INDRA — Input
    "audio_in": Sense(
        slug="audio_in",
        body_part="ear",
        description="Telinga — mendengar user via microphone/STT",
        check_fn=_probe_stt,
        capabilities=["listen", "transcribe", "voice_command"],
    ),
    "vision_in": Sense(
        slug="vision_in",
        body_part="eye",
        description="Mata — melihat via image analyze, OCR, screenshot",
        check_fn=_probe_vision_analyze,
        capabilities=["analyze_image", "ocr", "describe_scene"],
    ),
    "text_read": Sense(
        slug="text_read",
        body_part="eye",
        description="Membaca — corpus BM25, pdf_extract",
        check_fn=_probe_corpus_read,
        capabilities=["corpus_search", "read_chunk", "list_sources"],
    ),
    "web_read": Sense(
        slug="web_read",
        body_part="eye",
        description="Membaca web — web_search (DuckDuckGo) + web_fetch",
        check_fn=_probe_web_read,
        capabilities=["web_search", "web_fetch", "html_to_text"],
    ),

    # INDRA — Output
    "audio_out": Sense(
        slug="audio_out",
        body_part="mouth",
        description="Mulut — bicara via TTS (Piper/gTTS)",
        check_fn=_probe_tts,
        capabilities=["tts_synthesize", "stream_audio"],
    ),
    "vision_gen": Sense(
        slug="vision_gen",
        body_part="hand_right",
        description="Tangan kanan — generate gambar (SDXL/Flux)",
        check_fn=_probe_vision_gen,
        capabilities=["text_to_image", "image_edit"],
    ),
    "text_write": Sense(
        slug="text_write",
        body_part="hand_left",
        description="Tangan kiri — tulis file + execute code",
        check_fn=_probe_workspace_write,
        capabilities=["workspace_write", "code_sandbox", "git_commit_helper"],
    ),
    "tool_action": Sense(
        slug="tool_action",
        body_part="hand_right",
        description="Tangan — 45+ tools (action space SIDIX)",
        check_fn=_probe_tool_action,
        capabilities=["react_loop", "parallel_tools", "tool_registry"],
    ),

    # RASA / KESADARAN
    "emotional_tone": Sense(
        slug="emotional_tone",
        body_part="heart",
        description="Perasaan — emotional_tone_engine (Kimi paralel)",
        check_fn=_probe_emotional_tone,
        capabilities=["detect_tone", "adapt_response"],
    ),
    "persona_voice": Sense(
        slug="persona_voice",
        body_part="voice",
        description="Nada bicara — persona_voice_calibration (Kimi paralel)",
        check_fn=_probe_persona_voice,
        capabilities=["voice_per_persona", "register_adjust"],
    ),
    "creative_imagination": Sense(
        slug="creative_imagination",
        body_part="mind",
        description="Imajinasi — creative writing engine (Jiwa Sprint Phase 2, Kimi)",
        check_fn=_probe_creative_imagination,
        capabilities=["short_story", "poetry", "screenplay", "worldbuilding", "character_profile"],
    ),
    "self_awareness": Sense(
        slug="self_awareness",
        body_part="mind",
        description="Kesadaran diri — constitution + hygiene + CSC",
        check_fn=_probe_self_awareness,
        capabilities=["critique", "epistemic_check", "output_hygiene"],
    ),
}


def list_senses() -> list[Sense]:
    """Return all registered senses (unprobed)."""
    return list(_REGISTRY.values())


def probe_all(parallel: bool = True) -> dict[str, Any]:
    """
    Jalankan probe semua sense, return snapshot lengkap.

    Args:
        parallel: Jika True (default), probe semua sense secara parallel
                  menggunakan ThreadPoolExecutor. Jika False, sequential.

    Returns:
      {
        "total": int,
        "active": int,
        "inactive": int,
        "broken": int,
        "by_body": {"ear": [...], "eye": [...], ...},
        "senses": [...]  # list of sense snapshots
      }
    """
    senses = list(_REGISTRY.values())

    if parallel and len(senses) > 1:
        # Parallel probe using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(senses)) as executor:
            future_to_sense = {
                executor.submit(sense.probe): sense
                for sense in senses
            }
            snapshots = []
            for future in concurrent.futures.as_completed(future_to_sense):
                snapshots.append(future.result())
    else:
        # Sequential fallback
        snapshots = [sense.probe() for sense in senses]

    by_body: dict[str, list] = {}
    counts = {"active": 0, "inactive": 0, "broken": 0, "unknown": 0}

    for snap in snapshots:
        counts[snap["status"]] = counts.get(snap["status"], 0) + 1
        by_body.setdefault(snap["body_part"], []).append(snap["slug"])

    return {
        "total": len(snapshots),
        "active": counts["active"],
        "inactive": counts["inactive"],
        "broken": counts["broken"],
        "unknown": counts["unknown"],
        "by_body": by_body,
        "senses": snapshots,
    }


def mark_sense_used(slug: str, when_iso: str = "") -> None:
    """Update last_used_iso (dipanggil saat sense dipakai di runtime)."""
    if slug in _REGISTRY:
        if not when_iso:
            from datetime import datetime, timezone
            when_iso = datetime.now(timezone.utc).isoformat()
        _REGISTRY[slug].last_used_iso = when_iso


def get_sense(slug: str) -> Optional[Sense]:
    return _REGISTRY.get(slug)


def health_summary() -> dict[str, Any]:
    """Ringkasan satu-liner — untuk health endpoint."""
    result = probe_all()
    return {
        "senses_total": result["total"],
        "senses_active": result["active"],
        "senses_inactive": result["inactive"],
        "senses_broken": result["broken"],
        "body_parts_active": sorted(set(
            body for body, slugs in result["by_body"].items()
            if any(_REGISTRY[s].status == SenseStatus.ACTIVE for s in slugs)
        )),
    }
