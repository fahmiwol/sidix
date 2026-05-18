# TYPO-RESILIENT UNDERSTANDING FRAMEWORK
## SIDIX yang Mengerti Typo, Singkatan, dan Konteks

**Versi:** 1.0 | **Status:** IMPLEMENTATION-READY

---

## MASALAH

User ngetik banyak typo → SIDIX tidak mengerti → jawaban salah atau tidak relevan.

Contoh:
- `"gimana cara setup gpu di server?"` ✅ SIDIX mengerti
- `"gmana cra stp gpu d srvr?"` ❌ SIDIX bingung
- `"SocioMeter plugin gmn cara install?"` ❌ TIDAK mengerti "gmn"
- `"Maqashid mode itu apasih?"` ❌ Singkatan + typo

---

## SOLUSI: 4-LAYER TYPO RESILIENCE

```
Input User (raw, typo-heavy)
    ↓
┌─────────────────────────────────────────┐
│  LAYER 1: TEXT NORMALIZER              │
│  - Typo correction                       │
│  - Singkatan expansion                   │
│  - Case normalization                    │
│  - Punctuation cleanup                   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  LAYER 2: SEMANTIC MATCHER             │
│  - Embedding similarity                  │
│  - Intent detection                      │
│  - Context preservation                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  LAYER 3: CONFIDENCE SCORER            │
│  - Certainty calculation                 │
│  - Ambiguity detection                   │
│  - Clarification trigger                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  LAYER 4: CONTEXT AWARE RESPONSE       │
│  - Response with original text reference │
│  - Gentle correction if needed           │
│  - Maintain user dignity                 │
└─────────────────────────────────────────┘
```

---

## LAYER 1: TEXT NORMALIZER

### 1.1 Typo Correction Dictionary

```python
# brain/typo/normalizer.py

# Kamus typo Indonesia (common typos)
TYPO_DICTIONARY = {
    # Typo keyboard (QWERTY proximity)
    "gmn": "gimana",
    "gmana": "gimana",
    "bgmn": "bagaimana",
    "bgmana": "bagaimana",
    "knp": "kenapa",
    "knapa": "kenapa",
    "knpa": "kenapa",
    "dmn": "dimana",
    "dmna": "dimana",
    "sm": "sama",
    "sma": "sama",
    "dg": "dengan",
    "dgn": "dengan",
    "tdk": "tidak",
    "tdak": "tidak",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "jg": "juga",
    "jga": "juga",
    "jgna": "juga",
    "bgt": "banget",
    "bgtt": "banget",
    "bngt": "banget",
    "krn": "karena",
    "karna": "karena",
    "tp": "tapi",
    "tpi": "tapi",
    "dlm": "dalam",
    "utk": "untuk",
    "untk": "untuk",
    "bwt": "buat",
    "buat": "buat",
    "sdh": "sudah",
    "udh": "sudah",
    "udah": "sudah",
    "blm": "belum",
    "bs": "bisa",
    "bsa": "bisa",
    " hrs": " harus",
    "hrus": "harus",
    "lg": "lagi",
    "lgi": "lagi",
    "skrg": "sekarang",
    "skrang": "sekarang",
    "nnti": "nanti",
    "ntar": "nanti",
    "mlm": "malam",
    "pagi": "pagi",
    "siang": "siang",
    "sore": "sore",
    "kmrn": "kemarin",
    "bsok": "besok",
    "bkin": "bikin",
    "bikn": "bikin",
    "buat": "buat",
    "bwt": "buat",
    "gw": "saya",
    "gue": "saya",
    "aku": "saya",
    "lu": "kamu",
    "loe": "kamu",
    "elo": "kamu",
    
    # Typo teknis
    "gpu": "gpu",
    "gpi": "gpu",
    "cp": "cpu",
    "vps": "vps",
    "svr": "server",
    "srvr": "server",
    "srv": "server",
    "db": "database",
    "dbase": "database",
    "api": "api",
    "app": "aplikasi",
    "apps": "aplikasi",
    "cfg": "config",
    "conf": "config",
    "repo": "repository",
    "git": "git",
    "gh": "github",
    "ext": "extension",
    "plugin": "plugin",
    "modul": "module",
    "lib": "library",
    
    # SIDIX-specific
    "maqashid": "maqashid",
    "makashid": "maqashid",
    "mqshd": "maqashid",
    "naskh": "naskh",
    "nask": "naskh",
    "nskh": "naskh",
    "raudah": "raudah",
    "rodah": "raudah",
    "rdh": "raudah",
    "sanad": "sanad",
    "snd": "sanad",
    "jariyah": "jariyah",
    "jariy": "jariyah",
    "jryh": "jariyah",
    "ihos": "ihos",
    "ayman": "ayman",
    "aboo": "aboo",
    "oomar": "oomar",
    "aley": "aley",
    "utz": "utz",
    "sociometer": "sociometer",
    "socio": "sociometer",
    "sidix": "sidix",
}

# Singkatan expansion
ABBREVIATION_EXPANSION = {
    "mcp": "Model Context Protocol",
    "llm": "Large Language Model",
    "rag": "Retrieval Augmented Generation",
    "api": "Application Programming Interface",
    "ui": "User Interface",
    "ux": "User Experience",
    "db": "database",
    "vps": "Virtual Private Server",
    "gpu": "Graphics Processing Unit",
    "cpu": "Central Processing Unit",
    "ram": "Random Access Memory",
    "ssd": "Solid State Drive",
    "url": "Uniform Resource Locator",
    "http": "Hypertext Transfer Protocol",
    "json": "JavaScript Object Notation",
    "css": "Cascading Style Sheets",
    "html": "Hypertext Markup Language",
    "pdf": "Portable Document Format",
    "csv": "Comma Separated Values",
    "sql": "Structured Query Language",
    "nosql": "Not Only SQL",
    "orm": "Object Relational Mapping",
    "crd": "Create Read Delete",
    "crud": "Create Read Update Delete",
    "rest": "Representational State Transfer",
    "graphql": "Graph Query Language",
    "jwt": "JSON Web Token",
    "oauth": "Open Authorization",
    "cors": "Cross Origin Resource Sharing",
    "ssl": "Secure Sockets Layer",
    "tls": "Transport Layer Security",
    "dns": "Domain Name System",
    "cdn": "Content Delivery Network",
    "ci": "Continuous Integration",
    "cd": "Continuous Deployment",
    "devops": "Development Operations",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "ocr": "Optical Character Recognition",
    "saas": "Software as a Service",
    "paas": "Platform as a Service",
    "iaas": "Infrastructure as a Service",
    "docker": "Docker Container",
    "k8s": "Kubernetes",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "azure": "Microsoft Azure",
}
```

