"""
corpus_to_training.py — SIDIX Knowledge Absorption Pipeline

Fungsi: ubah corpus markdown → training pairs ChatML
Ini yang membuat SIDIX benar-benar BELAJAR dari corpus,
bukan sekadar menyimpan file untuk di-search.

Pipeline:
  Corpus doc → ekstrak konsep → generate Q&A → ChatML SFT format

Seperti cara manusia belajar:
  Baca buku → pahami konsep → latihan soal → ujian → jago

SIDIX:
  Baca corpus → ekstrak konsep → buat Q&A → fine-tune → pintar

Tanpa GPU lokal: generate Q&A via template NLP (deterministic)
Dengan GPU: bisa pakai model untuk generate Q&A yang lebih natural
"""

from __future__ import annotations

import hashlib
import json
import re
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

# ── Paths ──────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BRAIN_DIR = _ROOT / "brain" / "public"
_DATA_DIR = Path(__file__).resolve().parent.parent / ".data"
_TRAINING_DIR = _DATA_DIR / "training_generated"
_TRAINING_DIR.mkdir(parents=True, exist_ok=True)

# Exported: corpus dirs yang diproses (bisa di-import oleh agent_serve)
_CORPUS_DIRS: list[Path] = [
    _BRAIN_DIR / "research_notes",
    _BRAIN_DIR / "sources" / "web_clips",
    _BRAIN_DIR / "principles",
]

# Exported: finetune harvest dir (dari initiative.py)
_FINETUNE_DIR = _DATA_DIR / "finetune_harvest"

# ── Domain → Persona system prompt ────────────────────────────────────────────

PERSONA_SYSTEM = {
    "MIGHAN": (
        "Kamu adalah SIDIX dengan persona MIGHAN — AI kreatif yang menguasai "
        "image generation (Midjourney, Stable Diffusion, FLUX, DALL-E, Ideogram), "
        "video generation (Veo, Runway, Kling, Sora), music AI (Suno, Udio), "
        "design tools, logo, vector, dan workflow kreatif. "
        "Jawab dengan antusias, berikan contoh praktis, dan rekomendasikan tools terbaik."
    ),
    "HAYFAR": (
        "Kamu adalah SIDIX dengan persona HAYFAR — AI teknis yang menguasai "
        "Python, FastAPI, JavaScript, React, Docker, cloud deployment, "
        "machine learning engineering, dan software architecture. "
        "Jawab dengan presisi teknis, berikan kode contoh bila relevan."
    ),
    "TOARD": (
        "Kamu adalah SIDIX dengan persona TOARD — AI strategis yang menguasai "
        "business strategy, digital marketing, entrepreneurship, project management, "
        "OKR, product roadmap, dan business model canvas. "
        "Jawab dengan framework yang terstruktur dan actionable."
    ),
    "FACH": (
        "Kamu adalah SIDIX dengan persona FACH — AI akademik yang menguasai "
        "machine learning theory, NLP, deep learning, continual learning, "
        "research methodology, dan scientific writing. "
        "Jawab dengan akurasi akademik, sitasi konsep, dan analisis mendalam."
    ),
    "INAN": (
        "Kamu adalah SIDIX dengan persona INAN — AI general yang bisa menjawab "
        "pertanyaan umum tentang teknologi, bisnis, sains, dan kehidupan sehari-hari. "
        "Jawab dengan bahasa sederhana, mudah dipahami semua kalangan."
    ),
}

# ── Domain keyword → Persona mapping ──────────────────────────────────────────

DOMAIN_PERSONA = {
    "ai_image_gen": "MIGHAN", "ai_video_gen": "MIGHAN",
    "ai_music_gen": "MIGHAN", "design_tools": "MIGHAN",
    "python_programming": "HAYFAR", "web_development": "HAYFAR",
    "devops_cloud": "HAYFAR", "ml_engineering": "HAYFAR",
    "business_strategy": "TOARD", "digital_marketing": "TOARD",
    "entrepreneurship": "TOARD", "project_management": "TOARD",
    "machine_learning_theory": "FACH", "nlp_research": "FACH",
    "continual_learning": "FACH",
    "general_ai_news": "INAN", "economics_finance": "INAN",
}

