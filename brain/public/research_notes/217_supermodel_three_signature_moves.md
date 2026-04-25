---
name: SIDIX 2.0 Supermodel — 3 Signature Moves
description: Tiga endpoint differentiator yang bikin SIDIX beda dari Claude/Gemini/KIMI saat launch — Burst+Refinement (Gaga creative), Two-Eyed Seeing (Mi'kmaq dual-perspective), Foresight (visionary scenario planning). Plus fix web_search trigger regex.
type: project
---

# SIDIX 2.0 Supermodel — 3 Signature Moves

**Tanggal**: 2026-04-25
**Konteks**: User minta SIDIX di launching pertama jadi "Supermodel AI Agent" — visioner, mampu prediksi masa depan, inovatif, beda dari chatbot mainstream. KIMI sudah handover via wire log + 3 docs (HANDOFF/VALIDASI/PLAN_OPTIMIZATION). Saya eksekusi plan + tambah 3 signature differentiator.

## Visi User (verbatim dari KIMI wire log)

> "Buat inovasi baru dari riset-riset yang ada jika diperlukan, sehingga SIDIX berbeda lebih maju dari AI agent populer sekarang."

> "saya mau SIDIX jadi AI Model Supermodel pada launching pertamanya, visionare, mampu memprediksi masa depan."

## Strategi: Bukan "AI Better", tapi "AI Different"

Persaingan langsung "lebih pintar dari Claude" = kalah selamanya — model size + RLHF budget Anthropic/OpenAI. Tapi **3 signature move** yang chatbot mainstream tidak punya bisa bikin SIDIX **kategori sendiri**:

| Differentiator | Sumber Inspirasi | Output Beda |
|---|---|---|
| **Burst + Refinement** | Lady Gaga creative process | Multi-angle parallel exploration vs linear single-pass |
| **Two-Eyed Seeing** | Mi'kmaq Etuaptmumk | Dual-perspective explicit vs monolog satu sudut |
| **Foresight Engine** | Tetlock super-forecasters + Carlota Perez | Scenario-based prediction vs hallucinated guess |

## 1. Burst + Refinement (Gaga Method)

### Riset
Lady Gaga creative process: "vomit ide dulu, baru pilih & polish". IDEO design thinking divergent → convergent. OpenAI Best-of-N sampling. Anthropic constitutional AI iteration.

### Implementasi
2-phase pipeline (`agent_burst.py`):

**BURST** (creative explosion):
- 8 pre-defined angles: contrarian, first_principles, analogy_far, constraint_extreme, user_wrong, future_back, synthesis_unrelated, invert (Munger)
- Setiap angle generate paralel via `ThreadPoolExecutor`
- Temperature tinggi (0.95), no filter, max_tokens 320 (cepat)

**REFINE** (Pareto convergence):
- 4-axis scoring per kandidat: novelty, depth, feasibility, alignment
- Pareto front selection (kandidat ≥ semua axis dan > minimal 1)
- Synthesis prompt: gabungkan winners jadi 1 narasi tunggal (BUKAN list "kandidat 1 mengatakan X")
- Temperature lebih rendah (0.4) untuk polish

### Endpoint
```
POST /agent/burst
{ "prompt": "...", "n": 6, "top_k": 2 }
→ { "final": "...", "winners": [...], "n_candidates": 6, "n_ok": 6 }
```

### Diferensiasi
Chatbot biasa: 1 path linear, jawaban pertama yang muncul = jawaban final. SIDIX Burst: explore 8 path paralel dulu, bunuh 6, kawin-silang 2 terbaik. Output lebih banyak novelty + grounded, bukan dari "best-effort guess".

## 2. Two-Eyed Seeing (Mi'kmaq Etuaptmumk)

### Riset
Etuaptmumk = "tampak ganda" — Elder Albert Marshall (Mi'kmaq Nation): scientific eye + Indigenous eye, bukan substitute, paralel + complementary. Diadopsi di Canadian medical research, environmental policy.

Untuk SIDIX:
- **Mata Scientific** = empirical/Western: data, mekanisme, falsifiability, cost-benefit
- **Mata Maqashid** = spiritual/komunal: hikmah, dampak komunal, prinsip etis, syariah anchor
- **Sintesis** = eka-eka (titik temu), tegangan jadi insight bukan winner-takes-all

### Implementasi (`agent_two_eyed.py`)
3 LLM call (paralel + sequential):
1. Left eye system prompt → 2-3 paragraf scientific
2. Right eye system prompt → 2-3 paragraf maqashid
3. Synthesis prompt: dengan kedua hasil di context → 1-2 paragraf integrator + 1 rekomendasi

### Endpoint
```
POST /agent/two-eyed
{ "prompt": "haruskah anak SD belajar coding sejak dini?" }
→ {
    "scientific_eye": {...},
    "maqashid_eye": {...},
    "synthesis": {...},
    "ok": true
  }
```

### Live test (2026-04-25)
"Haruskah anak SD belajar coding sejak dini?" →
- Scientific: aplikasi/perangkat lunak yang dirancang untuk anak, intuitif
- Maqashid: keterampilan jangka panjang, menjaring interaktif
- Synthesis: rekomendasi yang honor kedua mata

### Diferensiasi
Chatbot biasa untuk pertanyaan etis/strategis = monolog satu sudut. SIDIX explicit dual-lens — pengguna lihat reasoning empirical DAN nilai-driven secara terpisah, lalu sintesis. Ini transparency yang biasanya implisit/hilang di Claude/Gemini.

## 3. Foresight Engine (Visionary Scenario Planning)

### Riset
- **Tetlock Super-Forecasters** (Good Judgment Project): top 2% peramal kalahkan CIA analysts, kuncinya ≠ IQ — tapi structured reasoning (granular probability, frequent updates, scenario-thinking).
- **Carlota Perez Technological Revolutions**: pola installation phase → deployment phase, golden age vs bubble.
- **Talebian Anti-Fragile**: aksi yang menang di SEMUA skenario > aksi yang menang di satu.
- **Royal Dutch Shell Scenario Planning** (1973): playbook yang lolos oil shock karena sudah model "what if oil = 4×".
- **Kevin Kelly / Carlota Perez** narasi visioner: berani spesifik, bukan academic kering.

### Implementasi (`agent_foresight.py`)
4-stage pipeline:

**1. SCAN**:
- Web search dual: "topik terkini 2026" + "topik trend future prediction"
- Corpus search BM25 untuk sinyal historis
- Paralel via ThreadPoolExecutor

**2. EXTRACT**:
- LLM destilasi sinyal jadi 4 kategori:
  - Leading indicators (3-5): yang sudah mulai berubah
  - Lagging (2-3): yang masih lama berubah
  - Frictions (2-3): apa yang menghambat
  - Accelerators (2-3): apa yang mempercepat
- Setiap poin kutip teks sumber (≤80 char) untuk audit trail

**3. PROJECT** (Royal Dutch Shell scenario planning):
- 3 skenario dengan probability:
  - Base case (~50%)
  - Bull case (~25%) — accelerators menang
  - Bear case (~25%) — frictions menang
- Setiap skenario: outcome konkret + trigger event + sinyal pantau (3 bullet)

**4. SYNTHESIZE**:
- Prediksi inti (1 paragraf, berani spesifik, BUKAN hedging)
- Reasoning chain (3-5 langkah)
- What to do NOW (3 bullet, anti-fragile bias)
- Watchlist (3 sinyal pantau bulanan)

### Endpoint
```
POST /agent/foresight
{ "topic": "AI agent open source", "horizon": "1y" }
→ { "topic": "...", "final": "Prediksi inti...", "scenarios": "..." }
```

### Live test (2026-04-25)
"AI agent open source" 1y horizon → output: "AI agent open source akan jadi standard di industri teknologi... IBM, Microsoft, Google sudah memasuki jaringan..." (specific company names + reasoning).

### Diferensiasi
Chatbot biasa "halusinasi soal masa depan tanpa data" — kalimat seperti "in the future, things will likely change". SIDIX Foresight: scan sinyal terkini → reasoning terstruktur → prediksi konkret yang bisa diaudit (sinyal mana yang dipakai). Ini **structured forecasting**, bukan crystal ball.

## Bonus: Fix `_CURRENT_EVENTS_RE` (web search trigger)

KIMI's `_CURRENT_EVENTS_RE` regex hanya match "presiden" (Indonesian). User input "siapa **president** indonesia sekarang?" (English variant) → tidak trigger → fallback ke LLM hallucination ("Eh saya nggak bisa jawab").

Fix: regex diperluas:
- EN+ID variants (presiden|president|presi(d)?ent typo-tolerant)
- "who is the president/PM/king/queen/CEO/champion"
- Tahun spesifik (2023+) sebagai sinyal current event
- "what is happening" full form (not just "what's")
- Finance broader (gold/oil/yen/sgd)
- News broader (breaking, headline, updates)

Test: 14/14 sample queries route correctly. Live verify: "who is the president of indonesia in 2026 right now?" → web_search hit, 5 citations, "prabowo" in answer.

## Anti-bentrok Compliance

Tidak menyentuh:
- `agent_react.py JIWA INTEGRATION` section (KIMI)
- `agent_memory.py` (KIMI)
- `parallel_executor.py`, `jiwa/*` (KIMI)
- `cot_system_prompts.PERSONA_DESCRIPTIONS` (KIMI Jiwa territory)
- `ollama_llm.SIDIX_SYSTEM` (SHARED Jiwa-tone)

Hanya:
- `agent_react.py` CORE (Claude territory): `_CURRENT_EVENTS_RE` regex expansion
- `agent_serve.py` (Claude territory): 3 endpoint wiring
- 3 new files: `agent_burst.py`, `agent_two_eyed.py`, `agent_foresight.py` (Claude territory, MIT-licensed)

## Roadmap (next sprint)

- **Persona Lifecycle** (Bowie state machine): persona dormant → emerging → peak → declining → retired → reborn
- **Hidden Knowledge Resurrection** (Noether method): surface overlooked insights dari corpus
- **Constitutional Kaizen**: GEPA-lite evolves rules themselves
- **MCP Protocol** compatibility: tool listing in Anthropic standard
- **Wabi-Sabi Mode**: embrace imperfection, transience
- **Frontend wire** `/agent/generate/stream` ke chat UI untuk streaming UX
- **Quality eval suite**: golden tests dengan baseline metrics

## Filosofi Akhir

> "Bukan 'AI Better'. SIDIX adalah 'AI Different'."

3 signature move ini bukan optimasi marginal — ini **kategori baru**:
- **Bukan "answer engine"** — eksplorasi multi-angle
- **Bukan "single voice"** — dual-perspective explicit
- **Bukan "guess machine"** — structured forecasting

Kombinasi ketiga ini, plus epistemic honesty (sanad chain, kontekstual labels), bikin SIDIX punya posisi yang jelas vs Claude (intelligence) / Gemini (multimodal) / KIMI (creative): **SIDIX = epistemic + visionary + plural**.
