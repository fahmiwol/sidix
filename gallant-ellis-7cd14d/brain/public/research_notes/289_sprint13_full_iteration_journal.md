# Note 289 — Sprint 13 Full Iteration Journal (Anti-Mengulang)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sanad**: Bos mandate (2026-04-29): *"Catat semua di log dan dokumen, biasakan mencatat, jangan ada sedikitpun konteks, riset, iterasi, perubahan yang terlewat, jadi kita bisa tua keseluruh perjalanan kita. mendapatkan pengalaman cognitive, tidak mengulang-ngulang."*  
**Tanggal**: 2026-04-29  
**Tujuan**: Single source of truth untuk SEMUA iterasi Sprint 13. Future agent cek note ini, bukan ulang riset/iterasi yang sudah dilakukan.

---

## 0 · Context awal

**Bos directive 2026-04-29**: pilih Sprint 13 (DoRA Persona Stylometry) sebagai sprint berikutnya — "keputusan sulit di awal mempermudah kedepannya". Score 18/20 (Innovation 5, Vision 5, Feasibility 3, Compound 5).

**Tujuan Sprint 13**: 5 persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) di **weight level via DoRA adapter**, bukan prompt level. Differentiator brand level — voice yang **tidak bisa di-replicate** dengan prompt engineering.

---

## 1 · Phase 3a — synthetic data pipeline (DONE 2026-04-29 sore)

### 1.1 Architecture decisions

- Template-based generation (opener × body × closer per persona)
- Signature scoring: pronoun 0.4 + vocab 0.4 + pattern 0.2, gate ≥0.5
- Dedup: SHA-256 hash[:12] pair_id
- Output: Alpaca-style JSONL (`instruction`, `input`, `output`, `metadata`). Persona di **metadata BUKAN prompt** — DoRA harus belajar voice tanpa cue eksplisit.

### 1.2 Iterasi marker tightening

| Iter | Finding | Fix |
|---|---|---|
| 1 (initial) | AYMAN gap 0.40 marginal, UTZ gap 0.25 weak | — |
| 2 (AYMAN tighten) | Generic words `kayak`, `gini`, `rasanya` overlap UTZ | Replace dengan empathy-specific: `perasaan`, `overwhelm`, `cerita`, `pelan-pelan`, `diri sendiri`, `boleh kok`, `kasih ruang`. Result: AYMAN 0.40→0.50 |
| 3 (UTZ expand) | UTZ tetap 0.28 gap | Tambah signature words yang dipakai di template: `kebayang`, `brushstroke`, `compose pengalaman`, `puzzle visual`, `breathing room`, `messy`, `wild card-nya`. Result: UTZ 0.28→0.52 |

Final 5-seed cross-persona discrimination (own_avg vs cross_avg, gap):
- UTZ 0.52 ✓
- ABOO 0.70 ✓
- OOMAR 0.64 ✓
- ALEY 0.52 ✓
- AYMAN 0.43 ✓

### 1.3 Production scale-up

- 200/persona × 5 = 1000 pairs (initial test) — all PASS, 0 dedup collision
- 1500/persona × 5 = 7500 pairs (target) — all PASS, avg score 0.639-0.767
- Train/val split 90/10 stratified per persona = 6750 train + 750 val

### 1.4 Files yang lahir

- `apps/brain_qa/brain_qa/persona_qa_generator.py` (350 lines, no external dep)
- `apps/brain_qa/brain_qa/merge_persona_dataset.py` (100 lines)
- `brain/public/research_notes/285_sprint13_dora_persona_qa_generator.md`
- `docs/ROADMAP_DORA_SPRINT13.md` (Sprint 13 phases + queue)
- CLI subcommands: `gen_persona_qa`, `merge_persona_dataset`

---

## 2 · Phase 3b — Kaggle attempts (FAILED setelah 7 iterasi)

### 2.1 Setup

Bos kasih credentials (chmod 600 di VPS):
- Kaggle API: format baru `KGAT_xxx` (CLI 1.7.4.5 belum support) → request legacy `kaggle.json` (mighan/`<key-redacted>`)
- HF token: `hf_xxx` (write scope, named SIDIX123, account Tiranyx)

