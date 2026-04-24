"""
Generate synthetic Q&A pairs untuk distilasi SIDIX.

Baca dari brain/public/research_notes/ dan corpus → generate pairs dengan gaya SIDIX.
Output: data/distillation/synthetic_pairs_YYYYMMDD.jsonl

Usage:
  # Mode mock (tanpa API key) — cocok untuk test pipeline:
  python scripts/distillation/generate_synthetic_data.py --count 100

  # Mode API (DeepSeek atau compatible OpenAI-format):
  export DISTIL_API_KEY=sk-xxx
  export DISTIL_API_BASE=https://api.deepseek.com/v1   # opsional, default DeepSeek
  export DISTIL_MODEL=deepseek-chat                     # opsional
  python scripts/distillation/generate_synthetic_data.py --count 500 --topic aqidah

  # Dry run (preview tanpa save):
  python scripts/distillation/generate_synthetic_data.py --dry-run --count 5
"""

import os
import json
import re
import datetime
import argparse
import random
import textwrap
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = REPO_ROOT / "brain" / "public" / "research_notes"
OUTPUT_DIR = REPO_ROOT / "data" / "distillation"

# ---------------------------------------------------------------------------
# Config from env
# ---------------------------------------------------------------------------
API_KEY = os.getenv("DISTIL_API_KEY", "")
API_BASE = os.getenv("DISTIL_API_BASE", "https://api.deepseek.com/v1")
MODEL_NAME = os.getenv("DISTIL_MODEL", "deepseek-chat")

MAX_CHUNK_TOKENS = 500   # rough estimate: 1 token ≈ 4 chars
CHARS_PER_TOKEN = 4


# ---------------------------------------------------------------------------
# 1. Load corpus chunks
# ---------------------------------------------------------------------------

def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of max_chars, respecting paragraph boundaries."""
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If single paragraph too long, hard-split
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i : i + max_chars])
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks


def load_corpus_chunks(
    topic_filter: Optional[str] = None,
    max_chars: int = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN,
) -> list[dict]:
    """
    Read all *.md files from NOTES_DIR.
    If topic_filter is given, only include files whose name contains the filter string.

    Returns list of dicts: {text, source, topic}
    """
    if not NOTES_DIR.exists():
        raise FileNotFoundError(f"Notes dir not found: {NOTES_DIR}")

    results: list[dict] = []
    md_files = sorted(NOTES_DIR.glob("*.md"))

    for md_file in md_files:
        if topic_filter and topic_filter.lower() not in md_file.stem.lower():
            continue

        raw = md_file.read_text(encoding="utf-8", errors="ignore")
        # Strip YAML front-matter if present
        raw = re.sub(r"^---.*?---\s*", "", raw, flags=re.DOTALL)

        chunks = _split_into_chunks(raw, max_chars)
        for chunk in chunks:
            if len(chunk.strip()) < 50:   # skip trivially short chunks
                continue
            results.append({
                "text": chunk.strip(),
                "source": md_file.name,
                "topic": md_file.stem,
            })

    random.shuffle(results)
    return results


# ---------------------------------------------------------------------------
# 2. Generate pair from chunk
# ---------------------------------------------------------------------------

SIDIX_SYSTEM_PROMPT = textwrap.dedent("""
    Kamu adalah SIDIX, asisten AI yang jujur dan bersumber. Setiap jawaban:
    - Gunakan label epistemik: [FAKTA], [OPINI], [SPEKULASI], [TIDAK TAHU]
    - Jawaban ringkas tapi informatif
    - Bahasa Indonesia
    - Sertakan sumber jika ada
