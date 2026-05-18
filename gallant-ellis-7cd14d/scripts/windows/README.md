# Skrip Windows (SIDIX)

Semua `.bat` untuk pengembangan lokal **Windows** berada di folder ini (bukan di root repo).

| Skrip | Fungsi |
|-------|--------|
| `install-brain_qa-venv.bat` | Buat/isi venv + `pip install -r requirements.txt` di `apps/brain_qa`. |
| `install-brain_qa-full.bat` | Seperti di atas + verifikasi rank-bm25 + index + `eval_qa.py`. |
| `install-agent-deps.bat` | Pasang `fastapi`, `uvicorn`, `httpx` di venv brain_qa. |
| `start-agent.bat` | `brain_qa serve` di port 8765. |
| `start-ui.bat` | Dev server UI (`SIDIX_USER_UI`). |
| `start-sidix.bat` | Backend + UI (dua jendela cmd). |
| `check-m4.bat` | Ringkasan index + stat QA + eval. |
| `run-m4-full.bat` | Eval + generate corpus QA. |
| `publish-all-drafts.bat` | Publish draft kurasi + reindex. |
| `cleanup-personal-corpus.bat` | Hapus path corpus “personal” (template) + reindex. |
| `startup-fetch.bat` | Jalankan `startup-fetch.py` dari root repo. |
| `setup-startup-fetch.bat` | Daftarkan Task Scheduler ke `startup-fetch.bat` (admin). |

Root repo dihitung dari lokasi skrip: `set REPO=%~dp0..\..` — pindahkan folder `scripts` hanya bersama seluruh repo.

**Migrasi dari nama lama:** `install-deps.bat` → `install-brain_qa-full.bat`; `install_deps.bat` → `install-brain_qa-venv.bat`.
