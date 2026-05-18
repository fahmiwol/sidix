# Research Note 317: SIDIX vs AI Landscape 2026 — Trend Analysis & Gap Benchmark

**Date**: 2026-05-07
**Researcher**: Kimi (agent)
**Scope**: Protocol landscape, evaluation frameworks, self-improving AI, multi-LoRA serving, edge inference
**Method**: Web search (12 queries), literature synthesis, gap analysis

---

## 1. Protocol Landscape 2026 — Key Findings

### MCP (Model Context Protocol)
- **Adoption**: 97M+ monthly SDK downloads, 18,000+ community servers (per Glama.ai / MCP.so)
- **Governance**: Donated to Linux Foundation Agentic AI Foundation (AAIF) Dec 2025
- **Key updates 2026**: OAuth 2.1 auth layer, Streamable HTTP transport (replaced SSE), MCP Apps (SEP-1865) — interactive UI components in tools
- **Native support**: Claude, GPT, Gemini, Cursor, VS Code, JetBrains
- **OpenAI deprecated Assistants API** in favor of MCP — signal of protocol maturity

### A2A (Agent-to-Agent Protocol)
- **Adoption**: 150+ organizations (April 2026), including AWS, Cisco, Google, Microsoft, Salesforce, SAP
- **Version**: v0.3 production-ready status
- **Key innovation**: Agent Cards at `/.well-known/agent-card.json` — automatic discovery
- **Stateful**: Built-in task lifecycle (submitted → working → input-required → completed/failed/canceled)
- **Complementary to MCP**: Google docs explicitly state "A2A + MCP" — layered architecture

### ACP (Agent Communication Protocol)
- **Creator**: IBM via BeeAI platform
- **Focus**: Local-first agent coordination, minimal network overhead, REST-native
- **Niche**: Privacy-first and low-latency environments

### Strategic Insight
> "The winner is not a single protocol — it is the layered ecosystem." — Zylos Research, March 2026
> Two-layer stack becoming default: MCP (vertical/tool) + A2A (horizontal/agent)

---

## 2. Evaluation Frameworks 2026 — Key Findings

### LLM-as-Judge Pattern
- **DeepEval**: 14.7K stars, pytest CI/CD integration, 50+ metrics, component-level tracing
- **Ragas**: 13.3K stars, research-backed RAG metrics (faithfulness, relevancy, precision, recall), reference-free
- **MLflow**: 30M+ monthly downloads, unified platform, trace-aware evaluation, human feedback alignment (`align()` API)

### Judge Alignment
- Critical problem: LLM judges only reliable if aligned with human expectations
- **MemAlign / GEPA**: Algorithms to calibrate judges against human labels
- **Self-preference bias**: Judge model must be separate from target model

### Trace-Aware Evaluation
- Scores EVERY step (tool calls, LLM invocations, planning) — not just final output
- Identifies exact step where agent went wrong
- MLflow leads here with native span tracing

### DSPy Optimization
- **MIPROv2**: Bayesian search for prompt optimization
- **Results**: 10-20 percentage point metric improvements on RAG pipelines
- **Cost**: Self-hosted = 6-10x cheaper than API, 3-5x faster (no rate limits)
- **Runtime**: `dspy.Refine` (hard constraints) + `dspy.BestOfN` (soft quality)

---

## 3. Self-Improving AI 2026 — Key Findings

### Voyager Skill Library Pattern
- **Pioneer**: Voyager (NVIDIA/Caltech/Stanford, May 2023)
- **Pattern**: Agent accumulates reusable code artifacts → checks library before writing new code
- **Key insight**: "Agent does not change how it thinks; it changes what tools it has"

### SAGE (Skill Augmented GRPO)
- **Results**: +8.9% scenario goal completion, -59% output tokens
- **Mechanism**: Write reusable functions → test against validation → save working ones
- **Token reduction = efficiency gain**: Agent solves faster as it accumulates skills

### Anthropic Agent Skills Standard
- **Released**: December 2025
- **Adopted by**: Microsoft, OpenAI, Atlassian, Figma, Cursor, GitHub
- **Purpose**: Interoperability layer for skill libraries — skills from one agent usable by another

### Devin (Cognition AI)
- **Metrics**: $73M ARR (early 2026), $10.2B valuation, 67% PR merge rate
- **Self-improvement**: Devin built tools/scripts it later reused — "tool-creation self-improvement"

### Karpathy Autoresearch Loop
- **Approach**: 630-line Python script — edit code → run experiment → evaluate → iterate
- **Results**: 700 experiments in 2 days, 11% efficiency gain on "Time to GPT-2"
- **Insight**: Self-improvement does not require elaborate frameworks when domain has clean metrics

---

## 4. Multi-LoRA & PEFT 2026

### vLLM Multi-LoRA Serving
- **Capability**: Concurrent decoding with multiple LoRA adapters in same batch
- **Dynamic mode**: Runtime load/unload via API (`POST /v1/load_lora_adapter`)
- **Use case**: Multi-tenant SaaS — per-client adapters without restarting server

### NVIDIA NIM LoRA
- **Static LoRA**: Discovered at startup, requires restart to update
- **Dynamic LoRA**: Directory monitoring + runtime API, no restart needed
- **Multiple adapters**: Serve simultaneously subject to GPU memory

