# Sprint A–E Summary & Next Roadmap — SIDIX Self-Evolving Engine

> **Date:** 2026-05-01
> **Branch:** `work/gallant-ellis-7cd14d`
> **Author:** Kimi Code CLI (Sprint Implementation)
> **Status:** 72/72 unit tests PASSED, committed, pushed to GitHub

---

## Part 1 — Apa yang Sudah Selesai (Sprint A–E)

### Ringkasan Eksekutif

Dalam 1 hari (2026-05-01), 5 sprint arsitektur inti telah diimplementasi dan terintegrasi. Semua sprint fokus pada **Fase 1: Organisme Hidup** — membuat SIDIX dari "chatbot dengan RAG" menjadi "organisme digital yang tumbuh sendiri."

---

### Sprint A — Sanad Orchestra (The Brain's Validator)

**File:** `apps/brain_qa/brain_qa/sanad_orchestra.py` (432 baris)

**Masalah:** Output SIDIX langsung ke user tanpa validasi. Tidak ada mekanisme untuk memastikan akurasi klaim faktual.

**Solusi:** Multi-source consensus validation engine.

**Cara kerja teknis:**
1. **Claim Extraction** — LLM (Ollama qwen2.5:1.5b) + regex fallback mengekstrak klaim faktual dari jawaban
2. **Claim Verification** — Setiap klaim diverifikasi terhadap 3 sumber:
   - `corpus_search` (BM25 lokal)
   - `web_search` (Mojeek + DDG + Wikipedia)
   - `tool_outputs` (calculator, sandbox, dll.)
3. **Consensus Calculation** — Weighted scoring: verified=1.0, partial=0.6, unverified=0.2
4. **Verdict Determination** — Relative thresholds per query type:
   - Simple factual (who/when/where): ≥ 0.92
   - Analytical (how/why): ≥ 0.85
   - Creative (opinion/design): ≥ 0.75
   - Tool output (code/calc): ≥ 0.95
5. **Retry Loop** — Kalau verdict="retry", synthesis ulang dengan failure context

**Endpoint:**
- `GET /agent/sanad/stats` — statistik validation
- `POST /agent/validate` — manual validation (body: `{answer, query, complexity}`)

**Tests:** 16/16 PASSED

---

### Sprint B — Hafidz Injection (The Brain's Memory)

**File:** `apps/brain_qa/brain_qa/hafidz_injector.py` (572 baris)

**Masalah:** Knowledge Accumulator menyimpan jawaban tapi tidak pernah di-inject kembali saat inference. SIDIX tidak "ingat."

**Solusi:** Two-Drawer Memory System.

**Cara kerja teknis:**
1. **Pre-query** — Retrieve context dari:
   - **Golden Store** (sanad ≥ threshold): few-shot examples yang berkualitas tinggi → inject ke prompt
   - **Lesson Store** (sanad < threshold): failure patterns → negative filter ("jangan lakukan ini")
2. **Prompt Injection** — `build_hafidz_prompt()` membuat section:
   - `## CONTOH BERKUALITAS TINGGI` — 2-3 contoh Q&A
   - `## PERINGATAN: Hindari kesalahan berikut` — 1-2 lesson warnings
3. **Post-query** — Store result berdasarkan Sanad score:
   - Score ≥ threshold → Golden Store (`brain/public/hafidz/golden/`)
   - Score < threshold → Lesson Store (`brain/public/hafidz/lesson/`)
4. **BM25-based Retrieval** — Keyword overlap scoring untuk find similar past queries

**Endpoint:**
- `GET /agent/hafidz/stats` — statistik memory

**Tests:** 18/18 PASSED

---

### Sprint C — Pattern Extractor Integration (The Brain's Induction)

**File:** `apps/brain_qa/brain_qa/pattern_extractor.py` (418 baris — sudah ada)

**Masalah:** Pattern Extractor ada tapi isolated — tidak di-wire ke pipeline OMNYX.

**Solusi:** Auto-extract patterns dari setiap conversation + inject ke future queries.

**Cara kerja teknis:**
1. **Post-query OMNYX** — `maybe_extract_from_conversation()` dipanggil setelah setiap interaksi
2. **Trigger Detection** — Regex mencari frasa induktif: "artinya", "berarti", "jadi kalau"
3. **LLM Extraction** — Ekstrak principle umum dari observation konkret
4. **Storage** — Save ke `brain/patterns/induction.jsonl` dengan metadata: domain, keywords, confidence
5. **Retrieval** — `search_patterns()` menggunakan keyword overlap + domain bonus
6. **Prompt Injection** — Patterns relevan di-inject ke synthesis prompt sebagai "POLA / PRINSIP RELEVAN"
7. **Corroboration/Falsification** — Pattern yang berhasil 5× naik confidence; counter-example turun

**Endpoint:**
- `GET /agent/patterns/stats`
- `GET /agent/patterns/search?q=...`
- `POST /agent/patterns/extract` (body: `{text, source_example}`)

**Tests:** 10/10 PASSED

---

### Sprint D — Aspiration Detector + Tool Synthesizer (The Brain's Ambition)