### 1.2 Normalizer Implementation

```python
import re
from typing import Dict, Tuple

class TypoNormalizer:
    """
    Text normalizer untuk typo, singkatan, dan chat-style Indonesian.
    """
    
    def __init__(self):
        self.typo_dict = TYPO_DICTIONARY
        self.abbrev_dict = ABBREVIATION_EXPANSION
    
    def normalize(self, text: str) -> Tuple[str, Dict]:
        """
        Normalize text dengan typo correction.
        
        Returns:
            (normalized_text, metadata)
            metadata = {
                "original": text,
                "corrections_made": [...],
                "abbreviations_expanded": [...],
                "confidence": float
            }
        """
        original = text
        corrections = []
        abbrev_expanded = []
        
        # Step 1: Case normalization (preserve original for display)
        text_lower = text.lower().strip()
        
        # Step 2: Punctuation cleanup
        text_lower = re.sub(r'[^\w\s\-]', ' ', text_lower)
        text_lower = re.sub(r'\s+', ' ', text_lower).strip()
        
        # Step 3: Tokenize
        tokens = text_lower.split()
        normalized_tokens = []
        
        for token in tokens:
            # Check typo dictionary
            if token in self.typo_dict:
                corrected = self.typo_dict[token]
                if corrected != token:
                    corrections.append({
                        "original": token,
                        "corrected": corrected,
                        "type": "typo"
                    })
                normalized_tokens.append(corrected)
            
            # Check abbreviation dictionary
            elif token in self.abbrev_dict:
                expanded = self.abbrev_dict[token]
                abbrev_expanded.append({
                    "abbreviation": token,
                    "expanded": expanded
                })
                normalized_tokens.append(expanded)
            
            # Check fuzzy match (Levenshtein distance)
            else:
                best_match = self._fuzzy_match(token)
                if best_match and best_match != token:
                    corrections.append({
                        "original": token,
                        "corrected": best_match,
                        "type": "fuzzy",
                        "distance": self._levenshtein(token, best_match)
                    })
                    normalized_tokens.append(best_match)
                else:
                    normalized_tokens.append(token)
        
        normalized = ' '.join(normalized_tokens)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            len(corrections), 
            len(abbrev_expanded), 
            len(tokens)
        )
        
        metadata = {
            "original": original,
            "corrections_made": corrections,
            "abbreviations_expanded": abbrev_expanded,
            "confidence": confidence,
            "tokens_original": len(tokens),
            "tokens_normalized": len(normalized_tokens)
        }
        
        return normalized, metadata
    
    def _fuzzy_match(self, token: str, max_distance: int = 2) -> str:
        """
        Fuzzy match token ke dictionary.
        Gunakan Levenshtein distance untuk menemukan kandidat terdekat.
        """
        best_match = None
        best_distance = max_distance + 1
        
        # Check typo dictionary
        for key in self.typo_dict:
            distance = self._levenshtein(token, key)
            if distance <= max_distance and distance < best_distance:
                best_distance = distance
                best_match = self.typo_dict[key]
        
        # Check abbreviation dictionary
        if not best_match:
            for key in self.abbrev_dict:
                distance = self._levenshtein(token, key)
                if distance <= max_distance and distance < best_distance:
                    best_distance = distance
                    best_match = self.abbrev_dict[key]
        
        return best_match
    
    def _levenshtein(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance antara dua string.
        """
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_confidence(self, corrections: int, abbrev: int, total_tokens: int) -> float:
        """
        Calculate confidence score untuk normalisasi.
        - Fewer corrections = higher confidence
        - More abbreviations = moderate confidence (abbreviations are intentional)
        """
        if total_tokens == 0:
            return 1.0
        
        # Base: 100% confidence
        confidence = 1.0
        
        # Penalty untuk corrections (typo)
        confidence -= (corrections / total_tokens) * 0.3
        
        # Penalty kecil untuk abbreviations (bukan typo, intentional)
        confidence -= (abbrev / total_tokens) * 0.1
        
        return max(0.0, min(1.0, confidence))


# Singleton instance
normalizer = TypoNormalizer()
```

