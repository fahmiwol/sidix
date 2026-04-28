# 94 — D:\Mighan: Kapabilitas & Integrasi ke SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Task:** Scan, ekstrak, dan konversi D:\Mighan ke training pairs + corpus SIDIX  
**Nomor:** 94  

---

## Apa Itu D:\Mighan?

`D:\Mighan` adalah project **Mighantect 3D** — simulasi kantor isometrik berbasis Three.js dengan sistem AI agent multi-provider. Ini adalah "dunia virtual" di mana setiap karyawan adalah AI agent dengan persona, role, dan kemampuan berbeda.

**Stack:** Three.js v0.162, Node.js + Express (gateway port 9797), Vanilla JS (browser), tanpa TypeScript.

---

## Struktur Folder (Non-node_modules)

| Kategori | Jumlah File |
|----------|------------|
| Code (.js, .ts, .py, dll) | 961 |
| Config (.json, .yaml, dll) | 770 |
| Docs (.md, .txt) | 636 |
| Web (.html, .css) | 170 |
| Script (.bat, .ps1) | 41 |
| **Total (setelah skip node_modules)** | **2768** |

File paling penting (non-library):
- `src/services/AgentBrain.js` — routing logic per agent ke gateway
- `src/services/DirectLLMClient.js` — fallback browser langsung ke LLM API
- `config/world.json` — 48 agent definitions, room layout, furniture
- `config/npc-profiles/*.json` — 25+ NPC profile dengan identity, brain, autonomy
- `config/agent-ledger.json` — coin/credit system per agent
- `server/gateway.js` — Express REST + Socket.io hub
- `server/ai-connector.js` — Multi-provider LLM (Anthropic, OpenAI, Mistral, Gemini)
- `server/innovation-agent.js` — Iris AI engine (riset, ideasi, sandbox)
- `server/microstock-pipeline.js` — Pipeline upload ke Shutterstock, Adobe Stock

---

## Skill / Logic Yang Bisa Diekstrak

### 1. Agent Routing Pattern
AgentBrain.js mengandung **AGENT_MODULE_MAP** — peta agent ID ke module ID. Pola ini adalah blueprint untuk skill routing di SIDIX:

```
agent_id → module_id → specific handler function
```

Contoh agent + module:
- `wordsmith` → `prompt_gen` (generasi prompt gambar)
- `hunter` → `product_hunt` (riset produk)
- `penulis` → `write_content` (penulisan konten)
- `omnyx-caption-writer` → `omnyx_caption` (caption AI)
- `omnyx-trend-hunter` → `omnyx_trend` (trend research)

### 2. NPC Profile Schema
Setiap NPC memiliki schema JSON standar:
```json
{
  "identity": { "id", "name", "role", "personality", "backstory" },
  "brain": { "provider", "model", "systemPrompt", "temperature" },
  "autonomy": { "tdafLoop", "heartbeatInterval", "permissions" },
  "memory": { "shortTerm", "longTerm", "skills" },
  "learning": { "searchQueries", "adoptedSkills", "knowledgeBase" }
}
```
Schema ini langsung bisa dipakai sebagai **template agent definition** di SIDIX.

### 3. Multi-Provider LLM Routing
Gateway mendukung: Anthropic Claude, OpenAI, Mistral, Gemini, Ollama. Pattern routing:
- Per-agent provider config
- Fallback browser → DirectLLMClient jika gateway down
- Coin system: 1 coin = $0.001, auto-approve ≤10.000 coins

### 4. Microstock Pipeline
Agent workflow lengkap untuk upload ke platform microstock:
```
wordsmith (prompt gen) → designer (visual gen) → kurator (quality check) →
reviewer (content review) → kurir (upload mgr) → pustakawan (keyword research)
```
Pattern multi-agent pipeline yang bisa diadaptasi SIDIX.

### 5. Innovation Engine (Iris)
Agent "Iris" dan "Prof. Toard" menjalan Iris AI engine dengan command pattern:
- `riset [topik]` → web research + summarize
- `ide` → generate ide berdasarkan riset
- `sandbox [id]` → test ide di environment terkontrol
- `review` → evaluasi hasil

### 6. WorldData.js — World State Management
80KB+ world state mencakup: room definitions, agent positions, furniture, lighting, NPC interaction zones. Knowledge tentang game world architecture.

---

## Kapabilitas Yang Diekstrak

| Tipe | Jumlah |
|------|--------|
| knowledge (dari docs/bible) | 3380 |
| pattern (dari JSON configs) | 954 |
| logic (dari JS/TS code) | 389 |
| skill (dari NPC profiles) | 144 |
| **Total** | **4867** |

---

## Bagaimana Integrasinya dengan SIDIX?

### 1. Training Corpus
Semua dokumen di `docs/bible/` (agent encyclopedia, world guide, tutorial) masuk ke RAG corpus SIDIX. User bisa tanya tentang Mighantect agent dan SIDIX bisa menjawab dari corpus ini.

### 2. Agent Persona Templates
25+ NPC profile JSON bisa dijadikan **template persona** untuk SIDIX agent. Format: identity → brain → autonomy → memory → learning.

### 3. Skill Taxonomy
AGENT_MODULE_MAP dari AgentBrain.js adalah skill taxonomy siap pakai: 40+ skill IDs yang sudah dikategorikan per domain (microstock, content studio, management, omnyx agency).

### 4. Training Pairs
4867 capabilities → 4867+ Alpaca training pairs, disimpan di `.data/harvest/mighan_opix_pairs.jsonl`. Bisa langsung dipakai untuk fine-tuning model SIDIX.

### 5. Multi-Agent Workflow Pattern
Pipeline microstock dan OMNYX agency menunjukkan pola orkestrasi multi-agent yang bisa dijadikan referensi implementasi ReAct agent di SIDIX.

---

## Keterbatasan

- `node_modules` sangat besar (96K+ .js files) — sudah di-skip otomatis
- Banyak file game engine (Three.js geometries, world data) yang sangat spesifik domain game, kurang relevan untuk general AI capability
- NPC profiles memiliki `systemPrompt: ""` (kosong) — perlu diperkaya untuk training

---

## File Output
- Corpus: `brain/public/sources/mighan_opix/mighan_NNNN_*.txt`
- Training pairs: `.data/harvest/mighan_opix_pairs.jsonl`
- Processor: `apps/brain_qa/brain_qa/multi_folder_processor.py`
