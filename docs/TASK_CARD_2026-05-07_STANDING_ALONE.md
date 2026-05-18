═══════════════════════════════════════════════════════════
TASK CARD: Standing Alone Sprint — Framework + A2AClient + Studio + Notebook + Auto-Tune

WHAT (1 kalimat konkret):
Implementasi 5 sprint paralel yang memperkuat SIDIX sebagai sistem mandiri: Built-in Apps Framework (artifact lifecycle), A2A Phase 3 (orkestrasi eksternal), Document Studio (editor), Data Notebook (visualisasi), dan Maqashid Auto-Tune (self-evaluation).

WHY:
- Visi mapping: Pencipta (framework + studio + notebook) + Cognitive (A2A orkestrasi) + Iteratif (auto-tune)
- Sprint context: BACKLOG "Sprint Product Layer — next sprints" + FOUNDER_IDEA_LOG "SIDIX harus standing alone"
- Founder request: "built tools sendiri, build logic dan orkestrasi sendiri, MCP sendiri"
- Coverage shift: Pencipta 75%→90%, Cognitive 90%→95%, Self-Bootstrap Phase 1→2

ACCEPTANCE (verifiable):
1. Built-in Apps Framework: POST /app/artifact/create, /app/artifact/{id}/pin, /app/artifact/{id}/export, /app/artifact/list — artifact lifecycle unified.
2. A2A Phase 3: A2AClient bisa discover external agent via AgentCard, kirim task, terima artifact — orkestrasi multi-agent.
3. Document Studio: Frontend panel TipTap (CDN) untuk rich text editing — bold, italic, heading, list, table, sanad citation.
4. Data Notebook: Frontend panel render structured data sebagai sortable table + ECharts (CDN) bar/line/pie dari markdown table AI output.
5. Maqashid Auto-Tune: Middleware di agent_serve.py yang auto-score output dengan maqashid_profiles.py, inject warning ke response kalau score rendah.

PLAN (10 step konkret):
1. Built-in Apps Framework: Buat `apps/brain_qa/brain_qa/app_framework.py` — Artifact model, CRUD, pin, export (md/json/html). Wire ke agent_serve.py.
2. A2A Phase 3: Buat `apps/brain_qa/brain_qa/a2a_client.py` — discover external AgentCard, send task, poll/get result. Wire ke agent_tools.py sebagai tool baru.
3. Document Studio: `index.html` + `main.ts` — TipTap CDN integration, panel kanan untuk document editing, toolbar WYSIWYG.
4. Data Notebook: `index.html` + `main.ts` — parse markdown table dari AI output, render sebagai HTML table sortable, ECharts visualization.
5. Maqashid Auto-Tune: `apps/brain_qa/brain_qa/maqashid_auto_tune.py` — wrapper yang evaluate output sebelum return ke user, inject correction suggestion.
6. Wire semua endpoint baru ke `agent_serve.py`.
7. Frontend: `api.ts` — tambah fungsi untuk artifact, studio, notebook.
8. Integration test: py_compile semua backend, build frontend, smoke test endpoint.
9. Commit + deploy ke VPS.
10. Update BACKLOG + LIVING_LOG.

RISKS:
- A2A Phase 3 butuh external agent untuk test → mitigation: buat mock AgentCard endpoint di local untuk test.
- TipTap + ECharts CDN bisa fail offline → mitigation: fallback ke textarea + plain table.
- Maqashid evaluation bisa lambat → mitigation: async background, jangan block response.
═══════════════════════════════════════════════════════════
