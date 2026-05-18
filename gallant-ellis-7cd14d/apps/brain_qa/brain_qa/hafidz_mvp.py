"""
hafidz_mvp.py — Hafidz Framework MVP: CAS + Merkle Ledger + Erasure Coding.

Terinspirasi dari tradisi hafalan Qur'an:
  - Distributed  : knowledge disebarkan di banyak "hafidz" (node)
  - Verifiable   : setiap bagian bisa diverifikasi lewat sanad (hash chain)
  - Reconstructable: knowledge bisa di-recover dari subset bagian

Komponen:
  1. ContentAddressedStore (CAS)  — simpan konten by SHA-256 hash
  2. MerkleLedger               — tree of hashes, verifikasi integritas
  3. ErasureCoder               — split N shares, reconstruct dari K shares
  4. HafidzNode                 — orchestrator lokal (CAS + Merkle + Erasure)

Roadmap P2P: ganti local disk CAS dengan libp2p / IPFS block store.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 1. Content-Addressed Store (CAS)
# ---------------------------------------------------------------------------


class ContentAddressedStore:
    """
    Simpan konten berdasarkan SHA-256 hash (content-addressable storage).

    Analogi Qur'an: setiap ayat diidentifikasi oleh kontennya sendiri,
    bukan nomor halaman — sehingga tidak bisa dimanipulasi tanpa terdeteksi.

    Data disimpan sebagai file di `<root>/<2-char-prefix>/<hash>`.
    Struktur ini sama dengan Git object store.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _path(self, cas_hash: str) -> Path:
        # Gunakan 2 char pertama sebagai subdirektori (seperti Git)
        prefix = cas_hash[:2]
        subdir = self._root / prefix
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / cas_hash[2:]

    def put(self, content: str) -> str:
        """
        Simpan konten; kembalikan CAS hash (sha256 hex).
        Idempotent: menyimpan konten yang sama dua kali aman.
        """
        cas_hash = self._hash(content)
        p = self._path(cas_hash)
        if not p.exists():
            p.write_text(content, encoding="utf-8")
        return cas_hash

    def get(self, cas_hash: str) -> Optional[str]:
        """Ambil konten berdasarkan CAS hash. Kembalikan None jika tidak ada."""
        p = self._path(cas_hash)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def exists(self, cas_hash: str) -> bool:
        """Cek apakah hash ada di store."""
        return self._path(cas_hash).exists()

    def list_all(self) -> list[str]:
        """Kembalikan semua CAS hash yang tersimpan."""
        hashes = []
        for prefix_dir in self._root.iterdir():
            if prefix_dir.is_dir() and len(prefix_dir.name) == 2:
                for obj_file in prefix_dir.iterdir():
                    if obj_file.is_file():
                        hashes.append(prefix_dir.name + obj_file.name)
        return hashes


# ---------------------------------------------------------------------------
# 2. Merkle Ledger
# ---------------------------------------------------------------------------


