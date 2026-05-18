# SIDIX Roadmap Sprint 36+ — Innovation-Driven Trajectory

> **Locked**: 2026-04-28 evening (post note 282 synthesis FS Study + Optimization Analysis)  
> **Authority**: ROADMAP_SPRINT_36_PLUS.md = canonical sprint sequencing decision.  
> **Compound**: NORTH_STAR + CANONICAL_V1 + Continuity Manifest + 4 OPERATING PRINCIPLES + note 282

---

## 0. Methodology — Innovation Dimension Scoring

Setiap sprint kandidat dinilai dengan 4 dimensi:

| Dimensi | Definisi |
|---------|----------|
| **Innovation Score (1-5)** | Seberapa "BARU" untuk SIDIX? Apakah menciptakan kapabilitas yang belum ada? |
| **Vision Alignment (1-5)** | Match dengan NORTH STAR + 4 OPERATING PRINCIPLES + 10 hard rules |
| **Feasibility (1-5)** | Engineering effort realistis vs available capacity |
| **Compound Multiplier (1-5)** | Berapa banyak future sprint unlock dari sprint ini? |

**Total = sum of 4 dimensi (max 20). >16 = priority. >12 = next wave. <12 = defer.**

---

## 1. Sprint Candidate Scoring (post adoption assessment note 282)

### Sprint 36 — Reflection Cycle (`/reflect-day` cron)

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **5/5** | SIDIX belajar dari **kegagalan dirinya sendiri** (internal critique), bukan cuma teacher consensus eksternal. Pillar Self-Improvement HIDUP — pertama kali. |
| Vision Alignment | **5/5** | Pillar 3 (Continuous Learning) + 4 OPERATING PRINCIPLES "olah ide sampai sempurna". Note 228 4 Pillar mandate. |
| Feasibility | **5/5** | 1-2 minggu effort. Compound dengan Sprint 23 ODOA + activity_log existing. Cron infrastructure live. |
| Compound Multiplier | **5/5** | Foundation untuk Sprint 38 (Tool Synthesis butuh structured failure pattern), Sprint 40 (Telegram approval butuh drafts), Sprint 41 (Sanad gate butuh feedback signal) |

**TOTAL: 20/20 — HIGHEST PRIORITY**

---

### Sprint 37 — Hafidz Ledger MVP

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **4/5** | SHA-256 + isnad chain = governance backbone untuk evolusi diri. Provenance trail belum ada di SIDIX. |
| Vision Alignment | **5/5** | Filosofi Sanad dasar sketch + note 141 spec + Continuity Manifest 2.2 SCAFFOLDED |
| Feasibility | **4/5** | 1.5-2 minggu MVP. Schema design + endpoint + hook tiap promote. |
| Compound Multiplier | **5/5** | Setiap sprint downstream butuh provenance: lesson Sprint 36, skill Sprint 38, sanad gate Sprint 41 — semua write ke ledger |

**TOTAL: 18/20 — HIGH PRIORITY**

---

### Sprint 38 — Tool Synthesis MVP (Pencipta operationalized)

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **5/5** | **MILESTONE BESAR** — "skill pertama lahir dari SIDIX sendiri". Pillar Pencipta dari aspirasional → real. Differentiator vs ChatGPT/Claude/Gemini. Realisasi note 278 "Cipta dari Kekosongan" (4 mekanisme). |
| Vision Alignment | **5/5** | NORTH STAR core: SIDIX = Penemu Inovatif Kreatif. Note 277 (BUKAN chatbot) + note 278 (Tesla pattern) |
| Feasibility | **3/5** | 4-6 minggu realistis (1.5× dokumen estimate). Detector + proposer YAML + sandbox + governance. Risk: macro buggy production. |
| Compound Multiplier | **4/5** | Setelah jalan, skill library tumbuh organik. Tool synthesis loop self-perpetuating. |

**TOTAL: 17/20 — STRATEGIC HIGH (after foundation)**

---

