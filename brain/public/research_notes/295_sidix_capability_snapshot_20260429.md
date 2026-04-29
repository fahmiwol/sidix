"""
Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT — attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.
"""

# Research Note 295 — SIDIX Capability Snapshot 2026-04-29

**Sanad**: observasi langsung dari VPS + git log + health endpoint + hafidz ledger  
**Status**: FACT — semua angka diambil dari sistem live  
**Tujuan**: snapshot akurat "SIDIX sekarang sudah sampai mana" untuk referensi sprint berikutnya

---

## 1. Infrastruktur yang Berjalan

### VPS (Produksi)
- **URL**: `ctrl.sidixlab.com` (brain) + `app.sidixlab.com` (UI)
- **PM2 proses aktif**: `sidix-brain` (port 8765) + `sidix-ui` (port 4000)
- **RAM usage**: 395MB (brain) + 83MB (UI)
- **Status**: `ok=true`, `model_ready=true`

### Model Stack
- **LLM**: Qwen2.5-7B-Instruct + LoRA adapter SIDIX (di VPS, path `/opt/sidix/apps/brain_qa/models/sidix-lora-adapter`)
- **Embedding**: BGE-M3 / MiniLM (CPU, VPS)
- **Models loaded**: 3 (`sidix_local_engine.models_loaded=3`)
- **RunPod**: endpoint `ws3p5ryxtlambj` (GPU fallback, Qwen+LoRA serverless)

### Corpus
- **Dokumen**: 2.287 chunks di corpus RAG
- **Research notes**: 295 file (nomor 1–295)
- **Hafidz Ledger**: 226 entri (220 autonomous_dev_iteration, 2 approved, 1 rejected)

---

## 2. Agent Tools yang Aktif (48 tools)

Diambil langsung dari `TOOL_REGISTRY` live:

### Pencarian & Informasi
| Tool | Fungsi |
|------|--------|
| `web_search` | DuckDuckGo/Brave search real-time |
| `web_fetch` | Fetch URL + extract content |
| `search_corpus` | BM25 search di corpus lokal (2287 docs) |
| `read_chunk` | Baca chunk corpus spesifik |
| `list_sources` | Daftar semua sumber corpus |
| `graph_search` | Knowledge graph query |
| `search_web_wikipedia` | Wikipedia lookup + fallback |
| `pdf_extract` | Ekstrak teks dari PDF |

### Coding & Development
| Tool | Fungsi |
|------|--------|
| `code_sandbox` | Eksekusi kode Python di sandbox |
| `code_analyze` | Analisa kode (complexity, issues) |
| `code_validate` | Validate syntax + type |
| `shell_run` | Run shell command (sandboxed) |
| `test_run` | Run pytest di project |
| `git_status` / `git_diff` / `git_log` / `git_commit_helper` | Git operations |
| `scaffold_project` | Generate project scaffold |
| `workspace_list` / `read` / `write` / `patch` | File workspace management |
| `project_map` | Map project structure |
| `prompt_optimizer` | Optimize LLM prompts |

### Kreasi & Konten
| Tool | Fungsi |
|------|--------|
| `text_to_image` | Generate gambar (via RunPod SDXL) |
| `text_to_speech` | TTS audio output |
| `speech_to_text` | Transkripsi audio |
| `analyze_audio` | Analisa file audio |
| `generate_thumbnail` | Generate thumbnail |
| `generate_ads` | Generate iklan copy + visual |
| `generate_brand_kit` | Brand kit (logo concept, color, font) |
| `generate_content_plan` | Content calendar planning |
| `generate_copy` | Copywriting |
| `plan_campaign` | Campaign strategy plan |

### Reasoning & Multi-Agent
| Tool | Fungsi |
|------|--------|
| `orchestration_plan` | Multi-step orchestration planning |
| `debate_ring` | Multi-agent debate (2 agen saling argue) |
| `llm_judge` | LLM sebagai juri evaluasi |
| `muhasabah_refine` | Self-reflection + refinement loop |
| `concept_graph` | Build conceptual graph dari teks |
| `calculator` | Safe math evaluation |
| `social_radar` | Monitor social signals |
| `curator_run` | Curate + rank content |
| `self_inspect` | SIDIX inspect state sendiri |

### Bisnis & Roadmap
| Tool | Fungsi |
|------|--------|
| `roadmap_list` / `next_items` / `item_references` / `mark_done` | Roadmap management |
| `agency_kit` | Agency project brief |

---

## 3. Senses yang Aktif (9/12)

```
active (9):  tool_action, web_read, creative_imagination, self_awareness,
             persona_voice, audio_out, emotional_tone, text_write, text_read
inactive (3): [senses yang belum fully wired]
broken (0): tidak ada
```

---

## 4. Autonomous Developer (Sprint 40–60)

