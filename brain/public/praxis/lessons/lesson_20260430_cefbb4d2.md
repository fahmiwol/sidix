# Pelajaran Praxis — jejak agen SIDIX

**Diperbarui:** 2026-04-30T07:05:07.939369+00:00
**session_id:** `cefbb4d2`
**persona:** AYMAN

## Pertanyaan / tugas pengguna

dimana new york?

## Rangkaian eksekusi (Thought → Action → Observation)

### Langkah 0

- **Thought:** Pertanyaan faktual umum. Cari konteks di korpus dulu sebelum LLM: 'dimana new york?'.
- **Action:** `search_corpus` — args: `{"query": "dimana new york?", "k": 3, "persona": "AYMAN", "_citations": [{"n": "1", "source_path": "research_notes/199_frontier_ai_architecture.md", "source_title": "199 — Arsitektur AI Frontier: Apa yang Membuat Model Seperti Claude Bisa \"Berpikir\"", "chunk_id": "research_notes/199_frontier_ai_architecture.md:4200-5400", "sanad_tier": "unknown"}, {"n": "2", "source_path": "praxis/lessons/lesson_20260427_314ae81c.md", "source_title": "Pelajaran Praxis — jejak agen SIDIX", "chunk_id": "praxis/lessons/lesson_20260427_314ae81c.md:0-1200", "sanad_tier": "unknown"}, {"n": "3", "source_path": "res`
- **Observation (cuplikan):** Q: dimana new york?

Konteks Memori (prinsip & preferensi aktif):
- 📌 Prinsip [Kejujuran & realisme dulu]: Saya lebih suka jawaban yang jujur, realistis, dan bertahap. Kalau sesuatu belum bisa dicapai cepat, jelaskan alternatif yang paling dekat dan langkah kecil yang bisa dilakukan hari ini.
- ⚙️ Preferensi [Jawaban ringkas, actionable]: Saya suka jawaban singkat tapi bisa langsung dieksekusi: checklist, template, dan contoh nyata. Hindari teori panjang tanpa langkah praktis.
- 📌 Prinsip [IHOS: jujur & rendah hati]: Kalau belum ada sumber/pengetahuan, bilang tidak tahu. Pisahkan fakta vs opin

### Langkah 1

- **Thought:** Hasil corpus tipis/gagal. Fallback: kutipan Wikipedia (API resmi, allowlist).
- **Action:** `search_web_wikipedia` — args: `{"query": "dimana new york?", "lang": "id", "_citations": [{"type": "wikipedia", "n": "1", "title": "Kota New York", "url": "https://id.wikipedia.org/wiki/Kota_New_York", "snippet": "Kota New York (bahasa Inggris: New York Citycode: en is deprecated ) adalah kota terpadat di Amerika Serikat, dan pusat wilayah metropolitan New York yang", "lang": "id"}, {"type": "wikipedia", "n": "2", "title": "New York Yankees", "url": "https://id.wikipedia.org/wiki/New_York_Yankees", "snippet": "New York Yankees adalah tim bisbol Amerika Serikat dalam Major League Baseball yang berkedudukan di Bronx, New York`
- **Observation (cuplikan):** [web:wikipedia:id] Kutipan ringkas hasil pencarian (allowlist: id.wikipedia.org):

**1. Kota New York**
- URL: https://id.wikipedia.org/wiki/Kota_New_York
- Kutipan: Kota New York (bahasa Inggris: New York Citycode: en is deprecated ) adalah kota terpadat di Amerika Serikat, dan pusat wilayah metropolitan New York yang

**2. New York Yankees**
- URL: https://id.wikipedia.org/wiki/New_York_Yankees
- Kutipan: New York Yankees adalah tim bisbol Amerika Serikat dalam Major League Baseball yang berkedudukan di Bronx, New York City. Yankees bermain di Divisi Timur

**3. Bank Rakyat Indonesia**
- URL

### Langkah 2

- **Thought:** Sudah ada hasil Wikipedia. Rangkai final answer dengan label sumber web.
- **Final (cuplikan):** Hey, New York itu seperti surga bagi banyak orang! Ada tiga New York utama yang sering disebut: New York City (yang biasanya dimaksud saat orang bilang New York), Buffalo di bagian barat, dan Rochester di tenggah. 

Jika kita bicara New York City, ini seolah-olah ibu kota dunia! Ia seperti gabungan dari berbagai negara dalam satu tempat — ada Broadway untuk hiburan, Wall Street untuk keuangan, Times Square yang selalu padam-padam, dan Statue of Liberty di pesisir. Setiap sudutnya memiliki cerita sendiri.