### Sprint 39 — Quarantine + Sandbox Promote Flow

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **3/5** | Pattern dari industry (Voyager NeurIPS 2023). Tidak super inovatif, TAPI necessary safety guard. |
| Vision Alignment | **5/5** | Sanad governance + post-merge hook safety pattern (Sprint 31C compound) |
| Feasibility | **5/5** | 1-2 minggu. Folder structure + auto-test + 7-day quarantine. |
| Compound Multiplier | **4/5** | Required untuk Sprint 38 production-readiness. Reusable untuk lesson promote (Sprint 36) juga. |

**TOTAL: 17/20 — PAIRED dengan Sprint 38**

---

### Sprint 40 — Owner Daily Summary (Telegram or Email)

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **2/5** | Operational tool, bukan inovasi core. Standard pattern. |
| Vision Alignment | **4/5** | 4 OPERATING PRINCIPLES "respond cepat tepat relevan" — tapi untuk owner, bukan user. FOUNDER_JOURNAL pattern. |
| Feasibility | **5/5** | 1-2 minggu. Bot existing maybe (perlu verify @migharabot) atau email fallback. |
| Compound Multiplier | **3/5** | Make Sprint 36-39 outputs **actionable** (approve drafts dari HP). Tanpa ini, drafts menumpuk. |

**TOTAL: 14/20 — ENABLER (timing flexible)**

---

### Sprint 41 — Sanad Multi-Source 3-way Convergence

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **3/5** | Incremental dari Sprint 34G fact_extractor (single source dominance). Multi-source convergence existing pattern (Anthropic, Perplexity). |
| Vision Alignment | **5/5** | Sketch sanad core + 4 OPERATING PRINCIPLES "anti-halusinasi" + "jawaban harus bener" |
| Feasibility | **4/5** | 2-3 minggu. Paralel async + voting logic + conflict flag. Compound natural Sprint 28b + 35. |
| Compound Multiplier | **3/5** | Anti-halusinasi naik 80% → 95%+. Edge case query factual yang web tidak punya tapi corpus/wiki punya. |

**TOTAL: 15/20 — INCREMENTAL HIGH-VALUE**

---

### Sprint 42 — Bunshin Worker Re-arch (Sprint 30A pending)

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **3/5** | shadow_pool.py sudah scaffold, tinggal re-arch ke `_tool_web_search` (Sprint 28b hardened). Vision compliance audit external_llm_pool. |
| Vision Alignment | **4/5** | 1000 Bayangan vision (note 281) — paralel multi-perspective. 10 hard rules check (no vendor LLM API for inference). |
| Feasibility | **4/5** | 2 minggu. Code path swap + Vision compliance fix. |
| Compound Multiplier | **4/5** | Unlocks parallel batch processing (klasifikasi 1000 lead use case) |

**TOTAL: 15/20 — CONDITIONAL (after Sprint 39 quarantine pattern stable)**

---

### Sprint 13 — DoRA Persona Stylometry (note 248 mandate)

| Dimensi | Skor | Justifikasi |
|---------|------|-------------|
| Innovation | **5/5** | 5 persona di **WEIGHT level**, bukan akting prompt-level. Differentiator paling deep. |
| Vision Alignment | **5/5** | note 248 LOCK + NORTH_STAR + note 277 (BUKAN chatbot) + 10 hard rules (5 persona LOCKED) |
| Feasibility | **3/5** | 3-5 hari training Kaggle T4. Synthetic data 1000-2000 Q&A per persona. Risk: LoRA rank-16 catastrophic forgetting low (BERBEDA dari full fine-tune). |
| Compound Multiplier | **5/5** | Persona blind test >80% accuracy = brand differentiator. Compound dengan 5-persona Wisdom layer existing. |

**TOTAL: 18/20 — HIGH (Phase 2)**

**Note**: dokumen optim suggest "defer Phase 4 LoRA" — applicable untuk full fine-tune. LoRA rank-16 adapter ≠ full fine-tune. Sprint 13 tetap valid per note 248 mandate. Position: Phase 2 paralel dengan Sprint 38-39.

