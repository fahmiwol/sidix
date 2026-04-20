# HANDOFF FINAL — 2026-04-21
# Untuk Agent Berikutnya — Baca Ini Dulu Sebelum Apapun

**Ditulis:** akhir sesi Claude Sonnet 4.6 — 2026-04-21
**Tujuan:** agent baru (akun lain) bisa lanjut tanpa kehilangan konteks

---

## 🗺️ BACA URUTAN INI (SSOT chain)

1. File ini (`HANDOFF_2026-04-21_FINAL.md`) ← mulai di sini
2. `docs/MASTER_ROADMAP_2026-2027.md` ← roadmap canonical
3. `CLAUDE.md` ← aturan keras + identitas SIDIX + UI lock
4. `docs/LIVING_LOG.md` (tail 50 baris) ← log terbaru
5. `brain/public/research_notes/174_*.md` + `175_*.md` ← knowledge sprint ini

---

## ✅ STATE SEKARANG (2026-04-21 malam)

### Git
- **Branch aktif:** `main` (sudah up to date, Sprint 1–4 merged)
- **Worktree lama:** `D:\MIGHAN Model\determined-chaum-f21c81` — sudah merged ke main, **bisa dihapus:**
  ```bash
  cd "D:\MIGHAN Model"
  git worktree remove determined-chaum-f21c81
  ```
- **Branch hanging:** `cursor/sprint-1/t1.2-sanad-ranker` — cek dulu sebelum hapus:
  ```bash
  git log --oneline main..cursor/sprint-1/t1.2-sanad-ranker
  ```

### GitHub
- `github.com/fahmiwol/sidix` → `main` sudah include Sprint 1–4
- PR #2 merged, GitGuardian passed (no secrets)
- README baru: IHOS philosophy + 3-layer architecture + 30 tools table

### VPS (revolusitani-vps)
- `sidix-brain` (PM2 id:12) → **online**, port 8765, `/health` 200 OK ✅
- `sidix-ui` (PM2 id:9) → **online**, port 4000 ✅
- Git pull sudah dijalankan: main terbaru sudah ada di `/opt/sidix/`
- SSH config di `~/.ssh/config`: `Host revolusitani-vps`

### ⚠️ Known Issue — Image Gen Mati
```
[ImageFastPath] tool result success=False err='image_gen request failed: HTTP Error 404: Not Found'
```
Laptop GPU (RTX 3060 + ngrok) sedang tidak nyala.
Fix: nyalain laptop GPU, jalankan SDXL server + ngrok, update `SIDIX_IMAGE_GEN_URL` di VPS `.env`.
**Tidak urgent** — chat tetap jalan, hanya image gen yang error.

### Tools aktif: **30 tools**
```
search_corpus, read_chunk, list_sources, calculator, search_web_wikipedia,
orchestration_plan, workspace_list, workspace_read, workspace_write,
roadmap_list, roadmap_next_items, roadmap_mark_done, roadmap_item_references,
web_fetch, code_sandbox (30s), web_search, pdf_extract, concept_graph,
text_to_image, generate_copy, generate_content_plan, generate_brand_kit,
generate_thumbnail, plan_campaign, generate_ads, muhasabah_refine,
code_analyze, code_validate, project_map, self_inspect
```

