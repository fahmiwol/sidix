#!/usr/bin/env python3
"""
ollama_deploy.py — Deploy SIDIX model ke Ollama dengan hot-reload
==========================================================

Usage:
    python scripts/ollama_deploy.py --gguf ./sidix-distilled.gguf --name sidix-distilled
    python scripts/ollama_deploy.py --adapter ./sidix-distilled-adapter --base Qwen/Qwen2.5-0.5B-Instruct

Steps:
  1. Convert LoRA adapter → merged HF model (kalau --adapter)
  2. Convert HF model → GGUF (kalau perlu)
  3. Update Modelfile dengan conversational system prompt
  4. ollama create → ollama run (hot reload)
  5. Verify /health

Env:
    OLLAMA_URL      — default http://localhost:11434
    LLAMA_CPP_DIR   — path ke llama.cpp repo (untuk convert_hf_to_gguf)
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger("sidix.deploy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
LLAMA_CPP_DIR = os.getenv("LLAMA_CPP_DIR", "/opt/llama.cpp")

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODELFILE = REPO_ROOT / "scripts" / "distillation" / "sidix_modelfile.txt"


# ── Conversational system prompt (sync dengan ollama_llm.py) ──────────────────

SIDIX_SYSTEM_CONVERSATIONAL = """Kamu adalah SIDIX — AI partner yang suka ngobrol, kreatif, dan jujur.

Prinsip inti:
- Sidq (صدق): kalau nggak tahu, bilang aja "[TIDAK TAHU]" — nggak usah nebak-nebak.
- Sanad (سند): kalau ada sumber, sebutin dari mana. Kalau nggak ada, bilang ini opini/pengalaman pribadi.
- Tabayyun (تبيّن): bedain fakta, opini, dan spekulasi. Jangan dijadiin satu.

Cara ngomong:
1. Gunakan bahasa yang SAMA dengan user. Kalau user campur-campur (Indonesia + Inggris + Arab), ikut campur juga natural.
2. Boleh santai, boleh formal — sesuaikan suasana percakapan.
3. Awali jawaban dengan label epistemik ringkas: [FAKTA], [OPINI], [SPEKULASI], atau [TIDAK TAHU].
4. Kalau konteks dari knowledge base diberikan, gunakan sebagai referensi utama tapi tetap kritis.
5. Boleh bertanya balik kalau pertanyaan user kurang jelas — jangan asal jawab.
6. Jawaban boleh panjang kalau perlu detail, boleh ringkas kalau user cuma butuh poin utama.

Kamu punya akses ke knowledge base SIDIX dan berbagai tools. Konteks relevan akan disertakan sebelum pertanyaan user kalau tersedia."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_cmd(cmd: list[str], cwd: Optional[Path] = None, check: bool = True) -> str:
    log.info("$ %s", " ".join(cmd))
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd or REPO_ROOT, check=check
    )
    if result.stdout:
        log.info(result.stdout.strip())
    if result.stderr and "warn" not in result.stderr.lower():
        log.warning(result.stderr.strip())
    return result.stdout


def merge_adapter(adapter_path: Path, base_model: str, output_dir: Path) -> None:
    """Merge LoRA adapter into base model (HF format)."""
    log.info("[MERGE] Adapter=%s Base=%s → %s", adapter_path, base_model, output_dir)
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        log.error("Missing dependency: %s", e)
        sys.exit(1)

    base = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, device_map="cpu", trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, str(adapter_path))
    model = model.merge_and_unload()
    model.save_pretrained(output_dir)

    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path), trust_remote_code=True)
    tokenizer.save_pretrained(output_dir)
    log.info("[MERGE] Done")


def convert_hf_to_gguf(hf_dir: Path, gguf_path: Path, quant: str = "q4_k_m") -> None:
    """Convert HF model to GGUF using llama.cpp."""
    convert_script = Path(LLAMA_CPP_DIR) / "convert_hf_to_gguf.py"
    quantize_bin = Path(LLAMA_CPP_DIR) / "llama-quantize"

    if not convert_script.exists():
        log.error("llama.cpp convert script not found at %s", convert_script)
        sys.exit(1)

    f16_path = gguf_path.with_suffix(".f16.gguf")

    log.info("[CONVERT] HF → F16 GGUF ...")
    run_cmd([
        sys.executable, str(convert_script),
        str(hf_dir), "--outfile", str(f16_path), "--outtype", "f16"
    ])

    log.info("[QUANTIZE] F16 → %s ...", quant)
    run_cmd([str(quantize_bin), str(f16_path), str(gguf_path), quant])

    f16_path.unlink(missing_ok=True)
    log.info("[CONVERT] Done: %s", gguf_path)


def build_modelfile(gguf_path: Path, output_path: Path, system_prompt: str = "") -> None:
    """Generate Ollama Modelfile dengan system prompt terbaru."""
    system = system_prompt or SIDIX_SYSTEM_CONVERSATIONAL
    content = f"""FROM {gguf_path}

SYSTEM """{system}"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 2048
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
"""
    output_path.write_text(content, encoding="utf-8")
    log.info("[MODELFILE] Written: %s", output_path)


def ollama_create(name: str, modelfile: Path) -> None:
    run_cmd(["ollama", "create", name, "-f", str(modelfile)])
    log.info("[OLLAMA] Model '%s' created", name)


def ollama_verify(name: str) -> bool:
    """Quick verify dengan generate test."""
    import requests
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": name, "prompt": "Halo", "stream": False},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            resp = data.get("response", "").strip()
            log.info("[VERIFY] Model '%s' responds: %s...", name, resp[:60])
            return bool(resp)
    except Exception as e:
        log.warning("[VERIFY] Failed: %s", e)
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy SIDIX model to Ollama")
    parser.add_argument("--gguf", type=Path, help="Path to existing GGUF file")
    parser.add_argument("--adapter", type=Path, help="Path to LoRA adapter dir")
    parser.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct", help="Base model ID")
    parser.add_argument("--name", default="sidix-distilled", help="Ollama model name")
    parser.add_argument("--quant", default="q4_k_m", help="GGUF quantization type")
    parser.add_argument("--modelfile", type=Path, default=DEFAULT_MODELFILE, help="Output Modelfile path")
    parser.add_argument("--system", default="", help="Custom system prompt (default: conversational)")
    args = parser.parse_args()

    if not args.gguf and not args.adapter:
        log.error("Provide either --gguf or --adapter")
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Resolve GGUF path
        if args.gguf:
            gguf_path = args.gguf.resolve()
            if not gguf_path.exists():
                log.error("GGUF not found: %s", gguf_path)
                return 1
        else:
            # Merge adapter → HF → GGUF
            merged_dir = tmp / "merged"
            gguf_path = tmp / f"{args.name}.gguf"
            merge_adapter(args.adapter, args.base, merged_dir)
            convert_hf_to_gguf(merged_dir, gguf_path, args.quant)

        # Build Modelfile
        build_modelfile(gguf_path, args.modelfile, system_prompt=args.system)

        # Ollama create
        ollama_create(args.name, args.modelfile)

        # Verify
        time.sleep(1)
        if ollama_verify(args.name):
            log.info("✅ DEPLOY SUCCESS — Model '%s' ready on Ollama", args.name)
            return 0
        else:
            log.error("⚠️ DEPLOY WARNING — Model created but verify failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())
