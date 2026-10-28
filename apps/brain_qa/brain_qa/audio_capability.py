"""
audio_capability.py — SIDIX Audio Capability Registry
======================================================
Registry untuk tool/skill audio yang dapat dipanggil SIDIX melalui ReAct agent.
Setiap tool punya fallback-instructions bila library pihak-ketiga (whisper,
librosa, demucs) tidak terpasang — sesuai aturan: tidak auto-install heavy deps.

Research notes terkait:
  - 84 fondasi akustik
  - 85 representasi digital
  - 86 ASR
  - 87 TTS + voice cloning
  - 88 MIR
  - 89 generasi musik
  - 90 audio LLM multimodal
  - 91 Islam: tajwid, qira'at, maqam
  - 92 master index + arsitektur e2e

Aturan SIDIX (lihat AGENTS.md):
  * JANGAN import openai / @google/genai / anthropic dari modul inference SIDIX.
  * Semua tool harus return dict berbentuk:
      { 'ok': bool, 'data': any, 'fallback_instructions': str, 'citations': list }
  * Citations merujuk ke research notes (path relatif brain/public/research_notes/).
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ── Citation Helpers ──────────────────────────────────────────────────────────

_RESEARCH_DIR = "brain/public/research_notes"

def _cite(*note_ids: int) -> list[str]:
    """Return list of research-note file paths for given IDs."""
    mapping = {
        84: "84_audio_fondasi_akustik.md",
        85: "85_audio_representasi_digital.md",
        86: "86_audio_asr_speech_recognition.md",
        87: "87_audio_tts_voice_cloning.md",
        88: "88_audio_mir_music_understanding.md",
        89: "89_audio_generasi_musik.md",
        90: "90_audio_llm_multimodal.md",
        91: "91_audio_islam_tajwid_qiraat.md",
        92: "92_audio_capability_track.md",
    }
    return [f"{_RESEARCH_DIR}/{mapping[n]}" for n in note_ids if n in mapping]


def _has_module(name: str) -> bool:
    """Cek apakah module tersedia tanpa import side-effect."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _ok(data: Any, *, citations: Optional[list[str]] = None,
        note: str = "") -> dict:
    return {
        "ok": True,
        "data": data,
        "fallback_instructions": note,
        "citations": citations or [],
    }


def _fallback(instructions: str, *, citations: Optional[list[str]] = None,
              data: Any = None) -> dict:
    return {
        "ok": False,
        "data": data,
        "fallback_instructions": instructions,
        "citations": citations or [],
    }


# ── Tool Implementations ──────────────────────────────────────────────────────

def transcribe_audio(path: str, lang: str = "id") -> dict:
    """
    ASR: konversi audio → teks.
    Prioritas: faster-whisper → openai-whisper → fallback instruction.
    Research note: 86 (ASR).
    """
    cites = _cite(86, 84, 85)
    if not os.path.exists(path):
        return _fallback(f"File tidak ditemukan: {path}", citations=cites)

    # Try faster-whisper (lebih cepat, CTranslate2)
    if _has_module("faster_whisper"):
        try:
            from faster_whisper import WhisperModel  # type: ignore
            model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, info = model.transcribe(path, language=lang, beam_size=5)
            texts = []
            for seg in segments:
                texts.append({
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": seg.text.strip(),
                })
            return _ok({
                "backend": "faster-whisper",
                "language": info.language,
                "duration": info.duration,
                "segments": texts,
                "text": " ".join(s["text"] for s in texts),
            }, citations=cites)
        except Exception as exc:  # noqa: BLE001
            return _fallback(f"faster-whisper gagal: {exc}. "
                             "Coba install ulang atau pakai whisper resmi.",
                             citations=cites)

    # Fallback ke openai-whisper (library open-source, BUKAN OpenAI API)
    if _has_module("whisper"):
        try:
            import whisper  # type: ignore  # lib open-source standalone
            model = whisper.load_model("small")
            result = model.transcribe(path, language=lang)
            return _ok({
                "backend": "openai-whisper",
                "language": result.get("language", lang),
                "text": result.get("text", "").strip(),
                "segments": result.get("segments", []),
            }, citations=cites)
        except Exception as exc:  # noqa: BLE001
            return _fallback(f"openai-whisper gagal: {exc}", citations=cites)

    return _fallback(
        "Library ASR belum terpasang. Jalankan salah satu:\n"
        "  pip install faster-whisper   # recommended, lebih cepat\n"
        "  pip install openai-whisper   # lib open-source standalone\n"
        "Lalu retry tool ini. Untuk Bahasa Indonesia, model 'small' cukup "
        "(CER <5% target, WER <15%). Fine-tune akan menurunkan WER ke 8-12%.",
        citations=cites,
    )


