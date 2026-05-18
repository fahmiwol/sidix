# Human Experience Engine — fondasi riset untuk SIDIX / Mighan

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## 1. Motivasi: paradoks dan domain “tidak hitam-putih”

Syair, karya seni, puisi, dan **studi kasus pengalaman hidup** sering berupa **kombinasi kompleks dari paradoks**: benar di satu sisi, ambigu di sisi lain; inspiratif sekaligus subjektif.  
Untuk AI yang mengaku **islamic + manusiawi**, domain ini **wajib** masuk — tetapi **tidak** boleh disamakan dengan klaim hukum/ilmiah bertekstual tanpa konteks.

Dokumen ini merangkum arah **“pengalaman sebagai data”** yang bisa dipakai **sistematis**, selaras `28_sidix_epistemic_modes_multi_perspective.md` (mode jawaban) dan `10_sanad_as_citations_system.md` (jenis kalimat).

---

## 2. Taksonomi konten pengalaman (untuk kurasi & tagging)

Bukan daftar tertutup; dipakai untuk **label**, filter retrieval, dan etika sumber.

| Kelompok | Contoh isi | Catatan epistemik |
|----------|------------|-------------------|
| **Hidup nyata (real story)** | Sukses/gagal, bangkit dari nol, inspirasi bisnis/karier/keluarga | Noise tinggi; sering dipotong; tetap bernilai sebagai **pola** |
| **Unik / ekstrem / absurd** | Kejadian langka, “hampir mati”, narasi yang sulit diverifikasi | Wajib **rendah keyakinan** pada detail; pola psikologis bisa tetap relevan |
| **Cinta & relasi** | Putus, LDR, toxic pattern, timing nikah | Sensitif; hindari menghakimi; fokus **refleksi & batas sehat** bila sesuai nilai |
| **Kerja & bisnis** | Bangun dari nol, resign, bangkrut | Cocok untuk **CSDOR** + prinsip ekonomi syariah (bila diminta) |
| **Sehari-hari (relatable)** | Keluarga, pertemanan, tekanan hidup | Kuat untuk empati & framing; tetap bedakan **anekdot** vs **aturan** |

**Yang sering “ngangkat” secara naratif (bukan kebenaran mutlak):** gagal → bangkit; pahit → pelajaran; ekstrem → rasa ingin tahu. Ini **heuristik konten**, bukan hukum alam.

---

## 3. Realita: pengalaman = noisy data (dan itu fitur)

| Masalah | Implikasi untuk sistem |
|---------|-------------------------|
| Subjektif (emosi, memori selektif) | Jangan menyimpan sebagai **fakta objektif** tanpa label |
| Bias (self-justification, hiperbola) | **confidence** rendah default; cross-check pola |
| Tidak lengkap (cerita dipotong) | Field `completeness` / `source_reliability` di metadata |
| Kontradiksi antar orang | **Multi-perspektif** atau **synthesis** dengan “biasanya / sering / pada konteks X” |

**Insight produk:** AI yang hanya jurnal ilmiah cenderung “kaku”; AI yang **memahami pola pengalaman manusia** bisa lebih **bijak dalam arti pastoral / nasihat umum** — asal **tidak** menyamar sebagai fatwa atau diagnosis klinis dari cerita anonim.

---

## 4. Struktur minimum: CSDOR (+ meta)

Untuk mengubah narasi mentah menjadi **data yang bisa diindeks & divalidasi lewat pola**, gunakan kerangka:

| Field | Isi |
|-------|-----|
| **Context** | Siapa (anonim/role), kondisi, batas usia/lokasi bila relevan |
| **Situation** | Apa yang terjadi (fakta sejauh cerita mengizinkan) |
| **Decision** | Keputusan atau respons yang diambil |
| **Outcome** | Hasil jangka pendek/panjang (sukses/gagal/mixed) |
| **Reflection** | Pelajaran yang diambil subjek (bukan klaim universal) |

**Reflection** harus bisa ditandai sebagai **interpretasi narasumber**, bukan **hukum**.

---

## 5. Validasi tanpa jurnal formal (empat lapisan)

Ketika **tidak ada sumber akademik**, validitas bersifat **lemah tetapi berguna** bila transparan:

1. **Pattern validation** — apakah pola serupa muncul di banyak kasus / domain? → indikasi *truth pattern* lemah, bukti kuat.
2. **Cross-domain validation** — apakah prinsip yang sama muncul (mis. tunda gratifikasi) di psikologi, bisnis, dan tuntunan etika? → mendukung **abstraksi** tanpa mengklaim teks tunggal.
3. **Consequence validation** — bila prinsip diterapkan, apakah konsekuensinya konsisten dalam simulasi / reasoning? → cocok untuk **rule + LLM**.
4. **Time validation** — apakah tetap relevan lintas waktu? → prinsip “timeless” vs mode yang cepat usang (teknologi, platform).

