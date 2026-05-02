# HANDOFF CLAUDE — 2026-05-02
## Status: ACTIVE BRANCH + LIVE VPS

**Branch**: `work/gallant-ellis-7cd14d`  
**Latest commit**: `269115f`  
**VPS**: Deployed ✅ — `ctrl.sidixlab.com` (brain:8765) + `app.sidixlab.com` (UI:4000)

---

## 🔴 BACA INI DULU — Canonical Deploy Command

```bash
cd /opt/sidix && git pull origin work/gallant-ellis-7cd14d && pm2 restart sidix-brain --update-env
```

Frontend rebuild (kalau ada perubahan UI):
```bash
cd /opt/sidix/SIDIX_USER_UI && npm run build && pm2 restart sidix-ui --update-env
```

---

## ✅ SUDAH SELESAI — Sesi 2026-05-01 s/d 2026-05-02

### 1. Bug Fix Critical: chat_holistic 0-byte response
- **Root cause**: `SourceResult.__init__()` missing required `source` arg di `omnyx_direction.py:488`
- **Fix**: `src = SourceResult(source=r.tool_name, ...)`
- **File**: `apps/brain_qa/brain_qa/omnyx_direction.py`

### 2. Web Search Fix: Mojeek 403 + DDG Blocked dari VPS
- **Root cause**: VPS IP diblokir DDG dan Mojeek
- **Fix**: Tambah `_wikipedia_search_async()` sebagai fallback ketiga di `mojeek_search.py`
- **User-Agent**: `SIDIXKnowledgeSearch/1.0 (https://sidixlab.com; ...)` (RFC bot UA)
- **File**: `apps/brain_qa/brain_qa/mojeek_search.py`

### 3. Playwright Fix: libasound.so.2 missing
- `apt-get install -y libasound2 libgbm1 libgtk-3-0`
- `playwright install-deps chromium`

### 4. Sprint Auto-Harvest
- **File baru**: `apps/brain_qa/brain_qa/auto_harvest.py`
- **File baru**: `apps/brain_qa/scripts/harvest_cron.py`
- **File baru**: `apps/brain_qa/crontab.example`
- **Pipeline**: Google Trends RSS → Wikipedia → YAML notes → BM25 reindex
- **Crontab di VPS**: `0 */6 * * *` (setiap 6 jam)
- **Admin token**: `BRAIN_QA_ADMIN_TOKEN` env var di `/opt/sidix/.env`

### 5. Deploy Sprint A–K (Kimi)
- **Commit**: `2e0f802` — 15 files, spawning/ package, persona_adapter.py
- **QA**: Sprint A, F, G, I, K endpoints semua HTTP 200
- **corpus**: 3237 docs setelah reindex
- **Catatan**: `/agent/maqashid/profile` → 404, yang benar `/agent/maqashid/tuned`

### 6. Cleanup 7 Audit Issues (Kimi)
1. ✅ Delete orphan `sanad_orchestrator.py` (665 baris duplikat)
2. ✅ Fix `tools_used` mismatch di `self_test_loop.py:208`
3. ✅ Refactor `asyncio.run()` → `loop.run_until_complete()` di `pencipta_mode.py`
4. ✅ Wire `persona_adapter.py` ke OMNYX di `omnyx_direction.py`
5. ✅ Fix filename mismatch aspiration docs
6. ✅ Update header docs
7. ✅ Prompt-only adapter (training pending)

