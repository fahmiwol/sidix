# Next steps (lokal) — mulai dari Markdown di `<WORKSPACE_ROOT>`

## 1) Masukkan data Markdown kamu
Taruh dokumen Markdown yang aman untuk publik ke:
- `brain/public/`

Kalau ada yang sensitif, buat folder:
- `brain/private/` (folder ini sudah di-ignore oleh git)

## 2) Lengkapi memory cards
Edit:
- `brain/datasets/memory_cards.jsonl`

Tambahkan 10–50 kartu pertama: prinsip, preferensi, proyek, glossary.

## 3) Buat QA pairs untuk evaluasi konsistensi
Edit:
- `brain/datasets/qa_pairs.jsonl`

Mulai dari 20 pertanyaan yang sering kamu tanya ke AI + jawaban ideal versi kamu.

## 4) MVP yang akan kita bangun berikutnya
1) Index Markdown → simpan chunks + metadata
2) Query → retrieve top-k → generate jawaban + sitasi sumber

