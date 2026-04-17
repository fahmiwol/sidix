---
id: 92
topic: audio_capability_track_master_index
tags: [audio, master_index, architecture, sidix_capabilities, e2e]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [84, 85, 86, 87, 88, 89, 90, 91]
---

# 92 — Master Index: Audio Capability Track SIDIX

## Apa
Indeks master yang menyatukan research notes 84-91 menjadi satu arsitektur end-to-end untuk SIDIX agar dapat **mendengar**, **berbicara**, **bernyanyi**, **membuat musik**, **mengenal alat musik**, dan **memahami tilawah Al-Qur'an** dengan lensa Islam.

## Mengapa
- Tanpa master index, 8 research note granular (84-91) terasa silo. Insight terbaik muncul dari integrasi 7 lapisan (fondasi -> multimodal).
- Membantu agent SIDIX dan kontributor baru memahami peta kapabilitas sekaligus.
- Menjadi acuan `AudioCapabilityRegistry` di `apps/brain_qa/brain_qa/audio_capability.py`.

## Bagaimana — Peta 7 Lapisan + 1 Lapisan Islam

| Layer | Research Note | Apa yang dipelajari |
|-------|---------------|---------------------|
| L1 Fondasi Akustik | [84](84_audio_fondasi_akustik.md) | Fisika suara, DFT/STFT, Mel, MFCC, CQT |
| L2 Representasi Digital | [85](85_audio_representasi_digital.md) | Nyquist, codec, neural codec (EnCodec, DAC, SNAC), RVQ |
| L3 ASR | [86](86_audio_asr_speech_recognition.md) | Whisper, MMS, Wav2Vec2, Tarteel, ASR Indonesia |
| L4 TTS + SVS | [87](87_audio_tts_voice_cloning.md) | Tacotron -> F5-TTS, XTTS, VITS, DiffSinger, etika consent |
| L5 MIR | [88](88_audio_mir_music_understanding.md) | MERT, BEATs, HTDemucs, Basic Pitch, instrument recognition, gamelan |
| L6 Generasi Audio | [89](89_audio_generasi_musik.md) | MusicGen, Stable Audio, YuE, AudioLDM 2, watermark AudioSeal |
| L7 Audio LLM | [90](90_audio_llm_multimodal.md) | Qwen2.5-Omni, Moshi full-duplex, SALMONN |
| L8 Islam | [91](91_audio_islam_tajwid_qiraat.md) | Fiqh al-ghina, tajwid, qira'at, maqam, maqashid, consent |

## Arsitektur End-to-End SIDIX Audio (dari dokumen compass)

```
              ┌──────────────────────────────────────────┐
              │  USER (voice / music / file upload)     │
              └────────────────┬─────────────────────────┘
                               │
              ┌────────────────▼─────────────────────────┐
              │  Audio Frontend (Pre-processing)         │
              │  Silero VAD + resample SoXR + LUFS norm  │
              └────────────────┬─────────────────────────┘
                               │
           ┌───────────────────▼──────────────────────────┐
           │    DUAL ENCODER (paralel)                    │
           │  ┌──────────────┐   ┌──────────────────┐     │
           │  │ Whisper v3   │   │ BEATs / MERT     │     │
           │  │ (speech sem) │   │ (music/env sem)  │     │
           │  └──────┬───────┘   └────────┬─────────┘     │
           │         └─── gated cross-attention ───┐      │
           └───────────────────┬───────────────────┴──────┘
                               │
              ┌────────────────▼─────────────────────────┐
              │ AUDIO TOKENIZER (DAC 24kHz / SNAC)       │
              │ → discrete tokens ≈ 75 tok/sec           │
              └────────────────┬─────────────────────────┘
                               │
              ┌────────────────▼─────────────────────────┐
              │ LLM CORE (Qwen2.5-Omni / Llama 3.3)      │
              │ kosa kata diperluas dengan audio tokens  │
              │ (tool-calling + ReAct)                   │
              └─┬───────────────┬───────────────┬────────┘
                │               │               │
         ┌──────▼─────┐  ┌──────▼───────┐ ┌─────▼──────────┐
         │ Text head  │  │ Speech tokens│ │ Music/SFX tok  │
         │ (answer)   │  │ → BigVGAN    │ │ → MusicGen /   │
         │            │  │   vocoder    │ │   StableAudio  │
         └────────────┘  └──────┬───────┘ └──────┬─────────┘
                                │                │
              ┌─────────────────▼────────────────▼────────┐
              │  FULL-DUPLEX WRAPPER (Moshi-style)        │
              │  user-stream + model-stream, <200ms lat.  │
              └────────────────┬──────────────────────────┘
                               │
              ┌────────────────▼─────────────────────────┐
              │  GUARDRAILS SYARIAH                       │
              │  AudioSeal watermark | Content filter     │
              │  Consent registry | Maqashid validator    │
              └────────────────┬─────────────────────────┘
                               │
                   ┌───────────▼─────────────┐
                   │   OUTPUT KE USER        │
                   └─────────────────────────┘

           Tool-calling modules (via ReAct):
           HTDemucs (separation), Basic Pitch (transcribe),
           madmom/Beat-This (beat), LAION-CLAP (zero-shot tag),
           pyannote (diarize), Silero VAD, Tarteel-style tajwid.
```

