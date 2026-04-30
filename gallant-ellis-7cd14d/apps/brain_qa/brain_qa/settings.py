from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import default_index_dir


@dataclass(frozen=True)
class AppSettings:
    # Ask
    default_persona: str | None = None  # None => auto
    autosuggest: bool = True
    auto_escalate: bool = False
    k: int = 5
    max_snippet_chars: int = 500

    # Validate
    default_validate_profile: str = "generic"  # generic | hadith

    # Curation automation
    auto_reindex_after_publish: bool = False

    # Plugins/connectors (future)
    enabled_plugins: list[str] | None = None


def settings_path(index_dir_override: str | None = None) -> Path:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    return index_dir / "settings.json"


def _coerce_bool(v: Any, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    return default


def _coerce_int(v: Any, default: int) -> int:
    if isinstance(v, int) and v > 0:
        return v
    return default


def load_settings(index_dir_override: str | None = None) -> AppSettings:
    path = settings_path(index_dir_override)
    if not path.exists():
        return AppSettings(enabled_plugins=[])

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppSettings(enabled_plugins=[])

    enabled_plugins = raw.get("enabled_plugins")
    if not isinstance(enabled_plugins, list) or not all(isinstance(x, str) for x in enabled_plugins):
        enabled_plugins = []

    return AppSettings(
        default_persona=raw.get("default_persona") if isinstance(raw.get("default_persona"), str) else None,
        autosuggest=_coerce_bool(raw.get("autosuggest"), True),
        auto_escalate=_coerce_bool(raw.get("auto_escalate"), False),
        k=_coerce_int(raw.get("k"), 5),
        max_snippet_chars=_coerce_int(raw.get("max_snippet_chars"), 500),
        default_validate_profile=raw.get("default_validate_profile")
        if isinstance(raw.get("default_validate_profile"), str)
        else "generic",
        auto_reindex_after_publish=_coerce_bool(raw.get("auto_reindex_after_publish"), False),
        enabled_plugins=enabled_plugins,
    )


def save_settings(settings: AppSettings, index_dir_override: str | None = None) -> Path:
    path = settings_path(index_dir_override)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "default_persona": settings.default_persona,
        "autosuggest": settings.autosuggest,
        "auto_escalate": settings.auto_escalate,
        "k": settings.k,
        "max_snippet_chars": settings.max_snippet_chars,
        "default_validate_profile": settings.default_validate_profile,
        "auto_reindex_after_publish": settings.auto_reindex_after_publish,
        "enabled_plugins": list(settings.enabled_plugins or []),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path

