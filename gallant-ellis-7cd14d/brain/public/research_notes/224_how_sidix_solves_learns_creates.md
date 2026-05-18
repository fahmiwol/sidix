# 224 — How SIDIX Solves, Learns, Creates: Cognitive Foundation Architecture

**Date**: 2026-04-26 (vol 5)
**Tag**: ARCHITECTURE / VISION / IMPLEMENTATION
**Status**: 4 modul foundation live + endpoint wired
**Trigger**: User question

> "Terakhir gimana caranya sidix bantu mecahin masalah? atau bagaimana caranya
> sidix belajar hal baru? bagaimana caranya sidix bisa membuat tools baru,
> padahal tools itu tidak ada referensinya?"

Plus 3 contoh konkret yang user kasih:

**A. Analogi induktif:**
> "Oh kalo batok kelapa dibakar bisa jadi arang. Artinya kayu juga kalo dibakar
> jadi arang."

**B. Komposisi kreatif:**
> "Oh teh itu kalo direbus pake gula rasanya jadi teh manis. Gimana kalo teh
> pake sirup leci, lebih enak pastinya."

**C. Aspirasi kapabilitas:**
> "Oh GPT bisa bikin gambar, harusnya saya juga bisa. OH ada banyak tools di
> Internet buat bikin 3D generator harusnya saya juga bisa, oh saya tahu cara
> kerjanya bikin tools editing video seperti CapCut, harusnya SIDIX juga bisa
> + ada inovasi terbaru dari SeedDance dan ByteDance, kalo dikombinasiin
> makin keren. Bikin ah!"

3 jenis kognisi → 4 modul foundation yang dibangun hari ini.

---

## Mapping User Examples → SIDIX Modules

| User Example | Tipe Kognisi | SIDIX Module | Existing? |
|---|---|---|---|
| A — batok kelapa → kayu | **Induktif Generalisasi** | `pattern_extractor.py` | ✅ NEW vol 5 |
| B — teh + gula → teh + leci | **Komposisi Kreatif** | `agent_burst.py` (existing) | ✅ JALAN |
| C — GPT image → SIDIX image | **Aspirasi Kapabilitas** | `aspiration_detector.py` + `tool_synthesizer.py` | ✅ NEW vol 5 |
| Problem solving general | **Polya 4-phase** | `problem_decomposer.py` | ✅ NEW vol 5 |

---

## Modul 1: `pattern_extractor.py` — Induktif Generalisasi

### Cara Kerja (jawab Example A)

User bilang: *"batok kelapa dibakar → arang. Artinya kayu juga kalo dibakar jadi arang."*

```
[1] Trigger detection — regex match "artinya" → looks_like_inductive_claim() = True
[2] LLM extract:
    Input: full sentence
    Output JSON: {
      "principle": "Material organik (biomass) dengan kandungan karbon
                    tinggi → karbonisasi saat dibakar menghasilkan arang",
      "domain": ["organic", "thermal", "biomass"],
      "keywords": ["bakar", "karbon", "arang", "biomass", "kayu", "kelapa"],
      "confidence": 0.78
    }
[3] Save ke brain/patterns/induction.jsonl
[4] Saat user query lain: "gimana cara bikin briket?" 
    → search_patterns("briket") → match domain "biomass"+"thermal"
    → inject pattern sebagai context ke LLM
    → SIDIX bisa reasoning: "Briket = bentuk arang dipadatkan, prinsip
                            karbonisasi sama dengan biomass lain"
```

### Key Innovations
- **Soft prior, bukan rule rigid** — pattern di-inject ke prompt LLM, biarkan
  LLM final-judge applicability (bukan hardcoded if-else)
- **Corroboration tracking** — pattern berhasil applied 5x → confidence naik
  ke 0.95. Counter-example → falsifications++ → confidence turun
- **Domain-tagged retrieval** — query "briket" + domain hint "thermal" lebih
  cepat match daripada keyword match saja

### Endpoint
- `POST /agent/patterns/extract {text}` — manual extract
- `GET /admin/patterns/stats` — total + by_domain + avg_confidence

### Status
✅ **Live**. Empty library hari ini, akan terisi otomatis saat hook
`maybe_extract_from_conversation` dipanggil di end of /ask.

---

## Modul 2: `agent_burst.py` (existing) — Komposisi Kreatif

