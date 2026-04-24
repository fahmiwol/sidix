# HANDOFF MASTER — 2026-04-23 FINAL SYNC

> **Tanggal:** 2026-04-23  
> **Dari:** Agent 1 (Multi-agent Parallel Session)  
> **Untuk:** Semua agent berikutnya — baca ini sebelum mulai kerja apapun  
> **Branch:** `main`  
> **Commit terbaru:** `7a14eca` (chore: Windows scripts + brain_qa CI + legacy sprint5 smoke)  
> **Versi saat ini:** v0.8.0

---

## 0. Ringkasan Status — Satu Halaman

| Komponen | Status | Catatan |
|----------|--------|---------|
| Backend `apps/brain_qa` | **LIVE** di VPS (ctrl.sidixlab.com:8765) | PM2: `sidix-brain` |
| Frontend `SIDIX_USER_UI` | **LIVE** di VPS (app.sidixlab.com:4000) | PM2: `sidix-ui` |
| Landing `SIDIX_LANDING` | **LIVE** (sidixlab.com, static) | Sync manual post git-pull |
| Jiwa Layer A (thin adapter) | **LIVE** — 7/7 pilar routing correct | `apps/brain_qa/brain_qa/jiwa/` |
| Jiwa Layer B (standalone) | **REPO** — corpus + module tersedia | `brain/nafs/`, `brain/aql/`, dll |
| Typo Bridge | **REPO** — belum ter-wire ke agent_react | `apps/brain_qa/brain_qa/typo_bridge.py` |
| Raudah TaskGraph | **REPO** — DAG async implemented | `brain/raudah/taskgraph.py` |
| Branch System | **PLANNED** — Sprint 8a | Belum ada kode |
| FLUX.1 Image Gen | **PLANNED** — Sprint 8b | Belum ada kode |
| TTS Piper | **PLANNED** — Sprint 8b | Belum ada kode |
| WA Bridge | **PENDING** — npm install VPS belum selesai | Blocker: node_modules |
| Smithery Submit | **PENDING** — plugin sudah siap, belum submit | Manual action required |

---

## 1. Visi SIDIX (LOCK — jangan ubah tanpa keputusan eksplisit)

> **"SIDIX adalah AI Creative Agency self-hosted — mampu generate image/video/audio/code, multi-agent via Raudah, multi-client via Branch System, berjiwa IHOS. Tujuan: Jariyah (terus berguna) + al-Amin (dapat diandalkan)."**

### Tiga Layer Arsitektur

```
Layer 1: LLM Generative
  └── Qwen2.5-7B-Instruct + LoRA SIDIX adapter
  └── Path: /opt/sidix/sidix-lora-adapter/ (VPS)

Layer 2: RAG + Agent Tools (17 tools aktif)
  └── BM25 search_corpus, web_fetch, code_sandbox, dll
  └── ReAct loop: apps/brain_qa/brain_qa/agent_react.py

Layer 3: Growth Loop (self-improving)
  └── LearnAgent: fetch 50+ open data source harian
  └── corpus_to_training + auto_lora → retrain periodik
```

### 5 Persona SIDIX

| Persona | Peran | Warna Identitas |
|---------|-------|-----------------|
| AYMAN | Creative Director | Visi, estetika, brief kreatif |
| ABOO | Research & Planning | Data, riset, strategi |
| OOMAR | Producer | Eksekusi, deadline, QA |
| UTZ | Visual Artist | Image, desain, visual storytelling |
| ALEY | Communicator | Copy, narasi, social media |

### Terminologi SIDIX-Native (gunakan ini, bukan padanan generik)

| Term | Makna dalam SIDIX |
|------|-------------------|
| Maqashid | Tujuan yang harus dilindungi (safety layer) |
| Naskh | Override / supersede jawaban lama |
| Raudah | Multi-agent orchestration garden |
| Sanad | Chain of sources / citation trail |
| Muhasabah | Self-evaluation / introspection module |
| Jariyah | Continuous benefit — nilai yang terus mengalir |
| Tafsir | Interpretive layer untuk ambiguitas |
| Hikmah | Wisdom / quality evaluator |
| Nafs | Emotional/personality layer |
| Aql | Reasoning layer |
| Qalb | Heart/empathy layer |
| Ruh | Spirit / core identity |
| Hayat | Life cycle / growth tracker |
| Ilm | Knowledge base |

