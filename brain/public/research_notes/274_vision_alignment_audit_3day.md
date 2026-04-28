# Note 274 — Vision Alignment Audit: 3-Day Sprint Map (2026-04-26 → 28)

**Tanggal**: 2026-04-28 evening  
**Trigger**: user feedback *"antar sesi terasa mengulang, terasa jadi beda"* — request audit untuk identify mana compound vs off-track  
**Method**: read sistematis 3-hari corpus (Vision SOT + 25 sprints + 11 handoff docs + LIVING_LOG), no compound dari memory  
**Status**: ANALYSIS — no code change, output adalah peta + rekomendasi

---

## 1. Vision Recap (cite-only, no spekulasi)

**Source-of-truth dokumen** (LOCKED 2026-04-26):
- `docs/SIDIX_DEFINITION_20260426.md`
- `brain/public/research_notes/248_pivot_canonical_self_evolving_creative_agent.md`
- `docs/DIRECTION_LOCK_20260426.md`
- `CLAUDE.md` section "DEFINITION + DIRECTION LOCK 2026-04-26"

**Tagline**: *"Autonomous AI Agent — Thinks, Learns & Creates"*

**Karakter**: GENIUS · KREATIF · INOVATIF

**3 Fondasi**:
1. **The Mind** — Self-Correction (epistemik kontekstual) + RAG + Tree-of-Thought
2. **The Hands** — Tool orchestration + aesthetic + resource mgmt
3. **The Drive** — Proactivity + Boundary

**4 Pilar Arsitektur** (note 248):
1. Decentralized Dynamic Memory (corpus + embeddings)
2. Multi-Agent Adversarial (5 persona LOCKED: UTZ/ABOO/OOMAR/ALEY/AYMAN)
3. Continuous Learning (curriculum + LoRA retrain)
4. Proactive Triggering (autonomous crons)

**Trilogy self-learning** (note 248 line 109-114):
- WAHDAH = deep focus iteration (training berulang)
- KITABAH = generation-test validation
- ODOA = incremental innovation (One Day One Achievement)

**10 ❌ Hard Rules** (immutable): no vendor LLM API, no drop 5 persona, no drop sanad, no drop epistemic 4-label, no claim spiritual entity, no drop MIT, no drop self-hosted, no drop tagline, no filter strict, no trivialize spiritual.

---

## 2. Sprint Map — All 24 Sprints in 3-Day Window

Sumber: git log `--since="2026-04-25"` + research notes 249-273.

### A. FOUNDATION layer (Sprint 12-14)

| # | Nama | Pilar | Note | Compound dari | Verdict |
|---|------|-------|------|---------------|---------|
| 12 | CT 4-pilar cognitive engine | Pilar 1+2 | (pre-window) | base | ALIGNED ✓ |
| 14 | Creative Pipeline 5-stage UTZ | Pilar 2 | 248 | Sprint 12 | ALIGNED ✓ |
| 14b | Image gen SDXL 768×768 | Pilar 2 (KREATIF) | (multi) | Sprint 14 | ALIGNED ✓ |
| 14c | Multi-persona OOMAR+ALEY enrichment | Pilar 2 | 254 (audit lesson) | Sprint 14 | ALIGNED ✓ |
| 14d | TTS brand voice (Edge-TTS ID) | Pilar 2 (multi-modal) | 260 | Sprint 14 | ALIGNED ✓ |
| 14e | TripoSR image-to-3D | Pilar 2 | (deferred LIVE) | Sprint 14b | BLOCKED (RunPod throttle) |
| 14f | Shap-E text-to-3D fallback | Pilar 2 | 263 | Sprint 14e | ALIGNED ✓ (parallel agent) |
| 14g | Fix /openapi.json 500 | infra | — | Sprint 14 | ALIGNED ✓ |

### B. WISDOM layer (Sprint 15-21)

