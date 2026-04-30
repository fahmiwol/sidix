# Catatan riset: Kemampuan AI Generatif dan LLM (PDF)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sumber lokal:** `c:\Users\ASUS\Downloads\Kemampuan AI Generatif dan LLM.pdf`  
**Format:** laporan teknis berbahasa Indonesia, **19 halaman**, banyak kutipan web (akses dicatat April 2026).  
**Judul tematik di isi:** arsitektur kognitif-generatif terpadu — sintesis visual, ketahanan linguistik, pengambilan keputusan otonom.

## Ringkasan isi (peta bab)

1. **Pengantar** — evolusi Generative AI & LLM ke sistem multimodal probabilistik; sintesis gambar, ketahanan terhadap typo/slang, ringkasan dokumen panjang, keputusan otonom + alat eksternal, dokumentasi dengan sitasi.
2. **Sintesis visi** — model difusi (termasuk *latent diffusion* / Stable Diffusion), proses difusi maju, jadwal varians; teknik kontrol (LoRA, DreamBooth, Hypernetworks, Textual Inversion, dll. — tabel ringkas di dokumen).
3. **Ketahanan linguistik** — tokenisasi subkata (BPE, WordPiece), mekanisme atensi (Q/K/V), batas ketahanan di bawah derau sintetis tinggi pada penalaran kompleks.
4. **Bahasa Indonesia** — morfologi aglutinatif; BPE pada korpus besar; opsi tokenisasi suku kata untuk bahasa Austronesia; slang / “Alay”; korpus lokal (IndoSafety, Cendol, Komodo, dll.).
5. **Konteks panjang & ringkasan** — batas jendela konteks; SWA, LongRoPE, Ring Attention; *lost-in-the-middle*; ringkasan rekursif / hierarkis (divide-and-conquer, HTSIR/HERCULES).
6. **Kognisi & agen** — CoT → ToT / GoT; **ReAct**; tool / function calling; definisi agen (IBM, Google Cloud, dll.).
7. **Penyelarasan & keamanan** — RLHF; batas sosiotechnical alignment; fine-tuning reasoning.
8. **RAG & keluaran terstruktur** — definisi RAG, mitigasi error; structured generation / JSON-mode style (Dataiku, Medium, dll.).
9. **Daftar pustaka** — puluhan URL (arXiv, AWS, IBM, Wikipedia, blog, dll.).

## Relevansi ke SIDIX / MIGHAN (praktis)

| Topik PDF | Taut ke komponen proyek |
|-----------|------------------------|
| RAG, sitasi, mitigasi halusinasi | `brain_qa` retrieval, chunking, QA golden |
| ReAct + tool calling | `agent_serve`, orkestrasi alat |
| Ringkasan rekursif / chunk panjang | kebijakan chunk + batas konteks di pipeline |
| Bahasa Indonesia + korpus lokal | kurasi dataset SFT / eval bias Nusantara |
| Structured output | kontrak API / schema respons agen |
| LoRA (bagian kontrol difusi; analog dengan adapter) | LoRA SIDIX di `models/sidix-lora-adapter` |

## Catatan metode

- Dokumen ini **bukan** sumber primer hukum/ushul; gunakan sebagai **survey teknik** generatif + LLM.
- Untuk RAG ke korpus proyek, salin PDF ke folder yang diindeks (atau ekstrak teks) bila ingin ditanyakan lewat retrieval — path Downloads default **tidak** ada di repo.

## Status

- **Dicerna:** ringkasan struktural + indeks (sesi kurasi repo).  
- **Tindakan opsional:** salin PDF ke `brain/public/corpus/` atau sejenisnya + jalankan ingest sesuai pipeline Anda.
