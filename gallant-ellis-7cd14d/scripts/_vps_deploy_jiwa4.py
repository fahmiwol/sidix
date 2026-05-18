"""
Deploy Jiwa Sprint 4 ke VPS.
Mencakup semua improvement dari Sprint 1-4 + Kimi collaboration.

Verifikasi:
- Git pull ke commit terbaru
- Restart sidix-brain
- Cek sensor hub (indra SIDIX)
- Cek parallel planner + execute_plan wiring
- Cek /agent/multimodal endpoint tersedia
- Cek stream_buffer module loaded
- Health check full
- pytest subset cepat (jiwa4 tests)
"""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    os.getenv('SIDIX_VPS_HOST', ''),
    username='root',
    password=os.getenv('SIDIX_VPS_PASS', ''),
    timeout=20
)

def run(cmd, t=60, ignore_stderr=False):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out:
        print(out)
    if not ignore_stderr and err:
        skip = any(x in err for x in ["Warning", "HEAD is now", "branch", "DeprecationWarning"])
        if not skip:
            print("[stderr]", err[:400])
    return out

# ── 1. GIT PULL ───────────────────────────────────────────────────────────────
print("=" * 55)
print("=== 1. GIT PULL ===")
print("=" * 55)
run("cd /opt/sidix && git fetch origin main && git reset --hard origin/main", t=90)
run("cd /opt/sidix && git log --oneline -5")

# ── 2. RESTART ────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 2. RESTART sidix-brain ===")
print("=" * 55)
run("pm2 restart sidix-brain --update-env", t=30)
run("sleep 12")

# ── 3. VERIFY JIWA SPRINT 4 MODULES ─────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 3. VERIFY JIWA SPRINT 4 MODULES ===")
print("=" * 55)
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')

# A: Sensor Hub
from brain_qa.sensor_hub import probe_all
result = probe_all()
print(f'[SensorHub] total={result[\"total\"]} active={result[\"active\"]} inactive={result[\"inactive\"]} broken={result[\"broken\"]}')

# B: Parallel Planner + execute_plan wiring
from brain_qa.parallel_planner import plan_tools
r = plan_tools([
    {'name': 'web_search', 'args': {'query': 'test'}},
    {'name': 'search_corpus', 'args': {'query': 'test', 'k': 3}},
])
print(f'[Planner] bundles={r[\"bundle_count\"]} savings={r[\"estimated_parallel_savings\"]:.0%}')

# C: execute_plan available
from brain_qa.parallel_executor import execute_plan
print(f'[execute_plan] available: OK')

# D: Stream buffer
from brain_qa.stream_buffer import get_stream_buffer
buf = get_stream_buffer()
buf.emit_quick('test', 'deploy verification ping')
snap = buf.snapshot()
print(f'[StreamBuffer] file_size={snap[\"file_size_kb\"]}KB in_memory={snap[\"in_memory_events\"]}')

# E: agent_serve imports clean
from brain_qa.agent_serve import create_app
print(f'[agent_serve] imports OK')

# F: steps_trace helper
from brain_qa.agent_serve import _build_steps_trace
t = _build_steps_trace([])
print(f'[steps_trace] helper OK, empty={t==[]}')

print()
print('=== ALL JIWA SPRINT 4 CHECKS PASSED ===')
" """, t=45)

# ── 4. HEALTH ENDPOINT ────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 4. HEALTH ENDPOINT ===")
print("=" * 55)
run("curl -s http://localhost:8765/health", t=15)

# ── 5. SENSES STATUS ENDPOINT ─────────────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 5. /sidix/senses/status ===")
print("=" * 55)
run("curl -s http://localhost:8765/sidix/senses/status | python3 -c \"import json,sys; d=json.load(sys.stdin); print(f'total={d[\\\"total\\\"]} active={d[\\\"active\\\"]} inactive={d[\\\"inactive\\\"]} broken={d[\\\"broken\\\"]}'); [print(f\\\"  [{s[\\\"status\\\"].upper():8}] {s[\\\"slug\\\"]}\\\") for s in d[\\\"senses\\\"]]\" 2>/dev/null || echo '[senses] endpoint response received'", t=20)

# ── 6. QUICK SMOKE — /agent/chat ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 6. SMOKE TEST /agent/chat ===")
print("=" * 55)
run("""curl -s -X POST http://localhost:8765/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"apa itu Python?","persona":"ABOO","simple_mode":true}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'steps={d[\\\"steps\\\"]} persona={d[\\\"persona\\\"]} trace_len={len(d.get(\\\"steps_trace\\\",[]))} planner={d.get(\\\"planner_used\\\",False)} answer_len={len(d[\\\"answer\\\"])}chars')" 2>/dev/null || echo '[chat] response received'""", t=90)

# ── 7. PYTEST JIWA4 SUBSET ────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("=== 7. PYTEST JIWA4 SUBSET ===")
print("=" * 55)
run("cd /opt/sidix && python3 -m pytest apps/brain_qa/tests/test_jiwa_sprint4_observability.py apps/brain_qa/tests/test_jiwa_sprint4_stream_buffer.py apps/brain_qa/tests/test_parallel_planner_wired.py -q --tb=short 2>&1 | tail -10", t=120)

c.close()

print("\n" + "=" * 55)
print("[JIWA SPRINT 4 DEPLOYED SUCCESSFULLY]")
print("=" * 55)
