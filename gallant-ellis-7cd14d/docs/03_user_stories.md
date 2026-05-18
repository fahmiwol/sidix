# User Stories

## Epic A — Chat (Text)
- **A1 (P0)**: Sebagai pengguna, saya bisa memilih model (API atau lokal) lalu chat dengan streaming agar terasa cepat.
- **A2 (P0)**: Sebagai pengguna, saya bisa melihat history percakapan dan mencari chat lama.
- **A3 (P1)**: Sebagai admin, saya bisa membatasi token per chat agar biaya terkendali.

## Epic B — Image Generation
- **B1 (P0)**: Sebagai pengguna, saya bisa generate gambar dari prompt dengan opsi aspect ratio dan seed.
- **B2 (P0)**: Sebagai pengguna, saya bisa menyimpan dan melihat ulang prompt yang menghasilkan gambar.
- **B3 (P1)**: Sebagai pengguna, saya bisa membuat preset style (mis. “cinematic”, “product photo”) agar konsisten.

## Epic C — Voice (STT/TTS)
- **C1 (P0)**: Sebagai pengguna, saya bisa merekam/unggah audio untuk diubah ke teks (STT).
- **C2 (P0)**: Sebagai pengguna, saya bisa mendengar jawaban AI dalam bentuk suara (TTS).
- **C3 (P2)**: Sebagai pengguna, saya bisa memilih voice profile (cepat/lambat, style) bila provider mendukung.

## Epic D — Knowledge Base (RAG)
- **D1 (P0)**: Sebagai pengguna, saya bisa upload dokumen lalu bertanya dan mendapat jawaban yang menyertakan kutipan sumber.
- **D2 (P1)**: Sebagai pengguna, saya bisa mengelola koleksi dokumen (hapus, re-index).
- **D3 (P2)**: Sebagai admin, saya bisa mengatur embedding model dan chunking strategy.

## Epic E — Agent Runner
- **E1 (P0)**: Sebagai pengguna, saya bisa menjalankan agent yang memakai tools (file/browser/terminal) dengan izin eksplisit.
- **E2 (P0)**: Sebagai pengguna, saya bisa melihat run log langkah demi langkah.
- **E3 (P1)**: Sebagai admin, saya bisa melihat audit log siapa melakukan apa (tool calls).
- **E4 (P2)**: Sebagai developer, saya bisa membuat “agent template” yang bisa dipakai ulang komunitas.

## Epic F — Coding Agent (opsional fase lanjut)
- **F1 (P2)**: Sebagai developer, saya bisa meminta agent membuat perubahan kode sebagai patch, bukan edit sembarangan.
- **F2 (P2)**: Sebagai developer, saya bisa menjalankan test command yang direkomendasikan agent sebelum merge.