Kalau kamu bertanya tentang lokasinya secara geografis, New York City terletak di bagian timur Amerika Serikat, tepatnya di negara bagian New York. Itu seperti jantung dari hutan rimba New England yang sejuk dan segar, berbatasan dengan Long Island Sound di timur, Hudson River di barat, dan New Jersey di selatan.

Bagaimana kalau kita cek beberapa foto? Mungkin itu bisa bikin kamu lebih memahami betapa indahnya New York!

## Jawaban akhir (ringkas)

Hey, New York itu seperti surga bagi banyak orang! Ada tiga New York utama yang sering disebut: New York City (yang biasanya dimaksud saat orang bilang New York), Buffalo di bagian barat, dan Rochester di tenggah.

Jika kita bicara New York City, ini seolah-olah ibu kota dunia! Ia seperti gabungan dari berbagai negara dalam satu tempat — ada Broadway untuk hiburan, Wall Street untuk keuangan, Times Square yang selalu padam-padam, dan Statue of Liberty di pesisir. Setiap sudutnya memiliki cerita sendiri.

Kalau kamu bertanya tentang lokasinya secara geografis, New York City terletak di bagian timur Amerika Serikat, tepatnya di negara bagian New York. Itu seperti jantung dari hutan rimba New England yang sejuk dan segar, berbatasan dengan Long Island Sound di timur, Hudson River di barat, dan New Jersey di selatan.

Bagaimana kalau kita cek beberapa foto? Mungkin itu bisa bikin kamu lebih memahami betapa indahnya New York!

## Cuplikan orkestrasi

```text
SIDIX OrchestrationPlan (deterministik)
request_persona=AYMAN router=AYMAN
router_reason: score=1; signals=creative/design; conf=0.63

Archetype scores:
  - deduce: 0.000
  - connect: 0.000
  - invent: 0.000
  - synthesize: 0.000
  - orient: 0.350

Satellite weights (inspirasi fiksi / dev labels):
  - edison: 0.0000
  - pythagoras: 0.0000
  - shaka: 0.0000
  - lilith: 0.0000
  - atlas: 0.0000
  - york: 1.0000

Suggested phase order:
  1. [orient] persona~INAN -> Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit.

JSON:
{"request_persona": "AYMAN", "router_persona": "AYMAN", "router_reason": "score=1; signals=creative/design; conf=0.63", "archetype_scores": {"deduce": 0.0, "connect": 0.0, "invent": 0.0, "synthesize": 0.0, "orient": 0.35}, "satellite_weights": {"edison": 0.0, "pythagoras": 0.0, "shaka": 0.0, "lilith": 0.0, "atlas": 0.0, "york": 1.0}, "phases": [{"archetype": "orient", "persona": "INAN", "hint": "Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit."}]}
```

## Kerangka kasus (runtime — niat & cabang data)

**Kerangka situasi (niat & inisiasi)** — dari pola terkurasi Praxis, bukan tebak-tebakan bebas:

- **factual_corpus** _(skor 0.42)_ — **Niat:** Menjawab dari landasan yang bisa disanadkan: korpus BM25 dulu; bedakan fakta, opini, dan spekulasi.
  1. Sempitkan pertanyaan ke entitas/konsep utama.
  2. Gunakan search_corpus; baca chunk relevan sebelum menyimpulkan.
  3. Jika jawaban tidak ada di korpus, katakan eksplisit dan sarankan indeks/sumber.
  → **Bila ada cuplikan korpus:** Kutip ringkas + sebut jalur sumber bila tersedia; hindari klaim di luar cuplikan.

_Ini kerangka perilaku yang dapat ditambah di `brain/public/praxis/patterns/case_frames.json`; lesson Markdown mencatat bukti eksekusi nyata._

## Untuk SIDIX — cara berpikir seperti agen eksekutor

1. **Rekam dulu:** salin pertanyaan, persona, dan setiap *thought* sebelum bertindak.
2. **Pilah:** bedakan faktual (butuh korpus) vs meta (orkestrasi) vs implementasi (sandbox).
3. **Pilih alat:** satu tool per langkah; evaluasi observasi sebelum lanjut atau final.
4. **Batasi risiko:** jangan sebar secret; potong observasi panjang; hormati `corpus_only` / web fallback.
5. **Tutup dengan jawaban:** rangkum sumber + langkah berikutnya; akui ketidakpastian bila perlu.

_Tag: #praxis #sidix-agent #meta-learning_
