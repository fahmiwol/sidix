# 🎯 BLUEPRINT: Claude — Optimasi SIDIX 2.0 (Post-Pivot)

> **Tanggal:** 2026-04-25  
> **Dari:** Kimi (diskusi seharian, rate-limited di akhir)  
> **Untuk:** Claude (eksekutor, karena kehilangan konteks karena error)  
> **Commit base:** `2531d23` — LOG: Full VPS deploy completed  
> **VPS:** 72.62.125.6 | Backend: port 8765 | Web: sidixlab.com / app.sidixlab.com  

---

## 🧠 VISI SIDIX 2.0 (Yang Sudah Kita Setujui Hari Ini)

**SIDIX = "bocah ajaib"** — genius, creative, human, autonomous.
- **Default = Agent Mode** (proactive, kreatif, tanpa filter) — `agent_mode=True`, `strict_mode=False`
- **Strict Mode = opt-in** (RAG-first, filter lengkap, untuk factual queries)
- **Persona = "ways of being"** (bukan role mask) — 5 persona: AYMAN/ABOO/OOMAR/ALEY/UTZ
- **Multi-layer memory** — working + episodic + semantic + procedural
- **Self-learning** — auto-extract pattern dari sesi sukses
- **Humanis > sempurna** — boleh nanya balik, ragu, punya opini, nggak formal

**KONTRAK dengan user (Mighan):**
- Own stack (Ollama + LoRA + corpus) — JANGAN jadikan Claude API / OpenAI / Gemini sebagai default inference
- API eksternal hanya sebagai perbandingan/benchmark
- Public artifact tanpa footprint vendor

---

## 📋 STATUS TERKINI (Hari Ini — Sudah Dilakukan)

### ✅ Sudah Selesai (Kimi)
| # | Pekerjaan | Detail |
|---|-----------|--------|
| 1 | Pivot fundamental | Default agent mode, strict_mode opt-in, system prompt rewrite |
| 2 | Multi-layer memory | `agent_memory.py` — 4 layer + `learn_from_session()` |
| 3 | Streaming endpoint | `/agent/generate/stream` SSE |
| 4 | Persona rewrite | "Ways of being" — AYMAN/ABOO/OOMAR/ALEY/UTZ |
| 5 | Greeting persona-aware | Fallback greeting sesuai persona (bukan formal) |
| 6 | Error obs filter | Skip error text masuk ke corpus_context |
| 7 | Persona compact | Dari ~300 token → ~80 token untuk model 1.5B |
| 8 | Frontend UX | Thinking indicator, hide confidence/feedback |
| 9 | Deploy VPS | Pull, rebuild UI, sync landing, restart brain+ui |

### ✅ Sudah Selesai (Claude — dari log VPS)
| # | Pekerjaan | Commit |
|---|-----------|--------|
| 1 | Casual gate | `c99415d` — bypass [EXPLORATORY] untuk casual query |
| 2 | Ollama timeout fix | `0db6ee0` — `OLLAMA_MODEL=qwen2.5:1.5b` + `.env` sourcing |
| 3 | Backend crash fix | `e111c2a` + `85695f6` — `start_brain.sh` + GenerateRequest schema |
| 4 | Coding planner spam | `0db6ee0` — downgrade empty-action ke DEBUG |
| 5 | Landing/UI sync | `9a3bf0c` + `0009378` — rebuild + footer v2.0 |

---

## 🔴 ROOT CAUSE ANALYSIS (Masalah yang MASIH ADA)

### Masalah #1 — Response Masih Formal / Robotik
**Observasi:** "Halo! Bagaimana saya bisa membantu Anda hari ini?" — ini adalah training default model, BUKAN persona AYMAN.

**Root Cause:**
1. Model `qwen2.5:1.5b` terlalu kecil (~1B effective) untuk **persona following** yang kompleks
2. System prompt SIDIX + persona compact (~80 token) masih terlalu panjang untuk 1.5B
3. Model fallback ke training default (chatbot formal) ketika instruction terlalu kompleks
4. Greeting regex match → model generate dari knowledge sendiri, bukan dari persona hint

