# SIDIX Cron Setup (VPS)

Copy-paste ke VPS untuk setup self-healing + flywheel automation.

## 1. Self-Healing Monitor (setiap 5 menit)

```bash
# Edit crontab
crontab -e

# Tambah baris:
*/5 * * * * cd /opt/sidix && python scripts/self_heal.py >> /var/log/sidix_heal.log 2>&1
```

Verifikasi:
```bash
tail -f /var/log/sidix_heal.log
```

## 2. Auto-Training Flywheel (setiap hari jam 3 pagi)

```bash
# Edit crontab
crontab -e

# Tambah baris:
0 3 * * * cd /opt/sidix && export FLYWHEEL_MIN_PAIRS=500 && export FLYWHEEL_TRAIN_MODE=mock && python scripts/auto_train_flywheel.py >> /var/log/sidix_flywheel.log 2>&1
```

Verifikasi:
```bash
tail -f /var/log/sidix_flywheel.log
```

## 3. Memory DB Backup (setiap hari jam 2 pagi)

```bash
# Edit crontab
crontab -e

# Tambah baris:
0 2 * * * cp /opt/sidix/apps/brain_qa/.data/sidix_memory.db /opt/sidix/backups/sidix_memory_$(date +\%Y\%m\%d).db
```

## 4. Deploy Manual (kalau auto-deploy gagal)

```bash
export SIDIX_VPS_HOST=<IP_VPS>
export SIDIX_VPS_PASS=<PASSWORD>
python scripts/deploy_latest.py
```

## 5. Ollama Model Reload (setelah flywheel deploy)

```bash
ollama create sidix-distilled -f scripts/distillation/sidix_modelfile.txt
ollama run sidix-distilled
```