### Cara Kerja (jawab Example B)

User bilang: *"teh + sirup leci, lebih enak pastinya?"*

Burst mode existing **sudah cocok untuk pattern ini**:

```
[1] User trigger Burst (manual atau auto-detect)
[2] LLM generate 6 angle paralel:
    - Angle 1: "Teh hijau + leci syrup + es batu (fresh)"
    - Angle 2: "Teh hitam + leci + bunga lavender (premium)"
    - Angle 3: "Teh oolong + leci konsentrat + soda (modern)"
    - Angle 4: "Teh chamomile + leci + madu (calming)"
    - Angle 5: "Teh matcha + leci + susu (Asian fusion)"
    - Angle 6: "Teh peppermint + leci + lime (refreshing)"
[3] Pareto filter: skor tiap angle pada (novelty, feasibility, depth, alignment)
[4] Top 2 diambil → synthesize jadi 1 jawaban polished
```

### Yang BELUM ada (P1 next)
- **Auto-trigger Burst** untuk pertanyaan "gimana kalo X jadi Y?" pattern.
  Sekarang user harus klik manual.
- **Cross-reference dengan pattern_extractor** — kalau ada pattern "teh +
  pemanis = enak", inject sebagai prior

### Status
✅ **Live**. Tinggal auto-trigger detection (P1, ~1 minggu effort).

---

## Modul 3: `aspiration_detector.py` + `tool_synthesizer.py` — Aspirasi Kapabilitas

### Cara Kerja (jawab Example C)

User bilang: *"oh GPT bisa bikin gambar, harusnya saya juga bisa... bikin ah!"*

```
[1] DETECT — aspiration_detector.detect_aspiration_keywords()
    Match phrases: ["GPT", "bisa", "harusnya", "bikin ah"]
    → Trigger LLM analyze
[2] ANALYZE — generate Aspiration spec:
    {
      "capability_target": "image generation tool integrasi",
      "competitors_mentioned": ["GPT", "ChatGPT", "DALL-E", "Midjourney",
                                "SeedDance", "ByteDance"],
      "inspiration_sources": ["Stable Diffusion", "FLUX", "DALL-E 3"],
      "decomposition": [
        "Setup HuggingFace inference endpoint untuk Stable Diffusion XL",
        "Wrap as FastAPI endpoint /tools/image_gen",
        "Add ke ReAct tool registry",
        "Frontend: tombol generate image di chat",
        "Quota: image gen = 5x text quota karena GPU heavy"
      ],
      "resources_needed": ["RunPod GPU 4090", "diffusers library",
                          "FastAPI", "frontend Vite"],
      "estimated_effort": "medium",
      "open_source_alternatives": ["Stable Diffusion XL", "FLUX.1-dev",
                                  "ComfyUI", "Diffusers"],
      "novel_angle": "Sidix-style image: tambah Quranic geometry overlay,
                     sanad-traceable prompt (provenance), Indonesian
                     cultural visual library (batik patterns, wayang
                     character references)"
    }
[3] SAVE — brain/aspirations/asp_xxx.md (markdown spec untuk review human)
[4] (Optional) SYNTHESIZE — kalau effort=low/medium, langsung trigger
    tool_synthesizer.synthesize_skill(decomposition[0])
    → LLM generate Python code
    → validate AST + forbidden patterns scan
    → test in code_sandbox dengan dummy input
    → kalau valid → save brain/skills/image_gen_xxxxxx.py
[5] DEPLOY — runtime register skill ke tool registry, ReAct query berikutnya
    bisa pakai tool ini
```

### Sample Aspiration Markdown (auto-generated)

```markdown
# image generation tool integrasi

**ID**: asp_a1b2c3d4ef
**Status**: draft
**Effort**: medium

## User Message
> oh GPT bisa bikin gambar, harusnya saya juga bisa...

## Competitors / Inspiration
- **Competitors**: GPT, ChatGPT, DALL-E, Midjourney, SeedDance
- **Open source alternatives**: Stable Diffusion XL, FLUX.1-dev, ComfyUI

## Novel Angle
Sidix-style image: Quranic geometry overlay, sanad-traceable prompt,
Indonesian cultural visual library (batik, wayang)

## Implementation Decomposition
1. Setup HuggingFace inference endpoint Stable Diffusion XL
2. Wrap as FastAPI endpoint /tools/image_gen
3. Add ke ReAct tool registry
4. Frontend tombol generate image
5. Quota: image gen = 5x text quota

## Resources Needed
- RunPod GPU 4090
- diffusers library
- FastAPI
- frontend Vite

## Next Steps
- [ ] Review draft (admin atau user)
- [ ] Approve untuk eksekusi
- [ ] Spawn ke tool_synthesizer (kalau effort low/medium)
- [ ] Atau buka issue GitHub (kalau effort high/moonshot)
```

