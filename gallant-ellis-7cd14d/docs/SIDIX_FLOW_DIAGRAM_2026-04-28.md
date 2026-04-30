# SIDIX Flow Diagram — Cara Kerja Sekarang (2026-04-28 evening)

> **Snapshot**: state production setelah Sprint 25-34J  
> **Authority**: live di VPS `/opt/sidix`, commit `1c784e9`  
> **Note**: diagram = **metafora arsitektur**, bukan blueprint rigid (per META-RULE founder)

---

## 1. End-to-End User Query Flow (`/ask` endpoint)

```
                    USER (chat UI app.sidixlab.com)
                              │
                              │ POST /ask {question, persona, allow_web_fallback}
                              ▼
                ┌─────────────────────────────────────┐
                │   nginx ctrl.sidixlab.com → :8765    │
                └─────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────────┐
                │   sidix-brain (PM2, FastAPI)         │
                │   pid 21, 4-vCPU AMD EPYC, 31GB     │
                │   /opt/sidix/start_brain.sh          │
                └─────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Layer 1: Rate Limit + Whitelist Check       │
            │  (env: SIDIX_WHITELIST_EMAILS)               │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Layer 2: Niat-Aksi Router (note 249)        │
            │  Parse intent → 5 turn types                  │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Layer 3: Complexity Router (note 274)       │
            │  Sprint 34D: <60 char + no deep_keyword      │
            │      → simple                                 │
            │  Else                                         │
            │      → standard / deep                        │
            └─────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────────┐
            │  Layer 4: Semantic Cache Lookup              │
            │  (in-memory LRU, embed-based similarity)     │
            │  HIT? return cached response                  │
            └─────────────────────────────────────────────┘
                              │ (miss)
                              ▼
                    ╔══════════════════════╗
                    ║   tier == simple ?    ║
                    ╚══════════════════════╝
                       │              │
                  YES  │              │  NO (standard/deep)
                       │              │
                       ▼              ▼
        ┌───────────────────┐    ┌──────────────────────┐
        │ Sprint 34E:        │    │ run_react()           │
        │ _needs_web_search? │    │ (full ReAct loop)     │
        └───────────────────┘    └──────────────────────┘
              │                            │
              ▼                            │
        ╔═══════════════╗                  │
        ║ web needed ?   ║                  │
        ╚═══════════════╝                  │
            │       │                      │
        NO  │       │ YES                  │
            │       └──────────────────────┤ (escalate ke standard)
            ▼                              │
   ┌────────────────────────────┐          │
   │ SIMPLE BYPASS               │          │
   │ Sprint 28a + 34B:           │          │
   │  • _simple_corpus_context() │          │
   │    BM25 top-1, skip praxis  │          │
   │    inject as ground truth   │          │
   │  • runpod_serverless        │          │
   │    .hybrid_generate()       │          │
   │  • RunPod first, Ollama fb  │          │
   └────────────────────────────┘          │
              │                              │
              │ direct response 1-2s         │
              │                              │
              └─────────────┬────────────────┘
                            │
                            ▼ (standard/deep path)
              ┌────────────────────────────────────┐
              │ run_react() — Multi-Step ReAct     │
              │                                     │
              │  Loop max ~6 steps:                 │
              │  Thought → Action → Observation     │
              │                                     │
              │  Tools available:                   │
              │   • search_corpus (Hybrid BM25+     │
              │     Dense BGE-M3 RRF, Sprint 25)   │
              │   • web_search (DDG → DDG Lite →    │
              │     Wikipedia simplified Sprint 28b)│
              │   • code_sandbox                    │
              │   • workspace_*                     │
              │   • orchestration_plan              │
              │   • dll (17+ tools)                 │
              └────────────────────────────────────┘
                            │
                            ▼
              ┌────────────────────────────────────┐
              │ _compose_final_answer (synthesis)   │
              │                                     │
              │ Sprint 34G: fact_extractor inject   │
              │  • Regex NER atas web_search obs    │
              │  • Frequency count entity            │
              │  • [FAKTA TERVERIFIKASI] block       │
              │    di TOP system prompt             │
              │                                     │
              │ Sprint 34F: prompt prioritize web   │
              │  • "Konteks SUMBER UTAMA"           │
              │  • "PRIORITAS over training prior"  │
              │                                     │
              │ Try sequence:                       │
              │  1. RunPod serverless (60s timeout) │
              │  2. Ollama qwen2.5:7b (60s)         │
              │  3. Sprint 34H DIRECT FACT RETURN   │
              │     (kalau LLM dead, fact ada)      │
              │  4. Local LoRA fallback             │
              │  5. Greeting template fallback      │
              │  6. (last) web text dump            │
              └────────────────────────────────────┘
                            │
                            ▼
              ┌────────────────────────────────────┐
              │ Sprint 34I+34J: POST-PROCESS        │
              │ OVERRIDE                             │
              │  • Re-run fact_extractor            │
              │  • Detect raw web dump format       │
              │  • Detect missing fact name         │
              │  • OVERRIDE answer dengan clean:    │
              │    "Berdasarkan pencarian web…"     │
              │                                     │
              │ ANTI-HALUSINASI defense layer       │
              └────────────────────────────────────┘
                            │
                            ▼
              ┌────────────────────────────────────┐
              │ Save QA pair (corpus growth)        │
              │ Activity log (per-user)             │
              │ Cognitive auto-hooks                │
              └────────────────────────────────────┘
                            │
                            ▼
                   Return JSON response
                   {answer, citations, persona,
                    confidence, _complexity_tier, ...}
                            │
                            ▼
                          USER
```

