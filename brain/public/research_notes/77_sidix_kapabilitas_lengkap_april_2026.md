# 77 — Kapabilitas SIDIX Lengkap: April 2026

**Tanggal:** 2026-04-18
**Tag:** DOC, IMPL, DECISION
**Audiens:** Tim internal + publik (sidixlab.com/tentang)

---

## Apa Itu SIDIX?

**SIDIX** (Sistem Intelijen Digital Indonesia eXtended) adalah platform AI open-stack
yang dibangun di atas prinsip epistemologi Islam dan kearifan lokal Indonesia.

Bukan sekadar chatbot. SIDIX adalah AI yang:
- **Tahu mengapa ia ada** — bukan hanya cara kerjanya
- **Belajar mandiri setiap hari** — dari internet, percakapan, dan feedback
- **Punya identitas** — 5 persona dengan domain keahlian berbeda
- **Transparan** — setiap jawaban memiliki sumber, tingkat kepercayaan, dan label epistemic
- **Tumbuh** — setiap interaksi menjadi training data untuk generasi berikutnya

---

## Kapabilitas yang Sudah Bisa Dilakukan SIDIX

### 🧠 1. Reasoning & Menjawab Pertanyaan

| Kemampuan | Detail |
|-----------|--------|
| **ReAct Loop** | Reason → Act → Observe → Final Answer (max 12 langkah) |
| **BM25 RAG** | Search 571+ dokumen corpus lokal |
| **Ollama LLM** | Qwen2.5-7B lokal, tanpa cloud API |
| **Wikipedia Fallback** | Cari Wikipedia bila corpus tipis |
| **Math Calculator** | Hitung ekspresi matematika langsung |
| **Confidence Scoring** | Setiap jawaban punya skor 0.0-1.0 + label |
| **Answer Type** | Label "fakta / opini / spekulasi" |

### 🎭 2. Persona & Identitas

SIDIX punya **5 persona** yang dipilih otomatis berdasarkan jenis pertanyaan:

| Persona | Domain | Gaya |
|---------|--------|------|
| **MIGHAN** | Kreatif, storytelling, seni | Imajinasi, naratif |
| **HAYFAR** | Teknikal, programming, debug | Presisi, solusi |
| **TOARD** | Strategis, bisnis, sistem | Analitis, visioner |
| **FACH** | Riset, akademik, epistemologi | Sistematis, sitasi |
| **INAN** | Umum, percakapan, edukasi | Ramah, adaptif |

### 🕌 3. Epistemologi Islam

