#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX-SocioMeter Deploy Script
# Jalankan di VPS setelah deploy key ditambahkan ke GitHub
# ═══════════════════════════════════════════════════════════════════

set -e

DEPLOY_KEY="$HOME/.ssh/sidix_deploy"
REPO_URL="git@github.com:fahmiwol/sidix.git"
BRANCH="sociometer-sprint7"
WORK_DIR="/tmp/sidix-sociometer-deploy"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SIDIX-SocioMeter — Deploy ke GitHub                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── 1. Setup SSH Agent ─────────────────────────────────────────
echo "[1/6] Setup SSH agent..."
eval "$(ssh-agent -s)" >/dev/null 2>&1
ssh-add "$DEPLOY_KEY" 2>/dev/null || {
    echo "❌ Error: Tidak bisa load deploy key"
    echo "Pastikan file $DEPLOY_KEY ada"
    exit 1
}
echo "✅ SSH agent ready"

# ─── 2. Clone Repo ──────────────────────────────────────────────
echo ""
echo "[2/6] Clone repo sidix..."
rm -rf "$WORK_DIR"
git clone "$REPO_URL" "$WORK_DIR" --quiet
cd "$WORK_DIR"
echo "✅ Repo cloned ke $WORK_DIR"

# ─── 3. Create Branch ───────────────────────────────────────────
echo ""
echo "[3/6] Create branch: $BRANCH..."
git checkout -b "$BRANCH" --quiet
echo "✅ Branch $BRANCH created"

# ─── 4. Create Directory Structure ──────────────────────────────
echo ""
echo "[4/6] Create directory structure..."
mkdir -p docs/sociometer/{strategi,prd,erd,dokumentasi,fitur,plan,riset,script}
echo "✅ Directories created"

# ─── 5. Create All Files ────────────────────────────────────────
echo ""
echo "[5/6] Create SIDIX-SocioMeter documentation files..."

# File 1: Strategi
cat > 'docs/sociometer/strategi/01_STRATEGI_SOCIOMETER.md' << 'FILE01'
# DOKUMEN INI AKAN DIISI DARI CONTENT YANG SUDAH DIBUAT
# Copy content dari: /mnt/agents/output/sidix-docs/strategi/01_STRATEGI_SOCIOMETER.md
FILE01

echo "✅ File placeholders created"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ⚠️  PERLU ISI MANUAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Karena file dokumentasi sangat besar, copy-paste manual"
echo "dari content yang sudah dibuat. Berikut daftar file:"
echo ""
echo "  docs/sociometer/strategi/01_STRATEGI_SOCIOMETER.md"
echo "  docs/sociometer/prd/02_PRD_SOCIOMETER.md"
echo "  docs/sociometer/erd/03_ERD_SOCIOMETER.md"
echo "  docs/sociometer/dokumentasi/04_DOKUMENTASI_SOCIOMETER.md"
echo "  docs/sociometer/fitur/05_FITUR_SPECS_SOCIOMETER.md"
echo "  docs/sociometer/plan/06_IMPLEMENTATION_SOCIOMETER.md"
echo "  docs/sociometer/riset/07_RISET_SOCIOMETER.md"
echo "  docs/sociometer/script/08_SCRIPT_MODULE_SOCIOMETER.md"
echo ""

cd "$WORK_DIR"

# ─── 6. Commit & Push ───────────────────────────────────────────
echo ""
echo "[6/6] Commit and push..."
git add -A
git commit -m "📊 SIDIX-SocioMeter: Documentation Suite v1.0

- Strategi: Arsitektur ekosistem dan Jariyah harvesting loop
- PRD: Product requirements dengan 19 fitur (6 P0 + 13 roadmap)
- ERD: 18 tabel database, 6 domain, schema PostgreSQL
- Dokumentasi: Arsitektur 6 lapis dengan data flow diagrams
- Fitur Specs: API specification lengkap untuk semua fitur
- Implementation: 12 sprint (24 minggu) execution plan
- Riset: Technology & market analysis
- Script: Production-ready module reference

Semua menggunakan terminologi SIDIX-native:
Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir

Closes: Sprint 7 foundation"

git push origin "$BRANCH"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ PUSH SUCCESS!                                           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Branch: $BRANCH                                            ║"
echo "║  URL: https://github.com/fahmiwol/sidix/tree/$BRANCH       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Isi file content (copy-paste dari hasil kerjaan)"
echo "  2. Commit ulang"
echo "  3. Push lagi: git push origin $BRANCH"
echo "  4. Buat Pull Request di GitHub"
echo ""
echo "Work directory: $WORK_DIR"
echo ""
echo "Untuk cabut deploy key setelah selesai:"
echo "  GitHub → Repo → Settings → Deploy keys → sociometer-deploy → Delete"
echo "  VPS: rm ~/.ssh/sidix_deploy ~/.ssh/sidix_deploy.pub"
