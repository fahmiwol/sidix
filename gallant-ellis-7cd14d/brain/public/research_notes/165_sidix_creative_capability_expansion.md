> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
title: SIDIX Creative & Programming Capability Expansion Directive
sanad_tier: primer
tags: [capability, roadmap, creative, multimodal, standing-alone]
date: 2026-04-19
---

# SIDIX Creative & Programming Capability Expansion

[FACT] Direktif dari user (owner): SIDIX harus jago di akademik, creativity, programming, gaming, membuat aplikasi/website/game/3D/WebGL/Three.js, design content/foto, text-to-image, image-to-text, image-to-image, image-to-video, text-to-sound, TTS, photo/video editor, content marketing, periklanan, filter, style.

[FACT] Prinsip non-negosiasi: semua kapabilitas harus standing-alone — open-source model self-host. Tidak ada OpenAI/Midjourney/ElevenLabs API.

---

## Apa yang diminta

User mendefinisikan scope SIDIX jauh lebih luas dari "chatbot tanya-jawab". Target adalah **AI agent kreatif multi-domain** yang bisa:

1. **Akademik & Research** — solve matematika, analisis data, baca paper, knowledge graph
2. **Programming** — jalankan kode Python/JS/Rust, debug, generate webapp, game
3. **3D & WebGL** — generate Three.js scene, Blender render, WebGL shader
4. **Gambar (Image)** — text-to-image, image-to-image, caption, filter, remove background
5. **Audio** — TTS (SIDIX bicara), ASR (user kirim suara), music gen, tajwid
6. **Video** — text-to-video, image-to-video, editor, auto-caption, transcribe
7. **Content Marketing** — copywriting iklan, social media post, SEO, hashtag, A/B test
8. **Design** — poster/banner via SVG template, style transfer, filter foto

---

## Mengapa ini penting

[OPINION] Untuk bersaing dengan GPT-4o, Claude, dan Gemini, SIDIX tidak bisa hanya jadi chatbot teks. Differensiasi SIDIX adalah:
1. **Epistemic transparency** (sanad chain, 4-label) — GPT/Claude tidak punya ini
2. **Cultural specialization** (Nusantara-Islam-native) — GPT/Claude generik
3. **Data sovereignty** (self-host, no vendor lock) — enterprise/gov bisa pakai

Tapi user juga perlu **paritas fungsional** dengan tool komersial. Kalau SIDIX tidak bisa generate gambar atau analisis data, user akan tetap pakai GPT untuk itu → SIDIX cuma jadi niche tool.

---

## Pendekatan Standing-Alone per Domain

### Text & Code (Baby — sudah ada)
- Python subprocess `code_sandbox` → aman, timeout, no network
- SymPy untuk matematika, pandas untuk data, matplotlib untuk plot

### Image Generation (Child Q3)
- [FACT] SDXL 1.0 adalah open-source image gen terkuat saat ini (Apache-2.0)
- [FACT] FLUX.1-schnell (Black Forest Labs) lebih cepat, license permissive
- [OPINION] Untuk Nusantara cultural image, SDXL butuh LoRA fine-tune dengan dataset lokal
- Self-host via Diffusers library atau ComfyUI API
- No DALL-E, no Midjourney

### Vision / Image-to-Text (Child Q3)
- Qwen2.5-VL (multimodal, strong performance, Apache-2.0)
- InternVL2 alternatif (MIT license)
- Self-host inference via Transformers + bfloat16

### Audio: TTS + ASR (Baby P2 / Sprint 3)
- [FACT] `audio_capability.py` sudah ada registry TTS/ASR/voice-clone/music-gen
- Piper TTS — Mozilla Foundation, MIT license, CPU-compatible
- Coqui XTTS — Apache-2.0, voice cloning
- whisper.cpp — MIT, CPU inference (real-time ~0.5x speed)
- Prasyarat: install whisper/librosa + wire sebagai agent tool

### Music Generation (Child Q3)
- AudioCraft/MusicGen (Meta, MIT license)
- Input: text prompt + duration
- GPU preferred tapi CPU bisa (very slow)

### Video Generation (Adolescent Q4)
- CogVideoX (THUDM, Apache-2.0) — text-to-video
- Open-Sora (Hpcai-tech, Apache-2.0) — open video diffusion
- Butuh GPU A100/H100 untuk reasonable speed
- [SPECULATION] Untuk Nusantara content, akan butuh fine-tune dataset lokal

### 3D / WebGL / Three.js (Child Q3)
- Tidak butuh GPU untuk generate kode
- LLM generative → generate Three.js scene code → serve via iframe sandbox
- Blender Python API → headless render → PNG/MP4 output
- Tool: `threejs_gen` (LLM + template), `blender_render` (subprocess)

### Content Marketing (Baby — sudah parsial)
- `threads_autopost.py` sudah live (40 endpoints)
- MIGHAN persona sudah ter-optimize untuk copywriting kreatif
- Extend: A/B test variant generator, SEO keyword extractor

---

## Keterbatasan & Trade-off

[FACT] Kapabilitas dengan GPU dependency (image gen, video gen, music gen) tidak bisa jalan di CPU server yang ada sekarang. Butuh upgrade infra atau cloud GPU instance.

[FACT] Video generation (CogVideoX) butuh GPU A100/H100 — di luar budget saat ini.

[OPINION] Prioritas yang benar:
1. Selesaikan Baby foundational (Sprint 1-2) dulu
2. Baru add multimodal (Sprint 3 Child) setelah GPU infra siap
3. Video gen adalah Sprint 7+ — jangan terburu-buru

[OPINION] Three.js generator bisa dimulai lebih awal karena tidak butuh GPU — pure LLM generative + kode template. Ini quick win untuk "creativity" story.

---

## Implikasi untuk Roadmap

`docs/CREATIVE_CAPABILITY_ROADMAP.md` adalah dokumen teknis detail per kapabilitas.

Key additions ke `docs/SIDIX_ROADMAP_2026.md` Stage Child:
- Image gen (SDXL/FLUX) — Sprint 3
- Vision (Qwen2.5-VL) — Sprint 3
- TTS/ASR (Piper/Whisper) — Sprint 3
- 3D/WebGL generator — Sprint 4
- Music gen — Sprint 5
- Video gen — Sprint 7 (Adolescent)

---

## Sanad
- Direktif langsung dari user/owner (2026-04-19)
- `docs/CREATIVE_CAPABILITY_ROADMAP.md` — dokumen teknis turunan
- `docs/SIDIX_ROADMAP_2026.md` — roadmap yang diupdate
- `brain/public/research_notes/162_framework_brain_hands_memory_peta_kemampuan_sidix.md` — framework Brain+Hands+Memory yang menjadi fondasi peta kapabilitas
