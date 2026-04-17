# 117 — Community Contribution Guide: Cara Mengajar SIDIX

## Apa ini / What is it

Panduan lengkap cara komunitas berkontribusi ke SIDIX — baik sebagai kontributor teknis maupun non-teknis. Setiap kontribusi adalah "mengajar SIDIX", dan ilmu yang diajarkan akan terus mengalir manfaatnya selama SIDIX berjalan.

Ini bukan sekadar "open source contribution guide" biasa. Ini adalah sistem di mana **kontribusi intelektual** ditransformasi menjadi **kemampuan AI yang nyata** — dan proses transformasinya transparan, terverifikasi, dan berkelanjutan.

---

## Mengapa penting / Why it matters

- **Amal jariyah ilmu** — dalam Islam, ilmu yang bermanfaat adalah salah satu dari tiga amal yang pahalanya terus mengalir setelah seseorang wafat. Berkontribusi ke SIDIX = ilmu terus mengalir dan bermanfaat ke pengguna di seluruh dunia.
- **AI yang dipahami** — berbeda dengan black-box AI vendor, SIDIX adalah AI yang bisa dilihat proses belajarnya. Kontributor bisa melihat bagaimana input mereka mengubah kemampuan SIDIX.
- **Network effect** — semakin banyak kontributor, semakin pintar SIDIX, semakin banyak yang tertarik berkontribusi.

---

## Bagaimana cara kerja / How it works

### 5 Jalur Kontribusi:

---

### 1. Submit Research Note

**Format** (lihat template di `brain/public/research_notes/`):
```markdown
# [Nomor]_[topik]

## Apa ini / What is it
## Mengapa penting / Why it matters
## Bagaimana cara kerja / How it works
## Contoh nyata / Real examples
## Keterbatasan / Limitations
## Referensi / References
```

**Yang SIDIX lakukan dengan research note:**
```
Research note (.md)
      │
      ▼
Corpus Indexer → masuk ke BM25 index → bisa di-retrieve saat user tanya
      │
      ▼
Conceptual Generalizer → ekstrak prinsip → tambah ke skill pool
      │
      ▼
SPIN Self-Play → generate training pairs → filter kualitas
      │
      ▼
LoRA Fine-Tuning (next batch) → internalisasi ke weights
      │
      ▼
SIDIX sekarang lebih pintar tentang topik ini
```

**Topik yang diprioritaskan:**
- Islamic epistemology, fiqh, ushul fiqh, tasawuf
- Sains dan teknologi dengan perspektif Islam
- Tutorial teknis dalam Bahasa Indonesia
- Problem-solving framework dan mental models
- Studi kasus lokal (Indonesia, ASEAN)

---

### 2. Tanya Jawab di Q&A

Setiap sesi Q&A dengan SIDIX menghasilkan data training:

```
User tanya: "Bagaimana Islam memandang AI?"
SIDIX jawab: [response]
User: [thumbs up/down] atau [tulis koreksi]
      │
      ▼
harvest.py mencatat:
  {
    "question": "...",
    "answer": "...",
    "feedback": "positive/negative",
    "correction": "seharusnya menyebut X, bukan Y"
  }
      │
      ▼
→ masuk ke BM25 RAG corpus (langsung, realtime)
→ masuk ke training queue (untuk fine-tuning berikutnya)
```

**Tips Q&A yang berkualitas:**
- Tanya pertanyaan spesifik, bukan terlalu umum
- Jika jawaban kurang tepat, tulis koreksi dengan referensi
- Follow-up question membuat pair lebih kaya

---

### 3. Solve Problems

Submit problem yang kamu hadapi + solusi yang kamu temukan:

```
Problem: "Bagaimana menghitung zakat saham?"
Solution: "Menurut Yusuf al-Qaradawi dalam Fiqh al-Zakat..."
Source: [referensi]
```

**Yang SIDIX lakukan:**

```
Problem-Solution pair
      │
      ▼
Experience Engine → simpan sebagai "experience"
      {
        "trigger": ["zakat saham", "saham", "zakat investasi"],
        "solution": "...",
        "confidence": 0.9,
        "source_type": "community"
      }
      │
      ▼
→ SIDIX bisa menjawab pertanyaan serupa di masa depan
→ Referensi ke kontributor dicatat (coming soon: attribution)
```

---

### 4. Submit Paper / Riset

Upload paper PDF atau paste teks riset:

```
Paper: "Maqasid al-Shariah and Fintech Regulation"
Format: PDF / teks panjang
```

**Yang SIDIX lakukan:**

```
Paper
  │
  ▼
Document Processor → pecah jadi chunk 512 token
  │
  ▼
Conceptual Generalizer → ekstrak:
  - Abstract principles (non-time-sensitive)
  - Concrete facts (time-sensitive, perlu verifikasi)
  - Methodological insights
  │
  ▼
Module Generator → konversi ke logic/skill module
  {
    "module": "maqasid_fintech",
    "principles": [...],
    "applicable_when": ["fintech", "regulasi", "keuangan Islam"]
  }
  │
  ▼
→ SIDIX bisa reasoning menggunakan framework paper ini
```

---

### 5. Test dan Beri Feedback

