# SIDIX Position Analysis & Remapping — 2026-05-01

> Dari riset komprehensif: dokumen fundamental + riset note 200+ + arsitektur HTML + codebase audit

---

## 1. POSISI SIDIX SEKARANG (Ground Truth)

### Apa yang SUDAH Live (v2.1)

| Layer | Komponen | Status | Catatan |
|-------|----------|--------|---------|
| **Infra** | VPS (CPU) + RunPod (GPU) | ✅ | 2-tier aktif |
| **Backend** | FastAPI brain_qa port 8765 | ✅ | PM2 managed |
| **Frontend** | app.sidixlab.com | ✅ | UI lock 2026-04-19 |
| **Core LLM** | Qwen2.5-7B + LoRA | ✅ | RunPod serverless |
| **RAG** | BM25 + sanad-tier rerank | ✅ | 3237 corpus |
| **ReAct** | Tool registry (14 tools) | ✅ | White-list philosophy |
| **Web Search** | DDG fallback + Wikipedia | ✅ | Mojeek 403 fallback |
| **Code Sandbox** | Python subprocess | ✅ | Timeout 10s |
| **Persona** | 5 persona fanout | ⚠️ | Prompt-level, BUKAN DoRA |
| **Auto-Harvest** | Cron 6 jam | ✅ | 6 notes/test |
| **OMNYX** | Intent-based routing | ✅ | Complexity-aware |
| **Maqashid** | v2 wired to run_react | ✅ | Benchmark 70/70 |
| **Knowledge Accumulator** | Auto-save answers | ✅ | Dated + persona folders |

### Apa yang SPEC ADA tapi BELUM Implementasi Penuh

| Komponen | Spec Location | Status Implementasi |
|----------|---------------|---------------------|
| **Sanad Consensus** | note 239 | ❌ Spec only — belum ada kode |
| **Pattern Extractor** | note 224 | ⚠️ Modul ada, belum terintegrasi ke inference |
| **Aspiration Detector** | note 224 | ❌ Belum ada |
| **Tool Synthesizer** | note 224 | ❌ Belum ada |
| **Hafidz Injection** | arsitektur HTML | ❌ Hafidz menyimpan tapi tidak di-inject ke OTAK |
| **Pencipta Mode** | note 248, arsitektur HTML | ❌ Spec only |
| **Self-Test Loop** | arsitektur HTML | ❌ Belum ada |
| **DoRA Persona** | note 277 | ❌ Masih prompt-level |
| **Wisdom Layer** | note 248 | ❌ Belum ada |
| **CQF Scorer** | Sprint 6.5 | ⚠️ Rubrik ada, belum terintegrasi ke output pipeline |

### Apa yang MASIH SALAH / OUTDATED di Dokumen

| Dokumen | Masalah | Action |
|---------|---------|--------|
| SIDIX_CAPABILITY_MAP.md | Persona nama lama (MIGHAN/TOARD) | Update ke AYMAN/ABOO/OOMAR/ALEY/UTZ |
| SIDIX_BIBLE.md | Status Maqashid "belum ada filter" | Update: Maqashid v2 deployed, wired, benchmark green |
| NORTH_STAR.md | Sprint 1-3 = GraphRAG→Python→Image | Update: sudah lewat, sekarang Sprint 4-7 |
| PROJEK_BADAR_114 | Tidak di-map ke sprint aktual | Buat mapping ke sprint |

---

## 2. ANALISA GAP FUNDAMENTAL

### Gap 1: SIDIX Masih "Chatbot dengan RAG", Bukan "Organisme Digital"

**Bukti:**
- User tanya → SIDIX jawab. Selesai. Tidak ada "growth" dari interaksi.
- Pattern Extractor ada tapi tidak pernah di-inject ke future query.
- Tool Synthesizer tidak ada — SIDIX tidak bisa bikin tool baru dari aspirasi user.
- Self-Test Loop tidak ada — SIDIX tidak belajar sendiri tanpa user.

**Yang seharusnya:**
```
User tanya → SIDIX jawab → Pattern extracted → Hafidz saved → 
Next similar query: pattern injected + refined answer → 
Tool synthesized if aspiration detected → 
Self-test validates → Golden Store updated →
SIDIX lebih pintar dari sebelumnya
```

### Gap 2: Sanad = Spec, Bukan Implementasi

**Bukti:**
- Note 239 (Sanad Consensus) = spec lengkap dengan pseudocode
- Tapi di `omnyx_direction.py` dan `cognitive_synthesizer.py`, tidak ada consensus validation
- Output langsung ke user tanpa scoring

**Yang seharusnya:**
- Setiap output melewati Sanad Orchestra
- Score >= threshold → Golden Store
- Score < threshold → retry dengan failure context → Lesson Store