Cloud assets created:
- HF repo: `Tiranyx/sidix-dora-persona-v1` (model, public)
- Kaggle dataset: `mighan/sidix-persona-qa-v1` (4.5MB, 7500 pairs)
- Kaggle kernel: `mighan/sidix-dora-persona-train-v1`

VPS automation:
- Cron `*/15 min /opt/sidix/scripts/sidix_kaggle_monitor.sh` → breadcrumb `/opt/sidix/.data/kaggle_kernel_state.json`

### 2.2 Iterasi log lengkap

| v | Status | Cell | Time | Root cause | Fix attempted | Verified via |
|---|---|---|---|---|---|---|
| 1 | ❌ | 5 | ~70s | Race condition: kernel push <5s setelah dataset upload, Kaggle backend belum sempat mount | Wait until indexed | dataset_files API confirm 2 files visible |
| 2 | 409+❌ | 5 | ~70s | Kernel id `sidix-dora-train-v1` mismatch dgn title-derived slug `sidix-dora-persona-train-v1` | Align id ke `mighan/sidix-dora-persona-train-v1` di kernel-metadata | Push v3 success message |
| 3 | ❌ | 5 | ~70s | Private dataset mount path: `/kaggle/input/datasets/<owner>/<slug>/` (bukan `/kaggle/input/<slug>/` untuk public datasets) | Auto-detect via `glob.glob('/kaggle/input/**/persona_qa_train.jsonl', recursive=True)` | **Diag kernel `mighan/sidix-diag-mount` (no GPU, 30s) os.walk('/kaggle/input/') → confirm path** |
| 4 | ❌ | 7 | ~150s | bitsandbytes 0.49.2 pre-built CUDA kernel incompat P100 (CC 6.0) | Drop quantization, bf16 + grad checkpoint | Log: `Error named symbol not found at line 62 in file /src/csrc/ops.cu` |
| 5 | ❌ | 7 | ~150s | peft 0.19.1 requires torchao≥0.16, Kaggle has 0.10 | Add `torchao>=0.16` to install | Log: `ImportError: Found incompatible torchao 0.10.0` |
| 6 | ❌ | 7 | ~150s | DoRA-specific CUDA op (`weight + scaling * lora_weight`) tidak ada kernel image untuk P100 | Try plain LoRA (use_dora=False) | Log: `cudaErrorNoKernelImageForDevice` di DoRA path |
| 7 | ❌ | 7 | ~150s | SAME error tanpa DoRA → fundamental. Modern PyTorch wheels skip SM_60 (P100) | **PIVOT TO RUNPOD** | Confirmed: bukan DoRA-specific, modern PEFT/torch CUDA path keseluruhan break di P100 |

**Total Kaggle iter**: 7 push + 1 diag + ~30 menit total tool time. **All free** (Kaggle GPU quota tidak charged).

### 2.3 Hipotesis kognitif yang muncul (note 288)

```
iteration_cost ∝ opacity(platform) × depth(assumption_stack)
```

Empirically validated:
- Kaggle = high opacity (logs only after fail) × deep stack (Python 3.12 × torch × PEFT × torchao × bitsandbytes × P100 SM_60)
- Result: 7 iter expected, bukan anomali

Pattern observation:
1. v1: timing/sync layer
2. v2: naming/slug layer
3. v3: filesystem mount layer
4. v4-v5: library version chain
5. v6-v7: hardware-software fundamental (CC mismatch)

Module proposals from this:
- `cloud_run_iterator.py` — abstract retry-with-fix loop dengan error classifier
- `multi_cloud_orchestrator.py` — primary (Kaggle) + fallback (RunPod) dengan auto-trigger pada CudaCompatError
- "Diagnostic-kernel-first" pattern → tambah ke CLAUDE.md kalau Sprint 14a approved

### 2.4 Kombinasi feasibility analysis (bos question 2026-04-29 evening)

Bos: *"bisa di kombinasi nggak kaggle sama runpod? kalo nggak bisa jangan"*

**Analysis**:

| Mode | Feasible? | Reason |
|---|---|---|
| Training mirror (sama train run paralel kedua platform) | ❌ NO | Kaggle P100 = fundamental block untuk modern PEFT, kernel binary mismatch |
| Mirror dengan smaller model (Qwen 3B) di Kaggle | ❌ NO | Bukan model size issue — PEFT ops universal break di SM_60 |
| Pin PEFT lama (<0.10) di Kaggle | ⚠️ Fragile | Defeats purpose (no DoRA, fragile dep stack) |
| **Artifact mirror** (adapter hasil RunPod → publish ke Kaggle Models post-training) | ✅ YES | Free, beneficial, kompatibel Kaggle inference ecosystem |

