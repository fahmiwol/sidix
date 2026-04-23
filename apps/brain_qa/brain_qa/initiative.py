"""
initiative.py — SIDIX Autonomous Learning Engine

Terinspirasi dari riset Continual Learning + RAFT architecture:
  - Self-initiated knowledge acquisition (bukan tunggu user)
  - Domain gap detection (tahu area mana yang lemah)
  - Q&A pair harvesting (simpan percakapan sebagai training data)
  - Experience Replay concept (synthesize dari yang sudah tahu)
  - Low-confidence trigger (jawaban ragu → otomatis cari tahu)

SIDIX Domain Map — target knowledge yang harus dikuasai:
  MIGHAN: design, image gen, video gen, music gen, branding
  HAYFAR: coding, APIs, DevOps, backend, frameworks
  TOARD:  planning, strategy, business, project management
  FACH:   research, science, academia, ML theory
  INAN:   general knowledge, news, everyday questions

Architecture mengikuti RAFT (Retrieval-Augmented Fine-Tuning):
  Phase 1: RAG layer (BM25 corpus) ← diperbarui terus-menerus
  Phase 2: LoRA fine-tune di Kaggle (batch, setiap N minggu)
  Hybrid: corpus sebagai "working memory", model sebagai "long-term memory"
"""

from __future__ import annotations

import datetime
import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────────────

# Repo root (dinamis, tanpa mengikat path lokal tertentu)
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BRAIN_DIR = _ROOT / "brain" / "public"
_CORPUS_WEB = _BRAIN_DIR / "sources" / "web_clips"
_CORPUS_RESEARCH = _BRAIN_DIR / "research_notes"
_DATA_DIR = Path(__file__).resolve().parent.parent / ".data"
_INITIATIVE_DIR = _DATA_DIR / "initiative"
_QA_LOG = _INITIATIVE_DIR / "qa_pairs.jsonl"
_GAP_LOG = _INITIATIVE_DIR / "knowledge_gaps.json"
_STATS_LOG = _INITIATIVE_DIR / "stats.json"
_FINETUNE_DIR = _DATA_DIR / "finetune_harvest"

USER_AGENT = "SIDIX-Initiative/1.0 (educational)"
REQUEST_DELAY = 2.5


# ── Domain Map — apa yang SIDIX harus kuasai ───────────────────────────────────
# Format: domain_id → {persona, topics, min_docs, keywords}
# min_docs: berapa minimum dokumen corpus yang diinginkan
#
# SIDIX belajar tanpa batas — seperti manusia yang terus membaca, berpikir, dan berkembang.
# Semakin banyak domain dikuasai, semakin SIDIX menjadi AI yang benar-benar serba bisa.

