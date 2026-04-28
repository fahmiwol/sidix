# 135. Paul-Elder Critical Thinking Framework — Disiplin Berpikir untuk SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: epistemologi / ai  
> **Sumber**: Paul, R. & Elder, L. (2010). *The Miniature Guide to Critical Thinking Concepts and Tools*. Foundation for Critical Thinking Press. Via University of Louisville Ideas To Action.  
> **Tanggal**: 2026-04-18

---

## Mengapa Framework Ini Diadopsi SIDIX

Critical thinking Paul-Elder adalah salah satu framework paling terstruktur
untuk menilai *kualitas* penalaran. Cocok dengan prinsip SIDIX: jawaban
bukan sekadar "benar" — tapi harus jernih, akurat, relevan, dalam, luas,
logis, signifikan, dan adil.

Framework ini akan kita pakai sebagai **quality gate** sebelum output
dikirim ke user, dan sebagai lensa ke-6 di multi-perspective engine.

## Struktur Tiga Komponen

```
┌─────────────────────────────────┐
│  INTELLECTUAL STANDARDS         │   <- diterapkan pada
│  (9 standar kualitas)           │
└──────────────┬──────────────────┘
               │ must be applied to
               ▼
┌─────────────────────────────────┐
│  ELEMENTS OF THOUGHT            │   <- 8 komponen penalaran
│  (8 "bagian" pikiran)           │
└──────────────┬──────────────────┘
               │ to deliver
               ▼
┌─────────────────────────────────┐
│  INTELLECTUAL TRAITS            │   <- 8 watak pemikir terlatih
│  (8 sifat watak)                │
└─────────────────────────────────┘
```

## 1. Elements of Thought (8 Bagian Penalaran)

Setiap penalaran *selalu* mengandung:

| # | Elemen | Pertanyaan Pemeriksaan |
|---|--------|------------------------|
| 1 | **Purpose** (tujuan) | Apa tujuan berpikirku? Apa yang ingin kucapai? |
| 2 | **Question at hand** | Pertanyaan inti apa yang sedang kucoba jawab? |
| 3 | **Assumptions** | Asumsi apa yang aku ambil tanpa sadar? |
| 4 | **Point of view** | Dari sudut pandang siapa aku melihat ini? |
| 5 | **Information / Data** | Data apa yang aku pakai? Cukup? Akurat? |
| 6 | **Concepts / Ideas** | Konsep kunci apa yang membentuk pikiranku? |
| 7 | **Inferences / Interpretations** | Kesimpulan apa yang kutarik dari data? |
| 8 | **Implications / Consequences** | Kalau ini benar, apa implikasinya? |

## 2. Universal Intellectual Standards (9 Standar Kualitas)

Setiap elemen di atas harus diuji dengan 9 standar:

| Standar | Pertanyaan Cek |
|---------|----------------|
| **Clarity** (kejernihan) | Bisa dielaborasi? Contohnya? Ilustrasinya? |
| **Accuracy** (akurasi) | Bagaimana cek kebenarannya? Bisa diverifikasi? |
| **Precision** (presisi) | Bisa lebih spesifik? Detail? Eksak? |
| **Relevance** (relevansi) | Ini berkaitan dengan pertanyaan? |
| **Depth** (kedalaman) | Kompleksitasnya apa? Kesulitan nyatanya? |
| **Breadth** (keluasan) | Perlu lihat dari sudut lain? POV lain? |
| **Logic** (logika) | Apakah semua koheren? Mengikuti bukti? |
| **Significance** (signifikansi) | Ini hal paling penting? Fakta paling krusial? |
| **Fairness** (keadilan) | Aku mempertimbangkan pikiran orang lain? Tidak mendistorsi konsep? |

## 3. Intellectual Traits (8 Watak Pemikir Terlatih)

Hasil dari penerapan standar secara konsisten membentuk watak:

