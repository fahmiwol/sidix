# publish_to_github.ps1
# Script untuk inisialisasi Git + push pertama ke GitHub
#
# SEBELUM jalankan:
# 1. Buat repo di https://github.com/new (nama: sidix, public, tanpa README)
# 2. Jalankan script ini dari root repo: .\scripts\publish_to_github.ps1
# 3. Isi GITHUB_USERNAME di bawah

param(
    [string]$GitHubUsername = "",
    [string]$RepoName = "sidix",
    [string]$Branch = "main"
)

if (-not $GitHubUsername) {
    $GitHubUsername = Read-Host "GitHub username kamu"
}

$RepoUrl = "https://github.com/$GitHubUsername/$RepoName.git"
$RootDir = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  SIDIX — Publish ke GitHub" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Repo: $RepoUrl"
Write-Host "Dir : $RootDir"
Write-Host ""

Set-Location $RootDir

# ── Step 1: Cek prereqs ───────────────────────────────────────
Write-Host "[1/6] Cek prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git tidak ditemukan. Install dari https://git-scm.com" -ForegroundColor Red
    exit 1
}

# ── Step 2: Pastikan .env tidak ada di direktori ──────────────
Write-Host "[2/6] Safety check — cari file sensitif..." -ForegroundColor Yellow

$sensitiveFiles = @(".env", "*.safetensors")
$found = $false
foreach ($pattern in $sensitiveFiles) {
    $matches = Get-ChildItem -Recurse -Name $pattern -ErrorAction SilentlyContinue |
        Where-Object { $_ -notmatch "\.venv|node_modules|\.data" }
    if ($matches) {
        Write-Host "  WARN: Ditemukan file: $matches" -ForegroundColor Yellow
        $found = $true
    }
}
if ($found) {
    Write-Host "  Pastikan file sensitif sudah masuk .gitignore!" -ForegroundColor Yellow
}
Write-Host "  Safety check selesai." -ForegroundColor Green

# ── Step 3: Git init ─────────────────────────────────────────
Write-Host "[3/6] Git init..." -ForegroundColor Yellow

if (Test-Path ".git") {
    Write-Host "  Repo sudah ada, skip git init." -ForegroundColor Gray
} else {
    git init -b $Branch
    Write-Host "  Git init selesai." -ForegroundColor Green
}

# ── Step 4: Konfigurasi ──────────────────────────────────────
Write-Host "[4/6] Tambah remote origin..." -ForegroundColor Yellow

$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Host "  Remote origin sudah ada: $remoteExists" -ForegroundColor Gray
} else {
    git remote add origin $RepoUrl
    Write-Host "  Remote ditambahkan: $RepoUrl" -ForegroundColor Green
}

# ── Step 5: Commit pertama ───────────────────────────────────
Write-Host "[5/6] Stage & commit..." -ForegroundColor Yellow

git add .
$status = git status --short
$fileCount = ($status | Measure-Object).Count
Write-Host "  $fileCount file akan di-commit."

git commit -m @"
feat: initial commit — SIDIX v1.0

Self-hosted AI agent platform dengan:
- RAG (BM25) + ReAct agent loop
- Islamic Epistemology Engine (Maqashid + Sanad + Constitutional)
- User Intelligence (language/literacy/intent/culture detection)
- 50+ research notes corpus (ID/AR/EN trilingual)
- 5 personas: MIGHAN/TOARD/FACH/HAYFAR/INAN
- Safety policy G1 (anti-injection/toxic/PII/maqashid)
- FastAPI backend + Vite UI
- Fine-tuned Qwen2.5-7B LoRA adapter v1

License: MIT
"@

Write-Host "  Commit selesai." -ForegroundColor Green

# ── Step 6: Push ──────────────────────────────────────────────
Write-Host "[6/6] Push ke GitHub..." -ForegroundColor Yellow
Write-Host "  (akan minta GitHub credentials)" -ForegroundColor Gray

git push -u origin $Branch

Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "  SELESAI! Repo tersedia di:" -ForegroundColor Green
Write-Host "  $RepoUrl" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Buka $RepoUrl di browser"
Write-Host "  2. Settings > About: tambah description + topics (ai, llm, indonesia, arabic, self-hosted)"
Write-Host "  3. Share di Twitter/X, komunitas Python Indonesia, Forum AI Indonesia"
Write-Host "  4. Untuk 24/7 online: lihat docs/DEPLOY_VPS.md"
