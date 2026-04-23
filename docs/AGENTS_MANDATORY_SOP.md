# SIDIX — Agent Mandatory SOP & Guardrails (v0.8.0)

> **IMPORTANT**: Dokumen ini bersifat wajib bagi **setiap agen pengembang** yang bekerja di repositori SIDIX. Pelanggaran terhadap SOP ini dapat membahayakan keamanan data internal dan integritas branding proyek.

---

## 1. Kebijakan Privasi & Kebocoran Informasi
Dilarang keras mempublikasikan informasi internal ke area publik (Landing Page, README publik, CHANGELOG publik, atau Commit Message).

- **Internal Paths:** Jangan pernah menulis path lokal (misal: `D:\MIGHAN Model`, `C:\Users\...`) ke file HTML, CSS, atau JS yang bisa diakses publik.
- **Credentials:** Jangan melakukan commit pada file `.env` atau file yang berisi API Key, Password, atau SSH Credentials.
- **Redaksi:** Gunakan istilah netral seperti "local path", "environment optimization", atau "server-side configuration".

## 2. Terminologi Native SIDIX (Kanonis)
Gunakan istilah-istilah berikut untuk menjaga keaslian (authenticity) proyek:

| Istilah | Fungsi / Makna |
|---------|----------------|
| **Maqashid** | Mode tujuan / exit paths dalam ReAct loop |
| **Naskh** | Resolusi konflik pengetahuan (Sanad-based) |
| **Raudah** | Protokol orkestrasi agen paralel (DAG) |
| **Sanad** | Sumber kutipan / rantai integritas data |
| **Muhasabah** | Evaluasi diri / quality gate (CQF) |
| **Jariyah** | Continual learning / siklus belajar mandiri |
| **Tafsir** | Reasoning / penjelasan langkah demi langkah |

## 3. Set Persona Resmi (Pivot 2026)
Hanya gunakan 5 persona ini. Jangan gunakan nama lama (Mighan, Toard, dll.) di UI atau dokumentasi publik.

1.  **AYMAN** (Creative)
2.  **ABOO** (Planning)
3.  **OOMAR** (Academic)
4.  **ALEY** (Technical)
5.  **UTZ** (Simple)

## 4. Aturan Penulisan Konten
- **Penjelasan & Dokumentasi:** Gunakan **Bahasa Indonesia** (agar Founder dan Agen lokal mudah memahami konteks).
- **Kode Sumber (Code):** Gunakan **English** (standar teknis global).
- **Bilingual:** Update status di Git & Landing Page wajib bilingual (Inggris untuk publik, Indonesia untuk transparansi lokal).

## 5. Workflow Pasca-Task (Wajib)
Setiap selesai menyelesaikan Task atau Sprint, agen wajib melakukan:

### A. Internal Documentation
- **Living Log:** Tambahkan entri di `docs/LIVING_LOG.md` (append-only).
- **Handoff:** Update `docs/HANDOFF_*.md` untuk agen berikutnya.
- **PRD Sync:** Pastikan fitur yang dibuat sesuai dengan PRD asli.

### B. External Synchronization
- **Changelog:** Update `CHANGELOG.md` dengan narasi yang jujur.
- **Landing Page:** Update versi rilis dan fitur baru (cek kebocoran internal!).
- **Git Status:** Pastikan branch `main` sinkron dengan server produksi.

---
*Ditetapkan pada: 2026-04-23*
*Status: MANDATORY*
