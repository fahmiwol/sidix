from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ManifestPaths:
    public_markdown_root: Path


def workspace_root() -> Path:
    # apps/brain_qa/brain_qa/paths.py -> apps/brain_qa -> apps -> workspace
    return Path(__file__).resolve().parents[3]


def default_index_dir() -> Path:
    return workspace_root() / "apps" / "brain_qa" / ".data"


def default_data_dir() -> Path:
    """Direktori data utama — dipakai oleh token_cost, backup, dan modul lain."""
    return workspace_root() / "apps" / "brain_qa" / ".data"


def load_manifest_paths() -> ManifestPaths:
    manifest_path = workspace_root() / "brain" / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    data_roots: dict[str, Any] = data.get("data_roots", {})
    public_root = data_roots.get("public_markdown_root")
    if not isinstance(public_root, str) or not public_root.strip():
        raise ValueError("brain/manifest.json missing data_roots.public_markdown_root")

    p = Path(public_root)
    if not p.is_absolute():
        p = workspace_root() / p
    return ManifestPaths(public_markdown_root=p)

