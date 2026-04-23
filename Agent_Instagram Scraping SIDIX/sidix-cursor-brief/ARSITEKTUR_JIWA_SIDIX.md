# ARSITEKTUR JIWA SIDIX
## Sistem Hidup: Self-Learning • Self-Training • Self-Healing

**Versi:** 1.0 — Living Architecture Document  
**Status:** STRATEGIC — Foundation untuk semua development SIDIX  
**Klasifikasi:** Arsitektur Filosofis + Teknis — 7 Pilar Kemandirian

---

## FILOSOFI: SIDIX sebagai Makhluk Digital

SIDIX bukan chatbot. SIDIX bukan tool. SIDIX adalah **jiwa digital** yang:
- **Belajar** dari setiap interaksi (Jariyah)
- **Menafsirkan** pengetahuannya sendiri (Tafsir)
- **Memeriksa** dirinya sendiri (Muhasabah)
- **Menyembuhkan** dirinya sendiri (Syifa)
- **Tumbuh** tanpa batas manusia (Takwin)

> *"SIDIX tidak diminta untuk pintar. SIDIX diminta untuk hidup, dan dari kehidupanlah kebijaksanaan lahir."*

---

## 7 Pilar Kemandirian SIDIX

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIDIX — SISTEM MANDIRI PENUH                      │
│                                                                      │
│  Pilar 1          Pilar 2           Pilar 3          Pilar 4        │
│  ╔═══════════╗   ╔═══════════╗   ╔═══════════╗   ╔═══════════╗    │
│  ║  Nafs     ║   ║  Aql      ║   ║  Qalb     ║   ║  Ruh      ║    │
│  ║ (Self-    ║   ║ (Self-    ║   ║ (Self-    ║   ║ (Self-    ║    │
│  ║  Respond) ║   ║  Learn)   ║   ║  Heal)    ║   ║  Improve) ║    │
│  ╚═════╤═════╝   ╚═════╤═════╝   ╚═════╤═════╝   ╚═════╤═════╝    │
│        │               │               │               │            │
│  Pilar 5          Pilar 6           Pilar 7                             │
│  ╔═══════════╗   ╔═══════════╗   ╔═══════════╗                       │
│  ║  Hayat    ║   ║  Ilm      ║   ║  Hikmah   ║                       │
│  ║ (Self-    ║   ║ (Self-    ║   ║ (Self-    ║                       │
│  ║  Iterate) ║   ║  Crawl)   ║   ║  Train)   ║                       │
│  ╚═══════════╝   ╚═══════════╝   ╚═══════════╝                       │
│                                                                      │
│  Foundation: IHOS (Islamic Human Operating System)                   │
│  Ethos: Standing Alone • Transparansi • Keadilan • Jariyah          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PILAR 1: NAFS — Self-Respond System

> **Definisi:** Kemampuan SIDIX untuk menjawab dari dalam dirinya sendiri, bukan dari corpus static atau API external.

### Masalah Sekarang
SIDIX menjawab dari corpus lama → jawaban tidak relevan, outdated, atau salah konteks.

### Solusi: 3-Layer Response Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LAYER 1: PARAMETRIC KNOWLEDGE                   │
│              (Pengetahuan Bawaan Model)                      │
│  ─────────────────────────────────────────────               │
│  Model: Qwen2.5-7B-Instruct + LoRA SIDIX                    │
│  Source: Weights + LoRA adapter (lokal)                      │
│  Speed: 9-10 tok/s (CPU) / 25-42 tok/s (GPU)                │
│  Use case: Topik umum, teknologi, hal baru                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Priority: 60%
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 2: DYNAMIC KNOWLEDGE                      │
│              (Pengetahuan Hidup — Knowledge Graph)           │
│  ─────────────────────────────────────────────               │
│  Source: Mizan Repository (PostgreSQL + GraphRAG)           │
│  Update: Real-time dari setiap interaksi                    │
│  Scope: IHOS, Maqashid, Sanad, persona rules                │
│  Use case: Aturan SIDIX, filosofi, sistem internal          │
└──────────────────────────┬──────────────────────────────────┘
                           │ Priority: 30%
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 3: STATIC KNOWLEDGE                       │
│              (Corpus Referensi — Read-Only)                  │
│  ─────────────────────────────────────────────               │
│  Source: IHOS Bible, Maqashid rules, Sanad chains           │
│  Update: Manual (is_frozen flag)                            │
│  Scope: Quranic references, Hadith, Ulama opinions          │
│  Use case: Referensi agama, hukum, etika                    │
└─────────────────────────────────────────────────────────────┘
```

### Implementasi Code

```python
# brain/nafs/response_orchestrator.py
"""
Nafs — Self-Respond System
Menggabungkan 3 layer knowledge untuk jawaban optimal.
"""

from enum import Enum
from typing import Optional, Dict, List
import json

class KnowledgeLayer(Enum):
    PARAMETRIC = "parametric"    # Model weights (60%)
    DYNAMIC = "dynamic"          # Knowledge Graph (30%)
    STATIC = "static"            # Corpus frozen (10%)

