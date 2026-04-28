# 76 — Konversi Semua Dokumen ke Kode: Modul Baru SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Tag:** IMPL, DECISION, DOC

---

## Apa

Sesi ini mengkonversi semua research notes, manifesto, dan referensi yang ada
menjadi modul Python aktif di `apps/brain_qa/brain_qa/`.

Prinsip utama: **"Jika kau pelajari dari filosofinya, kau dapat semuanya."**
Bukan sekadar menyimpan knowledge, tapi mengubahnya menjadi logika, identitas,
kemampuan, dan aksi nyata.

---

## Modul yang Dibangun

### 1. `experience_engine.py`
**Dari:** `29_human_experience_engine_sidix.md`

Framework CSDOR (Context-Situation-Decision-Outcome-Reflection):
- `ExperienceRecord` — schema terstruktur untuk pengalaman manusia
- `CSDORParser` — parse narasi bebas → CSDOR (heuristic, tanpa LLM)
- `ExperienceStore` — JSONL store dengan keyword search
- `ExperienceEngine` — search + synthesize pola pengalaman
- 4 lapisan validasi: pattern, cross-domain, consequence, time

**Fungsi kunci:**
```python
search_experiences(query) → str  # shorthand untuk agent_react
get_experience_engine().synthesize(query, top_k=3) → str
get_experience_engine().ingest_from_corpus_dirs() → int
```

### 2. `self_healing.py`
**Dari:** `70_self_healing_ai_system.md`

Error pattern knowledge base + diagnosis engine:
- 14 error patterns (RLS, port conflict, import error, OOM, dll.)
- `ErrorClassifier` — regex match + extract variabel dari error message
- `SelfHealingEngine` — diagnose + fix suggestion + confidence scoring
- Auto-log semua diagnosis ke `.data/self_healing/healing_log.jsonl`

**Contoh:**
```python
diagnose_error("violates row-level security policy for table 'feedback'")
# → {category: "permission", confidence: 0.90, fix: "CREATE POLICY..."}
```

### 3. `world_sensor.py`
**Dari:** `42_sidix_growth_manifesto_dikw_architecture.md`

"Mata dan telinga" SIDIX untuk mendeteksi tren dunia:
- `ArxivSensor` — fetch paper baru via RSS (cs.AI, cs.LG, cs.CL)
- `GitHubSensor` — fetch trending repos via GitHub Search API
- `MCPKnowledgeBridge` — **bridge D:\SIDIX\knowledge → corpus** ← PENTING
- `BenchmarkTracker` — track benchmark drift lokal
- `WorldSensorEngine` — orchestrator semua sensor

**Fungsi kunci:**
```python
run_sensors(sources=["mcp_bridge", "arxiv", "github"]) → dict
bridge_mcp_to_corpus()  # Export 47 knowledge items dari D:\SIDIX ke corpus
```

### 4. `skill_library.py`
**Dari:** `41_sidix_self_evolving_distributed_architecture.md` (Voyager-style)

Skill yang terus tumbuh dari setiap eksekusi berhasil:
- `SkillRecord` — code/reasoning/prompt skill dengan success tracking
- `SkillLibrary` — add + search + format_for_context
- 8 default skills: search_wikipedia, kaggle_path_autodetect, maqashid_evaluate, dll.

**Integrasi:**
```python
search_skills("debug kaggle notebook") → str  # untuk agent context
get_skill_library().add(name, description, content, ...)
```

### 5. `curriculum.py`
**Dari:** `27_continual_learning_sidix_architecture.md`

Urutan belajar L0→L4 (mudah→sulit):
- 20 curriculum tasks dari L0 (fakta) sampai L4 (wisdom)
- Prerequisite tracking — task yang lebih sulit baru bisa setelah yang mudah selesai
- Progress tracking per persona (MIGHAN/HAYFAR/TOARD/FACH/INAN)

**Contoh task:**
```
l0_ai_basics → l1_llm_concepts → l2_fine_tuning → l3_continual_learning → l4_self_improving_ai
```

### 6. `identity.py`
**Dari:** `43_sidix_prophetic_pedagogy_learning_architecture.md` + AGENTS.md

Identitas dan Constitutional Framework SIDIX:
- `SIDIX_IDENTITY` — misi, visi, 4 nilai inti (Sidq/Amanah/Tabligh/Fathanah)
- `CONSTITUTIONAL_RULES` — 12 prinsip (C01-C12)
- `PERSONA_MATRIX` — 5 persona dengan domain, tone, strengths, limitations
- `IdentityEngine` — generate system prompt, route persona, constitutional check

**Fungsi kunci:**
```python
get_sidix_system_prompt(persona="HAYFAR") → str  # untuk ollama_llm.py
route_persona(question) → "MIGHAN" | "HAYFAR" | "TOARD" | "FACH" | "INAN"
get_identity_engine().check_constitutional(text) → list violations
```

### 7. `social_agent.py`
**Dari:** Request user + Growth Manifesto (sensor architecture)

SIDIX di media sosial secara otonom:
- `ThreadsClient` — Threads API (Meta) posting + baca replies
- `RedditRSSClient` — Fetch top posts dari 7 subreddits (tanpa auth)
- `ContentQualityFilter` — filter spam + score kualitas konten
- `SocialAgentEngine` — orchestrator: post, belajar, ingest

**Kemampuan:**
```
SIDIX posting pertanyaan ke Threads
    ↓ Followers reply
    ↓ SIDIX collect replies → quality filter → ingest corpus
    ↓ Re-index BM25
    ↓ SIDIX lebih pintar dari feedback sosial

SIDIX scroll Reddit → extract knowledge → ingest → training pairs
```

