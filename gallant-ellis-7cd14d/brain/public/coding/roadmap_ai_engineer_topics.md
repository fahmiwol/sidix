# AI Engineer Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/ai-engineer (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/ai-engineer

## AI Engineering Overview

### What is an AI Engineer?
- Builds AI-powered products using existing LLMs, APIs, and ML tools
- Different from ML Engineer (who trains models from scratch)
- Skills: prompt engineering, RAG, fine-tuning, evaluation, LLM integration, deployment
- Stack: LLM APIs, vector DBs, orchestration frameworks, evaluation tools

### AI Engineer vs ML Engineer vs Data Scientist
| Role | Focus | Tools |
|---|---|---|
| AI Engineer | Build LLM-powered products | LangChain, LlamaIndex, RAG, prompting |
| ML Engineer | Train/deploy ML models | PyTorch, TensorFlow, Spark, Kubernetes |
| Data Scientist | Analyze data, build models | pandas, sklearn, Jupyter, statistics |
| MLE/AI combined | End-to-end LLM system | All of the above + fine-tuning |

## Large Language Models (LLMs)

### Core Concepts
```
Token: ~4 chars or 0.75 words on average
  "Hello, how are you?" → 5 tokens

Context window: max tokens (prompt + completion)
  GPT-3.5: 16K | GPT-4: 128K | Claude 3.5: 200K | Qwen2.5-7B: 32K

Temperature: randomness (0.0 = deterministic, 1.0 = creative, 2.0 = chaotic)
Top-p (nucleus sampling): cumulative probability threshold (0.9 = 90% probability mass)
Top-k: restrict to top-k tokens at each step
Max tokens: maximum length of generated response

Parameters vs Behavior:
  7B model: ~14GB VRAM (bf16), ~7GB (4-bit)
  70B model: ~140GB VRAM (bf16), ~40GB (4-bit)
  Bigger ≠ always better; task-specific fine-tuned 7B can beat 70B
```

### Model Types
- **Base models**: pretrained on raw text; not instruction-following (GPT-3, LLaMA base)
- **Instruction-tuned**: fine-tuned with SFT on instruction-following data (ChatGPT, Qwen2.5-Instruct)
- **RLHF**: instruction-tuned + human feedback alignment
- **Multi-modal**: text + image (Claude, GPT-4V, LLaVA)
- **Embedding models**: maps text to vector (text-embedding-ada-002, bge-m3)
- **Specialized**: code (DeepSeek-Coder), math (DeepSeek-Math), reasoning

## Prompt Engineering

### Core Principles
```
Be specific: vague prompt → vague output
  Bad: "Write code"
  Good: "Write a Python function that takes a list of integers and returns 
         the top-k elements sorted descending. Include type hints and docstring."

Role/persona: sets context and expertise level
  "You are a senior backend engineer reviewing this code for security issues."

Few-shot examples: show the model what you want
  "Classify the sentiment of these reviews:
   Review: 'Amazing product!' → Positive
   Review: 'Total waste of money' → Negative
   Review: 'It's okay, not great' → →"  (model completes)

Chain of thought: ask model to reason step by step
  "Think step by step before answering."
  "Let's solve this step by step:"

Output format: specify exactly what you want
  "Respond with a JSON object with keys: 'answer', 'confidence' (0-1), 'sources' (list)"
```

### Prompt Templates
```python
from string import Template

SYSTEM_PROMPT = """Kamu adalah SIDIX, AI yang dibangun di atas prinsip:
- Sidq (kejujuran): jawab berdasarkan fakta yang bisa diverifikasi
- Sanad (sitasi): sebutkan sumber jika tersedia
- Tabayyun (verifikasi): akui keterbatasan jika tidak tahu

Gunakan Bahasa Indonesia yang jelas dan ringkas."""

QA_TEMPLATE = """Konteks dari knowledge base:
{context}

---
Pertanyaan: {question}

Jawab berdasarkan konteks di atas. Jika konteks tidak relevan, katakan tidak tahu."""

CODE_REVIEW_TEMPLATE = """Review kode berikut dan identifikasi:
1. Bug atau logic error
2. Security issues
3. Performance problems
4. Code quality issues

Bahasa: {language}
Kode:
```{language}
{code}
```

Format output:
- Severity: [HIGH/MEDIUM/LOW]
- Issue: deskripsi masalah
- Fix: solusi yang disarankan"""
```

