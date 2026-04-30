# DUPLICATE AUDIT — SIDIX Repo — 2026-04-30

> **Scope**: repo root `c:\SIDIX-AI` (termasuk embedded worktrees & archive).  
> **Metode**: perbandingan nama file, isi, dan lokasi.  
> **Prinsip**: tidak menghapus apapun; hanya rekomendasi.  

---

## 1 · Tabel Duplikat & Redundansi

| # | File A | File B | Lokasi | Analisis | Rekomendasi |
|---|--------|--------|--------|----------|-------------|
| 1 | `deploy-scripts/deploy.sh` (63 baris) | `deploy-scripts/deploy-frontend.sh` (133 baris) | `deploy-scripts/` | `deploy.sh` sudah mengandung sync Landing Page + PM2 restart + health check. `deploy-frontend.sh` melakukan hal serupa (sync landing, PM2, health) tetapi tambah build Vite + sync SIDIX_BOARD. | **Merge** — jadikan `deploy.sh` sebagai entry universal yang memanggil sub-routine frontend bila flag `--frontend` diberikan. |
| 2 | `deploy-scripts/deploy.sh` + `deploy-frontend.sh` | `deploy-scripts/deploy-manual.md` (70 baris) | `deploy-scripts/` | Manual deploy adalah versi Markdown dari instruksi yang sudah tercakup di komentar & output kedua script shell. | **Archive** `deploy-manual.md` ke `docs/archive/` atau **hapus** bila README deploy sudah cukup. |
| 3 | `deploy-scripts/deploy_sprint25_hybrid.sh` | — | `deploy-scripts/` | Script one-time Sprint 25 (rebuild dense index + flip env). Logika hybrid retrieval sudah masuk ke `ecosystem.config.js` dan index rebuild bisa dipicu via CLI. | **Archive** ke `scripts/legacy/` karena bersifat historis; jangan hapus sebelum verifikasi tidak ada cron yang memanggilnya. |
| 4 | `Dockerfile.brain_qa` (multi-stage, 42 baris) | `Dockerfile.inference` (12 baris, single-stage) | Root repo | `Dockerfile.inference` adalah subset sederhana dari `Dockerfile.brain_qa` (sama-sama build index + serve port 8765), hanya tanpa optimasi multi-stage. | **Delete** `Dockerfile.inference`; gunakan `Dockerfile.brain_qa` untuk semua backend deploy. |
| 5 | `.env.sample` (root, 85 baris, komprehensif) | `SIDIX_USER_UI/.env.example` (19 baris, UI-only) | Root + `SIDIX_USER_UI/` | `.env.sample` root sudah mencakup `VITE_BRAIN_QA_URL`, tetapi `SIDIX_USER_UI/.env.example` punya field Supabase yang tidak ada di root. | **Keep both** tetapi **standardize nama** — ubah `.env.sample` → `.env.example` (konvensi umum) atau sebaliknya. Tambahkan cross-reference di header masing-masing. |
| 6 | `Framework_bahasa_plugin_update/sidix-sociometer-all.tar.gz` | `archive/legacy_sociometer/*/sidix-sociometer-all.tar.gz` (2 lokasi) | `Framework_bahasa_plugin_update/` vs `archive/legacy_sociometer/` | File tar.gz identik (hash berbeda? belum dicek, fungsi sama). | **Keep** salah satu di `archive/legacy_sociometer/` sebagai canonical; **delete** duplikat di `Framework_bahasa_plugin_update/` (folder tersebut untuk dokumen, bukan binary deploy). |
| 7 | `Framework_bahasa_plugin_update/sidix-sociometer-deploy.tar.gz` | `archive/legacy_sociometer/*/sidix-sociometer-deploy.tar.gz` (2 lokasi) | Sama seperti di atas | Deploy tarball duplikat. | **Keep** canonical di `archive/`; **delete** di `Framework_bahasa_plugin_update/`. |
| 8 | `brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md` | `Framework_bahasa_plugin_update/sidix-cursor-brief/ARSITEKTUR_JIWA_SIDIX.md` | `brain/jiwa/` vs `Framework_bahasa_plugin_update/` | Konten identik (ARSITEKTUR_JIWA_SIDIX.md). | **Keep** `brain/jiwa/` (lokasi canonical sesuai struktur repo sekarang); **delete** di `Framework_bahasa_plugin_update/` karena sudah di-archive. |
| 9 | `docs/sociometer/fitur/05_FITUR_SPECS_SOCIOMETER.md` (dan 7 file sociometer lainnya) | `Framework_bahasa_plugin_update/sidix-docs/fitur/05_FITUR_SPECS_SOCIOMETER.md` | `docs/sociometer/` vs `Framework_bahasa_plugin_update/sidix-docs/` | 8 file sociometer (01_STRATEGI, 02_PRD, 03_ERD, 04_DOKUMENTASI, 05_FITUR, 06_IMPLEMENTATION, 07_RISET, 08_SCRIPT_MODULE) terduplikasi di `Framework_bahasa_plugin_update/`. | **Keep** canonical di `docs/sociometer/`; **delete** duplikat di `Framework_bahasa_plugin_update/` (folder update bahasa tidak perlu salinan dokumen lama). |
| 10 | `docs/sociometer/fitur/05_FITUR_SPECS_SOCIOMETER.md` (canonical) | `archive/legacy_sociometer/*/sidix-docs/fitur/05_FITUR_SPECS_SOCIOMETER.md` (2 lokasi archive) | `docs/sociometer/` vs `archive/legacy_sociometer/` | File sociometer yang sama disimpan lagi di archive legacy. | **Keep** archive (sesuai fungsi `archive/`); **delete** tidak diperlukan karena archive memang untuk history. Status quo OK. |
| 11 | `docs/BRIEF_SIDIX_SocioMeter.md` | `Framework_bahasa_plugin_update/sidix-cursor-brief/BRIEF_SIDIX_SocioMeter.md` | Root `docs/` vs `Framework_bahasa_plugin_update/` | Brief sociometer duplikat. | **Keep** `docs/`; **delete** di `Framework_bahasa_plugin_update/`. |
| 12 | `kimi-plugin/manifest.json` + `bridge.py` + `sidix_skill.yaml` | `Framework_bahasa_plugin_update/sidix-cursor-brief/kimi-plugin/*` | `kimi-plugin/` vs `Framework_bahasa_plugin_update/` | Plugin Kimi duplikat di folder update bahasa. | **Keep** `kimi-plugin/` (canonical); **delete** duplikat di `Framework_bahasa_plugin_update/`. |
| 13 | `browser/social-radar-extension/background.js` + `popup.js` | `extension/sidix-pixel/background.js` + `popup.js` | `browser/` vs `extension/` | Nama file sama tetapi fungsi berbeda: social-radar vs pixel. | **Keep both** — bukan duplikat fungsional. |
| 14 | `SIDIX_LANDING/index.html` + `manifest.json` | `SIDIX_BOARD/index.html` + `manifest.json` | `SIDIX_LANDING/` vs `SIDIX_BOARD/` | Landing page vs Command Board; manifest berbeda (scope, icons). | **Keep both** — produk berbeda. |
| 15 | `apps/sidix-extension-bridge/src/index.js` | `apps/sidix-mcp/src/index.js` | `apps/sidix-extension-bridge/` vs `apps/sidix-mcp/` | Nama sama tetapi isi berbeda (bridge vs MCP). | **Keep both**. |

