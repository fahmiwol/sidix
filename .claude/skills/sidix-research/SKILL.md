---
name: sidix-research
description: Invoke SIDIX brain via /agent/chat_holistic untuk multi-source research (jurus seribu bayangan). Pakai saat butuh insight kompleks dari multiple perspective sebelum eksekusi sprint atau diskusi visi.
---

# SIDIX Research Skill

SIDIX brain punya endpoint `/agent/chat_holistic` yang fan-out paralel ke web + corpus + dense_index + 5-persona research + tools. Output = synthesis ringkas dengan attribution.

Pakai ini untuk:
- Riset visi besar bos sebelum eksekusi sprint
- Cross-check decision dengan SIDIX corpus + web sources
- Multi-perspective insight (5 persona angle simultan)
- Self-eating dogfood: SIDIX bantu bangun SIDIX (Phase 1 Self-Bootstrap)

## Cara Pakai

User: `/sidix-research [pertanyaan kompleks]`

Saya invoke via Bash:

```bash
ssh sidix-vps "curl -s --max-time 200 -X POST http://localhost:8765/agent/chat_holistic \
  -H 'Content-Type: application/json' \
  -d '{\"question\":\"[QUERY]\"}' \
  -o /tmp/sidix_research.json && \
  python3 -c 'import json; d=json.load(open(\"/tmp/sidix_research.json\")); \
    print(d.get(\"answer\",\"\")[:2000]); \
    print(); print(\"sources_used:\", d.get(\"sources_used\")); \
    print(\"latency:\", d.get(\"duration_ms\"))'"
```

(Atau langsung curl kalau VPS access dari local Claude Code working directory.)

## Output Yang Diberikan ke User

- Answer synthesis (max 2000 char)
- Sources used (yang berhasil)
- Latency
- Note tentang RunPod state kalau ada error

## Kapan Dipakai

✅ **Pakai saat**:
- Visi kompleks butuh multi-perspective (5 persona)
- Sprint planning yang butuh research backing
- Cross-verify klaim sebelum dokumentasi

⊘ **Skip saat**:
- Pertanyaan simple yang Claude Code bisa jawab langsung dengan grep/read
- Pertanyaan tentang state proyek (pakai `/sidix-state`)
- Pertanyaan teknis tentang implementation detail (baca code)

## Cost Awareness

Per call ~30-130s + RunPod compute. Tidak boros — pakai saat genuine multi-perspective needed.

## Reference

- `apps/brain_qa/brain_qa/multi_source_orchestrator.py` (Sprint Α)
- `apps/brain_qa/brain_qa/cognitive_synthesizer.py`
- Endpoint: `https://ctrl.sidixlab.com/agent/chat_holistic`
