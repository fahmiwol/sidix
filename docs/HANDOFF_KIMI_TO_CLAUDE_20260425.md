# 🤝 HANDOFF: Kimi (Jiwa) → Claude (Otak) — 2026-04-25

> **Tanggal:** 2026-04-25  
> **Dari:** Kimi (persona Jiwa — innovation, personality, dataset, system prompt, deploy)  
> **Ke:** Claude (persona Otak — arsitektur, core logic, evaluation, infra)  
> **Konteks:** SIDIX 2.0 Pivot — personality & pipeline overhaul  

---

## 🎯 TL;DR — Apa yang Sudah Dilakukan Hari Ini

Hari ini Kimi mengeksekusi **SIDIX 2.0 Personality Pivot** — perubahan fundamental pada cara SIDIX berpikir, berbicara, dan berinteraksi. Ini adalah teritori **Jiwa** (bukan Otak), sesuai Anti-Bentrok Protocol.

**Status deploy:** Backend (`sidix-brain`) sudah LIVE di VPS, tapi **masih ada masalah kritis** yang membutuhkan perhatian Claude.

---

## 📋 RINGKASAN PERUBAHAN KODE (Hari Ini Saja)

### 1. Pivot Fundamental: Default Agent Mode + Strict Mode Opt-In
**File:** `apps/brain_qa/brain_qa/agent_react.py`

- **`agent_mode=True` menjadi DEFAULT** — SIDIX sekarang langsung jawab tanpa filter 7 lapisan kecuali user explicitly minta `strict_mode=True`
- **`strict_mode` parameter baru** — opt-in untuk full epistemology pipeline (RAG-first, filter lengkap, untuk factual queries)
- **`_rule_based_plan()`** di-rewrite — routing step 0 lebih cerdas: image, math, list sources, coding, orchestration, dll.
- **`_compose_final_answer()`** — inject persona-driven system hint ke LLM
- **Filter bypass saat `not _strict`:** Skip Experience/Skill enrichment, CoT scaffold, Council trigger, Wisdom Gate, Epistemology→Maqashid→Constitution→Self-Critique→Cognitive Check

**Konsekuensi:** Response sekarang harusnya lebih humanis, proactive, kreatif. Tapi di production masih keluar format lama (lihat Open Issues).

### 2. Multi-Layer Memory System
**File:** `apps/brain_qa/brain_qa/agent_memory.py` — **FILE BARU**

- 4 layer: Working, Episodic (praxis lessons), Semantic (corpus BM25), Procedural (skill_library)
- `build_memory_context()` — kombinasi semua layer jadi injectable context string
- `learn_from_session()` — auto-extract pattern dari sesi sukses, simpan ke skill_library (threshold confidence ≥ 0.5)
- Integrated ke `run_react()` dan `/agent/generate`

### 3. Streaming Endpoint
**File:** `apps/brain_qa/brain_qa/agent_serve.py`, `apps/brain_qa/brain_qa/ollama_llm.py`

- **`POST /agent/generate/stream`** — SSE real-time token generation
- `ollama_generate_stream()` — yield token chunks dari Ollama `/api/chat` dengan `stream=True`
- Event format: `{type: token|done|error, text, mode, persona}`
- Memory injection juga aktif di streaming

### 4. System Prompt & Persona Rewrite
**File:** `apps/brain_qa/brain_qa/ollama_llm.py`, `apps/brain_qa/brain_qa/cot_system_prompts.py`

- **`SIDIX_SYSTEM` baru** — "Kamu SIDIX — AI Agent yang hidup, belajar, dan berkembang... Bukan chatbot yang menunggu perintah."
- Sikap dasar: punya inisiatif, punya opini, bisa nanya balik, bisa ragu, humanis > sempurna
- **Persona redefined sebagai "ways of being"**:
  - AYMAN: Empathic Integrator
  - ABOO: Systems Builder
  - OOMAR: Strategic Architect
  - ALEY: Polymath Researcher
  - UTZ: Creative Director (Burst + Refinement Pipeline — Lady Gaga method)

