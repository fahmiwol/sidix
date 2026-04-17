---
id: 87
topic: audio_tts_voice_cloning
tags: [audio, tts, f5tts, xtts, vits, voice_cloning, consent, ethics, svs, nasyid]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [84, 85, 86, 88, 91, 92]
---

# 87 — Audio: TTS, Voice Cloning, dan Singing Synthesis

## Apa
Kapabilitas SIDIX untuk **berbicara** dan **bernyanyi**: konversi teks menjadi gelombang suara, dengan opsi zero-shot voice cloning (F5-TTS, XTTS v2) dan Singing Voice Synthesis (DiffSinger, NNSVS) untuk nasyid/anasheed. Termasuk etika *consent by design*.

## Mengapa
- Untuk output suara: SIDIX jadi bisa "berbicara" ke user (voice note balasan, pembacaan teks Indonesia, tilawah edukatif).
- Voice cloning zero-shot 2024-2026 = kenyataan (F5-TTS dengan 5-10 detik referensi). Ini pedang bermata dua: aksesibilitas vs deepfake.
- Islam: voice adalah bagian dari *'ird* (kehormatan); meniru suara tanpa izin = potensi *kidzb*/*ghibah* digital. Fatwa Al-Azhar + MUI 2023-2024: haram untuk impersonasi qari mutawatir tanpa izin.

## Bagaimana

### Evolusi Neural TTS
- Concatenative (2000-2010) -> HMM parametric HTS -> **Tacotron 2** (Google 2017, seq2seq + WaveNet vocoder, MOS 4.53) -> **FastSpeech 2** (Microsoft 2020, non-AR, variance adaptor pitch/energy/duration) -> **VITS/VITS2** (end-to-end flow+GAN+VAE) -> **NaturalSpeech 3** (Microsoft 2024 latent diffusion factorized).

### Generasi 2024 SOTA
- **F5-TTS** (Chen SJTU 2024, arXiv:2410.06885): non-AR conditional flow matching, zero-shot voice clone dari 5-10 detik, training sederhana, muat RTX 3090/4090 24GB.
- **E2-TTS** (Microsoft 2024): Embarrassingly Easy non-AR tanpa alignment eksplisit.
- **CosyVoice** (Du Alibaba 2024, arXiv:2407.05407): scalable multilingual + emotion + instruction-following.
- **Seed-TTS** (ByteDance, arXiv:2406.02430): human parity.
- **VALL-E 2** (Microsoft, arXiv:2406.05370): neural codec LM, human parity zero-shot.
- **XTTS v2** (Coqui, open): 17 bahasa termasuk Indonesia eksperimental.
- **StyleTTS 2** (Li NeurIPS 2023, arXiv:2306.07691): style diffusion + adversarial.
- **OpenVoice v2** (MyShell): flexible voice clone.
- **Kokoro TTS** (82M): edge-friendly.
- **Bark** (Suno): tawa, musik, multilingual via AudioLM-style.

### Vocoder
- WaveNet (AR lambat) -> **HiFi-GAN** (Kong NeurIPS 2020, arXiv:2010.05646; multi-period + multi-scale D, 167x realtime V100) -> **BigVGAN** (NVIDIA 2022, universal cross-domain) -> **Vocos** 2023 (Fourier-based, sangat cepat) -> neural codec decoders (EnCodec/DAC/SNAC) untuk round-trip token-audio.

### Ekspresifitas
- Prosody adaptor eksplisit (F0/energy/duration di FastSpeech 2).
- Global Style Tokens (Tacotron-GST, Wang 2018).
- Emotional TTS dengan label (ESD, IEMOCAP).
- Prompt-based terbaru: "excited whisper" atau audio reference 3 detik kontrol gaya.

