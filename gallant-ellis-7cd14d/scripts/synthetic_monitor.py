"""
synthetic_monitor.py — Task 44 (Al-Inshiqaq / G5)
Synthetic monitor uptime endpoint SIDIX.
Hanya menggunakan stdlib: urllib.request, json, argparse, time, datetime, signal, sys.

Mode:
- Default: loop setiap --interval detik, graceful Ctrl-C
- --once: satu ping lalu exit 0 (ok) atau 1 (down) — untuk CI/cron
"""

import argparse
import datetime
import json
import signal
import sys
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


# Flag global untuk menangani Ctrl-C secara graceful
_berjalan = True


def tangani_sinyal(signum, frame):
    """Handler Ctrl-C / SIGTERM untuk graceful shutdown."""
    global _berjalan
    print("\n[INFO] Menerima sinyal berhenti. Menghentikan monitor...")
    _berjalan = False


def ping_health(host: str, port: int) -> Dict[str, Any]:
    """
    Kirim GET ke /health dan catat status, latensi, dan model_ready.
    Kembalikan dict hasil ping.
    """
    url = f"http://{host}:{port}/health"
    req = urllib.request.Request(url, method="GET")

    t_mulai = time.perf_counter()
    timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            t_selesai = time.perf_counter()
            latency_ms = (t_selesai - t_mulai) * 1000

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}

            # Ambil model_ready dari berbagai kemungkinan key
            model_ready = (
                data.get("model_ready")
                or data.get("model_loaded")
                or data.get("ready")
                or (resp.status == 200)
            )

            return {
                "timestamp": timestamp,
                "status": "ok",
                "latency_ms": round(latency_ms, 2),
                "model_ready": bool(model_ready),
                "http_status": resp.status,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        t_selesai = time.perf_counter()
        latency_ms = (t_selesai - t_mulai) * 1000
        return {
            "timestamp": timestamp,
            "status": "down",
            "latency_ms": round(latency_ms, 2),
            "model_ready": False,
            "http_status": e.code,
            "error": f"HTTP {e.code}: {e.reason}",
        }
    except urllib.error.URLError as e:
        t_selesai = time.perf_counter()
        latency_ms = (t_selesai - t_mulai) * 1000
        return {
            "timestamp": timestamp,
            "status": "down",
            "latency_ms": round(latency_ms, 2),
            "model_ready": False,
            "http_status": 0,
            "error": str(e.reason) if hasattr(e, "reason") else str(e),
        }


def append_jsonl(path_log: str, data: Dict[str, Any]) -> None:
    """Append satu baris JSON ke file JSONL."""
    with open(path_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def cetak_ringkasan(hasil: Dict[str, Any], iterasi: int) -> None:
    """Print ringkasan satu ping ke stdout."""
    status_icon = "UP" if hasil["status"] == "ok" else "DOWN"
    model_str = "ready" if hasil["model_ready"] else "not-ready"
    err_str = f" | Error: {hasil['error']}" if hasil["error"] else ""
    print(
        f"[{hasil['timestamp']}] #{iterasi:>4} | {status_icon} | "
        f"{hasil['latency_ms']:.1f} ms | model={model_str}{err_str}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthetic monitor uptime endpoint /health SIDIX"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host SIDIX (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port SIDIX (default: 8765)")
    parser.add_argument(
        "--interval", type=float, default=60.0,
        help="Interval ping dalam detik (default: 60)"
    )
    parser.add_argument(
        "--log", default=None,
        help="Path file JSONL untuk append log (opsional)"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Jalankan satu ping lalu exit 0 (ok) atau 1 (down)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Daftarkan handler sinyal untuk graceful Ctrl-C
    signal.signal(signal.SIGINT, tangani_sinyal)
    signal.signal(signal.SIGTERM, tangani_sinyal)

    target = f"http://{args.host}:{args.port}/health"

    if args.once:
        # Mode CI/cron: satu ping, exit segera
        print(f"[INFO] Mode --once | Target: {target}")
        hasil = ping_health(args.host, args.port)
        cetak_ringkasan(hasil, 1)
        if args.log:
            append_jsonl(args.log, hasil)
        sys.exit(0 if hasil["status"] == "ok" else 1)

    # Mode loop
    print(f"[INFO] Memulai synthetic monitor | Target: {target}")
    print(f"[INFO] Interval: {args.interval}s | Log: {args.log or 'tidak disimpan'}")
    print("[INFO] Tekan Ctrl-C untuk berhenti.\n")

    iterasi = 0
    while _berjalan:
        iterasi += 1
        hasil = ping_health(args.host, args.port)
        cetak_ringkasan(hasil, iterasi)

        if args.log:
            try:
                append_jsonl(args.log, hasil)
            except OSError as e:
                print(f"[WARN] Gagal menulis log: {e}")

        # Tunggu interval, tapi cek _berjalan setiap detik agar Ctrl-C responsif
        if _berjalan:
            for _ in range(int(args.interval)):
                if not _berjalan:
                    break
                time.sleep(1)
            # Sisa fraksi detik
            sisa = args.interval - int(args.interval)
            if sisa > 0 and _berjalan:
                time.sleep(sisa)

    print("[INFO] Monitor dihentikan.")
