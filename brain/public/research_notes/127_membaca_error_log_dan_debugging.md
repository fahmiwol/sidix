# 127 — Membaca Error Log & Menentukan Langkah Fix

## Tujuan Note Ini
SIDIX harus bisa **membaca output log server** sendiri — mendiagnosis masalah,
memisahkan yang darurat dari yang tidak, dan memutuskan langkah selanjutnya.
Ini adalah keterampilan inti seorang engineer.

---

## Kasus Nyata: VPS sidix-brain Crash Loop (2026-04-18)

### Log yang Diterima
```
curl: (7) Failed to connect to localhost port 8765 after 0 ms: Connection refused
Expecting value: line 1 column 1 (char 0)

[PM2] sidix-brain | status: online | restarts: 9
```

---

## Langkah 1: OBSERVE — Baca Semua Signal, Jangan Panik Dulu

Dari log di atas, ada **3 signal**:
```
Signal A: curl Connection refused           → port 8765 tidak ada yang listen
Signal B: restarts: 9                       → proses sudah restart 9 kali
Signal C: status: online, uptime: 105s     → tapi sekarang proses jalan OK
```

**Pertanyaan pertama:** Apakah masalah ini SEKARANG atau TADI?

```
Clue: uptime 105s → proses sudah jalan 1+ menit
Clue: curl dijalankan LANGSUNG setelah pm2 restart

Hipotesis: curl dijalankan terlalu cepat, sebelum Python app siap.
Python app butuh ~3-5 detik untuk startup (import library besar seperti groq, gemini).
```

---

## Langkah 2: ORIENT — Pisahkan Error dari Warning

Dari log PM2 yang lengkap:

```bash
# Error serius (menyebabkan crash):
# → TIDAK ADA error serius di log ini

# Warning (bukan error, tapi perlu diperhatikan):
FutureWarning: google.generativeai package deprecated
FutureWarning: Python 3.10 akan stop support di google.api_core

# Info normal (bukan masalah):
INFO: Uvicorn running on http://0.0.0.0:8765
INFO: Application startup complete.
INFO: GET /health HTTP/1.1 200 OK  (response normal!)
```

**Kesimpulan setelah ORIENT:**
- Proses TIDAK crash → restarts ke-9 terjadi SEBELUM sesi ini
- Sekarang proses JALAN dengan baik (health check 200 OK)
- Warning deprecated adalah teknis debt, bukan emergency

---

## Langkah 3: DECIDE — Prioritas Fix

```
Masalah A: curl gagal (Connection refused)
  → Root cause: timing, bukan crash
  → Fix: tidak perlu fix, tunggu saja setelah restart
  → Priority: BISA DIABAIKAN

Masalah B: restarts:9
  → Kemungkinan: crash-crash lama (sebelum sesi ini), atau rolling restart normal
  → Perlu investigasi LEBIH DALAM kalau ini terus bertambah
  → Fix sekarang: monitor apakah angkanya bertambah
  → Priority: MONITOR, tidak urgent

Masalah C: google.generativeai deprecated
  → Tidak memblok fungsi sekarang, tapi akan break di masa depan
  → Solusi: ganti ke google-genai SDK baru
  → Priority: FIX SEGERA (sebelum Google benar-benar mati)
```

---

## Cara Membedakan: Warning vs Error vs Critical

```
CRITICAL (sistem down):
  → Traceback + Exception tidak tertangkap
  → Port tidak bisa di-bind (Address already in use)
  → ImportError yang tidak di-catch
  → Database connection refused pada startup

ERROR (fungsi gagal tapi sistem jalan):
  → Exception yang di-catch dan di-log sebagai error
  → Status 500 dari endpoint tertentu
  → "groq error: ..." tapi fallback ke provider lain

WARNING (tidak rusak, tapi perlu perhatian):
  → FutureWarning, DeprecationWarning
  → Performance degradation
  → Rate limit approaching

INFO (normal operation):
  → Request masuk
  → Startup complete
  → Health check passed
```

**Rule untuk SIDIX:**
> Kalau hanya ada WARNING dan INFO di log → sistem jalan. Tenang.
> Kalau ada Traceback/Exception yang tidak di-catch → ini yang harus difix duluan.

---

## Langkah 4: ACT — Cara Fix `google.generativeai` Deprecated

### Masalah
```python
# Kode lama (deprecated):
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content(prompt)
```

### Diagnosis Root Cause
```
Google merilis SDK baru: google-genai (paket: pip install google-genai)
SDK lama: google-generativeai → masih jalan, tapi tidak dapat update
SDK baru: google-genai → API berbeda, lebih clean
```

