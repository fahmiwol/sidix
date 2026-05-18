# Machine Learning & AI Engineering

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari dokumentasi scikit-learn, PyTorch, Hugging Face, fast.ai, dan praktik industri ML/AI.
> Relevan untuk: ML engineers, AI researchers, backend developers integrating AI, data scientists
> Tags: machine-learning, deep-learning, pytorch, scikit-learn, llm, lora, qlora, rag, fine-tuning, transformers, prompt-engineering

## ML Fundamentals

### Learning Paradigms
```
Supervised Learning    — labeled data (X → y)
  Classification:   predict category (spam/not spam, image class)
  Regression:       predict continuous value (price, temperature)

Unsupervised Learning  — no labels, find structure in data
  Clustering:       k-means, DBSCAN, hierarchical
  Dimensionality Reduction: PCA, t-SNE, UMAP
  Generative:       VAEs, GANs

Self-Supervised        — create labels from data itself
  Masked prediction (BERT), next-token prediction (GPT)
  Used to pretrain large models cheaply

Reinforcement Learning — agent learns from rewards/penalties
  Policy gradient, Q-learning, PPO
  Used in: game playing, robotics, RLHF for LLMs
```

### Overfitting and Underfitting
```
Underfitting (high bias):
  Model too simple → high training AND test error
  Symptoms: training loss plateaus early and high
  Solutions: more complex model, more features, train longer

Overfitting (high variance):
  Model too complex → low training error, HIGH test error
  Symptoms: training loss << test loss
  Solutions: regularization, dropout, more data, data augmentation,
             early stopping, reduce model size

Bias-Variance Decomposition:
  Total Error = Bias² + Variance + Irreducible Noise
  
  High bias = systematic wrong predictions (underfitting)
  High variance = inconsistent predictions (overfitting)
  Goal: find sweet spot with cross-validation
```

### Regularization Techniques
```python
# L1 (Lasso) — promotes sparsity (zero out unimportant features)
# L2 (Ridge) — penalizes large weights (smooth weights)

from sklearn.linear_model import Ridge, Lasso, ElasticNet

ridge = Ridge(alpha=1.0)   # L2 regularization
lasso = Lasso(alpha=0.1)   # L1 regularization
elastic = ElasticNet(alpha=0.1, l1_ratio=0.5)  # mix of L1 and L2

# Dropout in neural networks — zero random neurons during training
import torch.nn as nn
layer = nn.Sequential(
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Dropout(p=0.3),   # 30% probability of zeroing each neuron
    nn.Linear(128, 64),
)
```

## Scikit-learn Pipeline

### Data Preprocessing and Feature Engineering
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Load data
df = pd.read_csv("data.csv")
X = df.drop("target", axis=1)
y = df["target"]

# Define column types
numerical_cols = ["age", "income", "score"]
categorical_cols = ["city", "category", "gender"]

# Numerical pipeline
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),   # fill missing with median
    ("scaler", StandardScaler()),                    # z-score normalization
])

# Categorical pipeline
cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

# Combine
preprocessor = ColumnTransformer([
    ("num", num_pipeline, numerical_cols),
    ("cat", cat_pipeline, categorical_cols),
])

# Full ML pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

full_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(n_estimators=100, random_state=42)),
])
```

### Train/Test Split and Cross-Validation
```python
from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold,
    GridSearchCV, RandomizedSearchCV
)

# Train/validation/test split
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# K-fold cross-validation (avoids data leakage)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(full_pipeline, X_train, y_train, cv=cv, scoring="f1_macro")
print(f"CV F1: {scores.mean():.4f} ± {scores.std():.4f}")

# Hyperparameter tuning
param_grid = {
    "classifier__n_estimators": [100, 200, 300],
    "classifier__max_depth": [None, 10, 20],
    "classifier__min_samples_split": [2, 5, 10],
}
grid_search = GridSearchCV(full_pipeline, param_grid, cv=5, scoring="f1_macro", n_jobs=-1, verbose=1)
grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
best_model = grid_search.best_estimator_

