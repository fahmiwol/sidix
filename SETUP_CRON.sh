#!/bin/bash
# SETUP_CRON.sh — Setup cron OTAK+ self-critique + daily growth
# Bos tinggal: ssh root@72.62.125.6, paste ini, enter

echo "=== Setup SIDIX Background Cron ==="

# Backup cron existing
crontab -l > /tmp/cron_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Write new cron
cat << 'EOF' | crontab -
# SIDIX Background Growth Loop
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 02:00 — Learn Agent (fetch external knowledge)
0 2 * * * cd /opt/sidix/apps/brain_qa && python3 -u brain_qa/learn_agent.py >> /var/log/sidix_learn.log 2>&1

# 03:00 — OTAK+ Self-Critique (evaluate yesterday's outputs)
0 3 * * * cd /opt/sidix/apps/brain_qa && python3 -u brain_qa/daily_self_critique.py >> /var/log/sidix_critique.log 2>&1

# 04:00 — Daily Growth (7-phase compound learning)
0 4 * * * cd /opt/sidix/apps/brain_qa && python3 -u brain_qa/daily_growth.py >> /var/log/sidix_growth.log 2>&1

# 04:30 — Process Queue (index new corpus)
30 4 * * * cd /opt/sidix/apps/brain_qa && python3 -u -m brain_qa process_queue >> /var/log/sidix_queue.log 2>&1

# 14:00 — Learn Agent afternoon run
0 14 * * * cd /opt/sidix/apps/brain_qa && python3 -u brain_qa/learn_agent.py >> /var/log/sidix_learn.log 2>&1

# 22:00 — Daily Synthesis (synthesize today into 1 paragraph state)
0 22 * * * cd /opt/sidix && bash scripts/daily_synthesis.sh >> /var/log/sidix_synthesis.log 2>&1
EOF

echo "Cron installed. Current crontab:"
crontab -l

echo ""
echo "=== Setup logrotate untuk log SIDIX ==="
cat << 'EOF' > /etc/logrotate.d/sidix
/var/log/sidix_*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

echo "Logrotate configured."
echo ""
echo "=== SELESAI ==="
echo "SIDIX sekarang tumbuh sendiri di background:"
echo "  02:00 — Learn Agent"
echo "  03:00 — OTAK+ Self-Critique (BARU)"
echo "  04:00 — Daily Growth"
echo "  04:30 — Process Queue"
echo "  14:00 — Learn Agent (afternoon)"
echo "  22:00 — Daily Synthesis"
