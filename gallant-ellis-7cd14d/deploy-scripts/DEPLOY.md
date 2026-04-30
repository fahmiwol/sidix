# 📦 Panduan Deploy SIDIX (VPS) — Metode PM2

Panduan ini menjelaskan cara menggunakan **Deploy Kit** untuk mengelola layanan SIDIX di VPS menggunakan PM2.

## 🚀 Persiapan Awal
1. Pastikan Anda sudah login ke VPS.
2. Clone repo SIDIX ke `~/sidix` jika belum ada.
3. Install PM2: `npm install -g pm2`.

## 🛠️ Cara Pakai Deploy Kit

### 1. Masuk ke direktori repo
```bash
cd ~/sidix
```

### 2. Beri izin eksekusi pada script
```bash
chmod +x deploy-scripts/*.sh
```

### 3. Jalankan Deploy Utama
Script ini akan melakukan pull, backup, install dependencies, dan restart semua layanan.
```bash
bash deploy-scripts/deploy.sh
```

---

## 📊 Manajemen Layanan (PM2)

| Perintah | Deskripsi |
|----------|-----------|
| `pm2 status` | Lihat status semua layanan SIDIX |
| `pm2 logs sidix-backend` | Lihat log real-time backend |
| `pm2 restart sidix-backend` | Restart hanya backend |
| `bash deploy-scripts/restart.sh` | Restart CEPAT semua layanan |

## 🔐 Aktifkan MCP (Default OFF)
Jika Anda ingin mengaktifkan layanan MCP:
```bash
pm2 start ecosystem.config.js --only sidix-mcp
```

## 🔍 Health Monitoring
Layanan `sidix-health` berjalan setiap 15 menit untuk memantau resource VPS dan kesehatan backend. Log dapat dilihat di `~/sidix_health.log`.
