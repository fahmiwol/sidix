"""
Lazy-load Qwen2.5-7B + LoRA adapter untuk SIDIX (opsional).

Butuh: torch, transformers, peft, accelerate; untuk 4-bit: bitsandbytes (Linux/WSL lebih mudah).
Adapter harus berisi adapter_config.json + adapter_model.safetensors (atau .bin).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

# Root paket = folder yang berisi brain_qa/ (apps/brain_qa)
_PKG_ROOT = Path(__file__).resolve().parent.parent

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

_model: Any | None = None
_tokenizer: Any | None = None


def find_adapter_dir() -> Path | None:
    """Cek lokasi umum (termasuk nested hasil extract zip)."""
    candidates = [
        _PKG_ROOT / "models" / "sidix-lora-adapter",
        _PKG_ROOT / "models" / "sidix-lora-adapter" / "sidix-lora-adapter",
    ]
    for p in candidates:
        if (p / "adapter_config.json").exists():
            return p
    return None


def adapter_weights_exist(adapter: Path) -> bool:
    return (adapter / "adapter_model.safetensors").exists() or (adapter / "adapter_model.bin").exists()


def adapter_fingerprint() -> dict[str, Any]:
    """Ringkas untuk /health dan telemetri — bukan audit kriptografi penuh."""
    adapter = find_adapter_dir()
    out: dict[str, Any] = {
        "adapter_path": str(adapter) if adapter else "",
        "config_present": bool(adapter and (adapter / "adapter_config.json").exists()),
        "weights_present": bool(adapter and adapter_weights_exist(adapter)),
        "config_sha256_prefix": "",
    }
    if adapter and (adapter / "adapter_config.json").exists():
        raw = (adapter / "adapter_config.json").read_bytes()
        out["config_sha256_prefix"] = hashlib.sha256(raw).hexdigest()[:16]
    return out


def _load_model_tokenizer() -> tuple[Any, Any]:
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer

    adapter = find_adapter_dir()
    if adapter is None or not adapter_weights_exist(adapter):
        raise RuntimeError("adapter atau bobot tidak ada")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(str(adapter), trust_remote_code=True)

    use_4bit = os.environ.get("SIDIX_DISABLE_4BIT", "").strip() not in ("1", "true", "yes")
    bnb_config = None
    if use_4bit:
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        except Exception:
            bnb_config = None

    kwargs: dict[str, Any] = {
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
        "device_map": "auto",
    }
    if bnb_config is not None:
        kwargs["quantization_config"] = bnb_config
    else:
        kwargs["torch_dtype"] = torch.float16

    base = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
    model = PeftModel.from_pretrained(base, str(adapter))
    model.eval()
    _model, _tokenizer = model, tokenizer
    return model, tokenizer


def generate_sidix(
    prompt: str,
    system: str,
    *,
    max_tokens: int = 256,
    temperature: float = 0.7,
) -> tuple[str, str]:
    """
    Returns (text, mode). mode is 'local_lora' or 'mock' with explanation.
    """
    adapter = find_adapter_dir()
    if adapter is None:
        return (
            "[SIDIX] Adapter tidak ditemukan. Letakkan folder adapter di "
            f"`{_PKG_ROOT / 'models' / 'sidix-lora-adapter'}` "
            "(atau nested `.../sidix-lora-adapter/sidix-lora-adapter/`).",
            "mock",
        )
    if not adapter_weights_exist(adapter):
        return (
            "[SIDIX] File bobot LoRA tidak ada di "
            f"{adapter} — butuh `adapter_model.safetensors` atau `adapter_model.bin`. "
            "Pastikan zip dari Kaggle lengkap dan diekstrak ulang.",
            "mock",
        )

    try:
        model, tokenizer = _load_model_tokenizer()
    except Exception as e:
        return (
            f"[SIDIX] Gagal load model: {e!s}\n"
            "Pastikan: pip install torch transformers peft accelerate bitsandbytes "
            "(di Windows, bitsandbytes bisa butuh setup khusus atau gunakan WSL/CUDA).",
            "mock",
        )

    import torch

    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        im_end = getattr(tokenizer, "eos_token", None) or ""
        text = (
            f"<|im_start|>system\n{system}{im_end}\n"
            f"<|im_start|>user\n{prompt}{im_end}\n"
            f"<|im_start|>assistant\n"
        )

    inputs = tokenizer(text, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=temperature > 0,
            temperature=max(0.01, float(temperature)),
            pad_token_id=tokenizer.eos_token_id,
        )

    gen = out[0, inputs["input_ids"].shape[1] :]
    decoded = tokenizer.decode(gen, skip_special_tokens=True).strip()
    return decoded if decoded else "(kosong)", "local_lora"


def clear_model_cache() -> None:
    global _model, _tokenizer
    _model = None
    _tokenizer = None
