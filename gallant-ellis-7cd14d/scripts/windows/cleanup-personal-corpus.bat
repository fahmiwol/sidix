@echo off
set "REPO=%~dp0..\.."
echo Cleaning personal data from SIDIX corpus...
echo Repo: %REPO%
echo.

set "BASE=%REPO%\brain\public"

if not exist "%BASE%" (
    echo ERROR: %BASE% tidak ditemukan.
    pause
    exit /b 1
)

rmdir /s /q "%BASE%\portfolio" 2>nul
rmdir /s /q "%BASE%\projects" 2>nul
rmdir /s /q "%BASE%\roadmap" 2>nul

del /q "%BASE%\sources\mighan-projects-overview.md" 2>nul
del /q "%BASE%\research_notes\01_riset_awal_mighan_brain_1.md" 2>nul
del /q "%BASE%\research_notes\02_research_queue.md" 2>nul
del /q "%BASE%\glossary\01_glossary_template.md" 2>nul
del /q "%BASE%\research_notes\00_research_note_template.md" 2>nul
del /q "%BASE%\research_notes\00_template_contested_topic.md" 2>nul
del /q "%BASE%\README.md" 2>nul

echo Done! Personal files removed (paths that existed).
echo.
echo Reindexing corpus...
cd /d "%REPO%\apps\brain_qa"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m brain_qa index
) else (
    python -m brain_qa index
)
echo.
echo Corpus cleaned and reindexed!
pause
