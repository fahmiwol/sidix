---
id: 85
topic: audio_representasi_digital
tags: [audio, digital, nyquist, codec, encodec, dac, snac, neural_codec, rvq]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [84, 86, 87, 89, 90, 92]
---

# 85 — Audio: Representasi Digital dan Neural Codec

## Apa
Jembatan antara dunia fisik (gelombang tekanan analog) dan dunia matematika AI (tensor/token). Mencakup sampling, quantization, codec tradisional, dan yang krusial di era 2024-2026: **neural audio codec** yang menghasilkan **token diskret** sebagai "bahasa" audio untuk LLM.

## Mengapa
- Tanpa pemahaman Nyquist + bit depth, kita tidak bisa memilih sampling rate yang tepat (16 kHz vs 24 kHz vs 44.1 kHz).
- Neural codec (EnCodec, DAC, SNAC, Mimi) adalah **prasyarat kompetitif** untuk Audio-LLM modern: AudioLM, MusicGen, VALL-E, Moshi beroperasi pada token diskret, bukan waveform.
- Insight kontra-intuitif: "token audio diskret adalah lingua franca baru audio AI" (dari dokumen compass).

## Bagaimana

### Teorema sampling
- Nyquist-Shannon: `f_s >= 2 * f_max`.
- Pilihan standar:
  - 16 kHz: ASR modern, VoIP wideband (0-8 kHz cakup formant speech).
  - 22.05 / 24 kHz: TTS.
  - 44.1 kHz: CD.
  - 48 kHz: pro studio.

### Bit depth dan SNR
- `SQNR ~= 6.02 * B + 1.76 dB`.
- 16-bit = 96 dB dynamic range (cukup musik).
- 24-bit = 144 dB (pro).

### Codec hierarki
1. **Lossless**: WAV (PCM mentah), FLAC (~50% kompresi tanpa hilang), ALAC.
2. **Lossy psychoacoustic**: MP3, AAC, OGG Vorbis, Opus (terbaik speech 16-32 kbps).
3. **Neural audio codec** (2022-2026):
   - **EnCodec** (Meta 2022): 6 kbps, 24 kHz.
   - **SoundStream** (Google, dasar Lyra v2).
   - **DAC** (Descript): high-fidelity.
   - **SNAC** (hierarchical, 12 Hz semantic + 75 Hz acoustic).
   - **Mimi** (Kyutai, dipakai Moshi).
   - Semua memakai **RVQ (Residual Vector Quantization)** untuk menghasilkan multiple codebook; MusicGen pakai 4 codebook dari EnCodec dengan delay pattern.

### Mengapa token diskret penting
- LLM autoregresif dilatih prediksi next-token; audio jadi sequence token yang bisa di-model sama seperti teks.
- Round-trip: audio -> encoder -> token -> (LLM generate) -> decoder -> audio.
- Throughput: EnCodec ~75 token/detik untuk 24 kHz dengan 8 codebook.

### Pre-processing pipeline standar
1. Resampling SoXR HQ.
2. Normalisasi peak/RMS/LUFS EBU R128 -23.
3. Silence removal Silero VAD (neural 2 MB) atau WebRTC VAD.
4. Denoising DeepFilterNet atau Facebook Denoiser.
5. Dereverberation WPE.

### Augmentasi SOTA
- **SpecAugment** (Park et al. 2019 Google): time warping + frequency masking (F=27) + time masking (T=100). Standar de-facto ASR.
- Pitch shift +-2 semitone.
- Time stretch 0.9-1.1x.
- Speed perturbation Kaldi 3x.
- Noise injection MUSAN/AudioSet dengan SNR 0-20 dB.
- RIR convolution (BUT ReverbDB) untuk robustness far-field.
- Mixup `x_tilde = lambda * x_i + (1-lambda) * x_j`.
- Codec augmentation (re-encode Opus low-bitrate).

## Contoh Nyata
Encode audio ke token EnCodec:
```python
from encodec import EncodecModel
import torchaudio
model = EncodecModel.encodec_model_24khz()
model.set_target_bandwidth(6.0)
wav, sr = torchaudio.load("nasyid.wav")
with torch.no_grad():
    encoded = model.encode(wav.unsqueeze(0))
codes = encoded[0][0]  # [B, K=8 codebook, T]
# Setiap frame sekarang dapat diperlakukan sebagai "token" seperti teks.
```

## Keterbatasan
- Neural codec butuh GPU untuk encode/decode real-time; latency bisa jadi bottleneck.
- Kompresi tinggi (1.5 kbps) di EnCodec mulai kehilangan timbre tipis — untuk musik 44.1 kHz stereo biasanya butuh DAC atau Stable Audio Open encoder.
- Tokenisasi audio membuat retraining sulit karena codebook model-specific (tidak interoperable antar Encodec/DAC/SNAC).
- Untuk Qur'an dan maqam mikrotonal, kompresi RVQ standar bisa menghilangkan detail quartertone; butuh codec fine-tuned di domain.

## Sitasi
Artefak compass user 2026-04-18; Defossez et al. *High Fidelity Neural Audio Compression* (EnCodec, arXiv:2210.13438); Zeghidour et al. *SoundStream* (2022).
