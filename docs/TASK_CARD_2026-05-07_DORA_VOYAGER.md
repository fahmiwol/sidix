═══════════════════════════════════════════════════════════
TASK CARD: Persona DoRA Adapter + Voyager Protocol Phase 1

WHAT (1 kalimat konkret):
Implementasi 2 sprint paralel: Persona DoRA Adapter (dynamic persona switching via LoRA weights) dan Voyager Protocol Phase 1 (dynamic tool creator — SIDIX generates Python tools from natural language).

WHY:
- Visi mapping: Cognitive (DoRA — model adaptation) + Iteratif (Voyager — self-improving toolset)
- Sprint context: BACKLOG next sprints + FOUNDER_IDEA_LOG "SIDIX harus standing alone"
- Founder request: "lanjut, catat, analisa, iterasi, QA, review, testing, catat, recap"
- Coverage shift: Cognitive 95%→98%, Self-Bootstrap Phase 2→3

ACCEPTANCE (verifiable):
1. DoRA Adapter: POST /agent/generate dengan persona parameter → load LoRA adapter spesifik persona (AYMAN/ABOO/OOMAR/ALEY/UTZ) → output sesuai karakter persona. Fallback ke base model kalau adapter tidak ada.
2. Voyager P1: POST /app/voyager/create — input: natural language intent → generate Python tool code → AST security scan → whitelist import check → save ke workspace → register ke TOOL_REGISTRY → return tool name + code.

PLAN (8 step konkret):
1. DoRA Adapter: Buat `apps/brain_qa/brain_qa/dora_adapter.py` — load/switch LoRA adapters per persona, adapter registry, fallback logic.
2. DoRA Adapter: Update `local_llm.py` generate_sidix() untuk support persona-specific adapter loading.
3. DoRA Adapter: Update `agent_serve.py` — persona parameter propagation ke generate endpoint.
4. Voyager P1: Buat `apps/brain_qa/brain_qa/voyager_protocol.py` — intent parser, code generator (generate_sidix), AST scanner, whitelist checker.
5. Voyager P1: Update `agent_tools.py` — dynamic TOOL_REGISTRY registration, `call_tool()` support untuk generated tools.
6. Voyager P1: Tambah endpoint POST /app/voyager/create + GET /app/voyager/tools di agent_serve.py.
7. Integration test: py_compile semua backend, build frontend, smoke test endpoint.
8. Commit + deploy ke VPS.

RISKS:
- DoRA adapter files belum ada — mitigation: buat stub adapter (copy base adapter 5x dengan config berbeda), atau implementasi logical switch dulu (system prompt + temperature).
- Voyager generated code security — mitigation: AST scan strict + whitelist import + forbidden pattern scanner (reuse code_sandbox security).
═══════════════════════════════════════════════════════════
