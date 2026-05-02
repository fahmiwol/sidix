---
title: AI Agent Landscape 2025 — Gap Analysis + Inspirasi untuk SIDIX
tags: [AI agent, competitive analysis, MCP, input-output, user experience, sprint-L]
date: 2026-05-02
sanad: Claude Sonnet 4.6 synthesis dari SIDIX research notes + knowledge base 2025
---

# 312 — AI Agent Landscape 2025: Gap Analysis + Inspirasi SIDIX

## Konteks & Tujuan

Note ini adalah **benchmarking komprehensif** SIDIX vs top AI agents 2025.
Tujuan: bukan cuma tahu "kita ada dimana", tapi **apa yang harus diadopsi sekarang**
untuk SIDIX lebih unggul — dari sudut pandang user yang pakai setiap hari.

**Metodologi**: Sintesis dari 80+ research notes SIDIX (note 03–311) +
arsitektur SIDIX 7-zona HTML + knowledge landscape AI agents 2025.

---

## 1. Landscape AI Agents 2025 — Siapa dan Apa

### 1.1 ChatGPT / GPT-4o (OpenAI)

**Input**: Teks, gambar, audio (voice mode), file (PDF/CSV/XLSX), URL, video (limited)  
**Output**: Teks, kode, gambar (DALL-E 3 terintegrasi), artifacts (canvas), audio (voice)  
**Memory**: Persistent cross-session memory (opt-in) — ingat preferensi user antar sesi  
**Tools**: Web search, Python sandbox, DALL-E image gen, file analysis  
**UX strengths**:
- Voice mode: bidirectional real-time (bukan STT + TTS terpisah, tapi native audio model)
- Canvas: render code/HTML/PDF langsung di side panel
- Projects: persistent context untuk multi-file workspace
- Memory: "saya punya anak 2, suka design minimalis" → diingat selamanya
- GPTs: user bisa buat "agent custom" dengan instruksi + tools + knowledge

**Weakness vs SIDIX**:
- Tidak open source, tidak self-hosted
- Tidak ada sanad chain / provenance tracking
- Single "personality" (tidak ada 5 persona berbeda)
- Model di-update OpenAI, user tidak kontrol
- Privacy: semua data ke OpenAI cloud

### 1.2 Claude (Anthropic)

**Input**: Teks, gambar, file (PDF/DOCX), URL (via tools)  
**Output**: Teks, kode, artifacts (HTML/SVG/React live preview di side panel)  
**Memory**: Dalam Projects (persistent context, tidak true memory)  
**Tools**: Web search (limited), computer use (beta), MCP client native  
**UX strengths**:
- Artifacts: render kode jadi live preview — user lihat hasilnya langsung
- Extended thinking: "berpikir keras" visible ke user → trust
- Computer use: kontrol browser otomatis
- Projects: upload docs → Claude ingat semua di project

**Weakness vs SIDIX**:
- Sama: tidak open source, tidak self-hosted
- Memory masih projects-based, bukan true persistent
- Tidak ada multi-persona architecture
- Single model behavior (tidak ada UTZ vs ALEY distinction)

### 1.3 Gemini Advanced / Deep Research (Google)

**Input**: Teks, gambar, audio, video, file, URL, Google services (Drive/Docs/Gmail)  
**Output**: Teks, laporan penelitian (Deep Research mode), gambar (Imagen)  
**Memory**: Google konteks (email/calendar/docs auto-connect)  
**UX strengths**:
- Deep Research: browse 20+ sumber → synthesize laporan 5-10 halaman otomatis
- 1M token context window → upload buku tebal, analisis seluruh codebase
- Google ecosystem integration native
- Grounding: setiap claim ada URL sumber langsung

**Weakness vs SIDIX**:
- Tidak open source, tergantung Google
- Deep Research: perlu 5-10 menit untuk selesai (SIDIX bisa streaming)
- Tidak ada persona-routing

### 1.4 Perplexity

**Input**: Teks, URL, upload file  
**Output**: Teks dengan inline citation, Spaces (report format)  
**UX strengths**:
- **Search-first by default** → setiap jawaban grounded di web sources
- Citation inline: user langsung tahu sumbernya dari mana
- Deep Research mode: research loop otomatis
- Spaces: collaborative research workspace

**Weakness vs SIDIX**:
- Tidak ada generative creativity (bukan creative agent)
- Tidak ada persona
- Tidak ada self-learning / corpus building