---

## 2. Background Cron Loops (Pilar 4: Proactive)

```
                    VPS crontab (Sprint 33 staggered)
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
   */15 * * * *          7,37 * * * *           4,19,34,49 * * * *
        │                     │                      │
        ▼                     ▼                      ▼
  sidix_always_on.sh    sidix_radar.sh         sidix_worker.sh
  (git observer +        (mention listener      (task queue
   mini growth)          Reddit/GH/News)         processor)
        │                     │                      │
        └──────┬──────────────┴──────────────┬──────┘
               │                              │
        9,24,39,54 * * * *              0 * * * *
               │                              │
               ▼                              ▼
       sidix_aku_ingestor.sh         sidix_classroom.sh
       (atomic knowledge unit         (multi-LLM teacher
        extractor)                     hourly Q&A)
               │                              │
               │                              ▼
               │               ┌──────────────────────────┐
               │               │ Multi-Teacher Pool        │
               │               │  • Gemini Flash           │
               │               │  • Kimi (Moonshot)        │
               │               │  • Groq Llama 3.3         │
               │               │  • OpenRouter / RunPod    │
               │               │                            │
               │               │ Consensus extract →        │
               │               │ classroom_pairs.jsonl      │
               │               │ → future LoRA retrain     │
               │               └──────────────────────────┘
               │
               ▼
        AKU inventory growth
        → corpus chunks
        → research notes ingest

        Plus (lain):
        - 0 23 * * *  : ODOA daily tracker
        - 0 0 * * 0   : visioner_weekly (foresight)
        - * 6-22 * * *: warmup_runpod (anti cold-start)
```

---

## 3. 5-Layer Anti-Hallucination Defense (Sprint 28b → 34J)

```
USER Query: "siapa Presiden Indonesia 2026?"
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 1: Sprint 28b                             │
│ web_search hardened:                            │
│  DDG → DDG Lite → Wikipedia (simplified query)  │
└────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 2: Sprint 34E                             │
│ Force web_search untuk current events:          │
│ siapa <role> + sekarang/saat ini/<year>         │
│  → bypass simple-tier, escalate ke standard     │
└────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 3: Sprint 34F                             │
│ System prompt PRIORITIZE web context:           │
│  "Konteks SUMBER UTAMA, prioritaskan over       │
│   training prior. Khusus tokoh saat ini,        │
│   JAWAB BERDASARKAN konteks."                   │
└────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 4: Sprint 34G — fact_extractor.py         │
│ DETERMINISTIC ENTITY EXTRACTION:                 │
│  • Regex NER atas web hits                       │
│  • Frequency count → most-mentioned name         │
│  • Inject [FAKTA TERVERIFIKASI] di TOP prompt   │
│  • LLM jadi FORMATTER, bukan JUDGE              │
└────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 5: Sprint 34H — DIRECT FACT RETURN        │
│ Kalau LLM (RunPod + Ollama) dead:               │
│  • BYPASS LLM entirely                           │
│  • Return fact langsung: "Berdasarkan web,       │
│    <role> adalah <name>. (Sumber: <url>)"        │
│  • Confidence 0.95 (deterministic > LLM judg.)   │
└────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────┐
│ Layer 6: Sprint 34I+J — /ask Post-Process       │
│ OVERRIDE kalau:                                  │
│  • Answer tidak mention extracted fact name     │
│  • Answer is raw web markdown dump (ugly)       │
│ → REPLACE dengan clean narrative + citations    │
└────────────────────────────────────────────────┘
            │
            ▼
        OUTPUT: "Presiden Indonesia adalah Prabowo.
                Sumber: https://presidenri.go.id"
```