Lapisan ini **tidak** menggantikan sanad untuk klaim **wajib berteks**; melengkapi **mode pengalaman & hikmah**.

---

## 6. Skema JSON (minimal — bisa diekspansi ke ontology)

```json
{
  "id": "exp_000001",
  "version": 1,
  "context": {
    "role": "entrepreneur",
    "age_band": "30-35",
    "locale": "ID"
  },
  "situation": "ekspansi terlalu cepat, cashflow kering",
  "decision": "tutup cabang, fokus satu unit",
  "outcome": "stabilisasi, pertumbuhan lambat",
  "reflection": "skala setelah sistem kuat",
  "tags": ["bisnis", "failure", "cashflow", "scale"],
  "value_flags": ["risk_overspending"],
  "confidence": 0.65,
  "source_type": "synthetic|interview|forum|biography|religious_narrative",
  "epistemic_note": "anecdote — not legal or medical advice"
}
```

**Sumber kaya tapi berisiko etika:** forum, komentar publik, podcast — wajib **konsen, anonimisasi, dan kebijakan penggunaan** sebelum masuk korpus produk.

---

## 7. Arsitektur besar (selaras stack Mighan)

Konsep lapisan (bukan commit implementasi tunggal):

| Lapisan | Fungsi | Catatan repo |
|---------|--------|----------------|
| **LLM / bahasa** | Merumuskan, merangkai, merespons gaya | `brain_qa`, adapter SIDIX, dll. |
| **Experience Engine** | Penyimpanan + retrieval **kasus terstruktur** (CSDOR) | Bisa mulai dari koleksi Markdown + metadata JSON; nanti vector DB |
| **Value system** | Filter nilai: halal/haram (domain yang memang relevan), etika, niat, maqasid | `brain/public/principles/`, khususnya `06_ihos_islamic_human_operating_system.md` |
| **Reasoning engine** | Rule + pola + analogi terbatas; bukan hanya probabilitas kata | Decision engine (lihat `16_decision_engine_maqasid_ushul_xai_v0.md` bila relevan) |
| **Output** | Sintesis: nasihat umum, narasi, skenario — dengan **label mode** | Selaras mode di `28_...` |

**Pertanyaan panduan output (bukan slogan marketing):**

- AI umum: “Apa yang sering dianggap benar secara statistik?”  
- AI berbasis pengalaman: “**Apa yang biasanya terjadi pada manusia dalam konteks serupa?**” (dengan caveat)  
- AI berbasis nilai Islam: “Apa yang **benar menurut wahyu/kaidah** + apa yang **baik/maslahah** dalam konteks ini?” — **hanya** untuk domain yang memang dilayani dengan rujukan yang jelas.

---

## 8. Alur jawaban (contoh: user takut ekspansi bisnis)

1. Klasifikasi intent + **mode epistemik** (pengalaman vs fatwa vs faktual).  
2. Retrieve kasus relevan dari Experience Engine (gagal ekspansi vs sukses bertahap).  
3. Bandingkan pola + **value layer** (spekulasi berlebihan, utang, zalim, dll.).  
4. Generate **sintesis** — bukan opini tunggal tanpa struktur: pola + caveat + opsi aman.  
5. Tampilkan **sumber**: potongan korpus / “pola dari N kasus anonim” / “bukan nasihat investasi resmi” sesuai kebutuhan.

---

## 9. Teknik yang selaras codebase sekarang

- **RAG** pada dokumen terkurasi — `05_retrieval_playbook.md`, `03_rag_chunking_markdown_aware.md`.  
- **Embedding + indeks** untuk pengalaman terstruktur (chunk = satu kasus atau satu paragraf refleksi).  
- **Prompt layering:** `[VALUE / PRINSIP]` + `[KASUS TERAMBIL]` + `[PERTANYAAN]` + instruksi **jangan klaim kepastian** di luar data.

---

## 10. Validasi produk & garis merah

- Uji skenario (ratusan) membandingkan: jawaban generik vs jawaban **berpola pengalaman + nilai**.  
- Metrik: relevansi, konsistensi nilai, **tidak** memberi diagnosis medis / putusan hukum dari anekdot.  
- **Privasi:** cerita pribadi tidak boleh bocor lintas user; dataset publik harus bersih PII.

---

## 11. Status

- **Fondasi konsep & riset** — siap dipecah jadi task: schema v1, koleksi pilot 100–500 entri sintetis/terkurasi, pipeline ingest.  
- **Lihat juga:** `28_sidix_epistemic_modes_multi_perspective.md`, `10_sanad_as_citations_system.md`, `06_ihos_islamic_human_operating_system.md`.
- **Blueprint stack nyata (Python / brain_qa, bukan Node+OpenAI default):** `30_blueprint_experience_stack_mighan.md`.