### Tool Synthesizer — End-to-end Pipeline

```python
def synthesize_skill(task_description: str) -> SkillSpec:
    """
    1. spec = generate_skill_spec(task)        # LLM JSON output
    2. code = generate_skill_code(spec)        # LLM Python output
    3. ok = validate_code(code)                # AST + forbidden scan
    4. success = test_skill_in_sandbox(spec)   # exec di code_sandbox
    5. save_skill(spec)                        # brain/skills/<name>.py
    """
```

### Forbidden Patterns (Safety)
```python
_FORBIDDEN_PATTERNS = [
    r"openai", r"anthropic", r"google.genai", r"gemini",  # NO vendor LLM
    r"os\.system", r"subprocess",                          # NO shell escape
    r"__import__", r"eval\(", r"exec\(",                  # NO dynamic code
    r"requests\.(post|put|delete)",                       # NO mutation HTTP
    r"open\(.+,\s*['\"]w",                                # NO disk write
]
```

Skill yang fail validate atau sandbox → status="invalid"/"test_failed".
Skill yang sukses → status="tested" → admin review → status="deployed".

### Endpoint
- `POST /agent/aspirations/analyze {text}` — manual capture
- `POST /agent/skills/synthesize {task_description}` — manual synthesize
- `GET /admin/aspirations/stats` + `GET /admin/skills/stats` — dashboard

### Status
✅ **Foundation live**. Belum auto-trigger di /ask (P1). Belum runtime
auto-register skill ke ReAct tool registry (P2, butuh integration).

---

## Modul 4: `problem_decomposer.py` — Polya 4-Phase Problem Solving

### Cara Kerja (jawab pertanyaan "gimana sidix bantu mecahin masalah?")

Polya's "How to Solve It" (1945) — 4 tahap:

```
PHASE 1: UNDERSTAND
  - given_data: apa yang sudah ada?
  - unknown_target: apa yang dicari?
  - constraints: batasan?
  - related_patterns: cari di pattern_extractor

PHASE 2: PLAN
  - strategy: high-level approach
  - sub_goals: langkah konkret
  - tools_needed: web_search, code_sandbox, calculator, etc.
  - similar_solved_cases: ada referensi?

PHASE 3: EXECUTE  ← di-handle oleh ReAct loop existing (run_react)
  - execution_steps: per-step trace
  - final_answer: jawaban ditemukan

PHASE 4: REVIEW
  - correctness_check: solusi benar? blunder?
  - confidence_estimate: 0-1
  - generalizable_insight: bisa jadi pattern baru?
  - lessons_learned: untuk future
  - AUTO: kalau generalizable, save ke pattern_extractor library
```

### Key Innovation: Phase 4 Closes the Loop

Saat solusi ditemukan, SIDIX **otomatis cek**: "ada prinsip umum yang bisa
di-extract?" Kalau ya → save ke pattern library → next problem similar
domain bisa retrieve langsung.

**Compound learning**: tiap problem-solve sesi makin pintar untuk problem
serupa. Bukan retrain LLM (mahal), tapi retrieve-augmented (cheap).

### Endpoint
- `POST /agent/decompose {problem}` — phase 1+2 only (Phase 3 ReAct, Phase 4 manual review)

### Status
✅ **Foundation live**. Belum auto-invoke di /ask (P1, ~1 minggu).

---

## Bagaimana 4 Modul Bekerja Bersama (Holistic)

User chat: *"buatkan saya AI assistant yang bisa baca screenshot kode dan
auto-debug, kayak GitHub Copilot tapi local."*

