# SIDIX UI - Dev Server
# Jalankan di terminal BARU (backend harus sudah jalan di terminal lain)
# powershell -ExecutionPolicy Bypass -File "D:\MIGHAN Model\scripts\dev_ui.ps1"

$ErrorActionPreference = 'Stop'
$UI = 'D:\MIGHAN Model\SIDIX_USER_UI'

Write-Host ''
Write-Host '======================================================' -ForegroundColor Magenta
Write-Host '  SIDIX UI - Dev Server' -ForegroundColor Magenta
Write-Host '======================================================' -ForegroundColor Magenta
Write-Host ''

Set-Location $UI

if (-not (Test-Path (Join-Path $UI 'node_modules'))) {
    Write-Host '[1/2] node_modules belum ada. Menjalankan npm install ...' -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[ERROR] npm install gagal. Pastikan Node.js ada di PATH.' -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host '[1/2] node_modules sudah ada, skip install.' -ForegroundColor Green
}

Write-Host ''
Write-Host '[2/2] Menjalankan Vite dev server ...' -ForegroundColor Yellow
Write-Host ''
Write-Host '  SIDIX UI : http://localhost:3000' -ForegroundColor Cyan
Write-Host '  Backend  : http://localhost:8765  (harus sudah jalan)' -ForegroundColor Gray
Write-Host ''
Write-Host '  CTRL+C untuk stop.' -ForegroundColor Gray
Write-Host '======================================================' -ForegroundColor Magenta
Write-Host ''

npm run dev