DOMAIN_MAP: dict[str, dict] = {

    # ═══════════════════════════════════════════════════════
    # MIGHAN — AI Kreatif: image, video, musik, desain, visual
    # ═══════════════════════════════════════════════════════

    "ai_image_gen": {
        "persona": "MIGHAN",
        "label": "AI Image Generation",
        "topics": [
            "Text-to-image model", "Stable Diffusion", "Midjourney (software)",
            "Generative adversarial network", "Diffusion model",
            "DALL-E", "Imagen (Google)", "Neural style transfer",
            "ControlNet", "FLUX (image model)", "Firefly (Adobe)",
        ],
        "keywords": ["midjourney", "stable diffusion", "dall-e", "flux", "image generation", "ai art", "controlnet"],
        "min_docs": 6,
    },
    "ai_video_gen": {
        "persona": "MIGHAN",
        "label": "AI Video Generation",
        "topics": [
            "Video generation AI", "Text-to-video model",
            "Runway ML", "Sora (OpenAI)", "AI video synthesis",
            "Video diffusion model", "Kling (AI)", "Pika (AI)",
        ],
        "keywords": ["video generation", "text to video", "runway", "sora", "veo", "kling", "pika"],
        "min_docs": 4,
    },
    "ai_music_gen": {
        "persona": "MIGHAN",
        "label": "AI Music & Audio Generation",
        "topics": [
            "AI music generation", "Text-to-music", "Voice cloning",
            "Music synthesis", "Audio generation neural network",
            "Speech synthesis", "Text-to-speech",
        ],
        "keywords": ["suno", "udio", "music generation", "tts", "voice clone", "audio ai", "elevenlabs"],
        "min_docs": 4,
    },
    "design_principles": {
        "persona": "MIGHAN",
        "label": "Design Principles & Theory",
        "topics": [
            "Graphic design", "Logo design", "Brand identity",
            "Typography", "Color theory", "Vector graphics",
            "UI design", "Gestalt principles", "Design thinking",
            "Grid layout", "Visual hierarchy", "Whitespace",
        ],
        "keywords": ["design", "typography", "color theory", "gestalt", "ui", "ux", "visual hierarchy"],
        "min_docs": 4,
    },
    "design_tools": {
        "persona": "MIGHAN",
        "label": "Design Tools & Software",
        "topics": [
            "Adobe Creative Suite", "Adobe Photoshop", "Adobe Illustrator",
            "Figma", "Canva", "InDesign", "Adobe Premiere Pro",
            "Sketch (software)", "Affinity Designer",
        ],
        "keywords": ["photoshop", "illustrator", "figma", "canva", "premiere", "after effects", "sketch"],
        "min_docs": 4,
    },
    "photography_visual": {
        "persona": "MIGHAN",
        "label": "Photography & Visual Arts",
        "topics": [
            "Photography", "Composition (visual arts)", "Lighting (photography)",
            "Color grading", "Photo editing", "Portrait photography",
            "Landscape photography", "Street photography", "Product photography",
            "RAW image format", "HDR photography",
        ],
        "keywords": ["photography", "composition", "lighting", "exposure", "aperture", "shutter", "iso", "raw"],
        "min_docs": 4,
    },
    "visual_styles": {
        "persona": "MIGHAN",
        "label": "Art Styles & Movements",
        "topics": [
            "Art movement", "Impressionism", "Surrealism", "Abstract art",
            "Minimalism", "Art nouveau", "Bauhaus", "Pop art",
            "Cyberpunk", "Synthwave aesthetic", "Anime", "Manga",
            "Illustration", "Concept art", "Digital art",
        ],
        "keywords": ["impressionism", "surrealism", "abstract", "minimalism", "art nouveau", "cyberpunk", "anime", "concept art"],
        "min_docs": 4,
    },
    "3d_animation": {
        "persona": "MIGHAN",
        "label": "3D Design & Animation",
        "topics": [
            "3D computer graphics", "Blender (software)", "3D modeling",
            "Animation", "Rendering", "Texturing", "Rigging",
            "Motion graphics", "Visual effects", "CGI",
        ],
        "keywords": ["3d", "blender", "modeling", "rendering", "animation", "vfx", "cgi", "motion graphics"],
        "min_docs": 3,
    },
    "prompt_engineering": {
        "persona": "MIGHAN",
        "label": "Prompt Engineering for Visuals",
        "topics": [
            "Prompt engineering", "Text prompt", "Negative prompt",
            "Image prompt optimization", "Aesthetic prompt", "Artistic style prompt",
        ],
        "keywords": ["prompt", "negative prompt", "seed", "cfg scale", "sampling", "steps", "lora weight"],
        "min_docs": 3,
    },

    # ═══════════════════════════════════════════════════════
    # HAYFAR — Teknis: coding, engineering, sistem, arsitektur
    # ═══════════════════════════════════════════════════════

    "python_programming": {
        "persona": "HAYFAR",
        "label": "Python Programming",
        "topics": [
            "Python (programming language)", "FastAPI", "Flask",
            "Asynchronous programming", "Python data structures",
            "Decorators (Python)", "Context manager", "Generator (Python)",
            "Object-oriented programming", "Functional programming",
        ],
        "keywords": ["python", "fastapi", "flask", "async", "pip", "venv", "pytest", "decorator", "generator"],
        "min_docs": 5,
    },
    "javascript_typescript": {
        "persona": "HAYFAR",
        "label": "JavaScript & TypeScript",
        "topics": [
            "JavaScript", "TypeScript", "ECMAScript",
            "Node.js", "Deno", "Bun (JavaScript runtime)",
            "Promise (JavaScript)", "Async/await", "Closure (programming)",
            "Prototype (JavaScript)", "Event loop",
        ],
        "keywords": ["javascript", "typescript", "nodejs", "promise", "async", "closure", "event loop"],
        "min_docs": 5,
    },
    "web_frontend": {
        "persona": "HAYFAR",
        "label": "Frontend Development",
        "topics": [
            "React (JavaScript library)", "Vue.js", "Next.js",
            "HTML", "CSS", "Tailwind CSS", "Sass",
            "Web Components", "Progressive web application",
            "Single-page application", "Server-side rendering",
        ],
        "keywords": ["react", "vue", "nextjs", "html", "css", "tailwind", "spa", "ssr"],
        "min_docs": 5,
    },
    "web_backend": {
        "persona": "HAYFAR",
        "label": "Backend Development",
        "topics": [
            "REST API", "GraphQL", "Microservices", "gRPC",
            "Authentication", "JWT", "OAuth", "Middleware",
            "WebSocket", "Server-sent events", "Message queue",
        ],
        "keywords": ["rest api", "graphql", "microservices", "authentication", "jwt", "oauth", "websocket"],
        "min_docs": 4,
    },
    "databases": {
        "persona": "HAYFAR",
        "label": "Databases & Storage",
        "topics": [
            "PostgreSQL", "MySQL", "MongoDB", "Redis",
            "SQL", "Database index", "ACID (database)",
            "NoSQL", "Vector database", "Time series database",
            "Database sharding", "Replication",
        ],
        "keywords": ["sql", "postgresql", "mongodb", "redis", "database", "index", "query", "nosql"],
        "min_docs": 4,
    },
    "devops_cloud": {
        "persona": "HAYFAR",
        "label": "DevOps & Cloud",
        "topics": [
            "Docker (software)", "Kubernetes", "CI/CD", "Cloud computing",
            "Linux", "Git", "GitHub Actions", "Nginx",
            "Load balancer", "Infrastructure as code", "Terraform",
        ],
        "keywords": ["docker", "kubernetes", "devops", "github actions", "linux", "nginx", "terraform"],
        "min_docs": 4,
    },
    "algorithms_ds": {
        "persona": "HAYFAR",
        "label": "Algorithms & Data Structures",
        "topics": [
            "Algorithm", "Data structure", "Big O notation",
            "Sorting algorithm", "Graph (abstract data type)",
            "Dynamic programming", "Tree (data structure)",
            "Hash table", "Binary search", "Recursion",
        ],
        "keywords": ["algorithm", "data structure", "big-o", "sorting", "graph", "dynamic programming", "tree", "hash"],
        "min_docs": 5,
    },
    "system_design": {
        "persona": "HAYFAR",
        "label": "System Design & Architecture",
        "topics": [
            "System design", "Scalability", "Distributed computing",
            "CAP theorem", "Eventual consistency", "Event-driven architecture",
            "Cache (computing)", "CDN", "API gateway",
        ],
        "keywords": ["system design", "scalability", "distributed", "cap theorem", "cache", "cdn", "api gateway"],
        "min_docs": 4,
    },
    "ml_engineering": {
        "persona": "HAYFAR",
        "label": "ML Engineering",
        "topics": [
            "PyTorch", "Transformers (deep learning)", "Fine-tuning (deep learning)",
            "Large language model", "ONNX", "Model deployment",
            "MLOps", "Feature engineering", "Model serving",
        ],
        "keywords": ["pytorch", "transformers", "fine-tune", "llm", "mlops", "inference", "embedding"],
        "min_docs": 5,
    },
    "mobile_development": {
        "persona": "HAYFAR",
        "label": "Mobile Development",
        "topics": [
            "React Native", "Flutter", "Android development",
            "iOS development", "Swift (programming language)",
            "Kotlin", "Mobile UI", "App Store",
        ],
        "keywords": ["react native", "flutter", "android", "ios", "swift", "kotlin", "mobile app"],
        "min_docs": 3,
    },
    "security_cybersecurity": {
        "persona": "HAYFAR",
        "label": "Security & Cybersecurity",
        "topics": [
            "Cybersecurity", "Encryption", "HTTPS", "SSL/TLS",
            "SQL injection", "Cross-site scripting", "OWASP",
            "Penetration testing", "Firewall", "VPN",
        ],
        "keywords": ["cybersecurity", "encryption", "ssl", "sql injection", "xss", "owasp", "pen test"],
        "min_docs": 3,
    },
    "distributed_ai": {
        "persona": "HAYFAR",
        "label": "Distributed AI & Federated Learning",
        "topics": [
            "Federated learning", "Distributed computing",
            "DiLoCo", "Model merging", "DARE merging",
            "TIES merging", "LoRA (machine learning)",
            "Byzantine fault tolerance", "Gossip protocol",
        ],
        "keywords": ["federated learning", "distributed training", "model merging", "lora", "diloco", "flower"],
        "min_docs": 4,
    },

    # ═══════════════════════════════════════════════════════
    # TOARD — Strategi: bisnis, marketing, manajemen, ekonomi
    # ═══════════════════════════════════════════════════════

    "business_strategy": {
        "persona": "TOARD",
        "label": "Business Strategy",
        "topics": [
            "Business strategy", "Strategic planning", "Business model",
            "Competitive advantage", "Market analysis", "SWOT analysis",
            "Porter's five forces", "Blue ocean strategy",
        ],
        "keywords": ["strategy", "business model", "competitive", "swot", "porter", "blue ocean"],
        "min_docs": 4,
    },
    "digital_marketing": {
        "persona": "TOARD",
        "label": "Digital Marketing",
        "topics": [
            "Digital marketing", "Social media marketing",
            "Search engine optimization", "Content marketing",
            "Email marketing", "Influencer marketing",
            "Growth hacking", "A/B testing", "Conversion rate",
        ],
        "keywords": ["marketing", "seo", "social media", "content", "ads", "conversion", "funnel", "growth hacking"],
        "min_docs": 4,
    },
    "entrepreneurship": {
        "persona": "TOARD",
        "label": "Entrepreneurship",
        "topics": [
            "Entrepreneurship", "Startup company", "Venture capital",
            "Lean startup", "Product-market fit", "Bootstrapping",
            "Pivot (business)", "Minimum viable product",
        ],
        "keywords": ["startup", "founder", "entrepreneur", "funding", "mvp", "bootstrap", "pivot"],
        "min_docs": 4,
    },
    "project_management": {
        "persona": "TOARD",
        "label": "Project Management",
        "topics": [
            "Project management", "Agile software development",
            "Scrum (software development)", "Kanban (development)",
            "OKR (management)", "KPI", "Gantt chart", "Risk management",
        ],
        "keywords": ["project management", "agile", "scrum", "sprint", "okr", "kpi", "gantt"],
        "min_docs": 4,
    },
    "economics_finance": {
        "persona": "TOARD",
        "label": "Economics & Finance",
        "topics": [
            "Economics", "Microeconomics", "Macroeconomics",
            "Financial market", "Investment", "Inflation",
            "Supply and demand", "GDP", "Interest rate",
            "Stock market", "Financial statement",
        ],
        "keywords": ["economics", "microeconomics", "macroeconomics", "investment", "inflation", "gdp", "stock"],
        "min_docs": 4,
    },
    "crypto_blockchain": {
        "persona": "TOARD",
        "label": "Cryptocurrency & Blockchain",
        "topics": [
            "Cryptocurrency", "Blockchain", "Bitcoin", "Ethereum",
            "Smart contract", "Decentralized finance", "NFT",
            "Proof of work", "Proof of stake", "Web3",
        ],
        "keywords": ["crypto", "blockchain", "bitcoin", "ethereum", "defi", "nft", "web3", "smart contract"],
        "min_docs": 3,
    },
    "leadership_management": {
        "persona": "TOARD",
        "label": "Leadership & Management",
        "topics": [
            "Leadership", "Management", "Organizational behavior",
            "Human resources", "Team management", "Decision making",
            "Change management", "Corporate culture",
        ],
        "keywords": ["leadership", "management", "team", "hr", "decision making", "culture", "change management"],
        "min_docs": 3,
    },
    "product_management": {
        "persona": "TOARD",
        "label": "Product Management",
        "topics": [
            "Product management", "Product roadmap", "User story",
            "Feature prioritization", "Product-led growth",
            "Customer journey", "User research", "Wireframing",
        ],
        "keywords": ["product manager", "roadmap", "user story", "prioritization", "plg", "customer journey"],
        "min_docs": 3,
    },

    # ═══════════════════════════════════════════════════════
    # FACH — Akademik: riset, sains, matematika, filsafat
    # ═══════════════════════════════════════════════════════

    "machine_learning_theory": {
        "persona": "FACH",
        "label": "Machine Learning Theory",
        "topics": [
            "Machine learning", "Deep learning", "Reinforcement learning",
            "Supervised learning", "Neural network", "Backpropagation",
            "Gradient descent", "Overfitting", "Cross-entropy",
        ],
        "keywords": ["machine learning", "deep learning", "neural", "training", "gradient", "loss", "overfitting"],
        "min_docs": 5,
    },
    "nlp_research": {
        "persona": "FACH",
        "label": "NLP Research",
        "topics": [
            "Natural language processing", "Transformer model",
            "Attention mechanism (deep learning)", "BERT (language model)",
            "Sentiment analysis", "Named-entity recognition",
            "Text generation", "Tokenization",
        ],
        "keywords": ["nlp", "transformer", "attention", "bert", "gpt", "language model", "tokenizer"],
        "min_docs": 5,
    },
    "continual_learning": {
        "persona": "FACH",
        "label": "Continual & Federated Learning",
        "topics": [
            "Continual learning", "Catastrophic interference",
            "Transfer learning", "Meta-learning (computer science)",
            "Knowledge distillation", "Elastic weight consolidation",
            "RAFT (machine learning)",
        ],
        "keywords": ["continual learning", "catastrophic forgetting", "transfer learning", "meta-learning", "ewc"],
        "min_docs": 4,
    },
    "mathematics": {
        "persona": "FACH",
        "label": "Mathematics",
        "topics": [
            "Mathematics", "Linear algebra", "Calculus",
            "Probability theory", "Statistics", "Number theory",
            "Combinatorics", "Graph theory", "Differential equations",
            "Topology", "Abstract algebra", "Set theory",
        ],
        "keywords": ["mathematics", "linear algebra", "calculus", "probability", "statistics", "matrix", "eigenvalue"],
        "min_docs": 6,
    },
    "physics": {
        "persona": "FACH",
        "label": "Physics",
        "topics": [
            "Physics", "Classical mechanics", "Quantum mechanics",
            "Thermodynamics", "Electromagnetism", "Special relativity",
            "General relativity", "Particle physics", "Nuclear physics",
            "Optics", "Fluid dynamics", "Astrophysics",
        ],
        "keywords": ["physics", "quantum", "relativity", "thermodynamics", "electromagnetic", "particle physics"],
        "min_docs": 6,
    },
    "chemistry": {
        "persona": "FACH",
        "label": "Chemistry",
        "topics": [
            "Chemistry", "Organic chemistry", "Inorganic chemistry",
            "Chemical bond", "Periodic table", "Biochemistry",
            "Polymer chemistry", "Physical chemistry", "Chemical reaction",
        ],
        "keywords": ["chemistry", "organic", "inorganic", "molecule", "bond", "reaction", "periodic table"],
        "min_docs": 4,
    },
    "biology": {
        "persona": "FACH",
        "label": "Biology & Life Sciences",
        "topics": [
            "Biology", "Cell biology", "Genetics", "Evolution",
            "Molecular biology", "Microbiology", "Ecology",
            "Neuroscience", "Human anatomy", "DNA", "RNA",
            "CRISPR", "Protein folding",
        ],
        "keywords": ["biology", "genetics", "evolution", "dna", "rna", "neuroscience", "cell", "crispr"],
        "min_docs": 5,
    },
    "philosophy": {
        "persona": "FACH",
        "label": "Philosophy",
        "topics": [
            "Philosophy", "Epistemology", "Ethics",
            "Philosophy of mind", "Logic", "Metaphysics",
            "Philosophy of science", "Existentialism", "Phenomenology",
            "Analytic philosophy", "Continental philosophy",
        ],
        "keywords": ["philosophy", "epistemology", "ethics", "logic", "metaphysics", "existentialism"],
        "min_docs": 4,
    },
    "cognitive_science": {
        "persona": "FACH",
        "label": "Cognitive Science & Psychology",
        "topics": [
            "Cognitive science", "Psychology", "Cognitive bias",
            "Memory (psychology)", "Learning theory", "Behaviorism",
            "Cognitive psychology", "Decision theory", "Heuristics",
        ],
        "keywords": ["cognitive science", "psychology", "bias", "memory", "learning", "decision theory"],
        "min_docs": 4,
    },
    "research_methodology": {
        "persona": "FACH",
        "label": "Research Methodology",
        "topics": [
            "Scientific method", "Research methodology", "Academic publishing",
            "Peer review", "Statistical significance", "Hypothesis testing",
            "Literature review", "Citation", "Systematic review",
        ],
        "keywords": ["research", "scientific method", "peer review", "hypothesis", "statistical", "literature review"],
        "min_docs": 3,
    },
    "information_theory": {
        "persona": "FACH",
        "label": "Information Theory & Computer Science",
        "topics": [
            "Information theory", "Entropy (information theory)",
            "Data compression", "Cryptography", "Computability theory",
            "Complexity theory", "Automata theory",
        ],
        "keywords": ["information theory", "entropy", "compression", "cryptography", "turing", "complexity"],
        "min_docs": 3,
    },

    # ═══════════════════════════════════════════════════════
    # INAN — General Knowledge: serba bisa, pengetahuan luas
    # ═══════════════════════════════════════════════════════

    "general_ai_news": {
        "persona": "INAN",
        "label": "General AI & Technology",
        "topics": [
            "Artificial intelligence", "OpenAI", "Google DeepMind",
            "Anthropic", "Robotics", "Automation", "AGI",
            "Large language model", "AI safety", "AI ethics",
        ],
        "keywords": ["openai", "anthropic", "google ai", "chatgpt", "gemini", "claude", "agi", "ai safety"],
        "min_docs": 5,
    },
    "world_history": {
        "persona": "INAN",
        "label": "World History",
        "topics": [
            "World history", "Ancient history", "Medieval history",
            "Modern history", "Industrial Revolution", "World War I",
            "World War II", "Cold War", "Colonialism",
            "Renaissance", "Islamic Golden Age", "Roman Empire",
            "Ottoman Empire", "Mongol Empire", "History of China",
        ],
        "keywords": ["history", "ancient", "medieval", "world war", "empire", "civilization", "revolution"],
        "min_docs": 6,
    },
    "indonesian_history": {
        "persona": "INAN",
        "label": "Indonesian History & Culture",
        "topics": [
            "History of Indonesia", "Majapahit", "Srivijaya",
            "Dutch East India Company", "Indonesian Revolution",
            "Suharto", "Sukarno", "Indonesian culture",
            "Batik", "Wayang", "Pancasila",
        ],
        "keywords": ["indonesia", "majapahit", "srivijaya", "colonial", "proklamasi", "pancasila", "batik"],
        "min_docs": 4,
    },
    "geography": {
        "persona": "INAN",
        "label": "Geography & Earth Sciences",
        "topics": [
            "Geography", "Physical geography", "Climate",
            "Ocean", "Continent", "Country", "Ecosystem",
            "Climate change", "Natural disaster", "Geology",
        ],
        "keywords": ["geography", "climate", "ocean", "continent", "ecosystem", "climate change", "geology"],
        "min_docs": 4,
    },
    "linguistics_language": {
        "persona": "INAN",
        "label": "Linguistics & Languages",
        "topics": [
            "Linguistics", "Language", "Grammar", "Syntax",
            "Semantics", "Phonetics", "Indonesian language",
            "Arabic language", "English language", "Javanese language",
            "Language family", "Writing system",
        ],
        "keywords": ["linguistics", "language", "grammar", "syntax", "phonetics", "bahasa indonesia"],
        "min_docs": 4,
    },
    "literature_poetry": {
        "persona": "INAN",
        "label": "Literature & Poetry",
        "topics": [
            "Literature", "Poetry", "Novel", "Short story",
            "World literature", "Indonesian literature",
            "Arabic poetry", "Classical literature",
            "Narrative structure", "Literary analysis",
        ],
        "keywords": ["literature", "poetry", "novel", "prose", "narrative", "metaphor", "syair", "pantun"],
        "min_docs": 4,
    },
    "religion_spirituality": {
        "persona": "INAN",
        "label": "Religion & Spirituality",
        "topics": [
            "Islam", "Quran", "Hadith", "Fiqh",
            "Sufism", "Islamic philosophy", "Comparative religion",
            "Buddhism", "Christianity", "Hinduism",
            "Ethics (religion)", "Theology",
        ],
        "keywords": ["islam", "quran", "hadith", "fiqh", "sufism", "religion", "theology", "ethics"],
        "min_docs": 5,
    },
    "health_medicine": {
        "persona": "INAN",
        "label": "Health & Medicine",
        "topics": [
            "Medicine", "Public health", "Nutrition",
            "Mental health", "Anatomy", "Physiology",
            "Disease", "Pharmacology", "Epidemiology",
            "First aid", "Exercise physiology",
        ],
        "keywords": ["medicine", "health", "nutrition", "mental health", "anatomy", "disease", "pharmacology"],
        "min_docs": 4,
    },
    "environment_sustainability": {
        "persona": "INAN",
        "label": "Environment & Sustainability",
        "topics": [
            "Environmental science", "Climate change", "Renewable energy",
            "Sustainability", "Biodiversity", "Carbon emission",
            "Solar energy", "Wind energy", "Circular economy",
        ],
        "keywords": ["environment", "climate change", "renewable energy", "sustainability", "biodiversity", "carbon"],
        "min_docs": 3,
    },
    "social_science": {
        "persona": "INAN",
        "label": "Social Sciences",
        "topics": [
            "Sociology", "Anthropology", "Political science",
            "International relations", "Democracy", "Geopolitics",
            "Social inequality", "Human rights", "Cultural studies",
        ],
        "keywords": ["sociology", "anthropology", "politics", "democracy", "geopolitics", "human rights"],
        "min_docs": 3,
    },
    "astronomy_space": {
        "persona": "INAN",
        "label": "Astronomy & Space",
        "topics": [
            "Astronomy", "Solar System", "Galaxy",
            "Black hole", "Stars", "Universe", "Cosmology",
            "Space exploration", "NASA", "James Webb Telescope",
        ],
        "keywords": ["astronomy", "space", "galaxy", "black hole", "universe", "nasa", "telescope"],
        "min_docs": 3,
    },
    "classical_texts": {
        "persona": "INAN",
        "label": "Classical Texts & Knowledge",
        "topics": [
            "Classical antiquity", "Greek philosophy", "Aristotle",
            "Plato", "Socrates", "Confucianism", "Taoism",
            "Ancient Egypt", "Mesopotamia", "Sanskrit literature",
            "Kitab kuning", "Islamic manuscripts",
        ],
        "keywords": ["classical", "aristotle", "plato", "confucius", "ancient", "manuscript", "kitab"],
        "min_docs": 4,
    },
}



# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class QAPair:
    """Percakapan yang disimpan sebagai training data masa depan."""
    session_id: str
    question: str
    answer: str
    persona: str
    confidence: str
    confidence_score: float
    citations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    domain: str = ""
    answer_type: str = "fakta"


@dataclass
class KnowledgeGap:
    """Domain yang corpus-nya lemah — perlu di-fetch."""
    domain_id: str
    label: str
    persona: str
    doc_count: int
    min_docs: int
    deficit: int
    last_fetched: str = ""
    fetch_priority: float = 1.0


@dataclass
class InitiativeStats:
    """Statistik autonomous learning SIDIX."""
    total_qa_saved: int = 0
    total_docs_fetched: int = 0
    total_reindexes: int = 0
    last_gap_scan: str = ""
    last_fetch: str = ""
    gaps_detected: int = 0
    gaps_resolved: int = 0
    domains_covered: int = 0
    domains_total: int = len(DOMAIN_MAP)
    low_confidence_triggers: int = 0


# ── Corpus scanner ─────────────────────────────────────────────────────────────

def scan_corpus_coverage() -> dict[str, int]:
    """
    Hitung berapa dokumen corpus per domain.
    Returns: {domain_id: doc_count}
    """
    coverage: dict[str, int] = {d: 0 for d in DOMAIN_MAP}

    all_docs: list[Path] = []
    for d in [_CORPUS_WEB, _CORPUS_RESEARCH]:
        if d.exists():
            all_docs.extend(d.glob("*.md"))

    for doc in all_docs:
        try:
            content = doc.read_text(encoding="utf-8", errors="ignore").lower()
            for domain_id, meta in DOMAIN_MAP.items():
                for kw in meta["keywords"]:
                    if kw.lower() in content:
                        coverage[domain_id] += 1
                        break
        except Exception:
            continue

    return coverage


