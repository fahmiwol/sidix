# Privacy (SIDIX)

Dokumen ini menjelaskan **kebijakan privasi** untuk artefak publik di repo SIDIX dan situs `sidixlab.com`.

## Prinsip

- **Self-hosted / own stack**: SIDIX dirancang agar bisa dijalankan secara lokal atau di server milik pengguna.
- **Minim data**: fitur publik tidak membutuhkan data pribadi untuk digunakan.
- **Transparansi**: perubahan signifikan dicatat di `CHANGELOG.md` dan `docs/LIVING_LOG.md`.

## Data yang mungkin tercatat

- **Log server** (jika Anda menjalankan SIDIX di server): alamat IP, user-agent, waktu akses, dan error standar web.
- **Input pengguna**: hanya jika Anda menyimpan/menyalakan logging aplikasi di server Anda sendiri.
- **Korpus**: berkas di `brain/public/` adalah publik; `brain/private/` **tidak** di-commit.

## Aturan kontribusi

- Jangan commit **secret** (API key, token, password) atau path lokal pengguna.
- Jika perlu contoh konfigurasi, gunakan placeholder seperti `<WORKSPACE_ROOT>` atau `<local_user_path>`.

## Kontak

- Email: `contact@sidixlab.com`

