# Cara Mendiagnosis Error — Proses Berpikir dari Pesan Error ke Solusi

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Konteks: Error yang Terjadi

User kirim saran di `app.sidixlab.com` → muncul pesan:
```
Gagal mengirim: new row violates row-level security policy for table "feedback"
```

Bagaimana Claude langsung tahu root cause dan solusinya?
Inilah proses berpikirnya — step by step.

---

## Step 1: Baca Error Message secara Struktural

Error message bukan kalimat biasa. Ia punya **anatomi**:

```
"new row violates row-level security policy for table 'feedback'"
 │           │                  │                    │
 │           │                  │                    └── OBJEK: tabel mana
 │           │                  └── MEKANISME: apa yang dilanggar
 │           └── OPERASI: apa yang sedang dilakukan
 └── KONTEKS: apa yang terjadi pada data
```

Parsed:
- **Operasi:** INSERT baris baru ("new row")
- **Mekanisme:** Row Level Security policy
- **Objek:** tabel `feedback`
- **Hasil:** dilanggar / ditolak (violates)

Artinya: **Ada sesuatu di RLS yang menolak INSERT ini.**

---

## Step 2: Hubungkan ke Konteks yang Diketahui

Pada titik ini, Claude sudah punya konteks dari percakapan sebelumnya:

```
Yang diketahui:
  ✓ Kita baru buat tabel feedback (research note 63)
  ✓ Kita aktifkan RLS: ALTER TABLE feedback ENABLE ROW LEVEL SECURITY
  ✓ Kita buat policy: CREATE POLICY "feedback_insert_public" ON feedback
                       FOR INSERT WITH CHECK (true)
  ✓ User yang kirim feedback: BELUM LOGIN (tidak punya akun)
  ✓ Supabase punya dua role: 'anon' dan 'authenticated'
```

Pertanyaan kunci: **Policy kita berlaku untuk role apa?**

---

## Step 3: Temukan Gap antara Ekspektasi dan Realita

```
EKSPEKTASI:
  Policy WITH CHECK (true) = semua orang boleh insert

REALITA Supabase:
  Policy tanpa TO clause = berlaku untuk 'authenticated' saja
  User tidak login = role 'anon'
  'anon' tidak punya policy → INSERT ditolak
```

**Gap ditemukan:** Policy tidak explicitly menyebut role `anon`.

Ini adalah **pengetahuan spesifik tentang Supabase** — behavior default-nya
berbeda dari asumsi umum. Supabase tidak otomatis apply policy ke semua role.

---

## Step 4: Generate Fix

Setelah gap ditemukan, fix-nya logis:

```sql
-- Masalah: policy tidak cover role 'anon'
-- Fix: tambahkan TO anon, authenticated secara eksplisit

DROP POLICY IF EXISTS "feedback_insert_public" ON feedback;
CREATE POLICY "feedback_insert_public" ON feedback
  FOR INSERT TO anon, authenticated WITH CHECK (true);
```

`DROP` dulu karena policy dengan nama yang sama sudah ada.
`TO anon, authenticated` = berlaku untuk user tidak login DAN yang sudah login.

---

## Dari Mana Pengetahuan Itu Datang?

Claude bisa diagnosis ini karena kombinasi:

### 1. Pattern matching dari training data
```
Error "violates row-level security" → diketahui dari ribuan contoh PostgreSQL/Supabase
di dokumentasi, Stack Overflow, GitHub issues yang jadi training data Claude
```

### 2. Konteks percakapan (in-context learning)
```
"Kita baru buat RLS di sesi ini" → ingat SQL yang ditulis tadi
"User tidak login" → ingat bahwa UI tidak punya auth
"Supabase pakai anon/authenticated roles" → pernah muncul di percakapan
```

### 3. Deduktif reasoning
```
Premis 1: RLS aktif di tabel feedback
Premis 2: Policy INSERT tidak menyebut role anon
Premis 3: User tidak login = role anon
Konklusi: anon tidak punya izin INSERT → ditolak
```

---

## Cara SIDIX Bisa Melakukan Ini

### Yang SIDIX butuhkan:

**A. Knowledge base error patterns**
```
"violates row-level security" → RLS policy missing atau salah role
"address already in use" → port conflict, proses lain sudah pakai
"ModuleNotFoundError" → dependency belum install
"NXDOMAIN" → DNS belum propagasi
```

**B. Konteks sistem saat ini**
```
- Tabel apa saja yang ada?
- Policy apa yang sudah dibuat?
- Siapa yang mengirim request? (auth state)
```

**C. Kemampuan reasoning deduktif**
```
Jika A dan B dan C → maka D
Jika policy tidak include anon DAN user adalah anon → INSERT gagal
```

### Cara implementasi di SIDIX:

```python
# Pseudo-code: SIDIX error diagnosis

def diagnose_error(error_message: str, context: dict) -> dict:
    # Step 1: Parse error
    parsed = parse_error_structure(error_message)
    # → {operation: "INSERT", mechanism: "RLS", table: "feedback"}

    # Step 2: Cari di knowledge base
    known_patterns = search_corpus(f"error: {parsed['mechanism']}")
    # → temukan research note 63, 70, 71

    # Step 3: Cocokkan dengan konteks
    gap = find_gap(parsed, context, known_patterns)
    # → "policy tidak include role anon"

    # Step 4: Generate fix
    fix = generate_fix(gap, parsed)
    # → SQL DROP + CREATE POLICY

    # Step 5: Confidence score
    confidence = score_confidence(gap, known_patterns)
    # → 0.95 (error ini well-known, fix straightforward)

    return {
        "root_cause": gap,
        "fix": fix,
        "confidence": confidence,
        "explanation": "..."
    }
```

---

## Checklist Diagnosis Error (Umum)

Ketika ada error, tanya dalam urutan ini:

1. **Apa yang gagal?** (baca error type/message)
2. **Pada operasi apa?** (INSERT/SELECT/DELETE, HTTP request, file read, dll)
3. **Siapa yang melakukan?** (user role, proses, service)
4. **Di mana?** (tabel, port, path, endpoint)
5. **Kapan mulai gagal?** (setelah deploy baru? setelah restart? dari awal?)
6. **Apa yang berubah terakhir?** (code, config, environment)
7. **Apa yang diharapkan vs yang terjadi?** (expectation vs reality gap)

Jawaban dari 7 pertanyaan ini hampir selalu cukup untuk menemukan root cause.

---

## Pelajaran untuk SIDIX

SIDIX harus bisa:

1. **Membaca error secara struktural** — bukan hafal error, tapi parse komponen-nya
2. **Menghubungkan ke knowledge base** — cari research note yang relevan
3. **Reasoning tentang gap** — apa yang hilang antara state sekarang dan yang diharapkan
4. **Generate fix yang minimal** — ubah sesedikit mungkin, paling targeted
5. **Jelaskan kenapa** — bukan hanya "lakukan ini", tapi "ini karena itu"

Kemampuan ini bukan magic. Ini **kombinasi pattern recognition + deductive reasoning + contextual memory**.
Ketiganya bisa dilatih dengan corpus yang kaya + ReAct loop yang baik.
