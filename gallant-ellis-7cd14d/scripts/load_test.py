"""
load_test.py — Task 34 (Saba / G5)
Load test ringan antrian inferensi SIDIX.
Hanya menggunakan stdlib: concurrent.futures, urllib.request, json, argparse, time, statistics.
"""

import argparse
import json
import statistics
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Payload default untuk load test
PAYLOAD_DEFAULT = {"question": "Apa itu SIDIX?"}


def satu_request(host: str, port: int, endpoint: str) -> Dict[str, Any]:
    """
    Kirim satu POST request ke endpoint SIDIX.
    Kembalikan dict berisi durasi dan status.
    """
    url = f"http://{host}:{port}{endpoint}"
    payload = json.dumps(PAYLOAD_DEFAULT).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t_mulai = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()  # Konsumsi body
            t_selesai = time.perf_counter()
            status_code = resp.status
            return {
                "ok": True,
                "status_code": status_code,
                "duration_ms": (t_selesai - t_mulai) * 1000,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        t_selesai = time.perf_counter()
        # 429 = rate limit — dianggap bukan error fatal
        is_rate_limit = (e.code == 429)
        return {
            "ok": False,
            "status_code": e.code,
            "duration_ms": (t_selesai - t_mulai) * 1000,
            "error": f"HTTP {e.code}",
            "rate_limited": is_rate_limit,
        }
    except urllib.error.URLError as e:
        t_selesai = time.perf_counter()
        return {
            "ok": False,
            "status_code": 0,
            "duration_ms": (t_selesai - t_mulai) * 1000,
            "error": str(e),
            "rate_limited": False,
        }


def hitung_persentil(data: List[float], pct: float) -> float:
    """Hitung nilai persentil dari list float."""
    if not data:
        return 0.0
    diurutkan = sorted(data)
    idx = int(len(diurutkan) * pct / 100)
    idx = min(idx, len(diurutkan) - 1)
    return diurutkan[idx]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load test ringan antrian inferensi SIDIX"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host SIDIX (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port SIDIX (default: 8765)")
    parser.add_argument(
        "--concurrent", type=int, default=5,
        help="Jumlah worker paralel (default: 5)"
    )
    parser.add_argument(
        "--total", type=int, default=20,
        help="Total request yang dikirim (default: 20)"
    )
    parser.add_argument(
        "--endpoint", default="/ask",
        help="Endpoint target (default: /ask)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print(f"[INFO] Target: http://{args.host}:{args.port}{args.endpoint}")
    print(f"[INFO] Total request: {args.total} | Workers paralel: {args.concurrent}")
    print("[INFO] Memulai load test...\n")

    semua_durasi: List[float] = []
    error_count = 0
    rate_limit_count = 0
    selesai_count = 0

    t_global_mulai = time.perf_counter()

    # Jalankan semua request dengan ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        futures = [
            executor.submit(satu_request, args.host, args.port, args.endpoint)
            for _ in range(args.total)
        ]

        for future in as_completed(futures):
            hasil = future.result()
            selesai_count += 1
            semua_durasi.append(hasil["duration_ms"])

            if hasil["ok"]:
                status_str = f"OK ({hasil['status_code']})"
            elif hasil.get("rate_limited"):
                status_str = "RATE_LIMIT (429)"
                rate_limit_count += 1
                error_count += 1
            else:
                status_str = f"GAGAL — {hasil['error']}"
                error_count += 1

            # Cetak progress setiap request selesai
            print(f"  [{selesai_count:>4}/{args.total}] {status_str} | {hasil['duration_ms']:.1f} ms")

    t_global_selesai = time.perf_counter()
    total_time_s = t_global_selesai - t_global_mulai

    # Hitung statistik
    sukses_durasi = [d for d in semua_durasi]  # semua request tercatat durasinya
    rps = args.total / total_time_s if total_time_s > 0 else 0
    p50 = hitung_persentil(sukses_durasi, 50)
    p95 = hitung_persentil(sukses_durasi, 95)
    mean_ms = statistics.mean(sukses_durasi) if sukses_durasi else 0

    # Ringkasan
    print("\n" + "=" * 50)
    print("RINGKASAN LOAD TEST")
    print("=" * 50)
    print(f"  Total request      : {args.total}")
    print(f"  Sukses             : {args.total - error_count}")
    print(f"  Error              : {error_count}")
    print(f"    - Rate limit 429 : {rate_limit_count}")
    print(f"  Total waktu        : {total_time_s:.2f} s")
    print(f"  Throughput (RPS)   : {rps:.2f} req/s")
    print(f"  Latensi Mean       : {mean_ms:.1f} ms")
    print(f"  Latensi P50        : {p50:.1f} ms")
    print(f"  Latensi P95        : {p95:.1f} ms")
    print("=" * 50)
