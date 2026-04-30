# Debate Ring — Multi-Agent Creative Debate Protocol

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
**[FACT]** — 2026-04-21

## Apa itu
`debate_ring.py` adalah sistem multi-agent debate untuk SIDIX di mana dua agent dengan
perspektif berbeda (Creator dan Critic) berdebat iteratif untuk menghasilkan output
kreatif yang lebih baik. Konsep: tidak ada output sempurna tanpa kritik, dan kritik
yang baik harus disertai revisi konkret.

## Mengapa
Satu model yang generate dan evaluate sendiri cenderung mengkonfirmasi bias awalnya.
Dengan memisahkan peran Creator (optimis, generatif) dan Critic (skeptis, evaluatif),
kita mendapatkan mekanisme self-correction yang lebih robust. Ini adalah implementasi
parsial dari "Adversarial Collaboration" dalam AI safety research.

Dalam konteks creative agency (brand, copy, campaign), debat ini memastikan output
memenuhi standar ganda: teknis kreatif (copywriter) dan strategis bisnis (campaign strategist).

## Bagaimana
**3 Standard Debate Pairs (Sprint 5):**

| Pair | Creator | Critic | Domain |
|------|---------|--------|--------|
| copy_vs_strategy | copywriter | campaign_strategist | content |
| brand_vs_design | brand_builder | design_critic | design |
| hook_vs_audience | script_hook | audience_lens | content |

**Flow per round (max 3):**
1. Critic evaluasi prototype → output: `SKOR:[1-10] | APPROVE:[ya/tidak] | KRITIK:[...]`
2. Jika skor ≥ 7.0 atau CQF ≥ DELIVERY_THRESHOLD → konsensus, stop
3. Creator revisi berdasarkan kritik → output: prototype baru
4. Ulang max 3 round

**LLM call chain:**
```
local_llm.generate_sidix() → fallback multi_llm_router.route_generate().text → fallback heuristic
```

**Note penting**: `route_generate()` mengembalikan `LLMResult` object, bukan string.
Perlu `.text` attribute untuk ekstrak hasil teks. Bug ini ditemukan saat smoke test Sprint 5
dan sudah difix.

**Consensus check**: LLM score + CQF heuristic double-check. Kalau salah satunya lulus
threshold → approved. Ini membuat sistem lebih toleran saat LLM parse gagal.

## Contoh nyata
```python
from brain_qa.debate_ring import debate_copy_vs_strategy
result = debate_copy_vs_strategy("Produk terbaik untuk kamu!", context="brand kuliner")
print(result.consensus)       # True/False
print(result.rounds_taken)    # 1-3
print(result.final_cqf)       # 6.94 (cqf heuristic pada smoke test)
print(result.final_prototype) # teks final setelah debate
```

## Keterbatasan
- **Parse dependency**: kritik dan revisi bergantung pada LLM mengikuti format exact.
  Saat LLM fallback ke heuristic, revisi hanya berupa append hint string — bukan revisi nyata.
- **Max 3 rounds**: cukup untuk mayoritas kasus, tapi konten kompleks mungkin butuh lebih.
- **Single domain per pair**: satu pair hanya bisa handle satu domain. Belum ada pair
  lintas domain (misal: brand + campaign sekaligus).
- **No memory across sessions**: setiap debate mulai fresh, tidak ada learning dari
  debate sebelumnya untuk pair yang sama.

## Referensi implementasi
- `D:\MIGHAN Model\sprint5\apps\brain_qa\brain_qa\debate_ring.py`
- `docs/CREATIVE_AGENT_TAXONOMY.md` (Debate pairs section)
