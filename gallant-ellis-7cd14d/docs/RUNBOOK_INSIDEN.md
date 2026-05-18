# Runbook Insiden SIDIX

> Task 43 — An-Nazi'at (G5) | Dokumen ini satu halaman — cetak dan pasang di tempat mudah dijangkau.

---

## Severity Level

| Level | Deskripsi | Contoh | Target Respons |
|-------|-----------|--------|----------------|
| **P0** | Down total — layanan tidak dapat diakses sama sekali | Server crash, `/health` timeout | Segera (< 5 menit) |
| **P1** | Degraded — layanan hidup tapi kualitas sangat menurun | Semua jawaban error, latency > 60 detik | < 15 menit |
| **P2** | Parsial — sebagian fitur tidak berfungsi | Reindex gagal, satu endpoint error | < 1 jam |
| **P3** | Minor — masalah kecil, tidak mempengaruhi pengguna | Log spam, warning di console | < 24 jam |

---

## Kontak On-Call

| Peran | Nama / Channel |
|-------|----------------|
| Engineer on-call | [isi nama / nomor HP] |
| Channel insiden | [isi nama channel Slack/WhatsApp/dll.] |
| Eskalasi teknis | [isi nama senior engineer] |
| Eskalasi bisnis | [isi nama PIC] |

---

## Cek Cepat (< 2 Menit)

Jalankan tiga perintah ini secara berurutan untuk diagnosis awal:

```bash
# 1. Cek status server
curl http://localhost:8765/health

# 2. Cek disk penuh
python scripts/disk_alarm.py

# 3. Cek endpoint hidup via synthetic monitor
python scripts/synthetic_monitor.py --once
```

Interpretasi:
- `/health` timeout atau connection refused → **P0**, lanjut ke triage P0
- `/health` `status: "degraded"` → **P1**, cek log dan model_ready
- Disk alarm berbunyi → segera bersihkan log lama atau tambah kapasitas
- Synthetic monitor gagal tapi `/health` ok → **P2**, cek endpoint spesifik

---

## Langkah Triage P0

Ikuti urutan ini sampai layanan pulih:

1. **Restart proses**
   ```bash
   # Identifikasi PID proses brain_qa
   # Kemudian:
   python -m brain_qa serve
   ```

2. **Cek log error**
   ```
   Lihat output terminal server atau file log uvicorn.
   Cari: "Error", "Exception", "Traceback", "OOM", "CUDA out of memory"
   ```

3. **Blue-green switch** — jika instance aktif tidak bisa dipulihkan:
   ```bash
   curl -X POST http://localhost:8765/agent/bluegreen/switch \
     -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN"
   ```

4. **Rollback ke backup** — jika switch tidak cukup (data korup):
   - Stop server
   - Restore `.data/` dari backup terbaru (lihat `OPERATOR_RESTORE_BACKUP.md`)
   - Restart server
   - Verifikasi `/health`

---

## Template Komunikasi Insiden

Gunakan template ini saat memberi update ke stakeholder:

```
[INSIDEN P0/P1] SIDIX — <ringkasan singkat masalah>
Waktu mulai  : YYYY-MM-DD HH:MM WIB
Status saat ini : [Investigasi / Ditangani / Pulih]
Dampak       : <siapa yang terdampak dan apa yang tidak bisa dilakukan>
Langkah aktif : <apa yang sedang dikerjakan sekarang>
Update berikut : <estimasi waktu update selanjutnya>
PIC          : <nama>
```

---

## Post-Mortem

- **P0 dan P1**: wajib post-mortem dalam **48 jam** setelah insiden selesai.
- Format post-mortem: timeline kejadian, root cause, dampak, tindakan korektif, dan timeline implementasi perbaikan.
- Simpan di `docs/postmortems/YYYY-MM-DD-<slug>.md`.
- P2 dan P3: cukup catatan singkat di `LIVING_LOG.md`.

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
