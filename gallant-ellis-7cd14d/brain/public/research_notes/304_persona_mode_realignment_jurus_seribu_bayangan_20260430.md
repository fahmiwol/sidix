---
title: Persona Mode Re-Alignment — Jurus Seribu Bayangan as Default
date: 2026-04-30
sprint: Pre-Sprint-0 (Re-Alignment ke Visi Northstar)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: founder dialogue 2026-04-30 evening + screenshot help modal UI lama + audit persona_research_fanout.py + research notes 279/281/288
---

# 304 — Persona Mode Re-Alignment: Jurus Seribu Bayangan as Default

## Bos Catch Yang Critical

Screenshot help modal UI lama menunjukkan tagline yang tertulis di SIDIX_USER_UI:

> **ROUTING OTOMATIS** — SIDIX secara otomatis memilih sumber terbaik: knowledge base lokal, web search, atau reasoning — tergantung pertanyaanmu.
>
> Pertanyaan tentang berita/harga/info terkini → otomatis web search.
> Pertanyaan coding/teknis → corpus + reasoning lokal.

Bos respond:

> "itu masih gitu? kalo secara ide konsep saya kan nggak gitu yah? **ga routing otmatis, tapi mengerahkan segala resource berbarengan intinya. jurus seribu bayangan dll, sanad** (atau sengaja kamu ubah karena ide saya bikin ngaco)"

**Bos's vision sebenarnya BUKAN routing-pilih-satu-sumber**. Visi bos: **MENGERAHKAN SEMUA RESOURCE PARALEL** — jurus seribu bayangan + sanad multi-source verifikasi + cognitive synthesis.

UI lama "ROUTING OTOMATIS" framing = degradasi konservatif dari visi bos. Saya (atau Claude sebelumnya) menulisnya begitu mungkin karena:
- Lebih simple secara teknis (1 sumber per query = cepat)
- Tapi LANGGAR Northstar (SIDIX = multi-perspective, multi-source, holistic)

Bos catch ini sebagai miss-alignment. Re-align WAJIB.

## Visi Northstar Bos (Verbatim Chain)

> "saya cuma tau maunya sidix **genius, creative, tumbuh → cognitive & semantic → iteratif → inovasi → pencipta**"