### Fix: SDK Baru dengan Fallback
```python
# Coba SDK baru dulu
try:
    from google import genai as google_genai
    client = google_genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-1.5-flash-latest",
        contents=prompt,
    )
    text = response.text
except ImportError:
    # Fallback ke lama kalau google-genai belum terinstall
    import google.generativeai as genai_old
    genai_old.configure(api_key=api_key)
    model_old = genai_old.GenerativeModel("gemini-1.5-flash-latest")
    text = model_old.generate_content(prompt).text
```

### Perbedaan API Lama vs Baru
```python
# LAMA (google-generativeai):
genai.configure(api_key=key)           # global config
model = genai.GenerativeModel(name)   # object model
response = model.generate_content(p)  # method di model

# BARU (google-genai):
client = google_genai.Client(api_key=key)      # client object
response = client.models.generate_content(     # method di client
    model=name,
    contents=p,
)
```

---

## Pola Umum: Cara Membaca Stack Trace

```
Traceback (most recent call last):
  File "agent_serve.py", line 45, in ask_stream    ← titik masuk
    result = route_generate(...)                    ← fungsi yang dipanggil
  File "multi_llm_router.py", line 163, in gemini_generate  ← di dalam ini
    import google.generativeai as genai             ← baris ini yang bermasalah
ImportError: No module named 'google.generativeai' ← ini PENYEBAB SEBENARNYA
```

**Cara baca:**
1. Mulai dari **baris paling bawah** — itu root cause-nya
2. Naik ke atas untuk melihat **alur pemanggilan**
3. File + line number → pergi ke sana langsung

---

## Decision Tree: "Harus Fix Sekarang atau Nanti?"

```
Ada error di log?
  ├── YA: Apakah sistem masih merespons?
  │   ├── TIDAK → CRITICAL, fix segera
  │   └── YA → ERROR, jadwalkan fix
  └── TIDAK: Hanya warning?
      ├── DeprecationWarning/FutureWarning
      │   └── Tanya: kapan deprecated? ← kalau < 6 bulan, fix segera
      └── PerformanceWarning
          └── Monitor dulu, fix kalau jadi bottleneck
```

**Dalam kasus ini:**
- `google.generativeai` → deprecated sekarang, Google sudah minta pindah → **fix segera**
- Python 3.10 end of life → Oktober 2026 → **fix dalam 3 bulan**
- `curl` connection refused → timing issue → **tidak perlu fix**

---

## Pola Khusus: Timing Issues saat Deployment

```
Symptom: Connection refused langsung setelah restart
Cause:   App butuh waktu startup (import library, init DB connection, dll)
Fix:     Tunggu 5-10 detik, coba lagi

Cara yang lebih baik:
  # Tunggu sampai health check berhasil
  until curl -s http://localhost:8765/health > /dev/null; do
    echo "Waiting for server..."
    sleep 2
  done
  echo "Server ready!"
```

---

## Cara Engineer Menentukan Langkah Selanjutnya

Setelah membaca log, pertanyaan yang harus dijawab:

```
1. Apakah sistem SEKARANG berfungsi? (yes/no)
   → YES: tidak perlu panik, bisa fix dengan tenang
   → NO: ini emergency, fix sekarang

2. Apa ROOT CAUSE yang paling likely?
   → Bukan symptom (curl gagal), tapi penyebab (deprecated library)

3. Fix apa yang paling SAFE?
   → Fix yang mudah di-rollback
   → Fix yang tidak merusak hal lain

4. Apakah perlu DEPLOY ulang atau cukup restart?
   → Perubahan kode → harus git pull + restart
   → Perubahan env var → cukup pm2 restart --update-env
   → Perubahan dependency → pip install + restart

5. Bagaimana VERIFIKASI fix berhasil?
   → curl /health → 200 OK
   → curl /llm/status → gemini: available: true
   → Test kirim pesan, lihat provider mana yang dipakai
```

---

## Ringkasan untuk SIDIX

Ketika melihat error/warning di log:

```
Langkah 1: CALM DOWN — baca semua signal dulu
Langkah 2: CLASSIFY — critical / error / warning / info?
Langkah 3: TIMING — apakah ini sekarang atau masa lalu?
Langkah 4: ROOT CAUSE — baris paling bawah stack trace
Langkah 5: PRIORITY — seberapa urgent?
Langkah 6: FIX — paling safe, paling reversible
Langkah 7: VERIFY — pastikan fix berhasil
Langkah 8: DOCUMENT — catat di LIVING_LOG supaya tidak lupa
```

**Prinsip terpenting:**
> "Sebuah warning bukan berarti sistem rusak.
> Sebuah proses yang jalan tidak berarti tidak ada masalah.
> Baca dengan teliti — context adalah segalanya."
