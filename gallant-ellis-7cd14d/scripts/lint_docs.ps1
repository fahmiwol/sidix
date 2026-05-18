# lint_docs.ps1 — Lint all project Markdown files with markdownlint-cli
# Usage:  .\scripts\lint_docs.ps1
# Requires: Node.js + markdownlint-cli (npm install -g markdownlint-cli)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot   # repo root (parent of scripts/)
$CONFIG = Join-Path $ROOT ".markdownlint.yml"

Write-Host ""
Write-Host "=== SIDIX Markdown Lint ===" -ForegroundColor Cyan
Write-Host "Config : $CONFIG"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Check if markdownlint-cli is installed globally
# ---------------------------------------------------------------------------
Write-Host "Checking for markdownlint-cli..." -NoNewline

$installed = $false
try {
    $listOutput = npm list -g markdownlint-cli --depth=0 2>&1
    if ($listOutput -match "markdownlint-cli") {
        $installed = $true
    }
} catch {
    $installed = $false
}

if (-not $installed) {
    Write-Host " NOT FOUND" -ForegroundColor Red
    Write-Host ""
    Write-Host "markdownlint-cli is not installed. Install it with:" -ForegroundColor Yellow
    Write-Host "    npm install -g markdownlint-cli" -ForegroundColor White
    Write-Host ""
    Write-Host "Then re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host " OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Collect files to lint (for reporting)
# ---------------------------------------------------------------------------
$docFiles   = @(Get-ChildItem -Path (Join-Path $ROOT "docs")         -Recurse -Filter "*.md" -ErrorAction SilentlyContinue)
$brainFiles = @(Get-ChildItem -Path (Join-Path $ROOT "brain/public") -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -notlike "*brain\public\web_clips*" -and $_.FullName -notlike "*brain/public/web_clips*" })

$totalFiles = $docFiles.Count + $brainFiles.Count
Write-Host "Files found : $totalFiles total ($($docFiles.Count) in docs/, $($brainFiles.Count) in brain/public/)"
Write-Host ""

# ---------------------------------------------------------------------------
# 3. Run markdownlint
# ---------------------------------------------------------------------------
Write-Host "Running markdownlint..." -ForegroundColor Cyan

$lintArgs = @(
    '"docs/**/*.md"',
    '"brain/public/**/*.md"',
    '--ignore', '"brain/public/web_clips"',
    '--config', "`"$CONFIG`""
)

$process = Start-Process -FilePath "markdownlint" `
    -ArgumentList $lintArgs `
    -WorkingDirectory $ROOT `
    -NoNewWindow `
    -Wait `
    -PassThru

$exitCode = $process.ExitCode

Write-Host ""

# ---------------------------------------------------------------------------
# 4. Report
# ---------------------------------------------------------------------------
if ($exitCode -eq 0) {
    Write-Host "PASS — $totalFiles file(s) checked, no issues found." -ForegroundColor Green
} else {
    Write-Host "FAIL — markdownlint reported issues in the files above." -ForegroundColor Red
    Write-Host "Fix the reported lines and re-run: .\scripts\lint_docs.ps1" -ForegroundColor Yellow
}

Write-Host ""
exit $exitCode