## Tahap Implementasi SIDIX (adaptasi roadmap dokumen)

### Fase 1 — Fondasi (bulan 1-6 sejak 2026-04)
- Kurasi 500-1000 jam audio Indonesia (speech + tilawah + gamelan/nasyid).
- Implementasi preprocessing standar (SpecAugment + LUFS + VAD + RIR).
- Daftarkan `AudioCapabilityRegistry` dengan fallback stubs.

### Fase 2 — Spesialis (bulan 7-12)
- Whisper-v3 + MMS fine-tune ASR Indonesia (target WER <10%).
- F5-TTS + XTTS v2 fine-tune TTS (target MOS >4.0).
- HTDemucs + MERT untuk MIR Indonesia + gamelan adapter.
- MusicGen fine-tune gamelan/keroncong/dangdut.

### Fase 3 — Audio-LLM (bulan 13-18)
- Integrasi Qwen2.5-Omni atau Moshi blueprint.
- Guardrails syariah lengkap.
- Benchmark MMAU + AIR-Bench + benchmark Indonesia kustom.
- Rilis open-source dengan sertifikasi halal digital.

## Top 3 Kapabilitas Paling Siap Sekarang (pip install)
1. **ASR** via `faster-whisper` atau `openai-whisper` — WER <15% out-of-box untuk Bahasa Indonesia (fine-tune -> 8-12%).
2. **Audio analysis** via `librosa` — pitch, tempo, duration, spectral features — langsung jalan di CPU.
3. **Source separation** via `demucs` CLI — 4/6 stem untuk musik.

## Top 3 Kapabilitas yang Butuh Riset Lebih Lanjut
1. **Full-duplex Audio LLM** (Moshi-style) — butuh GPU + integrasi Rust; riset engineering besar.
2. **SVS Nasyid/Tilawah dengan maqam mikrotonal** — dataset belum ada, butuh kolaborasi qari + riset SVS adaptasi quartertone.
3. **Tajwid validation neural end-to-end** — Tarteel-style belum publik; butuh dataset berlabel tajwid + classifier rules.

## Contoh Nyata — Panggilan Tool via Agent
```python
from brain_qa.audio_capability import get_audio_registry

reg = get_audio_registry()
result = reg.call_tool("transcribe_audio", path="voice_note.m4a", lang="id")
if result["ok"]:
    print(result["data"]["text"])
else:
    print("Fallback:", result["fallback_instructions"])
```

## Keterbatasan
- Tidak semua library (Demucs, Whisper, MERT) bisa di-install di VPS SIDIX tanpa GPU; stub + fallback jadi default.
- Copyright landscape masih berkembang (RIAA lawsuit); kebijakan SIDIX harus bisa di-update.
- Maqam + qira'at domain butuh validasi ulama manusia; neural output tetap dalam mode "alat bantu pendidikan" bukan otoritas.
- Benchmark Indonesia audio LLM belum ada kanonik; SIDIX sebaiknya jadi salah satu pembangun.

## Sitasi
Artefak compass user 2026-04-18 (kedua dokumen); research notes 84-91; Moshi Kyutai 2024; Muller *Fundamentals of Music Processing*.
