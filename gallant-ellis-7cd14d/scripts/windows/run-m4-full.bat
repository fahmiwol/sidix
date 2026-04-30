@echo off
set "REPO=%~dp0..\.."
echo ============================================
echo  SIDIX — M4 Full Run
echo  (Eval + Generate Corpus QA for M5)
echo  Repo: %REPO%
echo ============================================
echo.

cd /d "%REPO%\apps\brain_qa"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: venv tidak ditemukan. Jalankan install-brain_qa-venv.bat
    pause
    exit /b 1
)

echo [1/3] Evaluasi QA pairs (retrieval quality)...
.venv\Scripts\python.exe eval_qa.py --k 5 --threshold 0.12 --verbose
echo.

echo [2/3] Generate corpus QA untuk M5 fine-tune prep...
.venv\Scripts\python.exe generate_corpus_qa.py
echo.

echo [3/3] Tampilkan status index...
.venv\Scripts\python.exe -c "import json,os; d=json.load(open('.data/index_meta.json')) if os.path.exists('.data/index_meta.json') else {}; print('  Chunks      :', d.get('chunk_count','?')); print('  Chunk chars :', d.get('chunk_chars','?')); print('  Corpus root :', d.get('root','?'))"
echo.

echo ============================================
echo  SELESAI. File output:
echo  brain\datasets\corpus_qa.jsonl
echo  brain\datasets\finetune_sft.jsonl
echo  apps\brain_qa\.data\qa_eval_result.json
echo ============================================
pause