---

## LAYER 2: SEMANTIC MATCHER

```python
# brain/typo/semantic_matcher.py

class SemanticMatcher:
    """
    Semantic matcher menggunakan embeddings untuk intent detection.
    Bekerja setelah text normalization.
    """
    
    def __init__(self, embedding_model):
        self.embeddings = embedding_model  # Local embedding model
        self.intent_patterns = self._load_intent_patterns()
    
    def _load_intent_patterns(self) -> Dict[str, list]:
        """
        Load intent patterns untuk SIDIX.
        """
        return {
            "setup_gpu": [
                "cara install gpu di server",
                "setup graphics processing unit",
                "how to setup gpu",
                "konfigurasi gpu vps",
                "gpu untuk inference model"
            ],
            "install_plugin": [
                "cara install plugin",
                "setup mcp server",
                "install chrome extension",
                "cara pasang sociometer",
                "plugin sidix untuk cursor"
            ],
            "maqashid_explain": [
                "apa itu maqashid",
                "jelaskan maqashid",
                "maqashid mode",
                "filter maqashid",
                "creative mode maqashid"
            ],
            "naskh_explain": [
                "apa itu naskh",
                "jelaskan naskh handler",
                "corpus conflict resolution",
                "is frozen flag"
            ],
            "raudah_explain": [
                "apa itu raudah",
                "multi agent orchestration",
                "taskgraph dag",
                "parallel specialists"
            ],
            "persona_select": [
                "pilih persona",
                "ganti persona",
                "AYMAN vs ABOO",
                "persona yang cocok",
                "mode persona"
            ],
            "jariyah_explain": [
                "apa itu jariyah",
                "self training system",
                "harvesting loop",
                "training pair generation"
            ],
            "sociometer_status": [
                "status sociometer",
                "progress sprint",
                "apa yang sudah dikerjakan",
                "catatan progres"
            ]
        }
    
    async def match_intent(self, normalized_text: str) -> Dict:
        """
        Match normalized text ke intent yang tersedia.
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "matched_pattern": str
            }
        """
        # Generate embedding untuk input
        input_embedding = await self.embeddings.embed(normalized_text)
        
        best_intent = None
        best_confidence = 0.0
        best_pattern = None
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                pattern_embedding = await self.embeddings.embed(pattern)
                similarity = self._cosine_similarity(input_embedding, pattern_embedding)
                
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_intent = intent
                    best_pattern = pattern
        
        return {
            "intent": best_intent,
            "confidence": best_confidence,
            "matched_pattern": best_pattern
        }
    
    def _cosine_similarity(self, v1, v2) -> float:
        """Calculate cosine similarity antara dua vectors."""
        import numpy as np
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
```