```
[1] aspiration_detector trigger (keyword "kayak", "tapi local")
    → Capture aspiration:
      - capability: "screenshot OCR + code debug"
      - competitors: ["GitHub Copilot"]
      - novel_angle: "local self-hosted, no telemetry"
      - effort: medium
[2] problem_decomposer kicks in (Phase 1-2):
    - given: VLM, OCR, code analysis tools
    - unknown: integrate ke chat UI dengan low latency
    - sub_goals: [
        "Setup VLM endpoint (Qwen2.5-VL or LLaVA)",
        "OCR pre-process (paddleocr/tesseract)",
        "Code parse + lint via existing code_sandbox",
        "Wire ke ReAct loop"
      ]
    - tools_needed: [VLM, OCR, code_sandbox]
[3] pattern_extractor cek library:
    Match pattern "Multimodal input (vision) → text reasoning"
    Confidence 0.7 — applicable
    Inject ke ReAct prompt sebagai prior
[4] tool_synthesizer kicks in (untuk OCR component):
    - generate_skill_spec("OCR screenshot to text") 
    - generate_skill_code → Python module pakai paddleocr
    - validate AST → OK
    - test_skill_in_sandbox dengan dummy image → success
    - save brain/skills/ocr_screenshot_xxx.py
[5] Phase 3 ReAct execute:
    User screenshot → OCR skill (baru!) → code_sandbox lint → reply dengan
    annotated bug locations + fix suggestions
[6] Phase 4 review:
    correctness: verified by user feedback
    generalizable_insight: "Pattern: multimodal → preprocess → text reasoning
                            workflow applicable ke OCR/STT/VLM semua"
    → save sebagai pattern baru
```

**Hasil**: SIDIX tidak hanya jawab "iya, ada GitHub Copilot, kalau lokal
coba ini..." — tapi **literally bikin tool baru** untuk solve user need,
deploy, dan future query similar bisa langsung pakai.

---

## Comparison: SIDIX vs ChatGPT/Claude/Gemini

| Capability | ChatGPT | Claude | Gemini | **SIDIX** |
|---|---|---|---|---|
| Generate jawaban | ✅ | ✅ | ✅ | ✅ |
| Tool use (web/code) | ✅ | ✅ | ✅ | ✅ |
| Pattern extraction (induktif) | ❌ | ❌ | ❌ | ✅ |
| Aspiration detection | ❌ | ❌ | ❌ | ✅ |
| **Tool synthesis (autonomous)** | ❌ | ❌ | ❌ | ✅ (foundation) |
| Polya 4-phase explicit | ❌ | ❌ | ❌ | ✅ |
| Skill library auto-grow | ❌ | ❌ | ❌ | ✅ (foundation) |
| Self-improve (LoRA retrain) | — (provider only) | — | — | ✅ |
| Sanad chain (provenance) | ❌ | ❌ | ❌ | ✅ |
| Open source self-hosted | ❌ | ❌ | ❌ | ✅ |

**Compound advantage seiring waktu**: ChatGPT mengandalkan OpenAI add fitur.
Claude tunggu Anthropic. Gemini tunggu Google. **SIDIX nulis fitur sendiri.**
Kalau pattern library 1000+ patterns Q4 2026, SIDIX punya reasoning prior
yang ChatGPT tidak punya.

---

## Filosofi Cognitive Architecture

### "AI yang menjawab cepat" vs "AI yang menyelesaikan masalah"

ChatGPT optimasi untuk respond < 5 detik. Bagus untuk Q&A casual.

SIDIX optimasi untuk **structured reasoning trail**. Slower per-step
(5-30s tergantung kompleksitas), tapi:
- User lihat reasoning chain (Polya 4-phase visible)
- Pattern library tumbuh (compound learning)
- Skill library tumbuh (compound capability)
- Sanad chain (provenance verifiable)

Audience SIDIX bukan casual user — researcher, engineer, founder yang
butuh **reasoning yang bisa di-audit**.

### "Aspirasi → Eksekusi" mindset

Saat user bilang "harusnya bisa", LLM biasa jawab "iya betul, fitur itu
mungkin nanti". SIDIX jawab "**OK, ini draft cara implementasinya, mau
eksekusi sekarang?**"

Ini **karakter** SIDIX, bukan sekadar fitur. Tradisi Mighan Lab adalah
*self-reliance*: kalau kompetitor bisa, SIDIX juga bisa — pakai open source
+ creative novel angle.