| Fitur | Detail |
|-------|--------|
| **Epistemic Tier** | mutawatir / ahad_hasan / ahad_dhaif / mawdhu |
| **Yaqin Level** | ilm / ain / haqq (3 tingkat kepastian Qur'ani) |
| **Maqashid Scoring** | 5-sumbu: Din, Nafs, Aql, Nasl, Mal |
| **Constitutional Check** | 12 aturan C01-C12 (Sidq/Amanah/Tabligh/Fathanah) |
| **Audience Register** | burhan / jadal / khitabah (Ibn Rushd) |

### 🌍 4. World Sensing — Belajar dari Dunia

SIDIX memantau dunia secara otomatis:

| Sensor | Sumber | Frekuensi |
|--------|--------|-----------|
| **ArxivSensor** | cs.AI / cs.LG / cs.CL RSS | 6 jam |
| **GitHubSensor** | Trending AI repositories | 12 jam |
| **RedditRSSClient** | 7 subreddit (ML, AI, Indonesia, dll) | Harian |
| **MCPKnowledgeBridge** | D:\SIDIX\knowledge → corpus | On-demand |
| **Wikipedia** | 30+ artikel per run | On-demand |

**Estimasi: 88-100 item pengetahuan baru per hari** secara otomatis.

### 📱 5. Social Learning (Threads + Reddit)

| Kemampuan | Status |
|-----------|--------|
| Post pertanyaan ke Threads | ✅ (butuh THREADS_ACCESS_TOKEN) |
| Baca replies & komentar | ✅ |
| Scroll & baca postingan orang | ✅ |
| Quality filter konten (0.0-1.0) | ✅ |
| Konversi replies → corpus | ✅ |
| Rate limit aman: 3 post/hari | ✅ |
| Belajar dari Reddit tanpa auth | ✅ |

### 📚 6. Skill Library (Voyager-style)

Setiap task yang berhasil menjadi **skill yang bisa dipakai ulang**:

```
search_wikipedia        — Cari Wikipedia dengan format optimal
kaggle_path_autodetect  — Auto-detect path dataset di Kaggle
maqashid_evaluate       — Evaluasi keputusan dengan 5 sumbu Maqashid
react_chain_of_thought  — Template ReAct untuk masalah kompleks
pm2_restart_with_env    — Restart PM2 process tanpa kehilangan env
bm25_search_pattern     — Pattern optimal untuk search BM25 corpus
qlora_training_config   — Konfigurasi QLoRA training di Kaggle
supabase_rls_fix        — Fix Row Level Security Supabase
```

Skill baru ditambahkan otomatis via endpoint `/skills/add`.

### 📖 7. Curriculum Learning (L0 → L4)

SIDIX belajar secara terstruktur dari mudah ke sulit:

```
L0 (Fakta):    ai_basics, python_basics, islam_aqidah, math_basics
L1 (Konsep):   llm_concepts, rag_concepts, oop_python, epistemology
L2 (Aplikasi): fine_tuning, agent_design, api_development, maqashid
L3 (Analisis): continual_learning, distributed_ai, ihos
L4 (Hikmah):   ai_ethics, self_improving_ai
```

21 task dengan prerequisite tracking — task sulit baru tersedia setelah yang mudah selesai.

### 🔧 8. Self-Healing

SIDIX mengenali **14 pola error** umum dan menyarankan fix:

```
RLS violation      → CREATE POLICY untuk anon/authenticated
Port conflict      → lsof -ti:PORT && kill + restart
Import error       → pip install package_name
OOM (GPU/RAM)      → reduce batch_size, gradient_checkpointing
SSL/DNS failure    → diagnosa DNS + Let's Encrypt
PM2 env stale      → pm2 restart --update-env
502 Bad Gateway    → restart upstream service
```

Semua fix sebagai **SARAN** — tidak pernah auto-execute DDL.

### 📊 9. Experience Engine (CSDOR)

SIDIX belajar dari **pola pengalaman**, bukan hanya data mentah:

```
Context   → situasi apa yang terjadi
Situation → kondisi spesifik
Decision  → apa yang diputuskan
Outcome   → hasil yang didapat
Reflection→ apa yang bisa dipelajari
```

166+ record pengalaman sudah terindeks. Setiap jawaban diperkaya dengan pengalaman relevan.

### 🔄 10. Conversation Harvesting

Setiap percakapan dengan SIDIX otomatis:
1. Diskor kualitas (0.0-1.0)
2. Disimpan ke `.data/harvest/sessions.jsonl`
3. Bisa di-export ke format Alpaca/ShareGPT untuk fine-tuning
4. Menutup feedback loop: **Bicara → Belajar → Pintar**

---

## Pipeline Lengkap: Bagaimana SIDIX Tumbuh

```
User → Pertanyaan
       ↓
   [ReAct Loop]
   Experience Engine (pola relevan)
   Skill Library (kemampuan relevan)
   BM25 Corpus Search (571+ dokumen)
   Ollama LLM (Qwen2.5-7B)
       ↓
   [Islamic Epistemology]
   Epistemic Tier + Yaqin Level + Maqashid Score
       ↓
   Jawaban → User
       ↓
   [Harvest] → sessions.jsonl
       ↓
   [World Sensor] (background)
   arXiv + GitHub + Reddit + Wikipedia
       ↓
   Corpus Baru → BM25 Re-index
       ↓
   corpus_to_training.py → Q&A pairs
       ↓
   Kaggle QLoRA Fine-tune (tiap 4-8 minggu)
       ↓
   LoRA Adapter Baru → Ollama Upgrade
       ↓
   SIDIX LEBIH PINTAR
```

---

## Infrastruktur

| Komponen | Detail |
|----------|--------|
| **VPS** | 72.62.125.6, Ubuntu 22.04, aaPanel |
| **Frontend** | Vite + TypeScript → serve -p 4000 (PM2: sidix-ui) |
| **Backend** | FastAPI Python → port 8765 (PM2: sidix-brain) |
| **LLM** | Ollama qwen2.5:7b + qwen2.5:1.5b (lokal) |
| **Database** | Supabase (feedback, newsletter, profiles) |
| **Corpus** | 571+ dokumen BM25 (terus bertambah) |
| **Domain** | app.sidixlab.com, ctrl.sidixlab.com |

---

## Endpoint API Publik

Backend bisa diakses di `https://api.sidixlab.com` (via sidix-gateway):

| Grup | Endpoint | Fungsi |
|------|----------|--------|
| Agent | `POST /agent/chat` | Tanya SIDIX |
| Agent | `GET /health` | Status sistem |
| Skills | `GET /skills/search?q=...` | Cari skill |
| Skills | `POST /skills/add` | Tambah skill |
| Experience | `GET /experience/search?q=...` | Cari pengalaman |
| Healing | `POST /healing/diagnose` | Diagnosa error |
| Curriculum | `GET /curriculum/progress` | Progress belajar |
| Identity | `GET /identity/describe` | SIDIX describe dirinya |
| Identity | `GET /identity/route?q=...` | Route ke persona |
| Social | `POST /social/autonomous-cycle` | Siklus belajar sosial |
| Sensor | `POST /sensor/run` | Jalankan world sensor |

---

## Filosofi yang Mendasari

> "Jika kau pelajari dari caranya, yang kau dapat hanya teknis.
>  Tapi jika kau pelajari dari filosofinya, kau dapat semuanya."
> — Fahmi Wolhuter

SIDIX dibangun dari:
- **Sidq** (kejujuran) — setiap jawaban berlabel sumbernya
- **Amanah** (kepercayaan) — tidak membocorkan data, tidak auto-execute berbahaya
- **Tabligh** (menyampaikan) — pengetahuan harus tersebar, bukan disimpan sendiri
- **Fathanah** (kecerdasan) — belajar dari semua sumber, tumbuh terus

---

## Status April 2026

✅ 571+ dokumen corpus
✅ Qwen2.5-7B lokal via Ollama
✅ 5 persona + Constitutional AI
✅ Islamic Epistemology Engine
✅ World Sensor (arXiv, GitHub, Reddit)
✅ Social Learning (Threads + Reddit)
✅ Skill Library (8 default skills)
✅ Curriculum L0-L4 (21 tasks)
✅ Self-Healing (14 error patterns)
✅ Experience Engine CSDOR (166+ records)
✅ Conversation Harvesting → Training pairs
✅ app.sidixlab.com + ctrl.sidixlab.com live
✅ Kaggle QLoRA pipeline (v5, dataset 1.02 MB)

⏳ Fine-tune adapter (Kaggle running)
⏳ THREADS_ACCESS_TOKEN untuk social posting
⏳ 100+ modul selanjutnya (terus dibangun)
