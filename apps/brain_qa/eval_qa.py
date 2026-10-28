"""
eval_qa.py — QA Evaluator untuk Mighan-brain-1 / SIDIX
=======================================================
Jalankan SETELAH install-deps.bat dan `python -m brain_qa index`.

Usage:
    python eval_qa.py
    python eval_qa.py --k 5 --threshold 0.10 --verbose

Output:
    - Per-pair: PASS / MISS + overlap score
    - Summary: hit@k, coverage, rekomendasi
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────────────

# Repo root (dinamis, tanpa mengikat path lokal tertentu)
ROOT = Path(__file__).parent.parent.parent
DATA_DIR = Path(__file__).parent / ".data"
QA_PAIRS_PATH = ROOT / "brain" / "datasets" / "qa_pairs.jsonl"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
TOKENS_PATH = DATA_DIR / "tokens.jsonl"


# ── Tokenizer (sama dengan brain_qa/text.py) ───────────────────────────────────

_WS_RE = re.compile(r"\s+")
_MD_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MD_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def _normalize(s: str) -> str:
    s = _MD_CODE_FENCE_RE.sub(" ", s)
    s = _MD_INLINE_CODE_RE.sub(" ", s)
    s = _MD_LINK_RE.sub(r"\1", s)
    s = s.replace("\u00a0", " ")
    return _WS_RE.sub(" ", s).strip()


def tokenize(s: str) -> list[str]:
    s = _normalize(s).lower()
    return re.findall(r"[a-z0-9_]+", s)


# ── Index loader ───────────────────────────────────────────────────────────────

def load_index() -> tuple[list[dict], list[list[str]]]:
    if not CHUNKS_PATH.exists():
        print(f"ERROR: Index belum ada di {CHUNKS_PATH}")
        print("Jalankan dulu: python -m brain_qa index")
        sys.exit(1)

    chunks = []
    for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(json.loads(line))

    tokens = []
    for line in TOKENS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            tokens.append(obj.get("tokens", []))

    return chunks, tokens


def load_qa_pairs() -> list[dict]:
    if not QA_PAIRS_PATH.exists():
        print(f"ERROR: qa_pairs.jsonl tidak ditemukan di {QA_PAIRS_PATH}")
        sys.exit(1)

    pairs = []
    for line in QA_PAIRS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            pairs.append(json.loads(line))
    return pairs


# ── BM25 retriever ─────────────────────────────────────────────────────────────

def bm25_retrieve(query_tokens: list[str], tokens: list[list[str]], k: int) -> list[int]:
    """BM25Okapi retrieval — returns top-k chunk indices."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("ERROR: rank_bm25 belum terpasang. Jalankan install-deps.bat dulu.")
        sys.exit(1)

    bm25 = BM25Okapi(tokens)
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top = [i for i in ranked[:max(1, k)] if scores[i] > 0] or ranked[:max(1, k)]
    return top


# ── Overlap scorer ─────────────────────────────────────────────────────────────