# Randomized search (faster for large parameter spaces)
from scipy.stats import randint, uniform
param_dist = {
    "classifier__n_estimators": randint(100, 500),
    "classifier__max_features": uniform(0.1, 0.9),
}
rand_search = RandomizedSearchCV(full_pipeline, param_dist, n_iter=50, cv=5, n_jobs=-1)
rand_search.fit(X_train, y_train)
```

### Evaluation Metrics
```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score
)
import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay, ConfusionMatrixDisplay

y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)[:, 1]

# Classification metrics
print(classification_report(y_test, y_pred, target_names=["No", "Yes"]))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

# When to use which metric:
# Accuracy: balanced classes only
# Precision: when false positives are costly (spam filter)
# Recall: when false negatives are costly (disease detection)
# F1: harmonic mean of precision and recall
# AUC-ROC: threshold-independent, good for ranking problems
# MCC (Matthews): best single metric for imbalanced binary classification

# Regression metrics
# RMSE: penalizes large errors more (same units as target)
# MAE: more robust to outliers (same units)
# R²: proportion of variance explained (0 to 1; can be negative if model is worse than mean)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
```

## Neural Networks

### Architecture and Concepts
```
Input Layer    — receives raw features (flattened image, token embeddings)
Hidden Layers  — learn intermediate representations
Output Layer   — final predictions (softmax for classification, linear for regression)

Activation Functions (introduce non-linearity):
  ReLU:        f(x) = max(0, x) — most common, fast, avoids vanishing gradient
  LeakyReLU:   f(x) = x if x>0 else αx — handles dying ReLU
  Sigmoid:     f(x) = 1/(1+e^-x) — outputs 0-1, used for binary classification output
  Tanh:        outputs -1 to 1, zero-centered
  GELU:        smooth approximation of ReLU, used in Transformers
  Softmax:     normalizes to probability distribution, used in multi-class output

Backpropagation:
  1. Forward pass: compute predictions
  2. Compute loss (cross-entropy, MSE)
  3. Backward pass: compute gradients via chain rule
  4. Update weights: w -= lr * gradient

Optimizers:
  SGD:      w -= lr * gradient (noisy but good generalization)
  Adam:     adaptive learning rate per parameter (fast convergence)
  AdamW:    Adam + decoupled weight decay (preferred for LLMs)
  Lion:     memory-efficient optimizer for large models
```

### PyTorch Basics
```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Tensors — multi-dimensional arrays with autograd
x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
y = torch.randn(3, 4)                     # random from N(0,1)
z = torch.zeros(5, 5)
eye = torch.eye(4)

# Device management
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x = x.to(device)

# Autograd
x = torch.tensor([2.0], requires_grad=True)
y = x ** 3 + 2 * x
y.backward()  # compute dy/dx
x.grad        # tensor([14.]) — 3x² + 2 at x=2 → 12+2=14

# Defining a model
class FeedForwardNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
        )
        self._init_weights()
    
    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

# Custom Dataset
class TextDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[int], tokenizer, max_length: int = 128):
        self.encodings = tokenizer(texts, truncation=True, padding=True,
                                    max_length=max_length, return_tensors="pt")
        self.labels = torch.tensor(labels, dtype=torch.long)
    
    def __len__(self) -> int:
        return len(self.labels)
    
    def __getitem__(self, idx: int) -> dict:
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item
```

### PyTorch Training Loop
```python
def train_epoch(model, dataloader, optimizer, criterion, device, scaler=None):
    model.train()
    total_loss = 0.0
    
    for batch in dataloader:
        inputs = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        
        optimizer.zero_grad()
        
        # Mixed precision training (uses float16 for speed, float32 for stability)
        if scaler:
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds, all_labels = [], []
    
    with torch.no_grad():
        for batch in dataloader:
            inputs = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
            preds = outputs.argmax(dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    from sklearn.metrics import f1_score
    return total_loss / len(dataloader), f1_score(all_labels, all_preds, average="macro")

# Training orchestration
model = FeedForwardNet(768, 256, 2).to(device)
optimizer = optim.AdamW(model.parameters(), lr=2e-4, weight_decay=0.01)
criterion = nn.CrossEntropyLoss()
scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None

# Learning rate scheduler
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
# Alternative: warmup + decay
from transformers import get_linear_schedule_with_warmup
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=100, num_training_steps=1000)

