# Spesifikasi — `Mighan-brain-1` (Brain Pack)

## Tujuan
`Mighan-brain-1` berisi data yang merepresentasikan:
- cara berpikir & preferensi (nilai, prinsip, gaya komunikasi),
- riset dasar & catatan,
- portofolio & karya,
- knowledge pribadi (glossary, proyek, orang, timeline).

Targetnya bukan “melatih LLM dari nol”, tapi membuat AI:
- **kontekstual** (paham kamu),
- **konsisten**,
- **bisa ngutip sumber** dari data kamu,
melalui **RAG + memory + evaluasi**.

## Prinsip data
- **Sumber jelas**: tiap item punya `source` (asal dokumen/link) dan `created_at`.
- **Bisa dikutip**: isi dokumen disimpan sebagai teks yang bisa di-retrieve dan disitasi.
- **Versi & review**: perubahan besar pada brain pack sebaiknya lewat PR.
- **Privasi**: defaultnya anggap data sensitif; pisahkan publik vs privat.

## Struktur folder yang disarankan
*(akan dibuat di repo saat implementasi ingest dimulai)*

- `brain/`
  - `public/` — aman untuk open-source
    - `principles/`
    - `portfolio/`
    - `research_notes/`
    - `glossary/`
  - `private/` — JANGAN di-commit (masuk `.gitignore`)
    - `identity/`
    - `finance/`
    - `personal/`
    - `raw_exports/`
  - `datasets/`
    - `memory_cards.jsonl`
    - `qa_pairs.jsonl`
    - `reading_list.jsonl`
  - `manifest.json`

## Format data inti

### 1) Memory cards (`brain/datasets/memory_cards.jsonl`)
Satu baris = satu JSON.

Fields minimum:
- `id`: string unik
- `type`: `principle | preference | biography | project | glossary | note`
- `title`: ringkas
- `content`: teks utama (markdown ok)
- `tags`: string[]
- `source`: `{ kind: "doc"|"link"|"chat"|"manual", ref: string }`
- `created_at`: ISO string

### 2) QA pairs (`brain/datasets/qa_pairs.jsonl`)
Untuk evaluasi “apakah jawabannya sesuai kamu”.
- `id`
- `question`
- `ideal_answer` (jawaban contoh versi kamu)
- `rubric` (kriteria penilaian singkat)
- `tags`

### 3) Manifest (`brain/manifest.json`)
Menjelaskan isi brain pack:
- nama, deskripsi
- daftar dataset
- aturan lisensi untuk masing-masing folder (public/private)
- redaction rules (contoh pola yang harus dihapus)

## Pipeline awal (MVP)
- Import dokumen → ekstrak teks → chunking → embedding → simpan ke vector store
- Query → retrieve top-k chunks → generate jawaban + **citations**
- Optional: “memory injection” dari memory cards relevan

## Safety & Open-source
- `brain/private/` wajib di-ignore.
- Semua data publik harus:
  - punya hak distribusi (karya sendiri / izin),
  - tidak berisi data pribadi orang lain tanpa consent.

