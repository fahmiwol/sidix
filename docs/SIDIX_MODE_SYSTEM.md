# SIDIX Mode System — Instant · Thinking · Agent · Deep Research
**Version:** 1.0  
**Status:** Spec Approved for Implementation  
**Date:** 2026-05-07  
**Adopted from:** Kimi K2.5 (Instant/Thinking/Agent/Agent Swarm) + ChatGPT (o3-pro thinking)

---

## 1. OVERVIEW

Mode System mengontrol **depth, tool usage, persona activation, dan latency** dari setiap interaksi SIDIX.  
Inspirasi: Kimi K2.5 punya 4 mode (Instant/Thinking/Agent/Agent Swarm). ChatGPT punya model picker (GPT-4o/o3-pro).  
SIDIX punya 4 mode yang selaras dengan visi chain: **Instant → Thinking → Agent → Deep Research**.

---

## 2. MODE SPECIFICATIONS

### MODE 1: INSTANT ⚡

**Target:** Jawaban cepat < 2 detik. No tool calls. Direct LLM response.

**Use cases:**
- Greeting, small talk, clarify question
- Factual recall dari working memory
- Simple math, date/time, conversion
- "Halo", "Terima kasih", "Apa kabar?"

**Config:**
```python
{
  "max_tokens": 350,
  "temperature": 0.7,
  "tools": [],
  "persona": "AYMAN",  # default friendly
  "iterations": 0,
  "web_search": False,
  "corpus_search": False,
  "persona_fanout": False,
  "streaming": True,
  "sanad_required": False
}
```

**Backend path:** `chat_holistic` → skip orchestrator → direct LLM → streaming

**UI indicator:** ⚡ icon + blue accent

---

### MODE 2: THINKING 🧠

**Target:** Problem solving dengan reasoning. 5–30 detik. Selected tools.

**Use cases:**
- Coding problem, math complex
- Analysis single-dimension
- Explain concept
- "Jelaskan cara kerja transformer"

**Config:**
```python
{
  "max_tokens": 800,
  "temperature": 0.5,
  "tools": ["code_sandbox", "calculator", "search_corpus"],
  "persona": "Auto-detect",  # dari query classifier
  "iterations": 3,
  "web_search": False,  # corpus only
  "corpus_search": True,
  "persona_fanout": False,
  "streaming": True,
  "sanad_required": True
}
```

**Backend path:** `agent_react` → tool calls → reasoning trace → synthesis

**UI indicator:** 🧠 icon + purple accent

**Persona auto-detect:**
- Code query → ABOO
- Creative query → UTZ
- Business query → OOMAR
- Research query → ALEY
- General → AYMAN

---

### MODE 3: AGENT 🤖 (DEFAULT)

**Target:** Jurus Seribu Bayangan — full parallel multi-source. 30–120 detik.

**Use cases:**
- Research topic baru
- Compare multiple options
- Creative generation (logo, copy, naming)
- Multi-perspective analysis
- "Bandingkan 3 strategi marketing untuk UMKM"

**Config:**
```python
{
  "max_tokens": 1200,
  "temperature": 0.7,
  "tools": ["web_search", "web_fetch", "search_corpus", "code_sandbox", 
            "calculator", "pdf_extract", "workspace_*", "roadmap_*"],
  "persona": "All 5 (fanout)",
  "iterations": 5,
  "web_search": True,
  "corpus_search": True,
  "dense_search": True,
  "persona_fanout": True,  # UTZ/ABOO/OOMAR/ALEY/AYMAN parallel
  "streaming": True,
  "sanad_required": True,
  "output_type_detection": True
}
```

**Backend path:** `multi_source_orchestrator` → parallel sources → `cognitive_synthesizer`

**UI indicator:** 🤖 icon + gold accent (current "Holistic" button)

**Visual feedback:**
```
🔍 Web search... ✓
📚 Corpus search... ✓
🧠 UTZ thinking... ✓
🔧 ABOO thinking... ✓
📊 OOMAR thinking... ✓
🔬 ALEY thinking... ✓
💚 AYMAN thinking... ✓
🔄 Synthesizing...
```

---

### MODE 4: DEEP RESEARCH 🔬

**Target:** Report generation dengan recursive research. 2–10 menit.

**Use cases:**
- Comprehensive literature review
- Market analysis report
- Due diligence
- "Buatkan laporan lengkap tentang AI di Indonesia 2026"

