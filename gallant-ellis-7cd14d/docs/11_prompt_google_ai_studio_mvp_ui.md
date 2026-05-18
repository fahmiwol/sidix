# Prompt — Google AI Studio (desain UI MVP **Mighan-brain-1**)

Salin blok **ANTARA** tanda `<<<` di bawah ini ke Google AI Studio (atau Gemini). Sesuaikan bagian `[ISI MANUAL]` kalau sudah kamu putuskan.

---

<<< PROMPT MULAI

Anda adalah **UX + product designer** untuk aplikasi open-source **Mighan-brain-1**: *brain pack* (korpus Markdown + RAG + sitasi) + **AI workspace** bertahap (chat → multimodal → agent), MIT license, orientasi **self-host / lokal**.

## Konteks keputusan produk (wajib dipatuhi)

1. **UI dulu** — MVP fokus **permukaan pengguna**; backend awal boleh tipis (boleh anggap ada API lokal atau wrapper ke CLI `brain_qa`).
2. **Single-user / tanpa login** untuk MVP pertama (setuju pemilik repo): tidak perlu flow signup; cukup **mode lokal** + penyimpanan rahasia di perangkat (peringatan jangan sync sembarangan).
3. **Admin tidak wajib site terpisah**: **satu aplikasi**, area **Pengaturan** untuk hal “operator ringan”; nanti multi-user/RBAC mengikuti PRD fase lanjut.
4. **Security-by-default**: agent/tools **default OFF**; kalau ada menu Agent, tampilkan sebagai *Coming soon* atau disabled dengan penjelasan singkat.
5. **Source-based / RAG**: jawaban harus bisa menampilkan **kutipan sumber** (snippet + judul file); hindari UI yang “menyembunyikan” asal informasi.

## Referensi dokumen repo (ringkas — jangan mengada-ngada entitas di luar ini)

**ERD konseptual** (entitas inti; relasi workspace-centric): `users`, `workspaces`, `workspace_members`, `conversations`, `messages`, `assets`, `knowledge_bases`, `knowledge_documents` (+ opsional `knowledge_document_versions`), `agent_runs`, `tool_calls`.  
Untuk MVP **single-user**, boleh **semunyikan** `workspace_members` dari UI dan anggap satu `workspace` default.

**PRD MVP (P0)** mencakup: chat (streaming), history, model selection; knowledge upload + cite; image/voice/agent ada di PRD — untuk **desain navigasi MVP**, utamakan **Chat + Korpus**; Image/Voice/Agent boleh **tab sekunder** atau *Phase 1.1* dengan label belum aktif.

## Tugas Anda

Hasilkan **paket desain** berikut (bahasa Indonesia, istilah UI boleh Inggris di label tombol jika umum):

### A) Information architecture

- Pohon **menu / route** (maks. 8 item top-level; gabung yang mirip).
- Penjelasan 1 kalimat per menu: user story singkat.

### B) Wireframe-level screen list

Untuk setiap layar utama, berikan:

- Nama layar + route
- Komponen utama (layout, sidebar, header)
- **Empty state**, **loading**, **error** (1 bullet each per layar penting)
- **States** khusus: indexing dokumen (queued/indexing/ready/failed) mapping ke `knowledge_documents.status`

### C) Navigasi: User vs “Admin ringan”

- **User**: Chat, Korpus, (opsional) Riwayat global.
- **Admin ringan** (bukan produk terpisah): di dalam **Pengaturan** — sub-menu: Model & provider, Path korpus/index (read-only teks + tombol “buka folder” hanya copy path), Privasi & data lokal, Tentang / lisensi.

### D) Komponen desain sistem (minimal)

- Tipografi skala (h1–body), spacing 4/8 grid, warna **light + dark** (token nama: `--bg`, `--fg`, `--muted`, `--accent`, `--danger`).
- Aksesibilitas: kontras AA, focus ring, ukuran tap target.

### E) Mapping ERD → layar (tabel)

Kolom: `Entitas` | `Layar yang menyentuh` | `Aksi user`.

### F) Prompt engineering untuk tim dev (bonus)

- 5 **acceptance criteria** testable untuk MVP Chat + Korpus.

## Batasan (jangan lakukan)

- Jangan mendesain **blockchain**, **token ekonomi**, atau **marketplace plugin** penuh.
- Jangan mensyaratkan fitur multi-tenant kompleks di MVP ini.
- Jangan menyarankan menyimpan API key di plaintext tanpa peringatan; sebutkan **local vault** / env / OS keychain sebagai opsi.

## Format output

1. Markdown terstruktur dengan heading `##`/`###`.
2. Di akhir, **JSON satu objek** berisi: `{ "routes": [...], "components": [...], "theme_tokens": {...} }` agar bisa diparse ulang.

[PILIHAN MANUAL — isi oleh pemilik repo]

- Nama aplikasi di UI: [ISI MANUAL]
- Bahasa UI utama: Indonesia / dwibahasa [ISI MANUAL]
- Prioritas jika waktu terbatas: (1) Chat dulu atau (2) Korpus dulu [ISI MANUAL]

PROMPT SELESAI >>>

---

## Catatan pemakaian

- Lampirkan file `docs/04_erd.md` dan `docs/02_prd.md` ke AI Studio sebagai **context** jika tool mendukung upload; kalau tidak, potongan ERD di atas sudah cukup untuk MVP.
- Hasil desain bisa kamu arsipkan di `brain/public/projects/` atau `docs/` sebagai export (sesuai kebiasaan repo).

