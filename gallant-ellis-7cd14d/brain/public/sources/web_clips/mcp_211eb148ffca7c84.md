# kaggle-dataset-upload-cli

**Sumber:** claude-code  
**Tanggal:** 2026-04-17  
**Tags:** kaggle, dataset, cli, upload, fine-tuning  

## Konteks

Cara upload file ke Kaggle dataset dan update notebook ke versi terbaru

## Pengetahuan

Upload dataset baru ke Kaggle via CLI (bukan browser):

1. Siapkan folder dengan file + dataset-metadata.json
2. dataset-metadata.json: {"title":"...", "id":"owner/slug", "licenses":[{"name":"unknown"}]}
3. Jalankan: kaggle datasets version -p <folder> -m "pesan"
4. Kaggle CLI ada di venv: apps/brain_qa/.venv/Scripts/kaggle.exe
5. Credentials di: C:/Users/ASUS/.kaggle/kaggle.json

Setelah upload, update notebook:
- Buka notebook → DATASETS panel → klik ... pada dataset → "Check for updates" → klik "Update"

PENTING: Kaggle path dataset di notebook = /kaggle/input/<slug>/ (BUKAN /kaggle/input/datasets/<owner>/<slug>/)
Jangan hardcode path — gunakan glob auto-detect.

---
*Diambil dari SIDIX MCP Knowledge Base*
