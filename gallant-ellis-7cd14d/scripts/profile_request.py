"""
profile_request.py — Task 47 (Az-Zalzalah / G5)
Profiling satu request panjang ke SIDIX dengan breakdown timing per fase.
Hanya menggunakan stdlib: urllib.request, http.client, socket, json, argparse, time.

Fase yang diukur:
  - TCP connect
  - Send request (headers + body)
  - TTFB (Time To First Byte)
  - Total (sampai body selesai dibaca)

Mode SSE (/ask/stream): baca tiap event dan timestamp-kan tiap token.
"""

import argparse
import http.client
import json
import socket
import sys
import time
import urllib.parse
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profiling satu request ke SIDIX dengan breakdown timing"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host SIDIX (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port SIDIX (default: 8765)")
    parser.add_argument(
        "--question", default="Jelaskan secara lengkap apa itu epistemologi Islam.",
        help="Pertanyaan yang akan diprofil"
    )
    parser.add_argument(
        "--endpoint", default="/ask",
        help="Endpoint target (default: /ask). Gunakan /ask/stream untuk mode SSE."
    )
    parser.add_argument(
        "--output", default=None,
        help="Path file JSON untuk menyimpan laporan profiling (opsional)"
    )
    return parser.parse_args()


def profil_request_biasa(
    host: str, port: int, endpoint: str, pertanyaan: str
) -> Dict[str, Any]:
    """
    Profil request POST biasa (non-SSE).
    Ukur: TCP connect, send, TTFB, total.
    """
    payload = json.dumps({"question": pertanyaan}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
        "Connection": "close",
    }

    t_ref = time.perf_counter()  # referensi waktu awal
    timing: Dict[str, float] = {}

    # --- Fase 1: TCP Connect ---
    try:
        conn = http.client.HTTPConnection(host, port, timeout=30)
        conn.connect()
        timing["tcp_connect_ms"] = (time.perf_counter() - t_ref) * 1000
    except (socket.error, ConnectionRefusedError) as e:
        return {"ok": False, "error": f"TCP connect gagal: {e}", "timing": {}}

    # --- Fase 2: Send request ---
    t_sebelum_send = time.perf_counter()
    try:
        conn.putrequest("POST", endpoint)
        for k, v in headers.items():
            conn.putheader(k, v)
        conn.endheaders(payload)
        timing["send_ms"] = (time.perf_counter() - t_sebelum_send) * 1000
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Gagal mengirim request: {e}", "timing": timing}

    # --- Fase 3: TTFB (Time To First Byte) ---
    t_sebelum_ttfb = time.perf_counter()
    try:
        resp = conn.getresponse()
        timing["ttfb_ms"] = (time.perf_counter() - t_sebelum_ttfb) * 1000
        timing["ttfb_from_start_ms"] = (time.perf_counter() - t_ref) * 1000
        http_status = resp.status
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Gagal membaca respons: {e}", "timing": timing}

    # --- Fase 4: Baca seluruh body ---
    t_sebelum_body = time.perf_counter()
    try:
        body_bytes = resp.read()
        timing["body_read_ms"] = (time.perf_counter() - t_sebelum_body) * 1000
        timing["total_ms"] = (time.perf_counter() - t_ref) * 1000
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Gagal membaca body: {e}", "timing": timing}

    conn.close()

    # Parse body
    try:
        body_data = json.loads(body_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        body_data = {"raw_length": len(body_bytes)}

    # Ambil teks jawaban
    jawaban = (
        body_data.get("answer")
        or body_data.get("response")
        or body_data.get("text")
        or ""
    )

    return {
        "ok": True,
        "endpoint": endpoint,
        "http_status": http_status,
        "timing": timing,
        "body_size_bytes": len(body_bytes),
        "jawaban_panjang": len(jawaban),
        "jawaban_preview": jawaban[:200] if jawaban else "",
    }


def profil_request_sse(
    host: str, port: int, endpoint: str, pertanyaan: str
) -> Dict[str, Any]:
    """
    Profil request SSE (Server-Sent Events / streaming).
    Timestamp tiap event/token yang diterima.
    """
    payload = json.dumps({"question": pertanyaan}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    t_ref = time.perf_counter()
    timing: Dict[str, float] = {}
    events: List[Dict[str, Any]] = []

    # --- TCP Connect ---
    try:
        conn = http.client.HTTPConnection(host, port, timeout=60)
        conn.connect()
        timing["tcp_connect_ms"] = (time.perf_counter() - t_ref) * 1000
    except (socket.error, ConnectionRefusedError) as e:
        return {"ok": False, "error": f"TCP connect gagal: {e}", "timing": {}, "events": []}

    # --- Send request ---
    t_sebelum_send = time.perf_counter()
    try:
        conn.putrequest("POST", endpoint)
        for k, v in headers.items():
            conn.putheader(k, v)
        conn.endheaders(payload)
        timing["send_ms"] = (time.perf_counter() - t_sebelum_send) * 1000
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Gagal mengirim request: {e}", "timing": timing, "events": []}

    # --- TTFB ---
    t_sebelum_ttfb = time.perf_counter()
    try:
        resp = conn.getresponse()
        timing["ttfb_ms"] = (time.perf_counter() - t_sebelum_ttfb) * 1000
        timing["ttfb_from_start_ms"] = (time.perf_counter() - t_ref) * 1000
        http_status = resp.status
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Gagal membaca respons: {e}", "timing": timing, "events": []}

    # --- Baca SSE events baris per baris ---
    print("[SSE] Membaca stream token...", flush=True)
    buffer = b""
    event_index = 0
    t_event_pertama: Optional[float] = None

    try:
        while True:
            chunk = resp.read(1)  # baca satu byte agar TTFB akurat
            if not chunk:
                break
            buffer += chunk

            # SSE event dipisahkan oleh "\n\n"
            while b"\n\n" in buffer:
                event_raw, buffer = buffer.split(b"\n\n", 1)
                event_str = event_raw.decode("utf-8", errors="replace").strip()

                if not event_str:
                    continue

                t_event = (time.perf_counter() - t_ref) * 1000
                event_index += 1

                if t_event_pertama is None:
                    t_event_pertama = t_event

                # Parse "data: ..." dari SSE
                teks_token = ""
                for baris in event_str.split("\n"):
                    if baris.startswith("data:"):
                        teks_token = baris[5:].strip()
                        break

                events.append({
                    "index": event_index,
                    "t_ms": round(t_event, 2),
                    "delta_ms": round(t_event - (t_event_pertama or t_event), 2),
                    "data": teks_token[:100],  # potong agar laporan tidak terlalu besar
                })

                # Cetak progress ringkas
                print(f"  Token #{event_index:>4} | +{events[-1]['delta_ms']:.0f}ms | {teks_token[:40]}", flush=True)

    except Exception as e:
        print(f"[WARN] Error saat membaca stream: {e}")

    timing["total_ms"] = (time.perf_counter() - t_ref) * 1000
    timing["first_token_ms"] = t_event_pertama or timing["ttfb_ms"]
    conn.close()

    return {
        "ok": True,
        "mode": "sse",
        "endpoint": endpoint,
        "http_status": http_status,
        "timing": timing,
        "total_events": event_index,
        "events": events,
    }


def cetak_ringkasan(laporan: Dict[str, Any]) -> None:
    """Print ringkasan profiling ke stdout."""
    timing = laporan.get("timing", {})
    print("\n" + "=" * 55)
    print("LAPORAN PROFILING REQUEST SIDIX")
    print("=" * 55)
    print(f"  Status OK         : {laporan.get('ok', False)}")
    if not laporan.get("ok"):
        print(f"  Error             : {laporan.get('error')}")
        print("=" * 55)
        return
    print(f"  Endpoint          : {laporan.get('endpoint')}")
    print(f"  HTTP Status       : {laporan.get('http_status')}")
    print()
    print("  BREAKDOWN TIMING:")
    print(f"    TCP Connect     : {timing.get('tcp_connect_ms', 0):.2f} ms")
    print(f"    Send Request    : {timing.get('send_ms', 0):.2f} ms")
    print(f"    TTFB            : {timing.get('ttfb_ms', 0):.2f} ms")
    if "first_token_ms" in timing:
        print(f"    First Token     : {timing.get('first_token_ms', 0):.2f} ms")
    if "body_read_ms" in timing:
        print(f"    Body Read       : {timing.get('body_read_ms', 0):.2f} ms")
    print(f"    TOTAL           : {timing.get('total_ms', 0):.2f} ms")
    print()
    if "total_events" in laporan:
        print(f"  Total SSE Events  : {laporan['total_events']}")
    if "body_size_bytes" in laporan:
        print(f"  Body Size         : {laporan['body_size_bytes']} bytes")
    if "jawaban_preview" in laporan and laporan["jawaban_preview"]:
        print(f"  Preview Jawaban   : {laporan['jawaban_preview'][:100]}...")
    print("=" * 55)


if __name__ == "__main__":
    args = parse_args()

    print(f"[INFO] Profiling: http://{args.host}:{args.port}{args.endpoint}")
    print(f"[INFO] Pertanyaan: {args.question[:80]}")
    print()

    # Pilih mode: SSE atau biasa
    mode_sse = args.endpoint.endswith("/stream") or "stream" in args.endpoint

    if mode_sse:
        print("[INFO] Mode: SSE (Server-Sent Events)")
        laporan = profil_request_sse(args.host, args.port, args.endpoint, args.question)
    else:
        print("[INFO] Mode: Request biasa (JSON response)")
        laporan = profil_request_biasa(args.host, args.port, args.endpoint, args.question)

    # Tambahkan metadata ke laporan
    laporan["pertanyaan"] = args.question
    laporan["host"] = args.host
    laporan["port"] = args.port

    # Cetak ringkasan
    cetak_ringkasan(laporan)

    # Simpan ke file jika diminta
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(laporan, f, ensure_ascii=False, indent=2)
        print(f"\n[INFO] Laporan disimpan ke: {args.output}")

    # Exit code berdasarkan keberhasilan request
    sys.exit(0 if laporan.get("ok") else 1)
