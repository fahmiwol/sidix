from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from .paths import default_index_dir


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def tokens_path(index_dir_override: str | None = None) -> Path:
    idx = Path(index_dir_override) if index_dir_override else default_index_dir()
    return idx / "tokens" / "data_tokens.jsonl"


def _signing_key() -> str | None:
    k = os.environ.get("MIGHAN_BRAIN_DATA_TOKEN_KEY", "").strip()
    return k or None


def _canonical(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hmac_hex(key: str, msg: str) -> str:
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class DataToken:
    token_id: str
    file_cid: str
    version: int
    status: str
    issuer: str
    created_at: str
    signature: str | None


def issue_token(
    *,
    file_cid: str,
    version: int = 1,
    issuer: str = "local-maintainer",
    status: str = "APPROVED",
    index_dir_override: str | None = None,
) -> DataToken:
    token_id = f"dt_{uuid.uuid4().hex}"
    created_at = _now_utc_iso()

    base = {
        "token_id": token_id,
        "file_cid": file_cid,
        "version": int(version),
        "status": status,
        "issuer": issuer,
        "created_at": created_at,
    }

    sk = _signing_key()
    signature = _hmac_hex(sk, _canonical(base)) if sk else None

    record = dict(base)
    if signature:
        record["signature"] = signature

    p = tokens_path(index_dir_override)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return DataToken(
        token_id=token_id,
        file_cid=file_cid,
        version=int(version),
        status=status,
        issuer=issuer,
        created_at=created_at,
        signature=signature,
    )


def list_tokens(*, index_dir_override: str | None = None, tail: int = 50) -> list[dict[str, Any]]:
    p = tokens_path(index_dir_override)
    if not p.exists():
        return []
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[dict[str, Any]] = []
    for ln in lines[-max(1, min(int(tail), 500)) :]:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def verify_token_record(record: dict[str, Any]) -> dict[str, Any]:
    sk = _signing_key()
    if not sk:
        sig = record.get("signature")
        if sig:
            return {"ok": False, "message": "MIGHAN_BRAIN_DATA_TOKEN_KEY not set; cannot verify signatures."}
        return {"ok": True, "message": "No signature on record; nothing to verify (set MIGHAN_BRAIN_DATA_TOKEN_KEY to enable signing)."}

    sig = record.get("signature")
    if not isinstance(sig, str) or not sig:
        return {"ok": True, "message": "No signature on record (issued without signing key). Nothing to verify."}

    token_id = record.get("token_id")
    file_cid = record.get("file_cid")
    version = record.get("version")
    status = record.get("status")
    issuer = record.get("issuer")
    created_at = record.get("created_at")

    if not isinstance(token_id, str) or not token_id:
        return {"ok": False, "message": "Invalid token_id."}
    if not isinstance(file_cid, str) or not file_cid:
        return {"ok": False, "message": "Invalid file_cid."}
    if not isinstance(version, int):
        return {"ok": False, "message": "Invalid version."}
    if not isinstance(status, str) or not status:
        return {"ok": False, "message": "Invalid status."}
    if not isinstance(issuer, str) or not issuer:
        return {"ok": False, "message": "Invalid issuer."}
    if not isinstance(created_at, str) or not created_at:
        return {"ok": False, "message": "Invalid created_at."}

    base: dict[str, Any] = {
        "token_id": token_id,
        "file_cid": file_cid,
        "version": int(version),
        "status": status,
        "issuer": issuer,
        "created_at": created_at,
    }

    expected = _hmac_hex(sk, _canonical(cast(dict[str, Any], base)))
    ok = hmac.compare_digest(expected, sig)
    return {"ok": ok, "message": "OK" if ok else "Signature mismatch."}