**Proof:**
- `_compose_final_answer` kirim `system=_combined_system` ke Ollama
- `ollama_llm.py` line 162: `combined_system = f"{SIDIX_SYSTEM}\n\nInstruksi tambahan runtime:\n{system.strip()}"`
- Model 1.5B mungkin hanya "mendengar" 30-40% dari system prompt

### Masalah #2 — "aku sedang mengalami masalah..." untuk Factual Query
**Observasi:** Ditanya "siapa presiden indonesia sekarang?" → response error/fallback panjang.

**Root Cause:**
1. `web_search` tool DIPANGGIL (regex match "presiden indonesia sekarang") tapi GAGAL execute di VPS
2. DuckDuckGo HTML scraping return error (timeout, blocked, atau network issue)
3. Error text masuk ke observation blocks → dikirim ke LLM sebagai corpus_context
4. Model 1.5B melihat error text dan generate parrot: "aku sedang mengalami masalah..."
5. **Note:** Kimi sudah fix filter error obs (commit `d5a2895`), tapi web_search TOOL ITU SENDIRI masih gagal

**Proof dari test lokal:**
```python
_tool_web_search({'query': 'presiden indonesia 2024'})
# Result: success=False, error="gagal search: ConnectError: [Errno 11001] getaddrinfo failed"
```

### Masalah #3 — Response Ngelantur / Tidak To-The-Point
**Observasi:** Ditanya "kenapa ga cari di search engine?" → jawaban panjang lebar teori teknis.

**Root Cause:**
1. Model 1.5B tidak cukup kuat untuk **instruction following** yang presisi
2. Tidak ada post-processing (truncation, summarization, atau re-prompting)
3. `max_tokens=600` terlalu besar untuk model kecil → model "ngisi" dengan fluff

### Masalah #4 — Backend Timeout / Terputus
**Root Cause:**
1. qwen2.5:1.5b di CPU masih butuh 5-15 detik per request
2. Tidak ada timeout handler + retry di frontend
3. Frontend belum pakai streaming endpoint (`/agent/generate/stream`) — masih pakai `/ask` synchronous
4. User tidak tahu sistem sedang proses (thinking indicator baru di-fix tapi belum rebuild sampai deploy terakhir)

### Masalah #5 — Web Search Tidak Bisa Fetch Data Real-Time
**Root Cause:**
1. DuckDuckGo HTML endpoint (`html.duckduckgo.com`) mungkin blocked atau timeout di VPS China
2. Tidak ada fallback search engine (Bing, Google, SerpAPI, Brave)
3. `allow_web_fallback=True` tapi tidak ada web search yang jalan

---

## 🎯 RENCANA EKSEKUSI UNTUK CLAUDE

### FASE A: VALIDASI (30 menit — WAJIB DULUAN)
**Tujuan:** Catat baseline sebelum optimasi. Tanpa baseline, tidak tahu apakah optimasi berhasil.

#### A1. Test Model + Persona
```bash
ssh root@72.62.125.6

# Test 1: Greeting AYMAN (harusnya hangat, bukan formal)
curl -s -X POST http://localhost:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"halo","persona":"AYMAN","strict_mode":false}' | head -c 500

# Test 2: Greeting UTZ (harusnya playful)
curl -s -X POST http://localhost:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"halo","persona":"UTZ","strict_mode":false}' | head -c 500

# Test 3: Factual + web search (harusnya jawab atau bilang tidak tahu)
curl -s -X POST http://localhost:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"siapa presiden indonesia sekarang","persona":"AYMAN","strict_mode":false}' | head -c 800

# Test 4: Direct generate (bypass ReAct)
curl -s -X POST http://localhost:8765/agent/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"halo, siapa kamu?","persona":"UTZ"}' | head -c 500
```

