# Deploy SIDIX ke VPS (24/7 Online)

Panduan deploy SIDIX ke VPS murah (Hetzner €4/bulan atau DigitalOcean $6/bulan).

**Estimasi waktu**: 30-60 menit

---

## Prasyarat

- VPS Ubuntu 22.04 LTS (min 2 vCPU, 4GB RAM)
- Domain (opsional, tapi dianjurkan untuk SSL)
- Git, Docker, Docker Compose terinstall di VPS

---

## 1. Pilih VPS

| Provider | Spec | Harga | Link |
|---|---|---|---|
| **Hetzner** (recommended) | 2 vCPU, 4GB RAM, 40GB | €4.15/bulan | hetzner.com |
| **DigitalOcean** | 1 vCPU, 2GB RAM, 50GB | $6/bulan | digitalocean.com |
| **Fly.io** | shared, 256MB–1GB | Free tier ada | fly.io |
| **Railway** | managed, auto-scale | ~$5/bulan | railway.app |

Untuk SIDIX **mock mode** (tanpa GPU): 2GB RAM cukup.  
Untuk **full inference** (Qwen2.5-7B): butuh 16GB RAM atau GPU.

---

## 2. Setup VPS

```bash
# SSH ke VPS
ssh root@YOUR_VPS_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Install Docker Compose
apt install docker-compose-plugin -y

# Buat user non-root (good practice)
adduser sidix
usermod -aG docker sidix
su - sidix
```

---

## 3. Clone repo & konfigurasi

```bash
# Clone repo SIDIX
git clone https://github.com/fahmiwol/sidix.git
cd sidix

# Setup environment
cp .env.sample .env
nano .env   # isi DOMAIN, BRAIN_QA_ADMIN_TOKEN, dll.
```

Edit `.env`:
```env
DOMAIN=your-domain.com
VITE_BRAIN_QA_URL=https://your-domain.com/api
SIDIX_USE_MOCK_LLM=1           # 1 = mock (tanpa GPU), 0 = full model
BRAIN_QA_ADMIN_TOKEN=secret-token-kamu
BRAIN_QA_RATE_LIMIT_RPM=30
```

Edit `Caddyfile`:
```
# Ganti your-domain.com dengan domain kamu
your-domain.com {
    ...
}
```

---

## 4. Build & jalankan

```bash
# Build semua image (~5-10 menit pertama kali)
docker compose build

# Jalankan semua service
docker compose up -d

# Cek status
docker compose ps

# Lihat log
docker compose logs -f brain_qa
```

---

## 5. Verifikasi

```bash
# Health check backend
curl https://your-domain.com/api/health

# Atau kalau belum ada domain:
curl http://YOUR_VPS_IP:8765/health
```

Respons yang benar:
```json
{
  "status": "ok",
  "model_ready": false,
  "index_ready": true,
  "personas": ["MIGHAN", "TOARD", "FACH", "HAYFAR", "INAN"]
}
```

---

## 6. Update SIDIX

```bash
# Pull kode terbaru
git pull origin main

# Rebuild & restart
docker compose build brain_qa
docker compose up -d brain_qa

# Reindex BM25 jika ada research notes baru
docker compose exec brain_qa python -m brain_qa index
```

---

## 7. Monitoring & maintenance

```bash
# Cek resource usage
docker stats

# Backup data
docker compose exec brain_qa python -m brain_qa backup

# Lihat log error
docker compose logs --tail=100 brain_qa | grep ERROR
```

---

## Estimasi biaya

| Item | Biaya |
|---|---|
| Hetzner CX22 VPS | €4.15/bulan |
| Domain (.com) | ~$12/tahun |
| SSL (Let's Encrypt via Caddy) | Gratis |
| **Total** | **~€5.50/bulan** |

---

## Troubleshooting

**Port 8765 tidak bisa diakses:**
```bash
ufw allow 8765   # atau 80/443 kalau pakai Caddy
```

**BM25 index kosong:**
```bash
docker compose exec brain_qa python -m brain_qa index
```

**Out of memory:**
- Tambah swap: `fallocate -l 2G /swapfile && mkswap /swapfile && swapon /swapfile`
- Atau upgrade ke 4GB RAM plan

**Docker disk penuh:**
```bash
docker system prune -f
```
