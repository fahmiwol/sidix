# 203 — Self-Healing Recovery Monitor untuk SIDIX

**Tanggal:** 2026-04-24
**Agen:** Claude (Kimi Code CLI)
**Commit:** `a5fc9eb`

---

## Apa

`scripts/self_heal.py` — monitor kesehatan SIDIX yang bisa jalan otomatis (cron/systemd timer) dan melakukan recovery action kalau terdeteksi masalah.

Fitur:
1. Ping `/health` endpoint
2. Cek proses PM2 (`sidix-brain`, `sidix-ui`)
3. Auto-restart kalau service down
4. Cek disk space (warning >90%)
5. Log semua action ke `logs/self_heal.log`

Plus `scripts/deploy_latest.py` untuk auto-deploy via SSH: git pull → pip install → pm2 restart → health verify.

## Mengapa

Requirement user eksplisit: **self healing recovery**. SIDIX harus bisa "sembuh sendiri" tanpa intervensi manusia 24/7. VPS bisa crash, OOM, disk penuh, atau proses mati — semua harus ditangani otomatis.

## Bagaimana

### Self-Heal Architecture
```
[Cron every 5 min]
    → ping /health
    → cek PM2 jlist
    → cek disk usage
    → kalau fail → restart service → log
```

### Deploy Script Architecture
```
[Local machine]
    → SSH ke VPS (paramiko)
    → git pull origin main
    → pip install -r requirements.txt
    → pm2 restart sidix-brain sidix-ui
    → pm2 save
    → curl /health (verify)
```

Config via env var:
- `SIDIX_VPS_HOST`, `SIDIX_VPS_USER`, `SIDIX_VPS_PASS`
- `SIDIX_HEALTH_URL` (default: http://localhost:8765)
- `SIDIX_SELFHEAL_LOG`

## Contoh Nyata

Setup cron di VPS:
```bash
crontab -e
*/5 * * * * cd /opt/sidix && python scripts/self_heal.py >> /var/log/sidix_heal.log 2>&1
```

Deploy dari lokal:
```bash
export SIDIX_VPS_HOST=203.0.113.1
export SIDIX_VPS_PASS=secret
python scripts/deploy_latest.py
```

## Keterbatasan
- Self-heal hanya handle restart + disk check. Belum handle: OOM killer, corrupt DB, network partition.
- Deploy script butuh password SSH (bukan key-based). Next: support SSH key auth.
- Belum ada notifikasi external (email/Telegram/Discord) kalau self-heal gagal.

## Next Steps
- Integrasi notifikasi (Telegram bot / webhook Discord) kalai self-heal trigger
- Health check lebih granular: cek model load time, cek corpus integrity, cek DB connectivity
- Circuit breaker: kalau restart 3x gagal, stop retry dan alert human
