# SIDIX Checkpoint — 2026-04-24

> Dokumen internal sesi kerja. Dibaca oleh agent berikutnya atau owner bila perlu recovery.
> JANGAN tulis credential, path absolut server, atau username di sini.

---

## State Repo (2026-04-24 malam)

Branch aktif: `feat/sop-sync-sprint8` *(setelah rename dari branch agent lama)*
Commit terakhir: `e935b5a` (chore: checkpoint + gitignore)
Remote: `origin` — lihat `git remote -v` untuk URL aktual (jangan tulis di sini)
Tests: **22 passed** (baseline stabil)

### Commits sesi ini (urut terbaru)
| Hash | Deskripsi |
|---|---|
| `e935b5a` | chore: gitignore data/ + internal checkpoint |
| `a7a754c` | doc: research note 192 + living log sprint 8b |
| `cfcfaea` | feat(sprint-8b): Generative Core — 10 files, 986 insertions |
| `4cc6955` | feat(sprint-8a): Nafs Bridge + typo metadata + migration doc |
| `20fe170` | feat(sprint-8a): Standing Alone + Branch + Jariyah feedback |

---

## Apa yang Sudah Ada (Sprint 8a + 8b)

### Sprint 8a — Foundation Hardening ✅
- `multi_llm_router.py` → local-only (Ollama → LoRA → Mock), vendor API dihapus
- `multi_modal_router.py` → local-only interface
- `anthropic_llm.py` → **DIHAPUS** (tidak boleh ada di production)
- `nafs_bridge.py` → dynamic loader NafsOrchestrator (Layer B)
- `agent_react.py` → AgentSession + nafs_topic + nafs_layers_used
- `agent_serve.py` → `_ALLOWED_PERSONAS`, feedback→JSONL→Jariyah, ChatResponse +5 metadata fields
- `jiwa/aql.py` → `post_response()` terima `user_feedback`, thumbs_up = training pair
- `docs/schema/SIDIX_AGENCY_OS_CORE.sql` → PostgreSQL blueprint
- `docs/schema/MIGRATION_STRATEGY.md` → psql deployment guide
- `docs/sprints/2026-04-23_sprint-8a_implementation_checklist.md`

### Sprint 8b — Generative Core ✅
- `apps/image_gen/flux_pipeline.py` → FLUX.1-schnell (lazy load, mock SVG fallback)
- `apps/audio/tts_engine.py` → Piper TTS 4 bahasa (stub WAV fallback)
- `brain/tools/code_validator.py` → Python/JS/TS/SQL/HTML + security scan
- `brain/tools/scaffold_generator.py` → fastapi/react_ts/landing templates
- `agent_tools.py` → 36 tools (FLUX.1 replace SDXL, code_validate multi-lang, scaffold_project baru)
- `agent_serve.py` → `POST /generate/image`, `POST /tts/synthesize`

---

## Yang BELUM Dikerjakan (Sprint 8a sisa + Sprint 8c)

### Sprint 8a — masih kurang
- [ ] `apps/brain_qa/brain_qa/jariyah_collector.py` — modul Jariyah terpisah (saat ini inline)
- [ ] `apps/brain_qa/brain_qa/branch_manager.py` — BranchManager + AgencyBranch
- [ ] `apps/brain_qa/brain_qa/db/connection.py` — async PostgreSQL connection pool
- [ ] `apps/brain_qa/brain_qa/db/schema.sql` — schema per-app (saat ini di docs/schema/)

### Sprint 8c — belum mulai
- DB connection pool async
- Jariyah collector jadi modul mandiri
- Branch manager multi-tenant
- VPS: install Piper binary + download voice models (id+en)

---

## Konteks Teknis Penting

### Persona yang Valid (LOCK)
Hanya 5: `AYMAN`, `ABOO`, `OOMAR`, `ALEY`, `UTZ`
Guard di `agent_serve.py`: `_ALLOWED_PERSONAS`

### Vendor Naming Rules (SOP)
- Di inference pipeline: JANGAN sebut nama provider eksternal
- Alias: `mentor_alpha`, `mentor_beta`, `mentor_gamma`
- Di dokumen teknis internal: boleh sebut nama vendor
- Branch name: JANGAN pakai nama tool/agent eksternal sebagai prefix

### Layer Arsitektur (jangan salah kaprah)
1. **LLM Generative** — Qwen2.5-7B + LoRA (core, generate token-by-token)
2. **RAG + Agent Tools** — ReAct loop, 36 tools
3. **Growth Loop** — LearnAgent, Jariyah, auto-LoRA retrain

### Deploy VPS
- Domain publik: `app.sidixlab.com` (UI) dan `ctrl.sidixlab.com` (API)
- Detail port, path server, dan env var: lihat `.env` di server — jangan tulis di sini
- Deploy command: `git pull && npm run build && pm2 restart sidix-ui`

### GPU — Status
- VPS saat ini: CPU-only → semua generative module jalan di **mock/stub mode**
- Opsi GPU: cloud GPU per-jam (hybrid), atau upgrade ke GPU VPS
- Untuk aktifkan FLUX.1 nyata: install `diffusers torch` + set `SIDIX_IMAGE_DEVICE=cuda`
- Untuk aktifkan Piper TTS nyata: download binary piper + voice model (~60MB/bahasa)

---

## Catatan Owner

- Dokumen sprint pribadi di lokal → **jangan commit**
- Folder `data/` → generated media, masuk `.gitignore`
- Recovery: `git clone [repo-remote]` → semua kode kembali (remote URL lihat `.git/config`)
- Research notes: `brain/public/research_notes/` → sudah di-commit semua
- LIVING_LOG: `docs/LIVING_LOG.md` → sudah di-commit

---

*Checkpoint dibuat sesi 2026-04-24. Agent berikutnya: baca ini sebelum lanjut.*
