<#
.SYNOPSIS
    SIDIX v1 — One-shot launch verifier & starter.
    Memeriksa semua prasyarat lalu menawarkan untuk start backend + UI.

.DESCRIPTION
    Jalankan dari root repo:
        .\scripts\launch_v1.ps1

    Script ini akan:
      1. Cek Python tersedia
      2. Cek adapter LoRA lokal lengkap
      3. Cek torch/transformers/peft tersedia
      4. Build index RAG jika belum
      5. Start backend (port 8765)
      6. Instruksi start UI (port 3000)

    Tidak memerlukan GPU untuk menjalankan script ini —
    GPU hanya dibutuhkan saat model load di server.
#>

param(
    [switch]$SkipDepsCheck,
    [switch]$NoStart
)

$ErrorActionPreference = "Continue"
$ROOT = Split-Path $PSScriptRoot -Parent
$BRAIN_QA_DIR = Join-Path $ROOT "apps\brain_qa"
$ADAPTER_DIR  = Join-Path $BRAIN_QA_DIR "models\sidix-lora-adapter"
$UI_DIR       = Join-Path $ROOT "SIDIX_USER_UI"

$PASS = "[OK]"
$FAIL = "[FAIL]"
$WARN = "[WARN]"
$INFO = "[INFO]"

function Write-Step($msg) { Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "  $PASS $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  $FAIL $msg" -ForegroundColor Red }
function Write-Warn($msg) { Write-Host "  $WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  $INFO $msg" -ForegroundColor Gray }

$allOk = $true

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SIDIX v1 — Launch Verifier" -ForegroundColor Cyan
Write-Host "  Projek Badar — 114 artefak, 0 vendor API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── 1. Python ─────────────────────────────────────────────────────────────────
Write-Step "1. Cek Python"
$pyVer = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Pass "$pyVer"
} else {
    Write-Fail "Python tidak ditemukan. Install Python 3.10+ dari python.org"
    $allOk = $false
}

# ── 2. Adapter ────────────────────────────────────────────────────────────────
Write-Step "2. Cek LoRA Adapter"
$adapterConfig  = Join-Path $ADAPTER_DIR "adapter_config.json"
$adapterWeights = Join-Path $ADAPTER_DIR "adapter_model.safetensors"

if (Test-Path $adapterConfig) {
    Write-Pass "adapter_config.json ditemukan"
} else {
    Write-Fail "adapter_config.json tidak ada di: $ADAPTER_DIR"
    $allOk = $false
}

if (Test-Path $adapterWeights) {
    $size = (Get-Item $adapterWeights).Length / 1MB
    Write-Pass ("adapter_model.safetensors ditemukan ({0:F1} MB)" -f $size)
} else {
    Write-Fail "adapter_model.safetensors tidak ada"
    Write-Info "Ekstrak dari: apps\brain_qa\models\sidix-lora-adapter.zip"
    $allOk = $false
}

# ── 3. ML Dependencies ────────────────────────────────────────────────────────
if (-not $SkipDepsCheck) {
    Write-Step "3. Cek ML Dependencies"

    $torchOk = python -c "import torch; print(torch.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $cudaOk = python -c "import torch; print(torch.cuda.is_available())" 2>&1
        Write-Pass "torch $torchOk (CUDA: $cudaOk)"
    } else {
        Write-Warn "torch tidak terinstall"
        Write-Info "pip install torch --index-url https://download.pytorch.org/whl/cu121"
        $allOk = $false
    }

    $peftOk = python -c "import peft; print(peft.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "peft $peftOk"
    } else {
        Write-Warn "peft tidak terinstall"
        Write-Info "pip install peft>=0.10.0"
        $allOk = $false
    }

    $trfOk = python -c "import transformers; print(transformers.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "transformers $trfOk"
    } else {
        Write-Warn "transformers tidak terinstall"
        Write-Info "pip install transformers>=4.40.0"
        $allOk = $false
    }

    $bitsOk = python -c "import bitsandbytes; print('ok')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "bitsandbytes OK (4-bit quantization tersedia)"
    } else {
        Write-Warn "bitsandbytes tidak ada — inference akan pakai fp16 (butuh lebih banyak VRAM)"
        Write-Info "Set env SIDIX_DISABLE_4BIT=1 untuk bypass, atau: pip install bitsandbytes"
    }
} else {
    Write-Info "3. Cek deps dilewati (--SkipDepsCheck)"
}

# ── 4. Index RAG ──────────────────────────────────────────────────────────────
Write-Step "4. Cek / Build Index RAG"
$indexFile = Join-Path $BRAIN_QA_DIR ".data\index\bm25_index.pkl"
if (Test-Path $indexFile) {
    Write-Pass "Index BM25 sudah ada: $indexFile"
} else {
    Write-Warn "Index belum ada — membangun sekarang..."
    Push-Location $BRAIN_QA_DIR
    python -m brain_qa index
    Pop-Location
    if (Test-Path $indexFile) {
        Write-Pass "Index berhasil dibangun"
    } else {
        Write-Warn "Index tidak terbentuk. Jalankan manual: python -m brain_qa index"
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "  STATUS: SIAP LAUNCH ✅" -ForegroundColor Green
} else {
    Write-Host "  STATUS: ADA MASALAH — selesaikan item [FAIL] di atas" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

if (-not $allOk) {
    Write-Host ""
    Write-Host "Setelah semua masalah diselesaikan, jalankan ulang script ini." -ForegroundColor Yellow
    Write-Host "Lihat docs\LAUNCH_V1.md untuk panduan lengkap." -ForegroundColor Yellow
    exit 1
}

# ── 5. Start Server ────────────────────────────────────────────────────────────
if ($NoStart) {
    Write-Host ""
    Write-Info "Semua cek PASS. Jalankan manual:"
    Write-Info "  Terminal 1: .\scripts\tasks.ps1 serve"
    Write-Info "  Terminal 2: .\scripts\tasks.ps1 ui"
    Write-Info "  Browser   : http://localhost:3000"
    exit 0
}

Write-Host ""
Write-Host "Semua cek PASS! Memulai backend..." -ForegroundColor Green
Write-Host "Tekan Ctrl+C untuk stop." -ForegroundColor Yellow
Write-Host ""
Write-Host "UI dapat dijalankan di terminal terpisah:" -ForegroundColor Cyan
Write-Host "  .\scripts\tasks.ps1 ui  →  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

Push-Location $BRAIN_QA_DIR
python -m brain_qa serve --host 0.0.0.0 --port 8765
Pop-Location
