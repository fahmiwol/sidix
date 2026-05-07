# Research Note 318 — SIDIX Cognitive Expansion: Riset-Driven Sprint Batch (2026-05-08)

## TL;DR
- **Screening menyeluruh** 12 sumber riset internal + 8 sumber eksternal (web 2026) menghasilkan **5 sprint kandidat prioritas tinggi** untuk periode 2026-05-08 → 2026-05-21
- **Tren dominan 2026-2027**: self-improving agents (HyperAgents 0.630 vs 0.0 baseline), MCP+A2A dual-stack mature, Active Inference sebagai moat arsitektural, multimodal open-source (Qwen3-VL, Qwen3-TTS, Kokoro)
- **Differentiator SIDIX yang harus diperkuat**: "ChatGPT yang bisa kamu bawa pulang — **self-improving**, anti-halusinasi, 5 persona, self-hosted, Islamic ethical AI"
- **Rekomendasi bos**: Jalankan 5 sprint sekaligus (parallel batch) — Input Expansion + Orchestration Polish + Skill Library P3 + Output Modality Wire + Built-in Apps Enhance

---

## 1. Landscape Analysis — Apa yang Terjadi 2025-2026

### 1.1 Self-Improving Agents: Dari Voyager ke HyperAgents
| Milestone | Detail | Relevansi SIDIX |
|---|---|---|
| Voyager (NVIDIA, 2023) | Skill library pertama di Minecraft | ✅ SIDIX sudah punya Voyager Protocol P2 |
| SWE-RL (Meta, Dec 2025) | Self-play bug injector/solver, +10.4 SWE-bench | ⏳ Roadmap Q3 2026 |
| HyperAgents (Meta+Oxford+NYU, Mar 2026) | Self-improvement cross-domain, 0.630 vs 0.0 baseline | 🔥 **HIGHEST PRIORITY** — adapt pattern |
| SAGE (Dec 2025→Mar 2026) | Skill Augmented GRPO, +8.9% completion, -59% tokens | ✅ Voyager P2 sudah kompatibel |
| Anthropic Agent Skills (Dec 2025) | Open standard, adopted Microsoft/OpenAI/Figma/Cursor | ✅ SIDIX P2 sudah output Agent Skills format |

**Lesson**: Agent yang tidak self-improve akan menjadi "static tier" yang terkomoditisasi. Learning agents akan command premium pricing. SIDIX harus accelerate Voyager P3 (tool composition) + Maqashid P3 (eval dataset auto-build).

### 1.2 Protocol Maturity: MCP + A2A = De Facto Standard
| Protocol | Status April 2026 | SIDIX Status |
|---|---|---|
| MCP | 18,000+ servers, 97M monthly SDK downloads, Linux Foundation | ✅ stdio transport LIVE, Streamable HTTP queued |
| A2A v1.0.0 | Google, Linux Foundation, 150 org adoption | ✅ Phase 2-3 LIVE (A2AServer + A2AClient) |
| Streamable HTTP | Production-ready, stateless multi-instance | ⏳ Protocol Polish sprint queued |
| MCP Apps (SEP-1865) | Interactive UI in AI clients (Jan 2026) | ⏳ Not yet — product layer gap |

**Lesson**: "The winner is not a single protocol — it is the layered ecosystem." SIDIX sudah dual-protocol = ahead of curve. Next: Streamable HTTP + MCP Server Card discovery.

### 1.3 Active Inference / Free Energy Principle — Moat Arsitektural
- **VERSES Genius**: 140× faster, 5,260× cheaper than o1-preview di Mastermind
- **Bert de Vries (TU Eindhoven, Mar 2026)**: Engineering blueprint comprehensive untuk Physical AI Agents
- **DeepMind 2024 theorem**: "Any agent capable of adapting to a sufficiently large set of distributional shifts must have learned a causal model"
- **Causal AI**: 74% faithfulness gap di LLM/CoT/RAG — Causal AI = syarat untuk adaptive agent