**Catat hasil:** Tone formal/kah? Ada [EXPLORATORY]? Ada "Keyakinan: tinggi"? Response lama/ngelantur?

#### A2. Test Web Search Direct
```bash
ssh root@72.62.125.6
cd /opt/sidix && source .venv/bin/activate
python3 -c "
from brain_qa.agent_tools import _tool_web_search
r = _tool_web_search({'query': 'presiden indonesia 2024', 'max_results': 3})
print('success:', r.success)
print('error:', r.error)
print('output:', (r.output or 'NO OUTPUT')[:500])
"
```

**Kalau gagal → cek network:**
```bash
curl -I https://html.duckduckgo.com  # Cek apakah DuckDuckGo reachable
curl -I https://www.google.com        # Cek internet umum
```

#### A3. Test Health Endpoint
```bash
curl -s http://localhost:8765/health | python3 -m json.tool
```

---

### FASE B: FIX WEB SEARCH (Prioritas 🔴 HIGH)
**Tujuan:** Web search HARUS jalan — ini kunci untuk factual accuracy.

#### B1. Kalau DuckDuckGo Gagal (Blocked/Timeout)
**Opsi 1 — DuckDuckGo dengan proxy:**
- Cek apakah VPS perlu proxy (server China kadang block DuckDuckGo)
- Atau coba `https://lite.duckduckgo.com/lite/` (endpoint lebih simple)

**Opsi 2 — Ganti search engine (rekomendasi):**
Tambah konfigurasi di `.env`:
```bash
SEARCH_ENGINE=bing  # duckduckgo | bing | brave | serpapi
BING_API_KEY=xxx    # free tier: 1000 query/bulan
```

Implementasi di `agent_tools.py`:
```python
def _tool_web_search(args: dict) -> ToolResult:
    engine = os.environ.get("SEARCH_ENGINE", "duckduckgo")
    if engine == "bing":
        return _search_bing(args)
    elif engine == "brave":
        return _search_brave(args)
    # fallback duckduckgo
```

**Opsi 3 — Hybrid (fallback chain):**
```
DuckDuckGo → kalau gagal dalam 5 detik → Bing API → kalau gagal → model knowledge
```

#### B2. Web Search Result Processing
Saat ini web_search result hanya return URL + snippet. Perlu:
- Fetch 1-2 halaman top result untuk extract konten lengkap
- Simpan ke observation blocks sebagai "ringkasan artikel", bukan cuma URL list
- Ini membutuhkan `webfetch.py` yang sudah ada — wire ke ReAct loop

---

### FASE C: MODEL DECISION (Prioritas 🔴 HIGH)
**Tujuan:** Putuskan apakah 1.5B cukup atau perlu upgrade.

#### C1. Evaluasi 1.5B Setelah Fix Web Search
Setelah web_search jalan, test lagi:
```bash
# Test dengan web search jalan — harusnya bisa jawab factual
curl -s -X POST http://localhost:8765/agent/chat \
  -d '{"question":"siapa presiden indonesia sekarang","persona":"AYMAN"}'
```

**Kalau masih gagal → masalahnya BUKAN web search, tapi model memang terlalu lemah.**

#### C2. Decision Matrix

| Scenario | Action | Effort | Cost |
|----------|--------|--------|------|
| 1.5B + web search jalan + persona OK | Keep 1.5B, optimasi prompt | Low | Free |
| 1.5B + web search jalan + persona masih formal | Upgrade ke 3B/7B | Medium | GPU/CPU |
| 1.5B + web search gagal (tidak bisa fix) | Upgrade ke 7B + ganti search | High | GPU |

**Rekomendasi Kimi:** Upgrade ke **qwen2.5:7b** minimum. 1.5B tidak cukup kuat untuk persona following + tool calling + factual reasoning. Ini bukan masalah prompt — ini masalah kapasitas model.