Ikut program SIDIX Beta Tester:
- Akses early feature sebelum rilis publik
- Test edge cases dan domain baru
- Laporkan hallucination atau jawaban yang salah

**Format laporan bug knowledge:**
```
Pertanyaan: [apa yang ditanya]
Jawaban SIDIX: [apa yang dijawab]
Yang seharusnya: [jawaban yang benar]
Sumber: [referensi]
Tingkat kesalahan: [minor/major/critical]
```

---

## Sistem Nilai Kontribusi

Setiap kontribusi mendapat skor berdasarkan:

| Faktor | Bobot | Penjelasan |
|---|---|---|
| **Uniqueness** | 40% | Seberapa baru informasi ini untuk SIDIX |
| **Verifiability** | 30% | Apakah ada referensi yang bisa diverifikasi |
| **Utilization** | 20% | Seberapa sering kontribusi ini di-retrieve saat inference |
| **Quality feedback** | 10% | Apakah user puas ketika SIDIX menggunakan kontribusi ini |

Skor ini dicatat di **Merkle Ledger** (lihat research note 115) — tidak bisa dimanipulasi retroaktif.

---

## Contoh nyata / Real examples

### Contoh 1: Peneliti Fiqh

Ahmad adalah mahasiswa S2 Ushul Fiqh. Dia:
1. Submit 10 research notes tentang metodologi qiyas
2. Jawab 50+ pertanyaan fiqh muamalat di Q&A
3. Upload skripsinya tentang "Maqasid al-Shariah dalam Ekonomi Digital"

Hasilnya: SIDIX sekarang bisa menjelaskan qiyas dengan kedalaman level akademik, dan mampu mengaplikasikan maqasid ke kasus fintech modern. 300+ user mendapat manfaat dari ilmu Ahmad.

### Contoh 2: Developer Indonesia

Budi adalah developer yang sering menghadapi problem teknis. Dia:
1. Submit Q&A tentang debugging Python (dengan koreksi jawaban SIDIX)
2. Tulis research note tentang "arsitektur microservice untuk startup Indonesia"
3. Laporkan 5 bug knowledge ketika SIDIX memberi jawaban teknis yang salah

Hasilnya: SIDIX jauh lebih akurat dalam konteks teknis Indonesia — memahami constraint infrastruktur lokal, harga VPS Indonesia, dll.

---

## Visi Jangka Panjang

```
Tahun 1: 100 kontributor → 1000 research notes → SIDIX setara junior researcher
Tahun 2: 1000 kontributor → 10K notes → SIDIX setara senior researcher
Tahun 3: 10K kontributor → 100K notes → SIDIX menjadi corpus terbesar 
         pengetahuan Islam + teknologi dalam Bahasa Indonesia
```

Ini bukan sekadar AI product. Ini adalah **proyek peradaban** — membangun infrastruktur pengetahuan yang tidak bergantung pada vendor asing, yang akarnya di epistemologi Islam, yang manfaatnya terus mengalir.

**"Khayr al-nas anfa'uhum li al-nas"** — sebaik-baik manusia adalah yang paling bermanfaat bagi manusia lain.

Setiap research note yang kamu tulis = satu amal yang terus mengalir.

---

## Keterbatasan / Limitations

1. **Verifikasi manual masih terbatas** — tidak semua kontribusi bisa diverifikasi secara otomatis. Tim kurasi kecil menjadi bottleneck di skala besar.

2. **Kualitas input bervariasi** — kontributor dengan latar belakang berbeda menghasilkan kualitas berbeda. Perlu sistem peer review.

3. **Bahasa** — saat ini SIDIX paling optimal dalam Bahasa Indonesia dan Arab. Kontribusi dalam bahasa lain memerlukan proses terjemahan ekstra.

4. **Attribution** — sistem credit kontributor masih dalam pengembangan. Saat ini kontribusi dicatat di Merkle Ledger tapi belum ada UI untuk melihat "ilmu yang telah diajarkan."

5. **GDPR / Privacy** — jika kontribusi mengandung data pribadi, perlu prosedur sanitasi sebelum masuk ke corpus.

---

## Cara Mulai / Getting Started

```bash
# 1. Clone atau fork repo SIDIX
git clone https://github.com/fahmiwol/sidix.git

# 2. Buat research note baru
# Cek nomor terakhir:
ls brain/public/research_notes/ | sort | tail -3

# 3. Buat file baru:
# brain/public/research_notes/[nomor+1]_[topik].md

# 4. Ikuti format wajib (lihat contoh di folder ini)

# 5. Submit PR atau kirim ke Fahmi di fahmiwol@gmail.com

# Atau lebih mudah:
# Akses app.sidixlab.com → Submit Research Note → isi form → submit
```

---

## Referensi / References

- `brain/public/research_notes/115_p2p_smart_ledger_hafidz.md` — sistem penyimpanan terdistribusi
- `brain/public/research_notes/116_sidix_self_learning_loop.md` — siklus belajar SIDIX
- `brain/public/research_notes/112_permanent_learning_sidix.md` — SPIN self-play
- `apps/brain_qa/harvest.py` — feedback harvesting code
- Hadith: "Idha mata al-insan inqata'a 'anhu 'amaluhu illa min thalath..." — HR Muslim
- `CLAUDE.md` — aturan kontribusi untuk Claude agent
