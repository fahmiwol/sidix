from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .paths import default_index_dir, load_manifest_paths


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_pair(left_hex: str, right_hex: str) -> str:
    # domain-separated pair hash for Merkle
    return _sha256_text(f"m1:{left_hex}:{right_hex}")


def merkle_root(leaves_hex: Iterable[str]) -> str:
    leaves = [x for x in leaves_hex if isinstance(x, str) and x]
    if not leaves:
        return _sha256_text("m0:empty")

    level = sorted(leaves)
    while len(level) > 1:
        nxt: list[str] = []
        it = iter(level)
        for left in it:
            right = next(it, left)  # duplicate last if odd
            nxt.append(_hash_pair(left, right))
        level = nxt
    return level[0]


@dataclass(frozen=True)
class Snapshot:
    created_at: str
    root: str
    leaf_count: int
    public_root: str
    prev_entry_hash: str | None
    entry_hash: str


def ledger_dir(index_dir_override: str | None) -> Path:
    idx = Path(index_dir_override) if index_dir_override else default_index_dir()
    return idx / "ledger"


def events_path(index_dir_override: str | None) -> Path:
    return ledger_dir(index_dir_override) / "events.jsonl"


def snapshots_path(index_dir_override: str | None) -> Path:
    return ledger_dir(index_dir_override) / "snapshots.jsonl"


def _iter_public_markdown_files(public_root: Path) -> list[Path]:
    if not public_root.exists():
        raise FileNotFoundError(f"Public markdown root not found: {public_root}")
    return sorted([p for p in public_root.rglob("*.md") if p.is_file()])


def _file_leaf_hash(*, rel_path: str, content_hash: str) -> str:
    # domain-separated leaf hash binds path + content
    return _sha256_text(f"leaf:{rel_path}:{content_hash}")


def compute_public_leaves(*, public_root: Path) -> tuple[list[str], int]:
    files = _iter_public_markdown_files(public_root)
    leaves: list[str] = []
    for p in files:
        rel = str(p.relative_to(public_root)).replace("\\", "/")
        raw = p.read_text(encoding="utf-8", errors="ignore")
        content_hash = _sha256_text(raw)
        leaves.append(_file_leaf_hash(rel_path=rel, content_hash=content_hash))
    return leaves, len(files)


def _append_event(index_dir_override: str | None, event: dict[str, Any]) -> None:
    path = events_path(index_dir_override)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(_canonical_json(event) + "\n")


def _last_entry_hash(index_dir_override: str | None) -> str | None:
    sp = snapshots_path(index_dir_override)
    if not sp.exists():
        return None
    last = None
    for line in sp.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        last = s
    if not last:
        return None
    try:
        obj = json.loads(last)
        h = obj.get("entry_hash")
        return h if isinstance(h, str) and h else None
    except Exception:
        return None


def create_snapshot(*, index_dir_override: str | None = None) -> Snapshot:
    manifest = load_manifest_paths()
    public_root = manifest.public_markdown_root

    leaves, file_count = compute_public_leaves(public_root=public_root)
    root = merkle_root(leaves)

    prev = _last_entry_hash(index_dir_override)
    entry: dict[str, Any] = {
        "kind": "snapshot",
        "created_at": _now_utc_iso(),
        "public_root": str(public_root),
        "leaf_count": len(leaves),
        "file_count": file_count,
        "merkle_root": root,
        "prev_entry_hash": prev,
    }
    entry_hash = _sha256_text(_canonical_json(entry))
    entry["entry_hash"] = entry_hash

    sp = snapshots_path(index_dir_override)
    sp.parent.mkdir(parents=True, exist_ok=True)
    with sp.open("a", encoding="utf-8", newline="\n") as f:
        f.write(_canonical_json(entry) + "\n")
    _append_event(index_dir_override, {"kind": "snapshot_created", "at": entry["created_at"], "entry_hash": entry_hash})

    return Snapshot(
        created_at=str(entry["created_at"]),
        root=str(root),
        leaf_count=int(len(leaves)),
        public_root=str(public_root),
        prev_entry_hash=prev,
        entry_hash=str(entry_hash),
    )


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    message: str
    latest_snapshot_root: str | None
    recomputed_root: str | None
    chain_ok: bool


def verify_latest_snapshot(*, index_dir_override: str | None = None) -> VerifyResult:
    sp = snapshots_path(index_dir_override)
    if not sp.exists():
        return VerifyResult(ok=False, message="No snapshots found.", latest_snapshot_root=None, recomputed_root=None, chain_ok=False)

    lines = [ln.strip() for ln in sp.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries: list[dict[str, Any]] = []
    for ln in lines:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                entries.append(obj)
        except Exception:
            return VerifyResult(ok=False, message="Snapshot log contains invalid JSON.", latest_snapshot_root=None, recomputed_root=None, chain_ok=False)

    # Verify chain
    prev: str | None = None
    for e in entries:
        if e.get("kind") != "snapshot":
            continue
        expected_prev = prev
        if e.get("prev_entry_hash") != expected_prev:
            return VerifyResult(ok=False, message="Snapshot chain broken (prev_entry_hash mismatch).", latest_snapshot_root=None, recomputed_root=None, chain_ok=False)
        copy = dict(e)
        entry_hash = copy.pop("entry_hash", None)
        if not isinstance(entry_hash, str) or not entry_hash:
            return VerifyResult(ok=False, message="Snapshot entry missing entry_hash.", latest_snapshot_root=None, recomputed_root=None, chain_ok=False)
        if _sha256_text(_canonical_json(copy)) != entry_hash:
            return VerifyResult(ok=False, message="Snapshot entry hash mismatch (tampering suspected).", latest_snapshot_root=None, recomputed_root=None, chain_ok=False)
        prev = entry_hash

    latest = entries[-1]
    latest_root = latest.get("merkle_root")
    if not isinstance(latest_root, str) or not latest_root:
        return VerifyResult(ok=False, message="Latest snapshot missing merkle_root.", latest_snapshot_root=None, recomputed_root=None, chain_ok=True)

    manifest = load_manifest_paths()
    public_root = manifest.public_markdown_root
    leaves, _ = compute_public_leaves(public_root=public_root)
    recomputed = merkle_root(leaves)

    if recomputed != latest_root:
        return VerifyResult(
            ok=False,
            message="Recomputed root does not match latest snapshot (corpus changed since snapshot).",
            latest_snapshot_root=str(latest_root),
            recomputed_root=str(recomputed),
            chain_ok=True,
        )

    return VerifyResult(
        ok=True,
        message="OK (chain valid, root matches current corpus).",
        latest_snapshot_root=str(latest_root),
        recomputed_root=str(recomputed),
        chain_ok=True,
    )


def ledger_status(index_dir_override: str | None = None) -> dict[str, Any]:
    d = ledger_dir(index_dir_override)
    sp = snapshots_path(index_dir_override)
    ev = events_path(index_dir_override)
    return {
        "ledger_dir": str(d),
        "snapshots_path": str(sp),
        "events_path": str(ev),
        "snapshots_count": sum(1 for ln in sp.read_text(encoding="utf-8").splitlines() if ln.strip()) if sp.exists() else 0,
        "events_count": sum(1 for ln in ev.read_text(encoding="utf-8").splitlines() if ln.strip()) if ev.exists() else 0,
    }

