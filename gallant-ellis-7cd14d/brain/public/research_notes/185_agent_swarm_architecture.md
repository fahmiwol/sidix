# 185 — SIDIX Agent Swarm v0.1: Arsitektur Paralel Berbasis IHOS

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-23
**Sanad:** [OPINION] — adaptasi arsitektur Kimi Agent Swarm ke stack SIDIX own
**Tags:** agent-swarm, orchestration, parallel, ihos, no-vendor-api

---

## Apa

SIDIX Agent Swarm adalah sistem **multi-agent paralel** dimana satu OrchestratorAgent
memecah task kompleks menjadi subtask, mendistribusikan ke N SubAgent yang berjalan
bersamaan (via `asyncio.gather`), lalu mengagregasi hasilnya.

Terinspirasi dari **Kimi Agent Swarm (K2.5/K2.6)** tapi dengan perbedaan fundamental:
- Menggunakan **local LLM (Ollama/sidix-lora)** — BUKAN Claude/OpenAI API
- Memiliki **IHOS Guardrail** (Maqashid check sebelum spawn sub-agent)
- Memiliki **Sanad Validator** sebagai sub-agent khusus verifikasi sumber
- Open-source, dapat di-federate di multiple node

---

## Perbandingan Kimi vs SIDIX Swarm

| Fitur                  | Kimi K2.6              | SIDIX Swarm v0.1      |
|------------------------|------------------------|-----------------------|
| Max sub-agents         | 300                    | 10 (bisa scale)       |
| LLM backbone           | Kimi proprietary       | Qwen2.5-7B + LoRA local|
| IHOS Guardrail         | ❌ Tidak ada           | ✅ Ada (Maqashid check)|
| Sanad Validator        | ❌ Tidak ada           | ✅ Sub-agent khusus    |
| Training               | PARL (RL)              | Prompt-based (Phase 1)|
| Open source            | Partial (K2.5)         | ✅ MIT License         |
| No vendor API          | N/A (proprietary)      | ✅ 100% local          |

---

## Arsitektur

```
User Task
    │
    ▼
OrchestratorAgent.decompose_task()
    │
    ├── IHOS Guardrail (Maqashid check)
    │       ↓ FAIL → return error
    │       ↓ PASS → continue
    │
    ├── parallel_groups = [[task1, task2, task3], ...]
    │
    ▼
asyncio.gather(*[SubAgent.execute(task) for task in group])
    │
    ├── SubAgent.Researcher   → [FAKTA] / [OPINI] + source
    ├── SubAgent.Analyzer     → pro/kontra analysis
    ├── SubAgent.Writer       → draft konten
    ├── SubAgent.Coder        → implementasi kode
    └── SubAgent.Verifier     → sanad check
    │
    ▼
OrchestratorAgent.aggregate()   ← Ijma' Layer
    │
    ▼
SwarmResult.final_answer
```

---

## Konsep IHOS dalam Swarm

| Konsep IHOS        | Implementasi Swarm                          |
|--------------------|---------------------------------------------|
| Qiyas (analogi)    | Decompose task via analogical reasoning     |
| Ijma' (konsensus)  | Aggregation layer = konsensus sub-agent     |
| Ijtihad (reasoning)| Orchestrator mediasi jika sub-agent conflict|
| Sanad (chain)      | Verifier sub-agent cek rantai sumber        |
| Maqashid           | IHOS Guardrail sebelum spawn sub-agent      |

---

## Bagaimana Pakai

```python
import asyncio
from brain.swarm.core import run_swarm

# Contoh 1: research task
result = asyncio.run(run_swarm(
    "Riset dan bandingkan 5 sistem ekonomi syariah yang berhasil di Asia Tenggara"
))
print(result.final_answer)
print(f"Sub-agents: {len(result.sub_results)}, Waktu: {result.elapsed_s}s")

# Contoh 2: creative task
result = asyncio.run(run_swarm(
    "Buat kampanye media sosial untuk produk kopi lokal UMKM, target millennial muslim"
))
```

---

## Roadmap Swarm

```
v0.1 (sekarang)  : skeleton, rule-based decomposition, asyncio dispatch
v0.2             : TaskGraph DAG + dependency tracking (task B tidak mulai sebelum A selesai)
v0.3             : GraphRAG sebagai tool sub-agent Researcher
v0.4             : Simulated reward signal → log ke SQLite untuk RL nanti
v0.5             : Ijtihad Conflict Resolution (sub-agent conflict → Maqashid mediasi)
v1.0             : PARL reward-based orchestrator training
```

---

## Keterbatasan v0.1

1. Decomposition masih rule-based (regex), belum LLM-based
2. Tidak ada dependency tracking antar subtask (semua paralel flat)
3. Context sharding manual (800 char) — belum adaptive
4. Aggregation menggunakan Ollama sekali lagi → latency bertambah
5. Belum ada persistence/logging per swarm run

---

## File

- `brain/swarm/__init__.py`
- `brain/swarm/core.py`

---

## Referensi

- sidix-kimi-agent-research.html — Kimi Agent Swarm 7-day plan
- docs/MASTER_ROADMAP_2026-2027.md §Sprint 7
- Kimi paper: "Kimi k1.5: Scaling Reinforcement Learning with LLMs" (analogi PARL)