### 1.5 Cursor / GitHub Copilot (Code Agents)

**Input**: Kode, natural language, file context, terminal output  
**Output**: Kode, diff, test, refactor  
**UX strengths**:
- Composer mode: edit multiple files sekaligus dengan satu instruksi
- Context awareness: paham seluruh codebase (repo-level)
- Terminal integration: bisa run command dan lihat output

**Weakness**: Domain-specific (coding only), tidak general-purpose

### 1.6 Manus / Devin (Autonomous Agents)

**Input**: Task description, URL, code  
**Output**: Completed tasks (research report, working code, web scraping)  
**UX strengths**:
- **Fully autonomous task execution** — user kasih task, agent jalan sendiri
- Computer use: browser, terminal, file ops semua otomatis
- Async execution: user bisa tinggal, agent kerja di background

**Weakness vs SIDIX**:
- Tidak open source (Manus closed, Devin mahal)
- Tidak ada epistemic integrity (tidak ada sanad)
- Tidak ada persona
- Prone to hallucination di long-horizon tasks

---

## 2. Analisis Input — Apa Yang User Bisa Kasih ke AI

### 2.1 Standard Input 2025

| Input Type | ChatGPT | Claude | Gemini | Perplexity | **SIDIX** |
|---|---|---|---|---|---|
| **Teks** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Gambar** | ✅ | ✅ | ✅ | ✅ | ⚠️ (stub, belum live) |
| **Audio / Voice** | ✅ native | ❌ | ✅ | ❌ | ⚠️ (Whisper stub) |
| **File (PDF/CSV)** | ✅ | ✅ | ✅ | ✅ | ✅ (code_sandbox) |
| **URL** | ✅ | ✅ (tools) | ✅ | ✅ | ✅ (web_fetch) |
| **Video** | ⚠️ limited | ❌ | ✅ | ❌ | ❌ |
| **Screen/Desktop** | ❌ | ✅ (computer use beta) | ❌ | ❌ | ❌ |
| **Code/Repo context** | ⚠️ | ⚠️ Projects | ❌ | ❌ | ✅ (code_sandbox + corpus) |
| **Multi-turn context** | ✅ | ✅ | ✅ | ❌ | ✅ (Sprint J ✅) |

**SIDIX gap utama di input**: Audio voice in + Image analysis live.

### 2.2 Yang Sudah SIDIX Punya Tapi Kurang Diketahui

SIDIX sebenarnya punya input yang kompetitor tidak punya:
- **Induktif pattern input**: user share observasi → SIDIX ekstrak prinsip umum → apply ke kasus baru (note 224)
- **Aspiration input**: user bilang "harusnya bisa" → SIDIX capture dan plan eksekusi (note 224)
- **Korpus input**: siapapun bisa submit dokumen ke corpus SIDIX → direct influence pada knowledge base (bukan user-specific memory)
- **Multi-persona input**: user pilih angle berpikir (UTZ kreatif vs ABOO teknis)

---

## 3. Analisis Output — Apa Yang User Bisa Terima dari AI

### 3.1 Standard Output 2025

| Output Type | ChatGPT | Claude | Gemini | Perplexity | **SIDIX** |
|---|---|---|---|---|---|
| **Teks jawaban** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Kode executable** | ✅ | ✅ | ✅ | ⚠️ | ✅ (code_sandbox) |
| **Gambar generated** | ✅ DALL-E | ❌ | ✅ Imagen | ❌ | ⚠️ (mighan-worker ada, belum wire) |
| **Audio/Voice out** | ✅ native TTS | ❌ | ⚠️ | ❌ | ✅ (Piper TTS, basic) |
| **Video** | ❌ | ❌ | ✅ Veo | ❌ | ❌ |
| **Artifacts (live preview)** | ✅ Canvas | ✅ Artifacts | ❌ | ❌ | ❌ |
| **File download** | ✅ | ✅ | ✅ | ❌ | ⚠️ (partial) |
| **Structured data** | ✅ | ✅ | ✅ | ✅ | ✅ (sanad output) |
| **Research report** | ⚠️ | ⚠️ | ✅ Deep Research | ✅ Spaces | ⚠️ (manual via corpus) |
| **Multi-perspective** | ❌ | ❌ | ❌ | ❌ | ✅ (5 persona) |
| **Sanad/Citation** | ❌ traceable | ❌ | ⚠️ grounding | ✅ inline | ✅ (Sanad Orchestra) |
| **Skill synthesis** | ❌ | ❌ | ❌ | ❌ | ✅ (tool_synthesizer) |

