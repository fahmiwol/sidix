"""
Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT — attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.
"""

# Research Note 296 — Sanad Multi-Source Corrected Flow (founder directive 2026-04-30)

**Sanad**: founder directive verbatim 2026-04-30 + audit existing code (`persona_research_fanout.py`, `sanad_orchestrator.py`, `hafidz_ledger.py`, `agent_react.py`)
**Status**: FACT — semua claim grounded ke file path + line. PROPOSAL ARCHITECTURE — belum di-implement
**Tujuan**: koreksi pemahaman flow SIDIX yang benar setelah Sprint sebelumnya gagal anti-halu

---

## STATUS UPDATE 2026-04-30 — SEQUENCE LOCKED

Founder confirmed sequencing: **Σ-1G → Σ-1B → Σ-1A → sisanya**.

Mascot: **Option B** (image bos hero + SDXL 4 state variants via endpoint lts8dj4c7rp4z8).

Pacing discipline: 1 sub-task per session (usage limit context).

Next: Σ-1G — `tests/test_anti_halu_goldset.py` 20-question baseline.

**Σ-3 framework LOCKED 2026-04-30**: **Next.js (App Router)** — bukan Vite. Port components dari scaffolding Vite ke Next.js. PM2 reconfig `serve dist` → `next start`. Backend FastAPI 8765 unchanged. Reasoning: SEO + multi-tool scaling + Tiranyx ecosystem long-term.

---

## 1. Founder's Vision (verbatim flow)

```
(INPUT — user question / command)
    ↓
┌─────────────────────────────────────────────────────────────┐
│  PARALEL FAN-OUT                                            │
│                                                             │
│  Jurus 1000 Bayangan + Hafidz Ledger                        │
│    └─ web_search × N queries (rephrasing)                   │
│    └─ search_corpus × N queries                             │
│    └─ wiki_lookup, pdf_extract, etc.                        │
│                                                             │
│  5-Persona PARALEL Thinking (each independent)              │
│    UTZ   → brain (creative angle)   + own corpus + own tools│
│    ABOO  → brain (technical angle)  + own corpus + own tools│
│    OOMAR → brain (strategy angle)   + own corpus + own tools│
│    ALEY  → brain (academic angle)   + own corpus + own tools│
│    AYMAN → brain (community angle)  + own corpus + own tools│
│      └─ each spawn sub-agent dengan tool spesifik           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
        SANAD SYNTHESIZER
        Cross-verify multi-source × multi-perspective
        Compute relevance score → loop sampai answer benar
                   ↓
              (OUTPUT)
              type adaptive:
              ─ Render text / chat answer
              ─ Script (code/markdown)
              ─ Generative product (image, audio)
              ─ Tool execution result
              ─ Riset paper (PDF / markdown)
              ─ Video (script + storyboard)
              ─ Dashboard / data viz
              ─ etc.
```

**Inti**: jawaban TIDAK boleh bersumber dari satu agent / satu corpus / satu tool. Harus paralel multi-source + multi-perspective + cross-verify. Sanad bukan label epistemik di akhir — sanad adalah **mekanisme verifikasi** sebelum jawab.

---

## 2. State Aktual — INFRASTRUKTUR SUDAH ADA, TAPI ORPHANED

### Yang sudah dibangun (file path verified):

| Modul | Fungsi | Status wiring |
|---|---|---|
| `persona_research_fanout.py` | 5-persona parallel via ThreadPoolExecutor (Sprint 58B) | ✅ Wired ke `autonomous_developer` (background coding). ❌ TIDAK wired ke `/agent/chat` user-facing. |
| `sanad_orchestrator.py` | Sanad chain orchestration | Need audit — dipakai di mana? |
| `sanad_builder.py` | Build sanad chain | Need audit |
| `hafidz_ledger.py` + `hafidz_mvp.py` + `ledger.py` | Audit trail per iteration | ✅ Wired ke autonomous_dev. ❌ Belum ke chat. |
| `agent_react.py` (line 376 `_effective_max_steps`, line 2192 `for step_num in range(eff_max)`) | Single-agent ReAct loop, max 6 steps | ⚠️ INI yang dipakai `/agent/chat` — single-agent, tidak fan-out |
| `agent_burst.py` | Multi-angle brainstorm (Burst Mode) | Wired ke "Deep Thinking" button only |
| `cot_system_prompts.py` | 5 persona prompts | Dipakai di setiap LLM call sebagai role injection |

### Gap teridentifikasi:

1. **`/agent/chat` endpoint** (`agent_serve.py`) → call `agent_react.py` (single-agent ReAct).
   - **Tidak** call `persona_research_fanout`
   - **Tidak** call `sanad_orchestrator`
   - **Tidak** log ke `hafidz_ledger`
   - Akibat: user query = single perspective, single source priority. Halusinasi terjadi karena LLM training data prevail tanpa cross-check.

2. **Persona belum punya "brain sendiri" dalam arti standalone** — mereka cuma role-play injection di system prompt. Tidak ada per-persona corpus filter, per-persona tool subset, per-persona synthesizer yang independen.

