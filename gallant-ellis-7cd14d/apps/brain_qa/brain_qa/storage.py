from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reedsolo import RSCodec

from .paths import default_index_dir, workspace_root


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _cid_for_sha256(hex_digest: str) -> str:
    # Simple CID-like identifier (not multiformats CID yet).
    return f"sha256:{hex_digest}"


def storage_dir(index_dir_override: str | None = None) -> Path:
    idx = Path(index_dir_override) if index_dir_override else default_index_dir()
    return idx / "storage"


def storage_manifest_path(index_dir_override: str | None = None) -> Path:
    return storage_dir(index_dir_override) / "manifest.json"


def nodes_path(index_dir_override: str | None = None) -> Path:
    return storage_dir(index_dir_override) / "nodes.json"


def locator_path(index_dir_override: str | None = None) -> Path:
    return storage_dir(index_dir_override) / "locator.json"


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "items": {}}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict) and isinstance(obj.get("items"), dict):
            return obj
    except Exception:
        pass
    return {"version": 1, "items": {}}


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return default


def _save_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_node(*, name: str, path: str, index_dir_override: str | None = None) -> dict[str, Any]:
    n = name.strip()
    if not n:
        raise ValueError("Node name is required.")
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

    np = nodes_path(index_dir_override)
    nodes = _load_json_or_default(np, {"version": 1, "nodes": {}})
    nodes_map: dict[str, Any] = nodes.get("nodes", {})
    nodes_map[n] = {"name": n, "path": str(p.resolve()), "added_at": _now_utc_iso()}
    nodes["nodes"] = nodes_map
    nodes["updated_at"] = _now_utc_iso()
    _save_json(np, nodes)
    return nodes_map[n]


def list_nodes(*, index_dir_override: str | None = None) -> list[dict[str, Any]]:
    np = nodes_path(index_dir_override)
    nodes = _load_json_or_default(np, {"version": 1, "nodes": {}})
    nodes_map: dict[str, Any] = nodes.get("nodes", {})
    out: list[dict[str, Any]] = []
    for k in sorted(nodes_map.keys()):
        v = nodes_map.get(k)
        if isinstance(v, dict):
            out.append(v)
    return out


def _load_locator(index_dir_override: str | None = None) -> dict[str, Any]:
    lp = locator_path(index_dir_override)
    return _load_json_or_default(lp, {"version": 1, "shards": {}})


def _save_locator(locator: dict[str, Any], index_dir_override: str | None = None) -> None:
    lp = locator_path(index_dir_override)
    locator["updated_at"] = _now_utc_iso()
    _save_json(lp, locator)


def _node_by_name(name: str, index_dir_override: str | None = None) -> dict[str, Any] | None:
    for n in list_nodes(index_dir_override=index_dir_override):
        if n.get("name") == name:
            return n
    return None


def distribute_pack_to_nodes(
    *,
    file_cid: str,
    node_names: list[str],
    index_dir_override: str | None = None,
) -> dict[str, Any]:
    """
    Copy shards from local pack dir into multiple node folders (round-robin),
    and record shard locations in locator.json.
    """
    if not node_names:
        raise ValueError("node_names required")

    pack_dir = _pack_dir_for_cid(file_cid, index_dir_override)
    mpath = pack_dir / "pack_manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(f"Pack not found for CID: {file_cid}")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    shards = manifest.get("shards", [])
    if not isinstance(shards, list) or not shards:
        raise ValueError("Pack manifest has no shards.")

    locator = _load_locator(index_dir_override)
    shard_map: dict[str, Any] = locator.get("shards", {})

    placed: list[dict[str, Any]] = []
    for i, s in enumerate(shards):
        shard_cid = str(s.get("cid", ""))
        shard_path = Path(str(s.get("path", "")))
        if not shard_cid or not shard_path.exists():
            continue

        node_name = node_names[i % len(node_names)]
        node = _node_by_name(node_name, index_dir_override=index_dir_override)
        if not node:
            raise FileNotFoundError(f"Node not found: {node_name}")
        node_root = Path(str(node["path"]))
        dst_dir = node_root / "mighan_storage" / "shards"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_path = dst_dir / f"{shard_cid.replace(':','_')}.bin"
        dst_path.write_bytes(shard_path.read_bytes())

        loc_entry = {
            "node": node_name,
            "path": str(dst_path),
            "added_at": _now_utc_iso(),
            "file_cid": file_cid,
            "shard_index": int(s.get("index", -1)),
        }
        existing = shard_map.get(shard_cid)
        if not isinstance(existing, list):
            existing = []
        existing.append(loc_entry)
        shard_map[shard_cid] = existing
        placed.append(loc_entry)

    locator["shards"] = shard_map
    _save_locator(locator, index_dir_override)
    return {"ok": True, "file_cid": file_cid, "placed": placed, "placed_count": len(placed)}