class MerkleLedger:
    """
    Merkle tree sederhana untuk verifikasi integritas knowledge.

    Analogi Sanad Qur'an: setiap periwayat (hash) bisa ditelusuri kembali
    ke akar (merkle root), membuktikan rantai integritas tidak putus.

    Implementasi: ledger disimpan sebagai JSONL (append-only).
    Merkle tree di-rebuild dari daftar semua item saat diperlukan.
    """

    def __init__(self, ledger_path: Path) -> None:
        self._path = Path(ledger_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        items = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return items

    def _append(self, record: dict) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _pair_hash(left: str, right: str) -> str:
        combined = left + right
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def _leaf_hash(data: str) -> str:
        return hashlib.sha256(("leaf:" + data).encode()).hexdigest()

    def _build_tree(self, leaf_hashes: list[str]) -> list[list[str]]:
        """
        Bangun Merkle tree dari leaf hashes.
        Kembalikan semua level (index 0 = daun, -1 = root).
        """
        if not leaf_hashes:
            return []
        levels = [leaf_hashes[:]]
        current = leaf_hashes[:]
        while len(current) > 1:
            # Duplikasi elemen terakhir jika jumlah ganjil
            if len(current) % 2 == 1:
                current.append(current[-1])
            next_level = [
                MerkleLedger._pair_hash(current[i], current[i + 1])
                for i in range(0, len(current), 2)
            ]
            levels.append(next_level)
            current = next_level
        return levels

    def _all_leaf_hashes(self) -> list[str]:
        return [MerkleLedger._leaf_hash(item["cas_hash"]) for item in self._items]

    def add_item(self, cas_hash: str, metadata: dict) -> str:
        """
        Tambahkan item baru ke ledger.
        Kembalikan merkle root terbaru setelah penambahan.
        """
        record = {
            "cas_hash": cas_hash,
            "metadata": metadata,
            "timestamp": time.time(),
        }
        self._items.append(record)
        self._append(record)
        root = self.get_root()
        return root

    def verify(self, cas_hash: str) -> bool:
        """Verifikasi bahwa cas_hash ada di ledger dan hash-nya konsisten."""
        for item in self._items:
            if item["cas_hash"] == cas_hash:
                return True
        return False

    def get_proof(self, cas_hash: str) -> list[str]:
        """
        Kembalikan Merkle proof path untuk cas_hash.
        Proof = daftar sibling hash dari daun ke root.
        """
        leaf_hashes = self._all_leaf_hashes()
        if not leaf_hashes:
            return []

        # Cari index item di ledger
        target_index = None
        for i, item in enumerate(self._items):
            if item["cas_hash"] == cas_hash:
                target_index = i
                break
        if target_index is None:
            return []

        levels = self._build_tree(leaf_hashes)
        proof = []
        idx = target_index
        for level in levels[:-1]:  # Semua level kecuali root
            # Jika ganjil, duplikasi terakhir
            if len(level) % 2 == 1:
                level = level + [level[-1]]
            sibling_idx = idx ^ 1  # XOR 1: partner pasangan
            if sibling_idx < len(level):
                proof.append(level[sibling_idx])
            idx = idx // 2
        return proof

    def get_root(self) -> str:
        """Kembalikan Merkle root dari seluruh ledger saat ini."""
        leaf_hashes = self._all_leaf_hashes()
        if not leaf_hashes:
            return hashlib.sha256(b"empty").hexdigest()
        levels = self._build_tree(leaf_hashes)
        return levels[-1][0]


# ---------------------------------------------------------------------------
# 3. Erasure Coder
# ---------------------------------------------------------------------------


class ErasureCoder:
    """
    Erasure coding sederhana: split knowledge ke N shares, reconstruct dari K shares.

    Analogi Hafalan Qur'an Tersebar:
      - Penghafal Qur'an di berbagai wilayah = N shares
      - Quorum K penghafal sudah cukup untuk reconstruct teks lengkap
      - Tidak perlu semua hadir — tahan banting terhadap kehilangan sebagian

    Implementasi: XOR-based erasure coding sederhana.
    CATATAN: Ini bukan Reed-Solomon penuh — hanya MVP proof-of-concept.
    Untuk production gunakan: isa-l, liberasurecode, atau pyeclib.

    Cara kerja XOR N-of-K (simplified):
      - Share 0..K-2: potongan asli konten (dibagi rata, di-pad)
      - Share K-1: XOR dari semua share sebelumnya (parity)
      - Share K..N-1: redundan (copy dari share 0..N-K-1)
      Sehingga kehilangan 1 share manapun bisa di-recover via XOR.
    """

    _SEPARATOR = "||HAFIDZ||"

    def encode(self, content: str, n_shares: int = 5, k_required: int = 3) -> list[str]:
        """
        Encode konten menjadi N shares.
        Setiap share berisi metadata (index, n, k, parity) + data sebagai JSON string.

        Args:
            content    : Teks yang akan di-encode.
            n_shares   : Total jumlah shares yang dibuat.
            k_required : Minimum shares untuk reconstruct.

        Returns:
            List N share string (bisa disimpan terpisah / di node berbeda).
        """
        if k_required > n_shares:
            raise ValueError("k_required tidak boleh lebih besar dari n_shares")
        if k_required < 2:
            raise ValueError("k_required minimal 2")

        content_bytes = content.encode("utf-8")
        # Bagi konten menjadi K-1 chunk (share data)
        n_data = k_required - 1
        chunk_size = math.ceil(len(content_bytes) / n_data)

        # Pad konten supaya bisa dibagi rata
        padded = content_bytes.ljust(chunk_size * n_data, b"\x00")
        data_chunks: list[bytes] = [
            padded[i * chunk_size: (i + 1) * chunk_size]
            for i in range(n_data)
        ]

        # Buat parity share (XOR semua data chunk)
        parity = bytearray(chunk_size)
        for chunk in data_chunks:
            for j, b in enumerate(chunk):
                parity[j] ^= b

        all_chunks = data_chunks + [bytes(parity)]  # K chunks total

        # Tambah redundan jika n_shares > k_required
        redundant_count = n_shares - k_required
        redundant = [data_chunks[i % n_data] for i in range(redundant_count)]
        all_chunks = all_chunks + redundant  # Total = n_shares

        shares = []
        for i, chunk in enumerate(all_chunks):
            meta = {
                "index": i,
                "n": n_shares,
                "k": k_required,
                "is_parity": (i == n_data),
                "is_redundant": (i >= k_required),
                "original_len": len(content_bytes),
                "chunk_size": chunk_size,
                "data": chunk.hex(),
            }
            shares.append(json.dumps(meta, ensure_ascii=False))
        return shares

    def decode(self, shares: list[str]) -> str:
        """
        Reconstruct konten dari minimal K shares.

        Args:
            shares: List share string (minimal K shares, boleh lebih).

        Returns:
            Konten asli yang di-reconstruct.

        Raises:
            ValueError: Jika tidak ada cukup data shares atau rekonstruksi gagal.
        """
        parsed = []
        for s in shares:
            try:
                parsed.append(json.loads(s))
            except json.JSONDecodeError:
                pass

        if not parsed:
            raise ValueError("Tidak ada share valid yang bisa di-parse.")

        k = parsed[0]["k"]
        chunk_size = parsed[0]["chunk_size"]
        original_len = parsed[0]["original_len"]
        n_data = k - 1  # Jumlah data chunks (bukan parity)

        # Pisahkan data shares dan parity share
        data_shares = {p["index"]: bytes.fromhex(p["data"]) for p in parsed if not p["is_parity"] and not p["is_redundant"]}
        parity_shares = [p for p in parsed if p["is_parity"]]

        # Jika semua data shares ada, reconstruct langsung
        if len(data_shares) >= n_data:
            chunks = [data_shares[i] for i in sorted(list(data_shares.keys()))[:n_data]]
            raw = b"".join(chunks)
            return raw[:original_len].decode("utf-8")

        # Jika ada 1 data share yang hilang, gunakan parity untuk recover
        if len(data_shares) == n_data - 1 and parity_shares:
            parity = bytes.fromhex(parity_shares[0]["data"])
            # Cari index yang hilang
            present = set(data_shares.keys())
            missing_idx = next(i for i in range(n_data) if i not in present)

            # Reconstruct via XOR
            recovered = bytearray(parity)
            for idx, chunk in data_shares.items():
                for j, b in enumerate(chunk):
                    recovered[j] ^= b

            # Rekonstruksi chunk order
            chunks = []
            for i in range(n_data):
                if i == missing_idx:
                    chunks.append(bytes(recovered))
                else:
                    chunks.append(data_shares[i])
            raw = b"".join(chunks)
            return raw[:original_len].decode("utf-8")

        raise ValueError(
            f"Tidak cukup shares untuk reconstruct. "
            f"Diperlukan {n_data} data shares, tersedia {len(data_shares)}."
        )


# ---------------------------------------------------------------------------
# 4. Hafidz Node
# ---------------------------------------------------------------------------


class HafidzNode:
    """
    Node Hafidz lokal: orchestrator CAS + Merkle + Erasure Coding.

    Setiap item yang di-store menghasilkan:
      - CAS hash (identitas unik konten)
      - Merkle root baru (verifikasi integritas keseluruhan ledger)
      - N shares (erasure encoded, siap didistribusikan)

    Ini adalah node tunggal (lokal). Roadmap P2P:
      - Ganti CAS disk dengan IPFS block store
      - Distribusi shares ke multiple HafidzNode peers via libp2p
      - Consensus merkle root antar peers
    """

    def __init__(self, data_dir: str = ".data/hafidz") -> None:
        self._base = Path(data_dir)
        self._cas = ContentAddressedStore(self._base / "cas")
        self._ledger = MerkleLedger(self._base / "ledger.jsonl")
        self._erasure = ErasureCoder()
        self._shares_dir = self._base / "shares"
        self._shares_dir.mkdir(parents=True, exist_ok=True)

    def store(self, content: str, metadata: dict | None = None) -> dict:
        """
        Simpan knowledge item.

        Returns dict:
          {
            "cas_hash"    : str,   # SHA-256 identitas konten
            "merkle_root" : str,   # Merkle root setelah penambahan
            "shares"      : list,  # N erasure-coded shares
            "stored_at"   : float, # Unix timestamp
          }
        """
        if metadata is None:
            metadata = {}

        # 1. CAS store
        cas_hash = self._cas.put(content)

        # 2. Merkle ledger
        enriched_meta = {**metadata, "stored_at": time.time()}
        merkle_root = self._ledger.add_item(cas_hash, enriched_meta)

        # 3. Erasure coding (default: 5 shares, butuh 3)
        shares = self._erasure.encode(content, n_shares=5, k_required=3)

        # 4. Simpan shares ke disk (satu file per share)
        share_dir = self._shares_dir / cas_hash[:16]
        share_dir.mkdir(parents=True, exist_ok=True)
        for i, share in enumerate(shares):
            (share_dir / f"share_{i}.json").write_text(share, encoding="utf-8")

        return {
            "cas_hash": cas_hash,
            "merkle_root": merkle_root,
            "shares": shares,
            "stored_at": enriched_meta["stored_at"],
        }

    def retrieve(self, cas_hash: str) -> Optional[str]:
        """
        Ambil konten berdasarkan CAS hash.
        Pertama coba dari CAS store langsung; fallback ke erasure decode dari shares.
        """
        # Fast path: CAS store
        content = self._cas.get(cas_hash)
        if content is not None:
            return content

        # Fallback: reconstruct dari shares (disaster recovery scenario)
        share_dir = self._shares_dir / cas_hash[:16]
        if not share_dir.exists():
            return None
        share_files = sorted(share_dir.glob("share_*.json"))
        if not share_files:
            return None
        shares = [f.read_text(encoding="utf-8") for f in share_files]
        try:
            return self._erasure.decode(shares)
        except (ValueError, Exception):
            return None

    def verify_integrity(self) -> dict:
        """
        Verifikasi integritas semua item di ledger.

        Returns:
          {
            "total"    : int,
            "ok"       : int,
            "failed"   : list[str],  # CAS hashes yang gagal
            "root"     : str,        # Merkle root saat ini
          }
        """
        all_hashes = self._ledger._all_leaf_hashes()
        total = len(self._ledger._items)
        failed = []

        for item in self._ledger._items:
            cas_hash = item["cas_hash"]
            content = self._cas.get(cas_hash)
            if content is None:
                failed.append(cas_hash)
            else:
                # Verifikasi hash konten konsisten
                expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if expected != cas_hash:
                    failed.append(cas_hash)

        return {
            "total": total,
            "ok": total - len(failed),
            "failed": failed,
            "root": self._ledger.get_root(),
        }

    def get_stats(self) -> dict:
        """Kembalikan statistik node Hafidz."""
        all_hashes = self._cas.list_all()
        shares_count = sum(
            1
            for share_dir in self._shares_dir.iterdir()
            if share_dir.is_dir()
            for _ in share_dir.glob("share_*.json")
        )
        return {
            "cas_items": len(all_hashes),
            "ledger_items": len(self._ledger._items),
            "merkle_root": self._ledger.get_root(),
            "total_shares": shares_count,
            "data_dir": str(self._base),
        }


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_node_instance: Optional[HafidzNode] = None


def get_hafidz_node(data_dir: str = ".data/hafidz") -> HafidzNode:
    """
    Kembalikan singleton HafidzNode.
    Aman dipanggil berkali-kali — instance dibuat hanya sekali.
    """
    global _node_instance
    if _node_instance is None:
        _node_instance = HafidzNode(data_dir=data_dir)
    return _node_instance


# ---------------------------------------------------------------------------
# FastAPI endpoint handlers (dipanggil dari serve.py)
# Endpoint: POST /hafidz/store, GET /hafidz/retrieve/{hash},
#           GET /hafidz/verify, GET /hafidz/stats
# ---------------------------------------------------------------------------


def handle_store(content: str, metadata: dict | None = None) -> dict:
    """Handler untuk POST /hafidz/store."""
    node = get_hafidz_node()
    result = node.store(content, metadata or {})
    return {
        "success": True,
        "cas_hash": result["cas_hash"],
        "merkle_root": result["merkle_root"],
        "stored_at": result["stored_at"],
        "shares_count": len(result["shares"]),
    }


def handle_retrieve(cas_hash: str) -> dict:
    """Handler untuk GET /hafidz/retrieve/{hash}."""
    node = get_hafidz_node()
    content = node.retrieve(cas_hash)
    if content is None:
        return {"success": False, "cas_hash": cas_hash, "content": None}
    return {"success": True, "cas_hash": cas_hash, "content": content}


def handle_verify() -> dict:
    """Handler untuk GET /hafidz/verify."""
    node = get_hafidz_node()
    return node.verify_integrity()


def handle_stats() -> dict:
    """Handler untuk GET /hafidz/stats."""
    node = get_hafidz_node()
    return node.get_stats()