1. **Intellectual Humility** — sadar batas pengetahuannya sendiri
2. **Intellectual Courage** — berani hadapi ide yang tidak nyaman
3. **Intellectual Empathy** — memahami sudut pandang orang lain secara akurat
4. **Intellectual Autonomy** — berpikir mandiri, tidak hanya konform
5. **Intellectual Integrity** — standar yang sama untuk diri dan orang lain
6. **Intellectual Perseverance** — tekun walau sulit
7. **Confidence in Reason** — percaya nalar bisa jadi panduan
8. **Fair-mindedness** — adil kepada semua POV, bukan hanya yang sefaham

## Karakteristik Pemikir Kritis yang Terlatih

Menurut Paul & Elder (2010), pemikir kritis yang terlatih mampu:

- Merumuskan pertanyaan vital dengan jelas dan presisi
- Mengumpulkan dan menilai informasi relevan dengan ide abstrak
- Sampai pada kesimpulan beralasan, diuji dengan kriteria relevan
- Berpikir terbuka dalam sistem pemikiran alternatif, mengenali asumsi
  dan konsekuensinya
- Berkomunikasi efektif dalam menyelesaikan masalah kompleks

## Implementasi untuk SIDIX

### A. Self-Check Gate (pre-output)

Sebelum jawaban dikirim ke user, SIDIX jalankan **self-check** minimal:

- [ ] Apakah **purpose** jawaban jelas?
- [ ] Apakah **question at hand** benar yang ditanya user?
- [ ] Apakah ada **assumption** yang tidak disebut?
- [ ] Jawaban **accurate** (bisa diverifikasi) dan **relevant**?
- [ ] Cukup **depth** (tidak dangkal) dan **breadth** (multi-POV)?
- [ ] Ada yang terlewat secara **significance** dan **fairness**?

Kalau 2+ check gagal → regenerasi dengan prompt penguat, atau akui
keterbatasan secara eksplisit.

### B. Lensa ke-6 di Multi-Perspective

Di atas 5 POV (kritis, kreatif, sistematis, visioner, realistis) yang sudah
ada di note 132, tambahkan lensa ke-6:

> **Disciplined Thinker** — menerapkan 9 standar Paul-Elder terhadap
> argumen yang sedang dibangun. Fokus: "apakah ini clear, accurate,
> precise, relevant, deep, broad, logical, significant, fair?"

### C. Uncertainty Output

Kalau SIDIX sadar ada standar yang tidak bisa dipenuhi (mis. **accuracy**
karena tidak punya data terkini), dia ungkap eksplisit dengan nada
*intellectual humility* — bukan menyembunyikan.

## Contoh Pemeriksaan

Pertanyaan user: *"Apakah X lebih baik dari Y?"*

- **Purpose**: bantu user ambil keputusan antara X dan Y
- **Question**: "lebih baik" dalam konteks apa? (perlu klarifikasi)
- **Assumptions**: X dan Y komparabel; user peduli kriteria tertentu
- **POV**: dari praktisi? akademis? pengguna akhir?
- **Data**: apa buktinya? sumbernya?
- **Concepts**: "lebih baik" = lebih cepat? lebih murah? lebih etis?
- **Inferences**: kesimpulan aku tarik berdasar kriteria mana
- **Implications**: kalau salah pilih, konsekuensinya apa

Jawaban yang baik menampilkan minimal 4-5 elemen ini secara eksplisit.

## Keterbatasan Framework

1. **Overhead**: menerapkan 9 standar × 8 elemen = 72 cek per jawaban —
   tidak feasible untuk semua interaksi. Prioritas: untuk jawaban
   panjang/berbobot, lewati untuk chit-chat.
2. **Subjektivitas "fairness"**: standar keadilan tetap butuh kalibrasi
   konteks budaya.
3. **Tidak menjamin kebenaran**: bagus proses ≠ bagus hasil. Framework ini
   meningkatkan *probabilitas* jawaban berkualitas, tidak menjamin.

## Sumber

- Paul, R. & Elder, L. (2010). *The Miniature Guide to Critical Thinking
  Concepts and Tools*. Dillon Beach: Foundation for Critical Thinking Press.
- University of Louisville Ideas to Action (i2a). "Paul-Elder Critical
  Thinking Framework." https://louisville.edu/ideastoaction/about/criticalthinking/framework