@dataclass(frozen=True)
class StorageItem:
    cid: str
    rel_path: str
    abs_path: str
    size_bytes: int
    sha256: str
    added_at: str


def _rel_to_workspace(p: Path) -> str:
    try:
        rel = str(p.resolve().relative_to(workspace_root().resolve()))
    except Exception:
        rel = str(p)
    return rel.replace("\\", "/")


def add_file(*, file_path: str, index_dir_override: str | None = None) -> StorageItem:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not p.is_file():
        raise ValueError(f"Not a file: {file_path}")

    sha = _sha256_file(p)
    cid = _cid_for_sha256(sha)
    size = p.stat().st_size
    rel = _rel_to_workspace(p)

    item = StorageItem(
        cid=cid,
        rel_path=rel,
        abs_path=str(p.resolve()),
        size_bytes=int(size),
        sha256=sha,
        added_at=_now_utc_iso(),
    )

    mpath = storage_manifest_path(index_dir_override)
    manifest = _load_manifest(mpath)
    items = manifest.get("items", {})
    items[cid] = {
        "cid": item.cid,
        "rel_path": item.rel_path,
        "abs_path": item.abs_path,
        "size_bytes": item.size_bytes,
        "sha256": item.sha256,
        "added_at": item.added_at,
    }
    manifest["items"] = items
    manifest["updated_at"] = _now_utc_iso()
    _save_manifest(mpath, manifest)
    return item


def verify_item(*, cid: str, index_dir_override: str | None = None) -> dict[str, Any]:
    mpath = storage_manifest_path(index_dir_override)
    manifest = _load_manifest(mpath)
    items: dict[str, Any] = manifest.get("items", {})
    it = items.get(cid)
    if not isinstance(it, dict):
        return {"ok": False, "message": "CID not found in manifest.", "cid": cid}

    path = Path(str(it.get("abs_path", "")))
    if not path.exists():
        return {"ok": False, "message": "File missing on disk.", "cid": cid, "abs_path": str(path)}

    sha_now = _sha256_file(path)
    ok = sha_now == str(it.get("sha256"))
    return {
        "ok": ok,
        "cid": cid,
        "abs_path": str(path),
        "expected_sha256": str(it.get("sha256")),
        "actual_sha256": sha_now,
        "message": "OK (hash matches)." if ok else "Hash mismatch (file changed).",
    }


def export_item(*, cid: str, dest_dir: str, index_dir_override: str | None = None) -> Path:
    mpath = storage_manifest_path(index_dir_override)
    manifest = _load_manifest(mpath)
    items: dict[str, Any] = manifest.get("items", {})
    it = items.get(cid)
    if not isinstance(it, dict):
        raise FileNotFoundError(f"CID not found: {cid}")

    src = Path(str(it.get("abs_path", "")))
    if not src.exists():
        raise FileNotFoundError(f"Source file missing: {src}")

    ddir = Path(dest_dir)
    ddir.mkdir(parents=True, exist_ok=True)
    out = ddir / src.name
    out.write_bytes(src.read_bytes())
    return out


