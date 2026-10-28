"""
persona_adapter_loader.py — Sprint 13 Phase 3c scaffold.

Manage DoRA persona adapter loading + hot-swap di inference path.

Architecture:
- 1 base SIDIX LoRA adapter (existing, default voice generic)
- 5 persona DoRA adapters (UTZ/ABOO/OOMAR/ALEY/AYMAN), trained Sprint 13 Phase 3b
- Hot-swap via vLLM lora_modules slot (RunPod inference) atau peft set_adapter()

Mode operasi:
- LOAD_ON_DEMAND: download adapter dari HF cache, swap in saat persona request
- LOAD_ALL: pre-download semua 5 adapter di warmup, swap by name
- FALLBACK: kalau adapter unavailable → fallback ke base SIDIX LoRA

Phase 3c (sesi setelah training done) akan wire ini ke `agent_react.py` +
`runpod_warmup.sh`.

Reference:
- research note 285 (Sprint 13 Phase 3a) + 286 (Phase 3b handoff)
- DoRA paper Liu et al ICML 2024 (arxiv 2402.09353)
- vLLM multi-LoRA: https://docs.vllm.ai/en/latest/models/lora.html
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


HF_REPO = "Tiranyx/sidix-dora-persona-v1"  # set Sprint 13 Phase 3b
ADAPTER_CACHE_DIR = Path("/opt/sidix/.data/adapters/dora_persona")
SUPPORTED_PERSONAS = ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")


@dataclass
class AdapterState:
    """Runtime state untuk satu persona adapter."""
    persona: str
    repo_id: str = HF_REPO
    local_path: Optional[str] = None
    loaded: bool = False
    last_used_at: str = ""
    error: str = ""


@dataclass
class PersonaRouter:
    """In-memory registry. Sprint 13 Phase 3c wire ke agent_react.py.

    Sprint 13 Phase 3a/3b status: SCAFFOLD ONLY. Adapter belum tersedia di HF
    sampai Phase 3b training selesai + upload sukses.
    """
    states: dict[str, AdapterState] = field(default_factory=dict)
    fallback_persona: str = "AYMAN"  # default voice kalau persona request gak match
    cache_dir: Path = ADAPTER_CACHE_DIR

    def __post_init__(self):
        for p in SUPPORTED_PERSONAS:
            self.states.setdefault(p, AdapterState(persona=p))

    def is_ready(self, persona: str) -> bool:
        """Check apakah adapter untuk persona sudah loaded di runtime."""
        s = self.states.get(persona.upper())
        return s is not None and s.loaded


def download_adapter(persona: str, force: bool = False) -> dict:
    """Download adapter persona dari HF ke local cache.

    Sprint 13 Phase 3c full implementation (sesi setelah training done):
    - Cek HF repo `HF_REPO` ada
    - Download `adapter_model.safetensors` + `adapter_config.json` ke cache
    - Verify via `peft.PeftConfig.from_pretrained(local_path)`
    - Update AdapterState.local_path + loaded=True

    Sprint 13 Phase 3a/3b: STUB — return placeholder status sampai training done.

    Args:
        persona: UTZ/ABOO/OOMAR/ALEY/AYMAN
        force: kalau True, re-download even if cached

    Returns:
        dict {ok, persona, local_path, error}
    """
    persona_upper = persona.upper()
    if persona_upper not in SUPPORTED_PERSONAS:
        return {"ok": False, "error": f"persona '{persona}' tidak supported"}

    target_dir = ADAPTER_CACHE_DIR / persona_upper
    if target_dir.exists() and not force:
        log.info("[adapter] cache hit %s", target_dir)
        return {"ok": True, "persona": persona_upper, "local_path": str(target_dir),
                "cached": True}

    # Sprint 13 Phase 3c TODO (post training):
    # from huggingface_hub import snapshot_download
    # snapshot_download(repo_id=HF_REPO, local_dir=str(target_dir),
    #                    allow_patterns=["adapter_*", "tokenizer.*"])
    # log.info("[adapter] downloaded %s → %s", HF_REPO, target_dir)
    # return {"ok": True, "persona": persona_upper, "local_path": str(target_dir)}

    return {
        "ok": False,
        "error": "STUB — Phase 3c implementation pending training done",
        "persona": persona_upper,
        "next_step": "wire snapshot_download(HF_REPO) di Phase 3c sesi berikutnya",
    }


def select_adapter_for_request(persona: Optional[str], router: PersonaRouter) -> str:
    """Persona dispatch: request persona → resolved persona (with fallback).

    Logika:
    - Kalau persona None → fallback (AYMAN — voice paling general)
    - Kalau persona valid + loaded → return persona
    - Kalau persona valid tapi belum loaded → return fallback (avoid blocking
      ReAct loop untuk download)

    Phase 3c full implementation: integrate dengan agent_react.py persona param.
    """
    if not persona:
        return router.fallback_persona

    persona_upper = persona.upper()
    if persona_upper not in SUPPORTED_PERSONAS:
        log.warning("[adapter] unknown persona '%s' → fallback %s", persona, router.fallback_persona)
        return router.fallback_persona

    if not router.is_ready(persona_upper):
        log.info("[adapter] persona '%s' not ready → fallback %s", persona_upper, router.fallback_persona)
        return router.fallback_persona

    return persona_upper


def list_adapter_status() -> dict:
    """Diagnostic: status semua persona adapter (cache + loaded state).

    Untuk admin endpoint /admin/persona-adapters/stats di Phase 3c.
    """
    out = {"hf_repo": HF_REPO, "cache_dir": str(ADAPTER_CACHE_DIR), "personas": {}}
    for p in SUPPORTED_PERSONAS:
        target = ADAPTER_CACHE_DIR / p
        out["personas"][p] = {
            "cached": target.exists(),
            "cache_path": str(target) if target.exists() else None,
            "loaded": False,  # Phase 3c will populate from runtime PersonaRouter
        }
    return out


__all__ = [
    "AdapterState",
    "PersonaRouter",
    "HF_REPO",
    "SUPPORTED_PERSONAS",
    "ADAPTER_CACHE_DIR",
    "download_adapter",
    "select_adapter_for_request",
    "list_adapter_status",
]
