#!/usr/bin/env python3
"""Deploy SIDIX to VPS via Paramiko SSH."""
import paramiko
import time

HOST = "187.77.116.139"
USER = "root"
KEY_PATH = r"C:\Users\ASUS\.ssh\hostinger_migration"
REPO_DIR = "/opt/sidix"
BRANCH = "work/gallant-ellis-7cd14d"

def run_cmd(client, label, cmd, timeout=60):
    print(f"\n>>> {label}...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
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

    # Step 0: Debug env
    run_cmd(client, "ENV", "echo $PATH; which node 2>/dev/null; which npm 2>/dev/null; which pm2 2>/dev/null; which git; whoami")
    run_cmd(client, "NVM check", "source ~/.nvm/nvm.sh 2>/dev/null && nvm list 2>/dev/null && which node && which npm && which pm2 || echo 'nvm not found'")

    # Step 1: Git pull via HTTPS (bypass SSH key issue)
    run_cmd(client, "Git config", f"git config --global --add safe.directory {REPO_DIR} 2>/dev/null; cd {REPO_DIR} && git remote set-url origin https://github.com/fahmiwol/sidix.git 2>/dev/null; git fetch origin {BRANCH} && git reset --hard origin/{BRANCH}")

    # Step 2: Restart backend (find pm2 path)
    run_cmd(client, "Restart brain", f"cd {REPO_DIR} && export PATH=\"$HOME/.nvm/versions/node/v20.18.0/bin:$PATH\" && which pm2 && pm2 restart sidix-brain --update-env || pm2 restart sidix-brain --update-env")

    # Step 3: Health check
    run_cmd(client, "Health check", "curl -s http://localhost:8765/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8765/health")

    # Step 4: Build frontend
    run_cmd(client, "Build frontend", f"cd {REPO_DIR}/SIDIX_USER_UI && export PATH=\"$HOME/.nvm/versions/node/v20.18.0/bin:$PATH\" && npm run build 2>&1 | tail -10")

    # Step 5: Restart UI
    run_cmd(client, "Restart UI", f"cd {REPO_DIR} && export PATH=\"$HOME/.nvm/versions/node/v20.18.0/bin:$PATH\" && pm2 restart sidix-ui --update-env")

    # Step 6: PM2 status
    run_cmd(client, "PM2 status", "export PATH=\"$HOME/.nvm/versions/node/v20.18.0/bin:$PATH\" && pm2 status")

    # Step 7: Smoke test MCP
    run_cmd(client, "Smoke MCP", "curl -s -X POST http://localhost:8765/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}' | python3 -m json.tool 2>/dev/null || echo 'MCP test failed'")

    # Step 8: Smoke test AgentCard
    run_cmd(client, "Smoke AgentCard", "curl -s http://localhost:8765/.well-known/agent-card.json | python3 -m json.tool 2>/dev/null || echo 'AgentCard test failed'")

    client.close()
    print("\n[DEPLOY] Done!")

if __name__ == "__main__":
    main()