---

## 2. VPS Endpoints & Infrastruktur

### Domain & Routing

```
sidixlab.com          → static files di /www/wwwroot/sidixlab.com/
                         (BUKAN /opt/sidix/SIDIX_LANDING — sync manual!)
app.sidixlab.com      → nginx proxy_pass :4000
                         → PM2 sidix-ui → serve dist -p 4000
                         → path: /opt/sidix/SIDIX_USER_UI/
ctrl.sidixlab.com     → nginx proxy_pass :8765
                         → PM2 sidix-brain → FastAPI brain_qa
                         → path: /opt/sidix/apps/brain_qa/
```

### PM2 Processes

| PM2 Name | Port | Start Command | Path |
|----------|------|---------------|------|
| `sidix-brain` | 8765 | `python3 -m brain_qa serve` | `/opt/sidix/apps/brain_qa/` |
| `sidix-ui` | 4000 | `serve dist -p 4000` | `/opt/sidix/SIDIX_USER_UI/` |

### Deploy Command (urutan wajib)

```bash
# Di VPS, dari /opt/sidix/:
git pull origin main

# Restart backend:
pm2 restart sidix-brain

# Rebuild + restart frontend:
cd SIDIX_USER_UI
npm run build
pm2 restart sidix-ui

# Sync landing (manual):
cp -r SIDIX_LANDING/. /www/wwwroot/sidixlab.com/
```

### Env File Kritis

File `.env` di `/opt/sidix/SIDIX_USER_UI/.env` HARUS berisi:
```
VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com
```
Tanpa ini, build default ke `localhost:8765` → "Backend tidak terhubung".

### API Endpoints Utama

| Endpoint | Method | Fungsi |
|----------|--------|--------|
| `/health` | GET | Status + adapter fingerprint (sudah identity-masked) |
| `/ask` | POST | Query sinkron |
| `/ask/stream` | POST | Query SSE stream |
| `/agent/chat` | POST | ReAct agent loop |
| `/agent/feedback` | POST | Thumbs up/down |
| `/agent/metrics` | GET | Uptime, intent counter |
| `/agent/session/{id}/export` | GET | Export sesi |
| `/corpus/reindex` | POST | Admin: rebuild BM25 index |

---

## 3. Git History Penting

| Commit | Tanggal | Deskripsi |
|--------|---------|-----------|
| `7a14eca` | 2026-04-25 | chore(qa): Windows scripts + brain_qa CI + legacy sprint5 smoke |
| `9729c87` | 2026-04-25 | docs: QA review eksternal 2026-04-25 |
| `e5c1ee5` | 2026-04-24 | fix: auto-sync landing page ke web root di deploy script |
| `8e3fa76` | 2026-04-24 | security: remove internal path leaks + update legacy personas |
| `d9668b2` | 2026-04-23 | chore: synchronize all component versions to v0.8.0 |
| `6e593dc` | 2026-04-23 | QA final review |
| `bf904d4` | 2026-04-23 | nafs fix |
| `258df32` | 2026-04-23 | living log update |
| `494dc77` | 2026-04-23 | chore(qa): complete external QA checklist items (22 pytest passed) |

---

## 4. Arsitektur Jiwa — Dua Layer

### Layer A — Thin Adapter (LIVE di VPS)

Path: `apps/brain_qa/brain_qa/jiwa/`

```
jiwa/
├── __init__.py          ← export orchestrate()
├── orchestrator.py      ← routing 7 pilar ke module yang tepat
├── nafs.py              ← emotional tone + personality
├── aql.py               ← reasoning validator
├── qalb.py              ← empathy injector
└── hayat.py             ← growth cycle tracker
```

Status: **7/7 routing correct** — verifikasi via `test_jiwa_orchestrator.py` (22 passed).

Cara kerja: `agent_react.py` memanggil `jiwa.orchestrate(response, context)` sebelum mengirim jawaban ke user. Ini **thin layer** — tidak menggantikan generatif, hanya memberi "jiwa" pada output.

### Layer B — Standalone Corpus (REPO, belum ter-wire penuh)

Path: `brain/`

