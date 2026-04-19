from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rank_bm25 import BM25Okapi

from .paths import default_index_dir, load_manifest_paths
from .sanad_ranking import extract_sanad_tier_from_markdown
from .text import Chunk, chunk_text, normalize_text_for_search, tokenize


def _title_from_markdown(md: str, fallback: str) -> str:
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:120] or fallback
    return fallback


def _iter_markdown_files(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Markdown root not found: {root}")
    return sorted([p for p in root.rglob("*.md") if p.is_file()])


def build_index(
    *,
    root_override: str | None,
    out_dir_override: str | None,
    chunk_chars: int,
    chunk_overlap: int,
) -> None:
    manifest = load_manifest_paths()
    root = Path(root_override) if root_override else manifest.public_markdown_root
    out_dir = Path(out_dir_override) if out_dir_override else default_index_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = _iter_markdown_files(root)
    chunks: list[Chunk] = []

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        sanad_tier = extract_sanad_tier_from_markdown(raw)
        title = _title_from_markdown(raw, fallback=path.stem)
        cleaned = normalize_text_for_search(raw)
        for start, end, part in chunk_text(cleaned, chunk_chars=chunk_chars, chunk_overlap=chunk_overlap):
            if not part.strip():
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            chunk_id = f"{rel}:{start}-{end}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source_path=rel,
                    source_title=title,
                    start_char=start,
                    end_char=end,
                    text=part,
                    sanad_tier=sanad_tier,
                )
            )

    tokenized = [tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized)

    # Persist chunks
    (out_dir / "chunks.jsonl").write_text(
        "\n".join(json.dumps(asdict(c), ensure_ascii=False) for c in chunks) + ("\n" if chunks else ""),
        encoding="utf-8",
    )
    # Persist tokenized corpus (for debug / reproducibility)
    (out_dir / "tokens.jsonl").write_text(
        "\n".join(json.dumps({"chunk_id": c.chunk_id, "tokens": toks}, ensure_ascii=False) for c, toks in zip(chunks, tokenized))
        + ("\n" if chunks else ""),
        encoding="utf-8",
    )
    # Persist bm25 as plain JSON (rebuildable)
    meta = {
        "version": 1,
        "root": str(root),
        "chunk_chars": chunk_chars,
        "chunk_overlap": chunk_overlap,
        "chunk_count": len(chunks),
    }
    (out_dir / "index_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # rank-bm25 object isn't trivially JSON-serializable; we rebuild at query time from tokens.
    # Still write a small marker so users know indexing succeeded.
    (out_dir / "READY").write_text("ok\n", encoding="utf-8")

