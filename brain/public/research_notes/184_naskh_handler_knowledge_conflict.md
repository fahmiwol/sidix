# 184 — Naskh Handler: Resolusi Konflik Knowledge (Competitive Advantage)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-23
**Sanad:** [OPINION] — adaptasi konsep ushul fiqh ke sistem AI
**Tags:** naskh, corpus-management, knowledge-conflict, competitive-advantage, ihos

---

## Apa

`naskh_handler.py` mengimplementasikan mekanisme **resolusi konflik knowledge**
yang terinspirasi dari konsep **Naskh** dalam ilmu ushul fiqh.

Naskh (النسخ) = mekanisme dalam ilmu Al-Quran/Hadits untuk menentukan
"ayat atau hadits mana yang memperbarui yang lain" — sehingga tidak ada
kontradiksi tersembunyi dalam corpus hukum Islam.

---

## Mengapa — Diferensiasi vs AI Lain

**Problem AI mainstream**: Model seperti GPT/Gemini "lupa" knowledge lama saat retrain
(catastrophic forgetting). Mereka tidak punya mekanisme eksplisit untuk mengelola
kontradiksi antara knowledge lama dan baru.

**SIDIX approach**:
- Frozen core (base weights) tidak pernah dimodifikasi sembarangan
- Setiap knowledge baru yang masuk corpus diproses via NaskhHandler
- Hasilnya: SIDIX tahu "knowledge ini sudah diperbarui oleh yang itu"
- Ini adalah **competitive advantage unik** yang tidak dimiliki AI komersial lain

---

## Bagaimana

### Tier Ranking (Sanad Tier)

```
primer      (4) → teks primer / sumber orisinil / wahyu
ulama       (3) → scholar / pakar bidang
peer_review (2) → jurnal / riset terkurasi
aggregator  (1) → Wikipedia, blog, agregator umum
```

### Resolution Rules

| Kondisi                                  | Status       | Tindakan                     |
|------------------------------------------|--------------|------------------------------|
| Tier baru > tier lama                    | superseded   | Ganti dengan yang baru       |
| Tier sama + tanggal lebih baru           | updated      | Update dengan yang lebih baru|
| Tier sama + confidence jauh lebih tinggi | updated      | Update berdasarkan confidence|
| Tier sama + kondisi seimbang             | conflict     | Keduanya disimpan + [CONFLICT]|
| Tier baru < tier lama                    | retained     | Pertahankan yang lama        |
| is_frozen = True                         | retained     | TIDAK PERNAH digantikan      |

---

## Contoh Nyata

```python
from brain_qa.naskh_handler import NaskhHandler, KnowledgeItem
from datetime import datetime, timezone

handler = NaskhHandler()

old_item = KnowledgeItem(
    content="Inflasi Indonesia 2025 = 3.1%",
    source="blog_ekonomi.com",
    sanad_tier="aggregator",
    date_added=datetime(2025, 1, 1, tzinfo=timezone.utc),
    topic="inflasi-indonesia-2025",
    confidence=0.7,
)

new_item = KnowledgeItem(
    content="Inflasi Indonesia 2025 = 2.8% (data BPS resmi)",
    source="bps.go.id",
    sanad_tier="primer",
    date_added=datetime(2025, 6, 1, tzinfo=timezone.utc),
    topic="inflasi-indonesia-2025",
    confidence=0.99,
)

corpus = [old_item]
corpus, logs = handler.add_to_corpus(new_item, corpus)
# logs → ["[Naskh] Tier lebih tinggi: primer > aggregator"]
# corpus → [new_item] (old digantikan)
```

---

## Integrasi Roadmap

- **v0.1 (sekarang)**: Standalone module, bisa dipanggil manual
- **v0.2**: Integrasi ke `corpus_to_training.py` — setiap batch training pakai NaskhHandler
- **v0.3**: Integrasi ke `learn_agent.py` — setiap knowledge baru dari web auto-resolve
- **v0.4**: API endpoint `POST /corpus/add` menggunakan NaskhHandler

---

## Keterbatasan

1. `topic` matching masih string exact match — perlu embedding similarity untuk topik mirip
2. Frozen items (`is_frozen=True`) harus di-set manual saat ingestion — belum otomatis
3. Conflict log belum persisten ke file — hanya in-memory saat runtime
4. Belum ada UI untuk review [CONFLICT] items

---

## Referensi

- `apps/brain_qa/brain_qa/naskh_handler.py`
- Konsep: sidix_handoff_kimi_to_claude.html §Naskh Handler Design
- Ushul Fiqh: Kitab Naskh wa Mansukh (ilmu Al-Quran)
