---
id: 88
topic: audio_mir_music_understanding
tags: [audio, mir, mert, beats, htdemucs, basic_pitch, clap, gamelan, instrument_recognition]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [84, 85, 89, 90, 91, 92]
---

# 88 — Audio: Music Information Retrieval (MIR)

## Apa
Kapabilitas SIDIX untuk **memahami musik**: beat, chord, key, melody, instrument recognition, source separation, genre/mood tagging. Termasuk pendekatan untuk musik tradisional Indonesia (gamelan, angklung, keroncong).

## Mengapa
- SIDIX perlu membedakan musik dari noise, vokal dari instrumen, beat dari ritme untuk menjalankan tool seperti `analyze_audio`, `classify_instrument`, `separate_stems`.
- MIR adalah fondasi untuk music generation yang terarah (tanpa paham tempo/chord, generasi jadi noise).
- Domain Indonesia: gamelan tidak equal-temperament; butuh model khusus.

## Bagaimana

### Tugas inti MIR
- **Pitch detection** monofonik: **CREPE** (Kim ICASSP 2018, CNN 6-layer). Polyphonic: **Basic Pitch** (Spotify 2022, 17K params, open).
- **Beat/downbeat tracking**: **Beat This!** transformer (Foscarin 2024), madmom, librosa.beat.
- **Chord recognition**: ChordFormer, Chordino + chromagram CNN.
- **Key estimation**: Krumhansl-Schmuckler + neural.
- **Genre classification**: musicnn (Pons), VGGish-style.
- **Melody extraction**: CREPE (mono), Basic Pitch (poly), SPICE (self-supervised).
- **Source separation** (bagian 7 dokumen):
  - Speech: Conv-TasNet, SepFormer, Mossformer.
  - Music: **HTDemucs v4** (Meta, 6-stem: vocals/bass/drums/piano/guitar/other), Spleeter (Deezer 2/4/5 stem), MDX-Net, Open-Unmix UMX.
  - Universal text-queried: AudioSep, LASS.
- **Structure analysis**: MSAF + self-similarity matrix.
- **Music tagging**: MagnaTagATune, MTG-Jamendo.

### Foundation model musik
| Model | Params | Pretraining | Tugas unggulan |
|-------|--------|-------------|----------------|
| **MERT** (M-A-P/HKUST) | 95M/330M | 160k jam + HuBERT-style + CQT teacher | SOTA 14 tugas MIR |
| **M2D-CLAP** (NTT) | 86M | AudioSet+music captions | GTZAN 75.17% zero-shot |
| **LAION-CLAP** | 153M | 633k audio-text pairs | ESC50 90.14% zero-shot |
| **BEATs** (Microsoft) | 90M | AudioSet iterative tokenizer | mAP 0.486 AudioSet |
| **Jukebox** (OpenAI) | 5B | 1.2M songs + lyrics | Raw music gen |
| **MuLan** (Google) | 750M | 44M music-text pairs | Text-music retrieval |

**Insight kontra-intuitif**: MERT-330M mengungguli JukeMIR 5B pada 14 tugas MIR (~15x lebih kecil). SSL + musical teacher > scale buta.

### Dataset
- **NSynth** (Google, 305k notes 1k+ instrumen).
- **MAESTRO** (piano + MIDI +-3ms).
- **MusicNet** (330 klasik annotated).
- **FMA** (106k tracks).
- **MTG-Jamendo** (55k multi-label).
- **IRMAS** (11 instrumen).
- **MedleyDB** (multi-track stems).
- **Slakh2100** (2100 synth multi-track).
- **OpenMIC-2018** (20k clips, 20 instrumen weak-label).
- Catatan: **GTZAN kontroversial** (duplikat + artist bias, Sturm 2014); validasi dengan FMA/MTG-Jamendo.

### Representasi musik
- MIDI (event-based), MusicXML (score), piano roll matriks [pitch x time], REMI tokens (Bar/Position/Tempo/Chord), Tonnetz geometri harmonik.

### Stack rekomendasi instrument recognition production
```
HTDemucs (separation) -> MERT-330M embedding per-stem
  -> multi-label sigmoid head (fine-tune: OpenMIC + IRMAS + Slakh + MedleyDB)
  -> augmentasi: SpecAugment + mixup
```
Pelengkap: LAION-CLAP untuk zero-shot tagging label terbuka; Basic Pitch untuk audio-to-MIDI multi-instrumen.

### Musik Tradisional Indonesia (peluang riset)
Riset ITS Surabaya, Kurniawati et al.:
- CNN-LSTM Automatic Note Generator Javanese Gamelan (International Journal of Intelligent Engineering and Systems).
- Dataset notasi gamelan Jawa publik (*Data in Brief* vol 53, 2024, DOI 10.1016/j.dib.2024.110116): balungan, bonang barung, bonang penerus, peking, struktural.
- Multi-Label 1D CNN bonang barung variasi (2023).
- IEEE 2024: Multi-Task Learning Autoencoder + Affine Transformation untuk overlap frekuensi metalofon.
- IEEE 2020 Regional Songs DRNN untuk angklung, gamelan, kulintang.
- Sinkron 2024: KNN 90% > CNN 85% pada Gangsa Bali.

Tantangan unik:
- Tuning non-equal-temperament (laras slendro 5 nada, pelog 7 nada).
- Fundamental overlap antar instrumen di oktaf sama.
- Inharmonisitas metalofon berbeda dari piano string.

### Metrik standar mir_eval + MIREX
- Beat F-measure +-70 ms.
- Chord WCSR.
- Transcription note F1.
- SDR/SI-SDR untuk separation.

## Contoh Nyata
Beat tracking dengan librosa (baseline sederhana):
```python
import librosa
y, sr = librosa.load("lagu.mp3", sr=22050)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print(f"Tempo: {tempo:.2f} BPM, jumlah beat: {len(beats)}")
```
Source separation dengan HTDemucs via demucs CLI:
```bash
demucs --two-stems=vocals nasyid.mp3  # pisah vokal vs instrumen
```

## Keterbatasan
- MERT dilatih mayoritas musik Barat/pop; transfer ke gamelan butuh adaptasi.
- Basic Pitch polyphonic tidak sempurna pada tekstur padat (orkestra atau gamelan ensemble).
- Source separation pada musik tradisional sering gagal karena stem pola tidak seperti band Barat (drum/bass/vocal/guitar).
- Zero-shot LAION-CLAP bias pada deskripsi bahasa Inggris.

## Sitasi
Artefak compass user 2026-04-18; MERT Li arXiv:2306.00107; Basic Pitch Spotify arXiv:2203.09893; HTDemucs Defossez arXiv:1909.01174 + v4; Kurniawati et al. *Data in Brief* 53/2024 DOI 10.1016/j.dib.2024.110116.