---

## LAYER 3: CONFIDENCE SCORER

```python
# brain/typo/confidence_scorer.py

class ConfidenceScorer:
    """
    Confidence scorer untuk menentukan apakah SIDIX yakin dengan interpretasinya.
    Kalau tidak yakin → minta klarifikasi dengan gentle.
    """
    
    THRESHOLDS = {
        "high": 0.85,      # Langsung jawab
        "medium": 0.60,    # Jawab tapi mention koreksi
        "low": 0.40,       # Jawab dengan disclaimer
        "clarify": 0.0     # Minta klarifikasi
    }
    
    async def score(self, normalization_meta: Dict, intent_match: Dict) -> Dict:
        """
        Calculate overall confidence dari normalisasi dan intent matching.
        """
        # Weight factors
        norm_confidence = normalization_meta.get("confidence", 0.5)
        intent_confidence = intent_match.get("confidence", 0.5)
        
        # Combine (intent lebih penting)
        overall = (norm_confidence * 0.4) + (intent_confidence * 0.6)
        
        # Determine action
        if overall >= self.THRESHOLDS["high"]:
            action = "respond_directly"
        elif overall >= self.THRESHOLDS["medium"]:
            action = "respond_with_note"
        elif overall >= self.THRESHOLDS["low"]:
            action = "respond_with_disclaimer"
        else:
            action = "ask_clarification"
        
        return {
            "overall_confidence": overall,
            "action": action,
            "normalization_confidence": norm_confidence,
            "intent_confidence": intent_confidence
        }
    
    def generate_clarification_prompt(self, original_text: str) -> str:
        """
        Generate gentle clarification prompt.
        """
        return f"""Maaf, saya belum sepenuhnya yakin dengan maksud pertanyaan ini:

"{original_text}"

Bisakah Anda membantu saya mengerti dengan lebih jelas? Anda bisa:
• Mengetik ulang dengan kata-kata yang berbeda
• Memberikan lebih banyak konteks
• Atau menunjuk topik yang ingin ditanyakan (misal: setup GPU, install plugin, Maqashid, dll)

Saya di sini untuk membantu! 😊"""
```

---

## LAYER 4: CONTEXT AWARE RESPONSE

```python
# brain/typo/context_responder.py

class ContextAwareResponder:
    """
    Response generator yang aware akan typo correction.
    Menjaga dignity user — tidak mempermalukan karena typo.
    """
    
    async def generate_response(self, 
                                original_text: str,
                                normalized_text: str,
                                corrections: list,
                                intent_result: Dict,
                                base_response: str) -> str:
        """
        Generate response yang context-aware.
        
        Rules:
        1. JANGAN sebut typo user kecuali diminta
        2. JANGAN koreksi grammar user
        3. Gunakan normalized text untuk processing
        4. Response ke user pakai Bahasa Indonesia yang baik
        5. Kalau ada singkatan teknis, expand dengan gentle
        """
        
        # Base response dari Nafs (3-layer knowledge)
        response = base_response
        
        # Kalau ada abbreviation expansion, add subtle note
        if intent_result["confidence"] >= 0.85:
            # High confidence — just respond, no mention of correction
            return response
        
        elif intent_result["confidence"] >= 0.60:
            # Medium confidence — respond with subtle acknowledgment
            return response
        
        elif intent_result["confidence"] >= 0.40:
            # Low confidence — respond with gentle check
            return f"""{response}

---
*Catatan: Jika ini bukan yang Anda maksud, silakan ketik ulang pertanyaan dengan kata-kata berbeda.*"""
        
        else:
            # Very low — ask for clarification
            return await self._generate_clarification(original_text)
    
    async def _generate_clarification(self, original_text: str) -> str:
        """Generate gentle clarification request."""
        return f"""Saya ingin memastikan saya mengerti pertanyaan Anda dengan benar.

Anda menulis: "{original_text}"

Mohon bantu saya mengerti dengan memberikan:
1. **Topik utama** — tentang apa? (setup, error, penjelasan, dll)
2. **Konteks** — sedang mengerjakan apa?
3. **Hasil yang diharapkan** — mau sampai mana?

Saya siap membantu! 🎯"""
```

