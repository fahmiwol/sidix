# Pelajaran Praxis — jejak agen SIDIX

**Diperbarui:** 2026-05-01T21:57:36.651910+00:00
**session_id:** `cfaa4ceb`
**persona:** UTZ

## Pertanyaan / tugas pengguna

[PERTANYAAN UTAMA] Apa itu ML?

## Rangkaian eksekusi (Thought → Action → Observation)

### Langkah 0

- **Thought:** Topik umum/non-SIDIX. Jawab langsung dari kemampuan model dulu, lalu gunakan corpus hanya bila diminta.
- **Final (cuplikan):** Hmm, soal ini belum ada di knowledge base SIDIX, tapi menurut pemahaman saya:

[Tulis jawaban dari pengetahuan model di sini — jangan bilang 'tidak tahu']

Kalau lo butuh sumber yang lebih solid, bilang aja, nanti gue cariin.

## Jawaban akhir (ringkas)

Hmm, soal ini belum ada di knowledge base SIDIX, tapi menurut pemahaman saya:

[Tulis jawaban dari pengetahuan model di sini — jangan bilang 'tidak tahu']

Kalau lo butuh sumber yang lebih solid, bilang aja, nanti gue cariin.

## Cuplikan orkestrasi

```text
SIDIX OrchestrationPlan (deterministik)
request_persona=UTZ router=AYMAN
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
{"request_persona": "UTZ", "router_persona": "AYMAN", "router_reason": "score=1; signals=creative/design; conf=0.63", "archetype_scores": {"deduce": 0.0, "connect": 0.0, "invent": 0.0, "synthesize": 0.0, "orient": 0.35}, "satellite_weights": {"edison": 0.0, "pythagoras": 0.0, "shaka": 0.0, "lilith": 0.0, "atlas": 0.0, "york": 1.0}, "phases": [{"archetype": "orient", "persona": "INAN", "hint": "Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit."}]}
```

## Kerangka kasus (runtime — niat & cabang data)

**Kerangka situasi (niat & inisiasi)** — dari pola terkurasi Praxis, bukan tebak-tebakan bebas:

- **factual_corpus** _(skor 0.42)_ — **Niat:** Menjawab dari landasan yang bisa disanadkan: korpus BM25 dulu; bedakan fakta, opini, dan spekulasi.
  1. Sempitkan pertanyaan ke entitas/konsep utama.
  2. Gunakan search_corpus; baca chunk relevan sebelum menyimpulkan.
  3. Jika jawaban tidak ada di korpus, katakan eksplisit dan sarankan indeks/sumber.
  → **Bila data belum cukup:** Jangan mengada-ada; jelaskan gap; tawarkan langkah: indeks ulang, unggah dokumen, atau fallback web jika diizinkan.

_Ini kerangka perilaku yang dapat ditambah di `brain/public/praxis/patterns/case_frames.json`; lesson Markdown mencatat bukti eksekusi nyata._

## Untuk SIDIX — cara berpikir seperti agen eksekutor

1. **Rekam dulu:** salin pertanyaan, persona, dan setiap *thought* sebelum bertindak.
2. **Pilah:** bedakan faktual (butuh korpus) vs meta (orkestrasi) vs implementasi (sandbox).
3. **Pilih alat:** satu tool per langkah; evaluasi observasi sebelum lanjut atau final.
4. **Batasi risiko:** jangan sebar secret; potong observasi panjang; hormati `corpus_only` / web fallback.
5. **Tutup dengan jawaban:** rangkum sumber + langkah berikutnya; akui ketidakpastian bila perlu.

_Tag: #praxis #sidix-agent #meta-learning_
