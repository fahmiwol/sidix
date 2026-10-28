"""
token_cost.py — Profil biaya token per fitur (Task 38, G5)
Surah Al-Qamar (#54) — Perbaiki pesan error yang membingungkan.

Menghitung perkiraan biaya token untuk tiap fitur SIDIX.
Bukan billing sistem — ini estimasi internal untuk monitoring & optimisasi.

Catatan terminologi pesan error:
  - Gunakan nama field yang eksplisit saat KeyError/ValueError
  - Sertakan nilai aktual dan nilai yang diharapkan di pesan error
  - Contoh baik : "Model 'xyz' tidak dikenal. Model tersedia: local, mock, api_gpt4o"
  - Contoh buruk : "Invalid model"
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .paths import default_data_dir

# ---------------------------------------------------------------------------
# Konfigurasi biaya per 1 000 token (USD)
# Format: { model_id: {"input": float, "output": float} }
# ---------------------------------------------------------------------------
COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    # Model lokal / mock — tidak ada biaya API
    "local": {"input": 0.0, "output": 0.0},
    "local_lora": {"input": 0.0, "output": 0.0},
    "mock": {"input": 0.0, "output": 0.0},
    # OpenAI GPT-4o (harga referensi Mei 2024, cek ulang sebelum produksi)
    "api_gpt4o": {"input": 0.03, "output": 0.06},
    # OpenAI GPT-4o-mini
    "api_gpt4o_mini": {"input": 0.00015, "output": 0.0006},
    # Anthropic Claude Sonnet 4 (estimasi)
    "api_claude_sonnet": {"input": 0.003, "output": 0.015},
}

_DEFAULT_LOG_FILENAME = "token_usage.jsonl"


# ---------------------------------------------------------------------------
# Dataclass utama
# ---------------------------------------------------------------------------
@dataclass
class TokenUsage:
    """Satu catatan pemakaian token untuk sebuah fitur / permintaan."""

    feature: str
    """Nama fitur SIDIX, contoh: 'ask', 'reindex', 'agent_react'."""

    input_tokens: int
    """Jumlah token pada prompt / input."""

    output_tokens: int
    """Jumlah token pada respons / output."""

    model: str
    """ID model, harus ada di COST_PER_1K_TOKENS atau 'unknown'."""

    timestamp: str
    """ISO-8601 UTC, contoh: '2026-04-17T08:30:00+00:00'."""

    @staticmethod
    def now_iso() -> str:
        """Kembalikan timestamp UTC sekarang dalam format ISO-8601."""
        return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Fungsi estimasi & kalkulasi
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """
    Estimasi jumlah token dari teks.

    Heuristik sederhana: 1 token ≈ 4 karakter.
    Cukup untuk monitoring internal — bukan pengganti tokenizer resmi.

    Args:
        text: Teks yang akan diestimasi.

    Returns:
        Perkiraan jumlah token (minimal 1).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def calculate_cost(usage: TokenUsage) -> float:
    """
    Hitung biaya USD berdasarkan usage dan model.

    Args:
        usage: Objek TokenUsage berisi jumlah token dan model.

    Returns:
        Biaya dalam USD (float). Kembalikan 0.0 jika model tidak dikenal.

    Pesan error yang jelas:
        Jika model tidak ada di COST_PER_1K_TOKENS, log peringatan dan
        kembalikan 0.0 — jangan raise exception supaya monitoring tidak berhenti.
    """
    rates = COST_PER_1K_TOKENS.get(usage.model)
    if rates is None:
        # Pesan eksplisit: sebutkan model yang tidak dikenal dan daftar yang tersedia
        known = ", ".join(sorted(COST_PER_1K_TOKENS.keys()))
        import warnings
        warnings.warn(
            f"[token_cost] Model '{usage.model}' tidak dikenal — biaya dihitung 0.0. "
            f"Model tersedia: {known}",
            stacklevel=2,
        )
        return 0.0

    input_cost = (usage.input_tokens / 1_000) * rates["input"]
    output_cost = (usage.output_tokens / 1_000) * rates["output"]
    return round(input_cost + output_cost, 8)


# ---------------------------------------------------------------------------
# Logging ke file JSONL
# ---------------------------------------------------------------------------

def _default_log_path() -> Path:
    """Kembalikan path log default: <data_dir>/token_usage.jsonl."""
    return default_data_dir() / _DEFAULT_LOG_FILENAME


