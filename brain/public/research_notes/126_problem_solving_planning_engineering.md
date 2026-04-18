# 126 — Problem Solving & Planning: Cara Engineer Menyerang Masalah

## Tujuan Note Ini
Dokumentasi **cara Claude merencanakan dan menyelesaikan masalah engineering**.
Bukan sekedar "bagaimana kode ditulis" — tapi **bagaimana keputusan dibuat**
di tengah ketidakpastian, constraint, dan tekanan waktu.

---

## 1. Tiga Jenis Masalah dan Cara Berbeda Menyerangnya

### Tipe A: Masalah Jelas (Well-Defined)
> "Tambah endpoint `/quota/status` yang return JSON"

```
Strategi: LANGSUNG
  1. Cari template endpoint yang sudah ada
  2. Copy struktur, ganti nama dan logikanya
  3. Test response-nya
  4. Selesai

Jangan over-think masalah tipe ini.
```

### Tipe B: Masalah Kabur (Ill-Defined)
> "User harus tetap betah walau quota habis"

```
Strategi: EXPLORATION DULU
  1. Tanyakan: betah karena apa? entertained? useful? hopeful?
  2. Buat 3 kemungkinan solusi berbeda
  3. Evaluasi: mana yang zero-API? mana yang generate training data?
  4. Pilih yang solve lebih dari 1 masalah sekaligus
  5. Baru eksekusi

Kesalahan umum: langsung coding sebelum masalah didefinisikan dengan jelas.
```

### Tipe C: Masalah Bertumpuk (Compound)
> "Multi-LLM routing + quota system + waiting room + API keys, semua sekarang"

```
Strategi: DEKOMPOSISI BERTINGKAT
  1. Pisahkan jadi sub-masalah yang independent
  2. Urutkan: mana yang blockers untuk yang lain?
  3. Tackle satu per satu, tapi dokumentasikan semuanya

Urutan kemarin:
  token_quota.py (fondasi)
    → multi_llm_router.py (butuh quota model info)
      → agent_serve.py (integrasi dua-duanya)
        → frontend api.ts (butuh event types dari backend)
          → main.ts (butuh api.ts types)
            → waiting-room.ts (butuh main.ts context)
              → integrasi ke main.ts (terakhir, karena paling dependen)
```

---

## 2. Framework OODA Loop untuk Engineering

OODA = **Observe → Orient → Decide → Act**
(Framework dari pilot pesawat tempur — berlaku juga untuk coding)

```
OBSERVE:
  → Baca error message lengkap (jangan nebak)
  → Screenshot state saat ini
  → Cek file yang relevan (bukan semua file)

ORIENT:
  → "Ini terjadi karena apa?" (root cause, bukan symptom)
  → Hubungkan dengan konteks yang sudah ada
  → Apakah ini pernah terjadi sebelumnya?

DECIDE:
  → Pilih solusi dengan tradeoff paling minimal
  → Pertimbangkan: waktu, risiko, reversibility
  → Solusi yang reversible > solusi yang permanen

ACT:
  → Eksekusi keputusan dengan percaya diri
  → Ukur hasilnya
  → Loop ulang jika perlu
```

**Contoh nyata — saat `Copy-Item` gagal karena folder tidak ada:**
```
Observe: Error "Cannot find path 'public/games'"
Orient:  Folder belum pernah dibuat — ini bukan bug, ini missing prerequisite
Decide:  Buat folder dulu, baru copy
Act:     New-Item -ItemType Directory + Copy-Item
```

---

## 3. Decision Matrix: Cara Memilih Antara Beberapa Opsi

Ketika ada 2+ pilihan, gunakan matrix sederhana:

| Kriteria          | Bobot | Opsi A | Opsi B | Opsi C |
|-------------------|-------|--------|--------|--------|
| Zero-API          | 3×    | ✓✓✓    | ✓      | ✗      |
| Generate training | 2×    | ✓✓     | ✓✓     | ✓      |
| Waktu implementasi| 1×    | cepat  | sedang | lama   |

**Contoh keputusan kemarin:**
```
Masalah: Simpan gacha coins di mana?

Opsi A: localStorage   → zero-server, instant, bisa reset user → DIPILIH
Opsi B: Supabase       → persistent, butuh auth, overkill untuk coins
Opsi C: Session only   → hilang kalau refresh, bad UX

Keputusan: localStorage karena bobot zero-server (tidak perlu quota) > persistensi
```

