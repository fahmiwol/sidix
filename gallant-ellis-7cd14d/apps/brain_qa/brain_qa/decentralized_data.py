"""
decentralized_data.py — Decentralized Data dengan Recall Memory SIDIX

Konsep:
  Data tidak disimpan monolitik di satu tempat, tapi dipecah menjadi
  fragment-fragment kecil yang terdistribusi secara terstruktur.

  Seperti Hafidz Al-Quran yang menyimpan ilmu di berbagai "node" (hafidz),
  data SIDIX disimpan dalam fragments yang bisa di-assemble kembali.

  Terinspirasi:
  - Hafidz Framework (research note 22)
  - DIKW Pyramid (Data → Information → Knowledge → Wisdom)
  - Merkle Tree (integrity verification via hash)
  - Erasure Coding (redundancy tanpa duplikasi penuh)

Storage:
  .data/decentralized/
    index.json          ← master index semua fragment
    fragments/          ← satu JSON per fragment
      {fragment_id}.json
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────────

DEFAULT_DATA_DIR = Path(".data") / "decentralized"
MIN_RELEVANCE_THRESHOLD = 0.1

# Tag hierarchy (DIKW levels)
DIKW_LEVELS = ["data", "information", "knowledge", "wisdom"]


# ─────────────────────────────────────────────
# KELAS FRAGMENT
# ─────────────────────────────────────────────

class Fragment:
    """Satu unit data yang dapat berdiri sendiri."""

    def __init__(
        self,
        content: str,
        tags: list[str],
        source: str,
        dikw_level: str = "information",
        metadata: Optional[dict] = None,
    ):
        # Fragment ID = hash dari content (content-addressable)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.fragment_id = f"frag_{content_hash[:16]}"
        self.content = content
        self.tags = list(set(tags))  # dedupe tags
        self.source = source
        self.dikw_level = dikw_level if dikw_level in DIKW_LEVELS else "information"
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.accessed_at = datetime.now().isoformat()
        self.access_count = 0
        self.relevance_score = 1.0  # Starts at max, may decay
        # Merkle-inspired: hash of content for integrity
        self.content_hash = content_hash

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "Fragment":
        f = cls.__new__(cls)
        f.__dict__.update(d)
        return f

    def touch(self) -> None:
        """Update access timestamp dan count."""
        self.accessed_at = datetime.now().isoformat()
        self.access_count += 1

    def keyword_score(self, query_terms: list[str]) -> float:
        """
        Score relevansi fragment terhadap query terms.
        BM25-simplified: term frequency + tag bonus.
        """
        content_lower = self.content.lower()
        tag_str = " ".join(self.tags).lower()

        score = 0.0
        for term in query_terms:
            term_lower = term.lower()
            # Content matches
            content_count = content_lower.count(term_lower)
            # Tag exact match (bonus)
            tag_match = 1.0 if term_lower in tag_str else 0.0

            score += (content_count * 0.5 + tag_match * 1.5)

        # Normalize oleh panjang content (tidak bias ke content panjang)
        content_words = max(len(content_lower.split()), 1)
        normalized = score / (1 + math.log(content_words)) if score > 0 else 0.0

        return min(1.0, normalized)

    def get_summary(self, max_chars: int = 150) -> str:
        """Dapatkan summary singkat dari fragment."""
        clean = re.sub(r'\s+', ' ', self.content).strip()
        return clean[:max_chars] + ("..." if len(clean) > max_chars else "")


# Import math setelah class definition untuk menghindari circular issues
try:
    import math
except ImportError:
    class math:
        @staticmethod
        def log(x):
            return x  # Fallback minimal


# ─────────────────────────────────────────────
# KELAS UTAMA
# ─────────────────────────────────────────────

class DecentralizedData:
    """
    Decentralized Data Store dengan recall memory terstruktur.

    Setiap unit pengetahuan disimpan sebagai fragment independen.
    Fragments bisa di-query secara semantik dan di-assemble kembali
    menjadi pengetahuan yang koheren.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.fragments_dir = self.data_dir / "fragments"
        self.fragments_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}  # fragment_id → metadata ringkas
        self._fragments_cache: dict[str, Fragment] = {}  # hot cache
        self._load_index()

    # ─── STORE ───

    def store_fragment(
        self,
        content: str,
        tags: list[str],
        source: str,
        dikw_level: str = "information",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Simpan fragment baru.

        Args:
            content: konten fragment (teks)
            tags: list tag untuk indexing
            source: asal fragment (URL, file path, "manual", dsb)
            dikw_level: posisi di DIKW pyramid
            metadata: metadata tambahan (author, date, dsb)

        Returns:
            fragment_id
        """
        if not content or not content.strip():
            raise ValueError("Content tidak boleh kosong")

        fragment = Fragment(
            content=content.strip(),
            tags=tags,
            source=source,
            dikw_level=dikw_level,
            metadata=metadata or {},
        )

        # Cek duplikat (content-addressable)
        if fragment.fragment_id in self._index:
            # Update tags dan access
            existing = self._load_fragment(fragment.fragment_id)
            if existing:
                existing.tags = list(set(existing.tags + tags))
                existing.touch()
                self._save_fragment(existing)
                return fragment.fragment_id

        # Simpan fragment baru
        self._fragments_cache[fragment.fragment_id] = fragment
        self._save_fragment(fragment)
        self._update_index(fragment)

        return fragment.fragment_id

    def store_text_chunked(
        self,
        text: str,
        source: str,
        base_tags: list[str],
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[str]:
        """
        Simpan teks panjang dengan memecahnya menjadi chunks.

        Args:
            text: teks panjang yang akan di-chunk
            source: asal teks
            base_tags: tag dasar untuk semua chunk
            chunk_size: ukuran chunk dalam karakter
            overlap: overlap antar chunk untuk konteks

        Returns:
            list of fragment_ids
        """
        chunks = self._chunk_text(text, chunk_size, overlap)
        fragment_ids = []

        for i, chunk in enumerate(chunks):
            chunk_tags = base_tags + [f"chunk_{i+1}_of_{len(chunks)}"]
            fid = self.store_fragment(
                content=chunk,
                tags=chunk_tags,
                source=f"{source}#chunk{i+1}",
                dikw_level="information",
                metadata={"chunk_index": i, "total_chunks": len(chunks)},
            )
            fragment_ids.append(fid)

        return fragment_ids

    # ─── RECALL ───

    def recall(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Cari fragment yang paling relevan dengan query.

        Menggunakan keyword matching + tag scoring.
        Dalam produksi: bisa diganti/augmented dengan embedding search.

        Args:
            query: query dalam bahasa natural
            top_k: jumlah hasil teratas

        Returns:
            list of dict fragment dengan relevance score
        """
        if not self._index:
            return []

        query_terms = self._tokenize(query)
        results = []

        for fid in list(self._index.keys()):
            fragment = self._load_fragment(fid)
            if not fragment:
                continue

            # Hitung relevance
            keyword_rel = fragment.keyword_score(query_terms)

            # Tag bonus
            tag_matches = sum(
                1 for t in fragment.tags
                if any(q in t.lower() for q in query_terms)
            )
            tag_bonus = min(0.3, tag_matches * 0.1)

            # DIKW level bonus (knowledge > information > data > wisdom for recall)
            dikw_bonus = {"knowledge": 0.1, "information": 0.05, "data": 0.0, "wisdom": 0.08}.get(
                fragment.dikw_level, 0.0
            )

            total_relevance = min(1.0, keyword_rel + tag_bonus + dikw_bonus)

            if total_relevance >= MIN_RELEVANCE_THRESHOLD:
                fragment.touch()
                results.append({
                    "fragment_id": fid,
                    "content": fragment.content,
                    "summary": fragment.get_summary(),
                    "tags": fragment.tags,
                    "source": fragment.source,
                    "dikw_level": fragment.dikw_level,
                    "relevance": round(total_relevance, 3),
                    "access_count": fragment.access_count,
                })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:top_k]

    # ─── ASSEMBLY ───

    def assemble(self, fragment_ids: list[str], separator: str = "\n\n---\n\n") -> str:
        """
        Rekonstruksi pengetahuan dari fragment-fragment.

        Args:
            fragment_ids: list ID fragment yang ingin diassemble
            separator: pemisah antar fragment

        Returns:
            string konten yang telah diassemble
        """
        assembled_parts = []

        for fid in fragment_ids:
            fragment = self._load_fragment(fid)
            if fragment:
                # Header sederhana
                header = f"[{fragment.dikw_level.upper()} | {fragment.source}]"
                assembled_parts.append(f"{header}\n{fragment.content}")
                fragment.touch()
                self._save_fragment(fragment)

        if not assembled_parts:
            return "[Tidak ada fragment yang ditemukan untuk ID yang diberikan]"

        return separator.join(assembled_parts)

    def assemble_from_query(self, query: str, top_k: int = 5) -> str:
        """
        Shortcut: recall + assemble dalam satu langkah.

        Args:
            query: query
            top_k: jumlah fragment untuk diassemble

        Returns:
            string assembled
        """
        fragments = self.recall(query, top_k=top_k)
        if not fragments:
            return f"[Tidak ada fragment yang relevan untuk: '{query}']"

        fragment_ids = [f["fragment_id"] for f in fragments]
        return self.assemble(fragment_ids)

    # ─── MEMORY MAP ───

    def get_memory_map(self) -> dict:
        """
        Dapatkan peta visual dari apa yang tersimpan.

        Returns:
            dict summary dengan breakdown per tag, domain, DIKW level
        """
        if not self._index:
            return {
                "total_fragments": 0,
                "message": "Memory kosong. Gunakan store_fragment() untuk mengisi.",
            }

        fragments = [self._load_fragment(fid) for fid in self._index.keys()]
        fragments = [f for f in fragments if f is not None]

        # DIKW distribution
        dikw_dist: dict[str, int] = {}
        for f in fragments:
            dikw_dist[f.dikw_level] = dikw_dist.get(f.dikw_level, 0) + 1

        # Tag cloud
        tag_freq: dict[str, int] = {}
        for f in fragments:
            for tag in f.tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1

        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        # Source distribution
        source_dist: dict[str, int] = {}
        for f in fragments:
            src_key = f.source.split("#")[0]  # Remove chunk suffix
            source_dist[src_key] = source_dist.get(src_key, 0) + 1

        # Most accessed
        most_accessed = sorted(fragments, key=lambda f: f.access_count, reverse=True)[:5]

        # Total content size
        total_chars = sum(len(f.content) for f in fragments)

        return {
            "total_fragments": len(fragments),
            "total_content_chars": total_chars,
            "avg_fragment_size": round(total_chars / len(fragments)) if fragments else 0,
            "dikw_distribution": dikw_dist,
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
            "sources": list(source_dist.keys())[:10],
            "most_accessed": [
                {
                    "fragment_id": f.fragment_id,
                    "summary": f.get_summary(80),
                    "access_count": f.access_count,
                }
                for f in most_accessed
            ],
            "integrity_check": self._verify_integrity(fragments[:10]),
        }

    # ─── PRUNE ───

    def prune(self, min_relevance: float = 0.3) -> int:
        """
        Hapus fragment dengan relevance sangat rendah.

        CATATAN: Ini adalah satu-satunya cara menghapus data.
        Dalam permanent learning — hapus hanya yang memang tidak relevan,
        bukan karena belum sering diakses.

        Args:
            min_relevance: threshold minimum (fragment di bawah ini akan dihapus)

        Returns:
            jumlah fragment yang dihapus
        """
        removed = 0
        to_remove = []

        for fid, index_entry in list(self._index.items()):
            fragment = self._load_fragment(fid)
            if not fragment:
                to_remove.append(fid)
                continue

            # Score berdasarkan akses dan ukuran
            access_score = min(1.0, fragment.access_count / 10)
            size_score = min(1.0, len(fragment.content) / 200)
            composite = (access_score * 0.6 + size_score * 0.4)

            if composite < min_relevance:
                to_remove.append(fid)

        for fid in to_remove:
            # Hapus dari index
            if fid in self._index:
                del self._index[fid]
            # Hapus file
            frag_file = self.fragments_dir / f"{fid}.json"
            try:
                if frag_file.exists():
                    frag_file.unlink()
            except Exception:
                pass
            # Hapus dari cache
            self._fragments_cache.pop(fid, None)
            removed += 1

        self._save_index()
        return removed

    # ─── STATS ───

    def get_stats(self) -> dict:
        """Return statistik singkat data store."""
        return {
            "total_fragments": len(self._index),
            "cached_fragments": len(self._fragments_cache),
            "data_dir": str(self.data_dir),
            "fragments_dir": str(self.fragments_dir),
        }

    # ─── PRIVATE METHODS ───

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize query menjadi terms yang bermakna."""
        # Remove punctuation, lowercase, split
        clean = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = clean.split()

        # Remove stopwords bahasa Indonesia + Inggris
        stopwords = {
            "dan", "atau", "yang", "di", "ke", "dari", "pada", "dengan",
            "untuk", "ini", "itu", "adalah", "merupakan", "juga", "sudah",
            "the", "is", "are", "was", "in", "on", "at", "to", "for",
            "of", "and", "or", "a", "an",
        }
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Chunk teks panjang dengan overlap."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size

            # Cari word boundary
            if end < len(text):
                space_idx = text.rfind(' ', start, end)
                if space_idx > start:
                    end = space_idx

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start <= 0:
                break

        return chunks

    def _update_index(self, fragment: Fragment) -> None:
        """Update master index dengan fragment baru."""
        self._index[fragment.fragment_id] = {
            "fragment_id": fragment.fragment_id,
            "tags": fragment.tags,
            "source": fragment.source,
            "dikw_level": fragment.dikw_level,
            "created_at": fragment.created_at,
            "content_preview": fragment.content[:80],
            "content_hash": fragment.content_hash,
        }
        self._save_index()

    def _save_fragment(self, fragment: Fragment) -> None:
        """Simpan satu fragment ke file."""
        try:
            frag_file = self.fragments_dir / f"{fragment.fragment_id}.json"
            with open(frag_file, "w", encoding="utf-8") as f:
                json.dump(fragment.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_fragment(self, fragment_id: str) -> Optional[Fragment]:
        """Load fragment dari cache atau file."""
        # Hot cache
        if fragment_id in self._fragments_cache:
            return self._fragments_cache[fragment_id]

        # File
        try:
            frag_file = self.fragments_dir / f"{fragment_id}.json"
            if frag_file.exists():
                with open(frag_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                fragment = Fragment.from_dict(data)
                self._fragments_cache[fragment_id] = fragment
                return fragment
        except Exception:
            pass

        return None

    def _save_index(self) -> None:
        """Simpan master index."""
        try:
            index_file = self.data_dir / "index.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_index(self) -> None:
        """Load master index dari file."""
        try:
            index_file = self.data_dir / "index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
        except Exception:
            self._index = {}

    def _verify_integrity(self, fragments: list[Fragment]) -> dict:
        """
        Verifikasi integritas fragment sample menggunakan content hash.
        Terinspirasi Merkle Tree.
        """
        total = len(fragments)
        intact = 0
        corrupted = []

        for f in fragments:
            expected_hash = hashlib.sha256(f.content.encode()).hexdigest()
            if expected_hash == f.content_hash:
                intact += 1
            else:
                corrupted.append(f.fragment_id)

        return {
            "checked": total,
            "intact": intact,
            "corrupted": corrupted,
            "integrity_rate": round(intact / total, 2) if total > 0 else 1.0,
        }


# ─────────────────────────────────────────────
# SINGLETON & SHORTCUTS
# ─────────────────────────────────────────────

_default_store: Optional[DecentralizedData] = None


def get_store(data_dir: Optional[str] = None) -> DecentralizedData:
    """Dapatkan instance DecentralizedData default."""
    global _default_store
    if _default_store is None:
        _default_store = DecentralizedData(
            data_dir=Path(data_dir) if data_dir else None
        )
    return _default_store


def store(content: str, tags: list[str], source: str = "manual") -> str:
    """Shortcut: simpan fragment."""
    return get_store().store_fragment(content, tags, source)


def recall(query: str, top_k: int = 5) -> list[dict]:
    """Shortcut: recall fragments."""
    return get_store().recall(query, top_k=top_k)


def assemble(fragment_ids: list[str]) -> str:
    """Shortcut: assemble fragments."""
    return get_store().assemble(fragment_ids)