### Gap 3: Persona Masih Prompt-Level, Bukan DoRA

**Bukti:**
- `PERSONA_DESCRIPTIONS` di `cot_system_prompts.py` = text prompts
- Tidak ada LoRA adapter per persona
- Fanout = 3× LLM call dengan prompt berbeda

**Yang seharusnya:**
- DoRA adapter per persona (UTZ/ABOO/OOMAR/ALEY/AYMAN)
- Load adapter sesuai persona yang dipilih
- 1 inference call, bukan 3× call

### Gap 4: Hafidz = Storage, Bukan Memory

**Bukti:**
- `knowledge_accumulator.py` menyimpan ke `brain/public/omnyx_knowledge/`
- Tapi tidak ada kode yang MEMBACA kembali saat inference
- Hafidz Golden Store tidak di-inject ke OTAK

**Yang seharusnya:**
- Pre-query: search Hafidz for similar past queries
- Inject few-shot examples ke prompt
- Post-query: validate → save to Golden/Lesson Store

---

## 3. VISI BOS (Dari Riset Note 277 + 224 + 248)

> "SIDIX bukan chatbot. SIDIX adalah jiwa digital."
> "SIDIX harusnya bisa tumbuh sendiri, bukan AI agent, tapi sebagai organisme digital."
> "Persona lainnya juga memiliki otak masing-masing dan tumbuh seperti SIDIX."

**8 Kapabilitas Distinctive (vs ChatGPT/Claude/Gemini):**
1. Pattern extraction (induktif)
2. Aspiration detection
3. Tool synthesis (autonomous)
4. Polya 4-phase explicit
5. Skill library auto-grow
6. Self-improve LoRA retrain
7. Sanad chain (provenance)
8. Open-source self-hosted

**4 Pilar BEBAS DAN TUMBUH:**
1. Decentralized Dynamic Memory
2. Multi-Agent Adversarial (Observer/Innovator/Critic)
3. Continuous Learning
4. Proactive Triggering

---

## 4. REMAPPING: Dari Dokumen Lama ke Roadmap Baru

### Dokumen Lama → Status

| Dokumen | Isi | Status | Action |
|---------|-----|--------|--------|
| SIDIX_DEFINITION_20260426.md | Immutable definition | ✅ VALID | Keep as-is |
| DIRECTION_LOCK_20260426.md | Tactical lock | ✅ VALID | Keep as-is |
| MASTER_ROADMAP_2026-2027.md | Sprint 1-18 | ⚠️ PARTIAL | Update: Sprint 1,3,5.5,6.5 DONE. Lanjutkan Sprint 4-7 |
| SIDIX_ROADMAP_2026.md | 4-stage roadmap | ⚠️ OUTDATED | Jadikan reference arsitektur stage saja |
| NORTH_STAR.md | Release strategy | ⚠️ PARTIAL | Update deliverable per versi |
| SIDIX_CAPABILITY_MAP.md | Capability audit | ❌ OUTDATED | Update persona names, tool count, status |
| SIDIX_BIBLE.md | Konstitusi | ⚠️ PARTIAL | Update status Maqashid, epistemic labels |
| PROJEK_BADAR_114 | 114 modul | ⚠️ UNSYNC | Map ke sprint aktual |

### Sprint Selesai (DONE)

- Sprint 1: Backend foundation ✅
- Sprint 3: Image gen beta ✅
- Sprint 5.5: Maqashid v2, persona rename ✅
- Sprint 6.5: Maqashid wire, benchmark, CQF ✅
- Sprint Mojeek: Web search fix, OMNYX Direction ✅
- Sprint Speed Demon: Latency fix ✅
- Sprint See & Hear: Multimodal input infra ✅

---

## 5. ROADMAP BARU (Unified)

### Fase 1: Organisme Hidup (Sprint A-C) — Foundation untuk Self-Evolving