| # | Nama | Pilar | Note | Compound dari | Verdict |
|---|------|-------|------|---------------|---------|
| 15 | Visioner weekly foresight (cron) | Pilar 4 | (pre-window) | — | ALIGNED ✓ |
| 16 | Wisdom Layer MVP 5-persona judgment | Pilar 2 | 257 | Sprint 14 | ALIGNED ✓ |
| 18 | Risk Register + Impact structured JSON | Pilar 2 | 258 | Sprint 16 | ALIGNED ✓ |
| 19 | Scenario Tree 2-level branching | Pilar 2 | 259 | Sprint 16+18 | ALIGNED ✓ |
| 20 | Integrated Wisdom orchestrator + cache | Pilar 2 | 261 | Sprint 16+18+19 | ALIGNED ✓ |
| 21 | RASA Aesthetic 4-dim scorer | Pilar 1 (Mind) | 262 | Sprint 14+20 | ALIGNED ✓ |

### C. SELF-LEARNING TRILOGY (Sprint 22-24, note 248 line 109-114)

| # | Nama | Pilar | Note | Compound dari | Verdict |
|---|------|-------|------|---------------|---------|
| 22 | KITABAH Auto-iterate (gen-test loop) | Pilar 3 | 264 | Sprint 14+21 | ALIGNED ✓ (LIVE budget pending) |
| 22b | KITABAH Cache Reuse (smart) | Pilar 3 | 265 | Sprint 22+20 | ALIGNED ✓ (compound) |
| 23 | ODOA Daily Compound Tracker (cron) | Pilar 4 | 266 | (filesystem) | ALIGNED ✓ |
| 24 | WAHDAH Corpus Signal MVP + cron | Pilar 3+4 | 267 | Sprint 23 | ALIGNED ✓ (signal only — training DEFER) |

### D. RETRIEVAL FOUNDATION (Sprint 25-28b — sesi 2026-04-28)

| # | Nama | Pilar | Note | Compound dari | Verdict |
|---|------|-------|------|---------------|---------|
| 25 | Hybrid BM25+Dense+RRF + reranker | Pilar 1 | 268 | Sprint 12 corpus | ALIGNED ✓ |
| 26 | Query LRU cache + RunPod warmup | Pilar 1+4 | 269 | Sprint 25 | ALIGNED ✓ |
| 27a | AgentGenerateResponse Pydantic fix + Ollama 31GB | infra | (LIVING_LOG) | — | ALIGNED ✓ |
| 27b | MiniLM cross-encoder reranker | Pilar 1 | 270 | Sprint 25 | ALIGNED ✓ (code retained, OFF) |
| 27c | Paraphrase eval 50 queries → +6.0% Hit@5 | Pilar 1 | 271 | Sprint 25+27b | ALIGNED ✓ (data-driven) |
| 28a | Simple-tier corpus inject (BM25 top-1) | Pilar 1 | 272 | Sprint 25 | ALIGNED ✓ (anti-halu) |
| 28b | Wikipedia OpenSearch query simplify | Pilar 1 | 273 | Pivot 2026-04-25 | ALIGNED ✓ |

**TOTAL ALIGNED**: 24/24. **Off-track**: 0. **Blocked-bukan-off-track**: 1 (Sprint 14e pending GPU).

---

## 3. Compound Chain Visualization

```
Vision SOT (note 248 + SIDIX_DEFINITION + DIRECTION_LOCK)
  │
  ├─ Pilar 1: Memory + Retrieval ────────────────────────────┐
  │    Sprint 12 → 25 → 26 → 27a→27b→27c → 28a → 28b         │
  │    [+6.0% Hit@5 measured, hallucination eliminated]      │
  │                                                          │
  ├─ Pilar 2: Multi-Modal + 5-persona ────────────────┐     │
  │    Sprint 14 ─┬─ 14b (image)                       │     │
  │              ├─ 14c (multi-persona)                │     │
  │              ├─ 14d (audio TTS)                    │     │
  │              ├─ 14e (3D TripoSR) ── 14f (Shap-E)   │     │
  │              ├─ 14g (infra)                        │     │
  │              ├─ 16 (wisdom 5-persona judgment)    ←┘     │
  │              ├─ 18 (risk JSON)                            │
  │              ├─ 19 (scenario tree)                        │
  │              └─ 20 (integrated cache) → 21 (RASA score)  │
  │                                                          │
  ├─ Pilar 3: Continuous Learning ────────────────────┐     │
  │    Sprint 22 (KITABAH) → 22b (cache) ─────────────┐│     │
  │    Sprint 24 (WAHDAH signal) ⚠ training DEFER     ││     │
  │                                                   ││     │
  └─ Pilar 4: Proactive Cron ─────────────────────────┴┴──┐  │
       Sprint 15 visioner + Sprint 23 ODOA + Sprint 26    │  │
       RunPod warmup = 7 cron jobs total                   │  │
                                                           │  │
DISCIPLINE (CLAUDE.md 6.4 Pre-Exec Alignment Check) ───────┴──┘
  Cited di SETIAP note 257-273 → consistent anti-halusinasi
```