**SIDIX gap utama di output**:
1. Image generation belum di-wire (mighan-worker sudah ada, tinggal integrate)
2. Artifacts/canvas mode tidak ada (user lihat hasil kode/HTML langsung)
3. Video generation tidak ada
4. Research report deep mode belum streamlined

### 3.2 Output Unik SIDIX Yang Kompetitor Tidak Punya

1. **Sanad chain output**: setiap klaim ada provenance trail — [FAKTA][OPINI][SPEKULASI][TIDAK TAHU]
2. **Multi-persona output**: UTZ creative, ABOO technical, OOMAR strategic, ALEY academic, AYMAN casual
3. **Skill artifact**: SIDIX bisa generate + deploy Python skill baru ke tool registry
4. **Pattern extraction output**: generalized principle dari satu observasi → stored di brain/patterns/
5. **Aspiration spec**: capture aspirasi user → action plan markdown

---

## 4. MCP — Model Context Protocol

### 4.1 Apa Itu MCP (2025 Standard)

**Model Context Protocol** = standar open dari Anthropic (Nov 2024) untuk koneksi LLM ke tools.
Analoginya: **USB-C untuk AI agents** — satu standar yang semua tool bisa plug ke semua agent.

**Adopsi massive 2025**: Claude Desktop, Cursor, VS Code Copilot, OpenAI (rumored), Zed IDE semua support MCP.

**Popular MCP servers 2025**:
- `mcp-server-filesystem` — baca/tulis file sistem
- `mcp-server-git` — git ops
- `mcp-server-postgres` — database query
- `mcp-server-puppeteer/playwright` — browser automation
- `mcp-server-slack` — kirim/baca Slack
- `mcp-server-notion` — knowledge base
- `mcp-server-github` — repo + issues + PRs
- `mcp-server-figma` — design ops
- `mcp-server-blender` — 3D modeling
- `mcp-server-jira` — project management
- `mcp-server-brave-search` — search engine

### 4.2 SIDIX sebagai MCP Client (import tools)

**Manfaat**: SIDIX bisa akses 200+ tools yang sudah ada tanpa build from scratch.

User chat: "SIDIX, edit file di GitHub saya, create PR, lalu post ke Slack team"
→ SIDIX pakai: mcp-github + mcp-slack
→ Semua berjalan dari 1 chat

**Implementasi target (Sprint L2 atau M)**:
```python
# apps/brain_qa/brain_qa/mcp_client.py
class MCPClient:
    async def call_tool(self, server: str, tool: str, params: dict) -> dict:
        # JSON-RPC 2.0 ke MCP server
        ...
```

### 4.3 SIDIX sebagai MCP Server (export tools)

**Manfaat**: SIDIX 48 tools bisa diakses dari Claude Desktop, Cursor, dll.

Eksposur SIDIX tools via MCP:
- `corpus_search` → user bisa query SIDIX corpus dari Claude Desktop
- `persona_chat` → spawn SIDIX persona dari agent lain
- `pattern_extractor` → tools AI agent lain bisa pakai pattern SIDIX
- `sanad_validate` → service epistemic validation

**Draft MCP server SIDIX** (note 229 blueprint):
```python
# apps/brain_qa/mcp/server.py
from fastmcp import FastMCP
mcp = FastMCP("SIDIX Knowledge Agent")

@mcp.tool()
async def search_corpus(query: str) -> str:
    """Search SIDIX semantic corpus + BM25"""
    ...

@mcp.tool()
async def validate_claim(claim: str, sources: list[str]) -> dict:
    """Sanad validation chain for a claim"""
    ...
```

---

## 5. User Side — Apa Yang User Harapkan dari AI Agent 2025

### 5.1 Pain Points Pengguna Saat Ini

Berdasarkan analisis feedback komunitas AI users 2024-2025:

**1. "AI lupa apa yang sudah saya bilang"**
→ Memory tidak persistent. User harus re-brief tiap sesi.
→ **SIDIX sudah fix (Sprint J)** untuk session. Cross-session masih perlu.