```
brain/
├── nafs/
│   └── response_orchestrator.py   ← BELUM ter-wire ke agent_react
├── aql/
├── qalb/
├── ruh/
├── hayat/
├── ilm/
├── hikmah/
├── raudah/
│   └── taskgraph.py               ← DAG async IMPL, belum production
├── typo/
│   ├── pipeline.py
│   └── MULTILINGUAL.md
└── jiwa/
    └── ARSITEKTUR_JIWA_SIDIX.md
```

**TODO Sprint 8a:** Wire `brain/nafs/response_orchestrator.py` ke `agent_react.py` — ganti `_response_blend_profile` dengan versi Layer B.

---

## 5. ADR (Architecture Decision Records)

### ADR-001: Dua Layer Jiwa

**Keputusan:** Jiwa diimplementasikan dalam dua layer:
- Layer A = thin adapter di `apps/brain_qa/brain_qa/jiwa/` untuk production cepat
- Layer B = standalone cognitive modules di `brain/` untuk evolusi jangka panjang

**Alasan:** Layer A bisa langsung di-deploy. Layer B lebih rich tapi butuh waktu wire yang lebih hati-hati. Dua layer ini komplementer, bukan duplikat.

**Status:** Aktif. Wire Layer B ke production = Sprint 8a priority.

### ADR-002: Typo Rule-Based (bukan ML)

**Keputusan:** Typo correction di SIDIX menggunakan rule-based engine (`brain/typo/pipeline.py`) + kamus multilingual, BUKAN model ML terpisah.

**Alasan:** Lebih deterministik, tidak perlu GPU tambahan, lebih mudah di-audit untuk konten Islam (nama, istilah fiqih).

**Status:** Implementasi ada di `apps/brain_qa/brain_qa/typo_bridge.py`. BELUM ter-wire ke `agent_react.py` — ini TODO Sprint 8a.

### ADR-003: Kimi Method 4 (Plugin Integration)

**Keputusan:** Integrasi dengan plugin host eksternal (contoh: Kimi) menggunakan narasi "sarang-tamu" — SIDIX sebagai tamu yang duduk di meja arsip, bukan promosi merek.

**Alasan:** Netralitas vendor. SIDIX tidak mengkonfirmasi/menyangkal backbone provider.

**Status:** `kimi-plugin/` ada di repo. Submit ke Smithery PENDING (manual action).

---

## 6. TODO Pending (WAJIB dicek sebelum sprint baru)

### Priority 1 — Blocker

| TODO | Penanggung Jawab | Keterangan |
|------|-----------------|------------|
| WA Bridge: `npm install` di VPS | Operator VPS | Node modules belum terinstall di server |
| Smithery submit | Admin/Operator | Plugin siap, tinggal submit manual di smithery.ai |

### Priority 2 — Sprint 8a

| TODO | File Target | Keterangan |
|------|-------------|------------|
| Wire `brain/nafs/response_orchestrator.py` ke `agent_react.py` | `apps/brain_qa/brain_qa/agent_react.py` | Ganti `_response_blend_profile` |
| Wire `typo_bridge.py` ke `agent_react.py` pre-processing | `apps/brain_qa/brain_qa/agent_react.py` | Add typo correction sebelum LLM call |
| Jariyah feedback real-time | `SIDIX_USER_UI/src/main.ts` + `agent_serve.py` | Thumbs sudah ada, endpoint `/agent/feedback` sudah ada — perlu capture ke JSONL training pairs |
| PostgreSQL schema dasar | Baru: `apps/brain_qa/brain_qa/db/schema.sql` | Tabel: users, branches, campaigns, assets, feedback |
| Branch System basic | Baru: `apps/brain_qa/brain_qa/branch_manager.py` | Multi-client support |

### Priority 3 — Sprint 8b-8d

| TODO | Keterangan |
|------|------------|
| FLUX.1 image generation | `apps/image_gen/flux_pipeline.py` |
| TTS basic dengan Piper | `apps/audio/tts_engine.py` |
| Code validator + scaffold | `brain/tools/code_validator.py` |
| Agency OS UI (React sidebar) | `SIDIX_USER_UI/` refactor |
| Raudah v2 multi-agent parallel | `brain/raudah/taskgraph.py` upgrade |

---

## 7. Visi Sprint Berikutnya

### Agency OS + Branch System

