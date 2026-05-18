═══════════════════════════════════════════════════════════
TASK CARD: A2A Phase 2 + Code Canvas MVP + MCP stdio transport

WHAT (1 kalimat konkret):
Implementasi 3 sprint paralel: A2AServer (menerima task eksternal), Code Canvas MVP (edit+run code di split-pane), dan MCP stdio transport (desktop integration Claude Desktop/Cursor).

WHY:
- Visi mapping: Pencipta (Code Canvas) + Cognitive (A2A interoperability) + Iteratif (MCP desktop bridge)
- Sprint context: BACKLOG "Sprint Product Layer — Mode System + Built-in Apps + MCP Full" + "A2A Phase 2-4"
- Founder request: "lanjut semua sprint" (continue all sprints)
- Coverage shift: Pencipta 60%→75%, Cognitive 85%→90%, Product differentiation ++

ACCEPTANCE (verifiable):
1. A2AServer: POST /a2a/tasks/send menerima task, proses via existing brain_qa, return task artifact. SSE streaming /a2a/tasks/sendSubscribe.
2. Code Canvas: Split-pane UI di frontend, Monaco-like editor (textarea+highlight), Run button → POST /app/code/run → code_sandbox → output panel. Multi-file tab support.
3. MCP stdio: Script `mcp_stdio_server.py` yang baca stdin JSON-RPC 2.0, panggil mcp_server_wrap.execute_tool(), tulis stdout. Bisa di-connect ke Claude Desktop via config.

PLAN (7 step konkret):
1. A2AServer: Buat `apps/brain_qa/brain_qa/a2a_server.py` — Task, Message, Artifact models + /tasks/send + /tasks/sendSubscribe SSE + /tasks/get + /tasks/cancel. Wire ke run_react.
2. A2AServer: Tambah endpoint di `agent_serve.py` — router prefix /a2a/* dengan CORS.
3. Code Canvas Backend: Buat `apps/brain_qa/brain_qa/app_code_canvas.py` — POST /app/code/run (wrap code_sandbox), POST /app/code/debug (error analysis), GET /app/code/history/{id}.
4. Code Canvas Frontend: Tambah panel kanan di `index.html` + `main.ts` — split-pane toggle, textarea editor dengan syntax highlight (Prism.js CDN), run button, output panel.
5. MCP stdio: Buat `apps/brain_qa/brain_qa/mcp_stdio_server.py` — baca line dari stdin, parse JSON-RPC, dispatch ke mcp_server_wrap, write response line ke stdout.
6. Integration test: py_compile semua file baru, build frontend, smoke test endpoint.
7. Commit + deploy: git commit → push → VPS deploy → smoke test.

RISKS:
- A2A spec evolving (Google belum final) → mitigation: implement subset core (tasks/send, tasks/get, artifacts) yang stabil.
- Code Canvas Monaco bundle besar → mitigation: gunakan textarea + Prism.js highlight sementara, Monaco di Phase 2.
- MCP stdio Windows PowerShell encoding → mitigation: set PYTHONIOENCODING=utf-8, test di VPS Linux.
═══════════════════════════════════════════════════════════
