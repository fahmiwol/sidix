<#
.SYNOPSIS
    Task runner untuk SIDIX / Mighan Model — Windows PowerShell equivalent of Makefile.
    Projek Badar Task 61 (G4).

.DESCRIPTION
    Gunakan: .\scripts\tasks.ps1 <target>
    Contoh:  .\scripts\tasks.ps1 serve
             .\scripts\tasks.ps1 test
             .\scripts\tasks.ps1 help

.PARAMETER Target
    Target yang akan dijalankan. Default: help.
#>

param(
    [Parameter(Position=0)]
    [string]$Target = "help"
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent
$BRAIN_QA_DIR = Join-Path $ROOT "apps\brain_qa"
$UI_DIR = Join-Path $ROOT "SIDIX_USER_UI"

function Show-Help {
    Write-Host ""
    Write-Host "SIDIX / Mighan Model — Task Runner (PowerShell)" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Setup:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 install          Install brain_qa Python deps"
    Write-Host "  .\scripts\tasks.ps1 pre-commit        Install pre-commit hooks"
    Write-Host ""
    Write-Host "Dev:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 index             Build BM25 RAG index"
    Write-Host "  .\scripts\tasks.ps1 serve             Start inference backend (port 8765)"
    Write-Host "  .\scripts\tasks.ps1 ui                Start SIDIX UI dev server (port 3000)"
    Write-Host "  .\scripts\tasks.ps1 status            Show system status"
    Write-Host "  .\scripts\tasks.ps1 gpu-status        Show GPU / CUDA availability"
    Write-Host ""
    Write-Host "Quality:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 lint              Run ruff linter"
    Write-Host "  .\scripts\tasks.ps1 test              Run pytest unit tests"
    Write-Host "  .\scripts\tasks.ps1 coverage          Run tests with coverage"
    Write-Host "  .\scripts\tasks.ps1 validate-env      Validate .env vs .env.sample"
    Write-Host ""
    Write-Host "Data:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 seed              Seed demo corpus data"
    Write-Host "  .\scripts\tasks.ps1 migrate-rag       Migrate RAG schema"
    Write-Host "  .\scripts\tasks.ps1 backup            Backup .data directory"
    Write-Host ""
    Write-Host "Operations (G5):" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 benchmark         Benchmark endpoint latency (Task 30)"
    Write-Host "  .\scripts\tasks.ps1 ablation          Ablation 3 system prompts (Task 31)"
    Write-Host "  .\scripts\tasks.ps1 load-test         Load test antrian inferensi (Task 34)"
    Write-Host "  .\scripts\tasks.ps1 disk-alarm        Cek disk penuh volume model (Task 41)"
    Write-Host "  .\scripts\tasks.ps1 log-rotate        Rotasi & retensi log (Task 42)"
    Write-Host "  .\scripts\tasks.ps1 monitor           Synthetic monitor uptime sekali (Task 44)"
    Write-Host "  .\scripts\tasks.ps1 cost-dashboard    Dashboard biaya token (Task 46)"
    Write-Host "  .\scripts\tasks.ps1 profile           Profiling satu request (Task 47)"
    Write-Host ""
    Write-Host "Corpus & Knowledge:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 fetch-corpus      Fetch coding corpus dari roadmap.sh"
    Write-Host "  .\scripts\tasks.ps1 launch-v1         Verify + start SIDIX v1"
    Write-Host ""
    Write-Host "Release:" -ForegroundColor Yellow
    Write-Host "  .\scripts\tasks.ps1 check-deps        Check outdated/vulnerable deps"
    Write-Host "  .\scripts\tasks.ps1 tag-release       Create git tag (dry-run)"
    Write-Host ""
}

switch ($Target.ToLower()) {
    "help" { Show-Help }

    "install" {
        Write-Host "[install] pip install -r requirements.txt" -ForegroundColor Cyan
        Push-Location $BRAIN_QA_DIR
        pip install -r requirements.txt
        Pop-Location
    }

    "pre-commit" {
        Write-Host "[pre-commit] Installing hooks..." -ForegroundColor Cyan
        Push-Location $ROOT
        pre-commit install
        Pop-Location
    }

    "index" {
        Write-Host "[index] Building BM25 index..." -ForegroundColor Cyan
        Push-Location $BRAIN_QA_DIR
        python -m brain_qa index
        Pop-Location
    }

    "serve" {
        Write-Host "[serve] Starting inference backend on port 8765..." -ForegroundColor Cyan
        Push-Location $BRAIN_QA_DIR
        python -m brain_qa serve --host 0.0.0.0 --port 8765
        Pop-Location
    }

    "ui" {
        Write-Host "[ui] Starting SIDIX UI dev server on port 3000..." -ForegroundColor Cyan
        Push-Location $UI_DIR
        npm run dev
        Pop-Location
    }

    "status" {
        Push-Location $BRAIN_QA_DIR
        python -m brain_qa status
        Pop-Location
    }

    "gpu-status" {
        Push-Location $BRAIN_QA_DIR
        python -m brain_qa gpu-status
        Pop-Location
    }

    "lint" {
        Write-Host "[lint] Running ruff..." -ForegroundColor Cyan
        Push-Location $ROOT
        ruff check apps/brain_qa/brain_qa/ --line-length 100
        ruff format --check apps/brain_qa/brain_qa/ --line-length 100
        Pop-Location
        Write-Host "Lint OK." -ForegroundColor Green
    }

    "test" {
        Write-Host "[test] Running pytest..." -ForegroundColor Cyan
        Push-Location $ROOT
        python -m pytest tests/ -v
        Pop-Location
    }

    "coverage" {
        Write-Host "[coverage] Running pytest with coverage..." -ForegroundColor Cyan
        Push-Location $ROOT
        python -m pytest tests/ --cov=apps/brain_qa/brain_qa --cov-report=term-missing --cov-report=html
        Pop-Location
        Write-Host "Coverage report: htmlcov/index.html" -ForegroundColor Green
    }

    "validate-env" {
        Push-Location $ROOT
        python scripts/validate_env.py
        Pop-Location
    }

    "seed" {
        Write-Host "[seed] Seeding demo corpus..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/seed_demo.py
        Pop-Location
    }

    "migrate-rag" {
        Push-Location $ROOT
        python scripts/migrate_rag_schema.py
        Pop-Location
    }

    "backup" {
        Push-Location $BRAIN_QA_DIR
        python -m brain_qa backup
        Pop-Location
    }

    "check-deps" {
        Push-Location $ROOT
        python scripts/check_deps.py
        Pop-Location
    }

    "tag-release" {
        Push-Location $ROOT
        python scripts/tag_release.py --dry-run
        Write-Host "Re-run dengan: python scripts/tag_release.py --push" -ForegroundColor Yellow
        Pop-Location
    }

    # ── G5 Operational scripts (Tasks 30, 31, 34, 41, 42, 44, 46, 47) ────────

    "benchmark" {
        Write-Host "[benchmark] Mengukur latensi endpoint /ask..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/benchmark_latency.py @args
        Pop-Location
    }

    "ablation" {
        Write-Host "[ablation] Membandingkan 3 varian system prompt..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/ablation_prompts.py @args
        Pop-Location
    }

    "load-test" {
        Write-Host "[load-test] Load test antrian inferensi..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/load_test.py @args
        Pop-Location
    }

    "disk-alarm" {
        Write-Host "[disk-alarm] Cek disk volume model..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/disk_alarm.py --path $ROOT @args
        Pop-Location
    }

    "log-rotate" {
        Write-Host "[log-rotate] Rotasi log lama..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/log_rotation.py @args
        Pop-Location
    }

    "monitor" {
        Write-Host "[monitor] Synthetic monitor --once..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/synthetic_monitor.py --once @args
        Pop-Location
    }

    "cost-dashboard" {
        Write-Host "[cost-dashboard] Dashboard biaya token..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/api_cost_dashboard.py @args
        Pop-Location
    }

    "profile" {
        Write-Host "[profile] Profiling satu request (gunakan --question '...')..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/profile_request.py @args
        Pop-Location
    }

    "fetch-corpus" {
        Write-Host "[fetch-corpus] Mengambil coding corpus dari roadmap.sh..." -ForegroundColor Cyan
        Push-Location $ROOT
        python scripts/fetch_coding_corpus.py @args
        Pop-Location
    }

    "launch-v1" {
        Write-Host "[launch-v1] Verifikasi + start SIDIX v1..." -ForegroundColor Cyan
        Push-Location $ROOT
        .\scripts\launch_v1.ps1 @args
        Pop-Location
    }

    default {
        Write-Host "Unknown target: $Target" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
