#!/usr/bin/env python3
"""
qa_tool_audit.py — Audit semua 92 tools SIDIX untuk beta readiness
====================================================================
Usage: python scripts/qa_tool_audit.py

Output:
  - OK: tool callable, tidak crash
  - GRACEFUL: tool return fallback (env tidak di-set) — acceptable
  - BROKEN: tool crash dengan error tak terduga
  - IMPORT: tool gagal import (module missing / syntax error)
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

# Add apps/brain_qa to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "brain_qa"))

def main():
    print("=" * 60)
    print("SIDIX Beta Tool Audit")
    print("=" * 60)

    try:
        from brain_qa.agent_tools import TOOL_REGISTRY, call_tool, ToolResult
        tools = list(TOOL_REGISTRY.keys())
        print(f"Total tools: {len(tools)}\n")
    except Exception as e:
        print(f"[FAIL] Cannot import TOOL_REGISTRY: {e}")
        traceback.print_exc()
        return 1

    results = {"ok": [], "graceful": [], "broken": [], "import_err": []}

    for name in sorted(tools):
        spec = TOOL_REGISTRY[name]
        # Build minimal args (all strings with placeholder)
        args = {}
        for p in spec.params:
            if p in ("query", "question", "text", "code", "message", "topic", "content", "problem", "prompt", "description"):
                args[p] = "test"
            elif p == "expression":
                args[p] = "2 + 2"
            elif p in ("url", "path", "file_path"):
                args[p] = "https://example.com/test.jpg"
            elif p == "output_path":
                args[p] = "test_output.json"
            elif p in ("k", "limit", "max_files", "per_page", "duration_seconds", "n", "max_depth", "depth", "timeout"):
                args[p] = 5
            elif p in ("folder_id", "file_id", "chunk_id", "voice_id", "account"):
                args[p] = "test_id"
            elif p == "persona":
                args[p] = "INAN"
            elif p == "model":
                args[p] = "qwen2.5"
            elif p == "lang":
                args[p] = "id"
            elif p in ("category", "status"):
                args[p] = "test"
            elif p in ("allow_restricted",):
                args[p] = False
            elif p in ("sources", "entries", "accounts", "files"):
                args[p] = []
            elif p in ("body", "data", "payload"):
                args[p] = {}
            elif p == "platform":
                args[p] = "reddit"
            elif p == "base_colors":
                args[p] = ["#3B82F6", "#10B981"]
            elif p == "archetype":
                args[p] = "everyman"
            elif p == "brand_name":
                args[p] = "TestBrand"
            elif p == "niche":
                args[p] = "coffee"
            elif p == "framework":
                args[p] = "pytest"
            elif p == "template":
                args[p] = "fastapi"
            elif p == "posts_per_week":
                args[p] = 3
            elif p == "budget_usd":
                args[p] = 100
            elif p == "duration_days":
                args[p] = 7
            elif p == "platforms":
                args[p] = ["instagram"]
            elif p == "pair_type":
                args[p] = "copy_vs_strategy"
            elif p == "html":
                args[p] = "<html><body>test</body></html>"
            elif p == "tolerance":
                args[p] = 0.1
            elif p == "session_id":
                args[p] = "qa_test"
            elif p == "step":
                args[p] = 1
            else:
                args[p] = "test"

        try:
            result = call_tool(
                tool_name=name,
                args=args,
                session_id="qa_audit",
                step=0,
                allow_restricted=True,
            )
            if result.success:
                results["ok"].append(name)
                status = "OK"
            elif result.error and ("tidak di-set" in result.error.lower() or
                                   "not set" in result.error.lower() or
                                   "wajib diisi" in result.error.lower() or
                                   "fallback" in result.error.lower() or
                                   "belum di-set" in result.error.lower()):
                results["graceful"].append(name)
                status = "GRACEFUL"
            else:
                results["broken"].append((name, result.error))
                status = "BROKEN"
        except Exception as e:
            err = str(e)
            if "ModuleNotFoundError" in err or "ImportError" in err or "cannot import" in err:
                results["import_err"].append((name, err))
                status = "IMPORT"
            else:
                results["broken"].append((name, err))
                status = "BROKEN"

        print(f"  [{status}] {name}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  OK       : {len(results['ok'])} tools")
    print(f"  GRACEFUL : {len(results['graceful'])} tools (env missing — acceptable)")
    print(f"  BROKEN   : {len(results['broken'])} tools (need fix)")
    print(f"  IMPORT   : {len(results['import_err'])} tools (module missing)")
    print(f"  TOTAL    : {len(tools)} tools")

    if results["broken"]:
        print("\n  BROKEN TOOLS:")
        for name, err in results["broken"]:
            print(f"    - {name}: {err[:120]}")

    if results["import_err"]:
        print("\n  IMPORT ERRORS:")
        for name, err in results["import_err"]:
            print(f"    - {name}: {err[:120]}")

    # Save report
    report_path = Path("scripts/qa_tool_audit_report.json")
    report_path.write_text(json.dumps({
        "ok": results["ok"],
        "graceful": results["graceful"],
        "broken": [{"name": n, "error": e} for n, e in results["broken"]],
        "import_err": [{"name": n, "error": e} for n, e in results["import_err"]],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Report saved: {report_path}")

    return 0 if not results["broken"] and not results["import_err"] else 1


if __name__ == "__main__":
    exit(main())
