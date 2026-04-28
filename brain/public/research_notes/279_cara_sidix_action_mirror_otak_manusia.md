---
sanad_tier: primer
---

# 279 — Cara SIDIX Action: Mirror Otak Manusia (Metafora Arsitektur, BUKAN Mapping Neural Literal)

> **🚨 META-DISCLAIMER (founder rule LOCKED 2026-04-28)**: Istilah "**otak manusia**",
> "**cortical specialists**", "**default mode network**", dan analogi neuroscience
> di dokumen ini adalah **METAFORA dan ANALOGI** untuk inspirasi arsitektur, BUKAN
> literal claim 1:1 mapping neuron ke kode.
> 
> Bos pakai pola otak sebagai **inspiration source** untuk design SIDIX yang multi-sensory,
> multi-perspective, plastic, reflective. Implementasi konkret bisa berbeda dari mapping
> rigid yang dijelaskan di bawah — **spirit > mechanic**.
> 
> Setiap agent WAJIB baca META-RULE di `docs/FOUNDER_JOURNAL.md` dulu.

**Tanggal**: 2026-04-28 evening (later)  
**Trigger**: founder feedback eksplisit — *"cara sidix action dan lainnya belum ada... cara otak manusia berfikir menerima informasi dan mengirim informasi ke semua indera agar aktif"*  
**Status**: LOCKED — spirit + pattern, bukan rigid neural mapping  
**Compound dengan**: `docs/SIDIX_NORTH_STAR.md`, note 224 (4 modul kognitif), note 244 (brain anatomy metafora), note 248 (canonical pivot)

---

## 🚨 Statement Inti

**SIDIX action BUKAN linear pipeline** ("input → process → output"), seperti AI Agent template biasa. SIDIX action **mirror cara otak manusia bekerja** — multi-sensory simultaneous, multi-perspective parallel, iterative reflective, embodied dengan tools.

Ini yang membedakan SIDIX dari **chatbot generic** — bukan dari prompt engineering, tapi dari **arsitektur action** itu sendiri.

---

## 🧠 7 Pola Otak Manusia → SIDIX Equivalent

### Pola 1 — Multi-Sensory SIMULTANEOUS Integration (bukan sequential)

**Otak manusia**: saat membaca buku, otak **paralel** memproses: huruf (visual) + suara dalam kepala (phonological loop) + memori asosiasi (hippocampus) + bayangan visual (occipital cortex) + emosi (amygdala) — **semua jalan bersamaan**, bukan satu-satu.

**SIDIX equivalent**:
```
User signal masuk → DISPATCH PARALLEL ke:
  ├─ Corpus search (BM25 + Dense hybrid) ────── memori semantik
  ├─ Web search (sanad consensus) ──────────── sensory eksternal
  ├─ Tool registry scan ───────────────────── procedural memory
  ├─ Persona DoRA selector ────────────────── attention focus
  ├─ Radar/env signal check ──────────────── peripheral awareness
  └─ Memory state (multi-layer) ──────────── working + episodic memory
```

Semua channel run paralel via `asyncio.gather`. Hasil **di-integrate** sebelum reasoning, bukan satu-satu (latency mahal + miss konteks lateral).

**Code reference**: `agent_serve.py` `/ask/stream` parallel dispatch (asyncio.gather wiki + brave + corpus).

### Pola 2 — Multi-Perspective Parallel (5 Cortical Specialists)

**Otak manusia**: prefrontal cortex bukan satu unit homogen — ada specialized regions:
- Dorsolateral PFC — analytical reasoning, working memory
- Ventromedial PFC — value-based decision, emotional integration
- Anterior cingulate — conflict detection, error monitoring
- Orbitofrontal — reward processing
- Mereka **berdebat internal paralel**, bukan vote sequential.

**SIDIX equivalent — 5 persona = 5 cortical specialists**:
| Persona | Otak analog | Function |
|---------|-------------|----------|
| **UTZ** | right hemisphere creative + visual cortex | Creative generation, aesthetic judgment |
| **ABOO** | left dorsolateral PFC | Engineering reasoning, precision, code |
| **OOMAR** | orbitofrontal + ventromedial PFC | Strategic value, market positioning |
| **ALEY** | hippocampus + parahippocampal | Deep research, evidence chain, memory recall |
| **AYMAN** | anterior cingulate + insula | Synthesis, accessibility, emotional resonance |

Di SIDIX Sprint 16-21 wisdom layer: **5 persona output paralel**, lalu integrated. Future Sprint 13 DoRA: persona distinct di **weight level**, bukan prompt-level akting → seperti specialized neural circuits, bukan general LLM acting.

