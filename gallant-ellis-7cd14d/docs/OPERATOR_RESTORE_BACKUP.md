# Runbook Restore Backup Volume SIDIX

> Task 35 — Az-Zumar (G5)

Dokumen ini menjelaskan langkah-langkah restore backup SIDIX secara detail, termasuk verifikasi, restore dari cloud/NAS, dan rollback adapter LoRA.

---

## Inventaris Backup

Backup disimpan di direktori `.backups/` di root workspace dengan format penamaan timestamp:

```
.backups/
├── backup_20260415_020001/
│   ├── .data/          ← corpus chunks + BM25 index + token log
│   └── adapters/       ← LoRA adapter weights
├── backup_20260416_020001/
│   ├── .data/
│   └── adapters/
└── backup_20260417_020001/   ← backup terbaru
    ├── .data/
    └── adapters/
```

Format nama direktori: `backup_YYYYMMDD_HHMMSS` (UTC).

---

## Cek Backup Tersedia

Sebelum restore, verifikasi backup yang ada:

```bash
# Lihat daftar backup (urutkan terbaru dulu)
ls -lt .backups/

# Dry run — tampilkan apa yang akan di-restore tanpa eksekusi
python -m brain_qa backup --dry-run
```

Output dry run contoh:

```
[DRY RUN] Backup terbaru: .backups/backup_20260417_020001
  .data/chunks.pkl          (2.3 MB)
  .data/bm25_index.pkl      (1.1 MB)
  .data/token_usage.jsonl   (45 KB)
  adapters/adapter_model.safetensors  (418 MB)
  adapters/adapter_config.json        (1 KB)
Total: 421.5 MB
```

---

## Langkah Restore Step-by-Step

### Langkah 1: Hentikan SIDIX Server

Pastikan tidak ada proses yang sedang menulis ke `.data/` saat restore.

```bash
# Jika dijalankan langsung di terminal: tekan Ctrl+C
# Jika menggunakan systemd:
systemctl stop sidix-brain-qa

# Verifikasi tidak ada proses yang berjalan di port 8765:
curl http://localhost:8765/health
# Harus timeout atau "connection refused"
```

---

### Langkah 2: Identifikasi Backup Terbaru di `.backups/`

```bash
# Linux/macOS — urutkan terbaru dulu
ls -lt .backups/ | head -5

# Windows PowerShell
Get-ChildItem .backups | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

Catat nama direktori backup yang akan digunakan, misalnya: `backup_20260417_020001`

---

### Langkah 3: Salin `.data/` dari Backup ke Posisi Aktif

**Linux/macOS:**

```bash
BACKUP_DIR=".backups/backup_20260417_020001"

# Buat backup dari .data/ yang sekarang (opsional tapi aman)
cp -r apps/brain_qa/.data apps/brain_qa/.data_before_restore

# Salin dari backup
cp -r "$BACKUP_DIR/.data/." apps/brain_qa/.data/
```

**Windows PowerShell:**

```powershell
$backupDir = ".backups\backup_20260417_020001"

# Buat backup dari .data/ yang sekarang (opsional)
Copy-Item -Recurse "apps\brain_qa\.data" "apps\brain_qa\.data_before_restore"

# Salin dari backup
Copy-Item -Recurse -Force "$backupDir\.data\*" "apps\brain_qa\.data\"
```

---

### Langkah 4: Verifikasi Chunk Count

```bash
python -m brain_qa index --check
```

Output yang diharapkan:

```
Index OK — doc_count=142, chunk_count=891
```

Jika `chunk_count=0` atau perintah error, coba rebuild index dari sumber dokumen:

```bash
python -m brain_qa index --rebuild
```

Rebuild akan membaca ulang semua file dari `brain/public/` dan membangun ulang index BM25. Proses ini membutuhkan waktu beberapa menit tergantung jumlah dokumen.

---

### Langkah 5: Restart Server dan Verifikasi

```bash
python -m brain_qa serve
```

Setelah server berjalan (tunggu beberapa detik), cek health:

```bash
curl http://localhost:8765/health
```

Respons yang diharapkan:

```json
{
  "status": "ok",
  "model_ready": true,
  "model_mode": "local_lora",
  "corpus_doc_count": 142,
  "corpus_chunk_count": 891
}
```

**Pastikan `corpus_doc_count > 0`** sebelum menganggap restore berhasil.

---

## Restore dari Cloud / NAS

Jika backup disimpan di penyimpanan eksternal:

### 1. Mount volume / share

**NAS via SMB (Windows):**

```powershell
# Mount NAS share
net use Z: \\nas-server\sidix-backups /user:username password

# Salin backup ke lokal
Copy-Item -Recurse "Z:\backup_20260417_020001" ".backups\"

# Unmount setelah selesai
net use Z: /delete
```

**NAS via NFS (Linux):**

```bash
sudo mount -t nfs nas-server:/sidix-backups /mnt/nas-backup
cp -r /mnt/nas-backup/backup_20260417_020001 .backups/
sudo umount /mnt/nas-backup
```

**Docker volume:**

```bash
docker run --rm \
  -v sidix_backup_volume:/backup \
  -v $(pwd)/.backups:/target \
  alpine cp -r /backup/backup_20260417_020001 /target/
```

### 2. Lanjutkan dengan Langkah 1–5 di atas

Setelah backup ada di `.backups/` lokal, ikuti langkah restore seperti biasa.

---

## Rollback Adapter LoRA

Jika model baru (adapter terbaru) bermasalah dan ingin kembali ke versi sebelumnya:

### Opsi A: Ganti direktori adapter

```bash
# Arahkan ke versi adapter lama yang ada di backup
export BRAIN_QA_ADAPTER_DIR=".backups/backup_20260416_020001/adapters"

# Restart server
python -m brain_qa serve
```

### Opsi B: Salin adapter lama ke posisi aktif

```bash
BACKUP_DIR=".backups/backup_20260416_020001"

# Backup adapter saat ini
cp -r adapters adapters_problematic

# Restore adapter lama
cp -r "$BACKUP_DIR/adapters/." adapters/

# Restart server (BRAIN_QA_ADAPTER_DIR tetap default)
python -m brain_qa serve
```

**Windows PowerShell:**

```powershell
$backupDir = ".backups\backup_20260416_020001"

# Backup adapter bermasalah
Copy-Item -Recurse "adapters" "adapters_problematic"

# Restore adapter lama
Copy-Item -Recurse -Force "$backupDir\adapters\*" "adapters\"

# Restart server
python -m brain_qa serve
```

Verifikasi setelah rollback:

```bash
curl http://localhost:8765/health
# Pastikan model_ready: true dan model_mode sesuai
```

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