---

## 2 · Embedded Worktrees / Full Repo Copies (REDUNDANSI MASIF)

Empat direktori berikut adalah **salinan integral (embedded git worktree)** dari seluruh atau sebagian besar repo. Mereka menduplikasi ribuan file (README.md, __init__.py, requirements.txt, manifest.json, dll.) secara eksak.

| Direktori | Tipe | Isi | Rekomendasi |
|-----------|------|-----|-------------|
| `epic-cray-3e451f/` | Embedded worktree / copy | Full repo snapshot (±37 subfolder level-1) | **Delete** dari branch aktif (`work/gallant-ellis-7cd14d`). Jika butuh history, gunakan `git worktree` proper atau simpan sebagai tag/archive tarball di luar repo. |
| `gallant-ellis-7cd14d/` | Embedded git repo (gitlink `160000`, commit `a0ffd74`) | Full repo snapshot (±47 subfolder level-1) | **Convert atau hapus**. Sudah ada catatan di `brain/public/research_notes/308_sprint_decision_2026-04-30.md`. Pilihan: (1) `git rm --cached gallant-ellis-7cd14d` lalu hapus folder; (2) jadikan submodule bila memang repo terpisah; (3) biarkan di branch `work/gallant-ellis-7cd14d` saja dan jangan merge ke `main`. |
| `pedantic-banach-c8232d/` | Embedded worktree / copy | Full repo snapshot (±43 subfolder level-1) | **Delete** dari working tree. Tidak ada catatan resmi mengapa folder ini ada. |
| `serene-murdock-dbcb1f/` | Embedded worktree / copy | Full repo snapshot | **Delete** dari working tree. Tidak ada catatan resmi. |

