# -*- coding: utf-8 -*-
"""
api_cost_dashboard.py — Dashboard biaya API pihak ketiga (Task 46, G5)
Surah Ash-Sharh (#94) — Luruskan satu rantai sanad/sumber untuk jawaban sensitif.

Menampilkan ringkasan biaya token dari log SIDIX.
Untuk model lokal, biaya = 0. Berguna bila ada rencana fallback ke API pihak ketiga.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# Harga estimasi per 1K token (USD) — update sesuai tarif aktual
_COST_TABLE = {
    "mock": {"input": 0.0, "output": 0.0},
    "local_lora": {"input": 0.0, "output": 0.0},     # model sendiri = gratis
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}

_DEFAULT_LOG = Path(__file__).parent.parent / "apps" / "brain_qa" / ".data" / "token_usage.jsonl"


def _load_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = _COST_TABLE.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])


def _format_number(n: int | float) -> str:
    if isinstance(n, float):
        return f"${n:.6f}"
    return f"{n:,}"


def generate_dashboard(entries: list[dict], since_days: int | None = None) -> dict:
    """Hasilkan ringkasan biaya dari daftar log entry."""
    now = datetime.now(timezone.utc)
    filtered = []
    for e in entries:
        if since_days is not None:
            ts_str = e.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if (now - ts).days > since_days:
                        continue
                except Exception:
                    pass
        filtered.append(e)

    total_input = sum(e.get("input_tokens", 0) for e in filtered)
    total_output = sum(e.get("output_tokens", 0) for e in filtered)
    total_cost = sum(
        _cost_usd(e.get("model", "mock"), e.get("input_tokens", 0), e.get("output_tokens", 0))
        for e in filtered
    )

    # Breakdown per feature
    by_feature: dict[str, dict] = {}
    for e in filtered:
        feat = e.get("feature", "unknown")
        if feat not in by_feature:
            by_feature[feat] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        by_feature[feat]["calls"] += 1
        by_feature[feat]["input_tokens"] += e.get("input_tokens", 0)
        by_feature[feat]["output_tokens"] += e.get("output_tokens", 0)
        by_feature[feat]["cost_usd"] += _cost_usd(
            e.get("model", "mock"), e.get("input_tokens", 0), e.get("output_tokens", 0)
        )

    # Breakdown per model
    by_model: dict[str, dict] = {}
    for e in filtered:
        model = e.get("model", "mock")
        if model not in by_model:
            by_model[model] = {"calls": 0, "cost_usd": 0.0}
        by_model[model]["calls"] += 1
        by_model[model]["cost_usd"] += _cost_usd(
            model, e.get("input_tokens", 0), e.get("output_tokens", 0)
        )

    return {
        "period_days": since_days,
        "total_entries": len(filtered),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "total_cost_usd": round(total_cost, 8),
        "by_feature": by_feature,
        "by_model": by_model,
    }


def print_dashboard(summary: dict) -> None:
    """Cetak dashboard ke stdout."""
    period = f"{summary['period_days']} hari terakhir" if summary["period_days"] else "semua waktu"
    print("=" * 56)
    print(f"  SIDIX API Cost Dashboard — {period}")
    print("=" * 56)
    print(f"  Total request    : {summary['total_entries']:,}")
    print(f"  Input tokens     : {summary['total_input_tokens']:,}")
    print(f"  Output tokens    : {summary['total_output_tokens']:,}")
    print(f"  Total tokens     : {summary['total_tokens']:,}")
    print(f"  Estimasi biaya   : ${summary['total_cost_usd']:.6f} USD")
    print()

    if summary["by_model"]:
        print("  Per Model:")
        for model, data in sorted(summary["by_model"].items(), key=lambda x: -x[1]["cost_usd"]):
            print(f"    {model:<24} {data['calls']:>6} calls  ${data['cost_usd']:.6f}")
        print()

    if summary["by_feature"]:
        print("  Per Fitur:")
        for feat, data in sorted(summary["by_feature"].items(), key=lambda x: -x[1]["cost_usd"]):
            print(
                f"    {feat:<20} {data['calls']:>6} calls  "
                f"{data['input_tokens']:,}+{data['output_tokens']:,} tok  "
                f"${data['cost_usd']:.6f}"
            )
        print()

    if summary["total_cost_usd"] == 0.0:
        print("  ℹ️  Biaya $0 — SIDIX berjalan dengan model lokal (own-stack).")
    print("=" * 56)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dashboard biaya token API SIDIX (Task 46 — G5)"
    )
    parser.add_argument(
        "--log",
        default=str(_DEFAULT_LOG),
        help=f"Path ke token_usage.jsonl (default: {_DEFAULT_LOG})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Filter N hari terakhir (default: semua waktu)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output sebagai JSON (untuk integrasi monitoring)",
    )
    args = parser.parse_args(argv)

    log_path = Path(args.log)
    entries = _load_log(log_path)

    if not entries:
        print(f"[INFO] Tidak ada log token ditemukan di: {log_path}")
        print("[INFO] Log akan muncul setelah token_cost.py mulai merekam penggunaan.")
        # Tampilkan dashboard kosong
        entries = []

    summary = generate_dashboard(entries, since_days=args.days)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_dashboard(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
