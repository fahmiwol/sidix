# Roadmap — Sprint 13 DoRA Persona Stylometry + Sprint Queue

**Locked**: 2026-04-29 (founder decision: "keputusan sulit di awal mempermudah kedepannya")  
**Decision context**: setelah Sprint 36-39 done, kandidat 13/40/41/42. Bos pilih Sprint 13 karena asymmetric leverage — compound dengan SEMUA sprint future.

---

## 1 · Sprint 13 — DoRA Persona Stylometry (CURRENT)

**Score**: 18/20 (Innovation 5, Vision 5, Feasibility 3, Compound 5)  
**Estimasi total**: 3-4 minggu (multi-session)

### Filosofi (note 248 mandate)

Sekarang 5 persona = **acting via prompt** (bisa di-replicate chatbot manapun dengan sistem prompt sama). Sprint 13 = 5 persona di **weight level via DoRA adapter** — voice yang **tidak bisa di-replicate** dengan prompt engineering.

Beda antara: "AI yang berperan jadi UTZ" vs "AI yang **adalah** UTZ secara neurologis".

### Phase decomposition (Polya 4-phase)

```
Phase 1 — UNDERSTAND (DONE 2026-04-29)
  └─ Pre-Exec Alignment Check (note 248 5 persona LOCKED ✓, 10 hard rules ✓)
  └─ Scan existing scaffold (synthetic_question_agent.py reusable, PERSONA_DESCRIPTIONS ada)
  └─ Architecture decision: Alpaca-style JSONL training format, DoRA rank-16

Phase 2 — PLAN (CURRENT — sesi 2026-04-29)
  └─ Roadmap doc (THIS FILE)
  └─ persona_qa_generator.py module — template-based seed + LLM amplify hybrid
  └─ CLI subcommand `gen_persona_qa`
  └─ Note 285 — architecture detail
  └─ Output schema lock

Phase 3 — EXECUTE (multi-session, ~3 minggu)
  └─ Stage 3a (Week 1-2): synthetic data pipeline LIVE
       ├─ Generate 1500 pair × 2 persona dulu (UTZ + ABOO) — proof of concept
       ├─ Quality gate: persona-distinctive marker validation
       ├─ Output: /opt/sidix/.data/training/persona_qa_{persona}.jsonl
  └─ Stage 3b (Week 3): Kaggle T4 LoRA rank-16 train
       ├─ Base: Qwen2.5-7B-Instruct
       ├─ Adapter: 1 per persona (UTZ.safetensors, ABOO.safetensors)
       ├─ Train hyperparam: lr 2e-4, 3 epoch, batch 4 gradient accum
       ├─ HF upload: Tiranyx/sidix-dora-{persona}
  └─ Stage 3c (Week 4): deploy + dispatch wiring
       ├─ Adapter loading di RunPod inference (multi-LoRA)
       ├─ Persona dispatch: persona request → load matching adapter
       ├─ Fallback: kalau adapter unavailable → base SIDIX LoRA

Phase 4 — REVIEW (post-deploy)
  └─ Blind A/B test: human reads output, guesses persona (target >80%)
  └─ Regression check: persona swap tidak break corpus answer accuracy
  └─ Iterate kalau gagal threshold (persona kurang distinctive → tambah data)
```

### Quality gates (HARD)

- **Phase 3a**: ≥1500 pair/persona, dedup hash < 5%, persona signature score ≥0.7
- **Phase 3b**: train loss converge, val loss < 1.2, no NaN/diverge
- **Phase 3c**: blind test accuracy ≥80% (else iterate Phase 3a dengan refined templates)
- **Regression**: corpus answer accuracy delta < 5% (DoRA tidak boleh hancurin generative ability)

### Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Catastrophic forgetting | LOW (LoRA rank-16, bukan full FT) | Validation set holdout, early stopping |
| Persona blur (UTZ ≈ AYMAN) | MEDIUM | Distinctive markers di prompt template, manual review 5% sample |
| Kaggle T4 quota habis | MEDIUM | Resume training dari checkpoint, alternative Colab Pro |
| Inference cost (5 adapter loaded) | LOW | Multi-LoRA via vLLM lora_modules, hot-swap |
| Synthetic data bias | HIGH | Mix template-based + LLM-paraphrased + edge cases; dedup ketat |

---