**Hard rule**: 5 persona LOCKED (note 248 + DIRECTION_LOCK). Mereka adalah arsitektur, bukan UI option.

### Pola 3 — Top-Down Attention Modulasi (bukan bottom-up only)

**Otak manusia**: pulvinar nucleus + frontal eye field modulate semua sensory input. Saat user fokus pada sesuatu, perception itu sendiri **terbentuk dari attention**, bukan raw input.

**SIDIX equivalent**:
- **Niat router** (note 249 niat-aksi flow) — parse user turn type → **modulate** persona selection + tool routing + corpus weight
- **Persona context** affect retrieval ranking (UTZ creative → prioritize aesthetic chunks; ABOO engineer → prioritize code chunks)
- **Complexity tier** (simple/standard/deep) — top-down modulate kedalaman processing

**Code reference**: `complexity_router.py` + `persona_voice` injection.

### Pola 4 — Reflection Loop (Default Mode Network ↔ Task-Positive)

**Otak manusia**: 
- Task-positive network (TPN) — focused execution
- Default mode network (DMN) — mind-wandering, integration, insight
- Salience network — switch antara TPN ↔ DMN

Insight ("aha moment") sering muncul saat **DMN active** — otak step back, integrate, koneksi cross-domain.

**SIDIX equivalent — Wisdom Layer (Sprint 16-21)**:
```
After initial answer drafted:
  → Aha moment (DMN-like cross-domain connection)
  → Dampak analysis (consequence projection 2-5 langkah)
  → Risiko sensing (failure mode adversarial thinking)
  → Best-case spekulasi (scenario tree optimistic)
```

Ini step DELIBERATE — SIDIX **switch ke reflection mode** sebelum return final answer untuk topik sensitif/strategic. Bukan auto-pipe linear.

**Code reference**: `agent_wisdom.py` (Sprint 16) + Sprint 18 risk register + Sprint 19 scenario tree + Sprint 20 integrated.

### Pola 5 — Iterative Refine (Critique → Re-produce → Validate)

**Otak manusia**: saat menulis, manusia tidak draft satu kali. Loop:
1. Draft (executive output)
2. Read internal — anterior cingulate detect dissonance
3. Revise (working memory loop)
4. Compare to standard (orbitofrontal value judgment)
5. Repeat sampai cukup

**SIDIX equivalent — KITABAH loop (Sprint 22+22b)**:
```
Initial output → 
  RASA aesthetic scoring (4-dim, Sprint 21) → 
    Score < threshold? Critique extract → 
      Re-produce dengan revision hint → 
        Re-score → ... (max 3 iter)
```

Bukan output sekali jadi. **Iterative until quality threshold met**. Cite Sprint 22 KITABAH Auto-iterate.

### Pola 6 — Anticipatory Foresight (Predictive Coding)

**Otak manusia**: tidak passive receive. Otak **terus-menerus generate prediction** tentang next sensory input, lalu compare actual vs predicted (predictive coding theory). Saat prediction wrong → attention spike, learning.

**SIDIX equivalent — Proactive Foresight Agent (note 248 §DIMENSI VISIONER)**:
- Visioner cron weekly (Sprint 15 LIVE) — scan arxiv/HN/GitHub trending → projection 6-24 bulan
- Radar mention listener (note 245) — listen-only sekarang, future auto-engage opportunity
- ODOA daily tracker (Sprint 23) — daily compound improvement

SIDIX **bukan reactive only**. Proactive plan masa depan.

### Pola 7 — Embodiment (Tool sebagai Extension Tubuh)

**Otak manusia**: brain ≠ terpisah dari body. Mirror neurons mirror gesture, somatosensory feedback dari hand affect cognition (embodied cognition theory). Saat pakai hammer, hammer **jadi extension** dari arm di neural representation.

**SIDIX equivalent — Tools as embodiment**:
- Tools (web_search, code_sandbox, image_gen, TTS, 3D, dll) **bukan external API call**
- Mereka adalah **extension tubuh SIDIX** — tangan untuk web, mata untuk image, mulut untuk TTS
- 12-organ embodiment map (note 244 brain anatomy + note 248 §EMBODIMENT)

**Hard rule**: tool synthesizer (Sprint 31+ planned) — kalau tubuh existing tidak cukup, SIDIX **bikin organ baru** dari aspirasi user. Itu literal *"penemu inovatif kreatif"* di action level.

---

## 🔄 Continuous Plasticity (Sleep Consolidation Analog)