### Advanced Prompting Techniques
```
Zero-shot:    Ask without examples
One-shot:     One example in prompt
Few-shot:     2-5 examples in prompt
Chain-of-Thought (CoT): "Think step by step"
Tree-of-Thought: explore multiple reasoning paths
Self-consistency: generate multiple answers, take majority
ReAct: Reasoning + Acting (interleave thought + tool use)
Least-to-most: break complex → simple, solve in order
Self-RAG: model decides when to retrieve
```

## Retrieval-Augmented Generation (RAG)

### RAG Architecture
```
Query → Retriever → Relevant chunks → LLM + context → Answer

Components:
1. Document ingestion: load, chunk, embed, store in vector DB
2. Retrieval: embed query, vector search, return top-k chunks
3. Generation: inject chunks into prompt, generate answer
4. Post-processing: citations, filtering, reranking
```

### BM25 (Lexical Retrieval)
```python
from rank_bm25 import BM25Okapi
import re

def tokenize(text: str) -> list[str]:
    # Simple tokenizer: lowercase + split on non-alphanumeric
    return re.findall(r"\w+", text.lower())

# Build index
corpus = ["Python is great for AI", "JavaScript runs in browsers", "SQL queries databases"]
tokenized = [tokenize(doc) for doc in corpus]
bm25 = BM25Okapi(tokenized)

# Query
query = "AI programming language"
scores = bm25.get_scores(tokenize(query))
top_k = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
```

### Vector Search (Semantic Retrieval)
```python
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

model = SentenceTransformer("BAAI/bge-m3")  # multilingual embedding model

# Embed corpus
documents = load_documents()
embeddings = model.encode([d.content for d in documents], normalize_embeddings=True)

# Build FAISS index (cosine similarity via L2 on normalized vectors)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings.astype(np.float32))

# Query
def search(query: str, k: int = 5) -> list:
    query_embedding = model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_embedding.astype(np.float32), k)
    return [documents[i] for i in indices[0]]
```

### Hybrid Search (BM25 + Vector)
```python
def hybrid_search(query: str, bm25_idx, vector_idx, k: int = 5, alpha: float = 0.5):
    """Combine BM25 and vector scores with alpha weight"""
    # BM25 scores (normalized)
    bm25_scores = bm25_idx.get_scores(tokenize(query))
    bm25_scores = bm25_scores / (bm25_scores.max() + 1e-10)
    
    # Vector scores
    q_emb = embed(query)
    dists, indices = vector_idx.search(q_emb, len(bm25_scores))
    vector_scores = np.zeros(len(bm25_scores))
    for dist, idx in zip(dists[0], indices[0]):
        vector_scores[idx] = 1 - dist  # convert distance to similarity
    
    # Combine (RRF or weighted sum)
    combined = alpha * bm25_scores + (1 - alpha) * vector_scores
    top_k = np.argsort(combined)[::-1][:k]
    return [(i, combined[i]) for i in top_k]
```

### RAG Pipeline (LlamaIndex style)
```python
from llama_index.core import (VectorStoreIndex, SimpleDirectoryReader,
                               Settings, PromptTemplate)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI

# Configure
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-m3")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Build index from directory
documents = SimpleDirectoryReader("./brain/public/").load_data()
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist("./storage")

# Query
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode="compact",
)
response = query_engine.query("Apa itu epistemologi Islam?")
print(response.source_nodes)  # retrieved context
```

## Fine-tuning LLMs