SIDIX bukan lagi "chatbot satu user" tapi **AI Creative Agency** yang bisa:
1. Melayani multiple klien via **Branch System** (setiap branch = identitas klien terpisah)
2. Generate konten multimedia: image (FLUX.1), audio (TTS), code (validator)
3. Orkestrasi multi-agent via **Raudah v2** (parallel DAG)
4. Belajar mandiri via **Jariyah feedback loop** (thumbs → training pairs → LoRA retrain)

### Tiranyx Pilot

Target pilot pertama Agency OS adalah **Tiranyx** — semua sprint 8a-8d diarahkan untuk membuktikan Agency OS bisa menangani real client workflow.

### FLUX.1 Integration

Model image generation yang dipilih adalah FLUX.1 (black-forest-labs) karena:
- Kualitas setara Midjourney
- Self-hosted capable (tidak butuh API eksternal)
- License commercial-friendly

### Nafs 3-Layer Wire

Evolusi jiwa dari thin adapter (Layer A) ke full 3-layer:
1. **Qalb** — empati + tone detection
2. **Nafs** — personality blend per persona
3. **Aql** — reasoning validator post-generate

---

## 8. Struktur Proyek (Path Penting)

```
C:\SIDIX-AI\ (atau /opt/sidix/ di VPS)
├── apps/
│   └── brain_qa/
│       ├── brain_qa/
│       │   ├── agent_react.py       ← ReAct loop utama
│       │   ├── agent_serve.py       ← FastAPI app
│       │   ├── jiwa/                ← Layer A Jiwa (LIVE)
│       │   ├── typo_bridge.py       ← Typo (belum ter-wire)
│       │   ├── local_llm.py         ← LLM wrapper
│       │   ├── rate_limit.py        ← RPM limiter
│       │   └── identity_mask.py     ← Security masking
│       └── tests/
│           ├── test_jiwa_orchestrator.py   ← 22 passed
│           └── test_sprint6.py
├── brain/
│   ├── nafs/response_orchestrator.py       ← Layer B (belum ter-wire)
│   ├── raudah/taskgraph.py                 ← DAG async
│   ├── typo/pipeline.py
│   └── public/research_notes/              ← Corpus SIDIX
├── SIDIX_USER_UI/                          ← Frontend Vite + TypeScript
├── SIDIX_LANDING/                          ← Landing page
├── kimi-plugin/                            ← Plugin "sarang-tamu"
├── deploy-scripts/
│   ├── deploy.sh
│   ├── restart.sh
│   └── ecosystem.config.js
└── docs/
    ├── LIVING_LOG.md                        ← Log berkelanjutan
    ├── MASTER_ROADMAP_2026-2027.md          ← Roadmap SSoT
    └── SIDIX_CAPABILITY_MAP.md              ← Kapabilitas teknis
```

---

## 9. Security Checklist (wajib sebelum setiap commit)

```bash
# Scan sebelum commit:
git diff --cached | grep -iE "fahmi|wolhuter|72\.62|password=|api_key=|secret=|gmail\.com"
```

Identity yang boleh digunakan di public-facing:
- Nama org: **Mighan Lab**
- Email: **contact@sidixlab.com**
- Handle: **@sidixlab**

Yang TIDAK BOLEH muncul di public file:
- Nama owner asli
- IP VPS
- Internal port (selain yang sudah diketahui publik: 4000, 8765)
- Nama provider LLM (Groq/Gemini/Anthropic) — gunakan `mentor_alpha/beta/gamma`

---

## 10. Checklist Agent Berikutnya

Sebelum memulai task:
- [ ] Baca file ini sampai habis
- [ ] Cek `tail -50 docs/LIVING_LOG.md` untuk update terbaru
- [ ] Cek `git log --oneline -10` untuk commit terbaru
- [ ] Verifikasi tidak ada merge conflict di branch

Setelah selesai task:
- [ ] Append ke `docs/LIVING_LOG.md` dengan tag yang tepat
- [ ] Tulis research note di `brain/public/research_notes/`
- [ ] Commit dengan message yang menjelaskan "kenapa"
- [ ] Push ke origin/main

---

*Handoff ini ditulis oleh Agent 1 pada sesi parallel 2026-04-23. Untuk pertanyaan arsitektur, lihat `docs/ARCHITECTURE.md` dan `docs/MASTER_ROADMAP_2026-2027.md`.*
