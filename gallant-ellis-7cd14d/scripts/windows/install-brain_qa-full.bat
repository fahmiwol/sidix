@echo off
set "REPO=%~dp0..\.."
echo ============================================
echo  SIDIX brain_qa — Install Dependencies (full)
echo  Repo: %REPO%
echo ============================================
echo.

cd /d "%REPO%\apps\brain_qa"

echo [1/4] Install requirements.txt ke venv...
.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install gagal.
    pause
    exit /b 1
)
echo.

echo [2/4] Verifikasi rank-bm25...
.venv\Scripts\python.exe -c "from rank_bm25 import BM25Okapi; print('rank_bm25 OK: BM25Okapi ready')"
if %errorlevel% neq 0 (
    echo ERROR: rank_bm25 masih tidak bisa diimport.
    pause
    exit /b 1
)
echo.

echo [3/4] Re-index corpus...
.venv\Scripts\python.exe -m brain_qa index
if %errorlevel% neq 0 (
    echo WARNING: index gagal, tapi dependency sudah terpasang.
    pause
    exit /b 1
)
echo Index sukses!
echo.

echo [4/4] Evaluasi QA pairs (M3 check)...
.venv\Scripts\python.exe eval_qa.py
echo.

echo ============================================
echo  SELESAI — SIDIX brain_qa M3 pipeline aktif
echo ============================================
echo.
echo Perintah berikutnya:
echo   python -m brain_qa ask "Apa itu RAG?" --k 5
echo   python -m brain_qa qa
echo   python -m brain_qa status
echo.
pause
