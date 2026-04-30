# Disaster Recovery SIDIX

> Task 48 — Al-Humazah (G5)

Dokumen ini menjelaskan prosedur pemulihan dari kegagalan besar (data loss, hardware failure, server crash) pada sistem SIDIX Brain QA.

---

## Aset Kritis

| Aset | Lokasi | Keterangan |
|------|--------|------------|
| **Corpus chunks & index** | `apps/brain_qa/.data/` | Hasil reindex BM25 — dapat di-rebuild dari sumber, tapi butuh waktu |
| **LoRA adapter weights** | `adapters/` | Bobot model yang telah ditraining — **tidak dapat di-rebuild tanpa training ulang** |
| **Dokumen sumber** | `brain/public/` | Markdown sumber corpus — backup paling penting |
| **Log token usage** | `apps/brain_qa/.data/token_usage.jsonl` | Monitoring & audit |
| **Log sistem** | Output uvicorn / file log | Untuk investigasi insiden |

---

## Backup Rutin

Jalankan backup harian menggunakan perintah berikut:

```bash
python -m brain_qa backup --dest .backups/backup_$(date +%Y%m%d_%H%M%S)
```

### Jadwal via Cron (Linux)

```cron
# Backup harian pukul 02:00 pagi
0 2 * * * cd /path/to/sidix && python -m brain_qa backup --dest .backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S)
```

### Jadwal via Task Scheduler (Windows)

Buat scheduled task yang menjalankan:
```
python -m brain_qa backup --dest .backups\backup_%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
```

### Verifikasi Backup (Dry Run)

```bash
python -m brain_qa backup --dry-run
```

Perintah ini menampilkan daftar file yang akan di-backup tanpa benar-benar menyalin.

---

## RTO / RPO

| Metrik | Target | Keterangan |
|--------|--------|------------|
| **RTO** (Recovery Time Objective) | < 30 menit | Waktu maksimal dari insiden hingga layanan pulih |
| **RPO** (Recovery Point Objective) | Terakhir kali backup berhasil | Data yang hilang = data sejak backup terakhir |

> Untuk memperkecil RPO: jalankan backup lebih sering (setiap jam jika kritikal).

---

## Langkah Recovery Step-by-Step

### Persiapan

Sebelum memulai recovery, identifikasi:
- Backup terbaru yang valid di `.backups/`
- Apakah adapter LoRA perlu di-restore atau cukup `.data/`

---

### Langkah 1: Hentikan Server SIDIX

```bash
# Temukan PID proses dan hentikan
# Atau jika menggunakan systemd:
systemctl stop sidix-brain-qa

# Atau jika proses langsung:
# Ctrl+C di terminal, atau kill <PID>
```

Pastikan tidak ada proses yang menulis ke `.data/` saat restore berlangsung.

---

### Langkah 2: Identifikasi Backup Terbaru

```bash
ls -lt .backups/
```

Pilih direktori dengan timestamp terbaru, misalnya: `.backups/backup_20260417_020001/`

```bash
python -m brain_qa backup --dry-run
```

---

### Langkah 3: Restore `.data/`

**Linux/macOS:**

```bash
BACKUP_DIR=".backups/backup_20260417_020001"
cp -r "$BACKUP_DIR/.data/" apps/brain_qa/.data/
```

**Windows PowerShell:**

```powershell
$backupDir = ".backups\backup_20260417_020001"
Copy-Item -Recurse -Force "$backupDir\.data\*" "apps\brain_qa\.data\"
```

---

### Langkah 4: Restore `adapters/` (jika perlu)

Jika adapter LoRA juga hilang atau korup:

**Linux/macOS:**

```bash
cp -r "$BACKUP_DIR/adapters/" adapters/
```

**Windows PowerShell:**

```powershell
Copy-Item -Recurse -Force "$backupDir\adapters\*" "adapters\"
```

---

### Langkah 5: Verifikasi Chunk Count

```bash
python -m brain_qa index --check
```

Output yang diharapkan:

```
Index OK — doc_count=142, chunk_count=891
```

Jika output menunjukkan `chunk_count=0`, lakukan reindex dari sumber:

```bash
python -m brain_qa index --rebuild
```

---

### Langkah 6: Jalankan Server dan Test

```bash
python -m brain_qa serve
```

Tunggu beberapa detik, lalu verifikasi:

```bash
curl http://localhost:8765/health
```

Pastikan respons menunjukkan `corpus_doc_count > 0` dan `model_ready: true`.

---

### Langkah 7: Test Fungsional

```bash
curl -X POST http://localhost:8765/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Apa itu SIDIX?"}'
```

Jika mendapat jawaban yang valid, recovery selesai. Catat waktu recovery di `LIVING_LOG.md`.

---

## Recovery dari Backup Volume (Docker / NAS)

Jika backup disimpan di Docker volume atau NAS:

```bash
# Contoh mount volume Docker ke direktori lokal
docker run --rm \
  -v sidix_backup_volume:/backup \
  -v $(pwd)/.restorepoint:/target \
  alpine cp -r /backup/. /target/

# Kemudian jalankan langkah 3–7 di atas
```

Untuk NAS: mount share network terlebih dahulu, lalu salin file seperti langkah 3–4.

---

## Kontak Eskalasi

Jika recovery gagal setelah mengikuti semua langkah di atas:

| Situasi | Kontak |
|---------|--------|
| Adapter LoRA hilang dan tidak ada backup | [isi kontak ML engineer / trainer] |
| Data `.data/` korup dan semua backup rusak | [isi kontak infrastruktur] |
| Server fisik rusak | [isi kontak cloud provider / hosting] |
| Recovery > 30 menit (melewati RTO) | [isi kontak eskalasi manajemen] |

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