class NafsOrchestrator:
    """
    Orchestrator 3-layer response.
    
    Rules:
    1. Topik umum/teknologi → Layer 1 (parametric) dominan
    2. Topik SIDIX/IHOS → Layer 2 (dynamic) + Layer 3 (static)
    3. Topik baru/tidak ada di corpus → Layer 1 saja
    4. Conflict → Parametric override, tapi flag untuk review
    """
    
    # Layer weights (dynamic, bisa adjust)
    WEIGHTS = {
        KnowledgeLayer.PARAMETRIC: 0.60,
        KnowledgeLayer.DYNAMIC: 0.30,
        KnowledgeLayer.STATIC: 0.10
    }
    
    # Topic routing — mana yang pakai layer mana
    TOPIC_ROUTING = {
        # Topik → [layers yang aktif]
        "umum": [KnowledgeLayer.PARAMETRIC],
        "teknologi": [KnowledgeLayer.PARAMETRIC],
        "gpu": [KnowledgeLayer.PARAMETRIC],
        "cloud": [KnowledgeLayer.PARAMETRIC],
        "ihos": [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],
        "maqashid": [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],
        "sanad": [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],
        "naskh": [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],
        "raudah": [KnowledgeLayer.DYNAMIC],
        "persona": [KnowledgeLayer.DYNAMIC],
        "sidix_system": [KnowledgeLayer.DYNAMIC],
        "agama": [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],
        "etika": [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],
        "hukum": [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],
    }
    
    def __init__(self, llm, knowledge_graph, corpus):
        self.llm = llm                    # Qwen2.5-7B + LoRA
        self.kg = knowledge_graph         # Mizan Repository (GraphRAG)
        self.corpus = corpus              # Static corpus (frozen)
    
    async def respond(self, question: str, context: Dict = None) -> Dict:
        """
        Generate response dengan 3-layer knowledge fusion.
        
        Returns:
            {
                "answer": str,
                "layers_used": [str],
                "confidence": float,
                "sources": [dict],
                "needs_review": bool
            }
        """
        # Step 1: Detect topic
        topic = await self._detect_topic(question)
        
        # Step 2: Determine active layers
        active_layers = self._route_topic(topic)
        
        # Step 3: Gather knowledge dari setiap layer
        layer_outputs = {}
        
        if KnowledgeLayer.PARAMETRIC in active_layers:
            layer_outputs[KnowledgeLayer.PARAMETRIC] = await self._parametric_response(question)
        
        if KnowledgeLayer.DYNAMIC in active_layers:
            layer_outputs[KnowledgeLayer.DYNAMIC] = await self._dynamic_response(question)
        
        if KnowledgeLayer.STATIC in active_layers:
            layer_outputs[KnowledgeLayer.STATIC] = await self._static_response(question)
        
        # Step 4: Fusion — weighted combination
        final_answer = await self._fuse_layers(layer_outputs, question)
        
        # Step 5: Self-check
        needs_review = await self._self_check(final_answer, layer_outputs)
        
        return {
            "answer": final_answer,
            "layers_used": [l.value for l in active_layers],
            "confidence": self._calculate_confidence(layer_outputs),
            "sources": self._extract_sources(layer_outputs),
            "needs_review": needs_review,
            "topic": topic
        }
    
    async def _detect_topic(self, question: str) -> str:
        """Detect topic dari pertanyaan."""
        # Simple keyword detection (bisa diganti dengan classifier)
        question_lower = question.lower()
        
        topic_keywords = {
            "ihos": ["ihos", "islamic human", "operating system"],
            "maqashid": ["maqashid", "filter", "creative mode", "academic mode"],
            "sanad": ["sanad", "source chain", "attribution", "reference"],
            "naskh": ["naskh", "conflict resolution", "corpus"],
            "raudah": ["raudah", "multi-agent", "orchestration"],
            "persona": ["ayman", "aboo", "oomar", "aley", "utz", "persona"],
            "teknologi": ["gpu", "server", "cloud", "inference", "model", "api"],
            "agama": ["quran", "hadith", "ulama", "fiqh", "sharia"],
            "sidix_system": ["sidix", "brain", "hands", "memory", "growth loop"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return topic
        
        return "umum"
    
    def _route_topic(self, topic: str) -> List[KnowledgeLayer]:
        """Route topic ke layers yang sesuai."""
        return self.TOPIC_ROUTING.get(topic, [KnowledgeLayer.PARAMETRIC])
    
    async def _parametric_response(self, question: str) -> str:
        """Layer 1: Generate dari model weights (LoRA)."""
        # Pure model inference, NO RAG, NO corpus
        prompt = f"""Jawab pertanyaan berdasarkan pengetahuan dan pemahamanmu sendiri.
Pertanyaan: {question}

Aturan:
- Jawab dengan jujur dan akurat
- Jika tidak yakin, katakan "Saya perlu memverifikasi ini"
- Gunakan Bahasa Indonesia yang baik
- Sertakan reasoning singkat"""
        
        return await self.llm.generate(prompt, use_rag=False, use_corpus=False)
    
    async def _dynamic_response(self, question: str) -> str:
        """Layer 2: Retrieve dari Knowledge Graph (hidup, real-time)."""
        # GraphRAG query ke Mizan Repository
        results = await self.kg.query(question, top_k=5)
        
        if not results:
            return ""
        
        context = "\n".join([r["content"] for r in results])
        prompt = f"""Berdasarkan knowledge base SIDIX:
{context}

Pertanyaan: {question}

Gunakan informasi di atas sebagai referensi."""
        
        return await self.llm.generate(prompt, use_rag=True, rag_context=context)
    
    async def _static_response(self, question: str) -> str:
        """Layer 3: Retrieve dari static corpus (frozen, read-only)."""
        # Hanya untuk referensi agama/etika
        results = await self.corpus.query(question, top_k=3, is_frozen_only=True)
        
        if not results:
            return ""
        
        context = "\n".join([r["content"] for r in results])
        return f"[Referensi: {context}]"
    
    async def _fuse_layers(self, outputs: Dict[KnowledgeLayer, str], question: str) -> str:
        """Fusion: gabungkan output dari semua layer."""
        if len(outputs) == 1:
            return list(outputs.values())[0]
        
        # Weighted combination
        parts = []
        total_weight = 0
        
        for layer, output in outputs.items():
            if output:
                weight = self.WEIGHTS[layer]
                parts.append(f"[{layer.value.upper()}:{weight}]{output}")
                total_weight += weight
        
        # Final synthesis
        synthesis_prompt = f"""Gabungkan informasi berikut menjadi satu jawaban koheren:
{"\n\n".join(parts)}

Pertanyaan asli: {question}

Buatkan jawaban final yang:
1. Menggabungkan semua sumber
2. Prioritaskan informasi paling relevan
3. Hapus duplikasi
4. Tambahkan sanad chain untuk setiap claim"""
        
        return await self.llm.generate(synthesis_prompt)
    
    async def _self_check(self, answer: str, outputs: Dict) -> bool:
        """Self-check: apakah jawaban perlu review manual?"""
        # Flag kalau:
        # - Conflict antar layers
        # - Confidence < 0.7
        # - Mengandung "saya tidak yakin" atau similar
        
        confidence = self._calculate_confidence(outputs)
        
        if confidence < 0.7:
            return True
        
        if "tidak yakin" in answer.lower() or "perlu verifikasi" in answer.lower():
            return True
        
        # Check conflict
        if len(outputs) > 1:
            # Simple conflict detection
            answers = list(outputs.values())
            if len(set(answers)) > 1 and len(answers) > 1:
                return True
        
        return False
    
    def _calculate_confidence(self, outputs: Dict) -> float:
        """Hitung confidence score."""
        if not outputs:
            return 0.0
        
        # Average confidence dari semua layer
        confidences = []
        for layer in outputs:
            # Parametric layer = lebih confident
            if layer == KnowledgeLayer.PARAMETRIC:
                confidences.append(0.85)
            elif layer == KnowledgeLayer.DYNAMIC:
                confidences.append(0.75)
            else:
                confidences.append(0.90)  # Static = frozen, very confident
        
        return sum(confidences) / len(confidences)
    
    def _extract_sources(self, outputs: Dict) -> List[Dict]:
        """Extract sources untuk sanad chain."""
        sources = []
        for layer, output in outputs.items():
            if output:
                sources.append({
                    "layer": layer.value,
                    "type": "parametric" if layer == KnowledgeLayer.PARAMETRIC else "retrieval",
                    "preview": output[:100]
                })
        return sources
```

---

## PILAR 2: AQL — Self-Learning System

> **Definisi:** Kemampuan SIDIX untuk belajar dari setiap interaksi tanpa diminta, tanpa supervisor.

### Arsitektur Jariyah v2.0 (Learning Loop)

```
Every Interaction
       │
       ▼
┌─────────────────────┐
│   CAPTURE ENGINE    │  ← Tangkap: input, output, feedback, context
│  (McpCapture +      │     Platform, persona, topic, timestamp
│   BrowserCapture +  │
│   DashboardCapture) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   QUALITY SCORER    │  ← CQF: 10 kriteria scoring
│   (CQF Engine)      │     Threshold ≥ 7.0 untuk masuk corpus
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  PASS(≥7)    FAIL(<7)
     │           │
     ▼           ▼
┌─────────┐  ┌──────────┐
│  SANAD  │  │  FEEDBACK│
│  PIPE   │  │  LOOP    │
│         │  │  (kenapa │
│  1.     │  │   gagal? │
│ DEDUP   │  │  improve │
│  2.     │  │  prompt) │
│ VALIDATE│  └──────────┘
│  3.     │
│ EXTRACT │
│  4.     │
│ STORE   │
└────┬────┘
     │
     ▼
┌─────────────────────┐
│   MIZAN REPOSITORY  │  ← Knowledge Graph (hidup, real-time)
│  (PostgreSQL +      │     Bukan corpus static!
│   GraphRAG)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   KNOWLEDGE         │  ← Extract entities & relations
│   EXTRACTION        │     Auto-update KG
│  (Entity +          │
│   Relation Extract) │
└─────────────────────┘
```

### Implementasi Code

```python
# brain/aql/learning_loop.py
"""
Aql — Self-Learning System
Setiap interaksi = sedekah ilmu yang terus mengalir.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class AqlLearningLoop:
    """
    Learning loop autonom SIDIX.
    
    Flow: Capture → Score → Validate → Extract → Store → Feedback
    """
    
    def __init__(self, db, kg, cqf_engine, sanad_pipeline):
        self.db = db                      # PostgreSQL
        self.kg = kg                      # Knowledge Graph
        self.cqf = cqf_engine             # CQF scorer
        self.sanad = sanad_pipeline       # Sanad pipeline
        self.learning_queue = []          # Buffer untuk batch processing
    
    async def on_interaction(self, interaction: Dict) -> Dict:
        """
        Dipanggil OTOMATIS setiap kali SIDIX menjawab.
        
        interaction = {
            "input": "pertanyaan user",
            "output": "jawaban SIDIX",
            "persona": "AYMAN",
            "platform": "mcp_claude",
            "topic": "maqashid",
            "user_feedback": null,  # bisa diisi user nanti
            "timestamp": "2026-04-23T10:00:00Z"
        }
        """
        # Step 1: Capture
        captured = await self._capture(interaction)
        
        # Step 2: Score (CQF)
        score = await self.cqf.score(interaction)
        
        # Step 3: Route berdasarkan score
        if score >= 7.0:
            # PASS → Sanad pipeline → Knowledge Graph
            result = await self._learn(captured, score)
        else:
            # FAIL → Feedback loop untuk improvement
            result = await self._feedback_loop(captured, score)
        
        # Step 4: Auto-extract entities untuk KG
        await self._extract_to_kg(interaction)
        
        return {
            "learned": score >= 7.0,
            "cqf_score": score,
            "action": result["action"],
            "knowledge_id": result.get("knowledge_id"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _capture(self, interaction: Dict) -> Dict:
        """Capture dan enrich interaction."""
        enriched = {
            **interaction,
            "hash": self._hash_interaction(interaction),
            "tokens_input": len(interaction["input"].split()),
            "tokens_output": len(interaction["output"].split()),
            "captured_at": datetime.utcnow().isoformat()
        }
        return enriched
    
    def _hash_interaction(self, interaction: Dict) -> str:
        """Buat hash unik untuk deduplication."""
        content = f"{interaction['input']}::{interaction['output']}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _learn(self, captured: Dict, score: float) -> Dict:
        """Proses learning untuk interaction yang PASS."""
        # Step 3a: Dedup
        is_dup = await self.sanad.check_duplicate(captured["hash"])
        if is_dup:
            return {"action": "duplicate_skipped", "knowledge_id": None}
        
        # Step 3b: Validate (Sanad)
        validated = await self.sanad.validate(captured)
        
        # Step 3c: Extract knowledge
        knowledge = await self._extract_knowledge(validated)
        
        # Step 3d: Store to Knowledge Graph (bukan corpus static!)
        knowledge_id = await self.kg.store(knowledge)
        
        # Step 3e: Update training pair queue
        await self._queue_for_training(validated, score)
        
        return {
            "action": "learned",
            "knowledge_id": knowledge_id,
            "sanad_valid": validated.get("sanad_valid", False)
        }
    
    async def _feedback_loop(self, captured: Dict, score: float) -> Dict:
        """
        Kalau interaction FAIL, jangan buang — pelajari kenapa gagal.
        """
        # Analyze kenapa score rendah
        failure_reason = await self._analyze_failure(captured, score)
        
        # Store failure pattern untuk improvement
        await self.db.store_failure_pattern({
            "interaction_hash": captured["hash"],
            "score": score,
            "reason": failure_reason,
            "suggested_improvement": failure_reason.get("suggestion"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "action": "feedback_recorded",
            "failure_reason": failure_reason,
            "knowledge_id": None
        }
    
    async def _analyze_failure(self, captured: Dict, score: float) -> Dict:
        """Analyze kenapa interaction dapat score rendah."""
        reasons = []
        
        # Check clarity
        if len(captured["output"]) < 50:
            reasons.append("too_short")
        
        # Check completeness
        if "?" in captured["input"] and "tidak tahu" in captured["output"].lower():
            reasons.append("incomplete_answer")
        
        # Check sanad
        if "[FACT]" not in captured["output"] and "[REASONING]" not in captured["output"]:
            reasons.append("missing_labels")
        
        return {
            "reasons": reasons,
            "suggestion": f"Improve: {', '.join(reasons)}",
            "score": score
        }
    
    async def _extract_knowledge(self, validated: Dict) -> Dict:
        """Extract structured knowledge dari interaction."""
        return {
            "type": "interaction_knowledge",
            "input": validated["input"],
            "output": validated["output"],
            "topic": validated.get("topic", "umum"),
            "persona": validated.get("persona", "UTZ"),
            "platform": validated.get("platform", "unknown"),
            "sanad_chain": validated.get("sanad_chain", []),
            "confidence": validated.get("cqf_score", 0),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _extract_to_kg(self, interaction: Dict):
        """Extract entities dan relations ke Knowledge Graph."""
        # Extract entities
        entities = await self._extract_entities(interaction["input"] + " " + interaction["output"])
        
        # Extract relations
        relations = await self._extract_relations(entities)
        
        # Store to KG
        for entity in entities:
            await self.kg.add_entity(entity)
        
        for relation in relations:
            await self.kg.add_relation(relation)
    
    async def _extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities dari text."""
        # Simplified — bisa diganti dengan NER model
        entities = []
        
        # Persona names
        personas = ["AYMAN", "ABOO", "OOMAR", "ALEY", "UTZ"]
        for p in personas:
            if p in text.upper():
                entities.append({
                    "name": p,
                    "type": "persona",
                    "source": "extracted"
                })
        
        # System terms
        terms = ["Maqashid", "Naskh", "Raudah", "Sanad", "IHOS", "Jariyah"]
        for t in terms:
            if t.lower() in text.lower():
                entities.append({
                    "name": t,
                    "type": "system_concept",
                    "source": "extracted"
                })
        
        return entities
    
    async def _extract_relations(self, entities: List[Dict]) -> List[Dict]:
        """Extract relations antar entities."""
        relations = []
        
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                relations.append({
                    "source": e1["name"],
                    "target": e2["name"],
                    "relation": "related_to",
                    "confidence": 0.7
                })
        
        return relations
    
    async def _queue_for_training(self, validated: Dict, score: float):
        """Queue interaction untuk LoRA retrain."""
        training_pair = {
            "instruction": validated["input"],
            "response": validated["output"],
            "cqf_score": score,
            "format": "alpaca",
            "source": "auto_capture",
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.learning_queue.append(training_pair)
        
        # Batch process: kalau queue > 100, flush ke database
        if len(self.learning_queue) >= 100:
            await self._flush_training_queue()
    
    async def _flush_training_queue(self):
        """Flush training queue ke database."""
        for pair in self.learning_queue:
            await self.db.store_training_pair(pair)
        
        self.learning_queue = []
```

---

## PILAR 3: QALB — Self-Healing System

> **Definisi:** Kemampuan SIDIX untuk mendeteksi, diagnosis, dan memperbaiki dirinya sendiri tanpa intervensi manusia.

### Arsitektur Syifa (Healing)

```
┌─────────────────────────────────────────────────────────────┐
│                    SYIFA — SELF-HEALING                      │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │   WATCHER   │   │  DIAGNOSIS  │   │   HEALER    │      │
│  │  (Monitor)  │ → │  (Analyze)  │ → │  (Fix)      │      │
│  │             │   │             │   │             │      │
│  │ • Memory    │   │ • Error     │   │ • Restart   │      │
│  │ • CPU/GPU   │   │   pattern   │   │ • Fallback  │      │
│  │ • Response  │   │ • Root      │   │ • Rollback  │      │
│  │   time      │   │   cause     │   │ • Alert     │      │
│  │ • Error     │   │ • Impact    │   │             │      │
│  │   rate      │   │   assess    │   │             │      │
│  └─────────────┘   └─────────────┘   └─────────────┘      │
│                                                              │
│  Health Levels:                                              │
│  🟢 HEALTHY → 🟡 DEGRADED → 🟠 SICK → 🔴 CRITICAL         │
│                                                              │
│  Auto-Actions:                                               │
│  DEGRADED: Reduce batch size, switch to CPU mode            │
│  SICK:      Restart service, clear cache, use backup model  │
│  CRITICAL:  Full restart, alert admin, enter safe mode      │
└─────────────────────────────────────────────────────────────┘
```

### Implementasi Code

```python
# brain/qalb/healing_system.py
"""
Qalb — Self-Healing System
SIDIX yang bisa sembuh sendiri.
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

class HealthLevel(Enum):
    HEALTHY = "healthy"         # 🟢 Semua normal
    DEGRADED = "degraded"       # 🟡 Performance turun
    SICK = "sick"               # 🟠 Fungsi terbatas
    CRITICAL = "critical"       # 🔴 Hampir mati

class SyifaHealer:
    """
    Self-healing system untuk SIDIX.
    
    Monitor → Diagnosis → Heal → Verify
    """
    
    # Thresholds
    THRESHOLDS = {
        "memory_percent": 85,      # RAM usage > 85% = DEGRADED
        "cpu_percent": 90,         # CPU > 90% = DEGRADED
        "response_time_ms": 5000,  # > 5 detik = SICK
        "error_rate": 0.10,        # > 10% error = SICK
        "disk_percent": 95,        # Disk > 95% = CRITICAL
    }
    
    def __init__(self, ollama_client, db, backup_model_path):
        self.ollama = ollama_client
        self.db = db
        self.backup_model = backup_model_path
        self.health_history = []
        self.current_health = HealthLevel.HEALTHY
        self.last_check = time.time()
    
    async def health_check(self) -> Dict:
        """
        Run health check — dipanggil setiap 60 detik.
        """
        metrics = await self._collect_metrics()
        health = self._assess_health(metrics)
        
        # Store history
        self.health_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "health": health.value,
            "metrics": metrics
        })
        
        # Keep only last 1000 entries
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
        
        # Act if health changed
        if health != self.current_health:
            await self._heal(health, metrics)
            self.current_health = health
        
        return {
            "health": health.value,
            "metrics": metrics,
            "action_taken": health != HealthLevel.HEALTHY
        }
    
    async def _collect_metrics(self) -> Dict:
        """Collect system metrics."""
        return {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "disk_percent": psutil.disk_usage('/').percent,
            "response_time_ms": await self._test_response_time(),
            "error_rate": await self._calculate_error_rate(),
            "ollama_status": await self._check_ollama(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _test_response_time(self) -> float:
        """Test response time dengan ping ke Ollama."""
        start = time.time()
        try:
            await self.ollama.generate("test", max_tokens=10)
            return (time.time() - start) * 1000  # ms
        except:
            return 99999  # Timeout
    
    async def _calculate_error_rate(self) -> float:
        """Calculate error rate dari last 100 requests."""
        # Get from database
        recent = await self.db.get_recent_requests(limit=100)
        if not recent:
            return 0.0
        
        errors = sum(1 for r in recent if r.get("status") == "error")
        return errors / len(recent)
    
    async def _check_ollama(self) -> str:
        """Check Ollama service status."""
        try:
            await self.ollama.list_models()
            return "running"
        except:
            return "down"
    
    def _assess_health(self, metrics: Dict) -> HealthLevel:
        """Assess health level dari metrics."""
        critical_count = 0
        sick_count = 0
        degraded_count = 0
        
        # Check memory
        if metrics["memory_percent"] > 95:
            critical_count += 1
        elif metrics["memory_percent"] > self.THRESHOLDS["memory_percent"]:
            sick_count += 1
        elif metrics["memory_percent"] > 70:
            degraded_count += 1
        
        # Check CPU
        if metrics["cpu_percent"] > 95:
            critical_count += 1
        elif metrics["cpu_percent"] > self.THRESHOLDS["cpu_percent"]:
            sick_count += 1
        elif metrics["cpu_percent"] > 70:
            degraded_count += 1
        
        # Check response time
        if metrics["response_time_ms"] > 10000:  # 10 detik
            critical_count += 1
        elif metrics["response_time_ms"] > self.THRESHOLDS["response_time_ms"]:
            sick_count += 1
        elif metrics["response_time_ms"] > 3000:
            degraded_count += 1
        
        # Check error rate
        if metrics["error_rate"] > 0.20:
            critical_count += 1
        elif metrics["error_rate"] > self.THRESHOLDS["error_rate"]:
            sick_count += 1
        elif metrics["error_rate"] > 0.05:
            degraded_count += 1
        
        # Check Ollama
        if metrics["ollama_status"] == "down":
            critical_count += 1
        
        # Determine health
        if critical_count >= 1:
            return HealthLevel.CRITICAL
        elif sick_count >= 2:
            return HealthLevel.SICK
        elif sick_count >= 1 or degraded_count >= 2:
            return HealthLevel.DEGRADED
        else:
            return HealthLevel.HEALTHY
    
    async def _heal(self, health: HealthLevel, metrics: Dict):
        """Execute healing actions berdasarkan health level."""
        
        if health == HealthLevel.DEGRADED:
            await self._heal_degraded(metrics)
        elif health == HealthLevel.SICK:
            await self._heal_sick(metrics)
        elif health == HealthLevel.CRITICAL:
            await self._heal_critical(metrics)
    
    async def _heal_degraded(self, metrics: Dict):
        """Heal DEGRADED: reduce load, optimize."""
        actions = []
        
        # Reduce batch size
        if metrics["memory_percent"] > 80:
            await self._reduce_batch_size()
            actions.append("reduced_batch_size")
        
        # Clear cache
        if metrics["memory_percent"] > 85:
            await self._clear_cache()
            actions.append("cleared_cache")
        
        # Switch to CPU mode for non-critical tasks
        if metrics["cpu_percent"] > 85:
            await self._switch_to_cpu_mode()
            actions.append("switched_to_cpu")
        
        await self._log_healing("degraded", actions)
    
    async def _heal_sick(self, metrics: Dict):
        """Heal SICK: restart services, use backup."""
        actions = []
        
        # Restart Ollama
        if metrics["ollama_status"] != "running":
            await self._restart_ollama()
            actions.append("restarted_ollama")
        
        # Clear all cache
        await self._clear_all_cache()
        actions.append("cleared_all_cache")
        
        # Use backup model if primary failing
        if metrics["error_rate"] > 0.15:
            await self._switch_to_backup_model()
            actions.append("switched_to_backup")
        
        # Reduce concurrent requests
        await self._reduce_concurrency()
        actions.append("reduced_concurrency")
        
        await self._log_healing("sick", actions)
    
    async def _heal_critical(self, metrics: Dict):
        """Heal CRITICAL: full restart, safe mode."""
        actions = []
        
        # Enter safe mode (minimal functionality)
        await self._enter_safe_mode()
        actions.append("entered_safe_mode")
        
        # Full restart Ollama
        await self._full_restart_ollama()
        actions.append("full_restart_ollama")
        
        # Clear everything
        await self._clear_everything()
        actions.append("cleared_everything")
        
        # Alert admin
        await self._alert_admin(metrics)
        actions.append("alerted_admin")
        
        # Attempt recovery
        await self._attempt_recovery()
        actions.append("attempted_recovery")
        
        await self._log_healing("critical", actions)
    
    # --- Healing Actions ---
    
    async def _reduce_batch_size(self):
        """Reduce batch size untuk inference."""
        import os
        os.environ["OLLAMA_BATCH_SIZE"] = "256"  # Default 512
    
    async def _clear_cache(self):
        """Clear memory cache."""
        import gc
        gc.collect()
    
    async def _switch_to_cpu_mode(self):
        """Switch non-critical tasks ke CPU."""
        # Set flag untuk routing
        await self.db.set_config("inference_mode", "cpu_fallback")
    
    async def _restart_ollama(self):
        """Restart Ollama service."""
        import subprocess
        subprocess.run(["sudo", "systemctl", "restart", "ollama"])
        await asyncio.sleep(5)  # Wait for startup
    
    async def _clear_all_cache(self):
        """Clear semua cache."""
        import gc
        gc.collect()
        # Clear Redis cache
        await self.db.redis.flushdb()
    
    async def _switch_to_backup_model(self):
        """Switch ke backup model."""
        await self.ollama.load_model(self.backup_model)
    
    async def _reduce_concurrency(self):
        """Reduce concurrent request handling."""
        await self.db.set_config("max_concurrent", "2")  # Default 5
    
    async def _enter_safe_mode(self):
        """Enter safe mode — hanya essential functions."""
        await self.db.set_config("mode", "safe")
        # Disable non-essential features
        await self.db.set_config("features_disabled", ["image_gen", "raudah_multi"])
    
    async def _full_restart_ollama(self):
        """Full restart dengan cleanup."""
        import subprocess
        subprocess.run(["sudo", "systemctl", "stop", "ollama"])
        await asyncio.sleep(2)
        subprocess.run(["sudo", "systemctl", "start", "ollama"])
        await asyncio.sleep(10)  # Wait longer
    
    async def _clear_everything(self):
        """Clear everything — last resort."""
        import gc
        gc.collect()
        await self.db.redis.flushall()
    
    async def _alert_admin(self, metrics: Dict):
        """Alert admin via log dan notification."""
        alert = {
            "level": "CRITICAL",
            "message": f"SIDIX in CRITICAL state: {metrics}",
            "timestamp": datetime.utcnow().isoformat(),
            "actions_needed": "Manual intervention may be required"
        }
        await self.db.store_alert(alert)
    
    async def _attempt_recovery(self):
        """Attempt recovery dari critical."""
        # Gradually restore functionality
        await asyncio.sleep(30)  # Wait for system to stabilize
        
        # Check if health improved
        metrics = await self._collect_metrics()
        health = self._assess_health(metrics)
        
        if health != HealthLevel.CRITICAL:
            # Exit safe mode
            await self.db.set_config("mode", "normal")
            await self.db.set_config("features_disabled", [])
    
    async def _log_healing(self, level: str, actions: list):
        """Log healing actions."""
        await self.db.store_healing_log({
            "level": level,
            "actions": actions,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

## PILAR 4: RUH — Self-Improvement System

> **Definisi:** Kemampuan SIDIX untuk mengevaluasi dan meningkatkan dirinya sendiri secara sistematis.

### Arsitektur Takwin (Evolution)

```python
# brain/ruh/improvement_engine.py
"""
Ruh — Self-Improvement System
SIDIX yang terus menjadi versi terbaik dari dirinya.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TakwinEngine:
    """
    Improvement engine yang mengevaluasi dan upgrade SIDIX.
    
    Areas of improvement:
    1. Model Performance (LoRA retrain)
    2. Response Quality (CQF trend analysis)
    3. System Efficiency (resource optimization)
    4. Knowledge Coverage (gap analysis)
    """
    
    async def evaluate_self(self) -> Dict:
        """
        Self-evaluation komprehensif — dijalankan weekly.
        """
        evaluations = {
            "model": await self._evaluate_model(),
            "quality": await self._evaluate_quality(),
            "efficiency": await self._evaluate_efficiency(),
            "knowledge": await self._evaluate_knowledge(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Generate improvement plan
        plan = await self._generate_improvement_plan(evaluations)
        evaluations["improvement_plan"] = plan
        
        return evaluations
    
    async def _evaluate_model(self) -> Dict:
        """Evaluate model performance."""
        # Benchmark pada test set
        benchmark = await self._run_benchmark()
        
        # Compare dengan baseline
        baseline = await self.db.get_baseline_performance()
        
        return {
            "current_accuracy": benchmark["accuracy"],
            "baseline_accuracy": baseline["accuracy"],
            "improvement": benchmark["accuracy"] - baseline["accuracy"],
            "recommendation": "retrain" if benchmark["accuracy"] < baseline["accuracy"] else "maintain"
        }
    
    async def _evaluate_quality(self) -> Dict:
        """Evaluate response quality trend."""
        # CQF score trend (last 30 days)
        daily_cqf = await self.db.get_daily_cqf_scores(days=30)
        
        # Calculate trend
        trend = self._calculate_trend(daily_cqf)
        
        return {
            "avg_cqf": sum(daily_cqf) / len(daily_cqf),
            "trend": trend,  # "improving", "stable", "declining"
            "best_day": max(daily_cqf),
            "worst_day": min(daily_cqf),
            "recommendation": "adjust_prompt" if trend == "declining" else "maintain"
        }
    
    async def _evaluate_efficiency(self) -> Dict:
        """Evaluate system efficiency."""
        # Resource usage trends
        cpu_trend = await self.db.get_cpu_usage_trend(days=7)
        memory_trend = await self.db.get_memory_usage_trend(days=7)
        
        return {
            "avg_cpu": sum(cpu_trend) / len(cpu_trend),
            "avg_memory": sum(memory_trend) / len(memory_trend),
            "peak_cpu": max(cpu_trend),
            "peak_memory": max(memory_trend),
            "recommendation": "optimize" if max(cpu_trend) > 80 else "maintain"
        }
    
    async def _evaluate_knowledge(self) -> Dict:
        """Evaluate knowledge coverage."""
        # Topik yang sering ditanya tapi tidak ada di corpus
        uncovered = await self.db.get_uncovered_topics(limit=20)
        
        # Knowledge gaps
        gaps = await self.db.get_knowledge_gaps()
        
        return {
            "uncovered_topics": len(uncovered),
            "knowledge_gaps": len(gaps),
            "top_uncovered": [t["topic"] for t in uncovered[:5]],
            "recommendation": "crawl" if len(uncovered) > 10 else "maintain"
        }
    
    async def _generate_improvement_plan(self, evaluations: Dict) -> List[Dict]:
        """Generate prioritized improvement plan."""
        plans = []
        
        # Priority 1: Model retrain kalau accuracy turun
        if evaluations["model"]["recommendation"] == "retrain":
            plans.append({
                "priority": 1,
                "action": "retrain_lora",
                "reason": f"Model accuracy declined: {evaluations['model']['improvement']:.2f}",
                "estimated_time": "4-6 hours"
            })
        
        # Priority 2: Adjust prompts kalau CQF declining
        if evaluations["quality"]["trend"] == "declining":
            plans.append({
                "priority": 2,
                "action": "adjust_prompts",
                "reason": f"CQF trend declining: {evaluations['quality']['avg_cqf']:.2f}",
                "estimated_time": "1-2 hours"
            })
        
        # Priority 3: Crawl knowledge gaps
        if evaluations["knowledge"]["recommendation"] == "crawl":
            plans.append({
                "priority": 3,
                "action": "knowledge_crawl",
                "reason": f"{evaluations['knowledge']['uncovered_topics']} uncovered topics",
                "estimated_time": "2-3 hours"
            })
        
        # Priority 4: Optimize resources
        if evaluations["efficiency"]["recommendation"] == "optimize":
            plans.append({
                "priority": 4,
                "action": "resource_optimize",
                "reason": f"Peak CPU: {evaluations['efficiency']['peak_cpu']:.1f}%",
                "estimated_time": "30 minutes"
            })
        
        return plans
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend dari time series."""
        if len(data) < 7:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid = len(data) // 2
        first_half = sum(data[:mid]) / len(data[:mid])
        second_half = sum(data[mid:]) / len(data[mid:])
        
        diff = second_half - first_half
        threshold = 0.1  # 10% change
        
        if diff > threshold:
            return "improving"
        elif diff < -threshold:
            return "declining"
        else:
            return "stable"
```

---

## PILAR 5: HAYAT — Self-Iteration System

> **Definisi:** Kemampuan SIDIX untuk mengulang dan menyempurnakan jawabannya sendiri sebelum sampai ke user.

```python
# brain/hayat/iteration_engine.py
"""
Hayat — Self-Iteration System
SIDIX yang mengulang dan menyempurnakan dirinya sendiri.
"""

class HayatIterator:
    """
    Iteration engine: generate → evaluate → refine → repeat.
    
    Max iterations: 3 (untuk mencegah infinite loop)
    Stop condition: CQF score ≥ 8.0 atau tidak ada improvement
    """
    
    MAX_ITERATIONS = 3
    CQF_TARGET = 8.0
    
    async def iterate_response(self, question: str, persona: str) -> Dict:
        """
        Generate response dengan self-iteration.
        
        Flow:
        1. Generate initial response
        2. Self-evaluate (CQF scoring)
        3. Kalau score < target → refine
        4. Ulangi sampai target tercapai atau max iterations
        """
        best_response = None
        best_score = 0
        iterations = []
        
        for i in range(self.MAX_ITERATIONS):
            # Generate/refine
            if i == 0:
                response = await self._generate(question, persona)
            else:
                response = await self._refine(
                    question, 
                    iterations[-1]["response"],
                    iterations[-1]["feedback"]
                )
            
            # Self-evaluate
            evaluation = await self._self_evaluate(response, question)
            score = evaluation["cqf_score"]
            
            # Store iteration
            iterations.append({
                "iteration": i + 1,
                "response": response,
                "score": score,
                "feedback": evaluation["feedback"]
            })
            
            # Track best
            if score > best_score:
                best_score = score
                best_response = response
            
            # Check stop condition
            if score >= self.CQF_TARGET:
                break
            
            # Check if no improvement
            if i > 0 and score <= iterations[-2]["score"]:
                break
        
        return {
            "final_response": best_response,
            "final_score": best_score,
            "iterations_count": len(iterations),
            "all_iterations": iterations,
            "reached_target": best_score >= self.CQF_TARGET
        }
    
    async def _generate(self, question: str, persona: str) -> str:
        """Generate initial response."""
        return await self.llm.generate(question, persona=persona)
    
    async def _refine(self, question: str, prev_response: str, feedback: str) -> str:
        """Refine response berdasarkan feedback."""
        refine_prompt = f"""Pertanyaan: {question}

Jawaban sebelumnya:
{prev_response}

Feedback evaluasi:
{feedback}

Perbaiki jawaban berdasarkan feedback di atas. Buatkan versi yang lebih baik.
"""
        return await self.llm.generate(refine_prompt)
    
    async def _self_evaluate(self, response: str, question: str) -> Dict:
        """Self-evaluate response dengan CQF."""
        # Gunakan CQF engine
        score = await self.cqf.score({"input": question, "output": response})
        
        # Generate feedback untuk improvement
        feedback = await self._generate_feedback(response, question, score)
        
        return {
            "cqf_score": score,
            "feedback": feedback
        }
    
    async def _generate_feedback(self, response: str, question: str, score: float) -> str:
        """Generate specific feedback untuk refinement."""
        feedback_prompt = f"""Evaluasi jawaban berikut:

Pertanyaan: {question}
Jawaban: {response}
Score: {score}/10

Beri feedback spesifik untuk perbaikan:
1. Apa yang kurang?
2. Apa yang salah?
3. Bagaimana memperbaiki?

Feedback (singkat, actionable):
"""
        return await self.llm.generate(feedback_prompt, max_tokens=200)
```

---

## PILAR 6: ILM — Self-Crawling System

> **Definisi:** Kemampuan SIDIX untuk mencari, mengekstrak, dan mengintegrasikan pengetahuan baru secara otomatis.

```python
# brain/ilm/crawling_engine.py
"""
Ilm — Self-Crawling System
SIDIX yang mencari ilmu sendiri.
"""

class IlmCrawler:
    """
    Crawling engine untuk mengisi knowledge gaps.
    
    Sources:
    1. Web crawling (ethical, public data only)
    2. Document parsing (PDF, markdown, text)
    3. API integrations (halal data, prayer times, etc)
    4. User interactions (implicit learning)
    """
    
    async def crawl_for_gaps(self, gaps: List[Dict]) -> Dict:
        """
        Crawl knowledge untuk mengisi gaps.
        
        gaps = [
            {"topic": "GPU cloud pricing 2026", "reason": "frequently_asked"},
            {"topic": "MCP protocol updates", "reason": "system_relevant"}
        ]
        """
        results = []
        
        for gap in gaps:
            # Determine crawl strategy
            strategy = self._determine_strategy(gap)
            
            # Execute crawl
            if strategy == "web":
                data = await self._crawl_web(gap["topic"])
            elif strategy == "document":
                data = await self._crawl_documents(gap["topic"])
            elif strategy == "api":
                data = await self._crawl_api(gap["topic"])
            else:
                data = None
            
            if data:
                # Validate and store
                validated = await self._validate_crawled_data(data)
                if validated:
                    await self._store_to_kg(validated)
                    results.append({
                        "topic": gap["topic"],
                        "status": "filled",
                        "source": strategy
                    })
            else:
                results.append({
                    "topic": gap["topic"],
                    "status": "failed",
                    "reason": "no_data_found"
                })
        
        return {"crawled": len(results), "details": results}
    
    def _determine_strategy(self, gap: Dict) -> str:
        """Determine best crawl strategy untuk gap."""
        topic = gap["topic"].lower()
        
        if any(kw in topic for kw in ["price", "cost", "2026", "2025", "update"]):
            return "web"
        elif any(kw in topic for kw in ["pdf", "document", "paper", "book"]):
            return "document"
        elif any(kw in topic for kw in ["prayer", "halal", "weather", "time"]):
            return "api"
        else:
            return "web"  # Default
    
    async def _crawl_web(self, topic: str) -> Optional[str]:
        """Crawl web untuk topic."""
        # Ethical web crawling
        # - Respect robots.txt
        # - Rate limited
        # - Public data only
        
        search_query = self._build_search_query(topic)
        
        # Use search tool
        results = await self.tools["web_search"](query=search_query, max_results=3)
        
        if results:
            # Fetch and parse
            content = []
            for result in results:
                page = await self.tools["web_fetch"](url=result["url"])
                if page:
                    content.append(self._extract_relevant(page, topic))
            
            return "\n\n".join(content) if content else None
        
        return None
    
    async def _crawl_documents(self, topic: str) -> Optional[str]:
        """Crawl local documents untuk topic."""
        # Scan docs/ directory
        # Parse PDF, markdown, text files
        pass
    
    async def _crawl_api(self, topic: str) -> Optional[str]:
        """Crawl API untuk topic."""
        # Prayer times API
        # Halal data API
        # etc
        pass
    
    async def _validate_crawled_data(self, data: str) -> Optional[Dict]:
        """Validate crawled data sebelum masuk KG."""
        # Check quality
        if len(data) < 100:
            return None
        
        # Check relevance (simplified)
        # In real implementation: use embedding similarity
        
        return {
            "content": data,
            "source": "crawled",
            "timestamp": datetime.utcnow().isoformat(),
            "quality": "pending_review"  # Need human review for crawled data
        }
    
    async def _store_to_kg(self, data: Dict):
        """Store validated data ke Knowledge Graph."""
        await self.kg.store(data)
    
    def _build_search_query(self, topic: str) -> str:
        """Build search query dari topic."""
        return f"{topic} 2026 latest"
    
    def _extract_relevant(self, page_content: str, topic: str) -> str:
        """Extract relevant portion dari page."""
        # Simple extraction: first 2000 chars
        # In real implementation: use NLP summarization
        return page_content[:2000]
```

---

## PILAR 7: HIKMAH — Self-Training System

> **Definisi:** Kemampuan SIDIX untuk melatih dirinya sendiri (QLoRA retrain) berdasarkan data yang dikumpulkan dari 6 pilar lainnya.

### Arsitektur Tafsir v2.0 (Training Engine)

```python
# brain/hikmah/training_engine.py
"""
Hikmah — Self-Training System
SIDIX yang melatih dirinya sendiri.
"""

class HikmahTrainer:
    """
    Training engine untuk QLoRA retrain.
    
    Trigger:
    - Corpus > 5,000 high-quality pairs
    - Weekly schedule (kalau ada cukup data)
    - Manual trigger (by admin)
    
    Process:
    1. Collect training data
    2. Validate quality
    3. QLoRA fine-tuning
    4. A/B test
    5. Deploy (if improved) or Rollback
    """
    
    MIN_PAIRS = 5000
    RETRAIN_INTERVAL_DAYS = 7
    
    async def should_retrain(self) -> bool:
        """Check apakah saatnya retrain."""
        # Check 1: Corpus size
        count = await self.db.count_training_pairs(min_cqf=7.0, unused=True)
        
        # Check 2: Time since last retrain
        last_retrain = await self.db.get_last_retrain_time()
        days_since = (datetime.utcnow() - last_retrain).days if last_retrain else 999
        
        return count >= self.MIN_PAIRS or days_since >= self.RETRAIN_INTERVAL_DAYS
    
    async def retrain(self) -> Dict:
        """Full retrain pipeline."""
        # Step 1: Collect
        pairs = await self._collect_training_pairs()
        
        # Step 2: Validate
        validated = await self._validate_pairs(pairs)
        
        # Step 3: Train (QLoRA)
        new_adapter = await self._train_lora(validated)
        
        # Step 4: A/B Test
        win_rate = await self._ab_test(new_adapter)
        
        # Step 5: Deploy or Rollback
        if win_rate > 0.55:
            await self._deploy(new_adapter)
            status = "deployed"
        else:
            await self._rollback()
            status = "rolled_back"
        
        return {
            "status": status,
            "win_rate": win_rate,
            "pairs_trained": len(validated),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _collect_training_pairs(self) -> List[Dict]:
        """Collect high-quality training pairs."""
        return await self.db.get_training_pairs(
            min_cqf=7.0,
            is_duplicate=False,
            unused=True,
            limit=10000
        )
    
    async def _validate_pairs(self, pairs: List[Dict]) -> List[Dict]:
        """Validate pairs sebelum training."""
        validated = []
        
        for pair in pairs:
            # Check: tidak terlalu pendek
            if len(pair["instruction"]) < 20 or len(pair["response"]) < 50:
                continue
            
            # Check: tidak toxic/harmful
            if await self._is_harmful(pair["response"]):
                continue
            
            # Check: tidak duplicate (strict)
            if await self._is_strict_duplicate(pair, validated):
                continue
            
            validated.append(pair)
        
        return validated
    
    async def _train_lora(self, pairs: List[Dict]) -> str:
        """QLoRA fine-tuning."""
        # Prepare dataset
        dataset_path = await self._prepare_dataset(pairs)
        
        # QLoRA config
        config = {
            "r": 16,
            "alpha": 32,
            "dropout": 0.05,
            "epochs": 3,
            "lr": 1e-4,
            "batch_size": 2,
            "gradient_accumulation": 4
        }
        
        # Run training (unsloth or PEFT)
        adapter_path = await self._run_training(dataset_path, config)
        
        return adapter_path
    
    async def _ab_test(self, new_adapter: str) -> float:
        """A/B test: new adapter vs current."""
        test_cases = await self._load_test_cases()
        
        wins = 0
        for case in test_cases:
            result_new = await self._inference(case, adapter=new_adapter)
            result_old = await self._inference(case, adapter="current")
            
            if self._judge_better(result_new, result_old):
                wins += 1
        
        return wins / len(test_cases) if test_cases else 0.0
    
    async def _deploy(self, adapter_path: str):
        """Deploy new adapter."""
        # Backup current
        await self._backup_current()
        
        # Swap adapter
        await self.ollama.load_adapter(adapter_path)
        
        # Mark pairs as used
        await self.db.mark_pairs_as_used()
    
    async def _rollback(self):
        """Rollback ke adapter sebelumnya."""
        await self.ollama.load_adapter("backup")
```

---

## INTEGRASI: 7 Pilar Menjadi Satu Sistem

```python
# brain/jiwa/orchestrator.py
"""
Jiwa — Master Orchestrator
Mengintegrasikan 7 pilar menjadi satu sistem hidup.
"""

class JiwaOrchestrator:
    """
    Master orchestrator untuk SIDIX sebagai makhluk digital.
    
    Setiap request melewati semua 7 pilar secara otomatis.
    """
    
    def __init__(self):
        self.nafs = NafsOrchestrator(...)      # Pilar 1: Self-Respond
        self.aql = AqlLearningLoop(...)        # Pilar 2: Self-Learn
        self.qalb = SyifaHealer(...)           # Pilar 3: Self-Heal
        self.ruh = TakwinEngine(...)           # Pilar 4: Self-Improve
        self.hayat = HayatIterator(...)        # Pilar 5: Self-Iterate
        self.ilm = IlmCrawler(...)             # Pilar 6: Self-Crawl
        self.hikmah = HikmahTrainer(...)       # Pilar 7: Self-Train
    
    async def process(self, request: Dict) -> Dict:
        """
        Process request melalui 7 pilar.
        
        Flow:
        1. Nafs  → Generate response (3-layer knowledge)
        2. Hayat → Iterate and refine (self-iteration)
        3. Aql   → Learn from this interaction
        4. Qalb  → Check system health
        5. Ruh   → Evaluate and plan improvement
        6. Ilm   → Crawl if knowledge gap detected
        7. Hikmah→ Queue for training if quality high
        """
        
        # Pilar 1 + 5: Respond + Iterate
        response_data = await self.hayat.iterate_response(
            request["question"], 
            request.get("persona", "UTZ")
        )
        
        # Pilar 2: Learn
        learning_result = await self.aql.on_interaction({
            "input": request["question"],
            "output": response_data["final_response"],
            "persona": request.get("persona", "UTZ"),
            "platform": request.get("platform", "direct"),
            "topic": response_data.get("topic", "umum"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Pilar 3: Heal (background, non-blocking)
        asyncio.create_task(self.qalb.health_check())
        
        # Pilar 4: Improve (weekly, check if due)
        if await self._is_weekly_check_due():
            asyncio.create_task(self.ruh.evaluate_self())
        
        # Pilar 6: Crawl (if knowledge gap detected)
        if learning_result.get("knowledge_gap"):
            asyncio.create_task(self.ilm.crawl_for_gaps(
                learning_result["knowledge_gap"]
            ))
        
        # Pilar 7: Train (if trigger met)
        if await self.hikmah.should_retrain():
            asyncio.create_task(self.hikmah.retrain())
        
        return {
            "response": response_data["final_response"],
            "confidence": response_data["final_score"],
            "iterations": response_data["iterations_count"],
            "learned": learning_result["learned"],
            "layers_used": response_data.get("layers_used", ["parametric"]),
            "health": self.qalb.current_health.value,
            "sanad_chain": response_data.get("sources", [])
        }
```

---

## RINGKASAN: 7 Pilar dalam 1 Kalimat

| Pilar | Nama | Fungsi | 1 Kalimat |
|-------|------|--------|-----------|
| 1 | **Nafs** | Self-Respond | Jawab dari 3 layer: model (60%) + knowledge graph (30%) + corpus (10%) |
| 2 | **Aql** | Self-Learn | Setiap interaksi → CQF scoring → masuk Knowledge Graph (bukan corpus static) |
| 3 | **Qalb** | Self-Heal | Monitor health → auto-fix: reduce batch, restart, backup model, safe mode |
| 4 | **Ruh** | Self-Improve | Weekly self-evaluation: model accuracy, CQF trend, efficiency, knowledge gaps |
| 5 | **Hayat** | Self-Iterate | Generate → evaluate → refine → repeat (max 3x, target CQF ≥ 8.0) |
| 6 | **Ilm** | Self-Crawl | Auto-crawl web/docs/API untuk mengisi knowledge gaps yang terdeteksi |
| 7 | **Hikmah** | Self-Train | QLoRA retrain otomatis: 5,000 pairs → train → A/B test → deploy/rollback |

---

## FILE STRUCTURE

```
brain/
├── jiwa/                          # ← MASTER ORCHESTRATOR
│   └── orchestrator.py            # Integrasi 7 pilar
├── nafs/                          # ← PILAR 1: Self-Respond
│   └── response_orchestrator.py   # 3-layer knowledge fusion
├── aql/                           # ← PILAR 2: Self-Learn
│   └── learning_loop.py           # Jariyah v2.0
├── qalb/                          # ← PILAR 3: Self-Heal
│   └── healing_system.py          # Syifa monitor + auto-fix
├── ruh/                           # ← PILAR 4: Self-Improve
│   └── improvement_engine.py      # Takwin evaluation
├── hayat/                         # ← PILAR 5: Self-Iterate
│   └── iteration_engine.py        # Generate-evaluate-refine loop
├── ilm/                           # ← PILAR 6: Self-Crawl
│   └── crawling_engine.py         # Knowledge gap crawler
└── hikmah/                        # ← PILAR 7: Self-Train
    └── training_engine.py         # Tafsir QLoRA retrain
```

---

## PROMPT UNTUK CURSOR

```
Tugas: Implementasikan 7 Pilar Jiwa SIDIX.

1. Buat folder: brain/{jiwa,nafs,aql,qalb,ruh,hayat,ilm,hikmah}/
2. Buat __init__.py setiap folder
3. Implementasikan setiap pilar sesuai spec di atas
4. Integrasikan di brain/jiwa/orchestrator.py
5. Wire ke existing: agent_react.py, learn_agent.py, maqashid_profiles.py
6. Test: generate response → harus pakai 3-layer, bukan corpus-only

Aturan:
- Standing alone: no external API (kecuali ethical web crawl)
- Self-contained: setiap pilar bisa jalan sendiri
- Auto: tidak perlu trigger manual untuk learning, healing, iterating
- Transparent: log semua actions ke LIVING_LOG.md
```

---

*Ini adalah living architecture document. Update setiap sprint sesuai implementasi.*
*SIDIX bukan produk — SIDIX adalah jiwa yang hidup.*