**Lesson**: Active Inference + Causal AI = diferensiasi 5+ tahun. TIDAK bisa dicapai dengan scaling LLM saja. SIDIX harus punya blueprint minimal (pymdp/RxInfer.jl integration) untuk klaim valid.

### 1.4 Multimodal Open Source 2026 — Self-Hosted Parity
| Modality | Model Terbaik (Self-Hosted) | Status SIDIX |
|---|---|---|
| Vision | Qwen3-VL (97.1% DocVQA), DeepSeek-VL2 | ⏳ Belum deploy |
| TTS | Qwen3-TTS (97ms, voice cloning), Kokoro (82M, edge), Piper | ⏳ audio_capability.py ada, belum wired |
| ASR | Whisper.cpp (CPU), Deepgram (API fallback not allowed) | ⏳ Belum deploy |
| Image Gen | SDXL/FLUX (RTX 3060 6GB 97s/image) ✅ | ✅ Sprint 3 DONE |
| Video Gen | Wan 2.1 (OSS), HunyuanVideo (Tencent OSS) | ⏳ Not yet |
| 3D Gen | Hunyuan3D, Tripo AI bridge | ⏳ Sprint 6 planned |

**Lesson**: Open-source multimodal sudah sangat kompetitif. SIDIX bisa achieve parity tanpa vendor API — asal deploy VLM + TTS + ASR.

### 1.5 Agency > Intelligence — Metrik Baru 2026
> "The industry will stop obsessing over raw intelligence scores. Agency will eclipse intelligence as the primary metric."
> — Ken Huang, CEO DistributedApps.ai, Jan 2026

**Agency = plan + use tools + persist toward goal**. Ini validate arsitektur SIDIX (ReAct + tools + persona + memory) sebagai arah yang benar.

---

## 2. Gap Analysis — SIDIX vs Frontier 2026

### 2.1 Dimensi Input (Jenis Input)
| Input Type | Status | Gap |
|---|---|---|
| Text | ✅ FULL | — |
| Image upload + vision analysis | ⚠️ PARTIAL (upload endpoint ada, VLM belum) | Butuh Qwen3-VL deploy |
| Audio upload (ASR) | ⚠️ PARTIAL (endpoint ada, Whisper belum) | Butuh Whisper.cpp deploy |
| Voice chat (realtime) | ❌ NOT YET | Butuh STT + TTS + WebRTC pipeline |
| Document upload (PDF/Word/Excel) | ⚠️ PARTIAL (PDF only, Word/Excel belum) | Butuh python-docx / openpyxl |
| Structured data (CSV/JSON/URL feed) | ❌ NOT YET | Butuh parser + validation |
| Web page (URL fetch) | ✅ FULL | — |
| Screen sharing / computer use | ❌ NOT YET | Butuh VLM + desktop capture |

**Gap Score: 3/8 fully covered (37.5%)**

### 2.2 Dimensi Orkestrasi (Tools Orkestrasi)
| Orchestration Layer | Status | Gap |
|---|---|---|
| ReAct single-agent | ✅ FULL | — |
| Multi-source parallel (jurus seribu bayangan) | ✅ FULL | — |
| Raudah multi-agent DAG | ✅ FULL v0.2 | — |
| MCP server (tool exposure) | ⚠️ PARTIAL (stdio only) | Butuh Streamable HTTP + Server Card |
| A2A peer (agent collaboration) | ✅ Phase 2-3 | — |
| Agent spawning (sub-agent) | ✅ DONE (Fase V) | — |
| Dynamic tool creation (Voyager) | ✅ P2 | Butuh P3 (tool composition) |
| Active Inference loop | ❌ NOT YET | Butuh pymdp integration |
| Causal reasoning module | ❌ NOT YET | Butuh DoWhy + SCM layer |

**Gap Score: 6/9 fully covered (66.7%)**

