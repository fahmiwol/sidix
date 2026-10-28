#!/usr/bin/env python3
"""
sprint_l_cron.py — Sprint L Background Cron
============================================

Jalankan via crontab di VPS:
  0 6 * * * /opt/sidix/venv/bin/python /opt/sidix/apps/brain_qa/scripts/sprint_l_cron.py

Tasks:
  1. Foresight Radar (setiap hari jam 06:00)
  2. Self-improvement proposal (setiap Senin jam 06:00)
  3. Error registry analysis (setiap 3 hari)

Usage:
  python sprint_l_cron.py                    # run all tasks
  python sprint_l_cron.py --task radar       # only foresight radar
  python sprint_l_cron.py --task proposal    # only self-improvement proposal
  python sprint_l_cron.py --task errors      # only error analysis
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Setup sys.path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("sidix.sprint_l_cron")


def _get_llm_fn():
    """Get LLM function for text generation."""
    try:
        from apps.brain_qa.brain_qa.ollama_llm import ollama_generate
        return lambda p: ollama_generate(p, max_tokens=800)
    except Exception:
        try:
            from brain_qa.ollama_llm import ollama_generate
            return lambda p: ollama_generate(p, max_tokens=800)
        except Exception as e:
            log.warning("LLM unavailable for Sprint L cron: %s", e)
            return None


def run_foresight_radar():
    """Jalankan Foresight Radar — fetch RSS + detect weak signals."""
    log.info("=== SPRINT L2: Foresight Radar ===")
    try:
        from apps.brain_qa.brain_qa.foresight_radar import run_radar_cycle
        llm_fn = _get_llm_fn()
        result = run_radar_cycle(llm_fn=llm_fn)
        log.info("Radar result: %d signals, %d drafts in %.1fs",
                 result.get("signals_detected", 0),
                 result.get("drafts_created", 0),
                 result.get("duration_s", 0))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        log.error("Foresight Radar failed: %s", e)
        return False


def run_error_analysis():
    """Analisis pola error → proposal."""
    log.info("=== SPRINT L1: Error Pattern Analysis ===")
    try:
        from apps.brain_qa.brain_qa.error_registry import analyze_patterns, get_error_stats
        stats = get_error_stats()
        log.info("Error stats: %s", stats)
        if stats.get("total", 0) < 3:
            log.info("Belum cukup error untuk analisis (total=%d)", stats.get("total", 0))
            return True
        llm_fn = _get_llm_fn()
        result = analyze_patterns(llm_fn=llm_fn)
        log.info("Error analysis: %d proposals generated", len(result.get("proposal", {}).get("proposals", [])))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        log.error("Error analysis failed: %s", e)
        return False


def run_self_improvement_proposal():
    """Generate self-improvement proposal holistic."""
    log.info("=== SPRINT L1: Self-Improvement Proposal ===")
    try:
        from apps.brain_qa.brain_qa.self_modifier import generate_improvement_proposal
        llm_fn = _get_llm_fn()
        result = generate_improvement_proposal(llm_fn=llm_fn)
        n_proposals = len(result.get("proposals", []))
        log.info("Generated proposal %s with %d suggestions", result.get("id"), n_proposals)
        if n_proposals:
            for p in result.get("proposals", []):
                log.info("  P%d: %s [%s]", p.get("priority", "?"), p.get("title", "?"), p.get("effort", "?"))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        log.error("Self-improvement proposal failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="SIDIX Sprint L Cron")
    parser.add_argument("--task", choices=["radar", "errors", "proposal", "all"], default="all")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).isoformat()
    log.info("Sprint L Cron started at %s, task=%s", ts, args.task)

    results = {}

    if args.task in ("all", "radar"):
        results["radar"] = run_foresight_radar()

    if args.task in ("all", "errors"):
        results["errors"] = run_error_analysis()

    if args.task in ("all", "proposal"):
        results["proposal"] = run_self_improvement_proposal()

    ok = all(results.values())
    log.info("Sprint L Cron done: %s", results)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
