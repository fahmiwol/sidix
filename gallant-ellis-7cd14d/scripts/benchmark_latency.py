"""
benchmark_latency.py — Task 30 (Saba / G5)
Benchmark latensi jawaban endpoint /ask di SIDIX.
Hanya menggunakan stdlib: urllib.request, json, argparse, statistics, time.
"""

import argparse
import json
import statistics
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any

# Pertanyaan default jika tidak ada file JSON yang diberikan
PERTANYAAN_DEFAULT = [
    "Apa itu kecerdasan buatan?",
    "Jelaskan konsep machine learning secara singkat.",
    "Apa perbedaan antara supervised dan unsupervised learning?",
    "Bagaimana cara kerja neural network?",
    "Apa itu natural language processing?",
]


def kirim_pertanyaan(host: str, port: int, pertanyaan: str) -> Dict[str, Any]:
    """
    Kirim POST ke /ask dan ukur durasi end-to-end.
    Kembalikan dict berisi jawaban dan duration_ms.
    """
    url = f"http://{host}:{port}/ask"
    payload = json.dumps({"question": pertanyaan}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t_mulai = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            t_selesai = time.perf_counter()
            duration_ms = (t_selesai - t_mulai) * 1000
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body}
            return {"ok": True, "duration_ms": duration_ms, "data": data}
    except urllib.error.URLError as e:
        t_selesai = time.perf_counter()
        duration_ms = (t_selesai - t_mulai) * 1000
        return {"ok": False, "duration_ms": duration_ms, "error": str(e)}


def hitung_statistik(durasi_list: List[float]) -> Dict[str, float]:
    """Hitung min, max, mean, dan p95 dari list durasi (ms)."""
    if not durasi_list:
        return {"min": 0, "max": 0, "mean": 0, "p95": 0}
    diurutkan = sorted(durasi_list)
    # Hitung persentil ke-95
    idx_p95 = int(len(diurutkan) * 0.95)
    idx_p95 = min(idx_p95, len(diurutkan) - 1)
    return {
        "min": min(diurutkan),
        "max": max(diurutkan),
        "mean": statistics.mean(diurutkan),
        "p95": diurutkan[idx_p95],
    }


def cetak_tabel(hasil: List[Dict[str, Any]]) -> None:
    """Print tabel ringkas ke stdout."""
    col_q = 40
    col_n = 5
    col_stat = 10

    header = (
        f"{'Pertanyaan':<{col_q}} "
        f"{'Runs':>{col_n}} "
        f"{'Min(ms)':>{col_stat}} "
        f"{'Max(ms)':>{col_stat}} "
        f"{'Mean(ms)':>{col_stat}} "
        f"{'P95(ms)':>{col_stat}} "
        f"{'Errors':>{col_n}}"
    )
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    for baris in hasil:
        q_singkat = baris["pertanyaan"][:col_q - 1]
        stat = baris["statistik"]
        print(
            f"{q_singkat:<{col_q}} "
            f"{baris['total_runs']:>{col_n}} "
            f"{stat['min']:>{col_stat}.1f} "
            f"{stat['max']:>{col_stat}.1f} "
            f"{stat['mean']:>{col_stat}.1f} "
            f"{stat['p95']:>{col_stat}.1f} "
            f"{baris['error_count']:>{col_n}}"
        )

    print("=" * len(header))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark latensi endpoint /ask SIDIX"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host SIDIX (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port SIDIX (default: 8765)")
    parser.add_argument(
        "--questions",
        default=None,
        help="Path ke file JSON berisi list string pertanyaan (opsional)",
    )
    parser.add_argument("--runs", type=int, default=3, help="Jumlah run per pertanyaan (default: 3)")
    parser.add_argument(
        "--output",
        default=None,
        help="Path file JSON output hasil benchmark (opsional)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Muat pertanyaan dari file atau pakai default
    if args.questions:
        with open(args.questions, "r", encoding="utf-8") as f:
            pertanyaan_list: List[str] = json.load(f)
        print(f"[INFO] Memuat {len(pertanyaan_list)} pertanyaan dari {args.questions}")
    else:
        pertanyaan_list = PERTANYAAN_DEFAULT
        print(f"[INFO] Menggunakan {len(pertanyaan_list)} pertanyaan hardcoded")

    print(f"[INFO] Target: http://{args.host}:{args.port}/ask")
    print(f"[INFO] Runs per pertanyaan: {args.runs}")

    semua_hasil = []

    for pertanyaan in pertanyaan_list:
        print(f"\n[RUN] '{pertanyaan[:60]}...' " if len(pertanyaan) > 60 else f"\n[RUN] '{pertanyaan}'")
        durasi_sukses = []
        error_count = 0

        for i in range(args.runs):
            hasil = kirim_pertanyaan(args.host, args.port, pertanyaan)
            status = "OK" if hasil["ok"] else "GAGAL"
            print(f"  Run {i+1}/{args.runs}: {status} | {hasil['duration_ms']:.1f} ms")
            if hasil["ok"]:
                durasi_sukses.append(hasil["duration_ms"])
            else:
                error_count += 1
                print(f"    Error: {hasil.get('error', 'unknown')}")

        stat = hitung_statistik(durasi_sukses)
        semua_hasil.append({
            "pertanyaan": pertanyaan,
            "total_runs": args.runs,
            "sukses": len(durasi_sukses),
            "error_count": error_count,
            "statistik": stat,
            "durasi_ms_list": durasi_sukses,
        })

    # Tampilkan tabel ringkas
    cetak_tabel(semua_hasil)

    # Simpan ke file output jika diminta
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(semua_hasil, f, ensure_ascii=False, indent=2)
        print(f"\n[INFO] Hasil disimpan ke: {args.output}")
