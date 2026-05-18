# Self-Healing AI System — SIDIX yang Bisa Memperbaiki Dirinya Sendiri

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Konteks: Error yang Memunculkan Ide Ini

Saat user kirim feedback via tab Saran di `app.sidixlab.com`:
```
Gagal mengirim: new row violates row-level security policy for table "feedback"
```

Root cause: RLS policy INSERT di Supabase tidak menyertakan role `anon`
(user yang belum login diperlakukan sebagai `anon` oleh Supabase).

Fix manual:
```sql
CREATE POLICY "feedback_insert_public" ON feedback
  FOR INSERT TO anon, authenticated WITH CHECK (true);
```

**Pertanyaan yang lahir:** Bisakah SIDIX mendeteksi, mendiagnosis, dan memperbaiki error ini sendiri?

---

## Apa itu Self-Healing System?

Self-healing = kemampuan sistem untuk:
1. **Mendeteksi** bahwa ada yang salah (monitoring)
2. **Mendiagnosis** root cause (analisis)
3. **Mengeksekusi perbaikan** (aksi)
4. **Memverifikasi** perbaikan berhasil (validasi)
5. **Mendokumentasikan** apa yang terjadi (memory)

Tanpa manusia di tengah loop.

---

## Level Self-Healing (dari Mudah ke Susah)

### Level 1 — Restart otomatis (sudah bisa sekarang)
```
brain_qa mati → PM2 restart otomatis → SIDIX hidup lagi
```
Ini bukan "cerdas" — hanya process manager.

### Level 2 — Deteksi + Alert (butuh monitoring)
```
Health check gagal → kirim notif ke Telegram/email admin
→ Admin yang fix secara manual
```

### Level 3 — Deteksi + Diagnosis + Saran
```
Error masuk ke log → SIDIX analisis log → 
SIDIX jawab: "Kemungkinan root cause: X. Solusi: Y"
→ Admin eksekusi solusi
```

### Level 4 — Deteksi + Diagnosis + Eksekusi (semi-auto)
```
Error terdeteksi → SIDIX cocokkan dengan database error yang dikenal →
Generate fix → Admin review → Admin approve → Fix dieksekusi
```

### Level 5 — Fully Autonomous Self-Repair
```
Error terdeteksi → SIDIX analisis → SIDIX generate fix →
SIDIX test di sandbox → Jika aman: auto-apply → SIDIX dokumentasikan
```

Level 5 membutuhkan: sandboxed execution, rollback mechanism, confidence threshold.

---

## Untuk Error RLS Supabase Ini — Bagaimana SIDIX Bisa Menangani?

### Apa yang SIDIX perlu tahu:
1. Error message: "violates row-level security policy"
2. Tabel: "feedback"
3. Operasi: INSERT
4. Context: user anonim (tidak login)

### Apa yang SIDIX sudah punya (dalam corpus):
- `63_supabase_schema_setup.md` → tahu struktur tabel + RLS policy
- `62_api_keys_env_vars_security.md` → tahu konsep anon vs authenticated role

### Apa yang SIDIX harusnya bisa simpulkan:
```
Error: "violates row-level security policy" pada INSERT ke "feedback"
→ Policy INSERT tidak mengizinkan role ini
→ Cek: apakah policy FOR INSERT TO anon sudah ada?
→ Fix: tambah `TO anon, authenticated` pada policy
→ SQL: DROP POLICY ... CREATE POLICY ... TO anon, authenticated ...
```

### Apa yang dibutuhkan agar SIDIX bisa eksekusi fix-nya:
- Akses ke Supabase via service key (sudah ada di backend)
- Tool: `run_sql(query)` — eksekusi SQL ke Supabase
- Sandboxed validation: test setelah fix
- Approval gate: tanya admin sebelum eksekusi DDL (DROP/CREATE policy)

---

## Arsitektur Self-Healing untuk SIDIX

```
[Error Detector]
    │ (monitor logs, health check, user-reported errors)
    ▼
[Error Classifier]
    │ (cocokkan dengan known error patterns)
    ├── RLS violation → diagnose policy
    ├── Port conflict → diagnose process
    ├── Import error → diagnose dependencies
    └── Unknown → escalate ke admin
    ▼
[Fix Generator]
    │ (generate solusi berdasarkan diagnosis)
    ▼
[Confidence Scorer]
    │ >= 0.9 → auto-apply (jika izin granted)
    │ >= 0.7 → saran ke admin + 1-click apply
    │ < 0.7  → eskalasi ke admin + penjelasan
    ▼
[Fix Executor]
    │ (eksekusi di sandbox dulu, lalu production)
    ▼
[Validator]
    │ (verifikasi fix berhasil)
    ▼
[Documenter]
    (tulis ke LIVING_LOG + research note baru)
```

---

## Database Error Patterns (awal dari knowledge base self-healing)

| Error | Root Cause | Fix |
|---|---|---|
| `violates row-level security policy` | Policy tidak include role yang tepat | Tambah `TO anon, authenticated` di policy |
| `address already in use` pada port X | Proses lain pakai port X | Cek dengan `ss -tlnp`, kill atau ganti port |
| `ModuleNotFoundError: X` | Package belum install | `pip install X` atau `npm install X` |
| `FileNotFoundError: brain/public` | Relative path salah atau folder tidak ada | Cek manifest.json, pastikan path relative |
| `502 Bad Gateway` | Backend/frontend tidak jalan | Restart proses, cek log |
| `SSL validation failed NXDOMAIN` | DNS belum propagasi | Tunggu propagasi, cek dnschecker.org |

Tabel ini adalah awal dari **knowledge base self-healing** SIDIX.
Setiap error baru yang ditemui → tambah baris baru → SIDIX makin pintar diagnosa.

---

## Langkah Implementasi (Roadmap)

### Fase 1 — Knowledge base (sekarang)
- Kumpulkan error patterns ke corpus (research notes)
- SIDIX bisa mendiagnosis jika ditanya

### Fase 2 — Error ingestion (3 bulan)
- Log error dari frontend (Supabase) → masuk ke corpus otomatis
- SIDIX bisa menjawab: "Error apa yang paling sering terjadi bulan ini?"

### Fase 3 — Fix suggestion (6 bulan)
- SIDIX generate fix suggestion berdasarkan error + corpus
- Admin 1-click apply

### Fase 4 — Supervised auto-fix (12 bulan)
- Fix dengan confidence tinggi → auto-apply setelah admin grant izin
- Full audit trail di LIVING_LOG

---

## Filosofi: Sistem yang Belajar dari Kesalahannya Sendiri

Setiap bug yang terjadi adalah pelajaran.
Setiap error yang dicatat adalah data.
Setiap fix yang dieksekusi adalah pengalaman.

SIDIX tidak harus sempurna dari awal.
SIDIX harus bisa **tumbuh dari ketidaksempurnaannya**.

Ini bukan bug — ini feature dalam proses.
