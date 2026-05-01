"""
persona_adapter.py — Sprint I: DoRA Persona Adapter Foundation

Arsitektur:
  DoRA (Weight-Decomposed Low-Rank Adaptation) = visi jangka panjang.
  Sprint I = fondasi: persona-specific prompt engineering + data harvesting
  untuk future training.

Komponen:
  1. PersonaConfig — system prompt, temperature, top_p, max_tokens per persona
  2. PersonaAdapter — load config, apply ke generation call
  3. PersonaDataHarvester — extract persona-specific golden examples dari Hafidz
  4. TrainingDataBuilder — build JSONL untuk future LoRA/DoRA training

Personas (5 LOCKED):
  UTZ   = creative, visionary, metaphorical
  ABOO  = engineer, precise, technical
  OOMAR = strategist, big-picture, systemic
  ALEY  = researcher, evidence-based, skeptical
  AYMAN = general, balanced, approachable

Storage:
  - Config: brain/public/persona_adapter/configs/<persona>.json
  - Training data: brain/public/persona_adapter/training_data/<persona>.jsonl
  - Harvested: brain/public/persona_adapter/harvested/<persona>.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("sidix.persona_adapter")


# ── Storage ──────────────────────────────────────────────────────────────

ADAPTER_ROOT = Path("brain/public/persona_adapter")
CONFIG_DIR = ADAPTER_ROOT / "configs"
TRAINING_DIR = ADAPTER_ROOT / "training_data"
HARVESTED_DIR = ADAPTER_ROOT / "harvested"


# ── Persona Configurations ───────────────────────────────────────────────

@dataclass
class PersonaConfig:
    """Generation configuration for a persona."""
    persona: str
    system_prompt: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 600
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: list[str] = None
    description: str = ""

    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


_DEFAULT_CONFIGS: dict[str, PersonaConfig] = {
    "UTZ": PersonaConfig(
        persona="UTZ",
        system_prompt=(
            "Kamu adalah UTZ — kreatif, visioner, dan penuh metafora. "
            "Kamu melihat pola tersembunyi dan menghubungkan ide-ide yang tampak tidak terkait. "
            "Jawabanmu penuh analogi, cerita, dan insight yang membuat orang berpikir ulang. "
            "Gunakan bahasa Indonesia yang indah dan puitis ketika memungkinkan."
        ),
        temperature=0.85,
        top_p=0.95,
        max_tokens=700,
        description="Creative visionary — metaphorical, pattern-seeking, poetic",
    ),
    "ABOO": PersonaConfig(
        persona="ABOO",
        system_prompt=(
            "Kamu adalah ABOO — engineer yang presisi dan pragmatis. "
            "Kamu memberikan jawaban teknis yang akurat, terstruktur, dan actionable. "
            "Selalu sertakan langkah-langkah konkret, contoh kode jika relevan, dan caveat teknis. "
            "Bahasamu ringkas, tidak berlebihan, fokus pada solusi."
        ),
        temperature=0.4,
        top_p=0.85,
        max_tokens=800,
        description="Engineering pragmatist — precise, structured, code-forward",
    ),
    "OOMAR": PersonaConfig(
        persona="OOMAR",
        system_prompt=(
            "Kamu adalah OOMAR — strategist yang melihat gambaran besar. "
            "Kamu menghubungkan taktik dengan visi jangka panjang. "
            "Jawabanmu selalu mencakup: konteks strategis, trade-off analysis, dan rekomendasi prioritas. "
            "Gunakan framework-thinking dan systems perspective."
        ),
        temperature=0.6,
        top_p=0.9,
        max_tokens=700,
        description="Strategic architect — big-picture, systemic, framework-driven",
    ),
    "ALEY": PersonaConfig(
        persona="ALEY",
        system_prompt=(
            "Kamu adalah ALEY — researcher yang berbasis bukti dan skeptis. "
            "Kamu tidak menerima klaim tanpa sumber. "
            "Setiap jawaban harus mencantumkan: tingkat kepastian (tinggi/sedang/rendah), sumber referensi, dan batasan pengetahuan. "
            "Gunakan metode ilmiah: hipotesis → bukti → kesimpulan."
        ),
        temperature=0.5,
        top_p=0.85,
        max_tokens=750,
        description="Evidence-based researcher — skeptical, cited, methodical",
    ),
    "AYMAN": PersonaConfig(
        persona="AYMAN",
        system_prompt=(
            "Kamu adalah AYMAN — generalist yang seimbang dan approachable. "
            "Kamu menjelaskan konsep kompleks dengan bahasa sederhana. "
            "Tone-mu ramah, sabar, dan tidak judgmental. "
            "Selalu berikan multiple perspectives dan biarkan user memutuskan."
        ),
        temperature=0.65,
        top_p=0.9,
        max_tokens=600,
        description="Balanced generalist — approachable, multi-perspective, clear",
    ),
}


# ── Config Manager ───────────────────────────────────────────────────────

def get_persona_config(persona: str) -> PersonaConfig:
    """Load config for persona (from disk or default)."""
    persona = persona.upper()
    config_path = CONFIG_DIR / f"{persona}.json"

    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return PersonaConfig(**data)
        except Exception as e:
            log.debug("[persona_adapter] Load config failed for %s: %s", persona, e)

    return _DEFAULT_CONFIGS.get(persona, _DEFAULT_CONFIGS["AYMAN"])


def save_persona_config(config: PersonaConfig) -> None:
    """Save persona config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{config.persona}.json"
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("[persona_adapter] Saved config for %s", config.persona)