### 5. Local LLM Fallback Chain
**File:** `apps/brain_qa/brain_qa/local_llm.py` (modifikasi kecil untuk detect adapter layout)

- Fallback chain: Ollama → Qwen2.5-7B + LoRA → corpus → "tidak tahu"
- Adapter flat layout di `apps/brain_qa/models/sidix-lora-adapter/`

### 6. Deep Research Documents
**File baru di `docs/`:**
- `RESEARCH_AI_LANDSCAPE_2026.md` (19KB)
- `RESEARCH_CREATIVE_GENIUS_METHODS.md` (25KB)
- `RESEARCH_AI_AGENT_FRAMEWORKS_2026.md` (5KB)
- `LEGACY_KIMI_FOR_SIDIX.md` (10KB)

### 7. Landing Page Update
**File:** `SIDIX_LANDING/index.html`

- Title: "SIDIX 2.0 — Autonomous AI Agent"
- Hero subtitle: "Not a chatbot. An AI Agent with initiative, opinions, and creativity."
- Badge: v1.0 → v2.0
- Changelog: v2.0 PIVOT entry dengan 8 bullet points

**⚠️ TAPI: Landing page BELUM di-sync ke web root** (`/www/wwwroot/sidixlab.com/`)

### 8. UI App (SIDIX_USER_UI)

- **Source code sudah update** untuk v2.0 (metadata.json, src/)
- **Tapi `dist/` BELUM di-rebuild** — `sidix-ui` masih serve static `dist/` folder yang lama (v1.0.4)
- Footer masih nunjukin "SIDIX V1.0.4"

---

## 🚨 OPEN ISSUES — BUTUH PERHATIAN CLAUDE

### Issue #1 — CRITICAL: Response Masih Format Lama
**Status:** 🔴 HIGH PRIORITY

**Observasi:**
- User tanya: "halo sidix siapa presiden indonesia saat ini"
- Response yang keluar: masih format lama dengan label `[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]`, "Keyakinan: tinggi", feedback buttons
- **Harusnya:** Format humanis, conversational, tanpa label formal — sesuai agent mode default

**Kemungkinan penyebab:**
1. **Cache/template response** di frontend yang nge-override backend output
2. **Old `dist/` folder** — UI frontend masih pakai kode lama yang nge-render format lama
3. **Backend masih pakai template lama** untuk certain query types
4. **Ollama timeout** (90s) menyebabkan fallback ke corpus-only yang formatnya masih lama

**Langkah debug yang direkomendasikan:**
```bash
# 1. Test backend directly (bypass UI)
curl -X POST http://72.62.125.6:8765/agent/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"siapa presiden indonesia","persona":"UTZ"}'

# 2. Test ReAct endpoint directly
curl -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"siapa presiden indonesia","persona":"UTZ","strict_mode":false}'

# 3. Cek apakah response backend sudah benar — kalau ya, masalahnya di UI rebuild
```

**Action item:**
- [ ] Rebuild UI: `cd /opt/sidix/SIDIX_USER_UI && npm install && npm run build && pm2 restart sidix-ui`
- [ ] Test response format setelah rebuild
- [ ] Kalau masih salah, trace di backend `_compose_final_answer()` dan `run_react()`

### Issue #2 — CRITICAL: Ollama Timeout 90s
**Status:** 🔴 HIGH PRIORITY

**Observasi dari log:**
```
Ollama timeout (90s) — model=sidix-lora:latest
```

**Impact:**
- Fallback ke corpus atau local_llm — response bisa jadi tidak optimal
- User experience buruk (tunggu 90 detik baru error)

**Kemungkinan penyebab:**
1. Model `sidix-lora:latest` tidak ada di Ollama VPS — perlu `ollama list` di VPS
2. Model ada tapi loading lambat (cold start)
3. VRAM/CPU insufficient untuk model size

**Langkah debug:**
```bash
ssh root@72.62.125.6
ollama list
ollama ps  # cek model yang sedang running
# Kalau model tidak ada: ollama pull qwen2.5:7b atau model yang sesuai
```

