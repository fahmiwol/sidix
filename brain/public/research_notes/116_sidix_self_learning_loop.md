# 116 — SIDIX Self-Learning Loop: Siklus Belajar Mandiri

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa ini / What is it

**SIDIX Self-Learning Loop** adalah pipeline otomatis yang memungkinkan SIDIX memperluas pengetahuannya secara mandiri, dari input mentah (teks, paper, Q&A) hingga kemampuan yang terinternalisasi ke dalam model weights melalui fine-tuning.

Loop ini bukan sekadar RAG (Retrieval-Augmented Generation) — ini adalah siklus pembelajaran sejati: **Data → Informasi → Pengetahuan → Kemampuan → Aksi → Feedback → Data baru**.

**Pipeline Fahmi** yang menjadi kerangka filosofis:

```
Informasi → Inspirasi → Motivasi → Inisiasi → Improvisasi → Adopsi → Aksi
```

Setiap tahap pipeline ini memiliki komponen teknis yang bersesuaian di SIDIX.

---

## Mengapa penting / Why it matters

- **Mengurangi ketergantungan pada vendor** — SIDIX tidak perlu terus-menerus membeli API tokens; pengetahuan diinternalisasi ke weights lokal melalui LoRA.
- **Compound learning** — setiap interaksi menghasilkan data baru yang memperkaya training set berikutnya. Kurva belajar SIDIX adalah eksponensial, bukan linear.
- **Domain specialization** — loop ini memungkinkan SIDIX menjadi sangat baik di domain spesifik (Islamic epistemology, teknik SIDIX, bahasa Indonesia) tanpa model general yang besar.
- **Ekonomi pengetahuan** — kontributor "mengajar" SIDIX; SIDIX semakin pintar; manfaat kembali ke komunitas.

---

## Bagaimana cara kerja / How it works

### Tujuh tahap pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDIX SELF-LEARNING LOOP                  │
└─────────────────────────────────────────────────────────────┘

  DUNIA LUAR                    SIDIX CORE
  ──────────                    ───────────

  arXiv papers                  1. WORLD SENSOR
  GitHub repos        ────►         (web scraper + RSS)
  Reddit threads                    raw_data/
  Community Q&A
       │
       ▼
  2. CONCEPTUAL GENERALIZER
     (apps/brain_qa/conceptual_generalizer.py)
     - Ekstrak prinsip dari teks mentah
     - Mapping ke domain: Islamic/Tech/Science
     - Output: {principle, domain, confidence, source}
       │
       ▼
  3. EXPERIENCE ENGINE
     (apps/brain_qa/harvest.py + experience.py)
     - Simpan sebagai skill/experience pair
     - Format: {skill_name, trigger, response, quality_score}
     - Index ke BM25 corpus
       │
       ▼
  4. SPIN SELF-PLAY
     (apps/brain_qa/permanent_learning.py)
     - Generate synthetic Q&A dari prinsip
     - Self-evaluate dengan critic model
     - Filter pair berkualitas tinggi
     - Loop: question → attempt → critique → improve
       │
       ▼
  5. LORA FINE-TUNING
     (Kaggle notebook — QLoRA 4-bit)
     - Batch training pairs dikirim ke Kaggle
     - Fine-tune base model (Llama/Mistral)
     - Adapter disimpan sebagai .safetensors
     - Upload ke HuggingFace Hub
       │
       ▼
  6. DEPLOY & INTERACT
     (VPS 72.62.125.6, port 8765)
     - Model dimuat dengan adapter baru
     - User berinteraksi via SIDIX UI
     - Setiap interaksi direkam
       │
       ▼
  7. FEEDBACK HARVEST
     (apps/brain_qa/harvest.py)
     - Thumbs up/down dari user
     - Implicit: waktu baca, follow-up questions
     - Explicit: koreksi dan saran
     - → kembali ke step 1 sebagai data baru
