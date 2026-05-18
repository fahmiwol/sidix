# Projek Badar — penyelarasan tujuan (Cursor + Claude)

Dokumen ini menjawab: **bagaimana batch A (50), B (54), dan C (10) bersama-sama mencapai goal produk**, bukan sekadar menyelesaikan baris checklist.

## Tujuan utara (sumber kebenaran)

1. **Tabel G1–G5** — `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` bagian *Tujuan akhir (setelah 114 modul selesai)*: setiap modul checklist harus menghasilkan kemajuan terukur menuju salah satu goal tersebut.
2. **Etos Al-Amin** — output jujur, sumber terkutip, batas kemampuan diakui (sama dokumen, baris pembuka).
3. **Own-stack & narasi** — `AGENTS.md`: inference inti Mighan/SIDIX = stack sendiri; API vendor hanya POC bila diperintahkan eksplisit. Ke publik: terminologi ilmiah / metafora sistem (`docs/PROJEK_BADAR_INTERNAL_BACKBONE.md`).

## Peta goal → artefak yang dibuktikan

| Goal | Arti produk (ringkas) | Bukti “sudah berkontribusi” (contoh) |
|------|------------------------|-------------------------------------|
| **G1** | Q&A + RAG + web terkontrol + simpulan berlabel | Endpoint/alur teruji; sanad/kutipan di UI atau API; mode korpus vs web. |
| **G5** | LLM operasional: eval, antrian, biaya, kualitas | Golden set, regresi prompt, `/health` + versi model, observabilitas. |
| **G4** | Kualitas rekayasa: skrip, CI, mini-app aman | Pre-commit, stub CI, template satu perintah, dokumentasi ADR. |
| **G2** | Text → image | Pipeline internal, preset, filter policy, antrian/thumbnail. |
| **G3** | Memahami gambar | Upload → caption/OCR, normalisasi input, routing jenis gambar. |

Satu **baris checklist** boleh kecil, asal **terhubung** ke salah satu sel di atas (bukan pekerjaan mengambang).

## Peran batch (bukan duplikasi sembarangan)

| Batch | File | Fokus penyelarasan |
|-------|------|-------------------|
| **A — Cursor** | `PROJEK_BADAR_BATCH_CURSOR_50.md` | Menuntaskan **fondasi G1 + G5 + sebagian G4** (urut dependensi): percakapan, RAG, evaluasi, keamanan dasar, dokumentasi operasional — supaya batch B punya tanah yang kokoh. |
| **B — Claude** | `PROJEK_BADAR_BATCH_CLAUDE_54.md` | Melanjutkan **G4 + G2 + G3** (setelah G1/G5 banyak di A): tooling dev, pipeline gambar, vision, integrasi yang mengandalkan API/korpus yang sudah jelas. |
| **C — sisa** | `PROJEK_BADAR_BATCH_SISA_10.md` | Menutup **celah akhir** lintas goal sampai 114 modul ter-cover tanpa mengorbankan etos Al-Amin. |

Jika sebuah tugas di batch B ternyata **blokir** karena fondasi G1 belum ada, **tandai blocker** di `docs/LIVING_LOG.md` dan kerjakan item yang setara di batch A (atau minta pemilik repo memprioritaskan), jangan mengubah struktur folder.

## Definisi selesai per tugas (wajib dipenuhi kedua agen)

Sebelum menandai satu baris checklist selesai:

1. **Goal**: sebutkan **G1|G2|G3|G4|G5** yang dilayani (dari kolom batch).
2. **Artefak**: kode, tes, skrip, atau dokumen operasional yang bisa diaudit.
3. **Bukti**: perintah uji atau tautan ke entri `LIVING_LOG` / commit.
4. **Own-stack**: tanpa menggantikan default inference dengan API vendor kecuali sesuai `AGENTS.md`.

## Koordinasi Cursor ↔ Claude

- **Sumber kebenaran urutan kerja:** file batch (bukan nomor surah acak).
- **Konflik scope:** yang sama-sama menyentuh satu endpoint — menang **satu PR** beruntun; catat `DECISION:` di `LIVING_LOG`.
- **114 selesai** = semua baris di `PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` punya bukti di repo atau penjelasan eksplisit *won’t / deferred* dengan tanggal review.
