# Qada–Qadar & kerangka keputusan (konsep untuk fondasi AI / RAG)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tujuan dokumen ini:** menyimpan **konversi konsep** ringkas sebagai **landasan berpikir** untuk model penalaran, indeks RAG, atau prompt sistem — **bukan** fatwa, **bukan** materi khutbah/ceramah, dan **bukan** pengganti konsultasi ulama atau ahli untuk hukum/akidah spesifik.

**Cara pakai:** kutipan dalam jawaban AI harus tetap mengikuti sanad/tabayyun repo; untuk hal sensitif hukum/akidah, arahkan pengguna ke sumber resmi dan ulama setempat.

**Tanggal catatan:** 2026-04-15 (diperkaya dari input kurasi pengguna; batch kedua: mazhab Syafi’i/Hanbal, keputusan Islam, metodologi penelitian).

---

## 1. Batas narasi (wajib dibaca pengembang & model)

| Ya | Tidak |
|----|--------|
| Analogi, definisi ringkas, pola “sebab–usaha–hasil” untuk **logika keputusan** | Menyatakan halal/haram spesifik tanpa dalil dan tanpa kualifikasi |
| Menyebut nama kitab/ulama sebagai **rujukan literatur** (bukan otoritas mutlak model) | Gaya dakwah/penggugah massa |
| Menekankan **tabayyun** dan batas keyakinan | Klaim “wakil mazhab” atau fatwa tertutup |

---

## 2. Referensi web (dasar bacaan awal — verifikasi mandiri)

Tautan disalin sebagaimana diserahkan; isi situs dapat berubah — **cek ulang** sebelum mengutip di produksi.