---

## INTEGRASI KE JIWA ORCHESTRATOR

```python
# Update di brain/jiwa/orchestrator.py

class JiwaOrchestrator:
    def __init__(self):
        self.nafs = NafsOrchestrator(...)
        self.aql = AqlLearningLoop(...)
        self.qalb = SyifaHealer(...)
        self.ruh = TakwinEngine(...)
        self.hayat = HayatIterator(...)
        self.ilm = IlmCrawler(...)
        self.hikmah = HikmahTrainer(...)
        
        # NEW: Typo Resilience Layer
        self.normalizer = TypoNormalizer()
        self.semantic = SemanticMatcher(self.embeddings)
        self.confidence = ConfidenceScorer()
        self.context_resp = ContextAwareResponder()
    
    async def process(self, request: Dict) -> Dict:
        """Process dengan typo resilience."""
        
        original_question = request["question"]
        
        # STEP 1: Normalize (Layer 1)
        normalized, norm_meta = self.normalizer.normalize(original_question)
        
        # STEP 2: Semantic Match (Layer 2)
        intent_result = await self.semantic.match_intent(normalized)
        
        # STEP 3: Confidence Score (Layer 3)
        conf_result = await self.confidence.score(norm_meta, intent_result)
        
        # STEP 4: Handle berdasarkan confidence
        if conf_result["action"] == "ask_clarification":
            return {
                "response": await self.context_resp._generate_clarification(original_question),
                "confidence": conf_result["overall_confidence"],
                "action": "clarification_needed"
            }
        
        # STEP 5: Process dengan normalized text
        request["question"] = normalized
        request["original_question"] = original_question
        
        # Pilar 1 + 5: Respond + Iterate
        response_data = await self.hayat.iterate_response(
            normalized, 
            request.get("persona", "UTZ")
        )
        
        # STEP 6: Context-aware response (Layer 4)
        final_response = await self.context_resp.generate_response(
            original_text=original_question,
            normalized_text=normalized,
            corrections=norm_meta["corrections_made"],
            intent_result=intent_result,
            base_response=response_data["final_response"]
        )
        
        # Pilar 2-7: Learning, Healing, etc.
        # ... (existing code)
        
        return {
            "response": final_response,
            "confidence": conf_result["overall_confidence"],
            "intent": intent_result["intent"],
            "normalized": normalized,
            "action": conf_result["action"]
        }
```

---

## CONTOH HASIL

### Input 1: Typo Berat
```
User: "gmana cra stp gpu d srvr?"
```
**Processing:**
- Normalize: "gimana cara setup gpu di server"
- Corrections: gmana→gimana, cra→cara, stp→setup, d→di, srvr→server
- Intent: setup_gpu (confidence: 0.92)
- Action: respond_directly

**Response:**
> "Berikut cara setup GPU di server untuk SIDIX..." *(langsung jawab, tidak sebut typo)*

---

### Input 2: Singkatan
```
User: "mcp server gmn cara install?"
```
**Processing:**
- Normalize: "Model Context Protocol server gimana cara install"
- Abbrev expanded: mcp→Model Context Protocol
- Intent: install_plugin (confidence: 0.88)
- Action: respond_directly

**Response:**
> "Berikut cara install MCP Server untuk SIDIX-SocioMeter..."

---

### Input 3: Tidak Jelas
```
User: "itu apa sih yang kemarin?"
```
**Processing:**
- Normalize: "itu apa sih yang kemarin"
- Intent: unclear (confidence: 0.25)
- Action: ask_clarification

**Response:**
> "Saya ingin memastikan saya mengerti pertanyaan Anda dengan benar...
> 
> Anda menulis: 'itu apa sih yang kemarin?'
> 
> Mohon bantu saya mengerti dengan memberikan: topik utama, konteks, hasil yang diharapkan."

---

## FILE STRUCTURE

```
brain/
├── typo/
│   ├── __init__.py
│   ├── normalizer.py          # Layer 1: Text normalization
│   ├── semantic_matcher.py     # Layer 2: Intent detection
│   ├── confidence_scorer.py    # Layer 3: Confidence scoring
│   └── context_responder.py    # Layer 4: Response generation
│   └── dictionaries.py         # Typo + abbreviation dictionaries
```

---

*Framework ini memastikan SIDIX mengerti user — meski ngetik banyak typo.*
*User tidak perlu perfect. SIDIX yang harus adaptif.*
