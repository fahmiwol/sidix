# Sistem Knowledge Capture Otomatis — Sambil Melangkah, Ajari SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Konsep Utama

"Sambil menyelam minum air" — setiap pekerjaan yang dikerjakan developer/AI agent
**secara otomatis menghasilkan knowledge** yang masuk ke corpus SIDIX.

Tidak ada pekerjaan yang terbuang sia-sia. Setiap task = dua output:
1. **Artefak kerja** (kode, konfigurasi, deployment)
2. **Knowledge note** (dokumentasi proses, keputusan, pelajaran)

---

## Mengapa Ini Penting?

### Problem tanpa sistem ini:
- Knowledge ada di kepala developer, tidak tercatat
- SIDIX tidak tahu cara deploy, cara setup DB, cara debug
- Kontributor baru tidak punya panduan kontekstual
- Setiap sesi Claude harus "belajar dari nol" tentang proyek

### Dengan sistem ini:
- SIDIX makin pintar setiap kali developer bekerja
- Corpus tumbuh organik — tidak perlu waktu khusus untuk dokumentasi
- Knowledge tersimpan di git (versioned, searchable, permanent)
- AI agent berikutnya punya konteks penuh

---

## Komponen Sistem

### 1. CLAUDE.md — Instruksi Permanen
File di root project yang dibaca Claude Code setiap sesi baru.
Berisi aturan keras: "setiap task → tulis research note".

```
D:\MIGHAN Model\CLAUDE.md
```

Efeknya: Claude tidak bisa "lupa" untuk mendokumentasikan — sudah jadi instruksi sistem.

### 2. Research Notes di Corpus SIDIX
```
brain/public/research_notes/
  60_vps_deployment_sidix_aapanel.md
  61_supabase_database_backend.md
  62_api_keys_env_vars_security.md
  63_supabase_schema_setup.md
  64_vision_ai_membaca_gambar.md
  65_sistem_knowledge_capture_otomatis.md  ← file ini
  ...
```

Penomoran berurutan, slug deskriptif. Format: `[N]_[topik_slug].md`

### 3. Script `tools/sidix-learn.ps1`
Untuk capture knowledge cepat dari terminal tanpa membuka editor:

```powershell
# Buat template research note baru
.\tools\sidix-learn.ps1 "nginx ssl termination"

# Dengan isi awal
.\tools\sidix-learn.ps1 "postgresql rls" "Row Level Security adalah..."
```

### 4. LIVING_LOG.md — Log Berkelanjutan
Setiap aksi di-append dengan tag standar:
```
DOC: research note 65 — sistem knowledge capture otomatis
IMPL: CLAUDE.md + tools/sidix-learn.ps1
DECISION: wajibkan research note untuk setiap task, bukan opsional
```

---

## Alur Kerja (Workflow)

```
Developer/Claude mengerjakan task X
          │
          ▼
    Eksekusi task
    (kode, config, deploy, debug)
          │
          ├──────────────────────────────────┐
          ▼                                  ▼
  Artefak kerja                    Research Note
  (file diubah/dibuat)             brain/public/research_notes/N_X.md
          │                                  │
          └──────────────┬───────────────────┘
                         ▼
                   git commit + push
                         │
                         ▼
              Server pull → brain_qa index
                         │
                         ▼
              SIDIX bisa jawab pertanyaan tentang X
```

---

## Konvensi Penulisan Research Note

Setiap research note harus menjawab 5 pertanyaan:

| Pertanyaan | Section |
|---|---|
| Apa ini? | Definisi, konteks |
| Mengapa penting? | Masalah yang dipecahkan |
| Bagaimana caranya? | Langkah, cara kerja, kode |
| Contoh nyata? | Dari pengalaman proyek SIDIX |
| Batasannya apa? | Trade-off, kapan tidak digunakan |

---

## Integrasi dengan Tools Lain

### Cursor
Di `.cursorrules` atau system prompt Cursor, tambahkan:
```
Setiap kali kamu mengimplementasikan fitur atau fix bug, buat atau update
file di brain/public/research_notes/ yang menjelaskan konsep yang dipakai.
```

### Antigravity / Codex / AI Agent lain
Prinsip sama — setiap agent yang bekerja di repo ini membaca `CLAUDE.md`
dan mengikuti aturan "tulis research note" secara otomatis.

### GitHub Actions (roadmap)
```yaml
# Otomatis re-index SIDIX setelah push ke main
on:
  push:
    paths:
      - 'brain/public/**'
jobs:
  reindex:
    steps:
      - run: python3 -m brain_qa index
```

---

## Filosofi: Knowledge sebagai Produk Sampingan

Knowledge terbaik bukan yang ditulis untuk dokumentasi,
tapi yang lahir dari **pengalaman langsung mengerjakan**.

Ketika kita deploy ke VPS dan menemukan port conflict → research note tentang port management.
Ketika kita setup Supabase dan menghadapi RLS → research note tentang database security.
Ketika screenshot dikirim dan AI membacanya → research note tentang vision AI.

SIDIX belajar dari pengalaman nyata proyek, bukan dari teori generik.
Ini membuat pengetahuannya **kontekstual, relevan, dan dapat diverifikasi**.