**File:** `apps/brain_qa/brain_qa/aspiration_detector.py` (330 baris — sudah ada)
**File:** `apps/brain_qa/brain_qa/tool_synthesizer.py` (483 baris — sudah ada)

**Masalah:** SIDIX tidak bisa detect user aspiration atau bikin tool baru.

**Solusi:** Detect aspiration → analyze → synthesize tool → validate → deploy.

**Cara kerja teknis Aspiration:**
1. **Trigger Detection** — Regex: "harusnya SIDIX juga bisa", "kenapa gak bisa", "bikin ah!"
2. **LLM Analysis** — Decompose aspiration jadi capability spec:
   - `capability_target`: apa yang mau dibuat
   - `decomposition`: langkah-langkah teknis
   - `resources_needed`: GPU/library/API
   - `estimated_effort`: low/medium/high/moonshot
   - `novel_angle`: apa yang unik vs kompetitor
3. **Storage** — Save ke `brain/aspirations/_index.jsonl`

**Cara kerja teknis Tool Synthesizer:**
1. **Spec Generation** — LLM generate JSON spec (name, input/output schema, dependencies)
2. **Code Generation** — LLM generate Python function (max 80 baris, no vendor API)
3. **Validation** — AST parse + forbidden pattern scan (openai, anthropic, os.system, eval)
4. **Sandbox Test** — Execute di `code_sandbox` dengan test_input
5. **Persist** — Save ke `brain/skills/<name>_<id>.py` + update `_index.json`

**Endpoint:**
- `POST /agent/aspiration/detect` (body: `{text}`)
- `POST /agent/tools/synthesize` (body: `{task}`)
- `GET /agent/skills/stats`
- `GET /agent/skills/list`

**Tests:** 14/14 PASSED

---

### Sprint E — Pencipta Mode (Creative Engine)

**File:** `apps/brain_qa/brain_qa/pencipta_mode.py` (427 baris — baru dibuat)

**Masalah:** SIDIX tidak bisa menciptakan hal baru tanpa diminta user.

**Solusi:** Creative engine yang trigger otomatis ketika 3 kondisi terpenuhi.

**Cara kerja teknis:**
1. **Trigger Check** (3 kondisi):
   - Self-Learn: pattern corroboration ≥ 3
   - Self-Improvement: sanad score ≥ 0.95 consistently (5+ samples)
   - Self-Motivate: unexplored aspirations > 0
2. **Auto-Trigger** — Dipanggil async post-query di OMNYX (non-blocking)
3. **Creative Generation** — 7 output types dengan prompt khusus per type:
   - `metode` — framework/method baru
   - `script` — automation script
   - `versi` — improved capability
   - `teknologi` — new architecture
   - `artifact` — creative piece
   - `karya` — complete polished work
   - `temuan` — novel insight
4. **Pipeline** — Generate → Sanad validate → Hafidz store → Save ke `brain/pencipta/`

**Endpoint:**
- `GET /agent/pencipta/status` — trigger status + score
- `POST /agent/pencipta/trigger` (body: `{output_type, domain}`) — manual trigger
- `GET /agent/pencipta/outputs` — list creative outputs
- `GET /agent/pencipta/stats`

**Tests:** 14/14 PASSED

---

## Part 2 — Arsitektur Terintegrasi (Flow End-to-End)

```
User Query
    ↓
[Hafidz: retrieve golden + lesson + patterns] ← Pre-query memory injection
    ↓
[OMNYX Direction]
    → Intent classification (complexity-aware)
    → Tool execution (corpus + web + persona)
    → Synthesis (with Hafidz context injected)
    ↓
[Sanad Orchestra] ← Post-synthesis validation
    → Claim extraction → Verify → Consensus score → Verdict
    ↓
[Storage Decision]
    ≥ threshold → Golden Store
    < threshold → Lesson Store
    ↓
[Post-Query Hooks]
    → Pattern Extractor: auto-extract inductive patterns
    → Aspiration Detector: auto-detect user ambition
    → Pencipta Mode: check 3 triggers (async, non-blocking)
    ↓
[Response to User]
    + sanad_score, sanad_verdict, hafidz_injected, hafidz_stored
```

---

## Part 3 — File yang Diubah / Dibuat

### File Baru (9)
| File | Baris | Sprint |
|------|-------|--------|
| `sanad_orchestra.py` | 432 | A |
| `hafidz_injector.py` | 572 | B |
| `test_sanad_orchestra.py` | 230 | A |
| `test_hafidz_injector.py` | 285 | B |
| `test_e2e_sanad_hafidz.py` | 75 | A+B |
| `test_pattern_integration.py` | 180 | C |
| `test_aspiration_tool_integration.py` | 175 | D |
| `pencipta_mode.py` | 427 | E |
| `test_pencipta_mode.py` | 185 | E |

