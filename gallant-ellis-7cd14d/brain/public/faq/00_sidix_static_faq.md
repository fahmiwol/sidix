# FAQ statis — SIDIX & brain_qa (RAG)

Dokumen ini **statis** (bukan jawaban dinamis) dan diindeks bersama korpus `brain/public/`. Gunakan sebagai referensi cepat; jawaban runtime tetap harus disitasi dari kutipan RAG.

## Apa itu SIDIX di stack ini?

SIDIX adalah mesin inferensi lokal: ReAct + pencarian korpus (BM25) + alat terbatas (kalkulator, daftar sumber, Wikipedia API terkontrol bila diizinkan).

## Apa bedanya “korpus saja” dan “fallback web”?

- **Korpus saja**: hanya dokumen yang terindeks di workspace Anda.
- **Fallback web**: jika korpus tipis, agen boleh mengambil ringkasan dari Wikipedia (host diizinkan di backend).

## Bagaimana cara menambah pengetahuan?

Letakkan berkas `.md` di bawah `brain/public/` (lihat `brain/manifest.json`), lalu jalankan indeks ulang melalui endpoint reindex atau alur proyek Anda.

## Apa itu “keyakinan agregat”?

Label teks ringkas (bukan skor ML) yang menjelaskan seberapa kuat bukti kutipan; selalu verifikasi mandiri untuk keputusan penting.

## Privasi & export

Export sesi melalui API server meredaksi email/nomor telepon sederhana; jangan menempelkan rahasia API ke chat.
