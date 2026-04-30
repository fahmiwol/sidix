# Prompt Optimizer — Self-Evolution Level 1 (L1)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
**[FACT]** — 2026-04-21

## Apa itu

`prompt_optimizer.py` adalah modul SIDIX Sprint 5 yang mengimplementasikan **Self-Evolution Level 1 (L1)**: optimisasi prompt template secara otomatis berdasarkan output yang sudah diterima (accepted outputs, CQF ≥ 7.0).

Terinspirasi dari arsitektur DSPy (Bayesian prompt search), namun dibangun **own-stack** tanpa import library DSPy — cocok dengan prinsip SIDIX "Own Your Stack (IHOS)".

## Mengapa

Prompt template statis tidak optimal selamanya. Seiring agent menghasilkan output berkualitas tinggi, pola-pola tersebut bisa dijadikan **few-shot examples** untuk meningkatkan output berikutnya — tanpa perlu modifikasi bobot model (LoRA retrain).

Referensi dari `sidix_technical_architecture_ref.md §7.2`:
> *"Auto-optimize using production data... optimized_module = optimizer.compile(CopywriterModule(), trainset=last_100_accepted_outputs)"*

Ini adalah **data flywheel**: semakin banyak output diterima → prompt semakin baik → output baru semakin baik → siklus berlanjut.

## Bagaimana

### Pipeline L1

```
accepted_outputs.jsonl (log output CQF ≥ 7.0)
  → load top-K by score (default K=4)
  → build few-shot block dari output terbaik
  → inject ke base template agent
  → generate + evaluate 3 sample
  → bandingkan: optimized_score vs baseline_score
  → jika improvement ≥ 0.3 → simpan versi baru
  → jika tidak → rollback ke versi lama
```

### Fungsi utama

```python
# Catat output yang diterima (dipanggil oleh pipeline setelah quality gate)
log_accepted_output(agent, prompt_params, output_text, score, domain)

# Optimalkan satu agent
result = optimize_prompt(agent="copywriter", domain="content", force=False, dry_run=False)
# → OptimizeResult: ok, version, baseline_score, optimized_score, improvement, accepted

# Ambil template aktif (base atau optimized)
prompt = get_active_prompt(agent="copywriter")

# Optimalkan semua agents sekaligus (cocok untuk cron weekly)
optimize_all_agents(dry_run=False, force=False)
```

### Versioning

Setiap versi disimpan di `.data/optimized_prompts/<agent>_v<NNN>.json`. Rollback otomatis: kalau versi baru lebih buruk, versi lama tetap `active=True`.

## Contoh nyata

Skenario: copywriter sudah hasilkan 30+ caption dengan skor rata-rata 7.8. Top-4 caption diambil sebagai few-shot. Prompt baru dites di 3 sampel → rata-rata 8.2 → improvement +0.4 ≥ threshold 0.3 → versi baru disimpan sebagai `copywriter_v001.json`.

## Keterbatasan

1. **Minimum samples**: butuh ≥ 20 accepted outputs per agent sebelum bisa dioptimalkan (bisa di-override dengan `force=True`).
2. **LLM dependency**: evaluasi pakai `llm_judge` atau `quality_gate` fallback — kalau LLM offline, fallback ke heuristic scoring.
3. **Bukan LoRA**: ini L1 (prompt-level), bukan L2 (weight modification). Untuk peningkatan lebih dalam butuh LoRA retrain (L2, modul `auto_lora.py`).
4. **Few-shot context window**: terlalu banyak demos → prompt terlalu panjang → LLM lokal (7B) bisa degradasi. Dibatasi `TOP_K_DEMOS=4`.
5. **Domain mismatch**: demo dari domain A tidak bisa dipakai untuk domain B — tiap agent punya `_ACCEPTED_LOG` yang difilter by `agent` field.

## Relasi ke modul lain

- `llm_judge.py` → dipakai untuk scoring saat evaluasi prompt baru
- `creative_quality.py` → fallback scoring via `quality_gate()`
- `curator_agent.py` → L1 untuk corpus; prompt_optimizer → L1 untuk prompt templates
- `auto_lora.py` → L2 weight modification (retrain LoRA); prompt_optimizer feed data ke sana
- `agent_tools.py` → tool `prompt_optimizer` (permission: restricted, karena modifikasi template)