## 2 · Sprint Queue (post Sprint 13)

Recorded urutan eksekusi dengan justifikasi:

### Sprint 13b — DoRA Expand 3 personas (after Sprint 13 stable)
- **Score**: 16/20 estimated  
- **Scope**: OOMAR + ALEY + AYMAN adapters (extend dari 2 ke 5)  
- **Trigger**: Sprint 13 blind test ≥80% pada UTZ + ABOO  
- **Estimasi**: 1-2 minggu

### Sprint 39c — Macro Dispatch Wire (mini)
- **Score**: 14/20 (defer until Pencipta data accumulate)  
- **Scope**: wire `active/index.json` → `agent_react.py` tool dispatcher  
- **Trigger**: skill pertama lahir di production (react_steps.jsonl accumulate)  
- **Estimasi**: 2-3 hari  
- **Compound dengan Sprint 13**: dispatch bisa route by persona × topic × confidence (5x richer dengan DoRA aktif)

### Sprint 40 — Telegram Owner Daily Summary
- **Score**: 14/20 — ENABLER  
- **Scope**: Telegram bot untuk approve/reject lessons + skill proposals dari HP  
- **Trigger**: setelah ≥3 lessons + ≥1 skill proposal accumulated (real backlog)  
- **Estimasi**: 1-2 minggu  
- **Compound dengan Sprint 13**: notification bisa per-persona ("UTZ propose creative skill X — approve?")

### Sprint 41 — Sanad Multi-Source 3-way Convergence
- **Score**: 15/20 — INCREMENTAL HIGH-VALUE  
- **Scope**: web_search + corpus + wikipedia paralel async, ≥2 source agree → accept  
- **Trigger**: kapan saja standalone (no hard dep)  
- **Estimasi**: 2-3 minggu  
- **Compound dengan Sprint 13**: 5 persona × N source convergence = sintesis multi-dimensi (compound 5x)

### Sprint 42 — Bunshin Worker Re-arch
- **Score**: 15/20 — CONDITIONAL  
- **Scope**: shadow_pool.py: brave → `_tool_web_search` (Sprint 28b hardened), Vision compliance audit  
- **Trigger**: setelah Sprint 41 (sanad pattern stable, lebih natural fit)  
- **Estimasi**: 2 minggu

### Sprint 43+ — Phase 4 Frontier (defer 2-3 bulan)
- Innovation Loop (Pillar 4)  
- Hafidz Ledger Full Spec (Merkle + Reed-Solomon)  
- Vision Input Organ (CLIP/SigLIP local)  
- Audio Input Organ (Whisper local)

---

## 3 · Decision Log

### 2026-04-29 — Sprint 13 chosen

**Considered alternatives**:
- Sprint 39c (wire dispatch) — easy but low impact, defer until skill data accumulate
- Sprint 40 (Telegram) — operational, no innovation
- Sprint 41 (Sanad multi-source) — incremental quality, can do anytime
- Sprint 42 (Bunshin re-arch) — technical debt, no new capability

**Why Sprint 13 won**:
1. Score 18/20 (highest after Sprint 36 which is done)  
2. Innovation 5/5 — true differentiator, not incremental  
3. Compound 5/5 — every future sprint becomes 5x richer with weight-level personas  
4. Vision 5/5 — locks NORTH_STAR identity at weight level (anti-drift insurance)  
5. **Asymmetric reversibility**: delay cost grows quadratically — every new feature on top of prompt-level personas bakes in single-model + prompt-switching architecture  

**Founder verdict (verbatim)**: *"oke berarti ini! catat yang lainnya, buat roadmap, terus jangan lupa testing setelah sprint DoRA Persona Stylometry. Validasi -- iterasi -- Verfikasi -- optimasi --- testing validas --- catat!! jangan lupa push and deploy"*

---

## 4 · Mandatory Loop per Sub-phase

Setiap sub-phase Sprint 13 (3a, 3b, 3c) harus jalankan loop CLAUDE.md 6.5:

```
CATAT  →  TESTING  →  ITERASI  →  TRAINING (kalau touch model — ya untuk 3b)  →
REVIEW  →  CATAT  →  VALIDASI  →  QA  →  CATAT (final + push + deploy)
```

Tidak skip step. Tidak batch completions. Tidak lompat ke phase berikutnya tanpa selesaikan loop.
