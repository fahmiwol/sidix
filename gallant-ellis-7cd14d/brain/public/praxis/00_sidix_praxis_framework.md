# Kerangka Praxis — SIDIX belajar dari jejak eksekusi agen

## Tiga lapisan (supaya bukan “cuma baca folder”)

| Lapisan | Isi | Fungsi |
|--------|-----|--------|
| **L0 — Kerangka kasus** | `brain/public/praxis/patterns/case_frames.json` | **Konsep + niat + inisiasi + cabang** “bila ada data / bila belum” — dipilih **runtime** dari teks pertanyaan, disuntikkan ke jawaban & lesson. Dapat **diedit manusia** untuk menambah pola baru tanpa fine-tune. |
| **L1 — Bukti eksekusi** | `brain/public/praxis/lessons/*.md` + JSONL `.data/praxis/sessions/` | **Jejak nyata** Thought→Action→Observation; setelah indeks → **RAG** (BM25) menemukan “dulu begini”. |
| **L2 — Distilasi / model** *(opsional ke depan)* | Skrip merge, LoRA, atau planner LLM | Merangkum L1→aturan padat atau bobot model — **belum wajib**; L0+L1 sudah memberi perilaku “tumbuh” terkontrol. |

## Apa itu Praxis?

**Praxis** = pengetahuan prosedural yang tumbuh dari **tindakan nyata**: membaca repo, memutuskan langkah, menjalankan tool, mengecek hasil, menulis ulang korpus. Bukan teori kosong; setiap sesi agen ReAct menghasilkan:

1. **JSONL sesi** di `apps/brain_qa/.data/praxis/sessions/{session_id}.jsonl` — event: `session_start`, `react_step`, `blocked`, `cache_hit`, `session_end`.
2. **Lesson Markdown** di `brain/public/praxis/lessons/` — ringkasan manusia-membaca + cuplikan langkah; setelah `python -m brain_qa index`, isi folder ini **masuk BM25** sehingga SIDIX bisa menemukan pola “cara dulu menyelesaikan X”.

## Alur untuk SIDIX (inferensi)

- Saat menjawab pertanyaan baru, **utamakan korpus**; jika `search_corpus` mengembalikan cuplikan dari `praxis/lessons`, perlakukan sebagai **contoh prosedur**, bukan otoritas fatwa atau secret.
- **Bedakan** fakta domain vs meta-proses: tag `#praxis` menandakan meta-pembelajaran.

## Alur untuk agen luar (Cursor, CLI manusia)

- Setelah melakukan pekerjaan berarti, rekam ringkas:

```bash
cd apps/brain_qa
python -m brain_qa praxis note "Judul tugas" --summary "Apa yang diubah dan mengapa" --step "Langkah 1" --step "Langkah 2"
```

- Lalu **indeks ulang** agar SIDIX melihat pelajaran baru: `python -m brain_qa index`.

## API

- `GET /agent/praxis/lessons?limit=30` — daftar file lesson terbaru (path relatif repo).

## Batasan & keamanan

- Observasi tool dan teks dipotong; pola `api_key=` redacted.
- Tidak menggantikan ledger Hafidz untuk integritas korpus — **melengkapi** dengan pola kerja agen.