### Voice Cloning dan Etika
- Speaker embedding era: d-vector (Variani 2014), x-vector (Snyder 2018), ECAPA-TDNN (Desplanques 2020).
- Zero-shot modern (F5-TTS, VALL-E 2) sudah tidak butuh embedding eksplisit; in-context learning langsung dari reference audio.
- **Mitigasi deepfake**:
  - **AudioSeal** (Meta): watermark imperceptible.
  - **SynthID Audio** (Google DeepMind): watermark post-hoc detectable.
- **Consent by design** (wajib untuk SIDIX):
  1. Verifikasi identitas pemilik suara.
  2. Persetujuan tertulis eksplisit.
  3. Watermark otomatis di output.
  4. Log audit siapa memanggil voice clone kapan.
  5. Blokir impersonasi tokoh agama / qari mutawatir.

### TTS Bahasa Indonesia
- Struktur fonologi lunak: 5 vokal cardinal, silabel CV/CVC mayoritas -> relatif mudah.
- Dataset: Indonesian LJSpeech-style (TTS-ID), MLS-ID, corpus UI/ITB, MMS-TTS-ind (Meta 2023 gratis HF).
- Rekomendasi: fine-tune XTTS v2 atau F5-TTS pada 10-20 jam rekaman studio.

### TTS Al-Qur'an
- Posisi fatwa Al-Azhar + MUI 2023-2024: **diperbolehkan** jika:
  - Tidak diklaim sebagai ibadah kanonik.
  - Bukan pengganti talaqqi.
  - Tidak meniru qari mutawatir tanpa izin.
  - Disclaimer transparan pada output.
- Implementasi: fonem Arab + aturan tajwid mekanis (makhraj + sifat).

### Singing Voice Synthesis
SVS != TTS (pitch kontinu, vibrato, breath, sinkronisasi MIDI-lyric):
- **DiffSinger** (Liu AAAI 2022, arXiv:2105.02446): diffusion + shallow diffusion mechanism.
- **VISinger 2**: VITS untuk singing + F0 predictor.
- **SiFiSinger** (2024), **NNSVS** toolkit open-source.
- Komersial: VOCALOID (Yamaha 2003), Synthesizer V (Dreamtonics), ACE Studio (Timedomain).
- Voice conversion komunitas: So-VITS-SVC, RVC — kontroversial hak cipta.
- Dataset: OpenSinger, M4Singer, NUS-48E, JVS-MuSiC.
- **Dataset Indonesia/Melayu untuk singing belum ada publik signifikan — peluang riset terbuka untuk SIDIX.**

### Evaluasi
- **MOS** subjektif 1-5 (gold standard).
- **UTMOS / NISQA**: neural predictor otomatis.
- **MCD** (Mel Cepstral Distortion).
- **WER-based**: jalankan ASR pada output TTS -> harus rendah.

## Contoh Nyata
Voice clone dengan XTTS v2 (ethics-compliant, butuh consent explicit):
```python
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
# Hanya boleh dijalankan setelah log consent di consent_registry.jsonl
tts.tts_to_file(
    text="Assalamu'alaikum, ini ujian sintesis suara Bahasa Indonesia.",
    speaker_wav="consented_voice_sample.wav",
    language="id",
    file_path="output.wav",
)
# Tambahkan watermark AudioSeal setelah generate (best practice).
```

## Keterbatasan
- Voice cloning zero-shot bisa jebol bahkan watermark yang paling kuat via re-recording; tidak ada pertahanan sempurna.
- TTS Qur'an dengan suara sintetik pasif sering terasa "dingin" dibanding qari manusia; nilai talaqqi hilang.
- SVS untuk maqam Arab mikrotonal butuh adaptasi F0 predictor yang mendukung interval quartertone.
- Fatwa berubah: kebijakan SIDIX harus dapat di-update ketika MUI/Al-Azhar merilis fatwa baru.

## Sitasi
Artefak compass user 2026-04-18; F5-TTS Chen arXiv:2410.06885; XTTS Coqui; DiffSinger Liu AAAI 2022; fatwa Al-Azhar + MUI 2023-2024.
