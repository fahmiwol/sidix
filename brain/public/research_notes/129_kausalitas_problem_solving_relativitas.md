# 129 — Kausalitas, Problem Solving & Relativitas Sebab-Akibat

## Sumber
- PDF: BAB II_1811150.pdf (Metode Pemecahan Masalah — skripsi/akademik)
- Scribd: Metode Pemecahan Masalah, Sistem Pemrosesan Informasi, Problem Solving
- Framing dari Fahmi: "sebab + akibat = mitigasi risiko / perluas peluang"

---

## Insight Inti — Relativitas Sebab-Akibat

> **Sebab + Akibat = Mitigasi Risiko / Perluas Peluang**

Ini bukan hanya rumus problem solving. Ini adalah **cara melihat realitas**.

```
Realitas selalu bergerak dalam pasangan:
  Sebab   →   Akibat
  Input   →   Output
  Tindakan → Konsekuensi

Kalau kamu tahu hubungan ini:
  → Kamu bisa CEGAH akibat buruk (mitigasi risiko)
  → Kamu bisa PERKUAT akibat baik (perluas peluang)
  → Kamu tidak lagi bereaksi — kamu bisa BERNAVIGASI
```

**Relativitas** di sini bukan Einstein. Ini tentang:
> Setiap fenomena bersifat relatif terhadap penyebabnya.
> Tidak ada masalah yang muncul tanpa sebab.
> Tidak ada peluang yang ada tanpa kondisi yang memungkinkannya.

---

## Kerangka Dasar: Problem Solving Sebagai Ilmu Kausalitas

### Definisi
Metode pemecahan masalah adalah **pendekatan sistematis** untuk:
1. Mengidentifikasi masalah
2. Menganalisis sebab-akibatnya
3. Menemukan solusi efektif

Ini melatih: berpikir kritis, pengumpulan data, evaluasi alternatif → keputusan terbaik.

### 6 Tahapan Utama
```
Tahap 1: IDENTIFIKASI MASALAH
  → Apa masalahnya? Definisikan dengan jelas.
  → Jangan solve masalah yang salah.
  Pertanyaan kunci: "Apa yang sebenarnya terjadi vs apa yang seharusnya terjadi?"

Tahap 2: ANALISIS MASALAH
  → Kumpulkan data. Cari AKAR PENYEBAB.
  → Gejala ≠ penyebab. Jangan tertipu.
  Alat: 5 Whys, fishbone diagram, data collection

Tahap 3: RUMUSKAN ALTERNATIF SOLUSI
  → Bukan hanya SATU solusi — cari BANYAK kemungkinan
  → Brainstorming tanpa judgment dulu
  → "Solusi terbaik sering bukan yang pertama terpikirkan"

Tahap 4: PILIH SOLUSI TERBAIK
  → Evaluasi setiap alternatif: risiko, biaya, efektivitas, reversibilitas
  → Pilih yang solve root cause, bukan hanya symptom

Tahap 5: IMPLEMENTASI
  → Jalankan dengan plan yang jelas
  → Siapa? Kapan? Bagaimana? Apa resource yang dibutuhkan?

Tahap 6: EVALUASI
  → Apakah masalah teratasi?
  → Apakah ada efek samping baru?
  → Apa yang bisa dipelajari untuk ke depan?
```

---

## Hubungan dengan Relativitas Sebab-Akibat

Setiap tahap di atas adalah **operasi pada rantai kausalitas**:

```
Tahap 1 (Identifikasi)  → Temukan AKIBAT yang tidak diinginkan
Tahap 2 (Analisis)      → Trace balik ke SEBAB-nya
Tahap 3 (Alternatif)    → Temukan SEBAB alternatif yang menghasilkan akibat lebih baik
Tahap 4 (Pilih)         → Pilih SEBAB yang paling efisien menuju akibat yang diinginkan
Tahap 5 (Implementasi)  → INTERVENSI pada titik sebab
Tahap 6 (Evaluasi)      → Cek apakah rantai kausalitas berubah sesuai harapan
```

**Insight**: Problem solving bukan tentang "fix masalah". 
Problem solving adalah **merekayasa ulang rantai sebab-akibat**.

---

## Teknik-Teknik Problem Solving + Relasi ke Kausalitas