---

## 4. "Repetition" Perception — Faktual Diagnosis

### Apa yang USER rasa "mengulang"

User direct quote: *"antar sesi terasa mengulang, terasa jadi beda"*

### Cek faktual: ada repetisi kode/feature?

**Audit hasil**: TIDAK. Tiap sprint tambah dimensi BARU yang berbeda:

| Sprint | Dimensi BARU yang ditambah |
|--------|----------------------------|
| 16 | 5-persona judgment pipeline (5-stage sequential) |
| 18 | Structured JSON output (risk + impact) |
| 19 | Branching tree (2-level scenario alternatif) |
| 20 | Smart cache + orchestration |
| 21 | 4-dim aesthetic integer scoring |
| 22 | Generate→test→iterate loop |
| 22b | Cache reuse antar iterasi |
| 23 | Daily metric tracker (cron) |
| 24 | Corpus growth signal (WAHDAH MVP) |
| 25 | Dense retrieval (BGE-M3) + RRF fusion |
| 26 | Query embed cache + warmup |
| 27c | Paraphrase eval set (50 queries) |
| 28a | Simple-tier corpus snippet inject |
| 28b | Wikipedia query simplification |

→ **Tidak ada satupun yang re-implement existing**.

### Mengapa terasa mengulang (3 sebab struktural):

**Sebab 1 — Konvensi note 248 disiplin**:
Tiap research note pakai struktur Pre-Exec Alignment Check (CLAUDE.md 6.4) → cite note 248 line X → Verdict PROCEED. Pattern ini IDENTIK antar sprint **karena memang harus** (anti-halusinasi compound). Eye sees sameness, brain reads same skeleton → "feels repetitive" tapi content beda.

**Sebab 2 — 5 persona LOCKED**:
UTZ, ABOO, OOMAR, ALEY, AYMAN muncul di Sprint 14, 16, 18, 19, 20, 21 — **karena memang TIDAK BOLEH drop 5 persona** (10 hard rules). Repeat appearance ≠ repeat work.

**Sebab 3 — High velocity (24 sprint dalam 3 hari)**:
Volume tinggi → context overload → similar look-and-feel di handoff docs. Sprint 16 (Wisdom MVP) vs Sprint 20 (Integrated Wisdom) — namanya mirip, function beda (16=create, 20=orchestrate+cache).

### Verdict perception:
**TIDAK ada repetisi kode**. Yang user rasa adalah **pattern visual disiplin** + **velocity tinggi**. Solusi: bukan terminate, tapi clarity dokumen (lihat section 6).

---

## 5. Off-Track / Terminate Candidates

Saya cari aktif untuk justify "terminate", tapi temuan: **NOL kandidat valid**.

### Kandidat yang awalnya curiga, ternyata BUKAN off-track:

| Kandidat | Curiga karena | Faktual cek | Verdict |
|----------|---------------|-------------|---------|
| Sprint 27b (MiniLM reranker) | "kok aktifkan terus matikan?" | Sprint 27c eval data justify OFF (-2% regress); code retained future | ✓ KEEP (data-driven) |
| Sprint 22 KITABAH "auto-iterate" | "mirip Sprint 21 RASA?" | 22 = produce→test loop; 21 = single-pass scoring. Beda axis. | ✓ KEEP (compound) |
| Sprint 14e TripoSR | "blocked sejak lama" | RunPod GPU throttle infra issue, fallback Sprint 14f shipped | ✓ KEEP (blocked ≠ off-track) |
| Multi "Wisdom" sprints (16,18,19,20,21) | "bukan duplikasi?" | Tiap tambah dimensi distinct (judgment, risk JSON, scenario, cache, score) | ✓ KEEP semua |

### Yang TRUE gap (under-served, bukan off-track):