#### C3. Upgrade Path (kalau diputuskan)
```bash
# Di VPS
ollama pull qwen2.5:7b
# Edit .env
OLLAMA_MODEL=qwen2.5:7b
# Restart
pm2 restart sidix-brain
```

**RAM requirement:** qwen2.5:7b = ~4-5GB RAM. VPS saat ini punya berapa? Cek:
```bash
free -h
```

**Kalau RAM < 6GB → tidak bisa 7B.** Solusi:
- Quantized model: `qwen2.5:7b-q4_0` (lebih kecil, sedikit quality drop)
- Atau upgrade VPS ke tier lebih tinggi
- Atau pakai API eksternal sebagai **bridge sementara** (dengan label "POC bridge")

---

### FASE D: STREAMING FRONTEND (Prioritas 🟡 MEDIUM)
**Tujuan:** UX lebih responsif, tidak terasa "hang".

#### D1. Wire Streaming ke UI
Frontend saat ini pakai `/ask` (synchronous, tunggu full response). Streaming endpoint `/agent/generate/stream` sudah ada di backend tapi UI belum pakai.

**File:** `SIDIX_USER_UI/src/api.ts` dan `SIDIX_USER_UI/src/main.ts`

**Yang perlu diubah:**
1. `askStream()` function — sudah ada, tapi mungkin masih pakai `/ask` endpoint
2. Ganti ke `/agent/generate/stream` untuk generation
3. Atau tambah streaming untuk `/agent/chat` juga

**Note:** Streaming untuk ReAct loop lebih kompleks karena ada multiple steps. Streaming untuk `/agent/generate` (direct generation) lebih simple — cocok untuk casual chat.

**Rekomendasi:**
- Casual/greeting query → pakai `/agent/generate/stream` (fast, direct)
- Factual/research query → pakai `/agent/chat` (ReAct, slower tapi accurate)

---

### FASE E: RESPONSE POST-PROCESSING (Prioritas 🟡 MEDIUM)
**Tujuan:** Response lebih to-the-point, tidak ngelantur.

#### E1. Max Token Clamp untuk Model Kecil
```python
# Di _compose_final_answer
max_tokens = 300 if model_is_small else 600  # 1.5B = 300 max
```

#### E2. Question-Answer Relevance Check
Tambah lightweight check: apakah jawaban benar-benar menjawab pertanyaan?
```python
def _is_answer_relevant(question: str, answer: str) -> bool:
    # Simple heuristic: answer harus mengandung keyword dari question
    # atau panjang answer tidak lebih dari 3x panjang question
    pass
```

#### E3. Truncate / Summarize Ngelantur
Kalau response > 500 token dan tidak ada struktur (bullet, paragraph), truncate dan tambah "..."

---

### FASE F: EVALUATION FRAMEWORK (Prioritas 🟢 LOW — tapi penting)
**Tujuan:** Objective benchmark untuk tahu apakah optimasi berhasil.

#### F1. Buat Test Suite Kecil
File: `tests/test_sidix2_quality.py`

```python
TEST_CASES = [
    {
        "question": "halo",
        "persona": "AYMAN",
        "checks": {
            "not_contains": ["[EXPLORATORY]", "Berdasarkan referensi", "Keyakinan:"],
            "tone": "casual_warm",
        }
    },
    {
        "question": "siapa presiden indonesia sekarang",
        "persona": "AYMAN",
        "checks": {
            "not_contains": ["aku sedang mengalami masalah", "tidak tahu"],
            "contains_any": ["Prabowo", "Subianto", "presiden"],
        }
    },
    {
        "question": "1+1 berapa",
        "persona": "ABOO",
        "checks": {
            "contains": ["2"],
            "tone": "direct_concise",
        }
    },
]
```

#### F2. Automated Benchmark
```bash
python -m pytest tests/test_sidix2_quality.py -v
```

---

## 📎 FILE YANG PERLU DISENTUH CLAUDE

