---
id: 89
topic: audio_generasi_musik
tags: [audio, music_generation, musicgen, stable_audio, yue, audioldm, suno, diffusion, watermark, audioseal]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [85, 87, 88, 90, 91, 92]
---

# 89 — Audio: Generasi Musik, Suara Efek, dan Watermarking

## Apa
Kapabilitas SIDIX untuk **membuat musik** dan **suara efek** dari teks, melodi, atau chord. Mencakup open-source (MusicGen, Stable Audio Open, YuE, AudioLDM 2) dan landscape komersial (Suno, Udio, Seed-Music) plus isu etika (RIAA lawsuit) + watermark wajib (AudioSeal, SynthID Audio).

## Mengapa
- Produk seperti nasyid-AI, musik tradisional Indonesia yang di-generate (gamelan/keroncong/dangdut), atau soundtrack untuk konten edukasi butuh kapabilitas ini.
- 2024-2026 = era lompatan: Suno v5 menghasilkan lagu 4 menit dengan vokal + lirik nyaris tak terbedakan.
- Kebijakan syariah: generasi musik harus disertai filter konten (blokir lirik haram) dan watermark.

## Bagaimana

### Paradigma generatif
1. **Autoregressive waveform** (WaveNet, SampleRNN) — lambat sample-level.
2. **GAN** (WaveGAN, GANSynth) — kualitas terbatas.
3. **VAE** (RAVE realtime) — good untuk timbre transfer.
4. **Diffusion** (DiffWave, AudioLDM 1/2, Stable Audio) — kualitas tinggi.
5. **Token-based transformer atas neural codec** (AudioLM, MusicLM, MusicGen, VALL-E) — paradigma dominan.
6. **Flow matching** (Audiobox Meta, Stable Audio Open 2) — cepat + kualitas diffusion.

### Text-to-music SOTA 2026
| Model | Organisasi | Tipe | Lisensi | Durasi | Catatan |
|-------|-----------|------|---------|--------|---------|
| **MusicGen** | Meta | AR transformer + EnCodec | MIT/CC-BY-NC | 30s | Open, melody-cond variant |
| **Stable Audio 2/Open** | Stability AI | Latent diffusion | Komersial/CC | 3 menit | SOTA open, 44.1 kHz stereo |
| **AudioLDM 2** | Univ Surrey | Latent diffusion | CC-BY-NC | Variable | SFX + music |
| **MusicLM** | Google | Hierarki token | Tertutup | 5 menit | Teks + melodi |
| **Suno v4/v5/v5.5** | Suno AI | Proprietary | Komersial | 4-8 menit | SOTA lagu + vokal + lirik; April 2026 ~2M subs, $300M ARR |
| **Udio** | Uncharted Labs | Proprietary | Komersial | 15 menit | Inpainting |
| **YuE** | Open-source | Token-based | Apache 2.0 | 5 menit | Full-song open 2025 |
| **DiffRhythm** | 2024 | Diffusion end-to-end | Open | 4+ menit | Full-length song |
| **Seed-Music** | ByteDance | Flow matching | Tertutup | Variable | Lyric-to-song high quality |
| **Riffusion** | Open | Spectrogram diffusion | Open | 12s loop | Prompt-based loops |
| **Fugatto** | NVIDIA | Generative transformer | Tertutup | Variable | Composing instruction unik |
| **JEN-1, MAGNeT, JASCO** | Open | Masking + parallel decode | Open | Variable | Efisiensi |

### Conditioning modalities
- Teks prompt (di-encode via T5/FLAN-T5/CLAP).
- Melody (MusicGen-Melody menerima chroma target).
- Chord progression.
- Genre/mood tags.
- Audio-to-audio style transfer.
- Lyrics-to-song (Suno/Udio/YuE).

### Sound Effects & Foley
- **AudioGen** (Meta 2022) text-to-SFX.
- **AudioLDM 2** (Univ Surrey).
- **Stable Audio Open** untuk SFX.
- **V2A (Video-to-Audio)**: Meta MovieGen Audio, Google Lumiere V2A, ElevenLabs Sound Effects API.

### Watermarking (WAJIB untuk SIDIX)
- **AudioSeal** (Meta): imperceptible watermark yang tetap terdeteksi setelah kompresi/noise.
- **SynthID Audio** (Google DeepMind): watermark post-hoc detectable.
Kebijakan SIDIX: setiap output music-gen **harus** di-watermark + log audit.

### Isu Hukum 2024-2026
- **RIAA menggugat Suno dan Udio Juni 2024** atas dugaan pelatihan dari katalog copyright. Putusan akan membentuk masa depan industri.
- SIDIX kebijakan: hanya train/fine-tune pada dataset berlisensi jelas (CC, domain publik, dataset berlisensi).

### Evaluasi
- **FAD** (Frechet Audio Distance, analog FID).
- **KL divergence** pada CLAP embedding.
- **CLAP-score** text-adherence.
- **MOS** manusia untuk kualitas musikal.

### Rekomendasi untuk Indonesia
- Fondasi open: MusicGen + Stable Audio Open.
- Singing: DiffSinger + RVC (dengan consent).
- SFX: AudioLDM 2.
- Fine-tune pada gamelan/keroncong/dangdut — peluang riset terbuka.
- Integrasi AudioSeal untuk semua produk publik.

### Kebijakan Syariah SIDIX Music Gen
1. Filter konten: lirik NSFW/violence/syirik/khamr diblokir.
2. Hindari meniru qari/qariah mutawatir.
3. Watermark otomatis + log audit.
4. Fokus genre halal-by-default: nasyid, shalawat, gamelan, keroncong, murottal edukatif (dengan disclaimer).
5. Consent check untuk voice clone di dalam lagu.

## Contoh Nyata
MusicGen dengan Hugging Face transformers:
```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import scipy.io.wavfile

processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")

prompt = "gentle nasyid vocals with duff percussion, 80 BPM, Middle Eastern maqam"
inputs = processor(text=[prompt], padding=True, return_tensors="pt")
audio_values = model.generate(**inputs, max_new_tokens=512)
scipy.io.wavfile.write("nasyid.wav", rate=32000, data=audio_values[0, 0].numpy())
# TODO: apply AudioSeal watermark post-generation.
```

## Keterbatasan
- MusicGen small/medium sering menghasilkan artifact; large lebih baik tapi perlu GPU 16 GB+.
- Stable Audio Open belum sekuat Suno komersial.
- Generasi musik tradisional gamelan masih sulit karena data training minim; fine-tune custom dibutuhkan.
- Watermark AudioSeal bisa dihilangkan via re-recording (bocor audio) — tetap wajib sebagai deterrent.
- Hukum copyright masih berkembang; RIAA lawsuit bisa mengubah landscape 2026-2027.

## Sitasi
Artefak compass user 2026-04-18; MusicGen Copet arXiv:2306.05284; Stable Audio Evans arXiv:2407.14358; AudioSeal Meta 2024; SynthID Audio Google DeepMind.
