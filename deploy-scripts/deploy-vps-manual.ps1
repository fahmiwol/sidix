# SIDIX VPS Manual Deploy Script (PowerShell)
# Run this on your local machine with SSH access to VPS
# Usage: .\deploy-vps-manual.ps1

$VPS_IP = "187.77.116.139"
$VPS_USER = "root"
$SSH_KEY = "$env:USERPROFILE\.ssh\hostinger_migration"
$REPO_DIR = "/opt/sidix"
$BRANCH = "work/gallant-ellis-7cd14d"

function Invoke-RemoteCommand {
    param([string]$Cmd)
    $fullCmd = "ssh -i `"$SSH_KEY`" -o ConnectTimeout=10 -o UserKnownHostsFile=NUL ${VPS_USER}@${VPS_IP} `"$Cmd`""
    Write-Host "> $Cmd" -ForegroundColor DarkGray
    Invoke-Expression $fullCmd
}

Write-Host "🚀 SIDIX VPS Deploy — Branch: $BRANCH" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════"

# 1. Git pull
Write-Host "`n[1/5] Git fetch + reset to $BRANCH..." -ForegroundColor Yellow
Invoke-RemoteCommand "git config --global --add safe.directory $REPO_DIR 2>/dev/null; cd $REPO_DIR && git fetch origin $BRANCH && git reset --hard origin/$BRANCH"

# 2. Backend restart
Write-Host "`n[2/5] Restart SIDIX Brain (pm2)..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd $REPO_DIR && pm2 restart sidix-brain --update-env && sleep 2 && pm2 status sidix-brain"

# 3. Health check
Write-Host "`n[3/5] Health check..." -ForegroundColor Yellow
Invoke-RemoteCommand "curl -s http://localhost:8765/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8765/health"

# 4. Frontend build
Write-Host "`n[4/5] Build frontend..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd $REPO_DIR/SIDIX_USER_UI && npm run build 2>&1 | tail -5"

# 5. Frontend restart
Write-Host "`n[5/5] Restart SIDIX UI (pm2)..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd $REPO_DIR && pm2 restart sidix-ui --update-env && sleep 1 && pm2 status sidix-ui"

Write-Host "`n✅ Deploy complete!" -ForegroundColor Green
Write-Host "   App:  https://app.sidixlab.com"
Write-Host "   API:  https://ctrl.sidixlab.com"
Write-Host "   MCP:  https://ctrl.sidixlab.com/mcp"
