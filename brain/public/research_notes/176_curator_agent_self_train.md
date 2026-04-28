# Curator Agent — Self-Train Curation Pipeline

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
**[FACT]** — 2026-04-21

## Apa itu
`curator_agent.py` adalah pipeline curation otomatis SIDIX yang menyaring dokumen corpus
(research notes, praxis lessons, audio AI sources) dan mengkonversi konten berkualitas
tinggi menjadi JSONL training pairs siap pakai untuk fine-tuning LoRA.

## Mengapa
SIDIX dirancang sebagai sistem yang tumbuh mandiri. Tanpa curation pipeline, konten
baru dari LearnAgent tidak akan pernah masuk ke LoRA fine-tuning. Curator adalah jembatan
antara corpus (pengetahuan deklaratif) dan model (pengetahuan terparameterisasi).

Filosofi maqashid memastikan data yang masuk ke model bukan hanya "relevan secara teknis"
tapi juga selaras dengan 5 tujuan besar: din, nafs, aql, nasl, mal.

## Bagaimana
**Scoring formula (0.0–1.0):**
```
composite = relevance×0.40 + sanad×0.25 + maqashid×0.20 + dedupe×0.15
```

- **relevance (40%)**: keyword density dari `RELEVANCE_BOOST_WORDS` (sidix, agent, llm,
  lora, qwen, python, fastapi, dll.) + bonus panjang dokumen (max 0.2)
- **sanad (25%)**: marker epistemik `[FACT]`→0.90, `[OPINION]`→0.65, `[SPECULATION]`→0.35,
  default netral 0.50
- **maqashid (20%)**: hitung berapa axis maqashid al-syariah yang muncul dalam teks
  (din/nafs/aql/nasl/mal) × 0.22 per axis
- **dedupe (15%)**: 1.0 jika konten baru (hash SHA-256), 0.0 jika sudah pernah diekspor

**Output format**: ChatML/Alpaca JSONL
```json
{"instruction": "Apa itu X?", "input": "", "output": "...", "source": "path", "score": 0.72, "timestamp": "..."}
```

**Cron target**: weekly Senin 03:00 UTC. Min 100 pairs/run.

## Contoh nyata
```python
from brain_qa.curator_agent import run_curation
r = run_curation(min_score=0.45, dry_run=True)
# r: {ok: True, scanned: 175, scored: 89, exported: 178, output_file: "..."}
```

## Keterbatasan
- **Heuristic scoring**: relevance berdasarkan keyword density, bukan semantic similarity.
  Bisa miss dokumen berkualitas tinggi yang tidak menggunakan kata kunci eksplisit.
- **Training pair quality**: pair dibangun dari 800-1600 karakter pertama dokumen.
  Konteks panjang yang lebih baik membutuhkan chunking lebih cerdas.
- **No quality gate per pair**: tidak ada LLM judge per pair saat ini. Sprint 5
  sudah ada `llm_judge.py` tapi belum diintegrasikan ke curation loop.
- **Cron dependency**: belum ada trigger otomatis di server. Harus dijalankan manual
  atau via systemd timer.

## Referensi implementasi
- `D:\MIGHAN Model\sprint5\apps\brain_qa\brain_qa\curator_agent.py`
- `docs/MASTER_ROADMAP_2026-2027.md` (Sprint 5 — T5.1)
