# Membaca Output Server — Diagnosis dari Terminal

## Prinsip: Setiap baris output adalah data

Output terminal bukan sekadar teks — setiap baris mengandung sinyal.
Kemampuan membaca output server adalah skill inti seorang developer/AI agent.

---

## Contoh Nyata: Restart brain_qa di SIDIX VPS

```
INFO:     Started server process [956340]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
ERROR:    [Errno 98] error while attempting to bind on address ('0.0.0.0', 8765): address already in use
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
SIDIX Inference Engine starting at http://0.0.0.0:8765
[2] 957055
[2]+  Exit 1    nohup python3 -m brain_qa serve > /tmp/brain_qa.log 2>&1
{"status":"ok","engine":"SIDIX Inference Engine v0.1",...,"corpus_doc_count":523}
```

### Analisis baris per baris:

| Baris | Makna |
|---|---|
| `Started server process [956340]` | Log dari proses LAMA (masih jalan di PID 956340) |
| `[Errno 98] address already in use` | Proses BARU (957055) gagal bind port 8765 |
| `[2]+ Exit 1` | Proses baru keluar dengan error |
| `{"status":"ok",...}` | Curl ke /health BERHASIL — proses lama masih hidup! |

**Kesimpulan yang benar:** brain_qa TIDAK mati. Proses lama (956340) masih sehat.
Exit 1 dari proses baru bukan masalah — malah konfirmasi proses lama berjalan.

### Kesimpulan yang SALAH (kalau hanya baca sebagian):
```
[2]+ Exit 1 → "backend mati!" → PANIK → restart paksa → justru kill proses yang masih hidup
```

---

## Pola-Pola Output yang Perlu Dikenali

### 1. "Address already in use"
```
[Errno 98] error while attempting to bind on address ... address already in use
```
**Artinya:** port sudah dipakai proses lain
**Bukan berarti:** gagal, perlu restart
**Cek:** `ss -tlnp | grep 8765` → lihat siapa yang pakai port itu

### 2. "Exit 0" vs "Exit 1"
```
[1]  Done      perintah...   ← Exit 0: sukses
[2]+ Exit 1    perintah...   ← Exit 1: gagal (tapi cek konteksnya!)
```
Exit 1 pada proses background = perintah gagal, tapi mungkin tidak fatal
(seperti di atas — brain_qa gagal start BARU karena yang lama sudah jalan)

### 3. Perubahan ukuran bundle Vite
```
dist/assets/index-DUGyZbU3.js   44.55 kB  ← sebelum supabase
dist/assets/index-va_HHtKt.js  247.05 kB  ← sesudah supabase-js ditambah
```
Kenaikan ~200kB = library baru ter-include dalam build ✅

### 4. corpus_doc_count naik
```
"corpus_doc_count":520  ← sebelum research notes baru
"corpus_doc_count":523  ← sesudah 3 research notes ditambah + re-index
```
Artinya SIDIX sudah membaca dan mengindeks dokumen baru ✅

### 5. Health check pattern
```bash
curl http://localhost:8765/health
```
Response `{"status":"ok",...}` = backend sehat
Response `curl: (7) Failed to connect` = backend mati, perlu restart

---

## Checklist Verifikasi Deployment

Setelah setiap deploy, verifikasi urutan ini:

```bash
# 1. Frontend serving?
curl -I http://localhost:4000
# Expect: HTTP/1.1 200 OK

# 2. Backend healthy?
curl http://localhost:8765/health
# Expect: {"status":"ok",...}

# 3. Corpus ter-index?
curl http://localhost:8765/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Corpus: {d[\"corpus_doc_count\"]} docs')"
# Expect: angka naik dari sebelumnya

# 4. Env vars ter-bake di Vite build?
grep -o "NAMA_PROJECT_SUPABASE" dist/assets/*.js
# Expect: nama project muncul

# 5. Nginx proxy bisa dicapai dari luar?
curl -I https://app.sidixlab.com
# Expect: HTTP/2 200
```

---

## Kenapa Ini Penting untuk SIDIX

SIDIX yang cerdas harus bisa:
1. **Membaca log** yang diberikan user dan memberikan diagnosis
2. **Membedakan** error fatal vs warning vs false alarm
3. **Menyimpulkan** dari partial output (tidak selalu dapat log lengkap)
4. **Memberikan fix** yang tepat, bukan overkill

Ini adalah kemampuan **operational reasoning** — memahami sistem yang berjalan,
bukan hanya teori tentang sistem.