**Decision**: artifact mirror only (post-training). Process mirror SKIP.

---

## 3 · Phase 3b — RunPod pivot (ACTIVE 2026-04-29 evening)

### 3.1 Bos intel (screenshot RunPod console)

- Balance: $20.41 ✓ (sufficient for 50+ hours A4000 atau 25+ hours L4)
- Existing endpoints: vLLM v2.14.0 (24GB serverless, sidix LLM) + mighan-media-worker (48GB, 3 idle)
- Templates ready: **Axolotl Fine-Tuning** (axolotl-ai-cloud v0.16.0, supports LoRA/QLoRA/DPO)
- 43 GPU types available

### 3.2 GPU options (cost ascending)

| GPU | VRAM | CC | Cost/hr | Use case |
|---|---|---|---|---|
| RTX A4000 | 16GB | 8.6 | ~$0.20 | Cheapest training, fits Qwen 7B bf16 + LoRA |
| RTX 3090 | 24GB | 8.6 | ~$0.30 | More headroom |
| L4 | 24GB | 8.9 | ~$0.40 | Modern, efficient |
| V100 PCIe | 16GB | 7.0 | ~$0.40 | Proven, reliable |
| RTX 4090 | 24GB | 8.9 | ~$0.50 | Fastest |
| L40 | 48GB | 8.9 | ~$0.80 | Big model headroom |

**Selected**: RTX A4000 16GB ($0.20/hr × 3-5h ≈ $0.60-1.00)

### 3.3 Modules ready

- `training/runpod_train_lora.py` (220 lines) — standalone training, CLI args, auto HF upload
- `training/runpod_pod_orchestrator.py` (150 lines) — Pod create/monitor/terminate via runpod SDK
- GPU priority: `[A4000, 3090, L4, V100]` — auto-pick first available

### 3.4 Execution plan

```
1. python training/runpod_pod_orchestrator.py --action create
   → Pod created (~30s API call) → wait_pod_ready (~5-10 min boot)
2. SSH ke Pod (atau runpodctl exec)
3. Transfer dataset: scp train+val dari VPS atau wget dari HF dataset
4. pip install peft trl accelerate datasets transformers (Pod base image sudah ada PyTorch+CUDA)
5. python runpod_train_lora.py --use-dora --train-data <path> --val-data <path> --epochs 3
6. Adapter auto-upload ke Tiranyx/sidix-dora-persona-v1 (HF_TOKEN dari Pod env)
7. Monitor via stdout log polling
8. After complete: terminate Pod (avoid ongoing charge)
9. Verify HF repo files visible (adapter_*.safetensors ~150MB DoRA rank-16)
```

### 3.5 Decision gates

- Setelah training: verify training loss converge, val_loss <1.2, no NaN
- Run blind A/B test (`apps/brain_qa/brain_qa/blind_ab_test.py`) — target ≥80% accuracy
- Kalau ≥80%: ✅ promote, lanjut Phase 3c wire (note 287)
- Kalau 60-80%: iterasi Phase 3a iter2 (LLM-amplify dataset)
- Kalau <60%: rollback, root cause analysis

---

## 4 · Phase 3c — wire plan (POST-RUNPOD-TRAINING)

Detail di [note 287](287_sprint13_phase3c_dispatch_wire_plan.md):

1. Verify HF adapter LIVE
2. Wire `agent_react.py` persona dispatch via `persona_adapter_loader.select_adapter_for_request`
3. Wire RunPod inference path (multi-LoRA hot-swap atau set_adapter)
4. Update warmup script (download adapter di Pod boot)
5. Run blind A/B test → verify ≥80% gate
6. Decision: promote production / iterate / rollback

Modules sudah scaffold:
- `apps/brain_qa/brain_qa/persona_adapter_loader.py` (PersonaRouter, download_adapter STUB, select_adapter_for_request fallback)
- `apps/brain_qa/brain_qa/blind_ab_test.py` (50 prompts × 5 persona, auto-grader via signature_score, smoke test 92% verified)

---

## 5 · Files dan dokumen lahir Sprint 13

