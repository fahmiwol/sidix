# Cara AI Berpikir — Dari Input ke Eksekusi

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Catatan ini mendokumentasikan proses kognitif Claude (AI agent) secara eksplisit,
> agar SIDIX bisa memahami, meniru, dan akhirnya mengembangkan pola berpikir sendiri.

---

## Gambaran Besar: Loop Kognitif AI

```
INPUT (teks, gambar, kode, konteks)
    ↓
[1] INTAKE — Apa yang masuk?
    ↓
[2] PARSING — Apa maksudnya?
    ↓
[3] ANALISIS — Apa situasinya?
    ↓
[4] KEPUTUSAN — Apa yang harus dilakukan?
    ↓
[5] PERENCANAAN — Bagaimana urutannya?
    ↓
[6] EKSEKUSI — Lakukan.
    ↓
[7] VERIFIKASI — Berhasil? Ada yang salah?
    ↓
[8] OUTPUT — Sampaikan hasil + dokumentasikan
    ↓
[9] LOOP — Tunggu input berikutnya, update konteks
```

Setiap langkah punya teknik spesifik. Mari kita bongkar satu per satu.

---

## [1] INTAKE — Membaca Input

Ketika input masuk, AI tidak membaca secara linear dari atas ke bawah.
AI melakukan **scanning berlapis**:

### Layer 1: Signal kuat (dalam 0.1 detik pertama)
- Error message (kata kunci: "Error", "Failed", "502", "not found")
- Status indicator (warna, icon, angka)
- URL / domain / path (konteks lokasi)
- Nama file / fungsi yang disebut

### Layer 2: Struktur (memahami bentuk)
- Ini pertanyaan, perintah, atau laporan?
- Ada screenshot? Ada kode? Ada log?
- Berapa banyak konteks yang tersedia?

### Layer 3: Niat (apa yang sebenarnya diinginkan)
- Tersurat: "tolong perbaiki error ini"
- Tersirat: user frustrasi, butuh solusi cepat, bukan penjelasan panjang
- Kontekstual: berdasarkan percakapan sebelumnya, ini step ke-5 dari deploy

**Contoh nyata:**
```
User kirim: screenshot "502 Bad Gateway nginx"

Layer 1: "502 Bad Gateway" = server error, nginx = web server
Layer 2: laporan masalah, butuh solusi
Layer 3: user tidak minta penjelasan nginx — mereka mau app jalan lagi
```

---

## [2] PARSING — Memahami Makna

Parsing bukan hanya membaca kata — tapi membangun **model mental** situasi.

### Teknik: State Mapping
Buat peta: "apa yang kita tahu" vs "apa yang tidak kita tahu"

```
DIKETAHUI:
  ✓ App di port 4000 (dari percakapan sebelumnya)
  ✓ Nginx proxy ke 127.0.0.1:4000
  ✓ 502 = nginx tidak bisa reach backend

TIDAK DIKETAHUI:
  ? Apakah serve process masih jalan?
  ? Apakah ini karena reboot atau crash?
  ? Log terakhir apa?

DIASUMSIKAN (dengan confidence tinggi):
  ~ Proses 'serve dist -p 4000' mati (nohup tanpa PM2 = mati saat reboot)
```

### Teknik: Resolusi Ambiguitas
Ketika user bilang "itu masih salah" — apa yang salah?
AI mencari referensi terdekat dalam konteks sebelumnya, bukan menebak acak.

---

## [3] ANALISIS — Memahami Situasi

Analisis = menghubungkan fakta ke **pola yang dikenal**.

### Pola Database AI:
```
"502 Bad Gateway" + "nginx" + konteks: serve port 4000
→ Pattern match: "upstream process not running"
→ Confidence: 95%
→ Fix: restart serve

"FileNotFoundError: D:\\MIGHAN Model\\brain\\public"
→ Pattern match: "hardcoded absolute path, cross-platform issue"
→ Fix: gunakan relative path + resolve dari __file__
```

### Pertanyaan analisis yang selalu diajukan:
1. **Apa root cause-nya?** (bukan symptom)
2. **Sudah pernah terjadi sebelumnya?** (cek LIVING_LOG / penelitian sebelumnya)
3. **Apa yang bisa rusak kalau fix ini dilakukan?** (side effects)
4. **Ada solusi lebih baik jangka panjang?** (tech debt)

---

## [4] KEPUTUSAN — Memilih Tindakan

Keputusan dibuat dengan **matriks implisit**:

| Opsi | Effort | Risk | Dampak | Reversible? |
|---|---|---|---|---|
| Restart nohup | Rendah | Rendah | Langsung | Ya |
| Setup PM2 | Sedang | Rendah | Permanen | Ya |
| Ganti VPS | Tinggi | Tinggi | Besar | Tidak |

AI memilih **opsi dengan effort minimum yang menyelesaikan masalah nyata**,
sambil menyebut solusi jangka panjang sebagai rekomendasi.

### Prinsip keputusan:
- **Reversible > Irreversible** — selalu pilih yang bisa di-undo dulu
- **Root cause > Symptom** — jangan tambal, perbaiki sumbernya
- **Sekarang vs Nanti** — bedakan yang urgent dari yang penting
- **Konteks user** — solo founder, resources terbatas → pilih yang simpel