def synthesize_speech(text: str, voice: str = "default",
                      lang: str = "id", out_path: str = "tts_out.wav") -> dict:
    """
    TTS: teks → file audio.
    Prioritas: Coqui-TTS (XTTS) → pyttsx3 → fallback.
    Research note: 87 (TTS + consent).
    """
    cites = _cite(87, 85, 91)

    if not text or len(text) < 1:
        return _fallback("Teks kosong; tidak ada yang disintesis.",
                         citations=cites)

    if voice != "default":
        # Voice cloning butuh consent check yang explicit.
        # Untuk sekarang, blok dan minta flag eksplisit.
        return _fallback(
            f"Voice cloning ke '{voice}' butuh consent explicit. "
            "Hanya jalankan via UI consent-approval. "
            "Lihat note 87 bagian 'Consent by design'.",
            citations=_cite(87, 91),
        )

    # Try Coqui-TTS (XTTS v2 / VITS)
    if _has_module("TTS"):
        try:
            from TTS.api import TTS  # type: ignore
            # Pakai model yang tersedia di HF; MMS-TTS-ind adalah kandidat
            # untuk Bahasa Indonesia.
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts = TTS(model_name, progress_bar=False)
            tts.tts_to_file(text=text, language=lang, file_path=out_path)
            return _ok({
                "backend": "coqui-tts-xtts",
                "out_path": out_path,
                "text_len": len(text),
            }, citations=cites,
               note="Tambahkan watermark AudioSeal post-generation (best practice).")
        except Exception as exc:  # noqa: BLE001
            # jatuh ke pyttsx3
            pass

    if _has_module("pyttsx3"):
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            engine.save_to_file(text, out_path)
            engine.runAndWait()
            return _ok({
                "backend": "pyttsx3",
                "out_path": out_path,
                "text_len": len(text),
                "note": "pyttsx3 robotik, untuk demo; upgrade ke XTTS/F5-TTS untuk produksi.",
            }, citations=cites)
        except Exception as exc:  # noqa: BLE001
            return _fallback(f"pyttsx3 gagal: {exc}", citations=cites)

    return _fallback(
        "Library TTS belum terpasang. Rekomendasi:\n"
        "  pip install TTS             # Coqui XTTS v2, mendukung 17 bahasa termasuk id\n"
        "  pip install pyttsx3         # fallback offline robotik untuk demo\n"
        "Untuk kualitas SOTA: lihat F5-TTS (Chen arXiv:2410.06885) - "
        "butuh GPU 24GB.",
        citations=cites,
    )


def analyze_audio(path: str) -> dict:
    """
    MIR feature extraction: pitch, tempo, duration, spectral centroid, chroma.
    Butuh librosa.
    Research note: 84, 88.
    """
    cites = _cite(84, 88)
    if not os.path.exists(path):
        return _fallback(f"File tidak ditemukan: {path}", citations=cites)

    if not _has_module("librosa"):
        return _fallback(
            "librosa belum terpasang. Jalankan:\n"
            "  pip install librosa soundfile\n"
            "Librosa menyediakan: pitch detection, tempo, STFT, Mel, MFCC, "
            "beat tracking, onset detection.",
            citations=cites,
        )

    try:
        import librosa  # type: ignore
        import numpy as np  # noqa: F401
        y, sr = librosa.load(path, sr=None)
        duration = float(librosa.get_duration(y=y, sr=sr))
        try:
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            tempo_val = float(tempo)
            n_beats = int(len(beats))
        except Exception:
            tempo_val, n_beats = 0.0, 0
        try:
            centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
        except Exception:
            centroid = 0.0
        try:
            rms = float(librosa.feature.rms(y=y).mean())
        except Exception:
            rms = 0.0
        try:
            zcr = float(librosa.feature.zero_crossing_rate(y).mean())
        except Exception:
            zcr = 0.0
        return _ok({
            "backend": "librosa",
            "sample_rate": int(sr),
            "duration_sec": round(duration, 3),
            "tempo_bpm": round(tempo_val, 2),
            "beat_count": n_beats,
            "spectral_centroid": round(centroid, 2),
            "rms": round(rms, 4),
            "zero_crossing_rate": round(zcr, 4),
        }, citations=cites)
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"librosa gagal: {exc}", citations=cites)