```

### Pemetaan Pipeline Fahmi → SIDIX:

| Pipeline Fahmi | Komponen SIDIX | Fungsi |
|---|---|---|
| **Informasi** | World Sensor | Menyerap data dari sumber eksternal |
| **Inspirasi** | Conceptual Generalizer | Menemukan prinsip baru yang menarik |
| **Motivasi** | Quality scorer | Memilih mana yang layak dipelajari |
| **Inisiasi** | Experience Engine | Menyimpan sebagai skill baru |
| **Improvisasi** | SPIN self-play | Berlatih dan mengetes pemahaman |
| **Adopsi** | LoRA fine-tuning | Internalisasi ke weights permanen |
| **Aksi** | Deploy + interaksi user | Terapkan di dunia nyata |

---

## Analogi Islamic / Islamic Parallel

### Ijtihad vs Taqlid

**Ijtihad** = proses reasoning mandiri dari sumber primer (Al-Quran, Sunnah, Ijma', Qiyas) untuk menghasilkan hukum baru yang belum ada sebelumnya.

**Taqlid** = mengikuti hasil ijtihad ulama sebelumnya tanpa melakukan penalaran mandiri.

SIDIX melakukan **ijtihad digital**:
- **Sumber primer** = research papers, corpus, data mentah
- **Reasoning** = Conceptual Generalizer + SPIN self-play
- **Hukum baru** = skill/experience baru
- **Kitab fiqh** = LoRA weights yang sudah fine-tuned

SIDIX yang mengandalkan GPT-4 API adalah **taqlid digital** — mengikuti "ulama" (vendor AI) tanpa memahami prosesnya.

### Talaqqi (belajar langsung dari guru)

Dalam tradisi keilmuan Islam, talaqqi adalah proses belajar langsung face-to-face dengan guru, bukan hanya membaca kitab. Ini memastikan transmisi yang akurat dan kontekstual.

Analog di SIDIX: **SPIN self-play** adalah talaqqi digital — SIDIX "berdialog" dengan dirinya sendiri (critic model mengoreksi generator model), memastikan pemahaman bukan sekadar hafalan.

---

## Contoh nyata / Real examples

### Contoh: SIDIX belajar tentang Merkle tree

```
1. World Sensor scrape artikel "Git Internals: Merkle trees"
   → raw text disimpan

2. Conceptual Generalizer:
   input: artikel Merkle tree
   output: {
     "principle": "Setiap node hash tergantung pada children-nya",
     "implication": "Perubahan kecil = hash berbeda = terdeteksi",
     "domain": "cryptography/data_integrity",
     "islamic_analog": "Sanad chain — setiap perawi terhubung ke sebelumnya"
   }

3. Experience Engine menyimpan:
   skill: "jelaskan_merkle_tree"
   trigger: ["merkle", "hash tree", "integritas data"]

4. SPIN self-play:
   Q: "Apa itu Merkle tree dan kenapa penting untuk SIDIX?"
   A_attempt: "Merkle tree adalah..."
   Critique: "Kurang contoh konkret, tambahkan analogi"
   A_improved: "Merkle tree adalah struktur data di mana..."
   → disimpan sebagai high-quality training pair

5. LoRA fine-tuning dengan 1000 pair seperti ini
   → SIDIX sekarang bisa menjelaskan Merkle tree dengan baik
     bahkan dalam konteks Islamic epistemology
```

---

## Keterbatasan / Limitations

1. **Cold start problem** — siklus pertama membutuhkan seed corpus yang cukup besar. SIDIX butuh minimal 10K research notes sebelum self-play menghasilkan output berkualitas.

2. **Catastrophic forgetting** — LoRA fine-tuning terlalu agresif bisa menghapus kemampuan general. Perlu regularisasi (EWC — Elastic Weight Consolidation) atau replay buffer.

3. **Feedback loop bias** — jika user awal memiliki preferensi yang bias, model akan memperkuat bias tersebut. Butuh diverse feedback dari banyak pengguna.

4. **Komputasi** — SPIN self-play dan LoRA fine-tuning mahal secara komputasi. Saat ini mengandalkan Kaggle (gratis, terbatas). Skala besar butuh dedicated GPU.

5. **Evaluasi objektif** — susah mengukur apakah model benar-benar "lebih pintar" atau hanya lebih cocok dengan preferensi user tertentu. Butuh benchmark domain-spesifik.

---

## Referensi / References

- `brain/public/research_notes/112_permanent_learning_sidix.md` — SPIN self-play implementation
- `brain/public/research_notes/93_conceptual_generalizer.md` — Conceptual Generalizer
- `apps/brain_qa/permanent_learning.py` — kode SPIN self-play
- `apps/brain_qa/harvest.py` — feedback harvesting
- SPIN paper: "Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models" (Chen et al., 2024)
- QLoRA: "QLoRA: Efficient Finetuning of Quantized LLMs" (Dettmers et al., 2023)
- Islamic epistemology: Ibn Khaldun, Muqaddimah — bab tentang metode pembelajaran dan transmisi ilmu