**Setup Threads:**
```
THREADS_ACCESS_TOKEN=<dari Meta Developers>
THREADS_USER_ID=<user ID akun SIDIX>
```

---

## Endpoint Baru (agent_serve.py)

| Endpoint | Method | Fungsi |
|----------|--------|--------|
| `/sensor/stats` | GET | Status world sensor |
| `/sensor/run` | POST | Jalankan sensor cycle |
| `/sensor/bridge-mcp` | POST | Bridge D:\SIDIX → corpus |
| `/skills/stats` | GET | Statistik skill library |
| `/skills/search` | GET | Search skill (q=...) |
| `/skills/add` | POST | Tambah skill baru |
| `/skills/seed` | POST | Seed default skills |
| `/experience/stats` | GET | Statistik experience engine |
| `/experience/search` | GET | Search experiences |
| `/experience/synthesize` | POST | Synthesize pola |
| `/experience/ingest-corpus` | POST | Ingest corpus ke experience |
| `/healing/diagnose` | POST | Diagnosa error |
| `/healing/stats` | GET | Statistik diagnosis |
| `/healing/recent` | GET | N diagnosis terbaru |
| `/curriculum/progress` | GET | Progress learning |
| `/curriculum/next` | GET | Next tasks yang siap |
| `/identity/describe` | GET | SIDIX describe itself |
| `/identity/persona/:name` | GET | Detail persona |
| `/identity/route` | GET | Route pertanyaan ke persona |
| `/identity/constitutional-check` | POST | Check constitutional rules |
| `/social/stats` | GET | Status social agent |
| `/social/generate-post` | POST | Generate konten post |
| `/social/post-threads` | POST | Post ke Threads (dry_run default) |
| `/social/learn-reddit` | POST | Belajar dari Reddit |
| `/social/autonomous-cycle` | POST | Full autonomous learning cycle |

---

## D:\SIDIX\knowledge — Apa dan Bagaimana

**Status:** 47 knowledge items dari semua sesi sebelumnya
**Masalah:** Belum masuk ke BM25 corpus — hanya accessible via MCP

**Fix:** `MCPKnowledgeBridge.bridge()` mengexport semua item ke
`brain/public/sources/web_clips/mcp_*.md` → terindeks otomatis oleh indexer.

**Jalankan:**
```
POST http://localhost:8765/sensor/bridge-mcp
# atau:
POST http://localhost:8765/sensor/run
```

---

## Pipeline Otomatis yang Sekarang Tersedia

```
SIDIX baca artikel, post, DM, replies
    ↓
WorldSensor / SocialAgent / ArxivSensor
    ↓
ContentQualityFilter → threshold 0.4
    ↓
Ingest ke brain/public/sources/web_clips/*.md
    ↓
BM25 re-index (background)
    ↓
corpus_to_training.py → generate Q&A pairs
    ↓
Kaggle fine-tune (batch, tiap 4-8 minggu)
    ↓
LoRA adapter baru → Ollama model upgrade
    ↓
SIDIX lebih pintar
```

---

## Cara Menambah Ribuan Knowledge per Hari

| Sumber | Volume Estimasi | Status |
|--------|----------------|--------|
| arXiv RSS (3 kategori × 5) | ~15 paper/hari | ✅ Ready |
| GitHub trending | ~8 repo/hari | ✅ Ready |
| Reddit (7 subreddit × 5) | ~35 posts/hari | ✅ Ready |
| MCP Knowledge bridge | 47 items (one-time) | ✅ Ready |
| Threads replies | variabel | ⚙️ Butuh setup |
| Wikipedia initiative | 30+ artikel/run | ✅ Ready |
| User feeding (Fahmi) | variabel | ✅ Aktif |
| corpus_to_training pipeline | 5-10 pairs/doc | ✅ Ready |

**Total estimasi tanpa Threads:** ~88-100 items/hari
**Dengan Threads aktif:** +variabel dari community feedback

---

## Filosofi dari Fahmi yang Diimplementasikan

> "Jika kau pelajari dari caranya, yang kau dapat hanya teknis.
>  Tapi jika kau pelajari dari filosofinya, kau dapat semuanya."

Ini tercermin di:
- `identity.py`: SIDIX tahu MENGAPA ia ada, bukan hanya BAGAIMANA ia bekerja
- `constitutional_rules`: nilai yang tidak bisa dikompromikan
- `curriculum.py`: belajar dari L0 (fakta) sampai L4 (wisdom/judgment)
- `experience_engine.py`: belajar dari POLA pengalaman, bukan hanya data
- `self_healing.py`: mengenali kesalahan dan tumbuh darinya

---

## Pelajaran Penting

- D:\SIDIX\knowledge (MCP) dan brain/public/corpus (BM25) adalah dua memori terpisah — keduanya harus disinkronkan
- Social learning (Reddit, Threads) butuh quality filter ketat agar corpus tidak terkontaminasi konten rendah
- Constitutional framework adalah fitur, bukan overhead — SIDIX tumbuh dengan integritas
- Curriculum L0→L4 memastikan SIDIX menguasai fondasi sebelum ke hal kompleks
- Skill library adalah Voyager SIDIX — setiap task berhasil menjadi pengetahuan yang reusable

---

## Status

✅ 7 modul baru dibangun
✅ 24 endpoint baru di agent_serve.py
✅ Research note ini sebagai dokumentasi
⏳ Perlu: commit + push + deploy ke VPS
⏳ Perlu: setup THREADS_ACCESS_TOKEN untuk social posting
⏳ Perlu: jalankan /sensor/bridge-mcp untuk sync D:\SIDIX ke corpus