# ── Q&A Template Engine ────────────────────────────────────────────────────────

@dataclass
class TrainingPair:
    question: str
    answer: str
    persona: str
    source_doc: str
    domain: str
    template_type: str
    pair_id: str = field(default_factory=lambda: "")

    def __post_init__(self):
        if not self.pair_id:
            h = hashlib.md5(f"{self.question}{self.answer}".encode()).hexdigest()[:10]
            self.pair_id = f"tp_{h}"

    def to_chatml(self) -> dict:
        return {
            "messages": [
                {"role": "system", "content": PERSONA_SYSTEM.get(self.persona, PERSONA_SYSTEM["INAN"])},
                {"role": "user", "content": self.question},
                {"role": "assistant", "content": self.answer},
            ],
            "domain": self.domain,
            "persona": self.persona,
            "source": self.source_doc,
            "template_type": self.template_type,
            "pair_id": self.pair_id,
        }


# ── Text chunking ──────────────────────────────────────────────────────────────

def _clean_markdown(text: str) -> str:
    """Hapus markdown formatting untuk ekstraksi."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"^\s*[-*|]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_sections(doc_text: str) -> list[tuple[str, str]]:
    """
    Ekstrak bagian (heading → konten) dari dokumen markdown.
    Returns: [(heading, content), ...]
    """
    sections = []
    current_heading = "Overview"
    current_content: list[str] = []

    for line in doc_text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            if current_content:
                content = "\n".join(current_content).strip()
                if len(content) > 100:
                    sections.append((current_heading, content))
                current_content = []
            current_heading = re.sub(r"^#{1,3}\s+", "", line).strip()
        else:
            current_content.append(line)

    if current_content:
        content = "\n".join(current_content).strip()
        if len(content) > 100:
            sections.append((current_heading, content))

    return sections


def _extract_key_terms(text: str, max_terms: int = 5) -> list[str]:
    """Ekstrak istilah kunci dari teks (simple noun phrase extraction)."""
    clean = _clean_markdown(text)
    # Cari kata kapital (nama proper / konsep)
    proper = re.findall(r"\b([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{3,})*)\b", clean)
    # Cari bold terms dari original
    bold = re.findall(r"\*\*(.+?)\*\*", text)
    # Cari backtick terms
    code = re.findall(r"`([^`]{3,30})`", text)

    candidates = bold + code + proper
    seen: set[str] = set()
    result: list[str] = []
    for t in candidates:
        t = t.strip()
        if t and t not in seen and len(t) > 3:
            seen.add(t)
            result.append(t)
        if len(result) >= max_terms:
            break

    return result


def _split_paragraphs(text: str, min_len: int = 80) -> list[str]:
    """Split teks menjadi paragraf yang cukup panjang."""
    clean = _clean_markdown(text)
    paras = [p.strip() for p in clean.split("\n\n") if len(p.strip()) >= min_len]
    return paras


# ── Template Q&A Generators ────────────────────────────────────────────────────

def _gen_definition_pairs(heading: str, content: str, persona: str, source: str, domain: str) -> list[TrainingPair]:
    """Template: Apa itu X? → definisi dari dokumen."""
    clean = _clean_markdown(content)
    paras = _split_paragraphs(clean)
    if not paras:
        return []

    pairs = []
    first_para = paras[0][:600]

    questions = [
        f"Apa itu {heading}?",
        f"Jelaskan tentang {heading}.",
        f"Apa yang dimaksud dengan {heading}?",
        f"Tolong jelaskan {heading} secara singkat.",
    ]

    q = random.choice(questions)
    answer = first_para
    if len(paras) > 1:
        answer += f"\n\n{paras[1][:400]}"

    pairs.append(TrainingPair(
        question=q, answer=answer.strip(),
        persona=persona, source_doc=source,
        domain=domain, template_type="definition"
    ))
    return pairs


def _gen_howto_pairs(heading: str, content: str, persona: str, source: str, domain: str) -> list[TrainingPair]:
    """Template: Bagaimana cara menggunakan X? → langkah-langkah."""
    clean = _clean_markdown(content)

    # Cari numbered steps atau bullet points
    steps = re.findall(r"(?:^|\n)\s*(?:\d+\.|\-|\*)\s+(.+)", content)
    if len(steps) < 2:
        return []

    steps_text = "\n".join(f"{i+1}. {s.strip()}" for i, s in enumerate(steps[:7]))
    answer = f"Berikut langkah-langkah untuk {heading}:\n\n{steps_text}"

    questions = [
        f"Bagaimana cara menggunakan {heading}?",
        f"Apa langkah-langkah untuk {heading}?",
        f"Bagaimana {heading} bekerja?",
        f"Cara pakai {heading} yang benar?",
    ]

    return [TrainingPair(
        question=random.choice(questions), answer=answer,
        persona=persona, source_doc=source,
        domain=domain, template_type="howto"
    )]


def _gen_comparison_pairs(content: str, persona: str, source: str, domain: str) -> list[TrainingPair]:
    """Template: Apa perbedaan X dan Y? — dari tabel atau perbandingan."""
    # Cari pola tabel markdown
    table_match = re.search(r"(\|.+\|[\s\S]+?\|.+\|)", content)
    if not table_match:
        return []

    table = table_match.group(1)
    # Ekstrak nama dari kolom pertama
    col1_items = re.findall(r"^\|\s*\*{0,2}(.+?)\*{0,2}\s*\|", table, re.MULTILINE)
    col1_items = [c.strip() for c in col1_items if len(c.strip()) > 2 and c.strip() not in ["-", ":---"]]

    if len(col1_items) < 2:
        return []

    clean_table = _clean_markdown(table)[:800]

    questions = [
        f"Apa perbedaan {col1_items[0]} dan {col1_items[1]}?",
        f"Bandingkan {col1_items[0]} vs {col1_items[1]}.",
        f"Kapan pakai {col1_items[0]} vs {col1_items[1]}?",
    ]

    answer = (
        f"Berikut perbandingan {col1_items[0]} dan {col1_items[1]}:\n\n"
        f"{clean_table}\n\n"
        f"Pilihan tergantung kebutuhan: {col1_items[0]} unggul dalam beberapa aspek, "
        f"sementara {col1_items[1]} memiliki keunggulan berbeda."
    )

    return [TrainingPair(
        question=random.choice(questions), answer=answer,
        persona=persona, source_doc=source,
        domain=domain, template_type="comparison"
    )]


def _gen_concept_qa_pairs(heading: str, content: str, persona: str, source: str, domain: str) -> list[TrainingPair]:
    """Template: Q&A untuk setiap istilah kunci dalam konten."""
    terms = _extract_key_terms(content, max_terms=3)
    paras = _split_paragraphs(_clean_markdown(content))
    pairs = []

    for term in terms:
        # Cari paragraf yang mengandung term ini
        relevant = [p for p in paras if term.lower() in p.lower()]
        if not relevant:
            continue

        context = relevant[0][:500]
        if len(context) < 60:
            continue

        q_templates = [
            f"Apa itu {term} dalam konteks {heading}?",
            f"Bagaimana {term} digunakan?",
            f"Mengapa {term} penting?",
            f"Jelaskan {term}.",
        ]

        pairs.append(TrainingPair(
            question=random.choice(q_templates),
            answer=context,
            persona=persona, source_doc=source,
            domain=domain, template_type="concept"
        ))

    return pairs


def _gen_practical_pairs(heading: str, content: str, persona: str, source: str, domain: str) -> list[TrainingPair]:
    """Template: Pertanyaan praktis sesuai persona."""
    clean = _clean_markdown(content)[:600]
    if len(clean) < 100:
        return []

    persona_questions = {
        "MIGHAN": [
            f"Saya ingin buat konten visual menggunakan {heading}, bagaimana caranya?",
            f"Tools apa yang paling bagus untuk {heading}?",
            f"Berikan rekomendasi {heading} untuk pemula.",
        ],
        "HAYFAR": [
            f"Bagaimana cara implementasi {heading} di Python?",
            f"Apa best practice untuk {heading} di production?",
            f"Berikan contoh penggunaan {heading}.",
        ],
        "TOARD": [
            f"Bagaimana {heading} bisa diaplikasikan ke bisnis?",
            f"Strategi apa untuk menggunakan {heading} secara efektif?",
            f"Apa manfaat {heading} untuk pertumbuhan bisnis?",
        ],
        "FACH": [
            f"Apa landasan teori di balik {heading}?",
            f"Bagaimana {heading} dievaluasi dalam penelitian?",
            f"Jelaskan mekanisme {heading} secara teknis.",
        ],
        "INAN": [
            f"Apa itu {heading} dengan bahasa sederhana?",
            f"Kenapa saya harus tahu tentang {heading}?",
            f"Apakah {heading} berguna untuk orang awam?",
        ],
    }

    questions = persona_questions.get(persona, persona_questions["INAN"])
    return [TrainingPair(
        question=random.choice(questions),
        answer=clean,
        persona=persona, source_doc=source,
        domain=domain, template_type="practical"
    )]


# ── Document → Training Pairs ──────────────────────────────────────────────────

def doc_to_training_pairs(
    doc_path: Path,
    domain: str = "general",
    persona: str = "INAN",
    max_pairs: int = 8,
) -> list[TrainingPair]:
    """
    Ubah satu dokumen markdown menjadi training pairs.
    Ini inti dari 'belajar sungguhan' — knowledge masuk ke weights via fine-tune.
    """
    try:
        text = doc_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    if len(text.strip()) < 200:
        return []

    # ── Vol 20-fu2 #8: BadStyle defense (corpus poisoning prevention) ─────
    # Per riset note 235 finding: style trigger (Bible/Legal/Shakespeare) =
    # imperceptible backdoor 90% ASR di GPT-4. Risk SIDIX: LearnAgent fetch
    # external bisa kontaminasi LoRA retrain. Filter style-anomaly + topic
    # mismatch SEBELUM corpus_to_training write to JSONL.
    try:
        from .style_anomaly_filter import is_safe_for_training
        # Has-sanad heuristik: file path mengandung "approved/" atau "sanad/"
        # (kalau corpus pipeline track sanad, override di sini)
        _has_sanad = any(marker in str(doc_path).lower() for marker in ("approved/", "sanad/", "verified/"))
        _safe, _decision = is_safe_for_training(
            text[:5000],  # sample first 5K char untuk speed
            declared_topic=domain,
            has_sanad=_has_sanad,
        )
        if not _safe:
            log.warning(
                "[corpus_to_training] BLOCKED %s: severity=%s reason=%s styles=%s",
                doc_path.name, _decision.severity, _decision.reason,
                _decision.detected_styles,
            )
            # Quarantine log untuk review manual
            try:
                from pathlib import Path as _Path
                _qpath = _Path(__file__).parent.parent / ".data" / "corpus_quarantine.jsonl"
                _qpath.parent.mkdir(parents=True, exist_ok=True)
                import json as _json
                from datetime import datetime as _dt, timezone as _tz
                with _qpath.open("a", encoding="utf-8") as _f:
                    _f.write(_json.dumps({
                        "ts": _dt.now(_tz.utc).isoformat(),
                        "doc": doc_path.name,
                        "domain": domain,
                        "decision": _decision.to_dict(),
                    }, ensure_ascii=False) + "\n")
            except Exception:
                pass
            return []  # SKIP doc, no training pairs
    except Exception as _e:
        log.debug("[corpus_to_training] style filter error (proceeding): %s", _e)

    sections = _extract_sections(text)
    if not sections:
        # Treat whole doc as one section
        heading = doc_path.stem.replace("-", " ").replace("_", " ").title()
        sections = [(heading, text)]

    source = doc_path.name
    all_pairs: list[TrainingPair] = []

    for heading, content in sections[:10]:  # max 10 sections per doc
        if len(content) < 80:
            continue

        # Generate berbagai tipe Q&A dari section ini
        all_pairs.extend(_gen_definition_pairs(heading, content, persona, source, domain))
        all_pairs.extend(_gen_howto_pairs(heading, content, persona, source, domain))
        all_pairs.extend(_gen_comparison_pairs(content, persona, source, domain))
        all_pairs.extend(_gen_concept_qa_pairs(heading, content, persona, source, domain))
        all_pairs.extend(_gen_practical_pairs(heading, content, persona, source, domain))

    # Filter: hanya pair yang cukup informatif
    good_pairs = [
        p for p in all_pairs
        if len(p.question) > 10 and len(p.answer) > 60
    ]

    # Deduplicate by question
    seen_q: set[str] = set()
    unique: list[TrainingPair] = []
    for p in good_pairs:
        qkey = p.question[:50].lower()
        if qkey not in seen_q:
            seen_q.add(qkey)
            unique.append(p)

    # Shuffle + limit
    random.shuffle(unique)
    return unique[:max_pairs]


# ── Detect domain dari path/content ───────────────────────────────────────────

def _detect_domain_from_doc(doc_path: Path, content: str) -> tuple[str, str]:
    """Returns (domain_id, persona)."""
    fname = doc_path.name.lower()
    content_l = content.lower()

    # Cek dari nama file
    checks = [
        (["mighan_creative", "ai_tools", "image_gen", "video_gen", "music"], "ai_image_gen", "MIGHAN"),
        (["python", "fastapi", "coding", "backend"], "python_programming", "HAYFAR"),
        (["web_dev", "javascript", "react", "frontend"], "web_development", "HAYFAR"),
        (["docker", "devops", "cloud", "kubernetes"], "devops_cloud", "HAYFAR"),
        (["machine_learning", "deep_learning", "ml_theory"], "machine_learning_theory", "FACH"),
        (["nlp", "transformer", "bert", "language_model"], "nlp_research", "FACH"),
        (["continual", "catastrophic", "lifelong"], "continual_learning", "FACH"),
        (["business", "strategy", "marketing"], "business_strategy", "TOARD"),
        (["entrepreneur", "startup"], "entrepreneurship", "TOARD"),
        (["project", "agile", "scrum", "okr"], "project_management", "TOARD"),
    ]

    for keywords, domain, persona in checks:
        if any(kw in fname or kw in content_l for kw in keywords):
            return domain, persona

    # Default berdasarkan content keywords
    creative_kw = ["midjourney", "stable diffusion", "dall-e", "suno", "udio", "runway"]
    tech_kw = ["python", "fastapi", "javascript", "docker", "kubernetes"]
    business_kw = ["strategy", "marketing", "business", "revenue"]
    research_kw = ["machine learning", "neural network", "transformer", "nlp"]

    scores = {
        "MIGHAN": sum(1 for k in creative_kw if k in content_l),
        "HAYFAR": sum(1 for k in tech_kw if k in content_l),
        "TOARD": sum(1 for k in business_kw if k in content_l),
        "FACH": sum(1 for k in research_kw if k in content_l),
    }

    best_persona = max(scores, key=scores.get)
    domain_map = {"MIGHAN": "ai_image_gen", "HAYFAR": "python_programming",
                  "TOARD": "business_strategy", "FACH": "machine_learning_theory"}
    return domain_map.get(best_persona, "general"), best_persona


# ── Batch corpus processor ─────────────────────────────────────────────────────

def process_corpus_to_training(
    corpus_dirs: list[Path] | None = None,
    max_pairs_per_doc: int = 8,
    output_file: Path | None = None,
    verbose: bool = True,
) -> int:
    """
    Proses SELURUH corpus → training pairs.
    Returns: total pairs yang dihasilkan.
    """
    if corpus_dirs is None:
        corpus_dirs = [
            _BRAIN_DIR / "research_notes",
            _BRAIN_DIR / "sources" / "web_clips",
            _BRAIN_DIR / "principles",
        ]

    if output_file is None:
        from datetime import date
        output_file = _TRAINING_DIR / f"corpus_training_{date.today().isoformat()}.jsonl"

    total = 0
    doc_count = 0

    if verbose:
        print("=" * 55)
        print("  SIDIX Knowledge Absorption — Corpus to Training")
        print("=" * 55)

    with open(output_file, "w", encoding="utf-8") as out:
        for corpus_dir in corpus_dirs:
            if not corpus_dir.exists():
                continue

            docs = list(corpus_dir.glob("*.md"))
            if verbose:
                print(f"\n[{corpus_dir.name}] {len(docs)} docs")

            for doc in docs:
                try:
                    content = doc.read_text(encoding="utf-8", errors="ignore")
                    domain, persona = _detect_domain_from_doc(doc, content)
                    pairs = doc_to_training_pairs(doc, domain=domain, persona=persona,
                                                 max_pairs=max_pairs_per_doc)

                    for pair in pairs:
                        out.write(json.dumps(pair.to_chatml(), ensure_ascii=False) + "\n")
                        total += 1

                    doc_count += 1
                    if verbose and pairs:
                        print(f"  [{persona}] {doc.name[:50]}: {len(pairs)} pairs")

                except Exception as e:
                    if verbose:
                        print(f"  ERROR {doc.name}: {e}")

    if verbose:
        print(f"\nTotal: {total} training pairs dari {doc_count} dokumen")
        print(f"Output: {output_file}")
        print()
        print("Next step: upload file ini ke Kaggle dataset 'sidix-sft-dataset'")
        print("           lalu jalankan ulang notebook fine-tune.")

    return total


# ── Stats ──────────────────────────────────────────────────────────────────────

def get_training_stats() -> dict:
    """Statistik semua training file yang sudah di-generate."""
    total = 0
    by_persona: dict[str, int] = {}
    by_type: dict[str, int] = {}
    files = []

    for f in sorted(_TRAINING_DIR.glob("*.jsonl"), reverse=True):
        count = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
                count += 1
                p = d.get("persona", "?")
                t = d.get("template_type", "?")
                by_persona[p] = by_persona.get(p, 0) + 1
                by_type[t] = by_type.get(t, 0) + 1
            except Exception:
                pass
        total += count
        files.append({"file": f.name, "pairs": count, "size_bytes": f.stat().st_size})

    return {
        "total_pairs": total,
        "by_persona": by_persona,
        "by_template_type": by_type,
        "files": files[:10],
        "training_dir": str(_TRAINING_DIR),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SIDIX Corpus → Training Pipeline")
    sub = parser.add_subparsers(dest="cmd")

    process_p = sub.add_parser("process", help="Proses corpus jadi training data")
    process_p.add_argument("--max-pairs", type=int, default=8, help="Max pairs per dokumen")
    process_p.add_argument("--output", type=str, default="", help="Output file (opsional)")

    sub.add_parser("stats", help="Statistik training data yang sudah di-generate")

    demo_p = sub.add_parser("demo", help="Demo ekstraksi dari satu file")
    demo_p.add_argument("file", help="Path ke file markdown")

    args = parser.parse_args()

    if args.cmd == "process":
        out = Path(args.output) if args.output else None
        n = process_corpus_to_training(max_pairs_per_doc=args.max_pairs, output_file=out)
        print(f"\nSelesai! {n} training pairs siap untuk Kaggle fine-tune.")

    elif args.cmd == "stats":
        stats = get_training_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.cmd == "demo":
        doc = Path(args.file)
        content = doc.read_text(encoding="utf-8", errors="ignore")
        domain, persona = _detect_domain_from_doc(doc, content)
        pairs = doc_to_training_pairs(doc, domain=domain, persona=persona, max_pairs=5)
        print(f"Doc: {doc.name}")
        print(f"Domain: {domain} | Persona: {persona}")
        print(f"Generated {len(pairs)} pairs:\n")
        for i, p in enumerate(pairs, 1):
            print(f"--- Pair {i} [{p.template_type}] ---")
            print(f"Q: {p.question}")
            print(f"A: {p.answer[:200]}...")
            print()

    else:
        parser.print_help()
