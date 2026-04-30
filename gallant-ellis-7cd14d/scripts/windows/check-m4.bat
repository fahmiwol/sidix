@echo off
set "REPO=%~dp0..\.."
echo ============================================
echo  SIDIX — M4 Evaluation Report
echo  Repo: %REPO%
echo ============================================
echo.

cd /d "%REPO%\apps\brain_qa"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: venv tidak ditemukan. Jalankan install-brain_qa-full.bat atau install-brain_qa-venv.bat
    pause
    exit /b 1
)

echo [1/3] Status index corpus...
.venv\Scripts\python.exe -c "
import json, os
meta = '.data/index_meta.json'
if os.path.exists(meta):
    d = json.load(open(meta))
    print(f'  Chunks terindex : {d.get(\"chunk_count\", \"?\")}')
    print(f'  Source docs     : {d.get(\"doc_count\", \"?\")}')
    print(f'  Built at        : {d.get(\"built_at\", \"?\")}')
else:
    print('  index_meta.json tidak ditemukan — jalankan: python -m brain_qa index')
"
echo.

echo [2/3] QA Pairs stats...
.venv\Scripts\python.exe -c "
import json, os
qa_file = '../../brain/datasets/qa_pairs.jsonl'
if os.path.exists(qa_file):
    pairs = [json.loads(l) for l in open(qa_file, encoding='utf-8') if l.strip()]
    tags = {}
    for p in pairs:
        for t in p.get('tags', []):
            tags[t] = tags.get(t, 0) + 1
    print(f'  Total QA pairs  : {len(pairs)}')
    top_tags = sorted(tags.items(), key=lambda x: -x[1])[:5]
    print(f'  Top tags        : {top_tags}')
else:
    print('  qa_pairs.jsonl tidak ditemukan')
"
echo.

echo [3/3] Jalankan evaluasi QA (hit@k)...
.venv\Scripts\python.exe eval_qa.py --k 5 --threshold 0.12 --verbose
echo.

echo [BONUS] Cek hasil tersimpan di...
if exist ".data\qa_eval_result.json" (
    .venv\Scripts\python.exe -c "
import json
r = json.load(open('.data/qa_eval_result.json'))
print(f'  Hit rate        : {r.get(\"hit_rate\", \"?\"):.1%}')
print(f'  Passed          : {r.get(\"passed\", \"?\")} / {r.get(\"total\", \"?\")}')
print(f'  M3 checklist OK : {r.get(\"m3_ok\", \"?\")}')
"
) else (
    echo   .data/qa_eval_result.json belum ada
)

echo.
echo ============================================
echo  M4 check selesai.
echo ============================================
pause
