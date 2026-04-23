#!/usr/bin/env python3
"""Deploy Sprint 7b changes to VPS: git pull, landing sync, restart, health check."""

import paramiko
import sys
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '72.62.125.6'
USER = 'root'
PASS = 'gY2UkMePh,Zvt5)5'

STEPS = [
    ('Git stash', 'cd /opt/sidix && git stash 2>&1 || true'),
    ('Git pull', 'cd /opt/sidix && git pull origin main 2>&1 | tail -20'),
    ('Stash drop', 'cd /opt/sidix && git stash drop 2>&1 || true'),
    ('Landing sync', 'rsync -a --delete /opt/sidix/SIDIX_LANDING/ /www/wwwroot/sidixlab.com/ && echo LANDING_SYNCED'),
    ('Brain restart', 'pm2 restart sidix-brain 2>&1 | tail -5'),
    ('PM2 save', 'pm2 save 2>&1 | tail -3'),
    ('Health', 'curl -sf http://localhost:8765/health && echo "" || echo HEALTH_FAIL'),
    ('Git log', 'cd /opt/sidix && git log --oneline -3'),
]

def run(client, label, cmd, timeout=60):
    print(f'\n=== {label} ===')
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = out or err or '(no output)'
    print(result[:800])
    return result

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f'Connecting to {HOST}...')
client.connect(HOST, username=USER, password=PASS, timeout=20)
print('Connected.\n')

for label, cmd in STEPS:
    run(client, label, cmd)
    time.sleep(1)

client.close()
print('\n=== DEPLOY COMPLETE ===')
