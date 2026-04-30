@echo off
set "REPO=%~dp0..\.."
set "FETCH_BAT=%~dp0startup-fetch.bat"
:: Setup Windows Task Scheduler untuk SIDIX Auto-Knowledge Fetcher
:: Jalankan sekali saja sebagai Administrator

echo.
echo ================================================
echo   Setup: SIDIX Auto-Knowledge Fetcher
echo   Target: %FETCH_BAT%
echo ================================================
echo.

schtasks /delete /tn "SIDIX-StartupFetch" /f 2>nul

schtasks /create ^
  /tn "SIDIX-StartupFetch" ^
  /tr "\"%FETCH_BAT%\"" ^
  /sc ONLOGON ^
  /delay 0003:00 ^
  /rl HIGHEST ^
  /f

if %ERRORLEVEL% == 0 (
    echo.
    echo [OK] Task "SIDIX-StartupFetch" berhasil dibuat!
    echo      Akan berjalan 3 menit setelah login.
    echo.
    echo Untuk test sekarang:
    echo   schtasks /run /tn "SIDIX-StartupFetch"
    echo.
) else (
    echo.
    echo [ERROR] Gagal membuat task.
    echo Coba jalankan script ini sebagai Administrator.
    echo.
    echo Manual: Task Scheduler ^> Action ^> Program: %FETCH_BAT%
)

echo.
pause