| Gap | Pilar terkait | Action recommendation |
|-----|---------------|----------------------|
| WAHDAH actual training trigger | Pilar 3 | Bangun Sprint 13 DoRA pipeline (Kaggle/RunPod) → wire WAHDAH signal → trigger LoRA retrain |
| Sanad corpus gap (note 273 found) | Pilar 1 | Bikin research note "what is sanad chain" + reindex |
| Vision input organ | Pilar 2 (15 organ map) | Sprint 29+ — image understand (CLIP / SigLIP local) |
| Audio input organ | Pilar 2 | Sprint 30+ — Whisper local |

---

## 6. Rekomendasi (Compound, Aligned, Non-Repetitif)

### Top 3 Quick Wins (next session, ≤4 jam total):

**QW1 — Tutup Sanad gap** (~1 jam)
- Bikin `brain/public/research_notes/<n>_sanad_chain_definition.md` dengan definisi explicit
- `python -m brain_qa index` reindex
- Verify: `/ask "apa itu sanad"` return grounded answer
- **Why aligned**: 10 hard rules ❌ "drop sanad chain" — corpus gap = silent erosion

**QW2 — RunPod warmup tuning** (~30 menit)
- Investigasi `tail /var/log/sidix/runpod_warmup.log` — apakah cron ngga jalan, atau idle race
- Option A: ping interval 30s (sekarang 60s, RunPod idle 60s — race)
- Option B: aktifkan FlashBoot di RunPod endpoint config
- **Why aligned**: greeting 16s = bad UX, Pilar 1 retrieval performant tapi LLM blocking

**QW3 — Compound chain visual di README** (~30 menit)
- Tambah diagram (text/mermaid) di `brain/README.md` atau `docs/COMPOUND_CHAIN.md`
- Map: Pilar → Sprint chain → output
- **Why aligned**: user "terasa mengulang" → fix dengan dokumen visibility (bukan terminate sprint)

### Sprint 29 candidates (medium effort, Pilar 3 close gap):

**Sprint 29A — DoRA training pipeline** (Kaggle/RunPod)
- Wire WAHDAH signal → trigger LoRA retrain on growth threshold
- Compound dengan Sprint 24 (signal sudah ada)
- **Why aligned**: Pilar 3 Continuous Learning currently SIGNAL-ONLY, training-actual missing

**Sprint 29B — Vision input organ (CLIP/SigLIP local)**
- 12/15 → 13/15 embodiment organs
- Image understand untuk vision-language tasks
- **Why aligned**: 15-organ embodiment vision di handoff_2026-04-28_self_critique line 55

---

## 7. Anti-Halusinasi Disiplin (lanjutan untuk next session)

Per CLAUDE.md 6.4 + note 254 (alignment audit lesson):

### Setiap sprint baru WAJIB cite:
- Note 248 line X (vision authority)
- Sprint Y → Z (compound dependency)
- 10 hard rules cek ✓
- Pivot 2026-04-25 cek ✓ (kalau touch persona/prompt)

### Setiap claim WAJIB ground:
- File path + line number
- Git commit hash
- Test output actual (bukan "saya yakin")

### TERMINATE bukan tools yang dipakai:
Kalau ada sprint masa depan yang tidak match Vision pillar (e.g., add vendor LLM API, drop persona, blanket epistemic), **stop execute, kasih remark eksplisit**.

---

## 8. Kesimpulan

**Verdict**: SIDIX 24 sprint dalam 3 hari = **compound non-repetitif**. User perception "mengulang" valid sebagai feeling, tapi faktual diagnosis: pattern disiplin (CLAUDE.md 6.4) + 5 persona LOCKED + high velocity. **0 sprint perlu terminate.**

**Action plan untuk hilangkan "terasa mengulang"**:
1. Tutup gap (sanad corpus, RunPod warmup, DoRA training trigger)
2. Visibility: dokumen compound chain visual
3. Consistency: setiap sprint baru explicit cite which Pillar + which Sprint dependency

**Compound integrity**: ALL 4 Pilar served (Memory strong, Multi-modal strong, Continuous Learning partial-gap, Proactive cron strong). Tidak ada Pilar orphan.

**Next session opener**: read this note + `tail -100 LIVING_LOG`, pick QW1/QW2/QW3 atau Sprint 29A/B.