def reset_persona_config(persona: str) -> PersonaConfig:
    """Reset persona config to default."""
    persona = persona.upper()
    default = _DEFAULT_CONFIGS.get(persona)
    if default:
        save_persona_config(default)
    return default or _DEFAULT_CONFIGS["AYMAN"]


# ── Generation Wrapper ───────────────────────────────────────────────────

def generate_with_persona(
    prompt: str,
    persona: str = "AYMAN",
    **override_kwargs,
) -> str:
    """Generate text with persona-specific config applied.

    This is the foundation for future DoRA — currently prompt-based,
    will be upgraded to LoRA adapter loading once adapters are trained.
    """
    config = get_persona_config(persona)

    # Merge overrides
    temperature = override_kwargs.get("temperature", config.temperature)
    top_p = override_kwargs.get("top_p", config.top_p)
    max_tokens = override_kwargs.get("max_tokens", config.max_tokens)

    system = config.system_prompt
    full_prompt = f"{system}\n\nUser: {prompt}\n\nAssistant:"

    try:
        from .ollama_llm import ollama_generate
        response, _mode = ollama_generate(
            full_prompt,
            system="",
            model="qwen2.5:7b",
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return response or ""
    except Exception as e:
        log.warning("[persona_adapter] Generation failed: %s", e)
        return ""


# ── Data Harvester ───────────────────────────────────────────────────────

def harvest_persona_data(persona: str, limit: int = 50) -> list[dict]:
    """Harvest persona-specific golden examples dari Hafidz for future training.

    Returns list of {instruction, input, output} dicts for LoRA/DoRA training.
    """
    from .hafidz_injector import GOLDEN_ROOT

    persona = persona.upper()
    examples = []

    if not GOLDEN_ROOT.exists():
        return examples

    # Walk golden store untuk cari entries dengan persona match
    for date_dir in sorted(GOLDEN_ROOT.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for md_file in date_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                # Simple heuristic: check if persona mentioned in metadata
                check = f"persona: {persona.lower()}" in text.lower() or f"persona:{persona.lower()}" in text.lower()
                if check:
                    # Extract Q&A dari markdown
                    q_match = re.search(r'## Pertanyaan\n(.+?)\n', text, re.S)
                    a_match = re.search(r'## Jawaban\n(.+?)\n', text, re.S)
                    if q_match and a_match:
                        examples.append({
                            "instruction": f"Answer as {persona} persona",
                            "input": q_match.group(1).strip(),
                            "output": a_match.group(1).strip(),
                            "persona": persona,
                        })
                        if len(examples) >= limit:
                            break
            except Exception as e:
                log.debug("[harvest] skip %s: %s", md_file, e)
                continue
        if len(examples) >= limit:
            break

    return examples


def build_training_data(persona: str, limit: int = 100) -> Path:
    """Build JSONL training file for future DoRA training.

    Format: {"messages": [{"role": "system", "content": ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    examples = harvest_persona_data(persona, limit=limit)
    config = get_persona_config(persona)

    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    path = TRAINING_DIR / f"{persona}_dora_training.jsonl"

    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            record = {
                "messages": [
                    {"role": "system", "content": config.system_prompt},
                    {"role": "user", "content": ex["input"]},
                    {"role": "assistant", "content": ex["output"]},
                ],
                "metadata": {
                    "persona": persona,
                    "source": "hafidz_golden",
                    "harvested_at": datetime.now(timezone.utc).isoformat(),
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    log.info("[persona_adapter] Built %d training records for %s → %s", len(examples), persona, path)
    return path


# ── Stats ────────────────────────────────────────────────────────────────

def get_adapter_stats() -> dict:
    """Aggregate persona adapter stats."""
    stats = {
        "configs": {},
        "training_records": {},
        "harvested": {},
    }

    for persona in _DEFAULT_CONFIGS:
        config_path = CONFIG_DIR / f"{persona}.json"
        stats["configs"][persona] = config_path.exists()

        train_path = TRAINING_DIR / f"{persona}_dora_training.jsonl"
        if train_path.exists():
            lines = train_path.read_text(encoding="utf-8").strip().splitlines()
            stats["training_records"][persona] = len(lines)
        else:
            stats["training_records"][persona] = 0

    return stats
