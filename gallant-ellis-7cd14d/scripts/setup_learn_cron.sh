#!/bin/bash
# setup_learn_cron.sh — Tambah cron harian untuk SIDIX LearnAgent

ENV_FILE="/opt/sidix/apps/brain_qa/.env"
ADMIN_TOKEN=$(grep BRAIN_QA_ADMIN_TOKEN "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d '\r')

if [ -z "$ADMIN_TOKEN" ]; then
    echo "ERROR: BRAIN_QA_ADMIN_TOKEN tidak ditemukan di $ENV_FILE"
    exit 1
fi

# Hapus cron lama kalau ada
crontab -l 2>/dev/null | grep -v "LearnAgent" | grep -v "learn/run" | grep -v "learn/process_queue" > /tmp/crontab_clean.txt

# Tambah cron baru
cat >> /tmp/crontab_clean.txt << EOF

# SIDIX LearnAgent - daily fetch all sources (04:00 UTC = 11:00 WIB)
0 4 * * * curl -s -X POST -H "Authorization: Bearer ${ADMIN_TOKEN}" -H "Content-Type: application/json" -d '{"domain":"all"}' http://localhost:8765/learn/run >> /var/log/sidix_learn.log 2>&1

# SIDIX LearnAgent - process corpus queue (04:30 UTC)
30 4 * * * curl -s -X POST -H "Authorization: Bearer ${ADMIN_TOKEN}" http://localhost:8765/learn/process_queue >> /var/log/sidix_learn.log 2>&1
EOF

# Install crontab
crontab /tmp/crontab_clean.txt && echo "✅ Cron LearnAgent berhasil dipasang" && echo "" && echo "Crontab aktif:" && crontab -l | grep -A1 "LearnAgent"