def detect_knowledge_gaps(coverage: dict[str, int] | None = None) -> list[KnowledgeGap]:
    """
    Temukan domain yang doc_count < min_docs.
    Returns: list of KnowledgeGap sorted by priority (worst first).
    """
    if coverage is None:
        coverage = scan_corpus_coverage()

    gaps: list[KnowledgeGap] = []
    for domain_id, meta in DOMAIN_MAP.items():
        count = coverage.get(domain_id, 0)
        min_req = meta["min_docs"]
        if count < min_req:
            deficit = min_req - count
            priority = deficit / max(count, 0.1)  # ratio: makin deficit, makin prioritas
            gaps.append(KnowledgeGap(
                domain_id=domain_id,
                label=meta["label"],
                persona=meta["persona"],
                doc_count=count,
                min_docs=min_req,
                deficit=deficit,
                fetch_priority=round(priority, 2),
            ))

    gaps.sort(key=lambda g: g.fetch_priority, reverse=True)
    return gaps


# ── Wikipedia fetcher ──────────────────────────────────────────────────────────

def _fetch_wiki_summary(title: str) -> dict | None:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except Exception:
        pass
    return None


def _fetch_wiki_extract(title: str, sentences: int = 25) -> str:
    url = "https://en.wikipedia.org/w/api.php"
    params = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "exintro": "1",
        "explaintext": "1", "titles": title, "format": "json",
        "exsentences": sentences,
    })
    try:
        req = urllib.request.Request(f"{url}?{params}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                return page.get("extract", "")
    except Exception:
        pass
    return ""


def _slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")[:70]


def fetch_domain_knowledge(domain_id: str, max_topics: int = 3) -> int:
    """
    Fetch Wikipedia articles untuk domain tertentu.
    Returns: jumlah artikel baru yang disimpan.
    """
    meta = DOMAIN_MAP.get(domain_id)
    if not meta:
        return 0

    _CORPUS_WEB.mkdir(parents=True, exist_ok=True)
    existing_slugs = {_slugify(f.stem) for f in _CORPUS_WEB.glob("*.md")}

    topics = meta["topics"]
    random.shuffle(topics)  # variasi tiap run
    fetched = 0

    for topic in topics[:max_topics]:
        slug = _slugify(topic)
        if any(slug[:20] in ex for ex in existing_slugs):
            continue  # sudah ada

        data = _fetch_wiki_summary(topic)
        if not data:
            time.sleep(REQUEST_DELAY)
            continue

        extract = _fetch_wiki_extract(topic)
        title = data.get("title", topic)
        description = data.get("description", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        today = datetime.date.today().isoformat()

        if len(extract) > 7000:
            extract = extract[:7000] + "\n\n[... dipersingkat untuk corpus ...]"

        md = f"""# {title}
*Domain: {meta['label']} | Persona: {meta['persona']} | Fetched: {today}*

> {description}

**Source**: {page_url}
**Auto-fetched by**: SIDIX Initiative Engine (domain gap fill)

---

{extract}

---
*SIDIX Knowledge Corpus — {today} | domain:{domain_id}*
"""
        fname = f"{slug}-wiki-{hashlib.md5(topic.encode()).hexdigest()[:6]}.md"
        (_CORPUS_WEB / fname).write_text(md, encoding="utf-8")
        existing_slugs.add(slug)
        fetched += 1
        time.sleep(REQUEST_DELAY)

    return fetched


# ── Q&A Harvester ──────────────────────────────────────────────────────────────

def save_qa_pair(session_id: str, question: str, answer: str,
                 persona: str, confidence: str = "", confidence_score: float = 0.0,
                 citations: list[dict] | None = None, answer_type: str = "fakta") -> None:
    """
    Simpan percakapan sebagai training data untuk fine-tune Kaggle berikutnya.
    Format ChatML — langsung bisa dipakai SFTTrainer.
    """
    _INITIATIVE_DIR.mkdir(parents=True, exist_ok=True)
    _FINETUNE_DIR.mkdir(parents=True, exist_ok=True)

    # Hanya simpan yang cukup confident dan informatif
    if len(answer.strip()) < 50:
        return
    if "[SIDIX]" in answer and "tidak ditemukan" in answer:
        return  # jangan simpan error message

    cite_sources = [c.get("source", "") for c in (citations or [])]
    domain = _detect_domain_from_question(question)

    pair = QAPair(
        session_id=session_id,
        question=question,
        answer=answer,
        persona=persona,
        confidence=confidence,
        confidence_score=confidence_score,
        citations=cite_sources,
        domain=domain,
        answer_type=answer_type,
    )

    # Simpan ke JSONL log
    with open(_QA_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")

    # Simpan dalam format ChatML untuk fine-tune
    _save_chatml(pair)


def _detect_domain_from_question(question: str) -> str:
    """Deteksi domain dari pertanyaan (rule-based)."""
    q = question.lower()
    if any(k in q for k in ["gambar", "image", "midjourney", "stable diffusion", "dall-e", "flux"]):
        return "ai_image_gen"
    if any(k in q for k in ["video", "veo", "runway", "kling", "sora"]):
        return "ai_video_gen"
    if any(k in q for k in ["musik", "music", "suno", "udio", "audio", "lagu"]):
        return "ai_music_gen"
    if any(k in q for k in ["desain", "design", "logo", "brand", "warna", "tipografi"]):
        return "design_tools"
    if any(k in q for k in ["python", "fastapi", "django", "flask", "kode", "coding"]):
        return "python_programming"
    if any(k in q for k in ["javascript", "react", "vue", "frontend", "web"]):
        return "web_development"
    if any(k in q for k in ["docker", "kubernetes", "devops", "cloud", "deploy"]):
        return "devops_cloud"
    if any(k in q for k in ["machine learning", "deep learning", "neural", "pytorch", "tensorflow"]):
        return "ml_engineering"
    if any(k in q for k in ["bisnis", "business", "strategi", "strategy", "marketing"]):
        return "business_strategy"
    if any(k in q for k in ["startup", "entrepreneur", "founder", "produk", "mvp"]):
        return "entrepreneurship"
    if any(k in q for k in ["project", "proyek", "agile", "scrum", "sprint", "okr"]):
        return "project_management"
    return "general"


def _save_chatml(pair: QAPair) -> None:
    """Simpan dalam format ChatML untuk SFTTrainer Kaggle."""
    system_prompt = (
        f"Kamu adalah SIDIX, persona {pair.persona}. "
        "Berikan jawaban yang informatif, akurat, dan sebutkan sumber jika memungkinkan."
    )
    chatml = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pair.question},
            {"role": "assistant", "content": pair.answer},
        ],
        "domain": pair.domain,
        "persona": pair.persona,
        "confidence_score": pair.confidence_score,
        "timestamp": pair.timestamp,
    }
    outfile = _FINETUNE_DIR / f"harvest_{pair.timestamp[:10]}.jsonl"
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(chatml, ensure_ascii=False) + "\n")