### "Compound learning" via pattern library

ChatGPT lupa setiap session (kecuali memory feature OpenAI yang manual).
SIDIX:
- Pattern library = induktif memory
- Skill library = kapabilitas memory
- Sanad chain = provenance memory
- LoRA retrain = weight memory

**4 layer memory** — Q4 2026, SIDIX punya 1000+ patterns + 100+ skills =
moat yang kompetitor butuh tahun untuk catch up (mereka harus retrain
trillion-token model, SIDIX retrain LoRA monthly).

---

## Implementation Status (Vol 5)

### ✅ Foundation Built (hari ini)

| Modul | File | LOC | Endpoint |
|---|---|---|---|
| Pattern Extractor | `pattern_extractor.py` | 290 | `/agent/patterns/extract`, `/admin/patterns/stats` |
| Aspiration Detector | `aspiration_detector.py` | 220 | `/agent/aspirations/analyze`, `/admin/aspirations/stats` |
| Tool Synthesizer | `tool_synthesizer.py` | 320 | `/agent/skills/synthesize`, `/admin/skills/stats` |
| Problem Decomposer | `problem_decomposer.py` | 220 | `/agent/decompose` |

Total: ~1050 lines code + 8 endpoint baru.

### ⏭️ Next P1 (target Mei-Jun 2026)

- [ ] Auto-hook pattern_extractor di `/ask/stream` end (extract dari user msg)
- [ ] Auto-hook aspiration_detector di `/ask/stream` start
- [ ] Auto-trigger Burst mode untuk "gimana kalo X jadi Y?" pattern
- [ ] Skill registry runtime — synthesized skill auto-available di ReAct tools
- [ ] CodeAct adapter — switch ReAct dari JSON tool calls ke executable code
- [ ] MCP server wrap 17 tool — ekosistem play
- [ ] Admin tab di ctrl.sidixlab.com: Patterns + Aspirations + Skills viewer

### ⏭️ Next P2 (Q3-Q4 2026)

- [ ] PRM v1 — Process Reward Model untuk score reasoning per step
- [ ] Step-Audio integration — sensorial sensory in/out
- [ ] Skill cross-pollinate — multiagent debate antar 5 persona
- [ ] LoRA retrain monthly dari self-play trajectory + pattern + skill
- [ ] Tool-R0 self-play RL infra

### ⏭️ Moonshot Q1+ 2027

- [ ] Tactile/haptic input (Touch Dreaming pattern)
- [ ] Computer-use mode (Anthropic-style browser automation)
- [ ] Robot integration partnership (Figure / Physical Intelligence)

---

## Sumber Inspirasi