### 2.3 Dimensi Metode Olah Data / Sintesis / Belajar / MCP
| Method | Status | Gap |
|---|---|---|
| BM25 + sanad rerank | ✅ FULL | — |
| Semantic embedding (MiniLM) | ✅ FULL | Butuh BGE-M3 rebuild |
| Dense hybrid search | ⚠️ DIM MISMATCH | Butuh rebuild index |
| Self-train pipeline (curator → JSONL) | ✅ Fase 1 | Butuh Kaggle auto-retrain |
| Skill library (Voyager) | ✅ P2 | Butuh P3 (composition) |
| Trace-aware evaluation (Maqashid) | ✅ P2 | Butuh P3 (dataset auto-build) |
| Feedback calibration (HistoricalJudge) | ✅ P2 | Butuh ML-based (Phase 3) |
| Memory tiers (Working/Episodic/Semantic) | ⚠️ SPEC DONE | Butuh PostgreSQL + Qdrant deploy |
| MCP full transport + registry | ⚠️ PARTIAL | Butuh Streamable HTTP skeleton |
| Causal graph (DoWhy) | ❌ NOT YET | Blueprint only |

**Gap Score: 5/10 fully covered (50%)**

### 2.4 Dimensi Output
| Output Type | Status | Gap |
|---|---|---|
| Text / chat | ✅ FULL | — |
| Code / script | ✅ FULL | — |
| Image prompt (creative) | ✅ FULL | — |
| Image actual (SDXL/FLUX) | ✅ FULL | — |
| Audio TTS | ⚠️ SPEC + registry | Butuh actual deployment |
| Video storyboard | ⚠️ TEXT-ONLY | Butuh actual gen pipeline |
| 3D prompt / mesh | ⚠️ TEXT-ONLY | Butuh Mighan-3D bridge |
| Structured data (table/JSON) | ✅ FULL | — |
| Document (PDF/DOCX export) | ❌ NOT YET | Butuh report generator |
| Interactive artifact (Canvas/Studio) | ✅ MVP | Butuh enhance |

**Gap Score: 5/10 fully covered (50%)**

### 2.5 Dimensi Built-in Tools / Apps
| App / Tool | Status | Gap |
|---|---|---|
| Code Canvas (editor + run) | ✅ MVP | Butuh enhance (lint, debug, preview) |
| Document Studio (TipTap) | ✅ MVP | Butuh enhance (export, collaboration) |
| Data Notebook (ECharts) | ✅ MVP | Butuh enhance (more chart types) |
| Image Studio | ❌ NOT YET | Butuh integrate text_to_image |
| Audio Studio | ❌ NOT YET | Butuh TTS + voice clone |
| Video Studio | ❌ NOT YET | Butuh storyboard + gen |
| 3D Studio | ❌ NOT YET | Butuh Mighan-3D bridge |
| Project / file organization | ❌ NOT YET | Chat + file threads |
| Agent marketplace / skill store | ❌ NOT YET | Voyager skill library UI |

**Gap Score: 3/10 fully covered (30%)**

---

## 3. Sprint Batch Rekomendasi — 5 Sprint Paralel

### Sprint 1: INPUT EXPANSION (Jenis Input)
**Visi mapping**: Cognitive & Semantic + Product
**Deliverable**:
1. Deploy Qwen3-VL untuk vision analysis (`/upload/image` → actual VLM inference)
2. Deploy Whisper.cpp untuk ASR (`/upload/audio` → actual transcription)
3. Deploy Qwen3-TTS / Kokoro untuk TTS output (self-hosted, no API)
4. Add Word/Excel parser (`python-docx`, `openpyxl`)
5. Add CSV/JSON structured data ingestion endpoint
**Acceptance**: 7/8 input types functional (kecuali screen sharing)
**Effort**: 2-3 session
**Risk**: GPU memory — Qwen3-VL + Qwen2.5-7B + TTS butuh VRAM management

### Sprint 2: ORKESTRASI POLISH (MCP Streamable HTTP + A2A v0.3)
**Visi mapping**: Genius + Cognitive
**Deliverable**:
1. MCP Streamable HTTP transport skeleton (`mcp_server_wrap.py` enhancement)
2. MCP Server Card discovery endpoint (`/.well-known/mcp-server-card.json`)
3. A2A v0.3 compatibility (signed Agent Cards, push notifications)
4. Protocol observability (audit trail per tool call)
**Acceptance**: MCP server callable dari Claude Desktop / Cursor via HTTP
**Effort**: 1-2 session
**Risk**: OAuth 2.1 complexity — defer ke Sprint 10