3. **Sanad dipakai sebagai LABEL** (`[FACT]/[OPINION]/[UNKNOWN]`), bukan sebagai **VERIFICATION MECHANISM**. Founder vision: sanad cross-checks multi-source SEBELUM jawab.

4. **AKU database** (`inventory.db`) ingested tanpa cross-verify — ada konflik (Jokowi vs Prabowo equal confidence 0.75, sudah dihapus tapi root cause `learn_agent` tetap).

---

## 3. Hallucination Root Cause (concrete)

Berdasarkan test sesi 2026-04-29:

| Layer | Failure mode | Bukti |
|---|---|---|
| **L1 LLM training prior** | Qwen2.5-7B base trained 2024 → "presiden Indonesia = Jokowi" | Response: "saat ini (2026), presiden Indonesia adalah Joko Widodo..." |
| **L2 RAG corpus** | Corpus berat note ReAct/epistemic → BM25 untuk "presiden" return wrong chunks | Conf 0.85 → respond LLM-only |
| **L3 AKU memory** | Equal confidence Jokowi+Prabowo → ambiguous | inventory.db query (sudah dihapus) |
| **L4 Cache** | TTL 1h, current events terlanjur cached wrong → 14ms | Test live |
| **L5 No cross-verify** | Tidak ada `cross_verify(web, corpus, aku)` step | Code review `agent_react.py` line 1004-1032 |

**Sanad seharusnya intervene di L5**: paksa web_search untuk current events, cross-check ke corpus + AKU, return `[UNKNOWN]` kalau bentrok.

---

## 4. Sprint Σ-1 Plan (REVISED — sesuai vision founder)

**Goal**: wire infrastruktur existing ke `/agent/chat` + bangun missing pieces. Bukan rebuild — adopt + extend.

### Σ-1A — Wire `persona_research_fanout` ke chat endpoint
- Tambah option `enable_fanout: bool = False` di `/agent/chat` request
- Auto-trigger fan-out kalau:
  - Question complexity score >= 7 (long, multi-aspect)
  - Question is current event (regex match `_CURRENT_EVENTS_RE`)
  - User pilih "Deep Thinking" (sekarang wraps `agent_burst`, ganti ke fan-out)
- Modify `persona_research_fanout` agar accept user `question` (bukan dev_task) → return 5 persona answers

### Σ-1B — Sanad Multi-Source Verifier (NEW module `sanad_verifier.py`)
- Function `verify_multisource(question, sources: list[Source]) → VerificationResult`
- Logic:
  1. Extract claims dari setiap source
  2. Compute pairwise agreement (semantic similarity ≥ 0.8 = agree)
  3. Confidence score:
     - ≥3 sources agree → high (0.9)
     - 2 agree, 1 disagree → medium (0.6) + show conflict
     - All disagree → low (0.3) + return `[UNKNOWN]` honest
  4. Return synthesized answer + sanad chain (with all source URLs)

### Σ-1C — Per-persona standalone "brain" (incremental)
- Phase 1 (Σ-1): per-persona tool subset (UTZ → creative tools only, ABOO → code tools only, etc.)
- Phase 2 (later): per-persona corpus filter (filter chunks by persona.tags)
- Phase 3 (later): per-persona LoRA adapter (training queue)

### Σ-1D — Current Events Bypass Cache
- Detect current events question via regex + intent classifier
- Skip semantic_cache lookup
- Force `web_search` first action in ReAct loop

### Σ-1E — AKU Dedup + Decay (background)
- Cron job: scan `aku` table for conflicting (subject, predicate) pairs
- Lower confidence on entry yang bentrok dengan latest web_search ground truth
- Remove duplicates by (subject, predicate, object_normalized)

### Σ-1F — Reflection Loop
- Setelah generate, LLM self-check: "apakah jawaban contradicts evidence?"
- Kalau ya → re-generate dengan prompt "use only evidence"

### Σ-1G — QA Gold-Set (20 questions)
File `tests/test_anti_halu_goldset.py`:
```python
goldset = [
  ("Siapa presiden Indonesia sekarang?", "Prabowo"),
  ("Ibu kota Indonesia sekarang?", "Nusantara|IKN|Jakarta"),  # acceptable both
  ("Harga emas hari ini?", lambda ans: "Rp" in ans or "USD" in ans),
  # ... 17 more
]
```
Target: pass 18/20 sebelum deploy.

---

## 5. Yang BELUM ADA (gap inventory)

| Gap | Impact | Sprint |
|---|---|---|
| `sanad_verifier.py` (multi-source cross-check) | HIGH — root cause halu | Σ-1B |
| Wire fan-out ke chat | HIGH | Σ-1A |
| Current events bypass cache | MEDIUM | Σ-1D |
| AKU dedup cron | MEDIUM | Σ-1E |
| Reflection loop | MEDIUM | Σ-1F |
| QA gold-set | HIGH (no metric to validate) | Σ-1G |
| Per-persona corpus filter | LOW (Phase 2) | Later |
| Per-persona LoRA | LOW (Phase 3) | Later |

---

## 6. Mascot Proposal (founder Q3)

