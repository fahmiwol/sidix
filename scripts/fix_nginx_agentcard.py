#!/usr/bin/env python3
"""Fix nginx config to proxy /.well-known/agent-card.json to backend."""
import shutil

CONFIG_PATH = "/etc/nginx/sites-enabled/ctrl.sidixlab.com"
BACKUP_PATH = CONFIG_PATH + ".backup"

shutil.copy(CONFIG_PATH, BACKUP_PATH)

with open(CONFIG_PATH, "r") as f:
    content = f.read()

# Replace the generic /.well-known block with specific paths
old_block = "location /.well-known { allow all; root /www/wwwroot/ctrl.sidixlab.com; }"
new_block = """location /.well-known/acme-challenge { allow all; root /www/wwwroot/ctrl.sidixlab.com; }
    location /.well-known/agent-card.json {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
    }"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(CONFIG_PATH, "w") as f:
        f.write(content)
    print("nginx config updated successfully")
else:
    print("ERROR: old block not found in config")
    exit(1)
