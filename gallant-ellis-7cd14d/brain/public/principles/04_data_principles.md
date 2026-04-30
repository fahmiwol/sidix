# Prinsip Data — Mighan-brain-1

> Bagaimana data diperlakukan di proyek ini: dari pengumpulan sampai penyajian.

## 1 — Sumber harus jelas

- Setiap item data (memory card, dokumen, catatan) wajib punya field `source`.
- Kalau sumber belum diketahui: tandai `source.kind: "unverified"` dan isi `ref` dengan catatan asal.
- Jangan pernah "ngarang" sumber.

## 2 — Bisa dikutip (citable)

- Semua teks di brain pack disimpan dalam format yang bisa di-retrieve dan disitasi.
- Jawaban AI dari brain pack wajib menyertakan `doc_path` dan/atau `section_path`.

## 3 — Versioning & review

- Perubahan besar pada brain pack (misalnya revisi prinsip, hapus dokumen) sebaiknya lewat PR atau catatan changelog.
- Dokumen lama tidak dihapus sembarangan; bisa dipindah ke `archive/` dengan catatan alasan.

## 4 — Privasi by default

- Defaultnya anggap data **sensitif** sampai terbukti aman untuk publik.
- Data pribadi, keuangan, identitas → `brain/private/` (di-gitignore).
- Data publik → `brain/public/` (aman untuk open-source).

## 5 — Format konsisten

- File Markdown: heading jelas (`#`, `##`), bullet rapi, 1 file = 1 topik.
- JSONL: satu baris = satu objek JSON, sesuai schema di `08_mighan_brain_1_spec.md`.
- Nama file: lowercase, underscore, prefix nomor urut.

## 6 — Tidak ada data orang lain tanpa consent

- Dokumen publik tidak boleh berisi PII orang lain.
- Kalau memuat referensi karya orang lain: gunakan format sitasi, bukan copy-paste konten.