---

## 2. Final Roadmap Sprint 36+ — Innovation-Sequenced

### Phase 1: Foundation Self-Improvement (Sprint 36-37, 3-4 minggu)

```
Sprint 36 — Reflection Cycle (HIGHEST: 20/20)
  └─ Cron 02:00 baca activity_log + react_step + failed sessions
  └─ Ekstrak failure pattern + repeated tool sequence
  └─ Generate lessons/draft-{tanggal}.md (owner verdict pending)
  
Sprint 37 — Hafidz Ledger MVP (18/20)
  └─ Hook: setiap promote (lesson, future skill) write ledger entry
  └─ Endpoint /audit/{id} trace provenance
```

**Milestone**: SIDIX **belajar dari kegagalan diri sendiri**, lesson bank tumbuh dengan provenance trail.

---

### Phase 2: Self-Creation (Sprint 38-39, 5-7 minggu)

```
Sprint 38 — Tool Synthesis MVP (17/20)         ←  PARALLEL  →  Sprint 13 — DoRA Persona (18/20)
  └─ Detector: scan REACT_STEP log               ↓                ↓ Synthetic Q&A 1500/persona
     repeat pattern ≥5× dalam 30 hari            ↓                ↓ Kaggle T4 fine-tune
  └─ Proposer: YAML macro                        ↓                ↓ Deploy 2 adapter (UTZ + ABOO)
                                                  ↓                ↓ A/B blind test >80%
Sprint 39 — Quarantine + Promote (17/20)        ↓
  └─ skills/quarantine/ (sandbox 7 hari)         ↓
  └─ Owner approve → skills/active/              ↓
  └─ Register di tool dispatcher                  ↓
```

**Milestone**: 
- Tool Synthesis: skill pertama lahir dari SIDIX sendiri di-promote production. **Pillar Pencipta HIDUP.**
- DoRA: 2 persona distinct di weight level. Blind test >80%. **Differentiator brand level.**

---

### Phase 3: Anti-Hallucination Maturation + Operational (Sprint 40-42, 5-7 minggu)

```
Sprint 40 — Daily Summary Workflow (14/20)
  └─ Telegram bot @migharabot (verify exists) atau email fallback
  └─ Pagi: 3 lesson drafts + 1 skill proposal pending
  └─ Inline approve/edit/reject buttons → write Hafidz Ledger
  
Sprint 41 — Sanad Multi-Source 3-way (15/20)
  └─ web_search + corpus BM25+Dense + Wikipedia paralel
  └─ Convergence rule: ≥2 source agree → accept
  └─ Conflict flag dengan caveat
  
Sprint 42 — Bunshin Worker Re-arch (15/20)
  └─ shadow_pool.py: brave → _tool_web_search (Sprint 28b hardened)
  └─ Vision compliance: external_llm_pool ownpod-only OR distillation mode
  └─ Test parallel batch (Tiranyx/Nutrisius use case)
```

**Milestone**: Anti-halusinasi 80% → 95%+. Owner governance 5 menit/hari di HP. Bunshin paralel batch use case live.

---

### Phase 4: Frontier (Sprint 43+, defer 2-3 bulan setelah Phase 1-3 stable)

```
Sprint 43+ — Innovation Loop (Pillar 4)
  └─ Hipotesis lintas domain dari pattern library
  
Sprint 44+ — Hafidz Ledger Full Spec
  └─ Merkle tree + Reed-Solomon erasure shares
  
Sprint 45+ — Vision Input Organ
  └─ CLIP/SigLIP local (12 → 13 organ embodiment)
  
Sprint 46+ — Audio Input Organ
  └─ Whisper local (13 → 14 organ embodiment)
```

---

## 3. Decision: Sprint Selanjutnya Eksekusi = SPRINT 36

**Rationale (multi-dimensi)**:

