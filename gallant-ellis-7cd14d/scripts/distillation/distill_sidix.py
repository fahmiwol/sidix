"""
QLoRA fine-tuning script untuk distilasi SIDIX.

Jalankan di Kaggle T4 atau GPU node lain.

Requirements:
  pip install transformers peft datasets trl bitsandbytes accelerate

Usage:
  python distill_sidix.py --data_path data/distillation/synthetic_pairs_20260424.jsonl
  python distill_sidix.py --base_model Qwen/Qwen2.5-1.5B-Instruct --data_path ...
  python distill_sidix.py --base_model Qwen/Qwen2.5-3B-Instruct --lora_r 32 --epochs 5 ...

Note:
  - Default base model: Qwen/Qwen2.5-0.5B-Instruct (fits Kaggle T4 16GB easily)
  - Untuk 3B: gunakan --lora_r 16, batch_size 2, gradient_accumulation_steps 4
  - Output adapter di ./sidix-distilled-adapter/
"""

import os
import json
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    # Model
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    output_dir: str = "./sidix-distilled-adapter"

    # LoRA
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.05
    lr_scheduler_type: str = "cosine"
    max_seq_length: int = 512
    max_grad_norm: float = 1.0

    # Quantization
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"

    # Logging
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    save_total_limit: int = 2

    # Data
    data_path: Optional[str] = None
    eval_split: float = 0.1

    # Misc
    seed: int = 42
    report_to: str = "none"   # set "wandb" if W&B is available


# ---------------------------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "Kamu adalah SIDIX, asisten AI yang jujur dan bersumber. "
    "Setiap jawaban menggunakan label epistemik: [FAKTA], [OPINI], [SPEKULASI], [TIDAK TAHU]."
)


def _format_chat(pair: dict, tokenizer) -> str:
    """
    Format a Q&A pair into Qwen chat template.
    Input: {"prompt": "...", "completion": "..."}
    Output: tokenized string via apply_chat_template
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pair["prompt"]},
        {"role": "assistant", "content": pair["completion"]},
    ]
    # apply_chat_template returns a string with special tokens
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


def load_dataset(jsonl_path: str, tokenizer, eval_split: float = 0.1):
    """
    Read JSONL pairs, format to chat template, split train/eval.
    Returns (train_dataset, eval_dataset) as HF Dataset objects.
    """
    from datasets import Dataset

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                pair = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "prompt" not in pair or "completion" not in pair:
                continue

            text = _format_chat(pair, tokenizer)
            records.append({"text": text})

    if not records:
        raise ValueError(f"No valid records in {jsonl_path}")

    dataset = Dataset.from_list(records)

    # Train / eval split
    split = dataset.train_test_split(test_size=eval_split, seed=42)
    return split["train"], split["test"]


# ---------------------------------------------------------------------------
# 2. Setup model + LoRA
# ---------------------------------------------------------------------------

def setup_model_and_lora(config: TrainingConfig):
    """
    Load base model with 4-bit quantization and attach LoRA adapter.
    Returns (model, tokenizer).
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    print(f"[INFO] Loading base model: {config.base_model}")

    compute_dtype = getattr(torch, config.bnb_4bit_compute_dtype)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=bnb_config if config.load_in_4bit else None,
        device_map="auto",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        config.base_model,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Prepare for k-bit training
    if config.load_in_4bit:
        model = prepare_model_for_kbit_training(model)

    # Attach LoRA
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


# ---------------------------------------------------------------------------
# 3. Train
# ---------------------------------------------------------------------------

def train(config: TrainingConfig) -> None:
    """
    Full training run using SFTTrainer from trl.
    """
    import torch
    from transformers import TrainingArguments
    from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

    if not config.data_path:
        raise ValueError("--data_path is required")

    model, tokenizer = setup_model_and_lora(config)

    print(f"[INFO] Loading dataset: {config.data_path}")
    train_dataset, eval_dataset = load_dataset(
        config.data_path, tokenizer, eval_split=config.eval_split
    )
    print(f"[INFO] Train: {len(train_dataset)} | Eval: {len(eval_dataset)}")

    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        lr_scheduler_type=config.lr_scheduler_type,
        max_grad_norm=config.max_grad_norm,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_steps=config.eval_steps,
        evaluation_strategy="steps",
        save_total_limit=config.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        fp16=torch.cuda.is_available(),
        report_to=config.report_to,
        seed=config.seed,
        dataloader_num_workers=2,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        tokenizer=tokenizer,
        max_seq_length=config.max_seq_length,
        packing=False,
    )

    print("[INFO] Starting training ...")
    trainer.train()
    print("[INFO] Training complete.")


# ---------------------------------------------------------------------------
# 4. Save adapter
# ---------------------------------------------------------------------------

def save_adapter(output_dir: str, tokenizer=None) -> None:
    """
    Save LoRA adapter and tokenizer to output_dir.
    Usually called automatically by SFTTrainer, but exposed here for manual use.
    """
    from peft import PeftModel
    print(f"[INFO] Adapter saved at: {output_dir}")
    if tokenizer is not None:
        tokenizer.save_pretrained(output_dir)
        print(f"[INFO] Tokenizer saved at: {output_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> TrainingConfig:
    parser = argparse.ArgumentParser(
        description="QLoRA distillation training for SIDIX"
    )
    parser.add_argument("--base_model", default=TrainingConfig.base_model)
    parser.add_argument("--output_dir", default=TrainingConfig.output_dir)
    parser.add_argument("--data_path", required=True, help="Path to JSONL training data")
    parser.add_argument("--lora_r", type=int, default=TrainingConfig.lora_r)
    parser.add_argument("--lora_alpha", type=int, default=TrainingConfig.lora_alpha)
    parser.add_argument("--epochs", type=int, default=TrainingConfig.num_epochs)
    parser.add_argument("--batch_size", type=int, default=TrainingConfig.batch_size)
    parser.add_argument("--lr", type=float, default=TrainingConfig.learning_rate)
    parser.add_argument("--max_seq_length", type=int, default=TrainingConfig.max_seq_length)
    parser.add_argument("--no_4bit", action="store_true", help="Disable 4-bit quantization")
    parser.add_argument("--eval_split", type=float, default=TrainingConfig.eval_split)
    parser.add_argument("--report_to", default=TrainingConfig.report_to)

    args = parser.parse_args()

    return TrainingConfig(
        base_model=args.base_model,
        output_dir=args.output_dir,
        data_path=args.data_path,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_seq_length=args.max_seq_length,
        load_in_4bit=not args.no_4bit,
        eval_split=args.eval_split,
        report_to=args.report_to,
    )


if __name__ == "__main__":
    config = parse_args()
    print(f"[INFO] Config: {config}")
    train(config)