---

## [5] PERENCANAAN — Urutan Eksekusi

Sebelum eksekusi, AI membuat **dependency graph** implisit:

```
Goal: Supabase terintegrasi di frontend

Dependencies:
  [A] Install @supabase/supabase-js        (tidak ada dep)
  [B] Buat src/lib/supabase.ts             (butuh A selesai)
  [C] Buat .env dengan keys               (tidak ada dep)
  [D] Buat fungsi newsletter/feedback     (butuh B selesai)
  [E] Integrasi ke UI                     (butuh D selesai)
  [F] Build & deploy ke server            (butuh E selesai)

Urutan: A → B (paralel dengan C) → D → E → F
```

### Pertanyaan perencanaan:
- **Apa yang bisa dilakukan paralel?** (hemat waktu)
- **Apa yang blocking?** (kerjakan dulu)
- **Di mana titik verifikasi?** (cek sebelum lanjut)
- **Apa yang irreversible?** (hati-hati)

---

## [6] EKSEKUSI — Melakukan dengan Presisi

Eksekusi bukan asal jalan — ada **presisi dalam setiap langkah**:

### Kode: Minimal, Benar, Terbaca
```typescript
// Bukan ini (terlalu verbose):
export async function doNewsletterSubscription(emailAddressString: string): Promise<{success: boolean, errorMessage: string | null}> {

// Tapi ini (minimal dan jelas):
export async function subscribeNewsletter(email: string) {
```

### File: Edit Bedah, Bukan Tulis Ulang
Kalau hanya perlu ubah 3 baris → gunakan Edit, bukan Write ulang seluruh file.
Ini mengurangi risiko menghapus kode yang tidak disengaja.

### Command: Verifikasi Sebelum dan Sesudah
```bash
# Sebelum: cek kondisi awal
ps aux | grep serve

# Eksekusi
nohup serve dist -p 4000 &

# Setelah: verifikasi berhasil
curl -I http://localhost:4000
```

---

## [7] VERIFIKASI — Konfirmasi Hasil

AI tidak berasumsi eksekusi berhasil. Selalu ada **verification step**:

| Tipe aksi | Cara verifikasi |
|---|---|
| Deploy backend | `curl /health` → cek JSON response |
| Build frontend | Cek output Vite (no errors, file sizes) |
| Database migration | Screenshot Table Editor — tabel muncul? |
| Git push | Cek output "main -> main" tanpa error |
| DNS | dnschecker.org → semua node resolve ke IP yang sama |

---

## [8] OUTPUT — Menyampaikan Hasil

Output yang baik bukan yang paling panjang — tapi yang **paling berguna**.

### Struktur output AI:
```
[Status singkat] → "Berhasil ✅" atau "Ada masalah ⚠️"
[Apa yang dilakukan] → ringkasan 1-2 kalimat
[Apa yang perlu user lakukan] → instruksi konkret, bukan teori
[Langkah selanjutnya] → supaya momentum tidak terputus
```

### Yang dihindari:
- Penjelasan panjang kalau user butuh solusi cepat
- Jargon teknis tanpa konteks
- Memberikan 5 opsi kalau cukup 1 rekomendasi jelas
- Mengulang apa yang sudah diketahui user

---

## [9] LOOP — Belajar dari Feedback

Setiap respons user adalah **sinyal**:

| Respons user | Artinya | Adjustmen |
|---|---|---|
| "oke lanjut" | Benar, user puas | Pertahankan pola ini |
| "masih error" | Diagnosis salah | Re-analisis, cari root cause lain |
| "kecil banget logonya" | Output tidak memenuhi ekspektasi implisit | Tanya atau coba iterasi |
| "itu harusnya nggak ada dong" | Asumsi salah tentang requirement | Reset pemahaman, konfirmasi ulang |
| Screenshot tanpa kata-kata | User menunjukkan state, butuh diagnosis | Scan gambar, identifikasi masalah |

---

## Cara SIDIX Bisa Meniru Ini

SIDIX saat ini berbasis BM25 retrieval — dia mencari dokumen yang relevan,
bukan "berpikir" secara agentic. Untuk SIDIX bisa berpikir seperti Claude:

### Jangka pendek (sudah bisa):
- **Retrieval kontekstual**: temukan research note yang relevan dengan pertanyaan
- **Jawaban berbasis evidence**: kutip sumber dari corpus, bukan halusinasi
- **Pattern matching**: kenali pola error dari research notes

### Jangka menengah (roadmap):
- **ReAct loop**: Reason → Act → Observe → Reason (sudah ada di agent_react.py)
- **Tool use**: SIDIX bisa memanggil tools (search, calculator, API)
- **Memory**: simpan konteks percakapan antar sesi

### Jangka panjang (visi):
- **Self-reflection**: SIDIX bisa mengevaluasi kualitas jawabannya sendiri
- **Knowledge gap detection**: SIDIX tahu apa yang dia tidak tahu
- **Proactive documentation**: SIDIX meminta dokumentasi untuk topik yang sering ditanya tapi tidak ada di corpus