### High Priority
| File | Perubahan |
|------|-----------|
| `apps/brain_qa/brain_qa/agent_tools.py` | Fix/add web search engine (Bing/Brave fallback) |
| `apps/brain_qa/brain_qa/agent_react.py` | Max token clamp, relevance check, answer hygiene |
| `SIDIX_USER_UI/src/api.ts` | Wire streaming endpoint |
| `SIDIX_USER_UI/src/main.ts` | Streaming UI handler |
| `/opt/sidix/.env` | Add SEARCH_ENGINE, BING_API_KEY, dll |

### Medium Priority
| File | Perubahan |
|------|-----------|
| `apps/brain_qa/brain_qa/ollama_llm.py` | Model size detection, dynamic max_tokens |
| `apps/brain_qa/brain_qa/webfetch.py` | Wire to ReAct loop untuk fetch web result |
| `tests/test_sidix2_quality.py` | New file — automated benchmark |

---

## 🎨 KONSEP VISUAL / UX (Dari Diskusi Hari Ini)

User ingin:
1. **Thinking animation** — sudah di-fix Kimi ("Sedang berpikir..." + dot animation)
2. **Stream bubble hidden** — sudah di-fix Kimi (muncul setelah token pertama)
3. **No metadata clutter** — sudah di-fix Kimi (hide Keyakinan + feedback untuk casual)
4. **Persona switch smooth** — dropdown persona di header harusnya instant switch
5. **Response style berbeda per persona** — ini masih lemah karena model kecil

---

## ⚠️ ANTI-BENTROK NOTE (Override untuk Session Ini)

User secara eksplisit meminta: **"kamu kasih idenya aja, biar claude bantu eksekusi"**

Artinya untuk optimasi ini:
- **Kimi = Architect / Ideator** — visi, root cause, rencana
- **Claude = Executor / Implementor** — kode, deploy, validasi
- **Shared territory** — evaluation framework, infra decision

Claude boleh sentuh file apapun yang diperlukan untuk eksekusi rencana ini.

---

## ✅ CHECKLIST: Claude Mulai dari Sini

```
□ 1. Baca docs/VALIDASI_CLAUDE_20260425.md — jalankan test cases, catat hasil
□ 2. Test web_search direct di VPS — DuckDuckGo jalan atau tidak?
□ 3. Cek RAM VPS — cukup untuk 7B atau tidak?
□ 4. Putuskan: keep 1.5B + fix web search ATAU upgrade ke 7B
□ 5. Eksekusi fix web search (Bing/Brave fallback atau DuckDuckGo fix)
□ 6. Test lagi factual query — masih "aku sedang mengalami masalah" atau tidak?
□ 7. Kalau model masih lemah → upgrade ke 7B (atau q4_0 quantized)
□ 8. Wire streaming ke frontend (opsional — UX improvement)
□ 9. Buat evaluation test suite
□ 10. Commit + push ke main
□ 11. Update docs/LIVING_LOG.md dengan hasil
```

---

## 💬 KONTESK DISKUSI HARI INI (Ringkasan Singkat)

**Pagi:** Pivot fundamental SIDIX 2.0 — personality overhaul, system prompt rewrite, persona as "ways of being"
**Siang:** Multi-layer memory, streaming endpoint, self-learning, deep research docs
**Sore:** Deploy ke VPS — branch confusion fix, backend restart, UI rebuild
**Malam:** Response masih formal/error — analisis root cause, fix greeting + error filter + persona compact

**Visi user yang paling sering diulang:**
- "ubah yang bikin SIDIX kaku, ubah fundamentalnya yang terlalu banyak aturan"
- "SIDIX harus jadi AI Agent paling handal... casual mode"
- "Bukan chatbot. An AI Agent with initiative, opinions, and creativity."

---

*Blueprint ini dibuat oleh Kimi sebagai continuity untuk Claude. Semua root cause sudah dianalisis, rencana sudah jelas — tinggal eksekusi.*
