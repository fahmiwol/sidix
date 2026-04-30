# kaggle-notebook-fix

**Sumber:** claude-code  
**Tanggal:** 2026-04-17  
**Tags:** kaggle, fine-tuning, qlora, bug-fix, dataset-path  

## Konteks

Kaggle notebook SIDIX_GEN error: FileNotFoundError finetune_sft.jsonl

## Pengetahuan

Bug: notebook hardcode path /kaggle/input/datasets/mighan/sidix-sft-dataset/finetune_sft.jsonl — ini SALAH. Kaggle strip owner prefix saat dataset di-attach ke notebook.

Fix: gunakan glob auto-detect dengan dua kandidat path:
1. /kaggle/input/sidix-sft-dataset/*.jsonl  ← path standar Kaggle (benar)
2. /kaggle/input/datasets/mighan/sidix-sft-dataset/*.jsonl  ← fallback

Kalau dua-duanya kosong → scan recursive /kaggle/input/**/*.jsonl
Kalau tetap kosong → raise FileNotFoundError dengan pesan jelas: "Pastikan dataset sidix-sft-dataset sudah di-attach ke notebook ini."

Dataset lokal ada di: brain/datasets/finetune_sft.jsonl
Format: JSONL, setiap baris = {"messages": [...], "source_id": "...", "tags": [...]}
Training: QLoRA Qwen2.5-7B-Instruct, LoRA r=16 alpha=32, 3 epochs, output ke /kaggle/working/sidix-lora-adapter/

---
*Diambil dari SIDIX MCP Knowledge Base*