best_f1 = 0.0
patience = 3
no_improve = 0

for epoch in range(50):
    train_loss = train_epoch(model, train_loader, optimizer, criterion, device, scaler)
    val_loss, val_f1 = evaluate(model, val_loader, criterion, device)
    scheduler.step()
    
    print(f"Epoch {epoch+1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, val_f1={val_f1:.4f}")
    
    if val_f1 > best_f1:
        best_f1 = val_f1
        torch.save(model.state_dict(), "best_model.pt")
        no_improve = 0
    else:
        no_improve += 1
        if no_improve >= patience:
            print("Early stopping")
            break
```

## Fine-tuning LLMs: LoRA and QLoRA

### Why Fine-tuning?
Fine-tuning adapts a pretrained LLM to a specific task or domain without training from scratch. The pretrained model has already learned language understanding; fine-tuning redirects it.

### LoRA (Low-Rank Adaptation)
Instead of updating all model weights (billions of parameters), LoRA adds small trainable "adapter" matrices.

```
Original weight matrix W (d × k) — frozen
LoRA adds: ΔW = B × A
  where B is (d × r) and A is (r × k), r << d (rank, typically 4-64)
  Parameters saved: d×k vs r×(d+k)
  With d=4096, k=4096, r=16: 16M vs 131M (8x fewer params)

During inference: W' = W + α/r × B × A (α = scaling factor)
```

```python
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

# LoRA config
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                           # rank — higher = more capacity, more memory
    lora_alpha=32,                  # scaling factor (typically 2×r)
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],  # which layers to adapt
    bias="none",
)

from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B")
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Trainable: 41,943,040 || All: 7,242,588,160 || Trainable%: 0.5793%
```

### QLoRA (Quantized LoRA)
Load the base model in 4-bit or 8-bit quantization, add LoRA adapters in full precision. Allows fine-tuning 7B+ models on a single GPU with 24GB VRAM.

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch

# 4-bit quantization config (NF4 = Normal Float 4)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,   # nested quantization: saves more memory
    bnb_4bit_quant_type="nf4",        # NF4 data type (optimal for normally distributed weights)
    bnb_4bit_compute_dtype=torch.bfloat16,  # compute in bfloat16 for speed
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B",
    quantization_config=bnb_config,
    device_map="auto",        # automatically distribute across available GPUs
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

# Prepare for k-bit training (cast layer norms, fix frozen params)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(r=64, lora_alpha=16, lora_dropout=0.1,
                          target_modules=["q_proj", "v_proj"], bias="none",
                          task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, lora_config)
```

### Supervised Fine-Tuning (SFT) with TRL
```python
from trl import SFTTrainer, SFTConfig
from transformers import TrainingArguments
from datasets import Dataset

# Prepare dataset (instruction tuning format)
def format_prompt(example):
    return f"""<|im_start|>system
You are SIDIX, an expert AI assistant.
<|im_end|>
<|im_start|>user
{example['instruction']}
<|im_end|>
<|im_start|>assistant
{example['output']}
<|im_end|>"""

dataset = Dataset.from_list([
    {"instruction": "What is Python?", "output": "Python is a high-level programming language..."},
    # ... more examples
])

training_args = SFTConfig(
    output_dir="./qwen-sidix-lora",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,    # effective batch = 2 × 8 = 16
    learning_rate=2e-4,
    fp16=False,
    bf16=True,                         # bfloat16 preferred for training stability
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    load_best_model_at_end=True,
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    optim="paged_adamw_32bit",         # paged optimizer for QLoRA (manages GPU memory)
    max_seq_length=2048,
    gradient_checkpointing=True,       # trade compute for memory
    report_to="tensorboard",
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    formatting_func=format_prompt,
    args=training_args,
)

trainer.train()

# Save adapter (not full model — small!)
model.save_pretrained("./sidix-lora-adapter")
tokenizer.save_pretrained("./sidix-lora-adapter")

# Merge adapter back into base model for deployment
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./sidix-merged", safe_serialization=True)
```