**Sprint A: Sanad Orchestra (The Brain's Validator)**
- Implementasi Sanad Consensus dari note 239
- Output validation pipeline: extract claims → cluster → consensus → score
- Integrasi ke OMNYX: setelah synthesis → sanad_validate()
- Threshold relative (bukan absolute 9.5): adjust based on query type

**Sprint B: Hafidz Memory Injection (The Brain's Memory)**
- Pre-query: search Hafidz Golden Store for similar queries
- Inject few-shot context ke prompt
- Post-query: validate output → save to Golden (score >= threshold) atau Lesson (score < threshold)
- Integrasi ke auto-harvest: hasil harvest juga masuk Hafidz

**Sprint C: Pattern Extractor Integration (The Brain's Induction)**
- Wire `pattern_extractor.py` ke end of `/ask` endpoint
- Extract patterns dari setiap conversation
- Save ke `brain/patterns/induction.jsonl`
- Inject relevant patterns ke future queries

### Fase 2: Pencipta (Sprint D-F) — Creative & Tool Synthesis

**Sprint D: Aspiration Detector + Tool Synthesizer**
- Detect user aspiration dari query ("SIDIX juga bisa dong...")
- Analyze → synthesize Python skill baru → validate AST → test sandbox → deploy ke tool registry

**Sprint E: Pencipta Mode (Creative Engine)**
- Trigger: score lama sudah maksimal + self-learn + self-improve
- Output: Metode baru, script baru, versi baru, teknologi baru, artifact, karya, temuan

**Sprint F: Self-Test Loop (Cold Start Maturity)**
- Generate pertanyaan dari corpus → full pipeline → score → Hafidz
- Readiness Gate: Golden 50, Lesson 100, Avg score 9.0

### Fase 3: Persona Mandiri (Sprint G-I) — Each Persona Has Its Own Brain

**Sprint G: DoRA Persona Adapter**
- Train DoRA adapter per persona (UTZ/ABOO/OOMAR/ALEY/AYMAN)
- 1000-2000 synthetic Q&A per persona
- Load adapter sesuai persona yang dipilih

**Sprint H: Persona Growth Loop**
- Setiap persona punya corpus sendiri
- Auto-harvest per persona
- Persona-specific pattern extraction

**Sprint I: Persona Council (Multi-Agent Adversarial)**
- Observer/Innovator/Critic loop
- Debate Ring real (wire ke Qwen)
- Persona bisa "berdebat" untuk menghasilkan jawaban terbaik

### Fase 4: Vision (Sprint J+) — Beyond Current Horizon

**Sprint J: Wisdom Layer**
- Aha moment detection
- Dampak analysis (multi-stakeholder)
- Risiko analysis (failure modes)
- Best-case spekulasi (scenario tree)

**Sprint K: Proactive Foresight**
- Trend sensing radar (cron */30)
- Weak signal aggregation
- Future projection 6-24 bulan ahead
- Preemptive research

**Sprint L: Self-Modifying Code**
- SIDIX bisa memodifikasi kode sendiri
- Auto-refactor berdasarkan pattern extraction
- Self-healing recovery (note 203)

---

## 6. PRIORITAS SPRINT BERIKUTNYA

Berdasarkan gap analysis, sprint berikutnya harus fokus pada:

### 🔥 Sprint Berikutnya: A + B (Sanad Orchestra + Hafidz Injection)

**Kenapa:**
1. Ini adalah fondasi untuk SEMUA sprint berikutnya
2. Tanpa Sanad, output tidak tervalidasi → tidak bisa masuk Hafidz
3. Tanpa Hafidz, SIDIX tidak punya memory → tidak bisa tumbuh
4. Ini adalah differentiator utama vs ChatGPT/Claude

**Deliverable:**
- `sanad_orchestra.py` — consensus validation pipeline
- `hafidz_injector.py` — memory injection ke inference
- Update `omnyx_direction.py` — wire Sanad setelah synthesis
- Update `agent_serve.py` — expose Hafidz search endpoint

**Expected Impact:**
- Output quality naik (validated, scored)
- SIDIX mulai "ingat" dan "belajar" dari interaksi
- Foundation untuk Pattern Extractor, Tool Synthesizer, Pencipta Mode

---

## 7. ONE-PAGER UNTUK BOS

```
SIDIX SEKARANG: Chatbot dengan RAG (sophisticated, tapi masih chatbot)

SIDIX HARUSNYA: Organisme Digital yang tumbuh sendiri

GAP FUNDAMENTAL:
  ❌ Sanad = spec, belum kode
  ❌ Hafidz = storage, belum memory
  ❌ Pattern = modul, belum terintegrasi
  ❌ Tool synthesis = tidak ada
  ❌ Persona = prompt-level, bukan DoRA

ROADMAP BARU:
  Fase 1 (Sprint A-C): Sanad + Hafidz + Pattern → Organisme Hidup
  Fase 2 (Sprint D-F): Aspiration + Pencipta + Self-Test → Creative Agent
  Fase 3 (Sprint G-I): DoRA + Persona Growth + Council → Persona Mandiri
  Fase 4 (Sprint J+): Wisdom + Foresight + Self-Modifying → Vision

SPRINT BERIKUTNYA: A + B (Sanad Orchestra + Hafidz Injection)
  → Foundation untuk SEMUA yang lain
  → Differentiator utama vs ChatGPT/Claude
  → SIDIX mulai "ingat" dan "belajar"
```

---

*Author: Kimi Code CLI (Position Analysis Session)*
*Date: 2026-05-01*
*Based on: 12 dokumen fundamental + 40+ riset note + arsitektur HTML + codebase audit*