**Config:**
```python
{
  "max_tokens": 2000,
  "temperature": 0.3,
  "tools": ["web_search", "web_fetch", "search_corpus", "code_sandbox",
            "arxiv_search", "github_search", "wikipedia_search", "pdf_extract"],
  "persona": "ALEY-led + All 5",
  "iterations": 10,
  "web_search": True,
  "corpus_search": True,
  "dense_search": True,
  "persona_fanout": True,
  "recursive_research": True,  # follow links, expand sub-topics
  "streaming": False,  # batch, then deliver
  "sanad_required": True,
  "output_type": "structured",  # markdown report with TOC
  "citation_format": "APA-style"
}
```

**Backend path:**
```
Planner → Research (recursive) → Fact Extraction → Synthesis
   ↑_________________________________________________↓
              (iterative expansion)
```

**UI indicator:** 🔬 icon + deep red accent

**Output format:** Structured report dengan:
- Executive Summary
- Methodology
- Findings (with sanad citations)
- Analysis (5 persona perspectives)
- Recommendations
- References

---

## 3. MODE TRANSITIONS

```
User Input
    │
    ▼
[Intent Classifier] ──► Instant? → Mode 1
    │
    ▼ Complex?
[Complexity Estimator]
    │
    ├── Simple + factual → Mode 2 (Thinking)
    ├── Multi-source needed → Mode 3 (Agent) [DEFAULT]
    └── Report/recursive → Mode 4 (Deep Research)
```

**User override:**
- `/instant` — force Mode 1
- `/think` — force Mode 2
- `/agent` — force Mode 3
- `/deep` — force Mode 4

**Auto-escalation:**
- Mode 2 → Mode 3: jika tool calls > 3 atau sanad conflict
- Mode 3 → Mode 4: jika user minta "laporan", "analisis lengkap", "research"

---

## 4. MODE UI SPEC

### Chat Input Area
```
┌─────────────────────────────────────────────────────┐
│ [⚡] [🧠] [🤖] [🔬]  ← Mode toggle (icon buttons)   │
│                                                     │
│ ┌──────────────────────────────────────────────┐   │
│ │  Ketik pesan Anda...                         │   │
│ │                                              │   │
│ └──────────────────────────────────────────────┘   │
│ [📎] [🎤] [📷]  ← Attachment, voice, image        │
└─────────────────────────────────────────────────────┘
```

### Mode Badge (per message)
- Setiap bubble chat menunjukkan mode yang digunakan
- Hover → show tool calls count + latency + sources

### Mode Description (Help Modal)
| Mode | Deskripsi ID | Deskripsi EN |
|---|---|---|
| Instant | "Jawaban cepat untuk pertanyaan sederhana" | "Quick answers for simple questions" |
| Thinking | "Berpikir mendalam untuk problem solving" | "Deep thinking for problem solving" |
| Agent | "Mengerahkan semua resource secara paralel" | "Deploy all resources in parallel" |
| Deep Research | "Riset komprehensif dengan laporan lengkap" | "Comprehensive research with full report" |

---

## 5. BACKEND IMPLEMENTATION

### Mode Router (new file: `mode_router.py`)

```python
class ModeRouter:
    MODES = {
        "instant": InstantMode,
        "thinking": ThinkingMode,
        "agent": AgentMode,
        "deep_research": DeepResearchMode,
    }
    
    def classify(self, query: str, context: dict) -> str:
        """Auto-detect mode dari query."""
        # Keyword-based + LLM classifier (lightweight)
        if self._is_greeting(query): return "instant"
        if self._is_report_request(query): return "deep_research"
        if self._is_simple_factual(query): return "thinking"
        return "agent"  # default
    
    def execute(self, mode: str, state: ADOState) -> ADOResponse:
        handler = self.MODES[mode](state)
        return handler.run()
```

### Integration dengan ADOState

`ADOState` sudah punya field:
- `persona_mode` → rename ke `mode`
- `persona_selected` → tetap ada untuk single-persona override
- Tambah field: `recursive_research`, `citation_format`

---

## 6. BENCHMARKING PER MODE

| Metric | Instant | Thinking | Agent | Deep Research |
|---|---|---|---|---|
| Latency P95 | < 2s | < 30s | < 120s | < 10 min |
| Token avg | 350 | 800 | 1200 | 2000 |
| Tool calls avg | 0 | 2 | 8 | 15 |
| Source count | 0 | 1–2 | 4–6 | 10+ |
| Sanad score target | — | > 6.0 | > 7.0 | > 8.0 |
| Cost (inference) | 1x | 2x | 5x | 10x |

---

*Document version: 1.0 | Adopted from Kimi K2.5 mode system + ChatGPT model picker | Author: Claude Code*