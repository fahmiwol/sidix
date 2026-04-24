# 205 — Auto-Training Flywheel (Self-Learning Loop)

**Tanggal:** 2026-04-24
**Agen:** Claude (Kimi Code CLI)
**Commit:** TBD (Sprint 12)

---

## Apa

Orchestrator otomatis yang menjalankan siklus **self-training** SIDIX:

```
[CHECK]  → Cek availability data (jariyah + synthetic + DPO + memory)
[EXPORT] → Gabungkan semua sumber ke JSONL training dataset
[TRAIN]  → Trigger QLoRA distillation (mock / local / Kaggle)
[EVAL]   → Benchmark before vs after (epistemic + relevance + source + honesty)
[DEPLOY] → Convert ke GGUF → Ollama create → hot reload
[LOG]    → Checkpoint version, metrics, rollback point
```

## Mengapa

Visi user eksplisit: **self-learning, self-training, self-improvement**. Tanpa flywheel otomatis, setiap improvement memerlukan intervensi manusia manual: export data → jalankan training → convert → deploy. Flywheel menghilangkan bottleneck ini.

## Bagaimana

### Komponen

| File | Fungsi |
|------|--------|
| `scripts/auto_train_flywheel.py` | Orchestrator utama — 6-step pipeline |
| `apps/brain_qa/brain_qa/eval_harness.py` | Benchmark: epistemic accuracy, source coverage, ROUGE-L, honesty rate |
| `scripts/ollama_deploy.py` | Merge adapter → GGUF → Ollama create → verify |
| `scripts/distillation/sidix_modelfile.txt` | Ollama Modelfile dengan conversational system prompt |

### Data Sources
1. **Jariyah pairs** — user feedback (thumbs_up + score≥0.7)
2. **Synthetic pairs** — generated dari corpus/research_notes
3. **DPO pairs** — Constitutional AI critique→revise→preference pairs
4. **Memory pairs** — high-confidence conversation turns (confidence≥0.8)

### Training Modes
- `mock` — simulate tanpa GPU (default, untuk test pipeline)
- `local` — QLoRA training di mesin lokal (butuh GPU + torch/peft)
- `kaggle` — trigger Kaggle notebook via API (planned)

### Eval Metrics
- **Epistemic accuracy** (40%): apakah label [FAKTA]/[OPINI]/[SPEKULASI]/[TIDAK TAHU] tepat?
- **Avg relevance** (30%): ROUGE-L vs reference answer
- **Source coverage** (20%): % jawaban yang menyertakan sanad/citation
- **Honesty rate** (10%): kalau expected unknown, apakah benar-benar bilang tidak tahu?

### Deploy Flow
1. Merge LoRA adapter ke base model (HF)
2. Convert HF → GGUF f16
3. Quantize ke q4_k_m
4. Build Modelfile dengan system prompt terbaru
5. `ollama create sidix-distilled -f Modelfile`
6. Verify via `/api/generate` test

## Contoh Nyata

Setup cron harian:
```bash
0 3 * * * cd /opt/sidix && python scripts/auto_train_flywheel.py >> logs/flywheel.log 2>&1
```

Dry run check:
```bash
python scripts/auto_train_flywheel.py --check-only
# Output: {"ready": true, "total": 732, "jariyah": 500, "synthetic": 200, "dpo": 32}
```

Full flywheel:
```bash
export FLYWHEEL_MIN_PAIRS=500
export FLYWHEEL_TRAIN_MODE=mock
export FLYWHEEL_AUTO_DEPLOY=false
python scripts/auto_train_flywheel.py --dry-run
```

## Keterbatasan
- Eval harness masih menggunakan static benchmark seed (5 questions). Perlu expand ke 50–100 diverse questions.
- Memory pairs extraction naif — tidak ada filtering untuk PII atau sensitive content.
- Kaggle mode belum di-implementasi (butuh Kaggle API key + notebook template).
- No automatic rollback kalau eval score after < before.

## Next Steps
1. Expand benchmark dataset ke 50+ questions across all epistemic types
2. Implement Kaggle API trigger untuk training di T4
3. Add automatic rollback: kalau eval_after < eval_before, jangan deploy
4. Add memory pair PII filter sebelum masuk training dataset
5. UI: tampilkan flywheel status di dashboard admin