# ── Low-confidence trigger ────────────────────────────────────────────────────

def on_low_confidence(question: str, persona: str, confidence_score: float,
                      domain: str = "") -> None:
    """
    Dipanggil saat SIDIX menjawab dengan confidence rendah.
    Trigger: cari tahu topik ini → masukkan jadwal fetch.

    Threshold: < 0.4 → tandai sebagai gap dan jadwalkan fetch.
    """
    if confidence_score >= 0.4:
        return

    _INITIATIVE_DIR.mkdir(parents=True, exist_ok=True)

    gap_file = _GAP_LOG
    gaps: list[dict] = []
    if gap_file.exists():
        try:
            gaps = json.loads(gap_file.read_text(encoding="utf-8"))
        except Exception:
            gaps = []

    # Cegah duplikasi
    existing_questions = {g.get("question", "") for g in gaps}
    if question in existing_questions:
        return

    gaps.append({
        "question": question,
        "persona": persona,
        "domain": domain or _detect_domain_from_question(question),
        "confidence_score": confidence_score,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "pending",
    })

    # Atomic write
    tmp = gap_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(gaps, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(gap_file)

    _bump_stat("low_confidence_triggers")


# ── Stats ──────────────────────────────────────────────────────────────────────

def _load_stats() -> dict:
    _INITIATIVE_DIR.mkdir(parents=True, exist_ok=True)
    if _STATS_LOG.exists():
        try:
            return json.loads(_STATS_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return asdict(InitiativeStats())


def _save_stats(stats: dict) -> None:
    tmp = _STATS_LOG.with_suffix(".tmp")
    tmp.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_STATS_LOG)


def _bump_stat(key: str, by: int = 1) -> None:
    stats = _load_stats()
    stats[key] = stats.get(key, 0) + by
    _save_stats(stats)


def get_stats() -> dict:
    return _load_stats()


# ── Main initiative cycle ─────────────────────────────────────────────────────

def run_initiative_cycle(
    max_domains_to_fix: int = 3,
    max_topics_per_domain: int = 2,
    verbose: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Siklus inisiatif mandiri SIDIX:
    1. Scan coverage corpus
    2. Detect knowledge gaps
    3. Fetch Wikipedia untuk domain paling lemah
    4. Reindex
    5. Update stats

    Returns: ringkasan hasil.
    """
    today = datetime.datetime.utcnow().isoformat()

    if verbose:
        print("=" * 55)
        print("  SIDIX Initiative Engine — Autonomous Learning")
        print(f"  {today[:19]}")
        print("=" * 55)

    # Step 1: Scan
    if verbose:
        print("\n[1/4] Scanning corpus coverage...")
    coverage = scan_corpus_coverage()
    covered = sum(1 for d, cnt in coverage.items() if cnt >= DOMAIN_MAP[d]["min_docs"])

    if verbose:
        for domain_id, cnt in coverage.items():
            req = DOMAIN_MAP[domain_id]["min_docs"]
            status = "OK" if cnt >= req else f"GAP (need {req})"
            persona = DOMAIN_MAP[domain_id]["persona"]
            print(f"  [{persona}] {DOMAIN_MAP[domain_id]['label']}: {cnt} docs {status}")

    # Step 2: Detect gaps
    gaps = detect_knowledge_gaps(coverage)

    if verbose:
        print(f"\n[2/4] Knowledge gaps: {len(gaps)} domains below minimum")
        for g in gaps[:5]:
            print(f"  ! {g.label} ({g.persona}): {g.doc_count}/{g.min_docs} docs, priority={g.fetch_priority}")

    # Step 3: Fetch
    total_fetched = 0
    domains_fixed = 0

    if gaps and not dry_run:
        if verbose:
            print(f"\n[3/4] Fetching knowledge for top {min(max_domains_to_fix, len(gaps))} domains...")
        for gap in gaps[:max_domains_to_fix]:
            if verbose:
                print(f"  >> {gap.label}...")
            n = fetch_domain_knowledge(gap.domain_id, max_topics=max_topics_per_domain)
            total_fetched += n
            if n > 0:
                domains_fixed += 1
                if verbose:
                    print(f"    + {n} article(s) added")
            else:
                if verbose:
                    print(f"    (no new articles)")
    elif dry_run:
        if verbose:
            print("\n[3/4] DRY RUN — skipping fetch")

    # Step 4: Reindex if new docs
    if total_fetched > 0 and not dry_run:
        if verbose:
            print("\n[4/5] Reindexing corpus...")
        try:
            import subprocess
            venv_py = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
            py = str(venv_py) if venv_py.exists() else "python"
            result = subprocess.run(
                [py, "-m", "brain_qa", "index"],
                cwd=str(Path(__file__).parent.parent),
                capture_output=True, text=True, timeout=90,
            )
            if result.returncode == 0:
                if verbose:
                    print("  + Reindex complete")
                _bump_stat("total_reindexes")
            else:
                if verbose:
                    print(f"  Reindex warning: {result.stderr[:200]}")
        except Exception as e:
            if verbose:
                print(f"  Reindex error: {e}")

    # Step 5: Convert new docs → training pairs (Knowledge Absorption)
    training_pairs_added = 0
    if total_fetched > 0 and not dry_run:
        if verbose:
            print("\n[5/5] Converting new docs to training pairs...")
        try:
            from .corpus_to_training import process_corpus_to_training
            training_pairs_added = process_corpus_to_training(verbose=False)
            if verbose:
                print(f"  + {training_pairs_added} training pairs generated")
            _bump_stat("total_training_pairs_generated")
        except Exception as e:
            if verbose:
                print(f"  Training conversion warning: {e}")
    elif not dry_run and verbose:
        print("\n[5/5] No new docs — skipping training conversion")

    # Update stats
    stats = _load_stats()
    stats["last_gap_scan"] = today
    if total_fetched > 0:
        stats["last_fetch"] = today
        stats["total_docs_fetched"] = stats.get("total_docs_fetched", 0) + total_fetched
    stats["gaps_detected"] = len(gaps)
    stats["gaps_resolved"] = stats.get("gaps_resolved", 0) + domains_fixed
    stats["domains_covered"] = covered
    stats["domains_total"] = len(DOMAIN_MAP)
    _save_stats(stats)

    summary = {
        "domains_scanned": len(DOMAIN_MAP),
        "domains_covered": covered,
        "gaps_found": len(gaps),
        "domains_fetched": domains_fixed,
        "articles_fetched": total_fetched,
        "training_pairs_generated": training_pairs_added,
        "timestamp": today,
    }

    if verbose:
        print(f"\nDone: {total_fetched} articles fetched, {domains_fixed} domains improved")
        if training_pairs_added > 0:
            print(f"Training: {training_pairs_added} new pairs ready for Kaggle fine-tune")
        print(f"Coverage: {covered}/{len(DOMAIN_MAP)} domains at minimum")

    return summary


def get_finetune_harvest_stats() -> dict:
    """Statistik training data yang sudah dikumpulkan."""
    total = 0
    by_domain: dict[str, int] = {}
    if _FINETUNE_DIR.exists():
        for f in _FINETUNE_DIR.glob("*.jsonl"):
            lines = f.read_text(encoding="utf-8").splitlines()
            for line in lines:
                try:
                    d = json.loads(line)
                    total += 1
                    dom = d.get("domain", "unknown")
                    by_domain[dom] = by_domain.get(dom, 0) + 1
                except Exception:
                    pass
    return {"total_pairs": total, "by_domain": by_domain}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SIDIX Initiative Engine")
    sub = parser.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Jalankan satu siklus learning")
    run_p.add_argument("--max-domains", type=int, default=3)
    run_p.add_argument("--max-topics", type=int, default=2)
    run_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("gaps", help="Tampilkan knowledge gaps saat ini")
    sub.add_parser("stats", help="Statistik initiative engine")
    sub.add_parser("harvest", help="Statistik training data harvest")

    args = parser.parse_args()

    if args.cmd == "run":
        run_initiative_cycle(
            max_domains_to_fix=args.max_domains,
            max_topics_per_domain=args.max_topics,
            dry_run=args.dry_run,
        )
    elif args.cmd == "gaps":
        coverage = scan_corpus_coverage()
        gaps = detect_knowledge_gaps(coverage)
        if not gaps:
            print("OK: Semua domain sudah di atas minimum!")
        else:
            print(f"GAP: {len(gaps)} domain perlu diisi:\n")
            for g in gaps:
                print(f"  [{g.persona}] {g.label}: {g.doc_count}/{g.min_docs} docs (deficit: {g.deficit})")
    elif args.cmd == "stats":
        import json
        print(json.dumps(get_stats(), indent=2, ensure_ascii=False))
    elif args.cmd == "harvest":
        import json
        print(json.dumps(get_finetune_harvest_stats(), indent=2, ensure_ascii=False))
    else:
        parser.print_help()
