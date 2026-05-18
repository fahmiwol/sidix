# docs/snippets — Indeks Code Snippets SIDIX

Koleksi contoh kode siap pakai untuk mengintegrasikan dengan komponen SIDIX/Mighan.
Semua snippet bersifat **illustrative** — bukan production code langsung, perlu
disesuaikan dengan path dan konfigurasi deployment masing-masing.

## Daftar Snippet

| File | Bahasa | Deskripsi |
|------|--------|-----------|
| `python_rag_query.py` | Python | Query RAG brain_qa dengan persona via `httpx` |
| `python_sanad_cite.py` | Python | Tambah metadata sanad/sitasi ke knowledge claim |
| `python_ledger_verify.py` | Python | Verifikasi integritas ledger secara programatik |
| `python_react_agent.py` | Python | Panggil ReAct agent endpoint `POST /agent/chat` |
| `ts_brain_qa_client.ts` | TypeScript | Typed `BrainQAClient` dengan `ask()`, `health()`, `listCorpus()` |
| `webhook_outgoing.py` | Python | Webhook outgoing dengan HMAC-SHA256 + retry (OPSIONAL) |

## Cara Menggunakan

1. Salin snippet yang dibutuhkan ke proyek Anda
2. Sesuaikan `BASE_URL`, `PERSONA`, dan path sesuai environment
3. Install dependensi yang disebutkan di header masing-masing file

## Konvensi

- Semua Python snippet menggunakan header `# -*- coding: utf-8 -*-`
- `BASE_URL` selalu menunjuk ke `localhost` (own-stack, bukan vendor API)
- Komentar dalam Bahasa Indonesia kecuali nama variabel/fungsi