def record_usage(
    usage: TokenUsage,
    log_path: Optional[str] = None,
) -> None:
    """
    Catat satu TokenUsage ke file JSONL (append).

    Setiap baris adalah JSON object lengkap termasuk field `cost_usd`.
    File dan direktori dibuat otomatis jika belum ada.

    Args:
        usage:    Data pemakaian token.
        log_path: Path ke file JSONL. Jika None, pakai default_data_dir().
    """
    path = Path(log_path) if log_path else _default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    record = asdict(usage)
    record["cost_usd"] = calculate_cost(usage)

    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_usage_log(log_path: str) -> list[TokenUsage]:
    """
    Baca file JSONL log dan kembalikan list TokenUsage.

    Baris yang tidak valid (JSON rusak, field hilang) dilewati dengan peringatan
    — supaya satu baris korup tidak mematikan seluruh pembacaan log.

    Args:
        log_path: Path ke file JSONL.

    Returns:
        List TokenUsage yang berhasil diparsing.
    """
    import warnings

    path = Path(log_path)
    if not path.exists():
        return []

    usages: list[TokenUsage] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                usages.append(
                    TokenUsage(
                        feature=str(data["feature"]),
                        input_tokens=int(data["input_tokens"]),
                        output_tokens=int(data["output_tokens"]),
                        model=str(data["model"]),
                        timestamp=str(data["timestamp"]),
                    )
                )
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                warnings.warn(
                    f"[token_cost] Baris {lineno} di '{log_path}' tidak valid "
                    f"dan dilewati. Detail: {exc}",
                    stacklevel=2,
                )
    return usages


# ---------------------------------------------------------------------------
# Ringkasan & laporan
# ---------------------------------------------------------------------------

def summarize_usage(usages: list[TokenUsage]) -> dict:
    """
    Buat ringkasan dari list TokenUsage.

    Returns dict berisi:
        total_input_tokens  : int
        total_output_tokens : int
        total_tokens        : int
        total_cost_usd      : float
        record_count        : int
        breakdown_by_feature: dict[feature_name, {
            input_tokens, output_tokens, total_tokens, cost_usd, count
        }]
        breakdown_by_model  : dict[model_name, {
            input_tokens, output_tokens, total_tokens, cost_usd, count
        }]
    """
    total_in = 0
    total_out = 0
    total_cost = 0.0
    by_feature: dict[str, dict] = {}
    by_model: dict[str, dict] = {}

    for u in usages:
        cost = calculate_cost(u)
        total_in += u.input_tokens
        total_out += u.output_tokens
        total_cost += cost

        # Breakdown per fitur
        f = by_feature.setdefault(u.feature, {
            "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "cost_usd": 0.0, "count": 0,
        })
        f["input_tokens"] += u.input_tokens
        f["output_tokens"] += u.output_tokens
        f["total_tokens"] += u.input_tokens + u.output_tokens
        f["cost_usd"] = round(f["cost_usd"] + cost, 8)
        f["count"] += 1

        # Breakdown per model
        m = by_model.setdefault(u.model, {
            "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "cost_usd": 0.0, "count": 0,
        })
        m["input_tokens"] += u.input_tokens
        m["output_tokens"] += u.output_tokens
        m["total_tokens"] += u.input_tokens + u.output_tokens
        m["cost_usd"] = round(m["cost_usd"] + cost, 8)
        m["count"] += 1

    return {
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "total_cost_usd": round(total_cost, 8),
        "record_count": len(usages),
        "breakdown_by_feature": by_feature,
        "breakdown_by_model": by_model,
    }


def format_cost_report(summary: dict) -> str:
    """
    Format ringkasan biaya menjadi teks yang mudah dibaca manusia.

    Args:
        summary: Output dari summarize_usage().

    Returns:
        String multi-baris berisi laporan biaya.
    """
    lines: list[str] = [
        "=" * 56,
        "  LAPORAN BIAYA TOKEN SIDIX",
        "=" * 56,
        f"  Total rekaman     : {summary['record_count']:>10,}",
        f"  Token input       : {summary['total_input_tokens']:>10,}",
        f"  Token output      : {summary['total_output_tokens']:>10,}",
        f"  Token total       : {summary['total_tokens']:>10,}",
        f"  Biaya total (USD) : ${summary['total_cost_usd']:>12.6f}",
        "",
        "  Rincian per Fitur:",
        "  " + "-" * 54,
    ]

    for feature, data in sorted(summary["breakdown_by_feature"].items()):
        lines.append(
            f"  {feature:<22} | "
            f"{data['total_tokens']:>8,} tok | "
            f"${data['cost_usd']:>10.6f} | "
            f"{data['count']:>5} req"
        )

    lines += [
        "",
        "  Rincian per Model:",
        "  " + "-" * 54,
    ]

    for model, data in sorted(summary["breakdown_by_model"].items()):
        lines.append(
            f"  {model:<22} | "
            f"{data['total_tokens']:>8,} tok | "
            f"${data['cost_usd']:>10.6f} | "
            f"{data['count']:>5} req"
        )

    lines.append("=" * 56)
    return "\n".join(lines)