Translation engineering (mapping bos's chain ke kapabilitas teknis):

| Visi Word | Teknis Existing | Status |
|---|---|---|
| **Genius** | Jurus seribu bayangan (paralel multi-source) + sanad verifikasi multi-source | Scaffold ada (`persona_research_fanout.py`), BELUM wired ke /agent/chat |
| **Creative** | 5 persona perspectives + Sigma-3D creative methodology (METAFORA VISUAL, KEJUTAN SEMANTIK, dll) | Sigma-3D LIVE di UTZ persona |
| **Tumbuh** | Daily corpus growth (learn/run cron) + LoRA retraining + cognitive_synthesis_kernel iterasi | DNA cron aktif, LoRA pipeline belum verify |
| **Cognitive & semantic** | semantic_cache (PyTorch fix kemarin) + dense_index + embedding model | LIVE post PyTorch upgrade hari ini |
| **Iteratif** | Sigma sprints compound (Sigma-1/2/3/4 + brain stability fix + cognitive expansion) | LIVE, 11+ commits hari ini |
| **Inovasi** | Novel methods compound — note 291 catat semua method baru per sprint | LIVE catat |
| **Pencipta** | SIDIX bukan execute saja, tapi CREATE — output type adaptive (text/script/image/video) | Foundation creative methodology LIVE, output adaptive belum |

## Mental Model Bos (3 Mode SIDIX)

| Mode | Karakter | Otak | Use Case |
|---|---|---|---|
| **Basic / Natural (DEFAULT)** | SIDIX murni, tanpa persona | Pengetahuan dasar (LoRA + corpus) — tapi internally tetap jurus seribu bayangan + sanad | Pertanyaan sehari-hari, default user experience |
| **Single Persona** (5 pilihan optional) | UTZ creative · ABOO engineer · OOMAR strategist · ALEY researcher · AYMAN empati | Per-persona system prompt + lens spesifik | Saat user tahu butuh sudut spesifik (mis. code → ABOO) |
| **Pro / Multi-Perspective** | Gabungan 5 persona explicit | TIDAK punya otak sendiri — sintesis dari 5 persona | Pertanyaan kompleks butuh banyak sudut sekaligus (strategi bisnis, brand, decision besar) |

**Insight**: Bos bilang "Basic jadi default". Itu artinya **default user experience = Basic = SIDIX naturally**, BUKAN forced pilih persona. Tapi internally Basic tetap kerahkan jurus seribu bayangan.

## Audit State Code (Apa Yang Sudah Ada)

**70% infrastructure sudah ada**, tapi belum di-wire user-facing:

✅ Sudah ada:
- `persona_research_fanout.py` — scaffold paralel 5-persona (Sprint 40 Phase 1)
- `agent_burst.py` — endpoint `/agent/burst` (mode burst di UI lama)
- `cot_system_prompts.py` — 5 persona descriptions lengkap dengan voice distinct + Sigma-3D creative methodology
- `sanad_verifier.py` — sanad multi-source dengan brand canon (13 entries)
- `fact_extractor.py` — 12 entity types, role-aware cleaner
- `semantic_cache.py` + `dense_index.py` — embedding-based retrieval (post PyTorch fix)

⚠️ Gap (yang perlu dibangun):
- **Persona fanout cuma wired ke `autonomous_developer`**, bukan ke `/agent/chat` user-facing
- **Cognitive synthesis kernel** — modul yang ambil 5 output persona → merge jadi 1 jawaban utuh
- **Multi-source paralel default** untuk `/agent/chat` Basic mode (bukan routing pilih-satu)
- **Streaming SSE** untuk perceived latency (sekarang user wait 60-100s freeze)

## 3 Sprint Candidate Yang Sebelumnya Saya Propose (CATAT)

### Sprint A — Pro Mode (Multi-Perspective Synthesis)
- Wire `persona_research_fanout` ke `/agent/chat` sebagai mode Pro
- Pakai Ollama lokal (gratis CPU) untuk 5 persona think paralel
- Pakai RunPod (GPU) hanya untuk synthesis akhir
- ~60s end-to-end (vs 30-60s single persona = 2x slower untuk insight 5x lebih kaya)
- **Effort**: 2-3 session

### Sprint B — Persona UX Explainer + Auto-Suggest
- Tooltip persona dropdown: 1-line use case per persona
- Auto-suggest based on query (regex: code → ABOO, brand → UTZ)
- Default Pro/Auto untuk user baru
- **Effort**: 1 session

### Sprint C — Streaming SSE
- Wrap `/agent/chat` dengan SSE streaming
- 105s wait → first byte 2 detik
- **Effort**: 2 session

### Sprint 0 — Brain Stability + Monitoring
- Wire health monitoring + auto-alert RunPod state
- Failover ke Ollama saat RunPod down
- Goldset re-run dengan Idle 300s
- **Effort**: 1 session

## Engineering Questions Yang Saya Tanya — Saya Jawab Sendiri

Bos eksplisit: *"pertanyaan yg kamu tanyakan ke saya, kamu yg bisa jawab sebagai engineering. saya cuma tau maunya sidix genius, creative, tumbuh"*. Saya ambil otoritas:

### Q1: Basic mode di UI eksplisit atau implicit?
**Decision: Basic = DEFAULT (selected by default)**. Persona = optional advanced tab. Mode = Basic kalau user tidak otak-atik. Internal Basic mode tetap jurus seribu bayangan (paralel multi-source) — simple UX, powerful internals.

### Q2: Cognitive synthesizer LLM tersendiri atau salah satu persona?
**Decision: Synthesizer = NEUTRAL LLM** (Qwen2.5-7B base, no persona system prompt). Reason: kalau pakai 1 dari 5 persona sebagai synthesizer, dia bias ke perspektifnya sendiri (UTZ akan over-creative-ize, ABOO akan over-technical-ize). Synthesizer harus netral, ambil best-of-5 + merge.

### Q3: Sequence prioritas?
**Decision baru (post re-alignment)**:
1. **Sprint 0 — Brain Stability + Monitoring** (1 session) — foundation reliability sebelum apa pun. RunPod EngineCore_DP0 died kemarin = real risk.
2. **Sprint Α (alpha) — Multi-Source Paralel Default** (3 session) — REPLACE routing otomatis dengan jurus seribu bayangan + sanad multi-source + cognitive synthesis sebagai DEFAULT Basic mode. Bukan optional Pro Mode. Visi bos: "kerahkan semua resource berbarengan" = default behavior.
3. **Sprint C — Streaming SSE** (2 session) — pasangan dengan Sprint Α. Tanpa streaming, multi-source paralel akan terasa freeze 60s+.
4. **Sprint B — UX Persona Explainer** (1 session) — last priority, fix existing UX yang user gatau pilih apa.

**Total**: 7 session. Realistic ~1-2 minggu post limit reset.

## Re-Aligned Sprint Plan (Pasti Sesuai Visi Bos)

### Sprint 0: Brain Stability + Monitoring [URGENT]

**Goal**: Foundation reliability — SIDIX tidak boleh mati saat user buka.

Tasks:
1. Health endpoint check + auto-alert (telegram/email kalau RunPod IN_QUEUE >5 menit)
2. Hybrid_generate fallback ke Ollama saat RunPod fail (sudah ada code, perlu tested)
3. Goldset re-run dengan Idle 300s yang bos baru set
4. Document common failure modes (EngineCore died, Qalb CRITICAL, dense_index dim mismatch)

Effort: 1 session.

### Sprint Α: Multi-Source Paralel Default (CORE — Visi Bos)

**Goal**: Replace routing-pilih-satu-sumber dengan jurus seribu bayangan + sanad + synthesis.

Tasks:
1. Modify `agent_react.py` — kalau Basic mode, paralel: `web_search` + `search_corpus` + `persona_fanout (5 persona ringkas)` simultan
2. Wire `sanad_verifier.py` cross-check antar sumber (existing, sudah handle multi-source)
3. Build `cognitive_synthesizer.py` baru — ambil semua output, merge jadi 1 jawaban dengan attribution per sumber
4. Update help modal UI lama: ganti "ROUTING OTOMATIS" → "JURUS SERIBU BAYANGAN" — SIDIX kerahkan semua resource paralel

Effort: 3 session.

### Sprint C: Streaming SSE

**Goal**: Perceived latency turun ke ~2-3 detik first byte.

Tasks:
1. SSE backend wrapper untuk `/agent/chat` (yield events: source-A-found, source-B-found, persona-1-thinking, ..., synthesis-streaming)
2. Frontend typewriter render untuk synthesis output
3. Live show "SIDIX sedang kerahkan: web_search ✓ corpus ✓ ALEY thinking... UTZ thinking..."

Effort: 2 session.

### Sprint B: UX Persona Explainer (Last)

**Goal**: User paham kapan pilih single persona override.

Tasks:
1. Tooltip per persona dengan use case
2. Quick prompts mapping ke persona suggestion (Coding → ABOO suggested)
3. Default = Basic, persona dropdown jadi advanced toggle

Effort: 1 session.

## Pelajaran Saya Catat

1. **"Routing otomatis" framing = degradasi visi bos**. Bos visi = MULTI-SOURCE PARALEL, bukan PILIH-SATU. Saya (atau Claude sebelumnya) tulis "routing otomatis" karena lebih simple, tapi melanggar Northstar.

2. **Bos's chain visi adalah holistic system, bukan feature-pick**. `genius/creative/tumbuh → cognitive&semantic → iteratif → inovasi → pencipta`. Setiap word adalah aspek kapabilitas yang harus aktif simultan.

3. **Engineering decisions = saya ambil**. Bos cuma tau visi end-state. Saya partner yang implement teknis. Anti-pattern: tanya bos detail teknis yang dia sendiri akui "saya cuma tau maunya genius/creative/tumbuh".

4. **Default UX simple, internal powerful**. Basic mode = no persona forced, tapi internal jurus seribu bayangan. User experience clean, kapabilitas full.

## Referensi
- Research note 279 (Cara SIDIX action — multi-perspective)
- Research note 281 (Sintesis multi-dimensi)
- Research note 288 (Cognitive synthesis kernel iteration pattern)
- `apps/brain_qa/brain_qa/persona_research_fanout.py` (scaffold Phase 1)
- `apps/brain_qa/brain_qa/sanad_verifier.py` (multi-source verifier)
- FOUNDER_JOURNAL — "2026-04-30 (lanjutan 7)" entry
