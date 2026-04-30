#!/bin/bash
# Quick validation test untuk Fase 6 (curriculum + skills + opsec masking)

echo "=== SKILLS DISCOVER ==="
curl -s -X POST http://localhost:8765/sidix/skills/discover \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("discovered:", d.get("discovered_count")); [print(" -", s["skill_id"], ":", s["category"]) for s in d.get("skills", [])[:10]]'

echo ""
echo "=== SKILLS LIST (vision category) ==="
curl -s "http://localhost:8765/sidix/skills?category=vision" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("count:", len(d.get("skills",[]))); [print(" -", s["skill_id"]) for s in d.get("skills",[])[:10]]'

echo ""
echo "=== HEALTH MASKING CHECK ==="
curl -s http://localhost:8765/health \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("llm_providers leaked:", "llm_providers" in d); print("ollama leaked:", "ollama" in d); print("internal_mentor_pool:", d.get("internal_mentor_pool")); print("sidix_local_engine:", d.get("sidix_local_engine")); print("model_mode:", d.get("model_mode"))'

echo ""
echo "=== HARVEST DATASET (corpus_qa.jsonl, 50 samples) ==="
curl -s -X POST "http://localhost:8765/sidix/skills/harvest-dataset?jsonl_path=/opt/sidix/brain/datasets/corpus_qa.jsonl&max_samples=50" \
  | python3 -m json.tool

echo ""
echo "=== LORA STATUS (after harvest) ==="
curl -s http://localhost:8765/sidix/lora/status \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("total_pairs:", d.get("total_pairs"), "| ready:", d.get("ready_for_upload"), "| files:", len(d.get("files",[])))'

echo ""
echo "=== EXECUTE TODAY LESSON (will trigger research) ==="
echo "(skipped — heavy, takes ~50s. Trigger manually if needed.)"