### Files penting yang diubah sesi ini
| File | Perubahan |
|---|---|
| `apps/brain_qa/brain_qa/code_intelligence.py` | **BARU** — AST analyzer, validator, project map, self-inspect |
| `apps/brain_qa/brain_qa/agent_tools.py` | +4 tools baru, code_sandbox upgrade 30s |
| `apps/brain_qa/brain_qa/copywriter.py` | **BARU** — generate_copy tool |
| `apps/brain_qa/brain_qa/content_planner.py` | **BARU** — generate_content_plan tool |
| `apps/brain_qa/brain_qa/brand_builder.py` | **BARU** — generate_brand_kit tool |
| `apps/brain_qa/brain_qa/thumbnail_generator.py` | **BARU** — generate_thumbnail tool |
| `apps/brain_qa/brain_qa/campaign_strategist.py` | **BARU** — plan_campaign tool |
| `apps/brain_qa/brain_qa/ads_generator.py` | **BARU** — generate_ads tool |
| `apps/brain_qa/brain_qa/muhasabah_loop.py` | **BARU** — muhasabah_refine tool |
| `apps/brain_qa/brain_qa/creative_quality.py` | **BARU** — CQF scorer |
| `README.md` | **DITULIS ULANG** — IHOS philosophy + architecture |
| `brain/public/research_notes/174_*.md` | **BARU** — code intelligence sprint |
| `brain/public/research_notes/175_*.md` | **BARU** — Al-Qur'an cognitive blueprint |
| `docs/MASTER_ROADMAP_2026-2027.md` | **BARU** — SSoT roadmap unified |

---

## 🎯 SPRINT 5 — Langsung Kerjakan Ini

**Target:** 2026-05-05 → 2026-05-18

### Quick start untuk agent baru:
```bash
# 1. Pastikan di main
cd "D:\MIGHAN Model"
git checkout main && git pull

# 2. Hapus worktree lama (sudah merged)
git worktree remove determined-chaum-f21c81

# 3. Buat worktree Sprint 5
git worktree add sprint5 -b feat/sprint5-agency-kit
cd sprint5
```

### Task Sprint 5 — urutan prioritas:

**[T5.1] curator_agent.py — Self-Train Fase 1**
- File baru: `apps/brain_qa/brain_qa/curator_agent.py`
- Fungsi: rule-based scoring (relevance × sanad_tier × maqashid × dedupe)
- Endpoint: `POST /training/curate` + `GET /training/stats`
- Cron weekly: `corpus_to_training.py` → JSONL min 100 pair/minggu
- Research note: `176_self_train_fase1_curator_agent.md`

**[T5.2] debate_ring.py REAL (bukan mock)**
- File: `apps/brain_qa/brain_qa/debate_ring.py`
- Wire ke Qwen LLM (pakai `local_llm.generate_sidix()`)
- 3 pair wajib: Copywriter↔Strategist, Brand↔Designer, Script↔Hook
- Max 3 round, konsensus via CQF score ≥ 7.0
- Research note: `177_debate_ring_multi_agent.md`

**[T5.3] Agency Kit 1-click — KILLER OFFER #4**
- Endpoint: `POST /creative/agency_kit`
- Input: `{business_name, niche, target_audience, budget}`
- Pipeline DAG:
  ```
  brand_builder → content_planner → copywriter×3
       ↓
  campaign_strategist → thumbnail_generator×3
       ↓
  generate_ads (FB+Google+TikTok)
  ```
- Total output 1 klik: brand kit + 10 caption IG + 3 Reels script + 30-day campaign + 3 thumbnail
- Research note: `178_agency_kit_pipeline.md`

**[T5.4] Hugging Face Publish**
- Upload LoRA adapter: `mighan-lab/sidix-qwen2.5-7b-lora`
- Upload corpus dataset: `mighan-lab/sidix-corpus` (175 research notes trilingual)
- Space Gradio: demo chat publik
- Research note: `176_huggingface_publish_strategy.md` (atau nomor berikutnya)

**[T5.5] Iteration Protocol**
- Di `agent_react.py`: 4-round untuk agents dengan `needs_iteration=true`
- `llm_judge.py` — LLM-as-Judge Round 2 Evaluate

### DoD Sprint 5:
- [ ] Agency Kit 1-click live di `app.sidixlab.com/creative/agency-kit`
- [ ] Debate Ring aktif min 3 pair
- [ ] `tools_available ≥ 33`
- [ ] HuggingFace model card + dataset live
- [ ] Weekly JSONL training auto-generated (min 100 pair/minggu)
- [ ] Research notes 176–180 tersimpan di corpus

---

