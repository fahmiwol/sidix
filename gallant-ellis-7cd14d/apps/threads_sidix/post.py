"""
SIDIX → Threads Poster
──────────────────────
Post konten ke Threads via Meta API.
Bisa dipakai standalone (CLI) atau di-import dari bot/scheduler.

Usage:
  python post.py "Teks yang mau dipost"
  python post.py --generate "Topik untuk SIDIX generate konten"
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

THREADS_TOKEN   = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")
SIDIX_URL       = os.getenv("SIDIX_URL", "http://localhost:8765")


def sidix_generate(prompt: str) -> str:
    """Minta SIDIX generate konten berdasarkan prompt."""
    try:
        r = requests.post(
            f"{SIDIX_URL}/agent/chat",
            json={
                "message": f"Buatkan konten Threads singkat (max 400 karakter) tentang: {prompt}. "
                           "Langsung isi kontennya saja, tanpa penjelasan.",
                "session_id": "threads-gen"
            },
            timeout=30,
        )
        data = r.json()
        return data.get("reply") or data.get("response") or data.get("answer") or ""
    except Exception as e:
        print(f"⚠ SIDIX error: {e}")
        return ""


def post_thread(text: str) -> tuple[bool, str]:
    """
    Post teks ke Threads.
    Return: (sukses: bool, post_id/error: str)
    """
    if not THREADS_TOKEN or not THREADS_USER_ID:
        return False, "Set THREADS_ACCESS_TOKEN dan THREADS_USER_ID di .env"

    if len(text) > 500:
        return False, f"Teks terlalu panjang ({len(text)} char, max 500)"

    # Step 1: buat media container
    r1 = requests.post(
        f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_TOKEN,
        },
        timeout=12,
    )
    data1 = r1.json()
    if "error" in data1:
        return False, data1["error"].get("message", str(data1["error"]))
    creation_id = data1.get("id")
    if not creation_id:
        return False, f"Tidak ada creation_id: {data1}"

    # Step 2: publish
    r2 = requests.post(
        f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
        params={
            "creation_id": creation_id,
            "access_token": THREADS_TOKEN,
        },
        timeout=12,
    )
    data2 = r2.json()
    if "error" in data2:
        return False, data2["error"].get("message", str(data2["error"]))
    post_id = data2.get("id")
    if post_id:
        return True, post_id
    return False, f"Unexpected response: {data2}"


def main():
    parser = argparse.ArgumentParser(description="SIDIX → Threads Poster")
    parser.add_argument("text", nargs="?", help="Teks yang mau dipost langsung")
    parser.add_argument("--generate", "-g", metavar="TOPIK",
                        help="Minta SIDIX generate konten dari topik ini")
    args = parser.parse_args()

    if args.generate:
        print(f"🧠 SIDIX generate konten untuk: {args.generate}")
        content = sidix_generate(args.generate)
        if not content:
            print("❌ SIDIX tidak bisa generate konten.")
            sys.exit(1)
        print(f"\n📝 Konten:\n{content}\n")
        confirm = input("Post ke Threads? (y/N): ").strip().lower()
        if confirm != "y":
            print("Dibatalkan.")
            sys.exit(0)
        text = content

    elif args.text:
        text = args.text

    else:
        parser.print_help()
        sys.exit(1)

    print("📤 Posting ke Threads...")
    ok, info = post_thread(text)
    if ok:
        print(f"✅ Berhasil! Post ID: {info}")
    else:
        print(f"❌ Gagal: {info}")
        sys.exit(1)


if __name__ == "__main__":
    main()