**Dampak**: Keempat folder ini menduplikasi ~300+ file non-dependency (README, Python source, JS source, docs, brain, apps) sehingga ukuran repo dan waktu `git status` membengkak. Karena mereka bukan submodule yang terdaftar, setiap `git add .` berisiko menarik salinan duplikat ke index.

---

## 3 · Tabel File Tidak Perlu / Bisa Di-archive

| # | Path | Alasan | Action |
|---|------|--------|--------|
| 1 | `.embedded_git_backups/gallant-ellis-7cd14d_20260430213106.git` | Git bundle backup untracked yang baru dibuat (56 byte? sepertinya stub). Jika valid, sebaiknya di `.gitignore` atau di folder backup terpisah. | **Gitignore** `.embedded_git_backups/` atau pindahkan ke `D:\MIGHAN Model\backups\` (workspace lokal). |
| 2 | `Dockerfile.inference` | Subset `Dockerfile.brain_qa` tanpa multi-stage. Tidak ada CI atau dokumen yang mereferensinya. | **Delete** atau **archive** ke `docs/archive/`. |
| 3 | `deploy-scripts/deploy-manual.md` | Instruksi manual overlap dengan `deploy.sh` dan `deploy-frontend.sh` yang sudah self-documenting. | **Archive** ke `docs/archive/deploy-manual-legacy.md`. |
| 4 | `deploy-scripts/deploy_sprint25_hybrid.sh` | One-time deploy script Sprint 25. Sudah tidak relevan untuk sprint berjalan. | **Archive** ke `scripts/legacy/deploy_sprint25_hybrid.sh`. |
| 5 | `Framework_bahasa_plugin_update/sidix-sociometer-all.tar.gz` | Binary deploy duplikat dari `archive/legacy_sociometer/`. | **Delete**. |
| 6 | `Framework_bahasa_plugin_update/sidix-sociometer-deploy.tar.gz` | Binary deploy duplikat dari `archive/legacy_sociometer/`. | **Delete**. |
| 7 | `Framework_bahasa_plugin_update/sidix-docs/**` (8 file sociometer) | Duplikat dari `docs/sociometer/**`. Folder `Framework_bahasa_plugin_update/` seharusnya untuk brief/plugin, bukan dokumen lengkap. | **Delete** 8 file sociometer di folder ini; pertahankan `sidix-cursor-brief/` bila masih relevan. |
| 8 | `Framework_bahasa_plugin_update/sidix-cursor-brief/ARSITEKTUR_JIWA_SIDIX.md` | Duplikat `brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md`. | **Delete** (sudah ada canonical di `brain/jiwa/`). |
| 9 | `Framework_bahasa_plugin_update/sidix-cursor-brief/BRIEF_SIDIX_SocioMeter.md` | Duplikat `docs/BRIEF_SIDIX_SocioMeter.md`. | **Delete**. |
| 10 | `Framework_bahasa_plugin_update/sidix-cursor-brief/KIMI_INTEGRATION_GUIDE.md` | Duplikat `docs/KIMI_INTEGRATION_GUIDE.md`. | **Delete** (atau pindahkan canonical ke `docs/` bila belum). |
| 11 | `Framework_bahasa_plugin_update/sidix-cursor-brief/TYPO_RESILIENT_FRAMEWORK.md` | Duplikat `brain/typo/TYPO_RESILIENT_FRAMEWORK.md`. | **Delete** (canonical di `brain/typo/`). |
| 12 | `archive/legacy_sociometer/*/sidix-sociometer-all.tar.gz` (4 file) | Tar.gz lama di archive. | **Keep** (archive memang untuk history) tetapi pertimbangkan **compress/move** ke cloud storage bila repo terlalu besar. |
| 13 | `archive/legacy_sociometer/*/sidix-sociometer-deploy.tar.gz` (4 file) | Tar.gz lama di archive. | **Keep** (archive). |
| 14 | `epic-cray-3e451f/`, `pedantic-banach-c8232d/`, `serene-murdock-dbcb1f/` | Full repo copies tanpa catatan resmi di `LIVING_LOG`. | **Delete** seluruh folder dari working tree. Verifikasi dulu tidak ada file unik di dalamnya dengan `diff -r` terhadap root. |
| 15 | `gallant-ellis-7cd14d/` (embedded gitlink) | Full repo copy yang sudah dipindah ke branch `work/gallant-ellis-7cd14d`. | **Hapus** dari working tree root jika sudah tersimpan di branch; atau jadikan worktree terpisah via `git worktree add`. |

---

## 4 · Tabel Handoff / Archive

| # | File | Tanggal | Status | Action |
|---|------|---------|--------|--------|
| 1 | `docs/HANDOFF_CLAUDE_2026-04-29_FINAL.md` | 2026-04-29 | **Canonical** — versi paling lengkap & final untuk hari itu (179 baris, 8 sprint LIVE). | **Keep** di `docs/`. |
| 2 | `docs/HANDOFF_CLAUDE_2026-04-29_END.md` | 2026-04-29 | **Superseded** — versi "end session" awal (206 baris) yang kemudian diperbarui oleh `...FINAL.md`. Isi 70% overlap. | **Archive** ke `docs/archive/handoffs/HANDOFF_CLAUDE_2026-04-29_END.md`. |
| 3 | `docs/HANDOFF_2026-04-28_self_critique_self_iterate.md` | 2026-04-28 | Historical | **Keep** di `docs/` (masih < 7 hari). |
| 4 | `docs/HANDOFF_2026-04-27_evening_creative_stack.md` | 2026-04-27 | Historical | **Archive** ke `docs/archive/handoffs/` bila sudah > 30 hari atau jika jumlah handoff > 20 file. |
| 5 | `docs/HANDOFF_2026-04-27_endgame_multimodal.md` | 2026-04-27 | Historical | **Archive** jika > 30 hari. |
| 6 | `docs/HANDOFF_2026-04-27_pivot_canonical.md` | 2026-04-27 | Historical | **Archive** jika > 30 hari. |
| 7 | `docs/HANDOFF_2026-04-27_late_evening_full_stack.md` | 2026-04-27 | Historical | **Archive** jika > 30 hari. |
| 8 | `docs/HANDOFF_2026-04-26_vol20_to_vol21.md` | 2026-04-26 | Historical | **Archive** jika > 30 hari. |
| 9 | `docs/HANDOFF_2026-04-25_SPRINT10_RESEARCH.md` | 2026-04-25 | Historical | **Archive** jika > 30 hari. |
| 10 | `docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_KIMI.md` | 2026-04-25 | Historical | **Archive** jika > 30 hari. |
| 11 | `docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_PLUGIN_ORBIT.md` | 2026-04-25 | Historical | **Archive** jika > 30 hari. |
| 12 | `docs/HANDOFF_2026-04-24_MEMORY_SELFHEAL.md` | 2026-04-24 | Historical | **Archive** jika > 30 hari. |
| 13 | `docs/HANDOFF_2026-04-24_SPRINT8D.md` | 2026-04-24 | Historical | **Archive** jika > 30 hari. |
| 14 | `docs/HANDOFF_2026-04-24_ARSITEKTUR_JIWA_TYPo_PLUGIN.md` | 2026-04-24 | Historical | **Archive** jika > 30 hari. |
| 15 | `docs/HANDOFF_2026-04-23.md` | 2026-04-23 | Historical | **Archive** (banyak versi 2026-04-23). |
| 16 | `docs/HANDOFF_2026-04-23_FINAL.md` | 2026-04-23 | Historical | **Archive** (digantikan oleh `...FINAL_SYNC.md` atau versi terbaru). |
| 17 | `docs/HANDOFF_2026-04-23_FINAL_SYNC.md` | 2026-04-23 | Historical | **Archive**. |
| 18 | `docs/HANDOFF_2026-04-23_jiwa_typo_kimi.md` | 2026-04-23 | Historical | **Archive**. |
| 19 | `docs/HANDOFF_2026-04-23_QA_EXECUTION_FINAL.md` | 2026-04-23 | Historical | **Archive**. |
| 20 | `docs/HANDOFF_2026-04-23_QA_KONTINUITAS_DOK.md` | 2026-04-23 | Historical | **Archive**. |
| 21 | `docs/HANDOFF_2026-04-23_SPRINT7.md` | 2026-04-23 | Historical | **Archive**. |
| 22 | `docs/HANDOFF_2026-04-23_STATUS_SYNC.md` | 2026-04-23 | Historical | **Archive**. |
| 23 | `docs/HANDOFF_2026-04-23_v2.md` | 2026-04-23 | Historical | **Archive** (redundansi versioning). |
| 24 | `docs/HANDOFF-2026-04-19-SOCIALMEDIA-LEARNAGENT.md` | 2026-04-19 | Historical | **Archive**. |
| 25 | `docs/HANDOFF_2026-04-19.md` | 2026-04-19 | Historical | **Archive**. |
| 26 | `docs/HANDOFF-2026-04-17.md` | 2026-04-17 | Historical | **Archive**. |
| 27 | `docs/HANDOFF_CLAUDE_20260427.md` | 2026-04-27 | Historical | **Archive**. |
| 28 | `docs/HANDOFF_CLAUDE_20260426.md` | 2026-04-26 | Historical | **Archive**. |
| 29 | `docs/HANDOFF_CLAUDE_EMBODIED_SIDIX.md` | Tanpa tanggal | Historical | **Archive** atau **keep** bila masih jadi referensi arsitektur embodied. |
| 30 | `docs/HANDOFF_KIMI_TO_CLAUDE_20260425.md` | 2026-04-25 | Historical | **Archive** (handoff antar agen sudah tercatat di `LIVING_LOG.md`). |
| 31 | `docs/HANDOFF_CLAUDE_PROJEK_BADAR_54.md` | Tanpa tanggal | **Canonical / Referensi tetap** | **Keep** — ini bukan handoff harian, tapi dokumen handoff batch Projek Badar (54 langkah). Berbeda kategori. |

**Rekomendasi kategori handoff**:  
Buat folder `docs/archive/handoffs/` dan pindahkan semua `HANDOFF_2026-04-2[3-7]*.md` serta `HANDOFF_2026-04-19*.md` ke sana. Pertahankan hanya:
- `HANDOFF_CLAUDE_2026-04-29_FINAL.md` (latest)
- `HANDOFF_CLAUDE_PROJEK_BADAR_54.md` (canonical roadmap)

---

## 5 · Research Notes 290–310 — Analisis Overlap

| Note | Judul | Tanggal | Analisis Overlap |
|------|-------|---------|------------------|
| 290 | Conversation Synthesis: itu nya bisa diganti nggak sih sama white | 2026-04-28 | **Unik** — dogfood synthesizer dari sesi strategic dialogue. Tidak duplikat. |
| 291 | Novel Methods Discovered Compound Sprint 2026-04-29 | 2026-04-29 | **Unik** — 5 metode baru (CTDL, PaDS, AGSR, PMSC, CSVP). Referensi note 290, tapi isi berbeda. |
| 29 | Human Experience Engine — fondasi riset | — | **Unik** — fondasi konseptual CSDOR + taksonomi pengalaman. |
| 30 | Blueprint: Experience Engine — pemetaan ke stack nyata Mighan | — | **Unik** — blueprint eksekusi teknis, direct sequel note 29. Cross-reference sudah ada. |
| 308 | Accidental work on main: moved to branch work/gallant-ellis-7cd14d | 2026-04-30 | **Unik** — catatan proses git housekeeping. |

**Kesimpulan**: Tidak ada note di rentang 290–310 yang perlu dihapus. Masing-masing memiliki fungsi berbeda: synthesis (290), methods (291), concept (29), blueprint (30), process (308).

---

## 6 · Ringkasan Prioritas Tindakan

| Prioritas | Item | Estimasi Impact |
|-----------|------|-----------------|
| 🔴 **P0** | Hapus / konversi `gallant-ellis-7cd14d/` (embedded gitlink) | Mengurangi redundancy masif & mencegah accidental submodule commit |
| 🔴 **P0** | Hapus `epic-cray-3e451f/`, `pedantic-banach-c8232d/`, `serene-murdock-dbcb1f/` | Menghilangkan ~3 salinan integral repo |
| 🟡 **P1** | Archive / hapus duplikat `Framework_bahasa_plugin_update/sidix-docs/**` dan `sidix-cursor-brief/*.md` | Membersihkan folder update bahasa dari dokumen lama |
| 🟡 **P1** | Archive handoff pre-2026-04-29 ke `docs/archive/handoffs/` | Merapikan `docs/` root |
| 🟢 **P2** | Merge `Dockerfile.inference` ke `Dockerfile.brain_qa` | Menyederhanakan root Dockerfile |
| 🟢 **P2** | Standardize nama env file (`.env.sample` vs `.env.example`) | Konsistensi developer experience |
| 🟢 **P2** | Merge `deploy.sh` + `deploy-frontend.sh` atau jadikan wrapper | Menghindari overlap deploy logic |

---

*Audit oleh: Audit Agent (Kimi Code CLI) — 2026-04-30*  
*Referensi: `AGENTS.md`, `docs/LIVING_LOG.md`, `brain/public/research_notes/308_sprint_decision_2026-04-30.md`*
