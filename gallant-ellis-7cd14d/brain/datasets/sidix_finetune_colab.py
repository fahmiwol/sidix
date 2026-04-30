"""
SIDIX — QLoRA Fine-tune Qwen2.5-7B
Google Colab Pro+ (A100 40GB)

Cara pakai:
1. Upload file ini + finetune_sft.jsonl ke Google Drive
2. Buka Google Colab → Runtime → Change runtime type → A100 GPU
3. Mount Google Drive, copy file ke /content/
4. Jalankan sel satu per satu dari atas ke bawah

Estimasi waktu: 45-90 menit untuk 713 samples, 3 epoch di A100
Estimasi biaya: $0 (Colab Pro+) atau ~$2-5 (RunPod A100)
"""

# ════════════════════════════════════════════════════════
# SEL 1 — Install dependencies
# ════════════════════════════════════════════════════════
# !pip install -q transformers==4.40.0 peft==0.10.0 trl==0.8.6 bitsandbytes datasets accelerate

# ════════════════════════════════════════════════════════
# SEL 2 — Mount Google Drive (jika pakai Drive)
# ════════════════════════════════════════════════════════
# from google.colab import drive
# drive.mount('/content/drive')
# !cp "/content/drive/MyDrive/sidix/finetune_sft.jsonl" /content/finetune_sft.jsonl

# ════════════════════════════════════════════════════════
# SEL 3 — Load dataset
# ════════════════════════════════════════════════════════
import json
from datasets import Dataset

def load_sft_jsonl(path: str) -> Dataset:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return Dataset.from_list(records)

dataset = load_sft_jsonl("/content/finetune_sft.jsonl")
print(f"Dataset loaded: {len(dataset)} samples")
print("Sample:", dataset[0]["messages"][1]["content"][:100])

# Split train/eval (90/10)
split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split["train"]
eval_dataset = split["test"]
print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

# ════════════════════════════════════════════════════════
# SEL 4 — Load model + tokenizer dengan 4-bit quantization (QLoRA)
# ════════════════════════════════════════════════════════
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"  # base model dari Hugging Face

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = False
print("Model loaded OK")

# ════════════════════════════════════════════════════════
# SEL 5 — Setup LoRA config
# ════════════════════════════════════════════════════════
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,                    # rank — mulai dari 16, naikkan ke 32 jika loss tidak konvergen
    lora_alpha=32,           # scaling factor = 2 × r
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Expected: ~0.5-1% trainable (LoRA params << total params)

# ════════════════════════════════════════════════════════
# SEL 6 — Format dataset ke ChatML string
# ════════════════════════════════════════════════════════
def format_chatml(example):
    """Konversi messages list ke string ChatML untuk Qwen2.5."""
    text = ""
    for msg in example["messages"]:
        role = msg["role"]
        content = msg["content"]
        text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    text += "<|im_start|>assistant\n"
    return {"text": text}

train_dataset = train_dataset.map(format_chatml)
eval_dataset = eval_dataset.map(format_chatml)

# ════════════════════════════════════════════════════════
# SEL 7 — Training dengan SFTTrainer
# ════════════════════════════════════════════════════════
from trl import SFTTrainer, SFTConfig

OUTPUT_DIR = "/content/sidix-qwen2.5-7b-lora"

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,   # effective batch = 2 × 8 = 16
    gradient_checkpointing=True,
    optim="paged_adamw_32bit",
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    max_seq_length=2048,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=50,
    save_steps=100,
    save_total_limit=2,
    fp16=False,
    bf16=True,                        # A100 support bfloat16
    report_to="none",                 # ganti ke "wandb" jika pakai W&B
    dataset_text_field="text",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

print("Starting training...")
trainer.train()
print("Training complete!")

# ════════════════════════════════════════════════════════
# SEL 8 — Simpan LoRA adapter
# ════════════════════════════════════════════════════════
ADAPTER_DIR = "/content/sidix-lora-adapter"
trainer.model.save_pretrained(ADAPTER_DIR)
tokenizer.save_pretrained(ADAPTER_DIR)
print(f"LoRA adapter saved to {ADAPTER_DIR}")

# Copy ke Drive untuk disimpan
# !cp -r /content/sidix-lora-adapter "/content/drive/MyDrive/sidix/sidix-lora-adapter"
# print("Adapter copied to Google Drive")

# ════════════════════════════════════════════════════════
# SEL 9 — Quick eval: coba beberapa pertanyaan
# ════════════════════════════════════════════════════════
from peft import PeftModel
from transformers import pipeline

# Load adapter ke base model (opsional: merge dulu)
# model_merged = model.merge_and_unload()  # merge LoRA ke base weight

test_questions = [
    "Apa itu SIDIX dan apa diferensiasinya dari LLM lain?",
    "Jelaskan konsep sanad dalam tradisi hadis.",
    "Apa itu LoRA dan mengapa dipakai untuk fine-tuning model besar?",
    "Bagaimana cara kerja BM25 dalam sistem retrieval?",
]

SIDIX_SYSTEM = (
    "Kamu adalah SIDIX, AI multipurpose yang dibangun di atas prinsip kejujuran (sidq), "
    "sitasi (sanad), dan verifikasi (tabayyun). Jawab berdasarkan fakta, bedakan fakta vs hipotesis, "
    "sebutkan sumber jika ada, dan akui keterbatasan jika tidak tahu."
)

for q in test_questions:
    prompt = f"<|im_start|>system\n{SIDIX_SYSTEM}<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    print(f"\nQ: {q}")
    print(f"A: {response[:300]}")
    print("-" * 60)

# ════════════════════════════════════════════════════════
# SEL 10 — (Opsional) Merge LoRA ke base model untuk deployment
# ════════════════════════════════════════════════════════
# CATATAN: Butuh RAM lebih besar (tidak pakai 4-bit). Skip di Colab jika OOM.
# Jalankan di mesin dengan 16GB+ VRAM atau pakai RunPod A100 80GB.

# from peft import PeftModel
# base_model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto")
# merged_model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
# merged_model = merged_model.merge_and_unload()
# merged_model.save_pretrained("/content/sidix-merged-model")
# tokenizer.save_pretrained("/content/sidix-merged-model")
# print("Merged model saved — ready for deployment via Ollama/vLLM")