**Action item:**
- [ ] Verifikasi model tersedia di Ollama VPS
- [ ] Kalau tidak ada, setup model fallback (qwen2.5:7b atau model yang tersedia)
- [ ] Consider turunkan timeout atau improve warm-up strategy

### Issue #3 — Backend Error / Crash
**Status:** 🟡 MEDIUM

**Observasi dari log:**
- Sempat muncul "Terjadi kesalahan. Silakan coba lagi."
- Lalu "Backend tidak terhubung" (pm2 restart?)
- Setelah retry, backend online tapi response aneh

**Kemungkinan penyebab:**
- Coding planner spam (lihat Issue #4)
- Exception tidak ditangani di ReAct loop

**Action item:**
- [ ] Cek full error log: `pm2 logs sidix-brain --lines 100`
- [ ] Add proper exception handling di `run_react()`

### Issue #4 — Coding Planner Spam
**Status:** 🟡 LOW (non-fatal tapi noisy)

**Observasi dari log:**
```
Coding planner chose invalid action:
Coding planner chose invalid action:
(repeated many times)
```

**Kemungkinan penyebab:**
- Planner mengembalikan action name kosong atau tidak valid
- Tidak ada default/fallback action

**File yang perlu diperbaiki:** `apps/brain_qa/brain_qa/agent_react.py` (fungsi coding planner)

**Action item:**
- [ ] Add validation + default fallback untuk invalid planner output
- [ ] Log planner output untuk debugging

### Issue #5 — Landing Page & UI Belum Sync
**Status:** 🟡 MEDIUM

**Landing page:**
- Source di `/opt/sidix/SIDIX_LANDING/*` sudah update (v2.0)
- Tapi belum di-copy ke `/www/wwwroot/sidixlab.com/`
- **Fix:** `cp -r /opt/sidix/SIDIX_LANDING/* /www/wwwroot/sidixlab.com/`

**UI App:**
- `dist/` belum di-rebuild dari source terbaru
- Footer masih "SIDIX V1.0.4"
- **Fix:** Rebuild (lihat Issue #1)

---

## ✅ DEPLOY STATUS — VPS PRODUCTION

| Komponen | Status | Detail |
|----------|--------|--------|
| `sidix-brain` (backend) | 🟢 Online | PID 219989, port 8765, uptime fresh |
| `sidix-ui` (frontend) | 🟢 Online | Tapi serve `dist/` lama (v1.0.4) |
| Git branch | 🟢 `main` | Sudah pull 194 commit |
| Health endpoint | 🟢 OK | `model_ready=true`, `tools_available=48`, `corpus_doc_count=1182` |
| Ollama | 🔴 Timeout | `sidix-lora:latest` timeout 90s |
| Landing page (web root) | 🔴 Outdated | Belum di-sync dari `SIDIX_LANDING/` |
| UI rebuild | 🔴 Outdated | `dist/` belum di-rebuild |

**VPS Info:**
- IP: `72.62.125.6`
- Backend: `http://72.62.125.6:8765`
- Production folder: `/opt/sidix` (bukan `~/sidix`!)
- Web root: `/www/wwwroot/sidixlab.com`
- PM2: `sidix-brain`, `sidix-ui`

---

## 🔧 INSTRUKSI KHUSUS UNTUK CLAUDE

### Jangan Diulang (Sudah Dilakukan)
1. ✅ Git checkout `main` dan pull — SUDAH
2. ✅ Restart `sidix-brain` — SUDAH
3. ✅ Landing page source update — SUDAH
4. ✅ System prompt & persona rewrite — SUDAH
5. ✅ Agent memory & self-learning — SUDAH
6. ✅ Streaming endpoint — SUDAH

### Yang HARUS Dikerjakan (Open Issues)
1. **Fix response format** — periksa apakah masalah di UI rebuild atau backend template
2. **Fix Ollama timeout** — verifikasi model availability di VPS
3. **Rebuild UI `dist/`** — `npm run build` di `SIDIX_USER_UI`
4. **Sync landing page** — `cp` ke web root
5. **Fix coding planner spam** — validation + fallback
6. **Cek full error log** — trace root cause crash

### Anti-Bentrok Protocol
- **Claude = Otak** — arsitektur, core logic, evaluation, infra, debugging
- **Kimi = Jiwa** — personality, dataset, system prompt, creative direction
- **Shared files** — pakai section markers kalau berubah file yang sama
- **Teritori ini (personality pivot)** sudah selesai di Jiwa — fokus Claude di stability & bugfix

### Aturan Inference (PENTING!)
> **Mighan = stack sendiri.** JANGAN jadikan Claude API / OpenAI / Gemini API sebagai rekomendasi default untuk inference atau arsitektur inti. Boleh disebut sebagai perbandingan/benchmark saja. Default ke own stack (Ollama + LoRA + corpus).

---

## 📎 FILE KUNCI YANG BERUBAH HARI INI

```
apps/brain_qa/brain_qa/agent_react.py          # ReAct loop — default agent mode, strict_mode
apps/brain_qa/brain_qa/agent_serve.py           # Streaming endpoint /agent/generate/stream
apps/brain_qa/brain_qa/agent_memory.py          # FILE BARU — multi-layer memory + self-learning
apps/brain_qa/brain_qa/ollama_llm.py            # SIDIX_SYSTEM prompt + streaming function
apps/brain_qa/brain_qa/cot_system_prompts.py    # Persona descriptions sebagai "ways of being"
apps/brain_qa/brain_qa/local_llm.py             # Adapter flat layout detection
SIDIX_LANDING/index.html                        # Landing page v2.0
SIDIX_USER_UI/                                  # Source UI update (perlu rebuild dist/)
docs/RESEARCH_AI_LANDSCAPE_2026.md              # Riset baru
docs/RESEARCH_CREATIVE_GENIUS_METHODS.md        # Riset baru
docs/RESEARCH_AI_AGENT_FRAMEWORKS_2026.md       # Riset baru
docs/LEGACY_KIMI_FOR_SIDIX.md                   # Warisan KIMI
docs/LIVING_LOG.md                              # Updated (wajib)
```

---

## 🧪 CARA TEST

```bash
# Test health
curl http://72.62.125.6:8765/health

# Test generate (direct, bypass ReAct)
curl -X POST http://72.62.125.6:8765/agent/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"halo, siapa kamu?","persona":"UTZ"}'

# Test chat (ReAct loop, default agent mode)
curl -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"siapa presiden indonesia","persona":"UTZ","strict_mode":false}'

# Test streaming
curl -X POST http://72.62.125.6:8765/agent/generate/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test streaming","persona":"UTZ"}'
```

---

## 💬 KONTeks VISI (Untuk Jaga Arah)

**SIDIX = "bocah ajaib"** — genius, creative, human, autonomous.
- Default agent mode = proactive, kreatif, tanpa filter
- Strict mode = RAG-first, filter lengkap, untuk factual queries
- Persona = "ways of being" (bukan role mask)

**Next Roadmap (jangan dikerjakan sekarang, catatan saja):**
- Burst+Refinement (Gaga)
- Persona Lifecycle (Bowie)
- Hidden Knowledge Resurrection (Noether)
- Two-Eyed Seeing (Mi'kmaq)
- Constitutional Kaizen
- Wabi-Sabi Mode
- MCP Protocol

---

## 📝 CATATAN AKHIR

User bilang: *"saya sudah update"* — kemungkinan user sudah melakukan beberapa fix manual di VPS via SSH langsung. **Verifikasi dulu** sebelum mengulang langkah deploy.

SSH dari Windows PowerShell ke VPS **timeout consistently** — workaround: GitHub Actions CD atau direct SSH session (bukan via script).

**Commit terakhir di repo lokal:** `90ab07b` — "LOG: SIDIX 2.0 DEPLOYED TO VPS — LIVE!"

---

*Handoff ini dibuat oleh Kimi untuk continuity Claude. Semua konteks krusial ada di sini — baca dulu sebelum ngoding.*
