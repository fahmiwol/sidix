@echo off
set "REPO=%~dp0..\.."
echo Installing SIDIX Agent Runtime dependencies...
cd /d "%REPO%\apps\brain_qa"

if exist ".venv\Scripts\pip.exe" (
    .venv\Scripts\pip.exe install fastapi uvicorn httpx
) else (
    pip install fastapi uvicorn httpx
)

echo.
echo Done! Test server dengan:
echo   cd "%REPO%\apps\brain_qa"
echo   .venv\Scripts\python -m brain_qa serve --port 8765
echo.
pause
