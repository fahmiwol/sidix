# Pelajaran Praxis — jejak agen SIDIX

**Diperbarui:** 2026-07-11T18:15:31.203813+00:00
**session_id:** `befffd08`
**persona:** ABOO

## Pertanyaan / tugas pengguna

Apa kepanjangan HTTP?

## Rangkaian eksekusi (Thought → Action → Observation)

### Langkah 0

- **Thought:** Pertanyaan faktual umum. Cari konteks di korpus dulu sebelum LLM: 'Apa kepanjangan HTTP?'.
- **Action:** `search_corpus` — args: `{"query": "Apa kepanjangan HTTP?", "k": 3, "persona": "ABOO", "_citations": [{"n": "1", "source_path": "praxis/lessons/lesson_20260429_efcdc07c.md", "source_title": "Pelajaran Praxis — jejak agen SIDIX", "chunk_id": "praxis/lessons/lesson_20260429_efcdc07c.md:0-1200", "sanad_tier": "unknown"}, {"n": "2", "source_path": "research_notes/298_sigma2_latency_entity_fix_20260430.md", "source_title": "Sigma-2: Latency & Entity Extraction Fixes", "chunk_id": "research_notes/298_sigma2_latency_entity_fix_20260430.md:1050-2250", "sanad_tier": "unknown"}]}`
- **Observation (cuplikan):** Q: Apa kepanjangan HTTP?

Konteks Memori (prinsip & preferensi aktif):
- 📌 Prinsip [Kejujuran & realisme dulu]: Saya lebih suka jawaban yang jujur, realistis, dan bertahap. Kalau sesuatu belum bisa dicapai cepat, jelaskan alternatif yang paling dekat dan langkah kecil yang bisa dilakukan hari ini.
- ⚙️ Preferensi [Jawaban ringkas, actionable]: Saya suka jawaban singkat tapi bisa langsung dieksekusi: checklist, template, dan contoh nyata. Hindari teori panjang tanpa langkah praktis.
- 📌 Prinsip [IHOS: jujur & rendah hati]: Kalau belum ada sumber/pengetahuan, bilang tidak tahu. Pisahkan fakta vs

### Langkah 1

- **Thought:** Hasil corpus tipis/gagal. Fallback: kutipan Wikipedia (API resmi, allowlist).
- **Action:** `search_web_wikipedia` — args: `{"query": "Apa kepanjangan HTTP?", "lang": "id", "_citations": [{"type": "wikipedia", "n": "1", "title": "HTTPS", "url": "https://id.wikipedia.org/wiki/HTTPS", "snippet": "Protocol Secure (HTTPS) adalah ekstensi dari Hypertext Transfer Protocol (HTTP). Ini digunakan untuk komunikasi aman melalui jaringan komputer, dan banyak", "lang": "id"}, {"type": "wikipedia", "n": "2", "title": "Protokol Transfer Hiperteks", "url": "https://id.wikipedia.org/wiki/Protokol_Transfer_Hiperteks", "snippet": "deprecated , disingkat HTTP) adalah protokol pada lapisan aplikasi untuk sistem informasi hypermedia yan`
- **Observation (cuplikan):** [web:wikipedia:id] Kutipan ringkas hasil pencarian (allowlist: id.wikipedia.org):

**1. HTTPS**
- URL: https://id.wikipedia.org/wiki/HTTPS
- Kutipan: Protocol Secure (HTTPS) adalah ekstensi dari Hypertext Transfer Protocol (HTTP). Ini digunakan untuk komunikasi aman melalui jaringan komputer, dan banyak

**2. Protokol Transfer Hiperteks**
- URL: https://id.wikipedia.org/wiki/Protokol_Transfer_Hiperteks
- Kutipan: deprecated , disingkat HTTP) adalah protokol pada lapisan aplikasi untuk sistem informasi hypermedia yang terdistribusi dan kolaboratif. HTTP adalah dasar komunikasi

**3. Ada Apa den

### Langkah 2

- **Thought:** Sudah ada hasil Wikipedia. Rangkai final answer dengan label sumber web.
- **Final (cuplikan):** [SIDIX] Gagal load model: No module named 'torch'
Pastikan: pip install torch transformers peft accelerate bitsandbytes (di Windows, bitsandbytes bisa butuh setup khusus atau gunakan WSL/CUDA).

## Jawaban akhir (ringkas)

[SIDIX] Gagal load model: No module named 'torch'
Pastikan: pip install torch transformers peft accelerate bitsandbytes (di Windows, bitsandbytes bisa butuh setup khusus atau gunakan WSL/CUDA).

## Cuplikan orkestrasi

```text
SIDIX OrchestrationPlan (deterministik)
request_persona=ABOO router=AYMAN
router_reason: score=1; signals=creative/design; conf=0.63

Archetype scores:
  - deduce: 0.000
  - connect: 1.000
  - invent: 0.000
  - synthesize: 0.000
  - orient: 0.350

Satellite weights (inspirasi fiksi / dev labels):
  - edison: 0.0000
  - pythagoras: 0.8772
  - shaka: 0.0000
  - lilith: 0.0000
  - atlas: 0.0000
  - york: 0.1228

Suggested phase order:
  1. [connect] persona~HAYFAR -> Tebalkan batas API/protokol; minimalkan permukaan serangan.
  2. [orient] persona~INAN -> Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit.

JSON:
{"request_persona": "ABOO", "router_persona": "AYMAN", "router_reason": "score=1; signals=creative/design; conf=0.63", "archetype_scores": {"deduce": 0.0, "connect": 1.0, "invent": 0.0, "synthesize": 0.0, "orient": 0.35}, "satellite_weights": {"edison": 0.0, "pythagoras": 0.8772, "shaka": 0.0, "lilith": 0.0, "atlas": 0.0, "york": 0.1228}, "phases": [{"archetype": "connect", "persona": "HAYFAR", "hint": "Tebalkan batas API/protokol; minimalkan permukaan serangan."}, {"archetype": "orient", "persona": "INAN", "hint": "Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit."}]}
```

## Untuk SIDIX — cara berpikir seperti agen eksekutor

1. **Rekam dulu:** salin pertanyaan, persona, dan setiap *thought* sebelum bertindak.
2. **Pilah:** bedakan faktual (butuh korpus) vs meta (orkestrasi) vs implementasi (sandbox).
3. **Pilih alat:** satu tool per langkah; evaluasi observasi sebelum lanjut atau final.
4. **Batasi risiko:** jangan sebar secret; potong observasi panjang; hormati `corpus_only` / web fallback.
5. **Tutup dengan jawaban:** rangkum sumber + langkah berikutnya; akui ketidakpastian bila perlu.

_Tag: #praxis #sidix-agent #meta-learning_