""").strip()


def _mock_generate(chunk: dict) -> Optional[dict]:
    """
    Fallback generator tanpa API.
    Ekstrak pertanyaan dari heading/baris pertama, jawaban dari isi paragraf.
    """
    text = chunk["text"]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Find first heading as question seed
    question = None
    answer_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            question = re.sub(r"^#+\s*", "", line).strip()
            answer_start = i + 1
            break

    if not question and lines:
        # Use first line as question seed
        question = lines[0].rstrip(".:;")
        answer_start = 1

    if not question:
        return None

    # Build answer from subsequent lines
    answer_lines = lines[answer_start : answer_start + 12]
    if not answer_lines:
        return None

    answer_body = " ".join(answer_lines)
    # Trim to reasonable length
    if len(answer_body) > 600:
        answer_body = answer_body[:597] + "..."

    prompt = f"Apa itu {question}?" if len(question) < 60 else question
    completion = f"[FAKTA] {answer_body}\n\nSumber: {chunk['source']}"

    return {
        "prompt": prompt,
        "completion": completion,
        "source": chunk["source"],
        "topic": chunk["topic"],
        "mode": "mock",
    }


def _api_generate(chunk: dict, api_key: str) -> Optional[dict]:
    """
    Call OpenAI-compatible API (DeepSeek / any) to generate Q&A pair.
    Returns None on failure.
    """
    try:
        import urllib.request

        user_msg = (
            f"Berdasarkan teks berikut, buat SATU pasang pertanyaan-jawaban dalam Bahasa Indonesia "
            f"yang mencerminkan gaya SIDIX (epistemik, bersumber, ringkas).\n\n"
            f"Format output JSON:\n"
            f'{{\"prompt\": \"...\", \"completion\": \"...\"}}\n\n'
            f"Teks:\n{chunk['text'][:1500]}"
        )

        payload = json.dumps({
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SIDIX_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = data["choices"][0]["message"]["content"].strip()
        # Extract JSON from content
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            return None

        pair = json.loads(json_match.group(0))
        pair["source"] = chunk["source"]
        pair["topic"] = chunk["topic"]
        pair["mode"] = "api"
        return pair

    except Exception as exc:
        print(f"  [WARN] API call failed: {exc} — falling back to mock")
        return _mock_generate(chunk)


def generate_pair_from_chunk(
    chunk: dict, api_key: Optional[str] = None
) -> Optional[dict]:
    """
    Generate one Q&A pair from chunk.
    Uses API if api_key provided, otherwise mock.
    """
    if api_key:
        return _api_generate(chunk, api_key)
    return _mock_generate(chunk)


# ---------------------------------------------------------------------------
# 3. Save pairs
# ---------------------------------------------------------------------------

def save_pairs(pairs: list[dict], output_path: Path) -> None:
    """Save list of pairs to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(pairs)} pairs → {output_path}")


# ---------------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Q&A pairs for SIDIX distillation"
    )
    parser.add_argument(
        "--count", type=int, default=100,
        help="Number of pairs to generate (default: 100)"
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="Filter notes by topic substring (e.g. 'aqidah', 'lora', 'agent')"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSONL path (default: data/distillation/synthetic_pairs_YYYYMMDD.jsonl)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview pairs without saving"
    )
    args = parser.parse_args()

    api_key = API_KEY or None
    mode_label = "API" if api_key else "MOCK"
    print(f"[INFO] Mode: {mode_label} | Count: {args.count} | Topic filter: {args.topic or 'all'}")

    # Load corpus
    print(f"[INFO] Loading corpus from {NOTES_DIR} ...")
    chunks = load_corpus_chunks(topic_filter=args.topic)
    print(f"[INFO] Found {len(chunks)} chunks")

    if not chunks:
        print("[ERROR] No chunks found. Check NOTES_DIR or topic filter.")
        return

    # Generate pairs
    pairs: list[dict] = []
    target = min(args.count, len(chunks))

    for i, chunk in enumerate(chunks[:target]):
        print(f"  [{i+1}/{target}] Generating from: {chunk['source'][:50]}")
        pair = generate_pair_from_chunk(chunk, api_key=api_key)
        if pair:
            pairs.append(pair)

    print(f"[INFO] Generated {len(pairs)} valid pairs")

    if args.dry_run:
        print("\n--- DRY RUN PREVIEW (first 3) ---")
        for p in pairs[:3]:
            print(json.dumps(p, ensure_ascii=False, indent=2))
        return

    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.date.today().strftime("%Y%m%d")
        output_path = OUTPUT_DIR / f"synthetic_pairs_{date_str}.jsonl"

    save_pairs(pairs, output_path)


if __name__ == "__main__":
    main()