---

## 4. 12-Organ Embodiment Map (note 244)

```
                    ┌─ 🧠 OTAK (LLM Layer)
                    │   Qwen2.5-7B + LoRA SIDIX
                    │   Ollama local + RunPod GPU fallback
                    │
                    ├─ ❤️  HATI (Niat Router)
                    │   Niat-aksi flow (note 249)
                    │
                    ├─ 🎨 KREATIVITAS (UTZ persona)
                    │   Sprint 14 creative pipeline
                    │
                    ├─ 🎭 RASA (Aesthetic Scorer)
                    │   Sprint 21 4-dim quality scoring
                    │
                    ├─ 💪 MOTORIK (Tool Dispatcher)
                    │   17+ tools, ReAct loop
                    │
                    ├─ 👁️  MATA (Web Reading)
                    │   Hyperx browser (httpx + selectolax)
                    │   Sprint 28b: web_search hardened
                    │
        SIDIX ──────┤
                    ├─ 👅 MULUT (TTS Output)
                    │   Edge-TTS Indonesian voice
                    │
                    ├─ 🤚 TANGAN (Generative)
                    │   image_gen, code_sandbox, 3D
                    │
                    ├─ 🦵 KAKI (Filesystem)
                    │   sandbox + git ops
                    │
                    ├─ 🧬 DNA (Corpus + LoRA)
                    │   research_notes + skill library
                    │   pattern library (planned)
                    │
                    ├─ 🎯 INTUISI (Foresight)
                    │   visioner cron (planned 6-24mo)
                    │
                    └─ 👂 TELINGA (Audio Input)
                        Whisper local (PLANNED)
```

---

## 5. Compound Sprint Chain (Architecture Compound)

```
SPRINT 12 (CT 4-pilar engine)
    ↓
SPRINT 14 (Creative pipeline)
    ↓
SPRINT 16-21 (Wisdom layer 5-stage)
    ↓
SPRINT 22-24 (KITABAH/ODOA/WAHDAH self-learning)
    ↓
SPRINT 25-27 (Hybrid retrieval +6% Hit@5)
    ↓
SPRINT 28a-b (Simple-tier corpus inject + web hardened)
    ↓
SPRINT 29 (Shadow pool wired-blocked)
    ↓
SPRINT 30+ (Continuity manifest + sanad gap)
    ↓
SPRINT 31-33 (Permission hardening + cron stagger)
    ↓
SPRINT 34A-J (Anti-hallucination 5-layer defense)
    ↓
[Now] Q3 Presiden Indonesia → Prabowo ✓ verified
```

---

## 6. Production State Snapshot

| Component | Status | Verified |
|-----------|--------|----------|
| sidix-brain (PM2 id 21) | ONLINE | health 200ms |
| Hybrid retrieval (BM25+Dense+RRF) | LIVE | +6% Hit@5 |
| Cron (6 scripts) | LIVE post-chmod | logs growing |
| Post-merge hook auto-chmod | LIVE | terbukti preserve perms |
| RunPod warmup */1 6-22 WIB | LIVE | code 200 every minute |
| 5-layer anti-halusinasi | LIVE | Q3 Prabowo verified |
| Ollama systemd tune | LIVE | NUM_PARALLEL=1, KEEP_ALIVE=10m |
| SSH session_key auto | LIVE | post v2 expired |

---

**Locked**: 2026-04-28 evening (commit `1c784e9`).  
Next session bisa pickup dari sini sebagai canonical state diagram.