## RAG Pipeline (Retrieval-Augmented Generation)

RAG grounds LLM responses in retrieved documents, reducing hallucination and keeping knowledge current.

```
Architecture:
  1. Indexing (offline):
     Documents → Chunking → Embeddings → Vector Store
  
  2. Retrieval (online):
     Query → Embedding → Similarity Search → Top-k Chunks
  
  3. Generation:
     [System Prompt + Retrieved Chunks + User Query] → LLM → Response

Components:
  Chunking:     split documents into pieces (512-1024 tokens, with overlap)
  Embeddings:   encode text as dense vectors (semantic similarity)
  Vector Store: efficient similarity search (FAISS, Chroma, Qdrant, Weaviate)
  BM25:         sparse retrieval (keyword matching, no embedding needed)
  Reranking:    cross-encoder to rerank top candidates
  Hybrid:       combine BM25 + vector search (best of both worlds)
```

```python
# BM25 RAG (SIDIX uses this)
from rank_bm25 import BM25Okapi
import json
from pathlib import Path

class BM25RAG:
    def __init__(self, corpus_dir: str):
        self.documents = []
        self.tokenized_corpus = []
        self._load_corpus(Path(corpus_dir))
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def _load_corpus(self, corpus_dir: Path):
        for md_file in corpus_dir.glob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            chunks = self._chunk(text, chunk_size=400, overlap=50)
            for chunk in chunks:
                self.documents.append({"source": md_file.name, "content": chunk})
                self.tokenized_corpus.append(chunk.lower().split())
    
    def _chunk(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            {"score": scores[i], **self.documents[i]}
            for i in top_indices if scores[i] > 0
        ]
    
    def augmented_prompt(self, query: str, top_k: int = 5) -> str:
        docs = self.retrieve(query, top_k)
        context = "\n\n---\n\n".join(
            f"[Source: {d['source']}]\n{d['content']}" for d in docs
        )
        return f"""Answer the question based on the following context.
If the context doesn't contain the answer, say so.

Context:
{context}

Question: {query}
Answer:"""

# Dense vector RAG (semantic search)
from sentence_transformers import SentenceTransformer
import numpy as np

class DenseRAG:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
    
    def index(self, documents: list[str]):
        self.documents = documents
        self.embeddings = self.encoder.encode(documents, batch_size=32,
                                               show_progress_bar=True,
                                               normalize_embeddings=True)
    
    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[float, str]]:
        query_emb = self.encoder.encode([query], normalize_embeddings=True)
        scores = np.dot(self.embeddings, query_emb.T).squeeze()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(float(scores[i]), self.documents[i]) for i in top_indices]
```

## Prompt Engineering

```python
# System prompt design
SYSTEM_PROMPT = """You are SIDIX, an expert AI assistant specializing in programming and software engineering.

You ALWAYS:
- Provide accurate, working code examples
- Explain the "why" behind decisions, not just the "what"
- Mention trade-offs and alternative approaches
- Use clear, concise language

You NEVER:
- Make up APIs or library functions that don't exist
- Provide code without testing it mentally
- Give vague answers when a specific answer is possible

When code is requested, format it as:
```language
# code here
```

If you're unsure, say: "I'm not certain about [X]. What I do know is [Y]."
"""

# Few-shot prompting
FEW_SHOT_TEMPLATE = """
Convert the user's natural language query into a SQL SELECT statement.

Example 1:
Query: "Show me all users who signed up in January 2024"
SQL: SELECT * FROM users WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01';

Example 2:
Query: "Top 5 products by revenue"
SQL: SELECT product_name, SUM(quantity * price) AS revenue FROM order_items GROUP BY product_name ORDER BY revenue DESC LIMIT 5;

Now convert:
Query: "{user_query}"
SQL:"""

# Chain of thought — improves reasoning
COT_PROMPT = """Solve this step by step, showing your reasoning.

Problem: {problem}

Let me think through this carefully:
Step 1:"""

# Structured output with JSON mode
STRUCTURED_PROMPT = """Extract the following information from the text and return it as JSON.
Required fields: name (string), age (integer), skills (array of strings), available (boolean)
If a field is missing, use null.

Text: {input_text}

Return ONLY valid JSON, no explanation:"""
```

