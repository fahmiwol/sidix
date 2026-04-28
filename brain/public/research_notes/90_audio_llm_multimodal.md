> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
id: 90
topic: audio_llm_multimodal
tags: [audio_llm, qwen_omni, moshi, salmonn, audio_palm, multimodal, full_duplex]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [85, 86, 87, 89, 92]
---

# 90 — Audio: Foundation Audio LLM dan Multimodal

## Apa
Arsitektur end-to-end untuk SIDIX: **Audio LLM** yang menerima audio langsung sebagai input (tanpa cascade ASR->LLM->TTS) dan menghasilkan respons teks atau token audio. Termasuk paradigma full-duplex a la Moshi.

## Mengapa
- Cascaded pipeline (Whisper -> LLM -> TTS) kehilangan paralinguistic (emosi, intonasi, jeda), latency 1-2 detik.
- Audio LLM native (Moshi, GPT-4o, Qwen2.5-Omni) <200ms latency, mendukung interrupt natural, pertahankan karakteristik suara.
- Untuk SIDIX yang mengejar percakapan seperti manusia + epistemologi Islam (sanad lisan tradisional), full-duplex adalah arah masa depan.

## Bagaimana

### Dua tren besar 2025-2026
1. **Encoder audio universal** (BEATs, CLAP, M2D) — satu model 600+ kelas.
2. **Audio LLM full-duplex** (Moshi, GPT-4o, Qwen2.5-Omni) — percakapan real-time <200ms.

### Audio LLM populer
| Model | Org | Modalitas | Keunggulan |
|-------|-----|-----------|-------------|
| Qwen2-Audio / Qwen2.5-Omni | Alibaba | Audio in, teks out / audio in+out | Open, multibahasa, 2025 omni |
| SALMONN | Tsinghua/ByteDance | Audio in, teks out | Speech+music+event+reasoning |
| Gemini 1.5/2.0 | Google | Native audio in+out | 2M context, realtime |
| GPT-4o Voice | OpenAI | Full-duplex realtime | SOTA kualitas |
| **Moshi** | Kyutai | Speech LM full-duplex | Open, 200ms latency, inner monologue |
| LLaMA-Omni | Open | Speech-in/out | Blueprint |
| GLM-4-Voice | Zhipu | Bilingual Zh/En | Full-duplex |
| Spirit-LM | Meta | Text-speech interleaved | Ekspresif tanpa TTS |
| Voxtral | Mistral | Audio understanding | Open weights 2025 |
| Phi-4-Multimodal | Microsoft | Vision+audio+teks | Kecil, efisien |
| SeamlessM4T v2 | Meta | S2ST 100+ bahasa | Translation |
| AudioPaLM | Google | Unified speech-text LM | Rubenstein arXiv:2306.12925 |

### Pola arsitektur umum
```
audio encoder (Whisper encoder / AST / BEATs / CLAP)
  -> projector linear/Q-Former
  -> LLM core (Llama 3, Qwen 2, Mistral)
  -> output: teks ATAU token audio (via EnCodec/DAC/SNAC decoder)
```
Varian: discrete token langsung sebagai kosakata LLM (AudioLM/VALL-E/Moshi paradigm).

### Moshi (pantas disorot)
- Arsitektur **dual-stream**: user-stream + model-stream simultan.
- **Inner monologue**: text planning sebelum speech token.
- Interrupt natural karena model "memikirkan sambil mendengar".
- Latency <200ms pada satu GPU.
- **Open-source blueprint** untuk agen suara masa depan.

### Benchmark Audio LLM
- **AIR-Bench**: foundation + chat + instruction.
- **AudioBench**: speech understanding.
- **VoiceBench**: speech interaction.
- **MMAU**: multimodal audio scientific reasoning.
- **Dynamic-SUPERB**: task-diverse.

### Training Recipe Canonical (3 tahap)
1. **Pretrain alignment**: projector + encoder-LLM dengan caption data (WavCaps 400k, AudioCaps, Clotho, MusicCaps).
2. **Instruction tuning**: audio-Q&A synthetic + SALMONN-style mixed curriculum.
3. **RLHF/DPO opsional**: preferensi suara alami.

### Rekomendasi arsitektur untuk SIDIX (end-to-end)
1. **Audio frontend dual encoder**: Whisper v3 encoder (speech semantic) + BEATs atau MERT (music + environmental) fused via concat + gated cross-attention.
2. **Tokenizer audio**: DAC 24 kHz atau SNAC (hierarchical 12 Hz semantic + 75 Hz acoustic).
3. **LLM core**: Llama 3.3 70B atau Qwen 2.5 32B fine-tuned dengan audio token di kosakata.
4. **Output head paralel**: teks (tool calls, reasoning), speech tokens (-> BigVGAN), music/SFX tokens (-> MusicGen/Stable Audio head).
5. **Full-duplex wrapper** mengikuti Moshi.
6. **Tool-calling modules**: HTDemucs, Basic Pitch, madmom/Beat-This, LAION-CLAP, Silero VAD, pyannote diarization.
7. **Guardrails**: AudioSeal watermark otomatis, filter konten (classifier lirik haram), consent check voice clone.

### Tiga pendekatan integrasi LLM+audio
1. **Cascaded**: sederhana, latency tinggi, kehilangan paralinguistic.
2. **Encoder + adapter + LLM**: encoder beku, adapter ringan (Qwen-Audio, SALMONN, LTU).
3. **End-to-end codec LM**: full-duplex, audio tokens sebagai kosakata (Moshi, VALL-E, AudioLM).

## Contoh Nyata
Panggil Qwen2-Audio untuk audio Q&A (inference lokal, tidak via vendor API):
```python
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")
model = Qwen2AudioForConditionalGeneration.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")

conversation = [
    {"role": "user", "content": [
        {"type": "audio", "audio_url": "voice_question.wav"},
        {"type": "text", "text": "Apa yang dibicarakan di audio ini?"},
    ]},
]
inputs = processor.apply_chat_template(conversation, return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=256)
answer = processor.batch_decode(out, skip_special_tokens=True)
```

## Keterbatasan
- Audio LLM butuh GPU 16-40GB VRAM untuk 7B-70B params — belum workable di VPS 72.62.125.6 (tidak ada GPU).
- Moshi open-source tapi butuh Rust + CUDA setup yang non-trivial.
- Benchmark audio LLM bias bahasa Inggris; evaluasi Indonesia kustom belum ada.
- Full-duplex butuh streaming tokenizer yang kompleks untuk menjaga latency <200ms.

## Sitasi
Artefak compass user 2026-04-18; Qwen2-Audio Chu arXiv:2407.10759; Moshi Kyutai 2024; AudioPaLM Rubenstein arXiv:2306.12925; SALMONN Tang 2024.