def separate_stems(path: str, two_stems: bool = True) -> dict:
    """
    Source separation via Demucs / HTDemucs.
    Research note: 88 (MIR).
    """
    cites = _cite(88, 85)
    if not os.path.exists(path):
        return _fallback(f"File tidak ditemukan: {path}", citations=cites)

    if not _has_module("demucs"):
        return _fallback(
            "demucs belum terpasang. Jalankan:\n"
            "  pip install demucs\n"
            "Demucs (Meta) memisahkan audio ke stem vocals/drums/bass/other. "
            "HTDemucs v4 adalah varian terbaik (6-stem incl piano+guitar).",
            citations=cites,
        )

    # demucs biasanya dipanggil via CLI; di sini kita return guidance
    # tanpa subprocess (aman default, hindari execution asumsi environment).
    cmd = (
        f"demucs {'--two-stems=vocals' if two_stems else ''} \"{path}\""
    )
    return _ok({
        "backend": "demucs",
        "command_to_run": cmd,
        "note": "Jalankan command ini manual atau via subprocess dengan hati-hati.",
    }, citations=cites)


def detect_beat(path: str) -> dict:
    """
    Beat tracking via librosa.beat.beat_track atau madmom.
    Research note: 88.
    """
    cites = _cite(88)
    if not os.path.exists(path):
        return _fallback(f"File tidak ditemukan: {path}", citations=cites)

    if not _has_module("librosa"):
        return _fallback(
            "librosa belum terpasang (pip install librosa). "
            "Untuk beat tracking state-of-the-art gunakan 'madmom' atau 'beat_this'.",
            citations=cites,
        )

    try:
        import librosa  # type: ignore
        y, sr = librosa.load(path, sr=22050)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        return _ok({
            "backend": "librosa.beat.beat_track",
            "tempo_bpm": round(float(tempo), 2),
            "beat_count": int(len(beat_times)),
            "beat_times": [round(float(t), 3) for t in beat_times[:64]],
        }, citations=cites)
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"beat_track gagal: {exc}", citations=cites)


def classify_instrument(path: str) -> dict:
    """
    Instrument recognition stub.
    Arsitektur rekomendasi: HTDemucs → MERT-330M → multi-label sigmoid head.
    Research note: 88.
    """
    cites = _cite(88, 85, 92)
    if not os.path.exists(path):
        return _fallback(f"File tidak ditemukan: {path}", citations=cites)

    # Cek apakah ada model CLAP lokal
    if _has_module("laion_clap") or _has_module("msclap"):
        return _fallback(
            "CLAP detected — butuh kode wrapper yang belum di-implement. "
            "Lihat note 88 untuk stack: HTDemucs → MERT-330M → multi-label head.",
            citations=cites,
        )

    return _fallback(
        "Instrument classifier belum di-implement. Pipeline rekomendasi:\n"
        "  1) pip install demucs laion-clap transformers torchaudio\n"
        "  2) Separation dengan HTDemucs (opsional untuk musik campuran)\n"
        "  3) Embed per-stem dengan MERT-330M (m-a-p/MERT-v1-330M)\n"
        "  4) Fine-tune multi-label sigmoid head di OpenMIC+IRMAS+Slakh+MedleyDB\n"
        "  5) LAION-CLAP sebagai zero-shot pelengkap untuk label terbuka.\n"
        "Untuk musik tradisional Indonesia (gamelan) butuh fine-tune custom — "
        "lihat Kurniawati et al. Data in Brief vol 53/2024.",
        citations=cites,
    )


def validate_tajweed(audio_path: str, reference_ayah: str = "",
                     expected_qiraat: str = "hafs_an_asim") -> dict:
    """
    Stub validasi tajwid ala Tarteel AI.
    Research note: 86 (ASR) + 91 (tajwid rules).

    Return schema:
      {
        'makhraj_score': 0..1,
        'mad_errors': [],
        'idgham_errors': [],
        'overall_tajweed': 0..1,
        'qiraat_detected': str,
        'note': str,
      }
    """
    cites = _cite(91, 86)
    if not os.path.exists(audio_path):
        return _fallback(f"File tidak ditemukan: {audio_path}", citations=cites)

    return _fallback(
        "Validasi tajwid belum di-implement penuh. Pipeline yang direkomendasikan:\n"
        "  1) ASR Whisper-v3 fine-tuned pada Everyayah + Tarteel dataset.\n"
        "  2) Forced alignment huruf hijaiyah (Montreal Forced Aligner + mapping).\n"
        "  3) Classifier tajwid per-aturan (makhraj, sifat, mim/nun sakinah, mad)\n"
        "     sebagai multi-head neural — atau aturan deterministik bila ada "
        "     transkripsi huruf.\n"
        "  4) Output: skor makhraj + daftar error mad/idgham + match qira'at.\n"
        "Catatan syariah: output ini adalah 'alat bantu pendidikan', bukan "
        "pengganti talaqqi.",
        citations=cites,
        data={
            "makhraj_score": None,
            "mad_errors": [],
            "idgham_errors": [],
            "overall_tajweed": None,
            "qiraat_detected": expected_qiraat,
            "reference_ayah": reference_ayah,
        },
    )


