# Note 286 — Sprint 13 Phase 3b: Kaggle T4 DoRA Training Handoff

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sanad**: Sprint 13 Phase 3a (note 285) selesai → Phase 3b butuh action bos di luar lingkup agent.  
**Tanggal**: 2026-04-29  
**Status**: HANDOFF READY — bos action items listed di bawah.

---

## Apa yang sudah ready (sesi sebelumnya)

### Phase 3a — synthetic data pipeline LIVE

- ✅ `persona_qa_generator.py` — 5 persona × signature_voice templates
- ✅ `merge_persona_dataset.py` — combine + train/val split (90/10 stratified per persona)
- ✅ `training/sprint13_dora_persona_kaggle.ipynb` — Kaggle T4 notebook template
- ✅ 7500 pairs LIVE di VPS `/opt/sidix/.data/training/persona_qa_{PERSONA}.jsonl`
- ✅ Avg signature_score per persona: 0.639-0.767 (stable di scale 1500/persona)
- ✅ Cross-persona discrimination gap ≥0.43 semua persona

### Phase 3b deliverables yang ditambah sesi ini

- `apps/brain_qa/brain_qa/merge_persona_dataset.py`  
  → CLI: `python -m brain_qa merge_persona_dataset --val-ratio 0.10`  
  → Output: `persona_qa_train.jsonl` + `persona_qa_val.jsonl` + `persona_qa_stats.json`
- `training/sprint13_dora_persona_kaggle.ipynb`  
  → Notebook Jupyter Kaggle-ready (T4 16GB GPU, ~3-5 jam train)

---

## 🚦 Bos Action Items (sebelum jalan Kaggle)

### A. Persiapan dataset Kaggle

1. **SSH VPS, run merge**:
   ```bash
   ssh sidix-vps
   cd /opt/sidix && PYTHONPATH=/opt/sidix/apps/brain_qa python3 -m brain_qa merge_persona_dataset
   ```
   Output: `/opt/sidix/.data/training/persona_qa_{train,val}.jsonl`

2. **Download dari VPS ke laptop**:
   ```bash
   scp sidix-vps:/opt/sidix/.data/training/persona_qa_train.jsonl ./
   scp sidix-vps:/opt/sidix/.data/training/persona_qa_val.jsonl ./
   ```

3. **Upload ke Kaggle Dataset**:
   - Login Kaggle → Create Dataset → upload 2 file JSONL
   - Title: `sidix-persona-qa-v1`
   - Visibility: Private (recommended)
   - Catat slug: e.g. `tiranyx/sidix-persona-qa-v1`

### B. Persiapan Hugging Face

1. **Buat repo target di HF**:
   - URL: https://huggingface.co/Tiranyx/sidix-dora-persona-v1 (auto-create via notebook, atau manual)
   - Type: Model
   - Visibility: Public (atau private kalau preferensi)

2. **Generate HF token write access**:
   - https://huggingface.co/settings/tokens → New token → Write scope
   - Scope: `Tiranyx/sidix-dora-persona-v1` (atau "Read all + write to specific repos")
   - Copy token (akan dipakai di Kaggle Secrets)

### C. Setup Kaggle notebook

1. **New Notebook** di Kaggle → upload `training/sprint13_dora_persona_kaggle.ipynb`
2. **Add Data** → pilih dataset `sidix-persona-qa-v1` (yang upload di langkah A.3)
3. **Settings**:
   - Accelerator: **GPU T4 × 1** (atau T4 × 2 kalau tersedia, lebih cepat)
   - Internet: ON (untuk download base model + upload ke HF)
4. **Add-ons → Secrets** → tambah secret:
   - Label: `HF_TOKEN`
   - Value: token dari step B.2
5. **Adjust paths di notebook (Cell 2)** kalau slug Kaggle dataset beda:
   ```python
   DATA_DIR = '/kaggle/input/sidix-persona-qa-v1'  # match dataset slug
   HF_REPO = 'Tiranyx/sidix-dora-persona-v1'       # match HF target
   ```

### D. Run training

1. **Click "Run All"** — durasi ~3-5 jam untuk 7500 pairs × 3 epoch.
2. **Monitor**:
   - Cell 4 SFTTrainer logs: train_loss + eval_loss per epoch
   - Quality gate: eval_loss < 1.2, no NaN, train/eval gap < 0.3 (no overfitting)
3. **Saat selesai**:
   - Cell 5 auto-save ke `/kaggle/working/sidix-dora-persona-v1`
   - Cell 5 (HF upload) auto-push adapter weights
   - Cell 6 smoke test 5 persona (cek voice distinct di output)

---

## ⚠️ Risk + mitigation

| Risk | Mitigation |
|---|---|
| Kaggle T4 quota habis di tengah | Save checkpoint per epoch (`save_strategy=epoch` di SFTConfig). Resume dari last checkpoint kalau crash. |
| HF upload gagal | Manual upload via `huggingface-cli upload` setelah download adapter folder dari Kaggle. |
| eval_loss > 1.2 (under-fit) | Tambah epoch (3 → 5) atau increase LR (2e-4 → 3e-4). |
| eval_loss converge cepat tapi voice tidak distinct | Phase 3a iter2: LLM-amplify dataset untuk diversity boost (rerun gen_persona_qa dengan amplify mode), atau pisahkan jadi 5 adapter terpisah (mode PER_PERSONA_ADAPTER). |
| Overfitting (train_loss << eval_loss) | Reduce epoch atau add dropout (lora_dropout 0.05 → 0.10). |

---

## Phase 3c — Deploy plan (post training)

Setelah HF upload sukses, sesi berikutnya saya akan:

1. Update `runpod` warmup script untuk download adapter dari `Tiranyx/sidix-dora-persona-v1`
2. Update `local_llm.py` / inference flow untuk multi-LoRA hot-swap (vLLM `lora_modules`)
3. Update `agent_react.py` persona dispatch: persona name → load matching adapter slot
4. Blind A/B test design: 50 prompts × 5 persona, human grader → measure persona accuracy

Quality gate Phase 3c: blind test accuracy ≥80% (target dari roadmap).

---

## Filosofi (kenapa DoRA bukan LoRA biasa)

DoRA = **Weight-Decomposed Low-Rank Adaptation** (Liu et al, ICML 2024, https://arxiv.org/abs/2402.09353).

- LoRA: `W' = W + AB` (rank-decomposed delta)
- DoRA: `W' = m · (W + AB) / |W + AB|` (decompose ke magnitude `m` + direction `(W+AB)/|...|`)

Untuk persona stylometry, DoRA **lebih baik dari LoRA** karena:
- Persona = direction shift di output distribution (voice/tone) lebih dari magnitude
- DoRA decompose magnitude vs direction → adaptasi direction lebih clean
- Empiris: DoRA paper show 1-2% better than LoRA pada same rank
- Trade-off: 2-3% slower training, but worth it untuk stylometry use case

`use_dora=True` di PEFT 0.13+ — sudah di notebook config.

---

## Compound chain

```
Phase 3a (note 285) ✓                   Phase 3b (BOS RUN)             Phase 3c (next session)
─────────────────────                    ────────────────────            ────────────────────
gen_persona_qa LIVE       →   merge train/val split    →    Kaggle T4 DoRA train    →   HF upload   →   RunPod multi-LoRA wire   →   blind A/B test
7500 pairs                       10% holdout                 ~3-5 jam                  Tiranyx/sidix-dora-persona-v1     persona dispatch                ≥80% accuracy
                                                                                                                                                          target
```

Bos handle Phase 3b (Kaggle), saya prep Phase 3c arsitektur sambil nunggu adapter upload sukses.