### Phase 3a (Q&A generator)
- [`apps/brain_qa/brain_qa/persona_qa_generator.py`](../../apps/brain_qa/brain_qa/persona_qa_generator.py)
- [`apps/brain_qa/brain_qa/merge_persona_dataset.py`](../../apps/brain_qa/brain_qa/merge_persona_dataset.py)
- [note 285](285_sprint13_dora_persona_qa_generator.md)

### Phase 3b infra
- [`training/sprint13_dora_persona_kaggle.ipynb`](../../training/sprint13_dora_persona_kaggle.ipynb) (7 versions iteratively)
- [`training/kernel-metadata.json`](../../training/kernel-metadata.json)
- [`training/runpod_train_lora.py`](../../training/runpod_train_lora.py) (NEW pivot)
- [`training/runpod_pod_orchestrator.py`](../../training/runpod_pod_orchestrator.py) (NEW pivot)
- [note 286 (Phase 3b handoff)](286_sprint13_phase3b_kaggle_handoff.md)

### Phase 3c scaffold
- [`apps/brain_qa/brain_qa/persona_adapter_loader.py`](../../apps/brain_qa/brain_qa/persona_adapter_loader.py)
- [`apps/brain_qa/brain_qa/blind_ab_test.py`](../../apps/brain_qa/brain_qa/blind_ab_test.py)
- [note 287 (Phase 3c plan)](287_sprint13_phase3c_dispatch_wire_plan.md)

### Cognitive synthesis
- [note 288 (iteration pattern → module proposal)](288_cognitive_synthesis_kernel_iteration_pattern.md)
- [note 289 (THIS — full journal)](289_sprint13_full_iteration_journal.md)

### Handoff docs
- [`docs/ROADMAP_DORA_SPRINT13.md`](../../docs/ROADMAP_DORA_SPRINT13.md)
- [`docs/SESSION_STATE_2026-04-29_sprint13_kaggle_running.md`](../../docs/SESSION_STATE_2026-04-29_sprint13_kaggle_running.md)
- [`docs/LIVING_LOG.md`](../../docs/LIVING_LOG.md) full mandatory loop trail

### Updates ke existing
- `docs/SIDIX_CONTINUITY_MANIFEST.md` — concept #14 PLANNED → IN_PROGRESS

---

## 6 · Cron + monitoring infrastructure

VPS:
- `/opt/sidix/scripts/sidix_kaggle_monitor.sh` — 15-min poll (kernel sudah abandoned, but cron stays for reference)
- `/opt/sidix/.data/kaggle_kernel_state.json` — last status breadcrumb
- `/opt/sidix/.data/kaggle_monitor.log` — append history
- `/opt/sidix/.env.kaggle_hf` (chmod 600) — KAGGLE_API_TOKEN, HF_TOKEN, KAGGLE_USERNAME (post-Sprint 13: REVOKE both tokens per security pattern)

---

## 7 · Untuk agent next session

1. **Cek RunPod Pod state**: `python training/runpod_pod_orchestrator.py --action list` → list pods running
2. **Cek HF repo**: `hf repos info Tiranyx/sidix-dora-persona-v1` → kalau ada adapter_model.safetensors → training selesai
3. **Cek `/opt/sidix/.data/runpod_training_log.txt`** — saya akan tulis status real-time waktu Pod jalan
4. **Decision tree**:
   - HF repo punya adapter file → Phase 3c wire (ikuti note 287)
   - HF repo masih empty + Pod RUNNING → tunggu
   - Pod ERROR → log inspect, iterate (kemungkinan small fix di runpod_train_lora.py)
   - Pod TERMINATED + no adapter → root cause analysis, mungkin spin Pod baru

---

## 8 · Sintesis 1 paragraf

Sprint 13 = **case study live untuk Pillar Pencipta**: bos minta DoRA persona (idea), saya iterate 7x di Kaggle (friction reveal architectural assumptions), pivot ke RunPod (constraint-driven pivot), capture pattern via note 288 (cognitive synthesis), document journey via note 289 (anti-mengulang). Setiap "kegagalan" v1-v7 = data input untuk module masa depan (`cloud_run_iterator`, `multi_cloud_orchestrator`). Itu = literal "cipta dari kekosongan" — module baru lahir dari friction, bukan dari rencana awal.
