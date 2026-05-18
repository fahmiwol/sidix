@echo off
set "REPO=%~dp0..\.."
echo Starting SIDIX User Interface...
echo.
echo Backend harus sudah jalan di: http://localhost:8765
echo UI akan buka di: http://localhost:3000
echo.
cd /d "%REPO%\SIDIX_USER_UI"

if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

npm run dev
pause
