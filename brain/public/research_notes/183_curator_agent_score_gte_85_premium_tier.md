# Curator Agent — Score ≥ 0.85 Premium Tier
**[FACT]** — 2026-04-21

## Apa itu
Penambahan `PREMIUM_SCORE = 0.85` ke `curator_agent.py` untuk memisahkan
training pairs berkualitas tertinggi (composite score ≥ 0.85) ke file kumulatif
`.data/lora_premium_pairs.jsonl`. File ini adalah feed khusus untuk LoRA premium
tier — hanya dokumen terbaik corpus yang masuk ke sini.

## Mengapa
LoRA fine-tuning peka terhadap noise. Jika semua 600 pairs/run masuk ke training
tanpa filter ketat, pairs berkualitas rendah akan "mencairkan" signal dari pairs
terbaik. Premium file memungkinkan dua mode training:

1. **Standard LoRA** — `curated_YYYY-MM-DD.jsonl` (min 0.45, hingga 600 pairs)
   → untuk general knowledge update
2. **Premium LoRA** — `lora_premium_pairs.jsonl` (score ≥ 0.85, kumulatif)
   → untuk high-fidelity domain expertise fine-tuning

## Bagaimana
Perubahan minimal di `run_curation()`:

```python
PREMIUM_SCORE = 0.85
_PREMIUM_FILE = _BASE.parent / ".data" / "lora_premium_pairs.jsonl"

# dalam loop build training pairs:
pairs = _build_training_pairs(doc, text)
all_pairs.extend(pairs)
if doc.score >= PREMIUM_SCORE:
    premium_pairs.extend(pairs)

# setelah loop, saat dry_run=False:
if premium_pairs:
    with open(_PREMIUM_FILE, "a", ...) as pf:  # append, bukan overwrite
        ...
```

**Kenapa append (bukan overwrite)?** Premium pairs dikumpulkan dari banyak run
mingguan. File ini tumbuh bertahap. Overwrite akan menghapus pairs dari run
sebelumnya yang sudah teruji.

**Stats baru yang dikembalikan:**
```python
{
  "premium_pairs_written": 12,   # berapa pairs masuk premium file run ini
  "premium_file": ".data/lora_premium_pairs.jsonl",
}
```

## Hubungan dengan scoring (0.0–1.0 scale)
Composite scorer curator menggunakan 0.0–1.0. Threshold 0.85 ini setara dengan
8.5/10 pada `llm_judge.py` — sama dengan `PREMIUM_THRESHOLD` di LLM Judge.
Konsistensi ini disengaja: kelak jika `llm_judge` diintegrasikan ke curation loop
(Sprint 7), score-nya akan comparable.

## Contoh nyata
```python
from brain_qa.curator_agent import run_curation, PREMIUM_SCORE
r = run_curation(dry_run=False)
# r["exported"] = 187
# r["premium_pairs_written"] = 14  ← masuk lora_premium_pairs.jsonl
# r["premium_file"] = ".data/lora_premium_pairs.jsonl"
```

## Keterbatasan
- **Masih heuristic**: premium selection berdasarkan keyword density + sanad marker,
  bukan LLM semantic judgment. Dokumen bagus tanpa explicit keyword bisa terlewat.
- **Dedup belum per-file**: jika dokumen sudah ada di premium file dari run lalu,
  ia bisa muncul lagi jika `curator_seen_hashes` belum merekamnya (hash-based dedup
  mencegah duplicasi antar run, tapi tidak mencegah pair identik dari hash berbeda).
- **LLM Judge belum terintegrasi**: `llm_judge.py` (Sprint 5 T5.4) belum dipanggil
  per pair di curation loop. Integrasi dijadwalkan Sprint 7.

## Referensi implementasi
- `apps/brain_qa/brain_qa/curator_agent.py` — `PREMIUM_SCORE`, `_PREMIUM_FILE`
- `brain/public/research_notes/176_curator_agent_self_train.md` — context lengkap pipeline
- `brain/public/research_notes/179_llm_judge_evaluator.md` — llm_judge.py spec
- `docs/MASTER_ROADMAP_2026-2027.md` Sprint 5 §3.2, Sprint 6 Quick Wins
