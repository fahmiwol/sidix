# Sprint 9D — Admin Tab Workflows UI

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** admin-panel, workflows, sprint-9d, workflow-engine, ui  

## Konteks

Sprint 9D: Buat tab Workflows di MighanAdmin untuk mengelola workflow definitions dan runs dari workflow-engine.js. Apa saja fiturnya?

## Pengetahuan

Sprint 9D — Admin Tab Workflows (server/admin-panel/index.html):

LAYOUT: 4-KPI row + Def cards grid + Run panel (slide-in) + Recent Runs table + Run Detail

KPI ROW: Definisi (total defs dari /api/workflow-engine/defs), Total Run, Completed, Failed

WORKFLOW DEF CARDS (.wf-def-card):
- Nama + ID + trigger type
- Description (truncated 80 char)
- Step dots: colored per type — agent=cyan, service=purple, notify=green, wait=yellow + step count
- Last run status (colored: running=cyan, completed=green, failed=red, cancelled=muted)
- Tombol ▶ Run → openWfRunPanel()

RUN PANEL (slide-in, hidden by default):
- Header: nama def yang dipilih
- Context textarea (JSON, default {})
- Tombol Run → POST /api/workflow-engine/run → tampil runId + status
- Tombol Batal

RECENT RUNS TABLE (50 terakhir):
- runId (monospace), status (color), defName (cyan), started time, duration (ms/s), steps count
- Tombol Detail → showWfRunDetail()
- Tombol Cancel (hanya jika status=running) → POST /api/workflow-engine/runs/:id/cancel

RUN DETAIL PANEL (slide-in):
- Header: runId, status, defName, started
- Step log table: timestamp (HH:MM:SS), step id, type, status (color: ok/err/placeholder)
- Error message inline jika ada

FUNCTIONS: loadWorkflows, openWfRunPanel, closeWfRunPanel, runWorkflow, loadWfRuns, showWfRunDetail, cancelWfRun

API ENDPOINTS USED: GET /api/workflow-engine/defs, GET /api/workflow-engine/runs, POST /api/workflow-engine/run, GET /api/workflow-engine/runs/:id, POST /api/workflow-engine/runs/:id/cancel

---
*Diambil dari SIDIX MCP Knowledge Base*
