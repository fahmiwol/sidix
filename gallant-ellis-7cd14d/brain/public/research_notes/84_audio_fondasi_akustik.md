> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
id: 84
topic: audio_fondasi_akustik
tags: [audio, akustik, psikoakustik, dft, stft, mel, mfcc, signal_processing]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [85, 86, 87, 88, 89, 90, 91, 92]
---

# 84 — Audio: Fondasi Akustik dan Pemrosesan Sinyal

## Apa
Fondasi matematis dan fisik yang dibutuhkan SIDIX untuk "mendengar". Lapisan paling bawah dari 7 lapisan audio AI: fisika gelombang, psikoakustik, dan representasi sinyal (DFT/STFT/Mel/MFCC).

## Mengapa
Tanpa menguasai fondasi ini, setiap model audio hulu (ASR, TTS, MIR, generasi) jadi *black box* yang tidak bisa dipahami akar kegagalannya. Mayoritas pilihan hyperparameter di layer atas (window size STFT, jumlah Mel bin, sampling rate) diturunkan dari batasan fisik/persepsi. Untuk SIDIX yang berakar di epistemologi Islam, memahami *makhraj* dan *sifat huruf* di tajwid juga butuh framework akustik yang sama.

## Bagaimana

### Gelombang suara
- Gelombang tekanan longitudinal. 4 parameter: **frekuensi** (Hz), **amplitudo** (Pa / dB SPL), **fase**, **panjang gelombang** lambda = c/f.
- Kecepatan suara: 343 m/s (udara 20 C), 1480 m/s (air laut), 5120 m/s (baja).
- 0 dB SPL = 20 uPa referensi ambang dengar.

### Psikoakustik
- Equal-loudness contours ISO 226:2003 (revisi Fletcher-Munson 1933).
- Sensitivitas puncak 2-5 kHz (karena resonansi ear canal).
- Masking simultan dan temporal — dasar codec lossy.
- Critical bands Zwicker 24 Bark, ERB.
- Skala Mel: `m = 2595 * log10(1 + f/700)`.

### Timbre dan suara manusia
- Model source-filter: glottal pulse (sumber periodik harmonik) + vocal tract filter resonan.
- Formant F1/F2 menentukan vokal: /a/ F1~700 F2~1100; /i/ F1~270 F2~2300.
- Envelope ADSR = inductive bias untuk generative audio (DDSP, RAVE).

### Transformasi sinyal
- **DFT/FFT** O(N log N).
- **STFT** dengan window (Hann/Hamming/Blackman); parameter:
  - musik 44.1 kHz: `n_fft=2048, hop=512`.
  - speech 16 kHz: `n_fft=512, hop=160` (25/10 ms).
- **Mel spectrogram** = input standar Tacotron2/FastSpeech2 (80 mel), Whisper (80 mel log-compressed).
- **MFCC** pipeline: pre-emphasis alpha=0.97 -> frame -> Hamming -> FFT -> mel filterbank 26-40 -> log -> DCT type-II -> 13 koef + delta + delta-delta = 39-dim.
- **CQT** `f_k = f_min * 2^(k/b)` satu bin per semitone — ideal musik.
- Fitur bantu: chroma 12-dim, spectral centroid/rolloff/flatness, zero-crossing rate.

### Anatomi telinga
- Outer ear (pinna + canal resonansi 2-5 kHz) -> middle ear (malleus/incus/stapes) -> cochlea (basilar membrane = FFT biologis tonotopik) -> inner hair cells ~3500 -> auditory nerve -> brainstem -> primary auditory cortex (tonotopic map).

## Contoh Nyata
Kode librosa mengekstrak Mel spectrogram:
```python
import librosa
y, sr = librosa.load("tilawah.wav", sr=16000)
mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=512, hop_length=160, n_mels=80)
log_mel = librosa.power_to_db(mel)
```
Input ini langsung bisa dipakai untuk fine-tune Whisper-v3 untuk ASR tilawah.

## Keterbatasan
- Psikoakustik manusia tidak identik dengan psikoakustik model AI; SpecAugment masking justru dapat membantu robustness model.
- Skala Mel bias speech Barat; untuk maqamat Arab yang punya interval mikrotonal, CQT atau HCQT lebih presisi.
- Formant model tidak sempurna untuk bahasa dengan tone (Mandarin) atau artikulasi ekstrem pengkhasiran/idgham Arab.

## Sitasi
Zwicker & Fastl *Psychoacoustics* (Springer 2007); Rossing et al. *The Science of Sound* (2002); Muller *Fundamentals of Music Processing* (Springer 2015); artefak compass yang di-feed user 2026-04-18.