### 7. Landing Page Donate Button
- PayPal Hosted Button: `K37VVLFGJC5TY` (ko-fi: https://ko-fi.com/sidix)
- **File**: `SIDIX_LANDING/index.html`
- **Live**: sidixlab.com ✅

### 8. 🆕 Sprint J: Conversation Memory (SELESAI SESI INI)
- **Bug lama**: "siapa presiden?" → "kalo wakilnya?" → jawaban generik (LLM stateless)
- **Root cause**: setiap request berdiri sendiri, tidak ada history antar pesan
- **Fix**:
  - `apps/brain_qa/brain_qa/conversation_memory.py` — NEW: in-memory LRU store
  - `agent_serve.py` `chat_holistic` — load history dari `memory_store`, inject via `_inject_conversation_context()`, save setelah response
  - `SIDIX_USER_UI/src/api.ts` — `askHolistic()` kirim + terima `conversation_id`
  - `SIDIX_USER_UI/src/main.ts` — pass + persist `conversation_id`
  - `SIDIX_USER_UI/src/lib/session.ts` — NEW: session helpers
- **Fix 2**: `omnyx_direction.py` classifier — `[PERTANYAAN SAAT INI]` sentinel agar classify hanya actual question, bukan full context block
- **Fix 3**: OMNYX PATTERNS — tambah `wakilnya`, `kalo`, `gimana` ke factual_who/factual_what agar route ke simple fast path (bukan 90s analytical)
- **E2E test VPS**: Turn 1 → Turn 2 → Turn 3 semua NYAMBUNG ✅
- **Commits**: `8df85f8`, `4d299e4`, `d3d101e`, `269115f`

---

## ⏳ PENDING — Yang Belum Dikerjakan

### P1 — Manual Merge Main (BLOCKED: conflict di 7 file kritis)
**Status**: Attempt dilakukan tapi abort karena risk
**File conflict**:
- `apps/brain_qa/brain_qa/agent_react.py`
- `apps/brain_qa/brain_qa/agent_serve.py`
- `apps/brain_qa/brain_qa/cot_system_prompts.py`
- `apps/brain_qa/brain_qa/omnyx_direction.py` (sudah banyak perubahan kita)
- `apps/brain_qa/brain_qa/mojeek_search.py`
- `SIDIX_USER_UI/src/main.ts`
- `SIDIX_USER_UI/src/api.ts`
**Action needed**: Manual review + selective merge. JANGAN auto-resolve. Prioritas: ambil semua perubahan dari branch kita, cek main apakah ada hal penting yang belum ada.

### P2 — Cleanup Untracked Files
File untracked yang perlu di-commit atau di-.gitignore:
```
brain/public/praxis/lessons/lesson_20260501_*.md  (16 files)
brain/patterns/
brain/pencipta/
brain/public/persona_corpus/
```
Action: `git add brain/public/praxis/lessons/ brain/patterns/ brain/pencipta/ && git commit`
VPS scripts (opsional di-.gitignore): `_check_*.py _deploy_vps.py _test_chat_vps.py`

### P3 — Sprint L: Self-Modifying + Foresight (BELUM DIMULAI)
Scope:
- Self-modifying: auto-refactor berdasarkan pattern extraction dari korpus
- Foresight: trend radar cron, weak signal aggregation
Referensi Kimi: `docs/MEGA_HANDOFF_2026_04_30.md` Sprint L section

### P4 — Sprint J Testing Lebih Dalam
- Test conversation memory lewat browser (live app) untuk confirm
- Test dengan sesi panjang (10+ turn) — apakah trim TTL bekerja
- Test "New Chat" button — apakah bersih history atau tidak

### P5 — LoRA Training (Backlog)
- `persona_adapter.py` masih prompt-only
- Training dataset dari conversation memory belum di-generate
- RunPod balance ~$24 — cukup untuk 1-2 run

---

## 🗺️ SPRINT MAP — Apa yang Setiap Sprint Hasilkan

| Sprint | Nama | Menghasilkan | Status |
|--------|------|-------------|--------|
| A | Sanad Orchestra | Validator klaim (chain of custody untuk setiap fakta) — cek apakah jawaban punya sanad/sumber valid | ✅ Live |
| B | Hafidz Injector | Memori "golden examples" — inject contoh jawaban terbaik sebelumnya ke dalam context synthesis | ✅ Live |
| C | Pattern Extractor | Belajar dari percakapan — ekstrak pola domain knowledge dari chat history ke korpus | ✅ Live |
| D | Aspiration Detector | Deteksi intent jangka panjang user — apa yang user coba capai di luar pertanyaan literal | ✅ Live |
| E | Pencipta Mode | Mode kreatif — SIDIX bisa "menciptakan" konten generatif (puisi, narasi, ide) bukan hanya menjawab | ✅ Live |
| F | Self-Test Loop | SIDIX evaluasi diri sendiri — generate pertanyaan, jawab, score hasilnya untuk tracking kualitas | ✅ Live |
| G | Maqashid Auto-Tune | Alignment tuning — menyesuaikan tone + prioritas jawaban berdasarkan 5 tujuan (life/intellect/family/wealth/faith) | ✅ Live |
| H | Creative Polish | Iterasi output kreatif — refine jawaban secara otomatis sampai memenuhi kriteria kualitas | ✅ Live |
| I | DoRA Persona Adapter | Foundation untuk fine-tuning per-persona menggunakan DoRA (prompt-only dulu, training later) | ✅ Live |
| J | Conversation Memory | **Multi-turn context** — SIDIX ingat percakapan sebelumnya dalam satu sesi (fix "kalo wakilnya?") | ✅ Live |
| K | Multi-Agent Spawning | SIDIX bisa spawn sub-agent untuk task paralel — fondasi untuk "1000 Bayangan" (Jurus Multi-Agent) | ✅ Live |
| L | Self-Modifying + Foresight | SIDIX auto-refactor diri berdasarkan pola ekstraksi + radar tren untuk proactive knowledge update | 🔲 Belum |

---

## 🧠 ARSITEKTUR SAAT INI

```
User Browser (app.sidixlab.com:4000)
    │
    ▼ HTTPS
Nginx Proxy
    ├── app.sidixlab.com → port 4000 → sidix-ui (serve dist/)
    └── ctrl.sidixlab.com → port 8765 → sidix-brain (FastAPI)
    
sidix-brain (FastAPI — PM2)
    ├── /agent/chat          → ReAct loop (memory_store history)
    ├── /agent/chat_holistic → OMNYX Director (conversation_memory Sprint J)
    ├── /agent/spawn         → Multi-Agent (Sprint K)
    ├── /corpus/*            → BM25 RAG management
    └── /health              → status + metrics

OMNYX Director Flow:
    1. Load conversation history (memory_store SQLite)
    2. Inject context ke query
    3. IntentClassifier → simple/analytical
    4. ToolExecutor → corpus_search | web_search | persona_brain
    5. Synthesizer (qwen2.5:1.5b/7b via Ollama)
    6. Sanad validation + Hafidz injection
    7. Save to memory_store
    8. Return answer + conversation_id
```

---

## 🔧 ENV VARS PENTING (VPS: /opt/sidix/.env)

```
BRAIN_QA_ADMIN_TOKEN     # untuk /corpus/reindex + /admin/* endpoints
RUNPOD_API_KEY           # GPU inference endpoint
RUNPOD_ENDPOINT          # https://api.runpod.ai/v2/ws3p5ryxtlambj/run
SIDIX_EMBED_MODEL        # bge-m3 (default)
```

⚠️ PM2 tidak auto-load .env — gunakan ecosystem.config.js atau export sebelum pm2 start

---

## 📋 FILE PENTING YANG DIUBAH SESI INI

| File | Perubahan |
|------|-----------|
| `brain_qa/omnyx_direction.py` | SourceResult fix + classifier fix + PATTERNS extend + persona_adapter wire |
| `brain_qa/agent_serve.py` | chat_holistic wired ke conversation memory |
| `brain_qa/mojeek_search.py` | Wikipedia fallback + UA fix |
| `brain_qa/conversation_memory.py` | NEW — Sprint J in-memory store |
| `brain_qa/auto_harvest.py` | NEW — Sprint Auto-Harvest |
| `scripts/harvest_cron.py` | NEW — Cron script |
| `SIDIX_USER_UI/src/api.ts` | askHolistic + conversationId |
| `SIDIX_USER_UI/src/main.ts` | pass + persist conversationId |
| `SIDIX_USER_UI/src/lib/session.ts` | NEW — session helpers |
| `tests/test_conversation_memory.py` | NEW — 9 test scenarios |
| `SIDIX_LANDING/index.html` | PayPal + Ko-fi donate button |

---

## 🚀 NEXT AGENT INSTRUCTIONS

1. **Baca file ini dulu** (HANDOFF_CLAUDE_2026-05-02.md)
2. **Cek LIVING_LOG tail**: `tail -100 docs/LIVING_LOG.md`
3. **Deploy command** (selalu): `cd /opt/sidix && git pull origin work/gallant-ellis-7cd14d && pm2 restart sidix-brain --update-env`
4. **Test health**: `curl -s http://localhost:8765/health | python3 -m json.tool`
5. **Priority kerja**:
   - P1: Cleanup untracked files (commit praxis lessons + brain/patterns)
   - P2: Sprint L planning + impl
   - P3: Manual merge main (hati-hati conflict)
