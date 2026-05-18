# IMPLEMENTATION PLAN: SIDIX-SocioMeter

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Execution Plan

---

## SPRINT OVERVIEW (24 Minggu)

| Sprint | Fokus | ETA | Status |
|--------|-------|-----|--------|
| 7 | Foundation + Wire Maqashid/Naskh + MCP Server | Week 1-2 | 🔥 NOW |
| 8 | Chrome Extension MVP | Week 3-4 | Planned |
| 9 | Jariyah Harvesting Loop | Week 5-6 | Planned |
| 10 | Dashboard Semrawut + Privacy | Week 7-8 | Planned |
| 11 | Distribution (hub MCP, Chrome Web Store) | Week 9-10 | Planned |
| 12 | Multimodal F1 (Qwen2.5-VL) | Week 11-12 | Planned |
| 13 | Creative F2 (FLUX) | Week 13-14 | Planned |
| 14 | Video F3 (CogVideo) | Week 15-16 | Planned |
| 15 | 3D F4 (Hunyuan3D) | Week 17-18 | Planned |
| 16 | Code F5 (CodeQwen) | Week 19-20 | Planned |
| 17 | Swarm F6 (Campaign auto) | Week 21-22 | Planned |
| 18 | v1.0 Launch | Week 23-24 | Planned |

---

## SPRINT 7 — DETAIL (Sekarang)

### Day 1-2: Wire Maqashid
- Patch `run_react()`: add `maqashid_check` parameter
- `detect_mode(question, persona)` → auto-select mode
- `evaluate_maqashid()` → retry if fail → tag output
- Test: 50 creative PASS + 20 harmful BLOCK

### Day 3-4: Wire Naskh
- Patch `learn_agent.py`: add `naskh.resolve()` before `store_corpus()`
- Handle: accept / merge / conflict / reject
- Preserve `is_frozen` items

### Day 5-7: MCP Server Foundation
- Create `brain/sociometer/` directory structure
- `mcp_server.py`: FastMCP instance, 6 tools
- `connectors/stdio.py`: MCP stdio transport

### Day 8-10: Integration
- `test_sprint7.py`: Maqashid(30) + Naskh(20) + MCP(15)
- `/metrics` endpoint
- `LIVING_LOG.md` update

---

## DEFINITION OF DONE

Sprint selesai jika:
1. ✅ Code complete
2. ✅ Unit test coverage ≥ 80%
3. ✅ Integration test passed
4. ✅ Maqashid benchmark: 50 creative PASS, 20 harmful BLOCK
5. ✅ Documentation updated
6. ✅ Code review approved
7. ✅ Staging deploy + smoke test

---

## RESOURCE REQUIREMENTS

| Komponen | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| GPU | RTX 3060 12GB | RTX 4090 24GB |
| Storage | 100 GB SSD | 500 GB NVMe |
| Network | 10 Mbps | 100 Mbps |