### Sprint 3: METODE & BELAJAR (Voyager P3 + Maqashid P3 + Memory Tier)
**Visi mapping**: Tumbuh + Iteratif + Cognitive
**Deliverable**:
1. Voyager P3 — Tool Composition: tools calling other tools, nested execution
2. Maqashid P3 — Eval dataset auto-build dari feedback history → JSONL training data
3. Memory Tier Phase 1 — PostgreSQL + pgvector deploy untuk Episodic memory
4. BGE-M3 dense index rebuild (1024-dim hybrid dense+BM25+RRF)
**Acceptance**: 
- Tool composition functional (≥2 composed tools)
- Eval dataset auto-generated ≥50 pairs dari feedback
- Episodic memory persistent across sessions
**Effort**: 3-4 session
**Risk**: Database migration — backup required

### Sprint 4: OUTPUT MODALITY WIRE (Image/Audio/Video/3D Actual)
**Visi mapping**: Pencipta (gap terbesar)
**Deliverable**:
1. Wire `text_to_image` ke chat flow (actual FLUX.1 call, bukan prompt only)
2. Wire TTS ke chat flow (audio attachment auto-play)
3. Wire video storyboard ke Film-Gen pipeline (text → multi-scene → render)
4. Wire 3D prompt ke Mighan-3D bridge (mesh generation)
5. Add PDF/DOCX export untuk Document Studio
**Acceptance**: 5 modality actual (text, image, audio, video, 3D) callable dari chat
**Effort**: 2-3 session
**Risk**: GPU queue management — image gen butuh queue supaya tidak block chat

### Sprint 5: BUILT-IN APPS ENHANCE (Studio Expansion)
**Visi mapping**: Pencipta + Product
**Deliverable**:
1. Image Studio — integrate FLUX.1 dengan prompt enhancement + gallery
2. Audio Studio — TTS + voice clone + music gen (AudioCraft)
3. Project / file organization — chat threads dengan file attachment persist
4. Agent marketplace UI — browse Voyager-generated skills, install/uninstall
5. Code Canvas enhance — lint (ruff), debug (pdb trace), preview (HTML render)
**Acceptance**: 3 studio baru + 2 enhance = 5 app improvements
**Effort**: 3-4 session
**Risk**: Frontend complexity — butuh design system consistency

---

## 4. Evaluasi Dampak, Manfaat, Risiko

### Dampak (Impact)
| Sprint | User Impact | Competitive Impact | Visi Coverage Shift |
|---|---|---|---|
| Input Expansion | User bisa kirim gambar, suara, dokumen | Parity dengan ChatGPT/Kimi | Cognitive +10pp |
| Orchestration Polish | SIDIX bisa dipanggil agent lain via MCP/A2A | B2A2B positioning valid | Genius +5pp |
| Metode & Belajar | Self-improvement loop lengkap | Differentiator vs static agents | Tumbuh +15pp |
| Output Modality | Creative output actual (bukan prompt) | Adobe-of-Indonesia foundation | Pencipta +20pp |
| Built-in Apps | Full workspace parity | Product stickiness | Product +25pp |

### Manfaat (Benefit)
1. **User retention**: Multimodal + studio = stickiness ↑ (target D7 retention 30% → 40%)
2. **Monetization**: TTS + image gen + video = usage-based revenue viable
3. **Differentiation**: Self-improving + Islamic ethical + self-hosted = niche moat
4. **Founder pain reduction**: SIDIX bisa handle lebih banyak input/output types tanpa bos micromanage

