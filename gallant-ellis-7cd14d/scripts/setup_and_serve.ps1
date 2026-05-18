# =============================================================================
# Mighan-brain-1 - SIDIX Setup & Serve
# Repo: D:\MIGHAN Model
#
# Jalankan di PowerShell:
#   powershell -ExecutionPolicy Bypass -File "D:\MIGHAN Model\scripts\setup_and_serve.ps1"
#
# Yang dilakukan:
#   1. pip install requirements.txt (rank-bm25, fastapi, uvicorn, dll)
#   2. python -m brain_qa index    (build BM25 index dari brain/public/)
#   3. python -m brain_qa serve    (start API server di http://localhost:8765)
#
# Untuk UI (terminal terpisah setelah server ini jalan):
#   powershell -ExecutionPolicy Bypass -File "D:\MIGHAN Model\scripts\dev_ui.ps1"
#   -> http://localhost:3000
# =============================================================================

$ErrorActionPreference = 'Stop'
$ROOT      = 'D:\MIGHAN Model'
$BRAIN_QA  = 'D:\MIGHAN Model\apps\brain_qa'

Write-Host ''
Write-Host '======================================================' -ForegroundColor Cyan
Write-Host '  Mighan-brain-1 :: SIDIX Setup & Serve' -ForegroundColor Cyan
Write-Host '======================================================' -ForegroundColor Cyan
Write-Host ''

# 1. Masuk ke apps/brain_qa
Write-Host '[1/4] Masuk ke apps\brain_qa ...' -ForegroundColor Yellow
Set-Location $BRAIN_QA

# 2. Install Python deps
Write-Host ''
Write-Host '[2/4] Install Python dependencies ...' -ForegroundColor Yellow
Write-Host '      (rank-bm25, fastapi, uvicorn, python-multipart, dll)' -ForegroundColor Gray

python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[ERROR] pip install gagal. Pastikan Python ada di PATH.' -ForegroundColor Red
    Write-Host '        Coba: python --version' -ForegroundColor Gray
    exit 1
}
Write-Host '      OK - semua dependency ter-install.' -ForegroundColor Green

# 3. Build index
Write-Host ''
Write-Host '[3/4] Build BM25 index dari brain/public/ ...' -ForegroundColor Yellow
Write-Host '      (bisa 10-30 detik tergantung jumlah dokumen)' -ForegroundColor Gray

python -m brain_qa index
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[ERROR] Index gagal dibangun.' -ForegroundColor Red
    Write-Host '        Cek brain/manifest.json dan brain/public/ tidak kosong.' -ForegroundColor Gray
    exit 1
}
Write-Host '      OK - index siap.' -ForegroundColor Green

# 4. Start server
Write-Host ''
Write-Host '[4/4] Menjalankan brain_qa server ...' -ForegroundColor Yellow
Write-Host ''
Write-Host '  Backend API : http://localhost:8765' -ForegroundColor Cyan
Write-Host '  Swagger UI  : http://localhost:8765/docs' -ForegroundColor Cyan
Write-Host ''
Write-Host '  Untuk UI, buka terminal BARU dan jalankan:' -ForegroundColor Gray
Write-Host '    powershell -ExecutionPolicy Bypass -File "D:\MIGHAN Model\scripts\dev_ui.ps1"' -ForegroundColor Gray
Write-Host '    -> http://localhost:3000' -ForegroundColor Gray
Write-Host ''
Write-Host '  CTRL+C untuk stop server.' -ForegroundColor Gray
Write-Host '======================================================' -ForegroundColor Cyan
Write-Host ''

python -m brain_qa serve --host 127.0.0.1 --port 8765
