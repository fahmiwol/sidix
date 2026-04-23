# Implementasi 7 Pilar Jiwa SIDIX — Wiring ke agent_react.py

> Captured via SIDIX MCP - 2026-04-23

## Apa

Jiwa adalah layer arsitektur yang mengintegrasikan 7 pilar kemandirian SIDIX ke dalam pipeline
`agent_react.py`. Tujuannya: SIDIX terasa "hidup" — bisa ngobrol alami, punya karakter, punya rasa,
tidak ngelantur, dan terus belajar dari setiap interaksi.

## File yang Dibuat

```
apps/brain_qa/brain_qa/jiwa/
├── __init__.py           ← exports NafsRouter, HayatIterator, AqlLearner, QalbMonitor, JiwaOrchestrator
├── nafs.py               ← Pilar 1: topic routing 7 kategori + persona jiwa (karakter/rasa/gaya)
├── hayat.py              ← Pilar 5: self-iteration wrapper atas muhasabah_loop.py
├── aql.py                ← Pilar 2: fire-and-forget learning hook → jiwa_training_pairs/*.jsonl
├── qalb.py               ← Pilar 3: background health monitor (psutil, 120s interval)
└── orchestrator.py       ← JiwaOrchestrator singleton — entry point tunggal dari agent_react
```

## Cara Wiring ke agent_react.py

### Nafs (Pilar 1) — topic routing
Fungsi `_response_blend_profile(question, persona)` diupdate:
- Sebelum: hanya 2 kategori (sidix_focused / model_focused)
- Sesudah: 7 kategori via NafsRouter:
  - `ngobrol` → conversational, skip_corpus=True, hayat_enabled=False
  - `umum` → model_focused, max_obs_blocks=1
  - `kreatif` → creative_focused, max_obs_blocks=1
  - `koding` → model_focused, skip_corpus=True
  - `sidix_internal` → sidix_focused, max_obs_blocks=3
  - `agama` → religious_focused, max_obs_blocks=3
  - `etika` → ethical_focused, max_obs_blocks=2
- Setiap profil membawa `persona_jiwa` (karakter, rasa, gaya) yang diinjeksi ke system prompt

### Hayat (Pilar 5) — self-iteration
Setelah `_apply_maqashid_mode_gate()`, sebelum `session.final_answer = final_answer`:
```python
if _JIWA_ENABLED and not simple_mode and hayat_enabled:
    final_answer = _jiwa.refine(
        question=question, answer=final_answer,
        generate_fn=_gen_fn, topic=topic
    )
```
- Max 2 rounds (hemat inference)
- CQF target 8.0
- Non-blocking: gagal → fallback ke jawaban asli

### Aql (Pilar 2) — learning hook
Fire-and-forget setelah final_answer di-set:
```python
_jiwa.post_response(question, final_answer, persona, topic=topic, cqf_score=conf_score*10)
```
- Background thread: tidak blocking response
- Hanya simpan kalau CQF ≥ 7.0
- Output: `apps/brain_qa/data/jiwa_training_pairs/pairs_YYYY-MM-DD.jsonl`

### Qalb (Pilar 3) — health monitor
Auto-start saat JiwaOrchestrator diinstansiasi:
- Background thread, check setiap 120 detik
- Thresholds: memory >88%, CPU >92%, disk >95%
- Heal: gc.collect(), reduce_batch flag, safe_mode env var

## 5 Persona Jiwa (karakter, rasa, gaya)

| Persona | Karakter | Rasa | Gaya |
|---|---|---|---|
| AYMAN | Visioner bijak | Penuh hormat, hangat, tegas | Analogi, kutip tradisi ilmu |
| ABOO | Analis presisi | Objektif, curious, semi-akademis | Argumen terstruktur, data |
| OOMAR | Engineer solutif | To-the-point, pragmatis | Langsung ke kode/teknis |
| ALEY | Guru sabar | Hangat, supportif | Step-by-step, analogi sederhana |
| UTZ | Teman serba bisa | Relatable, genuine | Natural, bisa santai bisa serius |

## Pilar 4, 6, 7 — Delegates ke Modul Yang Sudah Ada

| Pilar | Nama | Delegasi |
|---|---|---|
| Ruh (4) | Self-Improve | `daily_growth.py` — weekly evaluation sudah ada |
| Ilm (6) | Self-Crawl | `learn_agent.py` — auto-crawl 50+ sources sudah ada |
| Hikmah (7) | Self-Train | `auto_lora.py` — QLoRA retrain pipeline sudah ada |

## MCP Registration

| Platform | Cara |
|---|---|
| Claude Desktop | Copy `claude_desktop_config.json` ke `%APPDATA%\Claude\` |
| Cursor | Copy `configs/cursor_mcp.json` ke `.cursor/mcp.json` |
| Kimi | Copy `configs/kimi_mcp.json` ke `.kimi/mcp.json` |
| GPT Actions | Import `openapi.yaml` di ChatGPT → My GPTs → Actions |
| Smithery | `npx @smithery/cli install sidix-socio-mcp --client claude` |
| Codex | Config di `~/.codex/config.toml` |

## Keterbatasan (Current State)

- Hayat: max 2 rounds (hemat GPU/CPU) — bisa dinaikkan via env `HAYAT_MAX_ROUNDS`
- Nafs: topic detection masih berbasis regex (akurasi ~85%) — ideal diganti NER model
- Aql: training pairs JSONL belum auto-trigger LoRA retrain (manual batch saat ini)
- Qalb: psutil opsional — kalau tidak installed, monitor skip (tidak error)
- Pilar 4/6/7: belum fully wired ke JiwaOrchestrator (delegate ke existing modules)