### 1. The 5 Whys — Drill Down ke Root Cause
```
Cara kerja:
  Tanya "Kenapa?" sampai 5 kali untuk menemukan sebab paling dalam.

Contoh:
  Masalah: Website SIDIX lambat
  Why 1: Server response time > 3s
  Why 2: Database query tidak di-index
  Why 3: Tabel users tidak punya index di kolom user_id
  Why 4: Waktu buat tabel tidak ada index
  Why 5: Tim tidak punya konvensi "selalu index FK"

  Root cause: PROSES, bukan teknisnya
  Fix root cause: Buat checklist schema review
  Bukan hanya: tambah index (fix symptom)
```

**Relasi ke kausalitas**: 5 Whys adalah teknik menelusuri rantai sebab secara mundur
sampai ketemu sebab yang bisa diintervensi.

### 2. Brainstorming — Perluas Ruang Solusi
```
Cara kerja:
  Generate sebanyak mungkin alternatif tanpa judgment.
  Diversitas = lebih banyak "sebab potensial" untuk akibat yang diinginkan.

Aturan:
  → Jangan kritik ide saat brainstorming (bunuh kreativitas)
  → Kuantitas dulu, kualitas kemudian
  → Ide gila kadang mengarah ke solusi jenius
```

**Relasi ke kausalitas**: Brainstorming adalah eksplorasi **ruang kemungkinan sebab**
sebelum memilih satu intervensi.

### 3. Analisis SWOT — Peta Sebab Eksternal & Internal
```
S (Strengths)  = sebab internal yang menguntungkan
W (Weaknesses) = sebab internal yang merugikan
O (Opportunities) = kondisi eksternal yang bisa jadi peluang
T (Threats)    = kondisi eksternal yang bisa jadi risiko

Formula Fahmi dalam SWOT:
  S + O = Perluas peluang (gunakan kekuatan untuk ambil kesempatan)
  S + T = Mitigasi risiko (gunakan kekuatan untuk lawan ancaman)
  W + O = Perbaiki diri (kurangi kelemahan untuk manfaatkan peluang)
  W + T = Survivabilitas minimum (hindari situasi ini)
```

**Relasi ke kausalitas**: SWOT adalah **pemetaan kondisi sebab** sebelum merencanakan
intervensi. Setiap kuadran adalah jenis "sebab" yang berbeda.

### 4. FMEA — Failure Mode and Effects Analysis
```
Cara kerja:
  Analisis kegagalan SEBELUM terjadi.
  Untuk setiap komponen: apa yang bisa gagal? bagaimana efeknya?

Langkah:
  1. List semua mode kegagalan potensial
  2. Nilai: Severity × Occurrence × Detectability = Risk Priority Number (RPN)
  3. Fix yang RPN tertinggi dulu

Ini adalah MITIGASI RISIKO paling proaktif:
  Bukan nunggu rusak baru fix. Tapi predict kerusakan sebelum terjadi.
```

**Relasi ke kausalitas**: FMEA adalah **peta sebab-akibat masa depan**.
Kamu predict: "kalau sebab X terjadi, akibatnya adalah Y, dengan dampak Z."

---

## Framework Terpadu: Sebab-Akibat sebagai Kompas

```
┌─────────────────────────────────────────────────────┐
│              RANTAI KAUSALITAS                       │
│                                                      │
│  [Kondisi Awal] → [Sebab] → [Akibat] → [Konteks]   │
│                                                      │
│  Intervensi bisa di:                                 │
│  1. Ubah Kondisi Awal (preventif, jangka panjang)   │
│  2. Ubah/Block Sebab (proaktif)                     │
│  3. Kurangi dampak Akibat (reaktif, mitigasi)       │
│  4. Ubah Konteks (reframing)                        │
└─────────────────────────────────────────────────────┘
```

### Contoh Nyata dari Proyek SIDIX

**Masalah**: User kabur saat quota habis

```
Kondisi awal: User bergantung pada quota
Sebab: Quota sistem terbatas, tidak ada alternatif saat habis
Akibat: User frustrated, uninstall/stop pakai

Intervensi yang dipilih:
  Level 2 (ubah sebab): tambah Groq+Gemini gratis → quota lebih besar
  Level 3 (mitigasi akibat): Waiting Room → user tetap engaged
  Level 1 (ubah kondisi awal): LoRA lokal → tidak bergantung cloud sama sekali

Peluang yang diperluas:
  Waiting Room quiz → training data SIDIX
  User yang sabar menunggu → lebih engaged, lebih loyal
```

