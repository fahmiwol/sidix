# docs/adr — Architecture Decision Records (ADR)

ADR adalah dokumen singkat yang mencatat keputusan arsitektur penting,
beserta konteks dan konsekuensinya. Tujuannya agar keputusan dapat
diaudit dan dipahami di masa depan tanpa harus "menebak" alasannya.

Referensi: [Michael Nygard — Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

## Apa itu ADR?

- **Bukan** dokumentasi teknis lengkap
- **Ya**: catatan *kenapa* keputusan diambil, bukan hanya *apa*-nya
- Setiap ADR adalah dokumen yang tidak berubah setelah diterima
  (Accepted). Jika keputusan berubah, buat ADR baru yang supersedes ADR lama.

## Status yang Valid

| Status | Arti |
|--------|------|
| `Proposed` | Sedang didiskusikan |
| `Accepted` | Keputusan final dan berlaku |
| `Deprecated` | Masih berlaku tapi tidak direkomendasikan |
| `Superseded by ADR-XXX` | Diganti oleh ADR lain |

## Cara Membuat ADR Baru

1. Salin `ADR-template.md` ke `ADR-NNN-judul-singkat.md`
2. Isi semua bagian template
3. Tambahkan ke indeks di bawah ini
4. Submit ke review melalui PR

```bash
cp docs/adr/ADR-template.md docs/adr/ADR-004-nama-keputusan.md
```

## Indeks Keputusan

| Nomor | Judul | Status | Tanggal |
|-------|-------|--------|---------|
| [ADR-001](ADR-001-own-stack-inference.md) | Own-Stack Inference (Qwen2.5 + QLoRA) | Accepted | 2026-04-16 |
| [ADR-002](ADR-002-bm25-rag.md) | BM25 sebagai Retrieval Primer | Accepted | 2026-04-16 |
| [ADR-003](ADR-003-reed-solomon-storage.md) | Reed-Solomon 4+2 untuk Penyimpanan Corpus | Accepted | 2026-04-16 |
