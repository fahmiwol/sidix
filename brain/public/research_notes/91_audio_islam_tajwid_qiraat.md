> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
id: 91
topic: audio_islam_tajwid_qiraat
tags: [islam, tajwid, qiraat, maqam, fiqh_ghina, tarteel, maqashid, consent, voice_cloning_ethics]
created_at: 2026-04-18
source: audio_capability_track_2026_04_18
related_notes: [86, 87, 88, 89, 90, 92]
---

# 91 — Audio + Islam: Tajwid, Qira'at, Maqam, dan Etika

## Apa
Kerangka syariah dan fikih untuk kapabilitas audio SIDIX: hukum musik (fiqh al-ghina' wal-musiqa), ilmu tajwid, qira'at mutawatir, maqamat Arab, serta etika voice cloning dalam bingkai maqashid syariah.

## Mengapa
- SIDIX = AI dengan akar epistemologi Islam. Setiap kapabilitas audio harus dievaluasi lewat lensa maqashid.
- Al-Qur'an punya ilmu fonetik berabad sebelum fonetik Barat (tajwid, makhraj). Ini aset bukan hambatan.
- Fatwa kontemporer Al-Azhar + MUI 2023-2024 sudah membuka jalan untuk AI Qur'an halal jika kondisi terpenuhi.

## Bagaimana

### Fiqh al-Ghina' wal-Musiqa — Tiga Posisi

**Posisi 1: Haram mutlak**
- Sebagian Hanbali, Zahiri, ulama kontemporer Ibn Baz, al-Albani, Utsaimin, sebagian fatwa Saudi.
- Dalil: QS Luqman:6 (*lahw al-hadits*, Ibn Mas'ud menafsir sebagai nyanyian); hadits Bukhari 5590 tentang *ma'azif* (alat musik).

**Posisi 2: Mubah bersyarat** (mayoritas empat mazhab kontemporer)
- Dalil: hadits Aisyah izin dua jariyah bernyanyi di rumah Nabi ﷺ pada hari raya (Bukhari 952, Muslim 892); hadits duff di pernikahan; "hiasilah Al-Qur'an dengan suaramu" (Abu Dawud).
- Syarat:
  1. Lirik tidak mengandung konten haram (cabul, syirik, khamr, kebencian).
  2. Tidak melalaikan dari kewajiban.
  3. Tidak bercampur dengan kemungkaran (ikhtilat, khamr).
  4. Tidak berlebihan.

**Posisi 3: Mubah luas**
- Ibn Hazm, sebagian Syafi'iyah, Al-Ghazali dalam *Ihya'* (sama' dengan syarat).
- Yusuf al-Qaradawi *al-Halal wal-Haram* + *Fiqh al-Ghina' wal-Musiqa*.
- Fatwa Dar al-Ifta Mesir + Al-Azhar.

**MUI Indonesia**: moderat — musik mubah bersyarat; haram bila lirik/konten langgar syariat.

### Suara Wanita
- Mayoritas ulama: suara wanita **bukan aurat mutlak** (wanita bicara di hadapan Nabi ﷺ dan sahabat).
- Larangan bila *takhannuts* (mendayu-dayu membangkitkan syahwat — QS Al-Ahzab:32).
- **Implikasi TTS**: rekam suara wanita untuk pendidikan/aksesibilitas/navigasi = diperbolehkan. Untuk nyanyian seduktif komersial = yang diperselisihkan.

### Ilmu Tajwid
- **Makhraj**: 17 titik artikulasi (halq, lisan, syafatayn, khaysyum, jawf).
- **Sifat huruf**:
  - Jahr/hams (keras/lembut).
  - Syiddah/rakhawah (kuat/lemah).
  - Isti'la/istifal (naik/turun).
  - Ithbaq/infitah, dll.
- **Hukum mim + nun sakinah**:
  - Izhhar (jelas).
  - Idgham (penggabungan, dengan/tanpa ghunnah).
  - Ikhfa' (samar).
  - Iqlab (ubah menjadi mim).
- **Mad**: panjang bacaan dengan satuan harakat (2, 4, 6).

### Qira'at Mutawatir
**Tujuh (sab'ah)**:
1. Nafi' (Madinah) - rawi Qalun + Warsh.
2. Ibn Kathir (Makkah).
3. Abu Amr (Basrah).
4. Ibn Amir (Syam).
5. Asim (Kufah) - rawi Hafs + Syu'bah. (Paling tersebar hari ini, Hafs an Asim = mushaf standar).
6. Hamzah (Kufah).
7. Al-Kisai (Kufah).

**Tambahan (tiga, menjadi 'asyarah)**:
8. Abu Ja'far.
9. Ya'qub.
10. Khalaf.

### Maqamat Arab
Tujuh maqam utama: **Bayati, Hijaz, Nahawand, Rast, Saba, Sikah, Ajam**.
Mayoritas ulama membolehkan penggunaan maqam dalam tilawah **selama**:
- Tidak keluar dari kaidah tajwid.
- Bukan *lahn jali* (kesalahan yang mengubah makna).
- Tidak *taghanni* berlebihan yang mengganggu khushu'.
Hadits: "Bukan dari golongan kami yang tidak memperindah (*tatanny*) bacaan Al-Qur'an" (Bukhari 7527).

### AI untuk Al-Qur'an — State of the Art
- **Tarteel AI** (USA): ASR Qur'an + validasi hafalan + tajwid real-time. 250k rekaman crowdsourced. Didukung fatwa yang membolehkan.
- **Ayah / Quran.com**: rekognisi ayat by voice.
- Dataset **Everyayah**: semua qari mutawatir membaca 114 surah.
- **AI Tajweed verification**: klasifikasi neural kualitas tajwid. Diterima ulama sebagai alat bantu pendidikan.
- **Qira'at classifier**: CNN/LSTM membedakan 7/10 qira'at (riset Shahriar & Tariq 2022).
- **Kurdish maqam detection** (2026): "Voices of the Mountains" deteksi error pitch/ritme/modal-stability.

### TTS Qur'an
Fatwa Al-Azhar + MUI 2023-2024:
- **Diperbolehkan** untuk pendidikan + disclaimer.
- Output **bukan** suara qari mutawatir.
- **Bukan** pengganti talaqqi (transmisi lisan).
- **Dilarang** meniru suara qari terkenal tanpa izin (ghibah digital / pelanggaran *haqq al-sautiyyah*).

### Voice Cloning — Etika Islam
Prinsip:
- **Amanah**: data suara = titipan.
- **Consent**: wajib izin pemilik suara.
- Larangan **kidzb** (dusta) dan **ghibah** (menisbahkan perkataan palsu).
- **Sadd al-dzari'ah**: tutup jalan keburukan (deepfake = fitnah potensial).

Fatwa MUI 2023-2024 + Al-Azhar: **haram** deepfake yang memfitnah, meniru ulama, atau menyebarkan disinformasi.

Konsensus yang dibangun: **halal** untuk aksesibilitas (hidupkan suara keluarga atas izin), pendidikan dengan disclaimer, produksi kreatif berlisensi. **Haram** untuk penipuan, impersonasi ulama/pejabat, konten seksual.

### Maqashid Syariah sebagai Kerangka Evaluasi AI Audio
- **Hifz al-din**: tidak promosi kemaksiatan atau menyalahgunakan nama suci.
- **Hifz al-'aql**: tidak mengalihkan akal dengan konten merusak.
- **Hifz al-nasab wal-'ird**: suara = identitas; lindungi dari pencurian.
- **Hifz al-mal**: hak cipta = bentuk mal.
- Dilengkapi **maslahah** (manfaat umat), **sadd al-dzari'ah** (tutup celah), **istihsan** (preferensi hukum).

### Rekomendasi Praktis Developer AI Audio Muslim (Checklist SIDIX)
1. Filter konten training: classifier NSFW/violence/syirik + blacklist + semantic detection.
2. Dataset Qur'an: hanya qari mutawatir bersanad (Al-Ghamidi, Husary, Sudais, Minshawi, Afasy) dengan tajwid terverifikasi.
3. Tidak meniru qari tanpa izin tertulis ahli waris.
4. Disclaimer transparan pada TTS Qur'an: "bukan pengganti talaqqi".
5. Fokus nasyid + shalawat sebagai genre utama produk musik-AI untuk pasar Muslim.
6. Consent by design voice cloning: verifikasi + persetujuan tertulis + watermark.
7. Moderasi output generatif: filter lirik otomatis + blokir impersonasi tokoh agama.
8. Kolaborasi dewan syariah internal / MUI Digital.
9. Adzan dan ibadah tidak digantikan AI.

## Contoh Nyata
Skema validasi tajwid (stub, untuk diisi ML model):
```python
def validate_tajweed_stub(audio_path: str, ayah_text: str) -> dict:
    """
    Return: {
      'makhraj_score': 0-1,
      'mad_errors': [list],
      'idgham_errors': [list],
      'overall_tajweed': 0-1,
      'consent_verified': True (wajib),
      'mutawatir_match': list (qira'at detected),
    }
    """
    # Implementasi nyata: Whisper fine-tuned on Everyayah + classifier tajwid rules.
    ...
```

## Keterbatasan
- Klasifikasi tajwid neural bisa salah pada bacaan non-standar (qira'at langka); butuh validasi ustadz manusia.
- Fatwa bisa berubah; SIDIX harus dapat update kebijakan (versioned policy file).
- Suara wanita dalam nasyid: masih ada perbedaan mazhab kontemporer; SIDIX sebaiknya default conservative (opt-in).
- Maqam detection bias pada qari Arab tertentu; qari Asia Tenggara dengan gaya lokal bisa terklasifikasi error.

## Sitasi
Artefak compass user 2026-04-18; Al-Qaradawi *al-Halal wal-Haram* + *Fiqh al-Ghina' wal-Musiqa*; Al-Ghazali *Ihya' Ulum al-Din*; fatwa Al-Azhar + MUI 2023-2024; Shahriar & Tariq 2022 Maqam Classifier; Tarteel AI dataset.