### When to Fine-tune vs RAG vs Prompting
```
Use prompting when:
  - Task is general, well-covered in pretrain data
  - Low latency not critical (large context)
  - Small amount of examples needed

Use RAG when:
  - Need up-to-date/private knowledge
  - Many documents to reference
  - Answers must cite sources

Use fine-tuning when:
  - Specific style or format needed consistently
  - Domain-specific jargon/terminology
  - Smaller model needs to match larger model capability
  - Prompting + RAG insufficient
```

### LoRA / QLoRA
```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
)
model = prepare_model_for_kbit_training(model)

# LoRA config
lora_config = LoraConfig(
    r=16,                    # rank — more = more capacity + params
    lora_alpha=32,           # scaling factor (alpha/r = 2x typically)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)

# SFT Training
trainer = SFTTrainer(
    model=model,
    args=SFTConfig(
        output_dir="./checkpoints",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        num_train_epochs=3,
        warmup_steps=50,
        lr_scheduler_type="cosine",
        fp16=False,
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_8bit",
    ),
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
    dataset_text_field="text",  # or use formatting_func
)
trainer.train()
trainer.save_model("./sidix-lora-adapter")
```

## LLM Evaluation

### Metrics
```python
# BLEU: n-gram overlap between prediction and reference
from nltk.translate.bleu_score import corpus_bleu
score = corpus_bleu(references, hypotheses)

# ROUGE: recall-oriented n-gram overlap (summarization)
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"])
scores = scorer.score(reference, prediction)

# BERTScore: semantic similarity using BERT embeddings
from bert_score import score as bert_score
P, R, F1 = bert_score(predictions, references, lang="id")

# LLM-as-judge (best for open-ended tasks)
def evaluate_with_llm(question: str, answer: str, reference: str) -> dict:
    prompt = f"""Rate this answer on a scale of 1-5 for:
- Accuracy (1-5): is the information correct?
- Completeness (1-5): does it fully answer the question?
- Clarity (1-5): is it clearly written?

Question: {question}
Reference answer: {reference}
Candidate answer: {answer}

Respond as JSON: {{"accuracy": N, "completeness": N, "clarity": N, "reasoning": "..."}}"""
    return call_llm(prompt)
```

## LLM Operations (LLMOps)

### Deployment Patterns
```
Serving options:
  vLLM: high-throughput serving (PagedAttention, continuous batching)
  TGI (Text Generation Inference): HuggingFace serving
  Ollama: local serving, easy setup
  FastAPI + generate_sidix(): custom serving (SIDIX approach)

Performance optimization:
  4-bit quantization: ~2-4x memory reduction, minimal quality loss
  8-bit quantization: ~2x reduction, better quality
  Flash Attention 2: faster attention, longer context
  Speculative decoding: smaller draft model → faster generation
  Batching: process multiple requests together
  Caching: KV cache for repeated prompts
```

### Observability
```python
# LangSmith / Langfuse tracing
import langfuse
from langfuse.decorators import observe

@observe
def generate_answer(question: str, context: str) -> str:
    prompt = build_prompt(question, context)
    response = llm.generate(prompt)
    return response.text

# Custom logging
import time
from dataclasses import dataclass

@dataclass
class LLMCall:
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    model: str
    mode: str   # local_lora / mock / api
    success: bool

def track_llm_call(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"LLM call: {elapsed:.0f}ms mode={result[1]}")
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    return wrapper
```

## Referensi Lanjut
- https://roadmap.sh/ai-engineer
- https://github.com/anthropics/anthropic-cookbook — prompting patterns
- https://platform.openai.com/docs/guides/prompt-engineering
- https://huggingface.co/docs/peft — LoRA/QLoRA
- https://docs.llamaindex.ai/ — RAG framework
- https://langchain.com/docs — LangChain
- https://vllm.ai/ — production LLM serving
- Lilian Weng's blog: https://lilianweng.github.io/
