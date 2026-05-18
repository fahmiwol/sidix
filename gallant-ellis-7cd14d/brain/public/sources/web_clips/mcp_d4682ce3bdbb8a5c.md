# Sprint 9E — NPC Lifecycle + Agent-Linked Outdoor NPCs

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** outdoor, npc, lifecycle, animation, three-js, sprint-9e  

## Konteks

Sprint 9E: Tambah leg/arm animation, time-aware lifecycle, dan agent-linked NPCs ke OutdoorWorld.js. Apa yang diubah?

## Pengetahuan

Sprint 9E — OutdoorWorld.js NPC Lifecycle:

1. LEG/ARM ANIMATION:
- _makePedestrianGroup restructured: legs/arms sekarang pivot Groups bukan plain meshes
- legLGroup/legRGroup position.set(-0.06, 0.48, 0) — hip pivot point
- legMesh.position.set(0, -0.175, 0) — mesh offset dari pivot
- armLGroup/armRGroup di shoulder (y=0.86)
- Stored in userData: legL, legR, armL, armR
- Walk animation: ud.legL.rotation.x = sin(time * speed * 10) * 0.45 (legs alternate)
- Arms swing opposite: armL = -sin() * 0.25
- Idle animation: ud.armL.rotation.x = sin(time * 1.2) * 0.05 (gentle sway)

2. TIME-AWARE LIFECYCLE:
- _getWibHour() → wall clock UTC+7 float (14.5 = 14:30)
- _getNpcLifecyclePhase() → 7 fases: morning_rush(7-9), work_morning(9-12), lunch(12-13), work_afternoon(13-17), evening_rush(17-19), evening(19-21), night(21-7)
- _lifecycleTick refresh setiap 5s:
  * night: hide 60% non-agent NPCs (based on seed hash)
  * morning/evening rush: speedMul = 1.5
  * night: speedMul = 0.6
  * other: speedMul = 1.0

3. AGENT-LINKED NPCs (_spawnAgentNPCs):
- 8 named staff: Sari(cyan), Budi(blue), Dewi(purple), Reza(green), Rina(orange), Profesor(gold), Iris(pink), Hafiz(teal)
- Shirt color = role color with higher emissiveIntensity (0.7 vs 0.45)
- Scale = ps * 1.05 (slightly taller than pedestrians)
- Spread radially (evenly spaced in a ring)
- Larger wander range (±12 vs ±15 road, ±4 park)
- Longer pause (2-8s vs 1-4s)
- Stored in agentNpcMap[agentId] + npcLabel in userData
- updateAgentNpc(agentId, {speed, visible}) API

4. getDebugSnapshot() expansion:
- Added: agentNpcs count, lifecycle phase, wibHour

---
*Diambil dari SIDIX MCP Knowledge Base*