**Satu masalah, 3 titik intervensi, 2 peluang yang muncul dari masalah itu sendiri.**

---

## Relativitas dalam Konteks Pemikiran Islam

Konsep sebab-akibat dalam Islam bukan deterministik buta:

```
Tabayyun (تبيُّن) = verifikasi sebab sebelum bereaksi pada akibat
  → Jangan langsung bereaksi. Cek dulu: benarkah sebab yang kita kira?

Tawakkul + Ikhtiar = usaha pada titik sebab, serahkan hasil (akibat) pada Allah
  → Manusia punya kontrol pada sebab. Akibat adalah domain Allah.
  → Ini bukan pasif — ini alokasi kontrol yang tepat.

Qada' dan Qadar = akibat adalah ketetapan, tapi sebab adalah pilihan
  → Berfikir kausalitas = menggunakan amanah akal untuk memilih sebab terbaik
```

**Untuk SIDIX**: Epistemologi Islam mengajarkan bahwa memahami sebab-akibat adalah
bagian dari tanggung jawab akal (Nazhar). Seseorang yang tidak mau menganalisis sebab
adalah seseorang yang tidak menggunakan akalnya dengan baik.

---

## Matriks Keputusan: Sebab mana yang perlu diintervensi?

```
Kriteria evaluasi:
  Controllability : Seberapa bisa kita kontrol sebab ini? (1-5)
  Impact          : Seberapa besar dampak intervensi? (1-5)
  Speed           : Seberapa cepat perubahan terasa? (1-5)
  Reversibility   : Seberapa mudah di-undo kalau salah? (1-5)

Pilih yang skor tertinggi dulu.
Hindari intervensi yang: low controllability + high irreversibility.
```

---

## Pola Berfikir "Sebab-Akibat" untuk SIDIX

Ketika SIDIX menerima pertanyaan atau masalah, gunakan lens ini:

```
Step 1: "Apa yang terjadi?" (akibat yang terobservasi)
Step 2: "Mengapa itu terjadi?" (sebab langsung)
Step 3: "Mengapa sebab itu ada?" (sebab lebih dalam — 5 Whys)
Step 4: "Apa yang bisa diintervensi?" (titik kontrol)
Step 5: "Apa akibat dari intervensi itu?" (prediksi kausalitas baru)
Step 6: "Apakah ada peluang tersembunyi dalam masalah ini?"

Terakhir: apakah jawaban ini [FAKTA], [OPINI], atau [TIDAK TAHU]?
```

---

## Insight Terpenting untuk SIDIX

> Setiap masalah adalah PELUANG yang belum dibalik.
> Setiap risiko adalah INFORMASI tentang rantai kausalitas yang belum dipahami.
>
> Orang yang takut pada masalah: melihat akibat buruk, tidak tahu sebabnya.
> Orang yang menguasai kausalitas: melihat akibat buruk, trace sebabnya,
> intervensi di titik yang tepat, dan sering menemukan peluang di prosesnya.

Formula Fahmi yang benar:
```
Sebab + Akibat
  → Pahami hubungannya
  → Identifikasi titik kontrol
  → Intervensi tepat
  = Mitigasi risiko (cegah akibat buruk)
  = Perluas peluang (perkuat akibat baik)
```

**Ini bukan rumus matematika — ini cara pandang dunia (worldview).**
Orang yang berpikir dengan lens kausalitas tidak pernah benar-benar terjebak,
karena mereka selalu bisa trace: "ini disebabkan apa, dan apa yang bisa saya ubah?"

---

## Hubungan dengan Research Notes Lain

- **Note 111** (Problem Solver Framework): kerangka umum problem solving
- **Note 126** (Problem Solving & Planning): OODA loop, 5 Whys, decision matrix
- **Note 016** (Decision Engine Maqasid): kausalitas dalam perspektif maqasid syariah
- **Note 128** (Identity Shield): sebab (probe) → akibat (identitas bocor) → mitigasi (interceptor)
- **Note 122** (Token Quota): sebab (traffic) → akibat (overload) → mitigasi (quota system)

Semua implementasi dalam proyek SIDIX adalah **aplikasi kausalitas dalam engineering**.
