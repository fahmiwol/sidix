"""
runpod_train_lora.py — Sprint 13 Phase 3b RunPod-side training script.

Standalone Python script (bukan Jupyter notebook) yang dijalankan di RunPod Pod
setelah Pod ready. Equivalent dengan Kaggle notebook tapi:
- Fully shell-runnable (no nbclient overhead)
- Auto-detect dataset path
- Push adapter ke HF di akhir (HF_TOKEN dari Pod env)
- Self-terminate Pod via runpod API (avoid ongoing charge)

Usage di Pod:
  export HF_TOKEN=hf_xxx
  cd /workspace
  python runpod_train_lora.py \\
    --train-data persona_qa_train.jsonl \\
    --val-data persona_qa_val.jsonl \\
    --hf-repo Tiranyx/sidix-dora-persona-v1 \\
    --use-dora  # toggle DoRA on/off (P100 needs off, T4+ needs on)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Sprint 13 RunPod training")
    parser.add_argument("--train-data", required=True, help="Path to persona_qa_train.jsonl")
    parser.add_argument("--val-data", required=True, help="Path to persona_qa_val.jsonl")
    parser.add_argument("--hf-repo", default="Tiranyx/sidix-dora-persona-v1",
                        help="HuggingFace repo target untuk adapter upload")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct",
                        help="Base model dari HF")
    parser.add_argument("--output-dir", default="/workspace/sidix-dora-persona-v1",
                        help="Local adapter save dir")
    parser.add_argument("--use-dora", action="store_true",
                        help="Enable DoRA (requires GPU CC ≥7.5 — T4 ke atas)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Per-device batch (T4/L4 16-24GB → 2, A100 → 4-8)")
    parser.add_argument("--grad-accum", type=int, default=4,
                        help="Gradient accumulation steps (effective batch = batch * grad_accum)")
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq", type=int, default=1024)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--skip-upload", action="store_true",
                        help="Skip HF upload (untuk dry-run / debug)")
    args = parser.parse_args()

    print("=" * 60)
    print("Sprint 13 RunPod Training — DoRA Persona Stylometry")
    print("=" * 60)
    print(f"Base model: {args.base_model}")
    print(f"Train: {args.train_data}")
    print(f"Val: {args.val_data}")
    print(f"HF target: {args.hf_repo}")
    print(f"DoRA: {args.use_dora} | epochs: {args.epochs} | batch: {args.batch_size}×{args.grad_accum}")
    print()

    # ── Import deps (lazy supaya error import langsung visible) ───────────────
    import torch
    print(f"PyTorch {torch.__version__} | CUDA {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print("FATAL: CUDA tidak available — Pod harus ada GPU")
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)} | "
          f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"Compute capability: {torch.cuda.get_device_capability(0)}")
    print()

    from datasets import load_dataset
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer, SFTConfig

    # ── Tokenizer + dataset ───────────────────────────────────────────────────
    print(">>> Loading tokenizer + dataset...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def to_chatml(row):
        messages = [
            {"role": "user", "content": row["instruction"]},
            {"role": "assistant", "content": row["output"]},
        ]
        return {"text": tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)}

    train_ds = load_dataset("json", data_files=args.train_data, split="train").map(
        to_chatml, remove_columns=["instruction", "input", "output", "metadata"])
    val_ds = load_dataset("json", data_files=args.val_data, split="train").map(
        to_chatml, remove_columns=["instruction", "input", "output", "metadata"])
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)}")
    print(f"Sample: {train_ds[0]['text'][:200]}")
    print()

    # ── Load base + LoRA/DoRA ──────────────────────────────────────────────────
    print(">>> Loading base model (bf16) + LoRA config...")
    # NOTE: device_map="auto" + SFTTrainer race condition (meta tensor cannot copy).
    # Load to CPU first, then trainer auto-moves to GPU. low_cpu_mem_usage=False to
    # avoid meta-init that breaks .to(device) downstream.
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=False,
    )
    model = model.to("cuda")
    model.config.use_cache = False
    if args.batch_size == 1:
        model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        lora_dropout=0.05,
        bias="none",
        use_dora=args.use_dora,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print(f"GPU mem after model load: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    print()

    # ── Train ─────────────────────────────────────────────────────────────────
    print(">>> Setting up SFTTrainer...")
    sft_config = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=(args.batch_size == 1),
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        optim="adamw_torch",
        bf16=True,
        max_seq_length=args.max_seq,
        dataset_text_field="text",
        packing=False,
        save_strategy="epoch",
        eval_strategy="epoch",
        logging_steps=20,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
    )
    t0 = time.time()
    trainer.train()
    train_secs = time.time() - t0
    print(f">>> Training selesai dalam {train_secs / 60:.1f} menit")
    print()

    # ── Save adapter ──────────────────────────────────────────────────────────
    print(">>> Saving adapter...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    saved_files = []
    for root, _, files in os.walk(args.output_dir):
        for f in files:
            p = os.path.join(root, f)
            sz = os.path.getsize(p) / 1024 / 1024
            saved_files.append((p, sz))
            print(f"  {p}: {sz:.2f} MB")
    print()

    # ── HF upload ─────────────────────────────────────────────────────────────
    if args.skip_upload:
        print(">>> Skip HF upload (--skip-upload). Adapter saved locally only.")
    else:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("WARNING: HF_TOKEN not set in env — skipping upload")
        else:
            print(f">>> Uploading to HF: {args.hf_repo}")
            from huggingface_hub import HfApi, login
            login(token=hf_token)
            api = HfApi()
            api.create_repo(repo_id=args.hf_repo, exist_ok=True, private=False)
            api.upload_folder(
                folder_path=args.output_dir,
                repo_id=args.hf_repo,
                commit_message=f"Sprint 13 LoRA persona adapter (use_dora={args.use_dora}, epochs={args.epochs})",
            )
            print(f">>> Uploaded → https://huggingface.co/{args.hf_repo}")

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = {
        "ok": True,
        "base_model": args.base_model,
        "use_dora": args.use_dora,
        "epochs": args.epochs,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "training_minutes": round(train_secs / 60, 2),
        "adapter_files": [{"path": p, "mb": round(sz, 2)} for p, sz in saved_files],
        "hf_repo": args.hf_repo if not args.skip_upload else None,
    }
    summary_path = os.path.join(args.output_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f">>> Summary saved: {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