def storage_status(index_dir_override: str | None = None) -> dict[str, Any]:
    mpath = storage_manifest_path(index_dir_override)
    manifest = _load_manifest(mpath)
    items: dict[str, Any] = manifest.get("items", {})
    total_bytes = 0
    for v in items.values():
        if isinstance(v, dict):
            sb = v.get("size_bytes")
            if isinstance(sb, int) and sb >= 0:
                total_bytes += sb
    return {
        "storage_dir": str(storage_dir(index_dir_override)),
        "manifest_path": str(mpath),
        "item_count": len(items),
        "total_bytes": total_bytes,
        "updated_at": manifest.get("updated_at"),
    }


def packs_dir(index_dir_override: str | None = None) -> Path:
    return storage_dir(index_dir_override) / "packs"


def _pack_dir_for_cid(cid: str, index_dir_override: str | None = None) -> Path:
    safe = cid.replace(":", "_")
    return packs_dir(index_dir_override) / safe


def pack_file_4_2(*, file_path: str, index_dir_override: str | None = None) -> dict[str, Any]:
    """
    Create 4+2 erasure-coded shards for a file.
    - 4 data shards + 2 parity shards.
    - Any 4 of 6 can reconstruct (tolerates 2 missing shards).
    """
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    raw = p.read_bytes()
    orig_size = len(raw)
    sha = _sha256_bytes(raw)
    cid = _cid_for_sha256(sha)

    k = 4
    m = 2
    n = k + m
    shard_size = (orig_size + k - 1) // k
    padded = raw + b"\x00" * (shard_size * k - orig_size)

    data_shards = [bytearray(shard_size) for _ in range(k)]
    for i in range(shard_size):
        for s in range(k):
            data_shards[s][i] = padded[i * k + s]

    rs = RSCodec(m)  # nsym = parity bytes
    parity_shards = [bytearray(shard_size) for _ in range(m)]
    for i in range(shard_size):
        msg = bytes([data_shards[0][i], data_shards[1][i], data_shards[2][i], data_shards[3][i]])
        codeword = rs.encode(msg)  # len 6
        parity_shards[0][i] = codeword[4]
        parity_shards[1][i] = codeword[5]

    out_dir = _pack_dir_for_cid(cid, index_dir_override)
    out_dir.mkdir(parents=True, exist_ok=True)

    shard_paths: list[str] = []
    shard_cids: list[str] = []
    for idx, shard in enumerate(list(data_shards) + list(parity_shards)):
        sp = out_dir / f"shard_{idx}.bin"
        sp.write_bytes(bytes(shard))
        shard_paths.append(str(sp))
        shard_cids.append(_cid_for_sha256(_sha256_bytes(bytes(shard))))

    manifest = {
        "version": 1,
        "created_at": _now_utc_iso(),
        "scheme": "rs_4_2",
        "k": k,
        "m": m,
        "n": n,
        "file": {
            "cid": cid,
            "abs_path": str(p.resolve()),
            "rel_path": _rel_to_workspace(p),
            "orig_size": orig_size,
            "sha256": sha,
        },
        "shard_size": shard_size,
        "shards": [
            {"index": i, "path": shard_paths[i], "cid": shard_cids[i]} for i in range(n)
        ],
    }
    (out_dir / "pack_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def reconstruct_pack_4_2(*, pack_dir: str, out_path: str, index_dir_override: str | None = None) -> dict[str, Any]:
    """
    Reconstruct original file from any 4 of 6 shards in a pack directory.
    `pack_dir` should contain `pack_manifest.json` and shard_*.bin files.
    """
    d = Path(pack_dir)
    mpath = d / "pack_manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(f"pack_manifest.json not found in: {pack_dir}")

    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    if manifest.get("scheme") != "rs_4_2":
        raise ValueError("Unsupported pack scheme.")

    k = int(manifest["k"])
    m = int(manifest["m"])
    n = int(manifest["n"])
    shard_size = int(manifest["shard_size"])
    orig_size = int(manifest["file"]["orig_size"])
    expected_sha = str(manifest["file"]["sha256"])

    shards: list[bytes | None] = [None] * n
    missing: list[int] = []
    for s in manifest["shards"]:
        idx = int(s["index"])
        sp = Path(str(s["path"]))
        if sp.exists():
            shards[idx] = sp.read_bytes()
        else:
            missing.append(idx)

    if len(missing) > 2:
        return {"ok": False, "message": f"Terlalu banyak shard hilang: {missing} (max 2)."}

    rs = RSCodec(m)
    data_out = bytearray(shard_size * k)
    for i in range(shard_size):
        codeword = bytearray(n)
        erasures: list[int] = []
        for j in range(n):
            b = shards[j]
            if b is None:
                codeword[j] = 0
                erasures.append(j)
            else:
                codeword[j] = b[i]
        decoded = rs.decode(bytes(codeword), erase_pos=erasures)[0]  # 4 bytes
        data_out[i * k + 0] = decoded[0]
        data_out[i * k + 1] = decoded[1]
        data_out[i * k + 2] = decoded[2]
        data_out[i * k + 3] = decoded[3]

    rebuilt = bytes(data_out[:orig_size])
    sha_now = _sha256_bytes(rebuilt)
    ok = sha_now == expected_sha

    op = Path(out_path)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_bytes(rebuilt)

    return {
        "ok": ok,
        "out_path": str(op),
        "expected_sha256": expected_sha,
        "actual_sha256": sha_now,
        "message": "OK (reconstruct + hash match)." if ok else "Reconstruct done, but hash mismatch.",
    }


def reconstruct_from_nodes_4_2(*, file_cid: str, out_path: str, index_dir_override: str | None = None) -> dict[str, Any]:
    """
    Reconstruct file using locator.json + local pack_manifest.json.
    It tolerates up to 2 missing shards across local/remote locations.
    """
    pack_dir = _pack_dir_for_cid(file_cid, index_dir_override)
    mpath = pack_dir / "pack_manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(f"Pack manifest not found for CID: {file_cid}")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    shards_meta = manifest.get("shards", [])
    if not isinstance(shards_meta, list) or not shards_meta:
        raise ValueError("Pack manifest missing shards.")

    locator = _load_locator(index_dir_override)
    shard_map: dict[str, Any] = locator.get("shards", {})

    # Build shard byte arrays (try local path first, then any locator entry)
    n = int(manifest["n"])
    shards: list[bytes | None] = [None] * n
    missing: list[int] = []
    for s in shards_meta:
        idx = int(s.get("index", -1))
        shard_cid = str(s.get("cid", ""))
        local_path = Path(str(s.get("path", "")))
        data: bytes | None = None
        if local_path.exists():
            data = local_path.read_bytes()
        else:
            locs = shard_map.get(shard_cid)
            if isinstance(locs, list):
                for le in locs:
                    if not isinstance(le, dict):
                        continue
                    sp = Path(str(le.get("path", "")))
                    if sp.exists():
                        data = sp.read_bytes()
                        break
        shards[idx] = data
        if data is None:
            missing.append(idx)

    if len(missing) > 2:
        return {"ok": False, "message": f"Terlalu banyak shard hilang: {missing} (max 2)."}

    # Delegate to the same RS reconstruction logic by temporarily using manifest paths list.
    # We reuse the core logic from reconstruct_pack_4_2 by inlining decode.
    k = int(manifest["k"])
    m = int(manifest["m"])
    n = int(manifest["n"])
    shard_size = int(manifest["shard_size"])
    orig_size = int(manifest["file"]["orig_size"])
    expected_sha = str(manifest["file"]["sha256"])

    rs = RSCodec(m)
    data_out = bytearray(shard_size * k)
    for i in range(shard_size):
        codeword = bytearray(n)
        erasures: list[int] = []
        for j in range(n):
            b = shards[j]
            if b is None:
                codeword[j] = 0
                erasures.append(j)
            else:
                codeword[j] = b[i]
        decoded = rs.decode(bytes(codeword), erase_pos=erasures)[0]
        data_out[i * k + 0] = decoded[0]
        data_out[i * k + 1] = decoded[1]
        data_out[i * k + 2] = decoded[2]
        data_out[i * k + 3] = decoded[3]

    rebuilt = bytes(data_out[:orig_size])
    sha_now = _sha256_bytes(rebuilt)
    ok = sha_now == expected_sha

    op = Path(out_path)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_bytes(rebuilt)
    return {
        "ok": ok,
        "out_path": str(op),
        "expected_sha256": expected_sha,
        "actual_sha256": sha_now,
        "missing_shards": missing,
        "message": "OK (reconstruct from nodes + hash match)." if ok else "Reconstruct from nodes done, but hash mismatch.",
    }


def _read_shard_bytes_for_meta(
    *,
    shard_meta: dict[str, Any],
    shard_map: dict[str, Any],
) -> tuple[bytes | None, dict[str, Any]]:
    """
    Resolve shard bytes using:
    1) local path from pack manifest
    2) any existing locator entry path that exists on disk
    """
    idx = int(shard_meta.get("index", -1))
    shard_cid = str(shard_meta.get("cid", ""))
    local_path = Path(str(shard_meta.get("path", "")))

    diag: dict[str, Any] = {"index": idx, "shard_cid": shard_cid, "local_path": str(local_path)}

    if local_path.exists():
        data = local_path.read_bytes()
        diag["resolved_from"] = "pack_local"
        diag["resolved_path"] = str(local_path)
        return data, diag

    locs = shard_map.get(shard_cid)
    if isinstance(locs, list):
        for le in locs:
            if not isinstance(le, dict):
                continue
            sp = Path(str(le.get("path", "")))
            if sp.exists():
                diag["resolved_from"] = "locator"
                diag["resolved_path"] = str(sp)
                diag["resolved_node"] = le.get("node")
                return sp.read_bytes(), diag

    diag["resolved_from"] = None
    diag["resolved_path"] = None
    return None, diag


def audit_pack_4_2(*, file_cid: str, index_dir_override: str | None = None) -> dict[str, Any]:
    """
    Safety report for a packed file:
    - per-shard presence + hash match vs expected shard CID
    - counts of missing shards + whether reconstruction is possible (<=2 missing)
    """
    pack_dir = _pack_dir_for_cid(file_cid, index_dir_override)
    mpath = pack_dir / "pack_manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(f"Pack manifest not found for CID: {file_cid}")

    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    if manifest.get("scheme") != "rs_4_2":
        raise ValueError("Unsupported pack scheme (expected rs_4_2).")

    shards_meta = manifest.get("shards", [])
    if not isinstance(shards_meta, list) or not shards_meta:
        raise ValueError("Pack manifest missing shards.")

    locator = _load_locator(index_dir_override)
    shard_map: dict[str, Any] = locator.get("shards", {})

    per_shard: list[dict[str, Any]] = []
    missing: list[int] = []
    bad_hash: list[int] = []

    for s in shards_meta:
        if not isinstance(s, dict):
            continue
        data, diag = _read_shard_bytes_for_meta(shard_meta=s, shard_map=shard_map)
        idx = int(diag.get("index", -1))
        expected_shard_cid = str(diag.get("shard_cid", ""))

        if data is None:
            missing.append(idx)
            per_shard.append(
                {
                    **diag,
                    "present": False,
                    "actual_shard_cid": None,
                    "hash_ok": False,
                }
            )
            continue

        actual_cid = _cid_for_sha256(_sha256_bytes(data))
        hash_ok = bool(expected_shard_cid) and (actual_cid == expected_shard_cid)
        if not hash_ok:
            bad_hash.append(idx)

        per_shard.append(
            {
                **diag,
                "present": True,
                "actual_shard_cid": actual_cid,
                "hash_ok": hash_ok,
            }
        )

    n = int(manifest["n"])
    missing_count = len(missing)
    good_count = sum(1 for s in per_shard if s.get("present") and s.get("hash_ok"))
    # For RS(4,2), reconstruction needs any 4 shards with correct bytes.
    recon_possible = (good_count >= int(manifest.get("k", 4))) and (len(bad_hash) == 0)
    strict_ok = (missing_count == 0) and (len(bad_hash) == 0)
    recoverable = recon_possible and (not strict_ok)

    if strict_ok:
        msg = "OK (all shards present + shard hashes match)."
    elif bad_hash:
        msg = "FAIL: hash mismatch on one or more present shards."
    elif not recon_possible:
        msg = f"FAIL: not enough valid shards for 4+2 reconstruction (need >=4 good shards; have {good_count})."
    else:
        msg = f"WARN: {missing_count} shard(s) missing on disk, but >=4 valid shards exist (reconstruction likely possible)."

    return {
        # Strict audit: all shards must be present on disk somewhere we can read,
        # and every present shard must match its expected shard CID.
        "ok": strict_ok,
        # Softer signal: if the only problem is missing shards (no hash corruption),
        # reconstruction may still be possible under 4+2.
        "recoverable": recoverable,
        "file_cid": file_cid,
        "pack_dir": str(pack_dir),
        "manifest_path": str(mpath),
        "n": n,
        "missing_shard_indexes": missing,
        "missing_count": missing_count,
        "good_shard_count": good_count,
        "bad_hash_indexes": bad_hash,
        "reconstruction_possible_if_missing_only": recon_possible,
        "shards": per_shard,
        "message": msg,
    }


def rebalance_pack_4_2(
    *,
    file_cid: str,
    target_node: str,
    index_dir_override: str | None = None,
) -> dict[str, Any]:
    """
    Best-effort repair:
    For each shard in the pack, if it is missing at `target_node`, copy bytes from any
    known existing location (local pack path or locator paths) into the target node shard dir.

    Also appends a locator entry for the copied shard (similar to distribute_pack_to_nodes).
    """
    node = _node_by_name(target_node, index_dir_override=index_dir_override)
    if not node:
        raise FileNotFoundError(f"Node not found: {target_node}")

    pack_dir = _pack_dir_for_cid(file_cid, index_dir_override)
    mpath = pack_dir / "pack_manifest.json"
    if not mpath.exists():
        raise FileNotFoundError(f"Pack manifest not found for CID: {file_cid}")

    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    if manifest.get("scheme") != "rs_4_2":
        raise ValueError("Unsupported pack scheme (expected rs_4_2).")

    shards_meta = manifest.get("shards", [])
    if not isinstance(shards_meta, list) or not shards_meta:
        raise ValueError("Pack manifest missing shards.")

    locator = _load_locator(index_dir_override)
    shard_map: dict[str, Any] = locator.get("shards", {})

    node_root = Path(str(node["path"]))
    dst_dir = node_root / "mighan_storage" / "shards"
    dst_dir.mkdir(parents=True, exist_ok=True)

    copied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for s in shards_meta:
        if not isinstance(s, dict):
            continue
        shard_cid = str(s.get("cid", ""))
        idx = int(s.get("index", -1))
        if not shard_cid:
            failed.append({"index": idx, "reason": "missing shard cid in manifest"})
            continue

        dst_path = dst_dir / f"{shard_cid.replace(':','_')}.bin"
        if dst_path.exists():
            skipped.append({"index": idx, "shard_cid": shard_cid, "path": str(dst_path), "reason": "already exists"})
            continue

        data, _diag = _read_shard_bytes_for_meta(shard_meta=s, shard_map=shard_map)
        if data is None:
            failed.append({"index": idx, "shard_cid": shard_cid, "reason": "no source bytes found"})
            continue

        dst_path.write_bytes(data)

        loc_entry = {
            "node": target_node,
            "path": str(dst_path),
            "added_at": _now_utc_iso(),
            "file_cid": file_cid,
            "shard_index": idx,
            "source": "rebalance",
        }
        existing = shard_map.get(shard_cid)
        if not isinstance(existing, list):
            existing = []
        existing.append(loc_entry)
        shard_map[shard_cid] = existing
        copied.append(loc_entry)

    locator["shards"] = shard_map
    _save_locator(locator, index_dir_override)

    return {
        "ok": len(failed) == 0,
        "file_cid": file_cid,
        "target_node": target_node,
        "copied_count": len(copied),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "copied": copied,
        "skipped": skipped,
        "failed": failed,
    }
