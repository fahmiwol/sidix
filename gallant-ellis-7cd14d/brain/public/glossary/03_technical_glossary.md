# Glossary Teknis — Mighan-brain-1

> Istilah teknis yang sering dipakai di proyek ini. Untuk istilah umum & template, lihat `01_glossary_template.md`.

## Brain Pack

- **Arti**: Kumpulan dokumen, prinsip, riset, portofolio, dan dataset yang jadi landasan konteks AI.
- **Contoh**: "Mighan-brain-1 adalah brain pack pertama."

## Memory Cards

- **Arti**: Kartu ringkas (JSONL) berisi prinsip, preferensi, definisi, atau catatan proyek. Dipakai AI untuk menjaga konsistensi jawaban.
- **File**: `brain/datasets/memory_cards.jsonl`

## QA Pairs

- **Arti**: Pasangan pertanyaan-jawaban ideal yang dipakai untuk mengevaluasi apakah jawaban AI "sejalan" dengan cara berpikir pemilik brain pack.
- **File**: `brain/datasets/qa_pairs.jsonl`

## Embedding

- **Arti**: Representasi numerik (vektor) dari teks. Dipakai untuk mencari potongan dokumen yang paling relevan dengan query pengguna.
- **Catatan**: Model embedding dipilih berdasarkan trade-off kualitas vs biaya (lihat `research_notes/04_embeddings_tradeoffs.md`).

## Chunking

- **Arti**: Proses memotong dokumen menjadi potongan-potongan kecil agar bisa di-index dan di-retrieve. Bisa berbasis paragraf, heading, atau sliding window.
- **Catatan**: Lihat `research_notes/03_rag_chunking_markdown_aware.md`.

## Vector Store

- **Arti**: Database khusus untuk menyimpan dan mencari vektor embedding. Contoh: Qdrant, ChromaDB, atau embedded local.
- **Rencana proyek**: Mulai dari embedded local, lalu opsional Qdrant di VPS.

## Agent Runner

- **Arti**: Komponen yang menjalankan agent (AI yang bisa pakai tools). Menggunakan pola ReAct (Reasoning + Acting).
- **Catatan**: Tools selalu off by default, butuh izin eksplisit per-run.

## Tool Gating / Permission Gate

- **Arti**: Mekanisme keamanan di mana setiap tool (file, terminal, browser) harus diizinkan secara eksplisit sebelum agent bisa memakainya.

## Sanad

- **Arti**: Rantai periwayatan/referensi. Di konteks proyek ini: prinsip bahwa setiap klaim harus punya jalur sumber yang bisa ditelusuri.
- **Asal konsep**: Tradisi ilmu hadis Islam, diadaptasi untuk validasi informasi modern.

## Tabayyun

- **Arti**: Verifikasi informasi sebelum diterima. Anti-hoax. Di konteks AI: jangan langsung percaya output tanpa cek sumber.
- **Sumber**: QS Al-Hujurat [49]:6

## SIDIX Inference Engine (`brain_qa`)

- **Arti**: Layanan FastAPI lokal (port default **8765**) yang menjalankan loop **ReAct** + pencarian **BM25** pada korpus `brain/public/`, plus alat terbatas (kalkulator, daftar sumber, Wikipedia API bila diizinkan).
- **Endpoint contoh**: `GET /health`, `POST /agent/chat`, `POST /ask`, `POST /ask/stream` (SSE), `GET /agent/session/{id}/summary`, `DELETE /agent/session/{id}`.
- **Keyakinan agregat**: label teks ringkas pada jawaban (bukan skor ML); selalu verifikasi mandiri untuk keputusan penting.

## Korpus-only vs fallback web

- **Korpus-only**: parameter `corpus_only: true` — tidak memanggil alat web.
- **Fallback web**: bila korpus lemah dan `allow_web_fallback: true`, planner boleh memakai kutipan Wikipedia terkontrol.