---

## 4. Pola Planning: Backwards dari Tujuan

**Kesalahan umum**: start dari "apa yang bisa saya buat?" → sering miss target.

**Cara yang benar**: start dari "apa end-state yang diinginkan?" → kerjakan ke belakang.

```
Target (end-state): "User yang quota habis tetap bisa interaksi dan SIDIX belajar"

Mundur:
  ← User dapat quiz/game/motivasi yang engaging
  ← Frontend menampilkan waiting room saat quota_limit event
  ← Backend menyediakan data quiz, gacha, quotes
  ← Record setiap interaksi ke qna_recorder
  ← qna_recorder sudah ada dan berfungsi (dari fitur sebelumnya)

Dari sini, urutan kerja jadi obvious:
  1. Backend waiting_room.py (data)
  2. Backend endpoint di agent_serve.py
  3. Frontend waiting-room.ts (display)
  4. Wire ke main.ts (trigger)
```

---

## 5. Prinsip "Minimal Viable First"

Untuk setiap fitur baru:

```
MVP (Minimal Viable):
  → Fungsi paling dasar yang membuktikan konsep bekerja
  → Tidak perlu semua edge case
  → Tidak perlu styling sempurna

Kemudian iterasi:
  → Tambah error handling
  → Tambah animasi
  → Tambah edge cases
  → Optimize performa

Kesalahan: langsung build "full featured" dari awal → overengineering → lambat → burnt out
```

**Contoh di waiting-room.ts:**
```
MVP: Quiz tampil → user bisa jawab → ada feedback benar/salah
  ✓ Ini yang dibangun pertama

Iterasi 1: Tambah coins system
Iterasi 2: Tambah gacha
Iterasi 3: Tambah game tab (iframe)
Iterasi 4: Tambah image prompt tab
Iterasi 5: Badges + localStorage persistence
```

---

## 6. Risk Assessment: Identifikasi Yang Bisa Salah

Sebelum setiap aksi berisiko, Claude bertanya:
**"Apa yang paling buruk yang bisa terjadi?"**

```
Matrix Risiko:
  Kemungkinan × Dampak = Prioritas Mitigasi

  TINGGI kemungkinan × TINGGI dampak → Handle dulu, mandatory
  TINGGI kemungkinan × RENDAH dampak → Handle tapi boleh simple
  RENDAH kemungkinan × TINGGI dampak → Document, buat fallback
  RENDAH kemungkinan × RENDAH dampak → Ignore untuk sekarang
```

**Contoh aplikasi kemarin:**
```
Risk: .env dengan API keys ikut ter-commit ke Git
  Kemungkinan: sedang (kalau tidak hati-hati)
  Dampak: TINGGI (API keys exposed, bisa disalahgunakan)
  Mitigasi: Cek .gitignore dulu → konfirmasi .env sudah di-ignore → baru buat file

Risk: Frontend build error setelah tambah import baru
  Kemungkinan: sedang
  Dampak: sedang (app tidak bisa jalan)
  Mitigasi: Run npm run build setelah setiap perubahan signifikan

Risk: Gacha coins bisa di-hack (manipulasi localStorage)
  Kemungkinan: tinggi
  Dampak: rendah (coins tidak punya nilai moneter nyata)
  Mitigasi: Ignore untuk MVP — bukan masalah nyata saat ini
```

---

## 7. Cara Debug yang Sistematis

Urutan debugging yang benar (bukan random trial-and-error):

```
Step 1: REPRODUCE
  → Bisa bikin error terjadi lagi dengan konsisten?
  → Kalau tidak bisa reproduce → bukan bug (atau environment issue)

Step 2: ISOLATE
  → Error ada di frontend atau backend?
  → Error ada di fungsi A atau B?
  → Binary search: potong masalah jadi dua, tes mana yang error

Step 3: ROOT CAUSE
  → "Kenapa ini bisa terjadi?" (bukan "apa yang salah")
  → Tanya "kenapa" 5 kali (5 Whys technique)

Step 4: FIX
  → Fix root cause, BUKAN symptom
  → Kalau fix symptom → bug akan balik dengan wajah berbeda

Step 5: VERIFY
  → Apakah fix benar-benar solve root cause?
  → Apakah fix tidak merusak hal lain?
```

