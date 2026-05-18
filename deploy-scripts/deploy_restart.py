#!/usr/bin/env python3
"""Restart SIDIX backend + frontend after git pull."""
import paramiko
import time

HOST = "187.77.116.139"
USER = "root"
KEY_PATH = r"C:\Users\ASUS\.ssh\hostinger_migration"
NVM_PATH = "export PATH=\"/root/.nvm/versions/node/v20.20.2/bin:$PATH\""

def run_cmd(client, label, cmd, timeout=60):
    print(f"\n>>> {label}...")
    full_cmd = f"{NVM_PATH} && {cmd}"
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out[:800] if len(out) > 800 else out)
    if err and "warning" not in err.lower():
        print(f"ERR: {err[:300]}")
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=HOST, username=USER, key_filename=KEY_PATH, timeout=15)

    # 1. Restart backend
    run_cmd(client, "Restart sidix-brain", "cd /opt/sidix && pm2 restart sidix-brain --update-env")
    time.sleep(5)

    # 2. Health check
    run_cmd(client, "Health check", "curl -s http://localhost:8765/health | python3 -m json.tool 2>/dev/null")

    # 3. Build frontend
    run_cmd(client, "Build frontend", "cd /opt/sidix/SIDIX_USER_UI && npm run build 2>&1 | tail -10")

    # 4. Restart UI
    run_cmd(client, "Restart sidix-ui", "cd /opt/sidix && pm2 restart sidix-ui --update-env")

    # 5. PM2 status
    run_cmd(client, "PM2 status", "pm2 status")

    # 6. Smoke MCP
    run_cmd(client, "Smoke MCP", "curl -s -X POST http://localhost:8765/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}' | python3 -m json.tool 2>/dev/null")

    # 7. Smoke AgentCard
    run_cmd(client, "Smoke AgentCard", "curl -s http://localhost:8765/.well-known/agent-card.json | python3 -m json.tool 2>/dev/null")

    # 8. Smoke mode instant
    run_cmd(client, "Smoke Instant mode", "curl -s -X POST http://localhost:8765/agent/chat_holistic -H 'Content-Type: application/json' -d '{\"question\":\"halo\",\"mode\":\"instant\"}' | python3 -m json.tool 2>/dev/null")

    client.close()
    print("\n[DEPLOY] Complete!")

if __name__ == "__main__":
    main()
