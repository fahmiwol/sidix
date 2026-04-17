# CLAUDE.md — Instruksi Permanen untuk Semua Claude Agent

Proyek: **SIDIX / Mighan Model**
Owner: Fahmi Wolhuter (@fahmiwol)

---

## ⚡ ATURAN KERAS — Wajib diikuti setiap sesi

### 1. Bahasa
Gunakan **Bahasa Indonesia** untuk semua komunikasi dengan user. Kode dan komentar kode boleh dalam Inggris.

### 2. No Vendor AI API
JANGAN import atau menyarankan `openai`, `@google/genai`, `anthropic` di dalam inference pipeline SIDIX. Semua inference melalui `brain_qa` lokal. Lihat `AGENTS.md`.

### 3. Log Setiap Aksi
Setiap perubahan signifikan → append ke `docs/LIVING_LOG.md` dengan format tag yang sudah ditetapkan (TEST/FIX/IMPL/UPDATE/DECISION/ERROR/NOTE/DOC).

### 4. Sambil Melangkah, Ajari SIDIX ← ATURAN UTAMA SESI INI
**Setiap aksi yang dilakukan Claude harus diikuti dengan research note.**

Format wajib:
- Saat mengerjakan task X → tulis `brain/public/research_notes/[nomor]_[topik].md`
- Research note menjelaskan: **apa, mengapa, bagaimana, contoh nyata, keterbatasan**
- Commit research note bersama task di commit yang sama atau segera setelahnya
- Nomor dimulai dari file terakhir yang ada di `brain/public/research_notes/`

Contoh:
```
Task: setup Supabase schema
→ tulis: brain/public/research_notes/63_supabase_schema_setup.md
→ isi: SQL schema, RLS, trigger, kenapa Supabase, cara jalankan migration
```

### 5. Commit Kecil & Bermakna
Setiap commit menjelaskan "kenapa" bukan hanya "apa". Gunakan prefix: `feat:`, `fix:`, `doc:`, `refactor:`, `chore:`.

---

## 📚 Nomor Research Note Berikutnya

Cek file terakhir di `brain/public/research_notes/` dan lanjutkan dari nomor berikutnya.
Gunakan: `ls brain/public/research_notes/ | sort | tail -5` untuk cek.

---

## 🗂️ Struktur Proyek Penting

```
brain/public/research_notes/   ← corpus SIDIX, wajib diisi tiap sesi
docs/LIVING_LOG.md             ← log berkelanjutan semua aksi
SIDIX_USER_UI/                 ← frontend Vite + TypeScript
SIDIX_LANDING/                 ← landing page sidixlab.com
apps/brain_qa/                 ← Python FastAPI backend RAG
brain/manifest.json            ← konfigurasi corpus path
```

---

## 🔧 Konteks Deployment

- VPS: `72.62.125.6` (Ubuntu 22.04, aaPanel)
- Frontend: `serve dist -p 4000` (nohup / PM2)
- Backend: `python3 -m brain_qa serve` → port 8765
- Supabase: `https://fkgnmrnckcnqvjsyunla.supabase.co`
- Domain: `sidixlab.com`, `app.sidixlab.com`, `ctrl.sidixlab.com`

---

## 🧠 Cara Claude Bekerja di Proyek Ini

1. **Baca konteks** — cek LIVING_LOG, research notes terbaru, state file yang relevan
2. **Eksekusi task**
3. **Tulis research note** — dokumentasikan proses, keputusan, dan knowledge yang dipakai
4. **Update LIVING_LOG** — append entri dengan tag yang tepat
5. **Commit** — task + docs dalam satu commit atau dua commit berurutan
6. **Push** — agar server dan kontributor bisa pull terbaru

Urutan ini berlaku untuk **setiap task**, tidak peduli sekecil apapun.