- Pengertian qada & qadar (ringkasan edukatif): [Ruangguru Blog — pengertian qada qadar](https://www.ruangguru.com/blog/pengertian-qada-qadar)
- Pengantar qada & qadar: [FAI UMSU — mengenal qada dan qadar](https://fai.umsu.ac.id/mengenal-qada-dan-qadar/)
- Tauhid — pengertian qadha dan qadar: [NU Online — ilmu tauhid](https://nu.or.id/ilmu-tauhid/ini-pengertian-qadha-dan-qadar-ra806)
- Rukun Islam & Rukun Iman (perbedaan & urutan): [BAZNAS — artikel](https://baznas.go.id/artikel-show/Rukun-Islam-dan-Rukun-Iman:-Perbedaan,-Urutan,-dan-Penjelasannya/1824)
- Makna rukun iman & Islam: [FAI UMSU — memahami makna](https://fai.umsu.ac.id/memahami-makna-dari-rukun-iman-dan-islam/)
- Keputusan & kualitas pilihan (konteks umum, bukan fiqh): [Industrial UII — agar keputusan kita menjadi yang terbaik](https://industrial.uii.ac.id/agar-keputusan-kita-menjadi-yang-terbaik/)
- Nasihat Rasulullah tentang keputusan suatu perkara (telaah hadis — **baca teks asli**): [Ilha UAD](https://ilha.uad.ac.id/nasihat-rasulullah-tentang-keputusan-suatu-perkara-telaah-suatu-hadis/)
- Materi ringkas rukun iman/islam (dokumen pihak ketiga — **saring sanad**): [Scribd — Rukun Iman dan Rukun Islam](https://www.scribd.com/document/533033513/Rukun-Iman-dan-Rukun-Islam-1)

**Pengambilan keputusan (blog / artikel umum — bukan fatwa):**

- Pendekatan Islam terhadap pengambilan keputusan (Medium): [The Islamic approach to decision making](https://medium.com/@usmankhaleeq56/the-islamic-approach-to-decision-making-9deb88bcf2f0)
- Lima langkah keputusan efektif (Productive Muslim): [5 steps to make effective decisions](https://productivemuslim.com/5-steps-to-make-effective-decisions/)
- Metode keputusan al-Qur’an (Quran Academy blog): [Quranic method for decisions](https://quranacademy.io/blog/quranic-method-decisions/)

---

## 3. Arsip PDF lokal (opsional — tidak di-commit)

File berikut disebutkan pengguna di mesin lokal Windows; **tidak** ada di repo. Bila ingin diindeks RAG, salin ke `brain/public/` (non-rahasia) atau `brain/private/` (sesuai kebijakan) dan jalankan indeks ulang.

| Judul / petunjuk | Lokasi asli (mesin pengguna) |
|------------------|------------------------------|
| Pertanyaan umum ateis (bahasa Inggris) | `c:\Users\ASUS\Downloads\New folder\most-common-questions-asked-athiests.pdf` |
| Dokumen FDK — Jeihan Hafiya Hernanto | `c:\Users\ASUS\Downloads\New folder\JEIHAN HAFIYA HERNANTO-FDK.pdf` |
| Skripsi / tugas — Yulia Safitri (190601069) | `c:\Users\ASUS\Downloads\New folder\Yulia Safitri(190601069).pdf` |
| *Kitab al-‘Umm* jil. 1 (pointer Z-Library — **cek legalitas salinan & sanad edisi**) | `c:\Users\ASUS\Downloads\New folder\KITAB-AL-UMM-1-FIQH-FIKIH-FIQIH-Imam-Syafii-Z-Library.pdf` |
| Aqidah & manhaj Imam al-Syafi’i | `c:\Users\ASUS\Downloads\New folder\Aqidah & Manhaj Imam Syafii.pdf` |
| Artikel teks (11-Article Text, 2021-06-24) | `c:\Users\ASUS\Downloads\11-Article Text-18-1-10-20210624.pdf` |
| Perkembangan pemikiran fiqh Imam Ahmad — konstruksi metode ijtihad | `c:\Users\ASUS\Downloads\6+PERKEMBANGAN+PEMIKIRAN+FIQIH+IMAM+AHMAD+BIN+HANBAL+KONSTRUKSI+METODE+IJTIHAD.pdf` |
| Artikel teks (900-Article Text, 2025-01-18) | `c:\Users\ASUS\Downloads\900-Article Text-3130-1-10-20250118.pdf` |
| *Application of Decision Making from Islamic Perspective* (judul dari nama file) | `c:\Users\ASUS\Downloads\ApplicationofDecisionMakingfromIslamicPerspectivebyDecisionMaker.pdf` |
| Dokumen `15.pdf` (isi — verifikasi manusia) | `c:\Users\ASUS\Downloads\New folder\15.pdf` |
| Islamic research methodology in contemporary research — *is it applicable?* | `c:\Users\ASUS\Downloads\New folder\islamic-research-methodology-in-contemporary-research-is-it-applicable.pdf` |

---

## 4. Inti konsep (ringkas — untuk struktur pengetahuan)

### 4.1 Qada vs Qadar (definisi pedagogis)

- **Qada’** (ketetapan): lapisan ketetapan ilahi dalam kerangka besar (metafora “blueprint” hanya analogi, bukan ilmu kalam formal di sini).
- **Qadar** (ketentuan peristiwa): perwujudan peristiwa dalam alam sehari-hari.

### 4.2 Empat pilar yang sering diajarkan (sebagai **skema ingatan** — bukan daftar hukum)

Dalam tradisi pengajaran populer, empat hal ini sering dikaitkan dengan qadar (nama Arab diseragamkan di sini sebagai label ingatan):

1. **Ilmu** — ilmu Allah meliputi segala sesuatu (konsep teologis; rincian dalil → kitab aqidah).
2. **Kitabah** — penulisan di Lauh Mahfuz (konsep teologis).
3. **Masyi’ah** — kehendak (konsep teologis).
4. **Khalq** — penciptaan peristiwa (konsep teologis).

**Untuk AI:** gunakan hanya sebagai **tag ontologi** atau **langkah refleksi**, bukan sebagai “output hukum”.

### 4.3 Tegangan klasik: takdir vs usaha (resolusi konseptual)

- Usaha manusia **bukan** “melawan” takdir dalam kosa kata pedagogis umum: usaha dipahami sebagai bagian dari rantai sebab-akibat yang juga dalam kerangka teologis dibahas ulama.
- Contoh yang sering dipakai dalam literatur: peristiwa **Umar** dan wabah — dipakai sebagai **ilustrasi naratif**, bukan dalil tunggal untuk fatwa kesehatan modern.

---

## 5. Tokoh & karya (pointer literatur — bukan endorsement otomatis)

Model boleh menyebut nama sebagai **historis** atau **rujukan bacaan lanjut**; kualitas sanad PDF harus diverifikasi manusia.

| Nama | Peran dalam catatan ini | Arah bacaan (manusia) |
|------|-------------------------|------------------------|
| Zakir Naik | Materi populer Q&A (bahasa Inggris/Indonesia) | Cari edisi resmi / transkrip; kritisi sumber |
| Ibnu Taimiyah | Diskusi kalam/takdir dalam korpus klasik | `Majmu‘ al-Fatawa`, risalah qadar — baca dengan guru |
| Al-Ghazali | Integrasi etika–hati | `Ihya’ ‘Ulum al-Din` — bagian terkait qadar/tawakkal |
| Ibnu Qayyim | Pembahasan sebab-akibat & hikmah | `Shifa’ al-‘Alil` — edisi terjemahan diverifikasi |
| ‘Umar Sulaiman al-Ashqar | Penyajian sistematis modern | `Al-Qada’ wa al-Qadar` — bandingkan beberapa syarah |

**Keyword pencarian bantu (manusia):** `filetype:pdf qada qadar islam`, `shifa al alil ibn qayyim`, `al qada wal qadar ashqar` — saring situs tepercaya (contoh repositori: archive.org, islamhouse.com, dll.) sebelum masuk indeks.

---

## 6. Kerangka keputusan (versi “logika umum” — tanpa fiqh spesifik)

Langkah berikut **disadur** dari pola yang pengguna susun; disesuaikan agar netral untuk AI penalaran umum:

1. **Pahami masalah** — pisahkan gejala vs akar.
2. **Validasi informasi** — sumber, bias, kelengkapan data.
3. **Risiko & batas** — etika, hukum umum (bukan fatwa), dampak pihak ketiga.
4. **Niat / tujuan** — transparansi terhadap diri sendiri (refleksi, bukan pengadilan hati oleh model).
5. **Ikhtiar** — pilih aksi konkret dengan rencana cadangan.
6. **Tawakkal** — hasil akhir di luar kontrol penuh manusia (framing psiko-spiritual umum, bukan klaim teologi mendalam oleh LLM).

**Satu kalimat ringkas (untuk prompt / sistem):**  
*Berpikir dengan ilmu yang terverifikasi, memilih dengan sadar, bertindak dengan usaha, menerima ketidakpastian hasil dengan sikap tawakkal — tanpa model mengklaim otoritas agama.*

---

## 7. Format output opsional (potongan prompt — gaya “insight manusiawi”)

Potongan berikut boleh disematkan sebagai **instruksi format** di persona “TOARD” / “MIGHAN” bila cocok; tetap **larangkan** fatwa tertutup.

```text
INSIGHT UTAMA:
(singkat, tajam, relate)

ANALISIS:
(realitas & data)

OPSI KEPUTUSAN:
- opsi 1: …
- opsi 2: …
- opsi 3: …

REKOMENDASI:
(pilihan + alasan non-hukum spesifik kecuali ada rujukan teks)

REFLEKSI:
(nilai umum & batas keyakinan; tawakkal sebagai sikap, bukan klaim takdir per individu)
```

Bahasa: santai/manusiawi **boleh**; motivasi klise dan janji pasti **dihindari**.

---

## 8. Metode belajar ulama → analogi pipeline data (hanya analogi)

| Klasik | Analogi modern (AI / data) |
|--------|----------------------------|
| Talaqqi | Kurasi dataset & mentor manusia |
| Takrar | Ulang eval / regresi |
| Kitabah | Logging terstruktur |
| Mudzakarah | Uji redaksi / peer review |
| Amal | Deploy & umpan balik lapangan |

---

## 9. Tautan ke dokumen lain di repo

- IHOS & batasan epistemik: `principles/06_ihos_islamic_human_operating_system.md`
- Mode jawaban SIDIX: `28_sidix_epistemic_modes_multi_perspective.md`
- Feeding & indeks: `31_sidix_feeding_log.md`

---

*Entri ini memenuhi permintaan “catat” + menambah referensi dasar (termasuk batch Syafi’i/Hanbal, keputusan Islam, PDF akademik); pengembang bertanggung jawab memfilter isi URL/PDF sebelum promosi ke produksi.*