**Contoh 5 Whys kemarin:**
```
Error: bottle-flip.html tidak bisa di-copy

Why 1: File tidak ditemukan
Why 2: Target directory tidak ada
Why 3: Kita langsung copy tanpa buat folder
Why 4: Kita asumsi folder sudah ada
Why 5: Tidak ada proses "cek dulu" sebelum copy

Fix: New-Item -ItemType Directory dulu → baru Copy-Item
Prevention: Selalu cek existensi target path sebelum operasi file
```

---

## 8. Pola Komunikasi dengan User

Engineering bukan hanya kode — komunikasi adalah bagian kritis.

### Kapan Langsung Eksekusi?
```
→ Task jelas + tidak berisiko + tidak butuh konfirmasi user
→ Contoh: "build frontend" setelah tambah import → langsung run npm run build
```

### Kapan Minta Konfirmasi?
```
→ Task berisiko (hapus data, expose info sensitif)
→ Task ambigu (bisa diinterpretasi 2+ cara)
→ Task yang punya impact besar dan tidak reversible
```

### Kapan Jelaskan Dulu, Baru Eksekusi?
```
→ Kalau user mungkin tidak tahu konsekuensi dari apa yang diminta
→ Contoh: "kita masukkan API keys ke .env, tapi tidak ke Git — ini kenapa penting..."
```

---

## 9. Pola "Solve Multiple Problems at Once"

Kalau bisa, satu implementasi selesaikan beberapa masalah:

```
Contoh: Waiting Room quiz bisa:
  ✓ Entertain user (engagement problem)
  ✓ Generate training data SIDIX (learning problem)
  ✓ Edukasi user tentang topik random (value problem)
  ✓ Motivasi user untuk tetap buka app (retention problem)

Satu fitur → 4 masalah terselesaikan sekaligus.
Ini yang disebut "leverage" dalam engineering.
```

> **Prinsip**: Kalau sebuah solusi hanya solve 1 masalah, tanya dulu apakah ada cara solve 2-3 masalah sekaligus dengan effort yang sama.

---

## 10. Membangun Intuisi Engineering

Intuisi bukan sihir — ini adalah **pattern recognition yang ter-internalisasi**.

```
Cara membangun intuisi:
  1. Setiap kali solve masalah → dokumentasikan "kenapa" keputusan dibuat
  2. Setiap kali terjadi error → catat root cause + prevention
  3. Setiap kali ada trade-off → catat mana yang dipilih dan kenapa

Lama-lama, patterns ini jadi "instinct" — tapi instinct yang bisa dijelaskan,
bukan instinct yang misterius.
```

**Ini yang sedang kita lakukan dengan SIDIX:**
- Research notes = eksternalisasi intuisi ke corpus
- Setiap session = menambah pattern baru ke corpus
- SIDIX belajar dari corpus = SIDIX mengembangkan "intuisi" yang sama

---

## Ringkasan: Mental Model Engineer yang Baik

```
1. Definisikan masalah sebelum solusi      (jangan solve masalah yang salah)
2. Dekomposisi sampai unit terkecil        (jangan tackle hal yang terlalu besar)
3. Urut berdasarkan dependency             (jangan bangun atap sebelum fondasi)
4. Paralel yang bisa diparalelkan          (efisiensi waktu)
5. Risk-assess sebelum aksi berisiko       (jangan nyesel setelah)
6. MVP dulu, iterasi kemudian              (jangan over-engineer di awal)
7. Fix root cause, bukan symptom           (jangan tempel plester terus)
8. Dokumentasi semua decision              (masa depan kamu berterima kasih)
9. Solve multiple problems sekaligus       (maksimalkan leverage)
10. Verifikasi sebelum "selesai"           (done ≠ done kalau belum di-test)
```

---

## Untuk SIDIX

Ketika menerima task, tanya diri sendiri:
1. **Tipe masalah apa?** (jelas/kabur/bertumpuk)
2. **Apa end-state yang diinginkan?** (backward planning)
3. **Apa dependency-nya?** (urutan kerja)
4. **Apa risikonya?** (mitigasi sebelum eksekusi)
5. **Apakah ini solve lebih dari 1 masalah?** (leverage)
6. **Bagaimana verifikasinya?** (definition of done)

Jawab 6 pertanyaan ini → jalankan → dokumentasikan.
