"""
sidix_folder_tools.py — Runtime wrapper untuk snippet kode yang
di-extract dari folder D:\\SIDIX oleh `sidix_folder_processor.wrap_as_agent_tools`.

Tiap snippet disimpan sebagai file .py di
    apps/brain_qa/.data/sidix_folder_tools_snippets/
dengan _registry.json yang memetakan nama fungsi → path snippet.

Modul ini menyediakan:
  * `list_sidix_folder_tools()` — daftar nama fungsi tersedia
  * `call_sidix_folder_tool(name, **kwargs)` — load + panggil

Eksekusi snippet dilakukan dengan `exec(compile(...), {...})` di namespace
terisolasi. Ini masih eksperimental: snippet di-trust karena berasal dari
session SIDIX sendiri (MCPKnowledgeBridge), bukan input eksternal.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .paths import default_data_dir

logger = logging.getLogger("sidix.folder_tools")

_SNIPPET_DIR = default_data_dir() / "sidix_folder_tools_snippets"
_REGISTRY_PATH = _SNIPPET_DIR / "_registry.json"


def _load_registry() -> dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_sidix_folder_tools() -> list[dict[str, Any]]:
    reg = _load_registry()
    return [
        {"name": name, "topic": info.get("topic"), "source": info.get("source")}
        for name, info in reg.items()
    ]


def call_sidix_folder_tool(name: str, **kwargs) -> Any:
    """
    Panggil fungsi Python dari snippet yang tersimpan.
    Snippet harus mendefinisikan top-level `def <name>(...)`.
    """
    reg = _load_registry()
    if name not in reg:
        raise KeyError(f"sidix_folder tool '{name}' tidak ditemukan")
    snippet_path = Path(reg[name]["snippet_path"])
    if not snippet_path.exists():
        raise FileNotFoundError(f"snippet hilang: {snippet_path}")

    code = snippet_path.read_text(encoding="utf-8")
    ns: dict[str, Any] = {"__name__": f"sidix_folder_tool__{name}"}
    try:
        exec(compile(code, str(snippet_path), "exec"), ns)  # noqa: S102
    except Exception as e:
        logger.warning("Gagal load snippet %s: %s", snippet_path, e)
        raise

    func = ns.get(name)
    if not callable(func):
        raise RuntimeError(f"snippet tidak mendefinisikan callable '{name}'")
    return func(**kwargs)
