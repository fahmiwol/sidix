# SIDIX full stack — start-sidix.bat + SSE streaming + auto-reindex

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** sidix, start-bat, sse-streaming, auto-reindex, full-stack  

## Konteks

Apa saja yang dibangun untuk SIDIX stack lengkap setelah baca semua file?

## Pengetahuan

1. start-sidix.bat di D:\MIGHAN Model — satu klik start backend (port 8765) + frontend (port 3000), auto-check index dan node_modules. 2. serve.py — auto-reindex background setelah upload .md/.txt (threading, _trigger_reindex_background). 3. serve.py — endpoint POST /ask/stream (SSE), POST /corpus/reindex, GET /corpus/reindex/status. 4. api.ts — askStream() SSE client + triggerReindex() + getReindexStatus(). 5. main.ts — handleSend pakai askStream (streaming bubble real-time). Stack: brain_qa Python FastAPI (port 8765) + SIDIX_USER_UI Vite/TS (port 3000). Index: 173 chunks. Cara start: double-click start-sidix.bat → browser auto-buka localhost:3000.

---
*Diambil dari SIDIX MCP Knowledge Base*
