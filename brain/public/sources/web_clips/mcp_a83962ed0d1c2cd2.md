# Git workflow Mighantect — cara push yang benar dari Windows

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** git, workflow, windows, powershell, troubleshooting  

## Konteks

Cara push git yang benar di Mighantect 3D, dan kenapa git add -A sering bermasalah?

## Pengetahuan

GIT WORKFLOW MIGHANTECT — WAJIB DARI POWERSHELL WINDOWS:

MASALAH git add -A:
- Mighan-tasks/opencode/ = submodule tanpa commit → error "does not have a commit checked out"
- .claude/worktrees/ = embedded git repo → warning "adding embedded git repository"
- Solusi: JANGAN pakai git add -A, stage file secara spesifik

CARA BENAR:
1. Set-Location D:\Mighan
2. npm run verify (pastikan semua OK dulu)
3. git add file1 file2 folder/ (spesifik)
4. git commit -m "feat: ..."
5. git push

FILE TIDAK BOLEH DI-COMMIT:
- server/settings.json (API keys)
- server/.data/ (runtime: events, inbox, agent-settings, canvas-projects)
- .claude/worktrees/ (internal Claude Code)
- Mighan-tasks/opencode/ (submodule rusak)
- .env files

PATTERN ERROR UMUM:
- "not a git repository" → belum Set-Location D:\Mighan
- "does not have a commit checked out" → ada submodule bermasalah → pakai git add spesifik
- "Everything up-to-date" di push tanpa commit → git add belum berhasil, periksa git status

---
*Diambil dari SIDIX MCP Knowledge Base*
