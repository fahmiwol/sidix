---
id: 86
topic: audio_asr_speech_recognition
tags: [audio, asr, whisper, wav2vec2, mms, tarteel, indonesia, qiraat, ctc, rnnt]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [84, 85, 87, 90, 91, 92]
---

# 86 — Audio: ASR (Speech Recognition) dari HMM ke Whisper

## Apa
Kapabilitas SIDIX untuk **mendengar** — mengubah gelombang suara bicara menjadi teks, dengan cabang spesial untuk **tilawah Al-Qur'an** dan **Bahasa Indonesia**.

## Mengapa
- Tanpa ASR, SIDIX tidak bisa menerima input suara dari user — buta pada modalitas yang paling natural untuk manusia Indonesia (voice note WhatsApp, Telegram, percakapan).
- Untuk misi epistemologi Islam: ASR tajwid memungkinkan SIDIX memverifikasi bacaan Qur'an secara otomatis (sanad digital, *hifz al-muashala*).
- Lompatan kualitas 10x pada bahasa low-resource berkat pretraining multibahasa (Whisper 680k jam, MMS 1107 bahasa).

## Bagaimana

### Empat era ASR
1. **GMM-HMM** (2000-an): MFCC + trigram LM + leksikon pronunciation. Kaldi toolkit.
2. **DNN-HMM hybrid** (2010-2017): DNN menggantikan GMM; Hinton 2012 breakthrough -20-30% WER relatif.
3. **End-to-end** (2017-): CTC (DeepSpeech Baidu), RNN-Transducer (Google Pixel streaming), attention LAS (Chan 2016).
4. **SSL + Transformer** (2020-2026): dominan.

### Model modern kunci
| Model | Tahun | Params | Data | Keunggulan |
|-------|-------|--------|------|------------|
| Wav2Vec 2.0 (Meta) | 2020 | 95M/317M | 60k jam LibriLight | Fondasi SSL |
| HuBERT (Meta) | 2021 | 95M-1B | Masked prediction | Stabil |
| Conformer (Google) | 2020 | 10M-1B | Conv+attention | Dasar USM |
| **Whisper v3** (OpenAI) | 2023 | 39M-1.55B | 680k jam multilingual | 99 bahasa termasuk `id` |
| **MMS** (Meta) | 2023 | 300M-1B | 1107 bahasa | Jawa, Sunda, Minang |
| SeamlessM4T v2 (Meta) | 2023 | 2.3B | S2ST | 100+ bahasa |
| Parakeet-TDT (NVIDIA) | 2024 | 0.6B-1.1B | FastConformer+TDT | WER terbaik English |
| Canary (NVIDIA) | 2024 | 1B | Multilingual | Top Open ASR Leaderboard |

### ASR Bahasa Indonesia
Tantangan: aglutinasi (ber-, meng-, -kan), code-switching ID-Inggris, 700+ bahasa daerah, data percakapan alami langka, Common Voice ID hanya ~50 jam vs LibriSpeech 1000 jam.

Strategi terbaik: fine-tune Whisper-large-v3 atau MMS-1B pada campuran:
- Common Voice ID
- NusaCrowd (100+ dataset NLP/speech Indonesia kurasi akademik)
- Bloom speech dataset
- SEACrowd (Lovenia EMNLP 2024, 498 dataset Asia Tenggara)
- OpenSLR SLR41 (Jawa), SLR44 (Sunda), SLR140 (ID STT)
- Data internal SIDIX

WER realistis:
- Whisper-v3 out-of-box: 15-20% WER pada ID formal.
- Fine-tune + LoRA (1-3% params): turun ke 8-12%.

Riset Adila et al. arXiv:2410.08828 (Okt 2024): Whisper fine-tuned **mengalahkan** Wav2Vec2 di berbagai skenario Indonesia; variabilitas gaya bicara = faktor pengaruh terbesar.

### ASR Tilawah Qur'an
- **Tarteel AI** (USA): ASR khusus Qur'an dengan transliterasi Arab + validasi tajwid real-time.
- Dataset **Everyayah**: 114 surah x ~20 qari mutawatir.
- Dataset **Tarteel**: 250k rekaman crowdsourced.
- Fine-tune Whisper pada tilawah + token huruf hijaiyah mencapai CER <3% untuk qari mutawatir.
- Target SIDIX: ikuti pola Tarteel + tambah decoder yang sadar hukum tajwid (idgham, ikhfa', mad).

### Pipeline Production ASR
1. **VAD**: Silero VAD (2 MB neural) atau WebRTC VAD.
2. **Diarization**: pyannote.audio 3.x atau NVIDIA NeMo.
3. **ASR**: Whisper / Wav2Vec2 fine-tuned.
4. **Punctuation restoration**: distilBERT head.
5. **Inverse text normalization**: angka, tanggal, mata uang.
6. **Forced alignment**: Montreal Forced Aligner untuk timestamp presisi.
7. **LM rescoring**: KenLM 4-gram atau neural LM.

### Metrik
- **WER** = (S+D+I)/N (substitusi+deletion+insertion).
- **CER** lebih cocok untuk Indonesia (morfologi kompleks) dan Arab Qur'an.
- **RTF** (Real Time Factor) <0.3 untuk production.
- **DER** (Diarization Error Rate) multi-speaker.

## Contoh Nyata
Transcribe dengan faster-whisper:
```python
from faster_whisper import WhisperModel
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe("voice_note.m4a", language="id", beam_size=5)
for seg in segments:
    print(f"[{seg.start:.2f} - {seg.end:.2f}] {seg.text}")
```

## Keterbatasan
- Whisper hallucinate pada audio sunyi panjang; butuh VAD pre-filter.
- Tidak mendeteksi hukum tajwid secara langsung — butuh post-classifier terpisah.
- MMS untuk dialek daerah Indonesia butuh fine-tune tambahan karena pretraining-nya pada Bible recordings (domain sempit).
- Latency Whisper-large-v3 ~5x realtime di CPU; butuh GPU atau Whisper-turbo/small untuk edge deployment VPS SIDIX.

## Sitasi
Radford et al. *Whisper* arXiv:2212.04356; Baevski et al. *Wav2Vec 2.0* arXiv:2006.11477; Pratap et al. *MMS* arXiv:2305.13516; Adila et al. arXiv:2410.08828; artefak compass user 2026-04-18.