def detect_maqam(audio_path: str) -> dict:
    """
    Stub klasifikasi maqam Arab (Bayati, Hijaz, Nahawand, Rast, Saba, Sikah,
    Ajam, Kurd) dari audio tilawah/nasyid.
    Research note: 91, 88.
    """
    cites = _cite(91, 88)
    if not os.path.exists(audio_path):
        return _fallback(f"File tidak ditemukan: {audio_path}", citations=cites)

    return _fallback(
        "Maqam classifier belum di-implement. Baseline yang bisa dibangun:\n"
        "  1) Ekstrak MFCC + chroma + spectral features dengan librosa.\n"
        "  2) Replikasi Shahriar & Tariq 2022 (CNN/LSTM/ANN, 8 kelas).\n"
        "  3) Untuk interval mikrotonal (quartertone), gunakan HCQT dengan\n"
        "     resolusi lebih tinggi dari 12-TET.\n"
        "  4) Dataset: Everyayah + rekaman qari terverifikasi maqam-nya.\n"
        "  5) Output: probabilitas 7/8 maqam utama.",
        citations=cites,
        data={
            "maqam_probs": None,
            "supported": ["Bayati", "Hijaz", "Nahawand", "Rast",
                          "Saba", "Sikah", "Ajam", "Kurd"],
        },
    )


# ── Registry ──────────────────────────────────────────────────────────────────

@dataclass
class AudioTool:
    name: str
    description: str
    fn: Callable[..., dict]
    research_notes: list[int] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)  # python modules yang dibutuhkan

    def is_available(self) -> bool:
        return all(_has_module(m) for m in self.requires) if self.requires else True


class AudioCapabilityRegistry:
    """Registry tool audio yang bisa dipanggil SIDIX ReAct agent."""

    def __init__(self):
        self._tools: dict[str, AudioTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(AudioTool(
            name="transcribe_audio",
            description="ASR audio → teks (default Bahasa Indonesia). "
                        "Backend: faster-whisper > openai-whisper.",
            fn=transcribe_audio,
            research_notes=[86, 84, 85],
            requires=[],  # fungsi sendiri sudah handle fallback
        ))
        self.register(AudioTool(
            name="synthesize_speech",
            description="TTS teks → file audio. Butuh consent untuk voice clone.",
            fn=synthesize_speech,
            research_notes=[87, 91],
        ))
        self.register(AudioTool(
            name="analyze_audio",
            description="Analisis audio: pitch, tempo, duration, spectral, RMS.",
            fn=analyze_audio,
            research_notes=[84, 88],
        ))
        self.register(AudioTool(
            name="separate_stems",
            description="Source separation via HTDemucs/Demucs.",
            fn=separate_stems,
            research_notes=[88],
        ))
        self.register(AudioTool(
            name="detect_beat",
            description="Beat tracking dan tempo estimation.",
            fn=detect_beat,
            research_notes=[88],
        ))
        self.register(AudioTool(
            name="classify_instrument",
            description="Instrument recognition stub (MERT + multi-label head).",
            fn=classify_instrument,
            research_notes=[88, 92],
        ))
        self.register(AudioTool(
            name="validate_tajweed",
            description="Validasi tajwid Tarteel-style stub (makhraj + mad + idgham).",
            fn=validate_tajweed,
            research_notes=[91, 86],
        ))
        self.register(AudioTool(
            name="detect_maqam",
            description="Klasifikasi maqam Arab stub (8 kelas utama).",
            fn=detect_maqam,
            research_notes=[91, 88],
        ))

    def register(self, tool: AudioTool) -> None:
        self._tools[tool.name] = tool

    def call_tool(self, name: str, **kwargs) -> dict:
        """Panggil tool by name, return standard dict."""
        if name not in self._tools:
            return _fallback(
                f"Tool '{name}' tidak terdaftar. Tersedia: {list(self._tools)}",
                citations=[],
            )
        try:
            return self._tools[name].fn(**kwargs)
        except TypeError as exc:
            return _fallback(
                f"Argumen tidak cocok untuk '{name}': {exc}", citations=[],
            )
        except Exception as exc:  # noqa: BLE001
            return _fallback(
                f"Tool '{name}' melempar exception: {exc}", citations=[],
            )

    def list_capabilities(self) -> list[dict]:
        """Daftar semua tool dengan status ketersediaan."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "available": t.is_available(),
                "requires": t.requires,
                "research_notes": t.research_notes,
            }
            for t in self._tools.values()
        ]


# ── Singleton ─────────────────────────────────────────────────────────────────

_registry: Optional[AudioCapabilityRegistry] = None

def get_audio_registry() -> AudioCapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = AudioCapabilityRegistry()
    return _registry
