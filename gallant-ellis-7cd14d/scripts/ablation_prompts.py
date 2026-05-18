"""
ablation_prompts.py — Task 31 (Maryam / G5)
Ablation perbandingan 3 varian system prompt pada set pertanyaan kecil.
Hanya menggunakan stdlib: urllib.request, json, csv, argparse, time.
"""

import argparse
import csv
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any

# Tiga varian system prompt hardcoded
VARIAN_PROMPT_DEFAULT = [
    {
        "nama": "singkat_faktual",
        "label": "Singkat dan Faktual",
        "prompt": "Jawab singkat dan faktual.",
    },
    {
        "nama": "sidix_standar",
        "label": "SIDIX Standar",
        "prompt": (
            "Kamu adalah SIDIX, asisten berbasis epistemologi Islam. "
            "Jawab dengan sidq (kejujuran), tabayyun (verifikasi), dan sanad yang jelas. "
            "Jika tidak tahu, nyatakan dengan tegas: 'Saya tidak tahu.' "
            "Hindari spekulasi tanpa dasar. Prioritaskan kebenaran di atas kenyamanan."
        ),
    },
    {
        "nama": "detail_contoh",
        "label": "Detail dengan Contoh",
        "prompt": "Jelaskan secara rinci dengan contoh konkret.",
    },
]

# Pertanyaan default jika tidak ada file JSON
PERTANYAAN_DEFAULT = [
    "Apa itu kecerdasan buatan?",
    "Bagaimana cara kerja model bahasa besar?",
    "Apa manfaat RAG dalam sistem AI?",
]


def kirim_ke_agent(
    host: str, port: int, system_prompt: str, pertanyaan: str
) -> Dict[str, Any]:
    """
    Kirim POST ke /agent/generate dengan system_prompt dan pertanyaan.
    Kembalikan dict dengan jawaban, duration_ms, dan metadata.
    """
    url = f"http://{host}:{port}/agent/generate"
    payload = json.dumps({
        "system_prompt": system_prompt,
        "message": pertanyaan,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t_mulai = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            t_selesai = time.perf_counter()
            duration_ms = (t_selesai - t_mulai) * 1000
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body}
            # Ambil teks jawaban dari berbagai format respons yang mungkin
            jawaban = (
                data.get("answer")
                or data.get("response")
                or data.get("text")
                or data.get("raw", "")
            )
            return {
                "ok": True,
                "duration_ms": duration_ms,
                "jawaban": jawaban,
                "panjang_jawaban": len(jawaban),
                "ada_tidak_tahu": "tidak tahu" in jawaban.lower(),
            }
    except urllib.error.URLError as e:
        t_selesai = time.perf_counter()
        duration_ms = (t_selesai - t_mulai) * 1000
        return {
            "ok": False,
            "duration_ms": duration_ms,
            "jawaban": "",
            "panjang_jawaban": 0,
            "ada_tidak_tahu": False,
            "error": str(e),
        }


def cetak_tabel(hasil: List[Dict[str, Any]]) -> None:
    """Print tabel ringkas hasil ablation ke stdout."""
    col_v = 22
    col_q = 35
    col_p = 8
    col_d = 10
    col_t = 8

    header = (
        f"{'Varian':<{col_v}} "
        f"{'Pertanyaan':<{col_q}} "
        f"{'Panjang':>{col_p}} "
        f"{'Durasi(ms)':>{col_d}} "
        f"{'TidakTahu':>{col_t}}"
    )
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    for baris in hasil:
        q_singkat = baris["pertanyaan"][:col_q - 1]
        print(
            f"{baris['varian_label']:<{col_v}} "
            f"{q_singkat:<{col_q}} "
            f"{baris['panjang_jawaban']:>{col_p}} "
            f"{baris['duration_ms']:>{col_d}.1f} "
            f"{'Ya' if baris['ada_tidak_tahu'] else 'Tidak':>{col_t}}"
        )

    print("=" * len(header))


def simpan_csv(hasil: List[Dict[str, Any]], path_output: str) -> None:
    """Simpan hasil ke file CSV."""
    fieldnames = [
        "varian_nama", "varian_label", "pertanyaan",
        "panjang_jawaban", "duration_ms", "ada_tidak_tahu",
        "ok", "error",
    ]
    with open(path_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for baris in hasil:
            writer.writerow(baris)
    print(f"[INFO] Hasil CSV disimpan ke: {path_output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ablation 3 varian system prompt di SIDIX /agent/generate"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host SIDIX (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port SIDIX (default: 8765)")
    parser.add_argument(
        "--questions",
        default=None,
        help="Path ke file JSON berisi list string pertanyaan (opsional)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path file CSV output hasil ablation (opsional)",
    )
    parser.add_argument(
        "--prompts",
        default=None,
        help="Path file JSON berisi list varian prompt [{nama, label, prompt}] (opsional)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Muat varian prompt
    if args.prompts:
        with open(args.prompts, "r", encoding="utf-8") as f:
            varian_list: List[Dict] = json.load(f)
        print(f"[INFO] Memuat {len(varian_list)} varian prompt dari {args.prompts}")
    else:
        varian_list = VARIAN_PROMPT_DEFAULT
        print(f"[INFO] Menggunakan {len(varian_list)} varian prompt hardcoded")

    # Muat pertanyaan
    if args.questions:
        with open(args.questions, "r", encoding="utf-8") as f:
            pertanyaan_list: List[str] = json.load(f)
        print(f"[INFO] Memuat {len(pertanyaan_list)} pertanyaan dari {args.questions}")
    else:
        pertanyaan_list = PERTANYAAN_DEFAULT
        print(f"[INFO] Menggunakan {len(pertanyaan_list)} pertanyaan hardcoded")

    print(f"[INFO] Target: http://{args.host}:{args.port}/agent/generate")
    total_kombinasi = len(varian_list) * len(pertanyaan_list)
    print(f"[INFO] Total kombinasi: {total_kombinasi}")

    semua_hasil = []

    for varian in varian_list:
        print(f"\n[VARIAN] {varian['label']}")
        for pertanyaan in pertanyaan_list:
            q_display = pertanyaan[:50] + "..." if len(pertanyaan) > 50 else pertanyaan
            print(f"  [Q] {q_display}", end=" ... ", flush=True)
            hasil = kirim_ke_agent(
                args.host, args.port, varian["prompt"], pertanyaan
            )
            status = "OK" if hasil["ok"] else "GAGAL"
            print(f"{status} | {hasil['duration_ms']:.0f}ms | len={hasil['panjang_jawaban']}")

            semua_hasil.append({
                "varian_nama": varian["nama"],
                "varian_label": varian["label"],
                "pertanyaan": pertanyaan,
                "panjang_jawaban": hasil["panjang_jawaban"],
                "duration_ms": hasil["duration_ms"],
                "ada_tidak_tahu": hasil["ada_tidak_tahu"],
                "ok": hasil["ok"],
                "error": hasil.get("error", ""),
                "jawaban": hasil["jawaban"],
            })

    # Tampilkan tabel ringkas
    cetak_tabel(semua_hasil)

    # Simpan CSV jika diminta
    if args.output:
        simpan_csv(semua_hasil, args.output)
