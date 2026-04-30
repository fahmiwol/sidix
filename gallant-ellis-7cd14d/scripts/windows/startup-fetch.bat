@echo off
set "REPO=%~dp0..\.."
echo.
echo ================================================
echo   SIDIX Knowledge Fetcher — Auto Startup
echo   Repo: %REPO%
echo ================================================
echo.

cd /d "%REPO%"

if exist "apps\brain_qa\.venv\Scripts\python.exe" (
    set PYTHON=apps\brain_qa\.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

echo Python: %PYTHON%
echo.

%PYTHON% startup-fetch.py --max 10 --category ALL

echo.
echo Startup fetch selesai!
echo.
