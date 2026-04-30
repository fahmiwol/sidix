"""
audio_seed.py — Seed AUDIO capability track
===========================================
Seed:
  * 8 skill (transcribe, synthesize, analyze, separate, beat, instrument,
    tajweed, maqam) ke SkillLibrary dengan domain "audio".
  * Curriculum tasks L0-L4 untuk track AUDIO.
  * 3 CSDOR experience dari insight dokumen compass.

Dipanggil via:
  python -m brain_qa.audio_seed

Idempoten — cek duplikat sebelum insert.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .skill_library import SkillLibrary, SkillType, SkillDomain
from .curriculum import (
    CurriculumEngine, DEFAULT_CURRICULUM, CurriculumStatus, _CURR_STORE,
)
from .experience_engine import (
    ExperienceEngine, ExperienceGroup, SourceType,
)


# ── Add AUDIO to SkillDomain (via string literal; Enum is open for suffix) ────

AUDIO_DOMAIN = "audio"

_AUDIO_SOURCE = "audio_capability_track_2026_04_18"


AUDIO_SKILLS: list[dict] = [
    {
        "name": "audio_transcribe",
        "description": "ASR: audio → teks (Bahasa Indonesia), backend Whisper.",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path, lang='id'):\n"
            "    return get_audio_registry().call_tool('transcribe_audio',\n"
            "                                          path=path, lang=lang)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "asr", "whisper", "id"],
    },
    {
        "name": "audio_synthesize_speech",
        "description": "TTS: teks → audio; Coqui XTTS / pyttsx3 fallback.",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(text, lang='id', out='tts.wav'):\n"
            "    return get_audio_registry().call_tool('synthesize_speech',\n"
            "                                          text=text, lang=lang,\n"
            "                                          out_path=out)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "tts", "voice", "id"],
    },
    {
        "name": "audio_analyze_features",
        "description": "Analisis MIR dasar: pitch, tempo, spectral, RMS (librosa).",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path):\n"
            "    return get_audio_registry().call_tool('analyze_audio', path=path)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "mir", "librosa", "features"],
    },
    {
        "name": "audio_separate_stems",
        "description": "Source separation via Demucs/HTDemucs.",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path, two_stems=True):\n"
            "    return get_audio_registry().call_tool('separate_stems',\n"
            "                                          path=path, two_stems=two_stems)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "mir", "demucs", "separation"],
    },
    {
        "name": "audio_detect_beat",
        "description": "Beat tracking + tempo BPM.",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path):\n"
            "    return get_audio_registry().call_tool('detect_beat', path=path)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "mir", "beat", "tempo"],
    },
    {
        "name": "audio_classify_instrument",
        "description": "Klasifikasi alat musik (MERT + multi-label head stub).",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path):\n"
            "    return get_audio_registry().call_tool('classify_instrument',\n"
            "                                          path=path)\n"
        ),
        "skill_type": SkillType.TOOL_COMBO,
        "tags": ["audio", "mir", "instrument", "mert"],
    },
    {
        "name": "audio_validate_tajweed",
        "description": "Validasi tajwid ala Tarteel (stub, pipeline Whisper + rules).",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path, ayah='', qiraat='hafs_an_asim'):\n"
            "    return get_audio_registry().call_tool('validate_tajweed',\n"
            "                                          audio_path=path,\n"
            "                                          reference_ayah=ayah,\n"
            "                                          expected_qiraat=qiraat)\n"
        ),
        "skill_type": SkillType.REASONING,
        "tags": ["audio", "islam", "tajwid", "tarteel", "qiraat"],
    },
    {
        "name": "audio_detect_maqam",
        "description": "Klasifikasi maqam Arab (8 kelas, stub Shahriar & Tariq 2022).",
        "content": (
            "from brain_qa.audio_capability import get_audio_registry\n"
            "def run(path):\n"
            "    return get_audio_registry().call_tool('detect_maqam',\n"
            "                                          audio_path=path)\n"
        ),
        "skill_type": SkillType.REASONING,
        "tags": ["audio", "islam", "maqam", "tilawah"],
    },
]


AUDIO_CURRICULUM: list[dict] = [
    # ── L0 ─────────────────────────────────────────────────────────────
    {"id": "l0_sound_physics_basics", "domain": "audio", "persona": "FACH",
     "topic": "Fisika suara: gelombang, frekuensi, amplitudo, fase, dB SPL",
     "level": 0, "fetch_query": "acoustics sound wave frequency amplitude",
     "corpus_target": 2},
    {"id": "l0_digital_audio_basics", "domain": "audio", "persona": "FACH",
     "topic": "Digital audio: Nyquist, bit depth, sampling rate, PCM, WAV",
     "level": 0, "fetch_query": "digital audio Nyquist sampling PCM",
     "corpus_target": 2},
    {"id": "l0_mel_spectrogram_intuition", "domain": "audio", "persona": "FACH",
     "topic": "Mel spectrogram + MFCC: intuisi dan cara hitung",
     "level": 0, "fetch_query": "mel spectrogram MFCC intuition deep learning",
     "corpus_target": 2},
    {"id": "l0_tajwid_ilm_basics", "domain": "audio", "persona": "INAN",
     "topic": "Dasar ilmu tajwid: makhraj, sifat huruf, hukum mim/nun sakinah",
     "level": 0, "fetch_query": "tajweed makhraj sifat huruf Quran",
     "corpus_target": 2},

    # ── L1 ─────────────────────────────────────────────────────────────
    {"id": "l1_asr_pipeline", "domain": "audio", "persona": "FACH",
     "topic": "Pipeline ASR modern: VAD → Whisper/MMS → punctuation → ITN",
     "level": 1, "prerequisites": ["l0_digital_audio_basics",
                                    "l0_mel_spectrogram_intuition"],
     "fetch_query": "automatic speech recognition Whisper MMS pipeline",
     "corpus_target": 3},
    {"id": "l1_tts_pipeline", "domain": "audio", "persona": "FACH",
     "topic": "Pipeline TTS: teks → phoneme → mel → vocoder (HiFi-GAN)",
     "level": 1, "prerequisites": ["l0_mel_spectrogram_intuition"],
     "fetch_query": "text-to-speech TTS neural vocoder HiFi-GAN",
     "corpus_target": 3},
    {"id": "l1_mir_basics", "domain": "audio", "persona": "FACH",
     "topic": "MIR dasar: beat, pitch, chord, source separation",
     "level": 1, "prerequisites": ["l0_digital_audio_basics"],
     "fetch_query": "music information retrieval beat chord separation",
     "corpus_target": 3},
    {"id": "l1_audio_codec_tokens", "domain": "audio", "persona": "FACH",
     "topic": "Neural audio codec: EnCodec, DAC, SNAC; RVQ & token diskret",
     "level": 1, "prerequisites": ["l0_digital_audio_basics"],
     "fetch_query": "neural audio codec EnCodec DAC residual vector quantization",
     "corpus_target": 3},

    # ── L2 ─────────────────────────────────────────────────────────────
    {"id": "l2_whisper_fine_tuning", "domain": "audio", "persona": "FACH",
     "topic": "Fine-tune Whisper-v3 + LoRA pada data Indonesia",
     "level": 2, "prerequisites": ["l1_asr_pipeline"],
     "fetch_query": "Whisper fine-tuning LoRA Indonesian low resource",
     "corpus_target": 3},
    {"id": "l2_tts_voice_cloning_ethics", "domain": "audio", "persona": "INAN",
     "topic": "TTS voice cloning: F5-TTS, XTTS, etika consent + watermark",
     "level": 2, "prerequisites": ["l1_tts_pipeline"],
     "fetch_query": "voice cloning F5-TTS consent watermark AudioSeal",
     "corpus_target": 3},
    {"id": "l2_music_generation_intro", "domain": "audio", "persona": "MIGHAN",
     "topic": "Music generation: MusicGen, Stable Audio, AudioLDM 2",
     "level": 2, "prerequisites": ["l1_mir_basics", "l1_audio_codec_tokens"],
     "fetch_query": "music generation MusicGen Stable Audio AudioLDM diffusion",
     "corpus_target": 3},
    {"id": "l2_qiraat_classifier_design", "domain": "audio", "persona": "INAN",
     "topic": "Desain classifier qira'at 7/10 mutawatir",
     "level": 2, "prerequisites": ["l1_asr_pipeline", "l0_tajwid_ilm_basics"],
     "fetch_query": "qiraat classifier Quran deep learning Tarteel",
     "corpus_target": 3},

    # ── L3 ─────────────────────────────────────────────────────────────
    {"id": "l3_audio_llm_architecture", "domain": "audio", "persona": "FACH",
     "topic": "Arsitektur Audio-LLM: encoder + adapter + LLM + parallel heads",
     "level": 3, "prerequisites": ["l2_whisper_fine_tuning",
                                    "l1_audio_codec_tokens"],
     "fetch_query": "audio large language model Qwen-Audio SALMONN architecture",
     "corpus_target": 3},
    {"id": "l3_moshi_full_duplex_pattern", "domain": "audio", "persona": "FACH",
     "topic": "Pola full-duplex Moshi: dual stream + inner monologue <200ms",
     "level": 3, "prerequisites": ["l3_audio_llm_architecture"],
     "fetch_query": "Moshi Kyutai full duplex speech LLM inner monologue",
     "corpus_target": 3},

    # ── L4 ─────────────────────────────────────────────────────────────
    {"id": "l4_halal_audio_ai_maqashid_framework", "domain": "audio",
     "persona": "INAN",
     "topic": "Halal audio AI: kerangka maqashid untuk evaluasi kapabilitas audio",
     "level": 4, "prerequisites": ["l2_tts_voice_cloning_ethics",
                                    "l2_qiraat_classifier_design",
                                    "l2_music_generation_intro"],
     "fetch_query": "Islamic ethics audio AI maqashid consent deepfake",
     "corpus_target": 3},
]


AUDIO_EXPERIENCES: list[dict] = [
    {
        "context": {
            "role": "researcher", "age_band": "30-35", "locale": "ID",
            "domain": "audio_ai_asr",
        },
        "situation": ("Bangun ASR Bahasa Indonesia low-resource; Common Voice ID "
                      "hanya 50 jam tervalidasi vs LibriSpeech 1000 jam English."),
        "decision": ("Fine-tune Whisper-large-v3 + LoRA rank 16 pada campuran "
                     "Common Voice ID + NusaCrowd + Bloom speech; SpecAugment + "
                     "pitch/speed augmentation."),
        "outcome": ("positive: WER turun dari ~18% (out-of-box Whisper-v3) ke "
                    "8-12% setelah 3 epoch fine-tune; RTF <0.3 di GPU A100."),
        "reflection": ("Transfer learning dari model multilingual besar > train "
                       "from scratch untuk low-resource. LoRA cukup; full "
                       "fine-tune tidak memberi gain signifikan di skala ini."),
        "tags": ["audio", "asr", "whisper", "indonesia", "low-resource", "lora"],
        "source_ref": "brain/public/research_notes/86_audio_asr_speech_recognition.md",
    },
    {
        "context": {
            "role": "developer", "age_band": "25-30", "locale": "ID",
            "domain": "audio_ai_tts_quran",
        },
        "situation": ("Rencana TTS Qur'an untuk aplikasi edukasi anak; tidak "
                      "boleh meniru qari mutawatir tanpa izin (fatwa Al-Azhar + "
                      "MUI 2023-2024)."),
        "decision": ("Pakai suara sintetik generik (XTTS v2 fine-tune suara "
                     "non-mutawatir) + disclaimer jelas 'bukan pengganti "
                     "talaqqi' + watermark AudioSeal + fokus aplikasi edukasi "
                     "huruf hijaiyah dan hafalan dasar."),
        "outcome": ("positive: produk diterima ulama dan keluarga; tidak ada "
                    "klaim fitnah; kerangka diadopsi fatwa 2024 sebagai "
                    "referensi 'TTS Qur'an halal'."),
        "reflection": ("Adab konsensual > kualitas impersonasi. Disclaimer + "
                       "niat edukasi memecahkan ambiguitas fiqh. Watermark + "
                       "consent log = due diligence yang menyelamatkan."),
        "tags": ["audio", "tts", "quran", "islam", "consent", "watermark"],
        "source_ref": "brain/public/research_notes/87_audio_tts_voice_cloning.md",
    },
    {
        "context": {
            "role": "researcher", "age_band": "30-35", "locale": "ID",
            "domain": "audio_ai_mir_music_foundation",
        },
        "situation": ("Perlu memilih foundation model MIR untuk 14 tugas "
                      "(beat, chord, genre, tagging, instrument, pitch, key, "
                      "structure, emotion, ...). Compute terbatas: 1x RTX 4090 "
                      "24GB."),
        "decision": ("Pilih MERT-330M (M-A-P/HKUST, HuBERT-style + CQT teacher, "
                     "160k jam pretrain) dibanding Jukebox 5B OpenAI."),
        "outcome": ("positive: MERT-330M mencapai SOTA pada 14 tugas MIR dengan "
                    "~15x lebih sedikit parameter dibanding Jukebox; fine-tune "
                    "muat di RTX 4090; latency inference <100ms per klip."),
        "reflection": ("SSL + musical teacher > scale buta. Foundation model "
                       "kecil yang tepat arsitekturnya bisa mengalahkan yang "
                       "jauh lebih besar — kabar baik untuk riset dengan "
                       "compute terbatas di Indonesia."),
        "tags": ["audio", "mir", "mert", "foundation_model", "compute_efficient"],
        "source_ref": "brain/public/research_notes/88_audio_mir_music_understanding.md",
    },
]


# ── Seed runners ──────────────────────────────────────────────────────────────

def seed_skills() -> dict:
    lib = SkillLibrary()
    added = 0
    skipped = 0
    for sk in AUDIO_SKILLS:
        # cek duplikat via internal _find_by_name (add() sendiri idempoten)
        existing = lib._find_by_name(sk["name"])  # noqa: SLF001 — internal ok
        if existing:
            skipped += 1
            continue
        lib.add(
            name=sk["name"],
            description=sk["description"],
            content=sk["content"],
            skill_type=sk.get("skill_type", SkillType.TOOL_COMBO),
            domain=AUDIO_DOMAIN,
            tags=sk.get("tags", []),
            source_session=_AUDIO_SOURCE,
        )
        added += 1
    return {"added": added, "skipped": skipped,
            "total_audio_skills": len(AUDIO_SKILLS)}


def seed_curriculum() -> dict:
    """Append AUDIO tasks ke curriculum store kalau belum ada."""
    if _CURR_STORE.exists():
        try:
            current = json.loads(_CURR_STORE.read_text(encoding="utf-8"))
        except Exception:
            current = []
    else:
        # init dulu dari DEFAULT_CURRICULUM supaya CurriculumEngine tidak
        # salah state
        current = [{**t, "status": CurriculumStatus.PENDING,
                    "created_at": time.time()} for t in DEFAULT_CURRICULUM]

    existing_ids = {t.get("id") for t in current}
    added = 0
    for task in AUDIO_CURRICULUM:
        if task["id"] in existing_ids:
            continue
        current.append({**task, "status": CurriculumStatus.PENDING,
                        "created_at": time.time()})
        added += 1

    _CURR_STORE.write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"added": added, "total_tasks": len(current),
            "audio_tasks": len(AUDIO_CURRICULUM)}


def seed_experiences() -> dict:
    eng = ExperienceEngine()
    added = 0
    for exp in AUDIO_EXPERIENCES:
        eng.add_structured(
            context=exp["context"],
            situation=exp["situation"],
            decision=exp["decision"],
            outcome=exp["outcome"],
            reflection=exp["reflection"],
            group=ExperienceGroup.WORK_BUSINESS,
            source_type=SourceType.CORPUS,
            source_ref=exp["source_ref"],
            tags=exp["tags"],
            confidence=0.7,
        )
        added += 1
    return {"added": added}


def seed_all() -> dict:
    return {
        "skills": seed_skills(),
        "curriculum": seed_curriculum(),
        "experiences": seed_experiences(),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(seed_all())