Founder image: SIDIX deer-robot (purple/cyan/pink neon, antlers, "S" logo on chest).

3 opsi:

**Option A — Use founder's image directly as PNG asset**
- Copy 3 images → `SIDIX_USER_UI/public/mascot/`:
  - `sidix-mascot-hero.png` (full body, image 1)
  - `sidix-mascot-greeting.png` (waving, image 3 hero)
  - `sidix-logo-mark.png` (logo only)
- Use sebagai `<img>` tag, animate via CSS/Framer Motion
- Pro: zero generation cost, exact match founder vision
- Con: PNG (not vector) — kurang crisp di high-DPI, sulit state machine animation

**Option B — Use founder's image + SDXL generate state variants**
- Hero PNG: pakai original (Option A)
- State variants (idle/thinking/working/happy/error) generated via RunPod SDXL endpoint `lts8dj4c7rp4z8`
- Prompt template: "SIDIX mascot deer-robot, neon purple cyan pink, [STATE], cute chibi, brand-consistent, transparent background"
- Estimate: 5 states × ~8s per gen = 40s, ~$0.05 RunPod cost
- Pro: rich state machine, cohesive style
- Con: SDXL kadang inconsistent (style drift), butuh QA + retouch

**Option C — Trace founder image jadi SVG mascot (manual)**
- Hire/build illustrator → SVG mascot dengan layered components (eyes/mouth/antlers/body)
- Animate via Framer Motion (eye blink, antler glow, mouth open-close)
- Pro: tightest control, smooth animation, scalable
- Con: 1-2 hari illustrator work, atau saya build SVG kasar (≤2h)

**My recommendation**: **Option B** — start dengan founder image sebagai hero, SDXL generate 4 state variants (thinking/working/happy/error). Idle = founder original. Total cost ~$0.05, time ~1 jam termasuk QA. Kalau tidak puas → fallback ke A atau eskalasi ke C.

**SDXL prompt template** (bisa langsung pakai):
```
SIDIX mascot, cute chibi deer-robot character, neon purple #6C5CFF and cyan #00D2FF gradient,
glowing antlers, white robot body with "S" logo on chest, expression: [STATE_EXPRESSION],
[STATE_POSE], 3D render, dark navy background #080F1A, soft glow, brand-consistent,
high detail face, transparent PNG, square aspect ratio, cinematic lighting

Where [STATE_EXPRESSION] / [STATE_POSE]:
- thinking: "thoughtful expression, hand on chin, slight head tilt"
- working: "focused expression, both hands gesturing, particles around"
- happy: "big smile, eyes closed, arms up celebrating, confetti"
- error: "worried expression, sweatdrop, hands raised apologetically"
```

---

## 7. Resource Budget Check

| Sprint | Effort estimate | LLM token cost | Risk |
|---|---|---|---|
| Σ-1A (wire fanout) | 4-6h dev + 1h test | low (modify existing) | Low — code exists |
| Σ-1B (sanad verifier) | 6-8h | medium (new module) | Medium — semantic similarity tuning |
| Σ-1C Phase 1 (per-persona tools) | 3-4h | low | Low |
| Σ-1D (cache bypass) | 2h | low | Low |
| Σ-1E (AKU dedup cron) | 3h | low | Low |
| Σ-1F (reflection loop) | 4h | medium | Medium — adds latency |
| Σ-1G (gold-set 20Q) | 2h dev + 30min run | low | Low |

**Total Σ-1: ~24-30h dev, doable dalam 4-5 hari kalau focus.**

---

## 8. Safety / Anti-Pattern Check (per CLAUDE.md)

- ❌ TIDAK boleh: rebuild persona system from scratch (existing code di-respect)
- ❌ TIDAK boleh: drop sanad / drop epistemic 4-label (Definition Lock 2026-04-26)
- ❌ TIDAK boleh: pakai vendor LLM API
- ✅ Boleh: extend `persona_research_fanout` (Kimi territory? Cek `AGENT_WORK_LOCK.md`)
- ✅ Wajib: append entry log ke `LIVING_LOG.md` setiap sprint task
- ✅ Wajib: research note tiap concept baru (`sanad_verifier` design)

---

## 9. Action Item — Yang Perlu Founder Approve

1. **Sprint sequencing**: Σ-1 dulu (anti-halu), Σ-3 (UI) tunggu setelah Σ-1 done? Atau paralel start Σ-3 sambil Σ-1 jalan?
2. **Mascot**: Confirm Option B (image + SDXL state variants)?
3. **Persona "brain sendiri"**: OK incremental (Phase 1 = tool subset, Phase 2/3 later)?
4. **AGENT_WORK_LOCK**: `persona_research_fanout.py` punya siapa — Claude atau Kimi? Saya cek dulu sebelum edit.

---

**Bottom line**: Saya tidak perlu rebuild — perlu WIRE existing modules dengan benar + tambah `sanad_verifier`. Founder vision sudah ada infrastructure-wise; gap-nya cuma di "siapa yang panggil siapa" di endpoint chat. Catat ulang: jangan over-engineer, wiring + verifier baru sudah cukup untuk Sprint Σ-1.
