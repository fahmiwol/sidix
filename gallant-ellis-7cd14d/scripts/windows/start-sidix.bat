@echo off
set "REPO=%~dp0..\.."
echo ============================================
echo  SIDIX — Start All Services
echo  Repo: %REPO%
echo ============================================
echo.

if not exist "%REPO%\apps\brain_qa\.venv\Scripts\python.exe" (
    echo ERROR: venv tidak ditemukan.
    echo Jalankan scripts\windows\install-brain_qa-venv.bat atau install-brain_qa-full.bat
    pause
    exit /b 1
)

if not exist "%REPO%\apps\brain_qa\.data\READY" (
    echo [!] Index belum ada. Membangun index dulu...
    cd /d "%REPO%\apps\brain_qa"
    .venv\Scripts\python.exe -m brain_qa index
    if %errorlevel% neq 0 (
        echo ERROR: Gagal build index.
        pause
        exit /b 1
    )
    echo Index selesai!
    echo.
)

if not exist "%REPO%\SIDIX_USER_UI\node_modules" (
    echo [!] node_modules belum ada. Install dulu...
    cd /d "%REPO%\SIDIX_USER_UI"
    npm install --silent
    echo.
)

echo [1/2] Menjalankan brain_qa serve (port 8765)...
start "SIDIX Backend" cmd /k "cd /d \"%REPO%\apps\brain_qa\" && .venv\Scripts\python.exe -m brain_qa serve"

timeout /t 2 /nobreak > nul

echo [2/2] Menjalankan SIDIX UI (port 3000)...
start "SIDIX Frontend" cmd /k "cd /d \"%REPO%\SIDIX_USER_UI\" && npm run dev"

timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo  SIDIX AKTIF
echo  Backend : http://localhost:8765
echo  UI      : http://localhost:3000
echo  API Docs: http://localhost:8765/docs
echo ============================================
echo.
echo Buka browser: http://localhost:3000
echo (Tekan Enter untuk buka di browser)
pause > nul
start "" "http://localhost:3000"