### PEFT Strategy 2026
- **Enterprise axes**: Cost/speed, downstream performance, operational complexity, governance
- **Matchmaking**: LoRA for quick iterations, QLoRA for larger models, adapters for multi-tenant
- **Delta registries**: Parameter-delta registries, secure adapter stores, automated merge-and-sign

---

## 5. Edge/CPU Inference 2026

### GGUF Format
- **Status**: De facto standard for local LLM
- **Evolution**: v1 (2024) → v4 (2026)
- **Performance**: Q4_K_M achieves ~92% perplexity retention, 20% faster than IQ4_XS on RTX 4060
- **Ecosystem**: Ollama, LM Studio, llama.cpp, GPT4All

### llama.cpp
- **Stars**: 70K+ GitHub stars
- **Strength**: CPU inference, Apple Silicon native (Metal), quantization flexibility
- **Server mode**: `./llama-server -m model.gguf --port 8080` — OpenAI-compatible API
- **Speed**: 15-20 tokens/s CPU, seconds-level startup

### ONNX Runtime
- **Strength**: Cross-platform (cloud, edge, web, mobile), WebAssembly support
- **Improvement**: Transformer-specific kernels, KV-cache management, attention fusion
- **Use case**: Enterprises standardized on ONNX pipelines

### TurboQuant (Experimental)
- **Speed**: 20-25 tokens/s CPU inference
- **Focus**: Aggressive compression for edge deployment

---

## 6. Gap Analysis: SIDIX vs State-of-the-Art 2026

| Trend 2026 | SIDIX Status | Gap Severity | Gap Detail |
|---|---|---|---|
| MCP OAuth 2.1 + Streamable HTTP | MCP HTTP + stdio (basic) | 🟡 Medium | No OAuth, no Streamable HTTP, no MCP Apps |
| A2A v0.3 + delegation attestation | A2A Phase 1-3 (basic) | 🟡 Medium | No v0.3 features, no macaroons, no attestation |
| LLM-as-Judge evaluation | Maqashid Phase 1 (heuristic regex) | 🔴 High | No ML judge, no trace-aware, no alignment loop |
| Skill library pattern | Voyager Phase 1 (tool creation) | 🔴 High | No usage stats, no self-refinement, no skill index |
| Multi-LoRA concurrent serving | DoRA (load/unload one-by-one) | 🟡 Medium | No concurrent batching, no dynamic API |
| GGUF native inference | PEFT/Ollama (LoRA adapter) | 🟡 Medium | No GGUF, no llama.cpp server integration |
| DSPy prompt optimization | None | 🟢 Low | Not yet needed — SIDIX prompt manual |
| Trace-aware evaluation | None | 🔴 High | No step-level scoring, no span tracing |
| Anthropic Agent Skills | None | 🟡 Medium | No interoperability format for tools |

---

## 7. Benchmark Recommendations

### Immediate (this batch)
1. **Voyager Phase 2** — Implement skill library pattern (usage tracking + self-refinement + BM25 index)
2. **Maqashid Phase 2 Hybrid** — Heuristic fast-path + lightweight judge for borderline cases

### Short-term (next 2-4 weeks)
3. **Raudah Protocol v0.2** — TaskGraph DAG execution
4. **Protocol polish** — MCP Streamable HTTP stub + A2A v0.3 compat

### Medium-term (next 1-3 months)
5. **GGUF inference path** — llama.cpp server integration for CPU-only deployment
6. **Multi-LoRA concurrent** — vLLM-style adapter batching (when GPU available)
7. **DSPy integration** — Prompt optimization for RAG pipeline (when metric pipeline mature)

---

## 8. Strategic Position

SIDIX is **ahead of curve** in:
- Self-hosted philosophy ( aligns with 2026 privacy trend )
- A2A + MCP dual protocol ( aligns with layered architecture )
- Dynamic tool creation ( Voyager Phase 1 )
- Multi-persona architecture ( 5 personas with DoRA )

SIDIX is **behind curve** in:
- Evaluation sophistication ( heuristic vs LLM-as-Judge )
- Self-improvement depth ( no skill library, no usage analytics )
- Inference optimization ( PEFT vs GGUF/llama.cpp )
- Protocol maturity ( basic vs OAuth/Streamable HTTP )

**Recommendation**: Double down on self-improving capabilities (Voyager P2 + Maqashid P2) — this is the highest-ROI path toward SIDIX replacing external agents. Protocol upgrades are hygiene; self-improvement is differentiation.

---

## Sources

1. Zylos Research — Agent Interoperability Protocols 2026 (2026-03-26)
2. PrimeAIcenter — MCP vs A2A Complete Guide (2026-04-22)
3. AgentLux — Agent Protocol Stack 2026 (2026-05-04)
4. MLflow — Top 5 Agent Evaluation Tools (2026)
5. Atlan — RAGAS vs TruLens vs DeepEval (2026-04-10)
6. Spheron — DSPy on GPU Cloud (2026-04-24)
7. o-mega.ai — Self-Improving AI Agents 2026 Guide (2026-03-26)
8. arXiv:2603.24775 — Agent Capability Protocols (2026)
9. arXiv:2505.13523 — Agent Collaboration Protocols (ACPs)
10. NVIDIA NIM — LoRA PEFT Documentation (2026-04-28)
11. CheeseCat — TurboQuant & GGUF (2026-03-27)
12. Zylos Research — Small Language Models & Edge AI (2026-02-07)