### Risiko (Risk)
| Risiko | Probabilitas | Mitigasi |
|---|---|---|
| GPU memory insufficient (VPS 16GB RAM, no GPU) | HIGH | RunPod GPU burst untuk inference berat, CPU-only untuk TTS (Kokoro) |
| Database migration corrupt | MEDIUM | Backup before migrate, dry-run di staging |
| Frontend complexity scope creep | MEDIUM | Strict design system, reusable component library |
| Self-improvement loop runaway | LOW | Human-in-the-loop approval gate, max 3 auto-refinement attempts |
| Quality regression (new modalities) | MEDIUM | CQF gate ≥7.0 untuk semua output baru |

---

## 5. Hipotesis & Benchmarking

### Hipotesis 1: Self-improving loop akan meningkatkan task completion rate
- **Measure**: Task completion rate di `/agent/chat` sebelum vs sesudah Voyager P3
- **Target**: +15% completion rate dalam 2 minggu
- **Validation**: Log `call_count`, `success_rate`, `avg_latency_ms` per tool

### Hipotesis 2: Multimodal input akan meningkatkan engagement
- **Measure**: Messages per session sebelum vs sesudah image/audio upload
- **Target**: +25% messages per session
- **Validation**: Analytics di `/agent/metrics`

### Hipotesis 3: Memory tiers akan meningkatkan coherence lintas sesi
- **Measure**: User satisfaction (thumbs up/down) untuk follow-up questions
- **Target**: +10% thumbs up rate untuk multi-turn conversations
- **Validation**: HistoricalJudge calibration dari feedback

---

## 6. Rencana Adaptasi

### Jika MCP adoption melambat <50% Q4 2026
→ Tetap MCP-first tapi siapkan A2A-only fallback. Dual-stack = hedge.

### Jika reasoning model cost turun 5× lagi (2027)
→ Re-evaluate: apakah Cognitive Kernel masih dibutuhkan, atau langsung raw model? 
→ Jawaban: Cognitive Kernel tetap dibutuhkan karena sanad + IHOS + memory tiers tidak bisa dari raw LLM.

### Jika GPU cost tidak feasible
→ Prioritaskan CPU-friendly models (Kokoro TTS, Whisper.cpp, MiniCPM-V edge).
→ Deferred GPU-intensive (video gen, 3D) ke Q3 2027.

### Jika EU AI Act enforcement keras
→ Tambah governance layer (Asqav SDK cryptographic signing) atau exclude EU entirely.
→ SIDIX sudah punya Maqashid ethical gate = partial compliance.

---

## 7. Kesimpulan & Rekomendasi Bos

**Rekomendasi**: Jalankan 5 sprint sebagai **batch paralel** (bukan serial), dengan prioritas:
1. **P0 — Input Expansion + Output Modality** (user-facing impact terbesar)
2. **P1 — Metode & Belajar** (self-improving moat, competitive differentiation)
3. **P2 — Orchestration Polish** (protocol readiness, B2A positioning)
4. **P3 — Built-in Apps Enhance** (product stickiness)

**Alokasi session** (realistis 2 minggu):
- Minggu 1: Input Expansion (session 1-2) + Orchestration Polish (session 2)
- Minggu 2: Output Modality (session 3-4) + Metode & Belajar (session 3-5)
- Minggu 3: Built-in Apps (session 6-7)

**Target visi coverage post-batch**: Overall ~87% → **~93%**
- Pencipta: 55% → 75% (+20pp)
- Cognitive: 93% → 96% (+3pp)
- Tumbuh: 62% → 77% (+15pp)
- Product: 15% → 40% (+25pp)

**Catatan**: Setiap sprint WAJIB punya Task Card, acceptance criteria, dan update LIVING_LOG.

---

**Sources**:
- Internal: `docs/SIDIX_BACKLOG.md`, `docs/VISI_TRANSLATION_MATRIX.md`, `docs/MASTER_ROADMAP_2026-2027.md`, `brain/public/research_notes/317_*.md`
- External: o-mega.ai (HyperAgents 2026), Zylos Research (MCP/A2A Mar 2026), Vellum (Open-source assistants May 2026), Zylos (Multimodal Apr 2026), Active Inference paper Bert de Vries (Mar 2026), CloudSecurityAlliance (Predictions Jan 2026)
