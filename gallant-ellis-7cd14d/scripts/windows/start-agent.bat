@echo off
set "REPO=%~dp0..\.."
echo Starting SIDIX Inference Engine...
echo.
echo Endpoints:
echo   http://localhost:8765/health
echo   http://localhost:8765/docs
echo   http://localhost:8765/agent/chat
echo   http://localhost:8765/agent/tools
echo.
cd /d "%REPO%\apps\brain_qa"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m brain_qa serve --port 8765
) else (
    python -m brain_qa serve --port 8765
)
pause