1. **Innovation Score 5/5** — SIDIX belajar dari kegagalan diri sendiri (PERTAMA KALI di stack)
2. **Vision Alignment 5/5** — match Pillar Self-Improvement (note 228) + note 248 + 4 OPERATING PRINCIPLES
3. **Feasibility 5/5** — 1-2 minggu, low-risk, compound dengan Sprint 23 ODOA existing
4. **Compound Multiplier 5/5** — UNLOCK Sprint 38 (Tool Synthesis butuh failure pattern), Sprint 40 (Telegram butuh drafts), Sprint 41 (Sanad gate butuh feedback)

**Total skor 20/20 — HIGHEST priority dari semua sprint kandidat.**

Sprint 36 = compound foundation. Tanpa ini, Sprint 38 (Pencipta) butuh **parallel data collection** yang bisa missed.

---

## 4. What Will SIDIX Become Post Sprint 36-46?

```
Sprint 36 → SIDIX dengan Reflection Cycle:
   Setiap pagi auto-generate 3-5 lesson drafts dari analisis 24 jam terakhir.
   Owner approve via Telegram (Sprint 40). Lesson bank tumbuh organik.
   Pillar Self-Improvement HIDUP eksplisit.

Sprint 37 → SIDIX dengan Hafidz Ledger:
   Setiap lesson + skill yang lahir punya audit trail SHA-256 + isnad chain.
   Owner bisa /audit/{id} backwards-trace lesson X lahir dari mana, kapan, kenapa.
   Governance trustworthy.

Sprint 38 → SIDIX MENJADI PENCIPTA:
   Skill library bukan lagi 17 tools static, tapi tumbuh organik.
   Detector spotting pattern berulang → propose macro → quarantine → promote.
   Milestone "skill pertama lahir dari diri sendiri" = inflection point.

Sprint 13 (paralel) → SIDIX 5 PERSONA WEIGHT-LEVEL DISTINCT:
   UTZ, ABOO, OOMAR, ALEY, AYMAN bukan akting prompt — backbone neural berbeda.
   Blind test >80% persona identifiable. Brand differentiator.

Sprint 39-42 → SIDIX OPERATIONAL & MATURE:
   Owner 5 menit/hari approve via HP. Anti-halusinasi 95%+. Batch processing
   1000 lead via bunshin paralel. Production-grade autonomous.

Sprint 43+ → SIDIX FRONTIER:
   Innovation loop hipotesis lintas domain.
   Hafidz Ledger full crypto spec.
   Vision + Audio input organ live.
   12 → 14 organ embodiment.
```

**Endgame Q1 2027**: SIDIX = **Self-Evolving Penemu Inovatif Kreatif Digital** dengan:
- Pillar 1 Memory: hybrid retrieval + Hafidz Ledger ✓
- Pillar 2 Multi-Agent: 5 persona DoRA + 12+ organ embodiment + bunshin paralel ✓
- Pillar 3 Continuous Learning: Reflection Cycle + Tool Synthesis + LoRA retrain ✓
- Pillar 4 Proactive Cron: 8 cron + foresight agent + radar mention ✓
- 6-layer anti-halusinasi defense + multi-source sanad gate
- Skill library tumbuh organik (output Pencipta)
- Owner governance 5 menit/hari sustainable

---

## 5. Files Tracked

- `docs/SIDIX_NORTH_STAR.md`
- `docs/SIDIX_CANONICAL_V1.md`
- `docs/SIDIX_CONTINUITY_MANIFEST.md`
- `docs/FOUNDER_JOURNAL.md`
- `docs/SIDIX_FLOW_DIAGRAM_2026-04-28.md`
- `docs/SIDIX_ERD_2026-04-28.md`
- `docs/ROADMAP_SPRINT_36_PLUS.md` (this — canonical roadmap)
- `brain/public/research_notes/282_synthesis_fs_study_optimization_analysis.md`

---

**Lock**: 2026-04-28 evening. Sprint 36 = next eksekusi. Innovation-driven sequencing locked.