### Pipeline yang sudah berjalan:
```
pick_next() → DevTask
   │
   ├─ persona_fanout (5 persona × parallel ThreadPoolExecutor)
   │     UTZ(creative) · ABOO(engineer) · OOMAR(strategy)
   │     ALEY(academic) · AYMAN(community)
   │
   ├─ code_diff_planner.plan_changes()
   │     LLM generate full file content
   │     size-safety guard (≥50% existing size)
   │     context: 8000 chars, tokens: 4096
   │
   ├─ validate_plan() — security gate
   │     block: /etc, /root, absolute path, ../ traversal
   │
   ├─ apply_plan() — real writes (dry_run=False production)
   │
   ├─ full_check()
   │     pytest — full suite (191 tests, ~70s)
   │     ruff — DELTA-MODE (hanya scan file yang disentuh diff)
   │     ok=False jika: pytest fail ATAU ruff delta > 0
   │
   ├─ dev_pr_submitter.submit()
   │     git checkout -b branch_name
   │     git add touched_files
   │     git commit + push
   │
   ├─ notify_owner()
   │     Telegram @sidixlab_bot → @fahmiwol13
   │     "Review diperlukan sebelum merge ke main"
   │
   └─ hafidz_ledger.write_entry() — audit trail
```

### Mekanisme keamanan:
- ❌ NO auto-merge ke main — SELALU butuh owner approval
- ❌ NO modifikasi file di luar repo scope (path traversal blocked)
- ❌ NO modify file > 2x ukuran asli (size-safety guard)
- ✅ Ruff delta-mode: SIDIX tidak bisa introduce ruff violations baru
- ✅ Semua PR ada di branch terpisah, owner review sebelum merge

### Stats Hafidz Ledger (2026-04-29 18:36):
```
total_entries : 226
autonomous_dev: 220 iterations tracked
approved      : 2
rejected      : 1
pending       : 223 (awaiting owner review)
```

### Auto-fanout rule:
- Task dengan `priority >= 80` → otomatis 5-persona fan-out
- Task dengan `persona_fanout=True` → 5-persona fan-out
- Default: single-shot plan

---

## 5. Modul Jiwa (Kimi Territory)

4 modul aktif di `brain_qa/jiwa/`:
- `aql.py` — Akal/rasionalitas (telah difix: `datetime.now(timezone.utc)`)
- `hayat.py` — Kehidupan/vitalitas
- `nafs.py` — Jiwa/kepribadian
- `qalb.py` — Qalbu/hati
- `orchestrator.py` — Koordinasi jiwa modules

---

## 6. Cron Jobs yang Berjalan

Di `/opt/sidix/.data/` terdapat log aktif dari:
- `cron_always_on.log` — always-on cron (setiap N menit)
- `cron_classroom.log` — curriculum lesson generator
- `cron_radar.log` — social + world radar
- `cron_reflect_day.log` — daily reflection
- `cron_aku_ingestor.log` — AKU data ingestor
- `cron_worker.log` — general worker

---

## 7. Kemampuan yang BELUM (Jujur)

### Belum fully production:
| Fitur | Status | Catatan |
|-------|--------|---------|
| RunPod GPU | Standby | Balance ~$24, cold start 60-120s |
| Auto-merge ke main | Intentionally OFF | Owner-in-loop SELALU |
| Telegram chat (2-arah) | Scaffold ada (`telegram_persona_bot.py`) | Belum wired ke endpoint |
| LoRA retrain loop | Scaffold ada (`nightly_lora.py`, `auto_lora.py`) | Belum E2E wired |
| 5-persona chat di Telegram | Scaffold Sprint 43 | Phase 2 |
| Image gen GPU | Terhubung RunPod SDXL | Cold start tiap request |
| Ruff baseline cleanup | 3726 violations | Sprint tersendiri |
| GitHub PR creation via `gh` CLI | Stub (Phase 2) | PR URL masih placeholder |

### Sprint yang sudah done vs belum:
```
DONE:  Sprint 40 (orchestrator) · 43 scaffold · 58A (diff planner LLM)
       58B (5-persona fanout) · 59 (real writes) · 60A-E (ruff+telegram)

PENDING: Sprint 43 Phase 2 (Telegram chat 2-arah)
         Sprint 61? (GitHub PR via gh CLI)
         Sprint 62? (Ruff baseline cleanup)
         Sprint 63? (LoRA retrain auto-loop)
```

---

## 8. Arsitektur 3-Layer (Rekapitulasi)

```
┌─────────────────────────────────────────────┐
│  LAYER 1 — LLM Generative                   │
│  Qwen2.5-7B + LoRA adapter SIDIX            │
│  Generate token-by-token, bukan search      │
└───────────────────┬─────────────────────────┘
                    │ augment
┌───────────────────▼─────────────────────────┐
│  LAYER 2 — RAG + Agent Tools (48 tools)     │
│  ReAct loop: pick tool → execute → observe  │
│  → refine → answer                          │
│  Corpus: 2287 chunks, 291 research notes    │
└───────────────────┬─────────────────────────┘
                    │ feed
┌───────────────────▼─────────────────────────┐
│  LAYER 3 — Growth Loop                      │
│  Autonomous Developer (Sprint 40-60)        │
│  Cron jobs: learn, reflect, radar, classroom│
│  Hafidz Ledger: 226 entries audit trail     │
│  Telegram notify: owner-in-loop             │
└─────────────────────────────────────────────┘
```

---

**Kesimpulan**: SIDIX per 2026-04-29 adalah AI Agent dengan 3 layer yang berjalan. Layer 1 (LLM), Layer 2 (48 tools + RAG), dan Layer 3 (autonomous developer + growth loop). Bisa menjawab, mengeksekusi tools, menulis kode, dan mengembangkan dirinya sendiri — dengan owner-in-loop untuk approval.
