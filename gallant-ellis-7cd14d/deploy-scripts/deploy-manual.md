# Manual Deploy SIDIX 2.0 ke VPS

> Karena SSH dari Windows development machine timeout, deploy harus dijalankan langsung di VPS.

## Langkah Cepat (5 menit)

Login ke VPS:
```bash
ssh root@72.62.125.6
```

Di VPS, jalankan:
```bash
cd ~/sidix
git pull origin main
bash deploy-scripts/deploy.sh
```

## Verifikasi Deploy

```bash
pm2 status
pm2 logs sidix-backend --lines 20
```

## Health Check

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/agent/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Halo SIDIX", "persona": "UTZ"}'
```

## Rollback (kalau ada masalah)

```bash
cd ~/sidix
git log --oneline -5
git reset --hard HEAD~1  # rollback 1 commit
bash deploy-scripts/deploy.sh
```

## Setup Auto-Deploy (GitHub Actions)

Tambahkan file `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: 72.62.125.6
          username: root
          password: ${{ secrets.VPS_PASSWORD }}
          script: |
            cd ~/sidix
            git pull origin main
            bash deploy-scripts/deploy.sh
```

Tambahkan secret `VPS_PASSWORD` di GitHub repository settings.