### File Di-update (4)
| File | Perubahan |
|------|-----------|
| `omnyx_direction.py` | +Sanad validation, +Hafidz injection, +Pattern extraction, +Aspiration detection, +Pencipta trigger |
| `agent_serve.py` | +16 endpoint baru (sanad/hafidz/pattern/aspiration/skills/pencipta) |
| `cognitive_synthesizer.py` | +`_try_corpus_passthrough()` helper |
| `docs/LIVING_LOG.md` | +5 entri log |
| `docs/STATUS_TODAY.md` | +Sprint status update |

---

## Part 4 — Test Summary

| Sprint | Tests | Passed |
|--------|-------|--------|
| A — Sanad | 16 | 16 |
| B — Hafidz | 18 | 18 |
| C — Pattern | 10 | 10 |
| D — Aspiration/Tool | 14 | 14 |
| E — Pencipta | 14 | 14 |
| **TOTAL** | **72** | **72** |

---

## Part 5 — Roadmap Sprint Selanjutnya (Fase 2–4)

### Fase 1: Organisme Hidup ✅ DONE
| Sprint | Status |
|--------|--------|
| A — Sanad Orchestra | ✅ |
| B — Hafidz Injection | ✅ |
| C — Pattern Extractor | ✅ |
| D — Aspiration + Tool | ✅ |
| E — Pencipta Mode | ✅ |

### Fase 2: Creative Agent (Sprint F–H)
| Sprint | Fokus | Deliverable |
|--------|-------|-------------|
| **F** | Self-Test Loop | Generate Q → pipeline → score → Hafidz (cold start maturity) |
| **G** | Maqashid Auto-Tune | Auto-adjust Maqashid profiles based on feedback |
| **H** | Creative Output Polish | Improve Pencipta output quality with iteration loop |

### Fase 3: Persona Mandiri (Sprint I–K)
| Sprint | Fokus | Deliverable |
|--------|-------|-------------|
| **I** | DoRA Persona Adapter | Train LoRA adapter per persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) |
| **J** | Persona Growth Loop | Auto-harvest per persona, persona-specific pattern |
| **K** | Persona Council | Observer/Innovator/Critic debate loop (multi-agent adversarial) |

### Fase 4: Vision (Sprint L–N)
| Sprint | Fokus | Deliverable |
|--------|-------|-------------|
| **L** | Wisdom Layer | Aha moment, dampak analysis, risiko analysis, best-case spekulasi |
| **M** | Proactive Foresight | Trend sensing radar, weak signal aggregation, future projection |
| **N** | Self-Modifying Code | SIDIX bisa modifikasi kode sendiri, auto-refactor |

---

## Part 6 — Instruksi untuk Claude Code (QA + Deploy)

### A. QA Review Checklist

Claude Code harus review:

1. **Syntax Check** — Semua file Python baru compile tanpa error:
   ```bash
   cd apps/brain_qa
   python -m py_compile brain_qa/sanad_orchestra.py
   python -m py_compile brain_qa/hafidz_injector.py
   python -m py_compile brain_qa/pencipta_mode.py
   python -m py_compile brain_qa/omnyx_direction.py
   python -m py_compile brain_qa/agent_serve.py
   ```

2. **Unit Tests** — Jalankan semua tests:
   ```bash
   cd apps/brain_qa
   python -m pytest tests/test_sanad_orchestra.py tests/test_hafidz_injector.py tests/test_pattern_integration.py tests/test_aspiration_tool_integration.py tests/test_pencipta_mode.py -v
   ```

3. **Import Check** — Pastikan tidak ada circular import:
   ```bash
   python -c "from brain_qa.omnyx_direction import omnyx_process; print('OK')"
   python -c "from brain_qa.agent_serve import app; print('OK')"
   ```

4. **Endpoint Check** — Pastikan FastAPI bisa start:
   ```bash
   cd apps/brain_qa
   python -c "from brain_qa.agent_serve import app; from fastapi.testclient import TestClient; c = TestClient(app); print(c.get('/health').status_code)"
   ```

5. **Integration Check** — Panggil OMNYX end-to-end:
   ```bash
   python -c "import asyncio; from brain_qa.omnyx_direction import omnyx_process; r = asyncio.run(omnyx_process('siapa presiden indonesia?')); print(r.get('sanad_score'), r.get('hafidz_injected'))"
   ```

### B. Deploy ke VPS

**Step 1:** Cari path repo yang benar di VPS:
```bash
find / -name "agent_serve.py" -path "*/brain_qa/*" 2>/dev/null | head -3
```

**Step 2:** Pull dan restart:
```bash
cd <path-repo-yang-benar>
git pull origin work/gallant-ellis-7cd14d
pm2 restart sidix-brain
```

**Step 3:** Verify deploy:
```bash
curl -s http://localhost:8765/health | python -m json.tool
curl -s http://localhost:8765/agent/sanad/stats
curl -s http://localhost:8765/agent/hafidz/stats
curl -s http://localhost:8765/agent/pencipta/status
```

**Step 4:** Smoke test live:
```bash
curl -X POST http://localhost:8765/agent/chat_holistic \
  -H "Content-Type: application/json" \
  -d '{"question": "siapa presiden indonesia?", "persona": "AYMAN"}'
```

---

*End of Document*
