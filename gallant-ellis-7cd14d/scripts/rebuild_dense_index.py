#!/usr/bin/env python3
"""
rebuild_dense_index.py — Sprint Cognitive 80%→100%

Fix dim mismatch: dense_index dibangun dengan BGE-M3 (512-dim) tapi
sekarang fallback ke MiniLM (384-dim) post PyTorch upgrade kemarin.
Ini bikin semua dense semantic search abort dengan
"[dense_index] query dim 384 != index dim 512, abort".

Solution: rebuild index dengan model yang aktif (MiniLM 384-dim).

Usage:
    python3 scripts/rebuild_dense_index.py [--source brain/public/research_notes]
                                            [--out apps/brain_qa/dense_cache.npz]
                                            [--model sentence-transformers/all-MiniLM-L6-v2]

Setelah selesai, restart sidix-brain — dense_index akan match dim ke embedding
saat ini, semantic search hidup lagi.

Cognitive & Semantic visi: 80% → 100%.

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def rebuild_dense_index(
    source_dir: str = "brain/public/research_notes",
    out_path: str = "apps/brain_qa/dense_cache.npz",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 800,
) -> int:
    """Rebuild dense index dari source dir ke out_path.

    Returns: jumlah chunks yang di-index.
    """
    print(f"[rebuild_dense_index] start")
    print(f"  source: {source_dir}")
    print(f"  out: {out_path}")
    print(f"  model: {model_name}")
    print(f"  chunk_size: {chunk_size} chars")

    src = Path(source_dir)
    if not src.exists():
        print(f"❌ source dir tidak ada: {src}")
        return 0

    # Load embedding model
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError as e:
        print(f"❌ butuh sentence-transformers + numpy: {e}")
        return 0

    print(f"[rebuild_dense_index] loading model...")
    t0 = time.monotonic()
    model = SentenceTransformer(model_name, device="cpu")
    embed_dim = model.get_sentence_embedding_dimension()
    print(f"  ✓ loaded in {time.monotonic() - t0:.1f}s, dim={embed_dim}")

    # Collect chunks
    chunks: list[dict] = []
    md_files = list(src.glob("**/*.md"))
    print(f"[rebuild_dense_index] {len(md_files)} markdown files")

    for fp in md_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  skip {fp.name}: {e}")
            continue

        # Simple chunking by paragraph blocks, cap to chunk_size chars
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        buf = ""
        for p in paras:
            if len(buf) + len(p) + 2 > chunk_size:
                if buf:
                    chunks.append({"file": fp.name, "text": buf.strip()})
                buf = p
            else:
                buf = (buf + "\n\n" + p) if buf else p
        if buf:
            chunks.append({"file": fp.name, "text": buf.strip()})

    print(f"[rebuild_dense_index] {len(chunks)} chunks created")

    if not chunks:
        print("❌ no chunks to index")
        return 0

    # Embed
    print(f"[rebuild_dense_index] embedding {len(chunks)} chunks...")
    t1 = time.monotonic()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    print(f"  ✓ embedded in {time.monotonic() - t1:.1f}s, shape={embeddings.shape}")

    # Save
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        embeddings=embeddings,
        files=np.array([c["file"] for c in chunks]),
        texts=np.array([c["text"][:500] for c in chunks]),  # cap text untuk hemat disk
        model_name=model_name,
        embed_dim=embed_dim,
    )

    print(f"[rebuild_dense_index] saved to {out}")
    print(f"  size: {out.stat().st_size / 1024:.1f} KB")
    print(f"  chunks: {len(chunks)}")
    print(f"  dim: {embed_dim}")
    print(f"\n✅ RESTART sidix-brain to load new index")

    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="brain/public/research_notes")
    parser.add_argument("--out", default="apps/brain_qa/dense_cache.npz")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--chunk-size", type=int, default=800)
    args = parser.parse_args()

    n = rebuild_dense_index(args.source, args.out, args.model, args.chunk_size)
    sys.exit(0 if n > 0 else 1)