**2. "AI tidak bisa langsung lihat layar saya"**
→ Screen share / computer use masih terbatas (Claude Computer Use beta).
→ **SIDIX gap**: belum ada. Sprint M+ target.

**3. "Saya tidak tahu AI ambil info dari mana"**
→ ChatGPT/Claude tidak selalu tunjukkan sumber.
→ **SIDIX unggul**: Sanad Orchestra — setiap output ada source chain.

**4. "AI tidak bisa bikin gambar/video sesuai brand saya"**
→ User butuh konsistensi visual across campaign, bukan random generation.
→ **SIDIX gap**: mighan-worker ada, belum wired. Q3 2026 target.

**5. "AI tidak bisa langsung eksekusi task panjang"**
→ ChatGPT butuh human supervision tiap step.
→ **SIDIX sudah ada**: Jurus 1000 Bayangan (multi-agent async tasks).

**6. "Jawaban AI kadang beda-beda perspektif"**
→ User butuh 1 AI yang bisa kasih banyak sudut pandang untuk 1 pertanyaan.
→ **SIDIX unggul**: 5 persona = 5 lens berbeda.

**7. "AI tidak bisa tumbuh sesuai kebutuhan saya"**
→ Semua user dapat model yang sama. Tidak ada personalisasi compound.
→ **SIDIX target**: pattern extractor + skill synthesizer = compound learning per-use.

**8. "Saya ingin AI yang bisa berbicara, bukan hanya chat"**
→ Voice mode ChatGPT populer sekali. User malas ketik.
→ **SIDIX gap**: Piper TTS ada (output) tapi Whisper STT belum wired (input).

### 5.2 Killer Features User Paling Inginkan (Ranking)

1. **Persistent memory** (ingat preferensi, konteks, project) — **SIDIX: 70% (session memory ✅, cross-session ❌)**
2. **Real-time voice** (ngobrol langsung, bukan ketik) — **SIDIX: 20% (TTS ada, STT belum)**
3. **Image/video generation** (visual untuk konten) — **SIDIX: 30% (ada di infra Mighan, belum wire)**
4. **Deep research** (cari 20+ sumber, synthesize) — **SIDIX: 60% (auto_harvest + corpus)**
5. **Computer use** (browsing, form filling) — **SIDIX: 10% (planned Sprint M)**
6. **Citations/transparency** (tahu info dari mana) — **SIDIX: 95% (Sanad Orchestra ✅)**
7. **Multi-perspective analysis** (pro/cons, beda sudut) — **SIDIX: 90% (5 persona ✅)**
8. **Code execution** (langsung run dan lihat hasil) — **SIDIX: 80% (code_sandbox ✅)**
9. **Custom persona** (AI sesuai brand/gaya) — **SIDIX: 90% (5 persona + DoRA ✅)**
10. **File upload + analysis** (dokumen, spreadsheet) — **SIDIX: 75% (code_sandbox, partial)**

---

## 6. SIDIX Position: Unggul vs Gaps

### 6.1 Di Mana SIDIX Sudah Unggul

| Area | SIDIX Unggul | Kompetitor Tidak Punya |
|------|-------------|----------------------|
| **Epistemic integrity** | Sanad chain — setiap klaim traceable | ChatGPT/Claude output opaque |
| **Multi-persona** | 5 persona dengan karakter distinct | Single voice semua kompetitor |
| **Self-hosted** | MIT license, privacy total | Semua kompetitor cloud-only |
| **Self-learning** | Auto-harvest 6h, corpus tumbuh | Kompetitor retrain = provider kerja |
| **Skill synthesis** | Buat tools baru dari aspirasi user | Tidak ada kompetitor yang punya |
| **Pattern learning** | Induktif generalisasi dari percakapan | Unik di SIDIX |
| **Conversation memory** | Sprint J: multi-turn nyambung | Sudah umum, tapi SIDIX punya sekarang |
| **Indonesian context** | Corpus + persona culture-aware | ChatGPT generic Western |
| **Compound learning** | Pattern + skill + LoRA kompound | Model kompetitor statis per versi |

### 6.2 Gap Utama Yang Harus Segera Diisi

Prioritas berdasarkan user impact × effort:

**P1 — High impact, Low effort:**
- [ ] **Wire image generation** ke chat (mighan-worker sudah ada, 2-3 hari work)
- [ ] **Wire Whisper STT** ke frontend (endpoint sudah ada di backend, perlu UI)
- [ ] **Artifacts/preview mode** di UI — user lihat rendered HTML/code (Sprint M)