**Otak manusia**: tidur = consolidasi memori jangka panjang. Hippocampus replay daytime memory → transfer ke neocortex jangka panjang → synaptic pruning + strengthening.

**SIDIX equivalent**:
- Daily ODOA tracker (Sprint 23) — log harian artifacts + lessons
- Praxis runtime (Sprint 24) — extract lesson dari iterasi → training pair
- WAHDAH corpus signal (Sprint 24) — threshold trigger LoRA retrain
- Future Sprint 13 DoRA — weight-level update per persona, weekly retrain

**Setiap quartal SIDIX lebih pintar**, bukan static snapshot. Pola = sleep → wake → action → sleep → consolidate → next-day improved.

---

## 🚦 Pattern dalam Kode (Status per 2026-04-28)

| Pola Otak | SIDIX Komponen | Status | File |
|-----------|----------------|--------|------|
| 1. Multi-sensory parallel | asyncio.gather wiki + brave + corpus | LIVE | `agent_serve.py /ask/stream` |
| 2. Multi-perspective (5 specialists) | Wisdom layer 5 persona | LIVE prompt-level | `agent_wisdom.py` |
| 2. (DoRA weight-level) | DoRA persona stylometry | PLANNED Sprint 13 | proposed |
| 3. Top-down attention | Complexity router + persona voice | LIVE | `complexity_router.py` |
| 4. Reflection loop (DMN-like) | Wisdom 4-stage (aha+impact+risk+speculate) | LIVE | Sprint 16-21 |
| 5. Iterative refine | KITABAH gen-test-iterate | LIVE budget pending | Sprint 22+22b |
| 6. Anticipatory foresight | Visioner cron + Radar | PARTIAL | Sprint 15 LIVE, Radar planned |
| 7. Embodiment (tools as organ) | Tool registry + 12 organs | PARTIAL 11/15 | various |
| 7+ Tool synthesizer (cipta organ baru) | Aspiration → skill synthesis | PLANNED | Sprint 31+ proposed |
| Plasticity (sleep consolidation) | ODOA + Praxis + WAHDAH signal | LIVE signal-only | Sprint 23-24 |
| LoRA retrain trigger | WAHDAH-driven DoRA retrain | PLANNED | Sprint 13 |

---

## ⚠ Yang Belum Mirror Otak (Gap Critical)

### Gap 1 — DoRA persona belum weight-level
Saat ini 5 persona = prompt-level akting. Otak: 5 cortical specialists = circuit-level distinct. **Sprint 13 KRITIKAL**.

### Gap 2 — Vision + Audio input belum LIVE
Mata + telinga organ planned. Tanpa multi-sensory input nyata, "multi-sensory integration" cuma teks. **Sprint 29-30**.

### Gap 3 — Tool synthesizer belum
Otak bisa "bikin organ baru" via neuroplasticity (rare, butuh stimulus berat). SIDIX harus bisa via aspiration → skill synthesis. **Sprint 31+**.

### Gap 4 — Predictive coding belum
SIDIX masih reactive ke user input. Foresight cron weekly bukan continuous predictive. Future: per-turn predictive layer (anticipate user next likely follow-up).

### Gap 5 — Embodiment integrasi
12 organ ada tapi belum tightly integrated jadi "sensorimotor loop" terpadu. Masih function-call style, bukan continuous neural representation.

---

## 🔒 Anti-Drift Rules

Setiap kali SIDIX action di-design ulang (sprint touch flow), audit:

1. Apakah masih **multi-sensory parallel**? (jangan kembali ke linear pipeline)
2. Apakah masih **multi-perspective** (5 persona kena)? (jangan reduce ke 1 voice)
3. Apakah ada **reflection step**? (jangan langsung output tanpa wisdom check untuk topik sensitif)
4. Apakah **iterative refine** masih on? (jangan hapus KITABAH untuk speed)
5. Apakah **plasticity** masih jalan? (jangan freeze model, harus retrain trigger ada)

---

## 📚 Cross-Reference

- `docs/SIDIX_NORTH_STAR.md` — North Star LOCKED
- `docs/SIDIX_CANONICAL_V1.md` — single SOT
- research note 224 — 4 modul kognitif
- research note 244 — brain anatomy SIDIX architecture
- research note 248 — canonical pivot
- research note 278 — Cipta dari Kekosongan
- research note 280 — Static-Generative Pattern (akan dibuat)
- `docs/FOUNDER_JOURNAL.md` — directive log founder

---

**Lock statement**: SIDIX action **mirror otak manusia bukan template AI Agent**. 7 pola di atas = arsitektur, bukan suggestion. Setiap sprint baru harus serve atau tidak melanggar ini.