def token_overlap(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard-style overlap: |A ∩ B| / |A| (recall of A given B)."""
    if not set_a:
        return 0.0
    return len(set_a & set_b) / len(set_a)


_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "pada", "adalah", "atau", "juga", "tidak", "lebih", "bisa", "ada",
    "akan", "agar", "oleh", "serta", "dalam", "sebagai", "dapat", "sudah",
    "the", "a", "an", "of", "to", "and", "or", "is", "in", "for",
    "with", "as", "by", "be", "are", "that", "this", "it",
}


def meaningful_tokens(tokens: list[str]) -> set[str]:
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


# ── Evaluator ──────────────────────────────────────────────────────────────────

def evaluate(k: int = 5, threshold: float = 0.12, verbose: bool = False) -> dict:
    chunks, tokens = load_index()
    pairs = load_qa_pairs()

    if not pairs:
        print("Tidak ada QA pairs ditemukan.")
        return {}

    print(f"\n{'='*60}")
    print(f"  SIDIX QA Evaluator — brain_qa")
    print(f"  Pairs: {len(pairs)} | k={k} | threshold={threshold:.0%}")
    print(f"  Index: {len(chunks)} chunks dari {DATA_DIR}")
    print(f"{'='*60}\n")

    results = []

    for pair in pairs:
        qa_id = pair.get("id", "?")
        question = pair.get("question", "")
        ideal = pair.get("ideal_answer", "")
        tags = pair.get("tags", [])

        q_tokens = tokenize(question)
        top_indices = bm25_retrieve(q_tokens, tokens, k=k)

        # Gabungkan teks dari top-k chunks
        retrieved_text = " ".join(chunks[i]["text"] for i in top_indices if i < len(chunks))
        retrieved_tokens = meaningful_tokens(tokenize(retrieved_text))
        ideal_tokens = meaningful_tokens(tokenize(ideal))

        overlap = token_overlap(ideal_tokens, retrieved_tokens)
        passed = overlap >= threshold

        result = {
            "id": qa_id,
            "question": question[:80] + ("…" if len(question) > 80 else ""),
            "overlap": overlap,
            "passed": passed,
            "top_sources": list({chunks[i]["source_title"] for i in top_indices if i < len(chunks)}),
            "tags": tags,
        }
        results.append(result)

        status = "✅ PASS" if passed else "❌ MISS"
        bar = "█" * int(overlap * 20)
        print(f"[{qa_id}] {status}  overlap={overlap:.1%}  |{bar:<20}|")
        print(f"         Q: {result['question']}")
        if verbose:
            print(f"         Sumber: {', '.join(result['top_sources'][:3])}")
        print()

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(results)
    hits = sum(1 for r in results if r["passed"])
    misses = total - hits
    hit_rate = hits / total if total else 0

    print(f"{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total pairs    : {total}")
    print(f"  PASS (hit@{k})  : {hits}  ({hit_rate:.0%})")
    print(f"  MISS           : {misses}")
    print(f"  Threshold      : {threshold:.0%} token overlap")
    print()

    if hit_rate >= 0.80:
        print("  ✅ BAGUS — retrieval sudah cukup baik untuk M3.")
    elif hit_rate >= 0.50:
        print("  ⚠️  CUKUP — ada beberapa miss, tambah dokumen ke corpus.")
    else:
        print("  ❌ KURANG — banyak miss, corpus belum cukup cover topik QA.")

    print()
    if misses > 0:
        print("  QA pairs yang MISS (perlu tambah dokumen ke corpus):")
        for r in results:
            if not r["passed"]:
                print(f"  - [{r['id']}] {r['question']} | tags: {r['tags']}")

    print(f"\n  Milestone M3 checklist:")
    print(f"  [x] Ingest Markdown → chunks")
    print(f"  [x] BM25 index (rank-bm25)")
    print(f"  [x] Retrieve + cite")
    print(f"  [{'x' if hit_rate >= 0.5 else ' '}] Evaluasi via QA pairs  ← skor: {hit_rate:.0%}")
    print(f"  [ ] Memory injection (memory_cards.jsonl → context)")
    print()

    # Simpan hasil ke .data/qa_eval_result.json
    out_path = DATA_DIR / "qa_eval_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "hit_rate": round(hit_rate, 4),
                "hits": hits,
                "misses": misses,
                "total": total,
                "k": k,
                "threshold": threshold,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  Hasil disimpan: {out_path}")

    return {"hit_rate": hit_rate, "hits": hits, "total": total}


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIDIX QA Evaluator — test retrieval quality")
    parser.add_argument("--k", type=int, default=5, help="Top-k chunks untuk retrieval (default: 5)")
    parser.add_argument("--threshold", type=float, default=0.12, help="Min token overlap untuk PASS (default: 0.12)")
    parser.add_argument("--verbose", action="store_true", help="Tampilkan sumber per pair")
    args = parser.parse_args()

    evaluate(k=args.k, threshold=args.threshold, verbose=args.verbose)