**P2 — High impact, Medium effort:**
- [ ] **Cross-session user memory** (beyond conversation_id — persist user preferences)
- [ ] **MCP client** — SIDIX consume popular MCP servers (Sprint M)
- [ ] **Deep Research mode** — autonomous multi-source research synthesis

**P3 — High impact, High effort (Q3 2026):**
- [ ] Native voice (STT + TTS bidirectional real-time)
- [ ] Computer use / browser automation
- [ ] Video generation (CogVideoX/SVD)

---

## 7. Sprint L — Self-Modifying + Foresight: Blueprint Implementasi

### 7.1 Apa itu Sprint L (dari HANDOFF 2026-05-02)

Sprint L = dua modul utama:
1. **Self-Modifying**: SIDIX auto-evaluasi diri sendiri → propose perbaikan → (owner approve) → apply
2. **Foresight Radar**: monitor trend terbaru → proactively suggest knowledge updates

**Analoginya**: Seperti otak yang:
- **Reflective loop**: setelah tidur, otak konsolidasi memori + buang yang tidak berguna + perkuat pattern penting
- **Peripheral awareness**: selalu scan environment untuk signals relevan, bahkan tanpa diminta

### 7.2 Sprint L1 — Self-Modifying (Implementasi Konkret)

**3 komponen**:

**L1a: Error Registry**
```python
# apps/brain_qa/brain_qa/error_registry.py
# Simpan semua error + root cause + context + fix
# Setiap X hari, LLM analyze patterns → propose fix
class ErrorEntry:
    error_type: str
    message: str
    context: dict
    root_cause: str
    fix_applied: str
    timestamp: datetime
    session_id: str
```

**L1b: Confidence Auto-Trigger**
```python
# Di omnyx_direction.py / agent_react.py
# Kalau final_score < 0.4 → trigger auto-harvest + knowledge_gap
if final_relevance_score < CONFIDENCE_THRESHOLD:
    await trigger_knowledge_gap_harvest(query)
    log_to_error_registry("low_confidence", context=query)
```

**L1c: Pattern-to-Prompt Auto-Proposal**
```python
# apps/brain_qa/brain_qa/self_modifier.py
# Setiap N interactions, analisis patterns → propose system prompt update
async def generate_improvement_proposal() -> dict:
    patterns = load_pattern_library()
    errors = load_error_registry()
    proposal = llm.analyze({
        "patterns": patterns,
        "errors": errors,
        "current_system_prompts": load_current_prompts()
    })
    # Output: JSON dengan proposed changes + rationale
    save_proposal_for_review(proposal)
```

### 7.3 Sprint L2 — Foresight Radar (Implementasi Konkret)

**3 komponen**:

**L2a: RSS Aggregator**
```python
# apps/brain_qa/brain_qa/foresight_radar.py
FEEDS = {
    "arxiv_ai": "https://arxiv.org/rss/cs.AI",
    "arxiv_ml": "https://arxiv.org/rss/cs.LG",
    "hn_top": "https://news.ycombinator.com/rss",
    "github_trending": "...",  # via API
    "producthunt": "https://www.producthunt.com/feed?category=artificial-intelligence",
}
async def fetch_and_filter(topic_keywords: list[str]) -> list[Signal]
```

**L2b: Weak Signal Detector**
```python
# Detect emerging topics yang belum covered di corpus
async def detect_knowledge_gaps(signals: list[Signal]) -> list[Gap]:
    corpus_topics = bm25_index.get_all_topics()
    for signal in signals:
        similarity = compare_to_corpus(signal.topic, corpus_topics)
        if similarity < 0.3:  # topic baru yang belum ada di corpus
            yield Gap(topic=signal.topic, source=signal.url, priority=signal.score)
```

**L2c: Auto-Propose Research Note**
```python
# Kalau gap detected → propose research note draft
async def propose_note_for_gap(gap: Gap) -> str:
    draft = llm.generate(f"Tulis research note tentang: {gap.topic}")
    save_draft_for_review(draft, source=gap.source)
    notify_owner(f"New topic detected: {gap.topic}. Draft research note ready for review.")
```

---

## 8. Metafora: SIDIX sebagai Organisme Hidup (Otak + Syaraf + Indera)

