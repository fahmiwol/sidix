# Makefile — Projek Badar Task 61 (G4)
# Task runner untuk SIDIX/Mighan Model dev workflow.
# Gunakan: make <target>
# Di Windows: jalankan lewat Git Bash, WSL, atau gunakan tasks.ps1 (PowerShell).
#
# Equivalent PowerShell: scripts/tasks.ps1 <target>
#   Example: .\scripts\tasks.ps1 serve

BRAIN_QA_DIR  = apps/brain_qa
BRAIN_QA_VENV = $(BRAIN_QA_DIR)/.venv
PYTHON        = python
PIP           = pip
UI_DIR        = SIDIX_USER_UI
PORT_BACKEND  = 8765
PORT_UI       = 3000

.PHONY: help install index serve ui lint test coverage backup status gpu-status \
        seed migrate-rag tag-release check-deps validate-env pre-commit-install

# --------------------------------------------------------------------------
# Default: show help
# --------------------------------------------------------------------------
help:
	@echo ""
	@echo "SIDIX / Mighan Model — Task Runner (Makefile)"
	@echo "================================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install brain_qa Python deps"
	@echo "  make pre-commit-install  Install pre-commit hooks"
	@echo ""
	@echo "Dev:"
	@echo "  make index            Build BM25 RAG index"
	@echo "  make serve            Start inference backend (port $(PORT_BACKEND))"
	@echo "  make ui               Start SIDIX UI dev server (port $(PORT_UI))"
	@echo "  make status           Show system status"
	@echo "  make gpu-status       Show GPU / CUDA availability"
	@echo ""
	@echo "Quality:"
	@echo "  make lint             Run ruff linter + formatter check"
	@echo "  make test             Run pytest unit tests"
	@echo "  make coverage         Run tests with coverage report"
	@echo "  make validate-env     Validate .env vs .env.sample"
	@echo ""
	@echo "Data:"
	@echo "  make seed             Seed demo corpus data"
	@echo "  make migrate-rag      Migrate RAG schema to latest version"
	@echo "  make backup           Backup .data directory"
	@echo ""
	@echo "Release:"
	@echo "  make check-deps       Check for outdated/vulnerable deps"
	@echo "  make tag-release      Create git tag from version"
	@echo ""

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------
install:
	cd $(BRAIN_QA_DIR) && $(PIP) install -r requirements.txt

pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed."

# --------------------------------------------------------------------------
# Dev workflow
# --------------------------------------------------------------------------
index:
	cd $(BRAIN_QA_DIR) && $(PYTHON) -m brain_qa index

serve:
	cd $(BRAIN_QA_DIR) && $(PYTHON) -m brain_qa serve --host 0.0.0.0 --port $(PORT_BACKEND)

ui:
	cd $(UI_DIR) && npm run dev

status:
	cd $(BRAIN_QA_DIR) && $(PYTHON) -m brain_qa status

gpu-status:
	cd $(BRAIN_QA_DIR) && $(PYTHON) -m brain_qa gpu-status

# --------------------------------------------------------------------------
# Quality
# --------------------------------------------------------------------------
lint:
	ruff check apps/brain_qa/brain_qa/ --line-length 100
	ruff format --check apps/brain_qa/brain_qa/ --line-length 100
	@echo "Lint OK."

test:
	$(PYTHON) -m pytest tests/ -v

coverage:
	$(PYTHON) -m pytest tests/ --cov=apps/brain_qa/brain_qa --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

validate-env:
	$(PYTHON) scripts/validate_env.py

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
seed:
	$(PYTHON) scripts/seed_demo.py

migrate-rag:
	$(PYTHON) scripts/migrate_rag_schema.py

backup:
	cd $(BRAIN_QA_DIR) && $(PYTHON) -m brain_qa backup

# --------------------------------------------------------------------------
# Release
# --------------------------------------------------------------------------
check-deps:
	$(PYTHON) scripts/check_deps.py

tag-release:
	$(PYTHON) scripts/tag_release.py --dry-run
	@echo "Re-run with: python scripts/tag_release.py --push"