## LLM Evaluation

```python
# Key metrics for LLM evaluation
"""
Task-specific:
  BLEU (0-1):       n-gram overlap with reference translations
  ROUGE (0-1):      recall-based n-gram overlap (summarization)
  METEOR:           better than BLEU, considers synonyms
  BERTScore:        embedding-based semantic similarity

Code generation:
  pass@k:           fraction of problems solved correctly in k attempts
  HumanEval:        164 Python coding problems benchmark
  MBPP:             mostly basic Python problems benchmark

General:
  MMLU:             multitask multiple choice (57 subjects)
  HellaSwag:        commonsense reasoning
  TruthfulQA:       measures factual accuracy / hallucination rate

RAG-specific:
  Faithfulness:     is the answer grounded in retrieved context?
  Answer Relevance: does the answer address the question?
  Context Recall:   was relevant context retrieved?
  RAGAS:            automated evaluation framework for RAG
"""

# Simple evaluation harness
def evaluate_rag(rag_system, test_cases: list[dict]) -> dict:
    """
    test_cases: [{"question": str, "expected_answer": str, "expected_sources": list}]
    """
    from rouge_score import rouge_scorer
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    
    results = []
    for case in test_cases:
        response = rag_system.generate(case["question"])
        scores = scorer.score(case["expected_answer"], response["answer"])
        results.append({
            "question": case["question"],
            "rouge1": scores["rouge1"].fmeasure,
            "rougeL": scores["rougeL"].fmeasure,
            "sources_correct": any(s in response["sources"] for s in case["expected_sources"]),
        })
    
    return {
        "avg_rouge1": np.mean([r["rouge1"] for r in results]),
        "avg_rougeL": np.mean([r["rougeL"] for r in results]),
        "source_accuracy": np.mean([r["sources_correct"] for r in results]),
        "n_evaluated": len(results),
    }
```

## ML Model Deployment

```python
# Save and load models
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Save
model.save_pretrained("./model")
tokenizer.save_pretrained("./model")

# Load
model = AutoModelForCausalLM.from_pretrained("./model",
    device_map="auto",
    torch_dtype=torch.float16,  # or bfloat16
)

# FastAPI serving
from fastapi import FastAPI
from pydantic import BaseModel
import torch

app = FastAPI()
model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    tokenizer = AutoTokenizer.from_pretrained("./model")
    model = AutoModelForCausalLM.from_pretrained("./model",
        device_map="auto", torch_dtype=torch.float16)
    model.eval()

class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

@app.post("/generate")
async def generate(request: GenerateRequest):
    inputs = tokenizer(request.prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return {"response": response}
```

## Key ML Libraries Quick Reference

| Library | Use Case |
|---------|----------|
| scikit-learn | Traditional ML, preprocessing, evaluation |
| PyTorch | Deep learning framework |
| transformers | HuggingFace — load/fine-tune LLMs |
| peft | LoRA, QLoRA, other parameter-efficient methods |
| trl | SFT, RLHF, DPO training |
| datasets | HuggingFace dataset loading/processing |
| bitsandbytes | 4-bit/8-bit quantization |
| accelerate | Multi-GPU, mixed precision training |
| sentence-transformers | Text embeddings |
| rank-bm25 | BM25 keyword retrieval |
| faiss-cpu/gpu | Vector similarity search |
| ragas | RAG evaluation framework |
| langchain | LLM orchestration (alternative: llama-index) |

## Referensi & Sumber Lanjut
- https://pytorch.org/docs/stable/
- https://huggingface.co/docs/transformers/
- https://huggingface.co/docs/peft/
- https://huggingface.co/docs/trl/
- https://arxiv.org/abs/2106.09685 — LoRA paper
- https://arxiv.org/abs/2305.14314 — QLoRA paper
- https://docs.ragas.io/ — RAG evaluation
- https://scikit-learn.org/stable/user_guide.html
- https://fast.ai/ — practical deep learning course
- roadmap.sh/ai-data-scientist
- roadmap.sh/mlops