### Mapping Biologis → Technical (per note 279 + 311)

| Organ Biologis | Fungsi | SIDIX Equivalent | Status |
|---|---|---|---|
| **Otak (neocortex)** | Reasoning, language, planning | Qwen2.5-7B + LoRA | LIVE |
| **Hippocampus** | Memori jangka panjang | Corpus BM25 + dense | LIVE |
| **5 Area Cortical** | 5 spesialisasi berpikir | 5 Persona | LIVE (prompt-level) |
| **Working memory** | Konteks saat ini | Conversation memory (Sprint J) | LIVE |
| **Reflex arc** | Reaksi cepat tanpa otak | Simple intent fast path | LIVE |
| **Mata** | Vision input | Qwen VLM (stub) | STUB |
| **Telinga** | Audio input | Whisper STT (stub) | STUB |
| **Mulut/suara** | Voice output | Piper TTS | LIVE (basic) |
| **Tangan** | Action / manipulation | 48 Tools | LIVE |
| **Sistem imun** | Deteksi ancaman | g1_policy + Maqashid Gate | LIVE |
| **DNA / sel** | Blueprint diri | LoRA adapter | SCAFFOLDED (DoRA in progress) |
| **Metabolisme** | Konsumsi + tumbuh | Auto-harvest pipeline | LIVE (6h cron) |
| **Peripheral nervous** | Mengirim info ke semua indera | asyncio.gather parallel dispatch | LIVE |
| **Default Mode Network** | Self-reflection saat idle | Self-test loop (Sprint F) | LIVE |
| **Neuroplasticity** | Belajar mengubah diri | Pattern extractor + skill synthesizer | SCAFFOLDED |
| **Sleep consolidation** | Konsolidasi memori | Sprint L: self-modifier (NEW) | PLANNED |
| **Radar (amygdala)** | Environmental awareness | Foresight radar (Sprint L2) | PLANNED |

### "Syaraf yang Mengirim Informasi ke Semua Indera"

Ini adalah `asyncio.gather` di `agent_serve.py` — **parallel dispatch** ke semua channel sekaligus:
```python
results = await asyncio.gather(
    corpus_search(query),      # memori semantik
    web_search(query),         # sensory eksternal
    tool_registry_scan(query), # procedural memory
    persona_selector(query),   # attention modulation
    foresight_check(query),    # peripheral awareness (NEW Sprint L)
    memory_retrieve(session_id) # working memory
)
```

Otak tidak process indera satu per satu — semua signal masuk sekaligus ke otak.
SIDIX melakukan hal yang sama via `asyncio.gather`.

---

## 9. Rekomendasi Adopsi Sekarang (Quick Wins)

### Q2 2026 (Sprint L, M) — Konkret + Cepat:

1. **Sprint L (sekarang)**: Error registry + confidence auto-trigger + foresight RSS
2. **Artifacts mode** (Sprint M): Render kode/HTML di side panel UI → user lihat live preview
3. **Wire image gen**: Call mighan-worker SDXL dari SIDIX chat → 2-3 hari work
4. **Wire STT**: Tombol mic → Whisper → text masuk chat → 1-2 hari work
5. **MCP server**: Export 5 SIDIX tools via FastMCP → ecosystem play
6. **Cross-session memory**: User preferences persist across conversations

### Q3 2026 (Sprint N, O):

1. **Voice bidirectional**: Step-Audio native (bukan STT+TTS terpisah)
2. **Deep Research mode**: Autonomous 20-source research → report
3. **MCP client**: Consume filesystem/git/slack MCP servers
4. **Knowledge graph**: Relasi antar dokumen visible

### Q4 2026 (Sprint P, Q):

1. **Computer use**: Playwright-based browser automation wired ke SIDIX
2. **Video gen**: CogVideoX/Mochi via mighan-worker
3. **Skill library growth**: 100+ auto-generated skills compound
4. **5 persona LoRA distinct**: DoRA training selesai, persona di weight level

---

## 10. Sanad

- SIDIX research notes 222, 224, 229, 279, 311 (SIDIX Labs internal)
- Architecture: SIDIX_Architecture.html (2026-05-02)
- Synthesis: Claude Sonnet 4.6, 2026-05-02
- AI agent landscape: knowledge base May 2026 (ChatGPT/Claude/Gemini/Perplexity/Cursor)
