"""
corpus.py — SIDIX Corpus Management Helpers
"""

from __future__ import annotations
from pathlib import Path
from .paths import default_index_dir

def get_corpus_stats() -> dict[str, int]:
    """
    Get statistics about the RAG corpus.
    Used by sensor_hub to probe text_read capability.
    """
    index_dir = default_index_dir()
    chunks_path = index_dir / "chunks.jsonl"
    
    doc_count = 0
    chunk_count = 0
    
    if chunks_path.exists():
        try:
            lines = chunks_path.read_text(encoding="utf-8").splitlines()
            chunk_count = sum(1 for line in lines if line.strip())
            
            # Estimate doc count (this is rough if not tracked in meta)
            # Actually index_meta.json might have it if it exists.
            import json
            meta_path = index_dir / "index_meta.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                doc_count = meta.get("doc_count", 0)
            
            # Fallback doc count from chunks if meta is missing
            if doc_count == 0 and chunk_count > 0:
                # Heuristic: just say we have documents if we have chunks
                doc_count = max(1, chunk_count // 5) 
        except Exception:
            pass

    return {
        "doc_count": doc_count,
        "chunk_count": chunk_count
    }

def is_available() -> bool:
    """Check if corpus is ready for reading."""
    index_dir = default_index_dir()
    return (index_dir / "READY").exists()