## 📋 ATURAN KERAS (jangan lupa)

1. **Bahasa Indonesia** untuk semua komunikasi ke user
2. **No vendor API** di inference pipeline (no openai/anthropic/gemini import)
3. **Setiap task → research note** di `brain/public/research_notes/NNN_*.md`
4. **Note berikutnya: 176** (cek dulu: `ls brain/public/research_notes/ | sort | tail -5`)
5. **Log di LIVING_LOG.md** setiap perubahan signifikan
6. **Security scan sebelum commit:** `git diff --cached | grep -iE "fahmi|wolhuter|72\.62|password=|api_key="`
7. **Commit kecil + bermakna** — prefix: `feat:` `fix:` `doc:` `refactor:`
8. **Push setiap selesai task** → VPS bisa pull

---

## 🔧 CARA DEPLOY KE VPS

SSH sudah terkonfigurasi di `~/.ssh/config` sebagai `revolusitani-vps`.

```bash
# Deploy backend (setelah push ke main)
ssh revolusitani-vps "cd /opt/sidix && git pull origin main && pm2 restart sidix-brain"

# Deploy frontend (kalau ada perubahan UI)
ssh revolusitani-vps "cd /opt/sidix/SIDIX_USER_UI && npm run build && pm2 restart sidix-ui"

# Cek status
ssh revolusitani-vps "pm2 status"

# Cek log error
ssh revolusitani-vps "pm2 logs sidix-brain --lines 30 --nostream"
```

---

## 💡 KONTEKS PENTING YANG TIDAK ADA DI FILE LAIN

### Tentang Hugging Face
User minta SIDIX "mejeng" di HuggingFace biar exist di komunitas AI.
- Dataset `sidix-corpus` unik: IHOS + sanad + trilingual (ID/AR/EN) → belum ada yang mirip di HF
- Ini bisa jadi citation di paper orang lain
- Publish setelah Agency Kit live, biar ada yang bisa di-demo di Space

### Tentang Reddit Post
User sudah post di Reddit tentang SIDIX + IHOS + Al-Qur'an sebagai cognitive blueprint.
Mod minta klarifikasi AI usage → user jawab dengan penjelasan teknis.
README baru sudah capture filosofi ini dengan lebih baik.
File: `brain/public/research_notes/175_alquran_sebagai_blueprint_cognitive_system.md`

### Tentang Quota Claude
User pakai Claude dengan quota mingguan — saat handoff ini ditulis, quota hampir habis.
Reset dalam beberapa hari. Agent baru dari akun berbeda akan punya quota fresh.

### Arsitektur 3 Layer (jangan lupa ini)
```
Layer 1 — Brain:   Qwen2.5-7B + LoRA SIDIX (generative, own stack)
Layer 2 — Hands:   30 tools via agent_react.py ReAct loop
Layer 3 — Memory:  corpus + daily growth + LoRA retrain quarterly
```
SIDIX BUKAN sekadar RAG. Ini LLM generative yang tumbuh mandiri.

---

## 📊 METRIC SIDIX HARI INI

```
Tools aktif:        30 (target Sprint 5 = 33+)
Creative agents:    6 (copywriter, content, brand, thumbnail, campaign, ads)
Code tools:         4 (code_analyze, code_validate, project_map, self_inspect)
Corpus notes:       175 research notes
Model:              Qwen2.5-7B + QLoRA (Kaggle T4)
Image gen:          SDXL (offline saat ini — laptop GPU mati)
Deploy:             app.sidixlab.com ✅ | ctrl.sidixlab.com ✅
GitHub:             github.com/fahmiwol/sidix (main = Sprint 4 complete)
HuggingFace:        ❌ belum (Sprint 5)
SEM Level:          L1 Reactive → target L2 Sprint 5
```

---

*Handoff ditulis oleh Claude Sonnet 4.6 — sesi 2026-04-21*
*Agent berikutnya: baca dari atas, mulai dari Quick Start Sprint 5.*
