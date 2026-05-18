#!/bin/bash
# Convert LoRA adapter → merged model → GGUF untuk Ollama
#
# Usage:
#   ./scripts/distillation/export_to_gguf.sh [ADAPTER_PATH] [BASE_MODEL] [OUTPUT_NAME]
#
# Args:
#   ADAPTER_PATH  Path ke LoRA adapter dir   (default: ./sidix-distilled-adapter)
#   BASE_MODEL    HuggingFace model ID        (default: Qwen/Qwen2.5-0.5B-Instruct)
#   OUTPUT_NAME   Output GGUF filename stem   (default: sidix-distilled)
#
# Requirements:
#   - Python env dengan transformers, peft, torch
#   - llama.cpp di /opt/llama.cpp (atau LLAMA_CPP_DIR env var)
#
# Example:
#   LLAMA_CPP_DIR=/usr/local/llama.cpp ./export_to_gguf.sh \
#       ./sidix-distilled-adapter \
#       Qwen/Qwen2.5-0.5B-Instruct \
#       sidix-0.5b-distilled

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ADAPTER_PATH="${1:-./sidix-distilled-adapter}"
BASE_MODEL="${2:-Qwen/Qwen2.5-0.5B-Instruct}"
OUTPUT_NAME="${3:-sidix-distilled}"

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-/opt/llama.cpp}"
MERGED_DIR="./merged_model_${OUTPUT_NAME}"
QUANT_TYPE="${QUANT_TYPE:-q4_k_m}"   # Options: q4_k_m, q5_k_m, q8_0, f16

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
echo "[INFO] === SIDIX GGUF Export ==="
echo "[INFO] Adapter   : ${ADAPTER_PATH}"
echo "[INFO] Base model: ${BASE_MODEL}"
echo "[INFO] Output    : ${OUTPUT_NAME}.gguf"
echo "[INFO] Quant     : ${QUANT_TYPE}"
echo ""

if [ ! -d "${ADAPTER_PATH}" ]; then
    echo "[ERROR] Adapter path not found: ${ADAPTER_PATH}"
    exit 1
fi

if [ ! -d "${LLAMA_CPP_DIR}" ]; then
    echo "[ERROR] llama.cpp not found at: ${LLAMA_CPP_DIR}"
    echo "        Set LLAMA_CPP_DIR env var or install at /opt/llama.cpp"
    echo "        Install: git clone https://github.com/ggerganov/llama.cpp ${LLAMA_CPP_DIR}"
    echo "                 cd ${LLAMA_CPP_DIR} && make"
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 1: Merge LoRA adapter into base model
# ---------------------------------------------------------------------------
echo "[STEP 1/3] Merging LoRA adapter into base model ..."

python3 - <<PYEOF
import os, sys
from pathlib import Path

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("        pip install transformers peft torch accelerate")
    sys.exit(1)

adapter_path = "${ADAPTER_PATH}"
base_model_id = "${BASE_MODEL}"
merged_dir = "${MERGED_DIR}"

print(f"  Loading base: {base_model_id}")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    device_map="cpu",
    trust_remote_code=True,
)

print(f"  Loading adapter: {adapter_path}")
model = PeftModel.from_pretrained(base_model, adapter_path)

print("  Merging weights ...")
model = model.merge_and_unload()

print(f"  Saving merged model → {merged_dir}")
model.save_pretrained(merged_dir)

tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
tokenizer.save_pretrained(merged_dir)

print("  Merge complete.")
PYEOF

echo "[INFO] Merged model saved at: ${MERGED_DIR}"

# ---------------------------------------------------------------------------
# Step 2: Convert to GGUF (f16 first)
# ---------------------------------------------------------------------------
GGUF_F16="${OUTPUT_NAME}-f16.gguf"
echo "[STEP 2/3] Converting to GGUF (f16) ..."

python3 "${LLAMA_CPP_DIR}/convert_hf_to_gguf.py" \
    "${MERGED_DIR}" \
    --outfile "${GGUF_F16}" \
    --outtype f16

echo "[INFO] F16 GGUF saved: ${GGUF_F16}"

# ---------------------------------------------------------------------------
# Step 3: Quantize to target precision
# ---------------------------------------------------------------------------
GGUF_FINAL="${OUTPUT_NAME}.gguf"
echo "[STEP 3/3] Quantizing to ${QUANT_TYPE} ..."

"${LLAMA_CPP_DIR}/llama-quantize" \
    "${GGUF_F16}" \
    "${GGUF_FINAL}" \
    "${QUANT_TYPE}"

echo "[INFO] Quantized GGUF saved: ${GGUF_FINAL}"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
echo ""
echo "[INFO] Cleaning up intermediate files ..."
rm -f "${GGUF_F16}"

echo ""
echo "[DONE] === Export complete ==="
echo "  GGUF  : ${GGUF_FINAL}"
echo "  Merged: ${MERGED_DIR}/"
echo ""
echo "Next steps:"
echo "  1. cp ${GGUF_FINAL} /opt/sidix/models/"
echo "  2. ollama create sidix-distilled -f scripts/distillation/sidix_modelfile.txt"
echo "  3. ollama run sidix-distilled"
