@echo off
chcp 65001 >nul
set "REPO=%~dp0..\.."
echo ========================================
echo   SIDIX brain_qa — Install Dependencies (venv only)
echo   Repo: %REPO%
echo ========================================
echo.

cd /d "%REPO%\apps\brain_qa"

if not exist ".venv\Scripts\pip.exe" (
    echo [!] Virtual env tidak ditemukan. Membuat baru...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python tidak ditemukan. Install Python 3.10+ dulu.
        pause
        exit /b 1
    )
)

echo [1/2] Mengaktifkan venv...
call .venv\Scripts\activate.bat

echo [2/2] Install semua dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  SUKSES! Dependencies terinstall.
    echo  Untuk index + eval lengkap jalankan: install-brain_qa-full.bat
    echo ========================================
) else (
    echo [ERROR] pip install gagal.
)
echo.
pause