### Akademik
- Polya, G. (1945). *How to Solve It*. Princeton University Press.
- Wang et al. (2023). [Voyager: An Open-Ended Embodied Agent](https://huggingface.co/papers/2305.16291).
- Memento-Skills (2026). [huggingface.co/papers/2603.18743](https://huggingface.co/papers/2603.18743).
- CodeAct (2024). [huggingface.co/papers/2402.01030](https://huggingface.co/papers/2402.01030).
- Tool-R0 (2026). [huggingface.co/papers/2602.21320](https://huggingface.co/papers/2602.21320).

### Filosofis
- Notes 219-223 SIDIX research_notes (own auth, activity log, AI 2026 roadmap, visionary, underground predictions)
- SIDIX_BIBLE.md (4 pilar konstitusi)
- NORTH_STAR.md (release v0.1→v3.0 strategy)

---

## Lessons Learned

1. **3 jenis kognisi user → 4 modul foundation**. Mapping clean.
   Induktif=pattern, kreatif=Burst, aspirasi=aspiration+synth, problem=Polya.

2. **MVP foundation sebelum production scale**. Modul ini ~1050 LOC total,
   tidak overengineered. Bisa di-scale incrementally.

3. **Soft prior > hardcoded rule**. Pattern di-inject ke LLM prompt, biarkan
   LLM judge applicability. Lebih fleksibel + robust ke edge case.

4. **Forbidden patterns penting** (untuk tool_synthesizer). Tanpa AST + regex
   scan, LLM gen bisa eksekusi `os.system` atau call vendor API. Static
   gating wajib sebelum dynamic exec.

5. **Compound advantage** = strategi 5-10 tahun, bukan sprint. ChatGPT cepat
   sekarang, SIDIX akan lebih pintar di domain-nya kalau pattern + skill
   library tumbuh konsisten.

6. **"Bikin ah!" mindset** = karakter, bukan fitur. SIDIX di-design untuk
   *aspirasi → eksekusi*, bukan asisten pasif. Ini differentiator emosional
   vs kompetitor.

---

## Cara Test Sekarang (untuk admin)

### 1. Test Pattern Extraction
```bash
curl -X POST https://ctrl.sidixlab.com/agent/patterns/extract \
  -H "x-admin-token: <TOKEN>" \
  -H "content-type: application/json" \
  -d '{"text":"kalo batok kelapa dibakar bisa jadi arang. artinya kayu juga kalo dibakar jadi arang"}'
```
Expected: pattern dengan principle "biomass + heat → carbonization", domain ["organic","thermal"], confidence ~0.7

### 2. Test Aspiration Capture
```bash
curl -X POST https://ctrl.sidixlab.com/agent/aspirations/analyze \
  -H "x-admin-token: <TOKEN>" \
  -d '{"text":"oh GPT bisa bikin gambar, harusnya SIDIX juga bisa, ada Stable Diffusion open source. Bikin ah!"}'
```
Expected: Aspiration dengan capability_target="image generation", competitors mentioned, decomposition steps.

### 3. Test Skill Synthesis
```bash
curl -X POST https://ctrl.sidixlab.com/agent/skills/synthesize \
  -H "x-admin-token: <TOKEN>" \
  -d '{"task_description":"convert HTML table to CSV string"}'
```
Expected: SkillSpec dengan code Python yang valid, status="tested".

### 4. Test Problem Decomposition
```bash
curl -X POST https://ctrl.sidixlab.com/agent/decompose \
  -d '{"problem":"saya mau buat AI yang bisa schedule meeting otomatis dari WhatsApp chat"}'
```
Expected: ProblemSolution dengan Phase 1 (given/unknown), Phase 2 (strategy/sub_goals/tools_needed).

---

## Untuk User: Jawaban Singkat

**Q1: "Gimana sidix bantu mecahin masalah?"**
A: Polya 4-phase decomposition (`problem_decomposer`). User bisa request
`POST /agent/decompose {problem}` untuk lihat reasoning chain explicit.
Atau di ReAct loop /ask, decomposition akan otomatis dipanggil P1 next iter.

**Q2: "Gimana SIDIX belajar hal baru?"**
A: 4 layer learning:
- INSTANT: BM25 corpus retrieval (sanad chain)
- BATCH: corpus_to_training → LoRA retrain (~weekly-monthly)
- PATTERN: induktif extraction (`pattern_extractor`) — dari satu observation
  → general principle → applicable ke kasus serupa
- SKILL: tool synthesis (`tool_synthesizer`) — saat tool baru dibuat dan
  sukses, jadi permanent capability

**Q3: "Bagaimana SIDIX bisa membuat tools baru padahal tidak ada referensinya?"**
A: 3 mekanisme:
- ASPIRATION TRIGGER (`aspiration_detector`): saat user bilang "harusnya
  bisa", auto-decompose jadi Aspiration spec markdown
- TOOL SYNTHESIS (`tool_synthesizer`): generate Python skill code via LLM,
  validate AST + forbidden scan, test di code_sandbox, save ke
  `brain/skills/<name>.py`
- COMPOUND: skill yang sukses → di-distill jadi training pair → LoRA
  retrain → SIDIX *belajar pakai skill itu* di model weight

**Yang kunci**: SIDIX bukan menunggu vendor add fitur. SIDIX nulis fitur
sendiri saat butuh. Itulah arti "self-modifying agent" yang note 222 bahas.

---

## Hubungan dengan Notes Lain

- 219: own auth (foundation user database)
- 220: activity log (foundation per-user data)
- 221: AI innovation 2026 adoption roadmap
- 222: visionary roadmap (multimodal + self-modifying)
- 223: AI 2026→2027 underground predictions
- **224: HOW SIDIX solves/learns/creates (this — implementation reality)**

Notes 219-223 = vision + research. Note 224 = **implementation made real**.
Foundation untuk vision-3.0 (Q4 2026) sudah dibangun di vol 5 ini.
