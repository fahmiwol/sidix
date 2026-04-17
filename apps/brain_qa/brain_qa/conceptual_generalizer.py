"""
conceptual_generalizer.py — SIDIX Core Abstraction Module

Filosofi:
    "SIDIX cuma tau awalnya 1+1=2, tapi langsung paham KONSEP-nya.
     Oh berarti 2+200=202. Dari sedikit ilmu langsung paham semuanya.
     Bukan dari CARA tapi dari KONSEP dan FILOSOFIS."
                                                              — Fahmi

Tiga primitif kognitif (ilm al-ushul → furu'):
    1. EXTRACT       : examples → principle (istiqra' / induksi)
    2. GENERALIZE    : principle + new input → prediction (tatbiq al-asl)
    3. ANALOGIZE     : source_concept + target_domain → mapping (qiyas)

Storage: .data/concepts/concepts.jsonl + .data/concepts/hierarchy.json

Referensi akademik:
    - Hofstadter — "Analogy as the Core of Cognition"
    - Chollet — ARC-AGI: measuring skill-acquisition efficiency
    - Lake et al. — Bayesian Program Learning
    - Ibn Rushd — Fasl al-Maqal: qiyas sebagai bridging induktif-deduktif

Catatan: JANGAN import openai/anthropic/genai. Heuristic + regex saja.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import default_data_dir


# ── Storage paths ─────────────────────────────────────────────────────────────

def _concepts_dir() -> Path:
    d = default_data_dir() / "concepts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _concepts_file() -> Path:
    return _concepts_dir() / "concepts.jsonl"


def _hierarchy_file() -> Path:
    return _concepts_dir() / "hierarchy.json"


_LOCK = threading.RLock()


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Concept:
    id: str
    principle_statement: str            # natural language statement of principle
    domain: str                         # math | logic | language | physics | islamic | programming | ...
    examples: list[dict] = field(default_factory=list)
    invariants: dict = field(default_factory=dict)   # {operator, arity, type, structure}
    conditions: list[str] = field(default_factory=list)  # when does principle apply
    counter_examples: list[dict] = field(default_factory=list)
    confidence: float = 0.5
    parent_ids: list[str] = field(default_factory=list)   # upward in hierarchy (more general)
    child_ids: list[str] = field(default_factory=list)    # downward (more specific)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Analogy:
    source_concept_id: str
    target_domain: str
    mapping: dict           # {from_symbol: to_symbol, ...}
    illah: str              # 'illah (shared underlying reason) — qiyas style
    confidence: float = 0.5
    narrative: str = ""     # "Penjumlahan bilangan ↔ penggabungan set" narrative
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Prediction:
    prediction: Any
    reasoning_trace: list[str]
    confidence: float
    assumed_conditions: list[str]
    concept_id: str

    def to_dict(self) -> dict:
        return asdict(self)


# ── Concept ID ────────────────────────────────────────────────────────────────

def _concept_id_from_principle(principle: str, domain: str) -> str:
    """Stable hash → dedup idempotent."""
    h = hashlib.sha256(f"{domain}::{principle.strip().lower()}".encode("utf-8")).hexdigest()
    return f"cpt_{h[:12]}"


# ── Persistence (atomic, thread-safe) ─────────────────────────────────────────

def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def save_concept(concept: Concept) -> bool:
    """Append concept jika belum ada (dedup by id). Return True jika baru ditulis."""
    with _LOCK:
        existing = load_concept(concept.id)
        if existing is not None:
            return False
        path = _concepts_file()
        line = json.dumps(concept.to_dict(), ensure_ascii=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return True


def load_all_concepts() -> list[Concept]:
    path = _concepts_file()
    if not path.exists():
        return []
    out: list[Concept] = []
    with _LOCK:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(Concept(**d))
            except Exception:
                continue
    return out


def load_concept(concept_id: str) -> Concept | None:
    for c in load_all_concepts():
        if c.id == concept_id:
            return c
    return None


def save_hierarchy(tree: dict) -> None:
    with _LOCK:
        _atomic_write(_hierarchy_file(), json.dumps(tree, ensure_ascii=False, indent=2))


def load_hierarchy() -> dict:
    path = _hierarchy_file()
    if not path.exists():
        return {"nodes": [], "edges": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"nodes": [], "edges": []}


# ── EXTRACT: examples → Concept ───────────────────────────────────────────────

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
_OP_PATTERNS = [
    ("add",      re.compile(r"\s*\+\s*")),
    ("subtract", re.compile(r"(?<=\d)\s*-\s*(?=\d)")),
    ("multiply", re.compile(r"\s*[\*x×]\s*")),
    ("divide",   re.compile(r"\s*[/÷]\s*")),
    ("power",    re.compile(r"\s*\^\s*|\s*\*\*\s*")),
]


def _detect_numeric_operator(input_str: str) -> str | None:
    for name, pat in _OP_PATTERNS:
        if pat.search(input_str):
            return name
    return None


def _numeric_apply(op: str, operands: list[float]) -> float | None:
    try:
        if op == "add":
            return sum(operands)
        if op == "subtract":
            out = operands[0]
            for x in operands[1:]:
                out -= x
            return out
        if op == "multiply":
            out = 1.0
            for x in operands:
                out *= x
            return out
        if op == "divide":
            out = operands[0]
            for x in operands[1:]:
                if x == 0:
                    return None
                out /= x
            return out
        if op == "power":
            if len(operands) != 2:
                return None
            return operands[0] ** operands[1]
    except Exception:
        return None
    return None


_OP_NAME_ID = {
    "add":      ("penjumlahan", "Penjumlahan bilangan: output = jumlah total input"),
    "subtract": ("pengurangan", "Pengurangan bilangan: output = operand_1 - operand_2 - ..."),
    "multiply": ("perkalian",   "Perkalian bilangan: output = hasil kali semua input"),
    "divide":   ("pembagian",   "Pembagian bilangan: output = operand_1 / operand_2 / ..."),
    "power":    ("pangkat",     "Pemangkatan bilangan: output = basis^eksponen"),
}


def extract_concept_from_examples(examples: list[dict], domain_hint: str = "") -> Concept:
    """
    Induksi sederhana (istiqra'): cari invariant operator/struktur dari N examples.

    examples: [{"input": "1+1", "output": "2"}, {"input": "3+5", "output": "8"}]

    Strategi:
      1. Coba deteksi numeric operator yang konsisten.
      2. Jika ya → bentuk principle_statement + verifikasi di semua example.
      3. Kalau tidak, fallback ke generic pattern description.
    """
    if not examples:
        raise ValueError("extract_concept_from_examples: examples kosong")

    ops_seen: list[str | None] = []
    all_numeric = True
    for ex in examples:
        inp = str(ex.get("input", ""))
        op = _detect_numeric_operator(inp)
        ops_seen.append(op)
        if op is None:
            all_numeric = False

    # Case 1: all-numeric dengan operator konsisten
    if all_numeric and len(set(ops_seen)) == 1 and ops_seen[0] is not None:
        op = ops_seen[0]
        op_name, principle = _OP_NAME_ID[op]
        # Verifikasi: hitung ulang dan bandingkan
        verified = 0
        for ex in examples:
            operands = [float(x) for x in _NUM_RE.findall(str(ex["input"]))]
            expected = _numeric_apply(op, operands)
            try:
                actual = float(str(ex["output"]).strip())
            except Exception:
                actual = None
            if expected is not None and actual is not None and abs(expected - actual) < 1e-9:
                verified += 1
        conf = verified / len(examples)

        domain = domain_hint or "math"
        cid = _concept_id_from_principle(principle, domain)
        invariants = {
            "operator": op,
            "operator_name": op_name,
            "arity": "n-ary" if op in ("add", "multiply") else "binary",
            "input_type": "number",
            "output_type": "number",
        }
        conditions = [
            "Semua operand adalah bilangan (int/float)",
            "Operator yang sama berlaku untuk semua contoh",
        ]
        if op == "divide":
            conditions.append("Operand pembagi ≠ 0")

        return Concept(
            id=cid,
            principle_statement=principle,
            domain=domain,
            examples=list(examples),
            invariants=invariants,
            conditions=conditions,
            counter_examples=[],
            confidence=conf,
            tags=[op_name, "aritmatika", "binary_op"],
        )

    # Case 2: generic fallback — treat input/output as strings
    domain = domain_hint or "general"
    # Cari pola "panjang output selalu sama dengan panjang input" dsb.
    len_eq = all(len(str(ex.get("output", ""))) == len(str(ex.get("input", ""))) for ex in examples)
    principle = (
        "Transformasi string (pola belum dispesialisasi): input → output"
        if not len_eq
        else "Transformasi length-preserving: output memiliki panjang sama dengan input"
    )
    cid = _concept_id_from_principle(principle, domain)
    return Concept(
        id=cid,
        principle_statement=principle,
        domain=domain,
        examples=list(examples),
        invariants={"length_preserving": len_eq},
        conditions=["Heuristic fallback — belum ada operator-level abstraction"],
        counter_examples=[],
        confidence=0.3,
        tags=["generic", "string_transform"],
    )


# ── GENERALIZE: Concept + new_input → Prediction ──────────────────────────────

def generalize(concept: Concept, new_input: Any) -> Prediction:
    """Terapkan prinsip ke input baru. Return prediksi + reasoning trace."""
    trace: list[str] = []
    trace.append(f"Prinsip dimuat: {concept.principle_statement}")
    trace.append(f"Domain: {concept.domain}")

    op = concept.invariants.get("operator") if concept.invariants else None
    inp_str = str(new_input)

    if op and op in _OP_NAME_ID:
        trace.append(f"Operator invariant terdeteksi: {op}")
        operands = [float(x) for x in _NUM_RE.findall(inp_str)]
        if not operands:
            return Prediction(
                prediction=None,
                reasoning_trace=trace + ["Tidak bisa parse operand numerik."],
                confidence=0.0,
                assumed_conditions=concept.conditions,
                concept_id=concept.id,
            )
        trace.append(f"Operand ter-parse: {operands}")
        result = _numeric_apply(op, operands)
        trace.append(f"Menerapkan {op} → {result}")
        pred = int(result) if (result is not None and result.is_integer()) else result
        return Prediction(
            prediction=pred,
            reasoning_trace=trace,
            confidence=min(1.0, concept.confidence),
            assumed_conditions=concept.conditions,
            concept_id=concept.id,
        )

    # Fallback string-level: tidak ada operator — return echo dengan catatan
    trace.append("Tidak ada operator numerik dalam concept. Fallback: echo input.")
    return Prediction(
        prediction=inp_str,
        reasoning_trace=trace,
        confidence=concept.confidence * 0.5,
        assumed_conditions=concept.conditions
        + ["Generalisasi fallback — hasil mungkin tidak akurat"],
        concept_id=concept.id,
    )


# ── ANALOGIZE: qiyas — cari 'illah yang sama antar-domain ─────────────────────

# Peta sederhana 'illah → mapping antar domain. Dibangun dari prinsip umum.
_ANALOGY_KB: list[dict] = [
    {
        "illah": "kombinasi aditif yang mempertahankan total",
        "operator": "add",
        "domains": {
            "math":        {"symbol": "+",        "name": "penjumlahan bilangan"},
            "set_theory":  {"symbol": "∪",        "name": "penggabungan set"},
            "cognition":   {"symbol": "merge",    "name": "pertemuan/fusi ide"},
            "economy":     {"symbol": "+",        "name": "agregasi aset"},
            "physics":     {"symbol": "Σ",        "name": "superposisi gaya sejajar"},
        },
    },
    {
        "illah": "replikasi/penggandaan struktur",
        "operator": "multiply",
        "domains": {
            "math":        {"symbol": "×",        "name": "perkalian bilangan"},
            "biology":     {"symbol": "mitosis",  "name": "pembelahan sel"},
            "economy":     {"symbol": "compound", "name": "bunga majemuk"},
            "cognition":   {"symbol": "copy",     "name": "peniruan pola"},
        },
    },
    {
        "illah": "pengurangan/pemisahan elemen",
        "operator": "subtract",
        "domains": {
            "math":        {"symbol": "-",        "name": "pengurangan bilangan"},
            "set_theory":  {"symbol": "\\",       "name": "selisih himpunan"},
            "physics":     {"symbol": "ΔE",       "name": "pelepasan energi"},
        },
    },
]


def detect_analogy(concept_a: Concept, target_domain: str) -> Analogy | None:
    """
    Qiyas-style analogy: cari 'illah yang sama, lalu petakan ke target_domain.
    Return None bila tidak ada analogi yang ditemukan.
    """
    op = concept_a.invariants.get("operator") if concept_a.invariants else None
    source_domain = concept_a.domain

    for entry in _ANALOGY_KB:
        if entry.get("operator") != op:
            continue
        domains = entry["domains"]
        if target_domain not in domains or source_domain not in domains:
            # masih coba jika source match walau via heuristic
            if target_domain not in domains:
                continue
        src = domains.get(source_domain) or next(iter(domains.values()))
        tgt = domains[target_domain]
        narrative = (
            f"{src['name']} ↔ {tgt['name']} — "
            f"keduanya berbagi 'illah: {entry['illah']}"
        )
        return Analogy(
            source_concept_id=concept_a.id,
            target_domain=target_domain,
            mapping={src["symbol"]: tgt["symbol"], "source_name": src["name"], "target_name": tgt["name"]},
            illah=entry["illah"],
            confidence=0.7,
            narrative=narrative,
        )
    return None


# ── ABSTRACT HIERARCHY: bangun tree dari list concept ─────────────────────────

# Hirarki manual: child → parent (label → label). Untuk bootstrap.
_HIERARCHY_RULES: dict[str, str] = {
    "penjumlahan": "operasi_biner_aritmatika",
    "pengurangan": "operasi_biner_aritmatika",
    "perkalian":   "operasi_biner_aritmatika",
    "pembagian":   "operasi_biner_aritmatika",
    "pangkat":     "operasi_biner_aritmatika",
    "operasi_biner_aritmatika": "transformasi",
    "komutatif":   "sifat_operasi",
    "asosiatif":   "sifat_operasi",
    "identitas_nol": "sifat_operasi",
    "sifat_operasi": "transformasi",
    "modus_ponens":  "aturan_inferensi",
    "kontrapositif": "aturan_inferensi",
    "hukum_identitas": "aturan_inferensi",
    "aturan_inferensi": "transformasi",
}


def abstract_hierarchy(concepts: list[Concept]) -> dict:
    """
    Bangun ConceptTree sederhana: nodes + edges (child→parent).
    Gunakan tag/label sebagai proxy label dalam _HIERARCHY_RULES.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()
    virtual_parents: set[str] = set()

    for c in concepts:
        if c.id in seen_ids:
            continue
        seen_ids.add(c.id)
        nodes.append({"id": c.id, "label": (c.tags[0] if c.tags else c.domain), "principle": c.principle_statement})

        label = c.tags[0] if c.tags else ""
        parent_label = _HIERARCHY_RULES.get(label)
        while parent_label:
            vid = f"virt_{parent_label}"
            if vid not in virtual_parents:
                virtual_parents.add(vid)
                nodes.append({"id": vid, "label": parent_label, "principle": f"(abstraksi) {parent_label}"})
            edges.append({"from": c.id if label == (c.tags[0] if c.tags else "") else f"virt_{label}",
                          "to": vid, "relation": "is_a"})
            label = parent_label
            parent_label = _HIERARCHY_RULES.get(label)

    tree = {"nodes": nodes, "edges": edges, "generated_at": datetime.now(timezone.utc).isoformat()}
    save_hierarchy(tree)
    return tree


# ── LEARN FROM RESEARCH NOTE ─────────────────────────────────────────────────

_HEAD_RE = re.compile(r"(?im)^##+\s*(apa|mengapa|bagaimana|contoh|keterbatasan)\b.*$")


def concept_from_research_note(note_path: str) -> list[Concept]:
    """
    Parse research note (markdown) dengan pola apa/mengapa/bagaimana.
    Ekstrak minimal 1 concept dari statement 'apa' (principle) + 'mengapa' (reason).
    """
    p = Path(note_path)
    if not p.exists():
        raise FileNotFoundError(f"Research note tidak ada: {note_path}")
    text = p.read_text(encoding="utf-8")

    # Ambil heading + paragraf setelahnya.
    sections: dict[str, str] = {}
    last_key = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _HEAD_RE.match(line)
        if m:
            if last_key is not None:
                sections[last_key] = "\n".join(buf).strip()
            last_key = m.group(1).lower()
            buf = []
        else:
            if last_key is not None:
                buf.append(line)
    if last_key is not None:
        sections[last_key] = "\n".join(buf).strip()

    principle = sections.get("apa") or ""
    reason = sections.get("mengapa") or ""
    how = sections.get("bagaimana") or ""

    if not principle:
        # Fallback: judul file + paragraf pertama
        title = p.stem.replace("_", " ")
        first_para = next((s.strip() for s in text.split("\n\n") if s.strip() and not s.startswith("#")), title)
        principle = f"{title}: {first_para[:200]}"

    # Potong principle ke 1 kalimat utama
    first_sentence = re.split(r"(?<=[.!?])\s+", principle.strip())[0][:240] or principle[:240]
    domain = "research_note"
    cid = _concept_id_from_principle(first_sentence, domain)

    concept = Concept(
        id=cid,
        principle_statement=first_sentence,
        domain=domain,
        examples=[],
        invariants={"source_note": p.name},
        conditions=[reason[:200]] if reason else [],
        counter_examples=[],
        confidence=0.5,
        tags=["from_note", p.stem[:40]],
    )
    return [concept]


# ── SEED CONCEPTS (20 foundasional) ───────────────────────────────────────────

_SEED_SPECS: list[dict] = [
    # Matematika
    {"principle": "Penjumlahan bilangan: output = jumlah total input", "domain": "math",
     "invariants": {"operator": "add", "operator_name": "penjumlahan"}, "tags": ["penjumlahan", "aritmatika"]},
    {"principle": "Perkalian bilangan: output = hasil kali semua input", "domain": "math",
     "invariants": {"operator": "multiply", "operator_name": "perkalian"}, "tags": ["perkalian", "aritmatika"]},
    {"principle": "Identitas nol: x + 0 = x untuk setiap bilangan x", "domain": "math",
     "invariants": {"neutral_element": 0, "operator": "add"}, "tags": ["identitas_nol", "sifat_operasi"]},
    {"principle": "Komutatif: a ∘ b = b ∘ a berlaku untuk operator tertentu", "domain": "math",
     "invariants": {"property": "commutative"}, "tags": ["komutatif", "sifat_operasi"]},
    {"principle": "Asosiatif: (a ∘ b) ∘ c = a ∘ (b ∘ c) berlaku untuk operator tertentu", "domain": "math",
     "invariants": {"property": "associative"}, "tags": ["asosiatif", "sifat_operasi"]},

    # Logika
    {"principle": "Modus ponens: jika P→Q dan P benar, maka Q benar", "domain": "logic",
     "invariants": {"rule": "modus_ponens"}, "tags": ["modus_ponens", "aturan_inferensi"]},
    {"principle": "Kontrapositif: P→Q ekuivalen dengan ¬Q→¬P", "domain": "logic",
     "invariants": {"rule": "contrapositive"}, "tags": ["kontrapositif", "aturan_inferensi"]},
    {"principle": "Hukum identitas: A = A untuk setiap A (prinsip tidak-kontradiksi dasar)", "domain": "logic",
     "invariants": {"rule": "identity"}, "tags": ["hukum_identitas", "aturan_inferensi"]},

    # Bahasa
    {"principle": "Subjek-predikat: klausa minimal terdiri dari subjek (pelaku) dan predikat (aksi/keadaan)", "domain": "language",
     "invariants": {"structure": "S+P"}, "tags": ["subjek_predikat", "sintaksis"]},
    {"principle": "Konteks-makna: makna kata bergantung pada konteks (pragmatik mendominasi)", "domain": "language",
     "invariants": {"principle": "context_dependency"}, "tags": ["konteks_makna", "pragmatik"]},
    {"principle": "Polisemi: satu kata dapat memiliki banyak makna terkait", "domain": "language",
     "invariants": {"relation": "one_to_many"}, "tags": ["polisemi", "semantik"]},

    # Fisika
    {"principle": "Sebab-akibat: setiap efek memiliki setidaknya satu sebab yang mendahului", "domain": "physics",
     "invariants": {"relation": "causal"}, "tags": ["sebab_akibat", "kausalitas"]},
    {"principle": "Konservasi: kuantitas tertentu (energi, momentum, muatan) tetap konstan dalam sistem tertutup", "domain": "physics",
     "invariants": {"principle": "conservation"}, "tags": ["konservasi", "invariansi"]},
    {"principle": "Gradien: perubahan besaran per unit posisi menentukan arah aliran (panas/potensial/massa)", "domain": "physics",
     "invariants": {"operator": "gradient"}, "tags": ["gradien", "kalkulus_vektor"]},

    # Islamic
    {"principle": "Niat (niyyah): amal bergantung pada niatnya — inti penentu nilai amal", "domain": "islamic",
     "invariants": {"rule": "intention_determines_value"}, "tags": ["niat", "ushul"]},
    {"principle": "Ushul-furu': cabang (furu') diturunkan dari prinsip dasar (ushul)", "domain": "islamic",
     "invariants": {"structure": "principle_to_branch"}, "tags": ["ushul_furu", "ushul"]},
    {"principle": "Qiyas: analogi hukum dari kasus ber-nash ke kasus baru via 'illah yang sama", "domain": "islamic",
     "invariants": {"rule": "analogy_by_illah"}, "tags": ["qiyas", "ushul"]},
    {"principle": "Maslahah-mafsadah: timbang manfaat vs mudharat; dahulukan yang lebih besar", "domain": "islamic",
     "invariants": {"rule": "weigh_benefit_harm"}, "tags": ["maslahah_mafsadah", "maqasid"]},
    {"principle": "Sadd dzari'ah: tutup jalan menuju keburukan, walau jalannya sendiri netral", "domain": "islamic",
     "invariants": {"rule": "preempt_harm"}, "tags": ["sadd_dzariah", "maqasid"]},

    # Pemrograman
    {"principle": "Abstraksi: sembunyikan detail, ekspos interface — yang penting apa, bukan bagaimana", "domain": "programming",
     "invariants": {"principle": "abstraction"}, "tags": ["abstraksi", "software_engineering"]},
    {"principle": "Komposisi: fungsi kecil digabung membentuk fungsi besar — f(g(x))", "domain": "programming",
     "invariants": {"operator": "compose"}, "tags": ["komposisi", "software_engineering"]},
    {"principle": "Idempoten: menjalankan operasi berulang hasilnya sama dengan menjalankan sekali", "domain": "programming",
     "invariants": {"property": "idempotent"}, "tags": ["idempoten", "software_engineering"]},
    {"principle": "Fail-safe: sistem harus gagal dengan aman — degradasi terkontrol, bukan kerusakan meluas", "domain": "programming",
     "invariants": {"property": "fail_safe"}, "tags": ["fail_safe", "software_engineering"]},
]


def seed_foundational_concepts(force: bool = False) -> dict:
    """Tulis 20+ concept fondasi ke storage. Idempoten."""
    existing_ids = {c.id for c in load_all_concepts()}
    written = 0
    skipped = 0
    for spec in _SEED_SPECS:
        cid = _concept_id_from_principle(spec["principle"], spec["domain"])
        if cid in existing_ids and not force:
            skipped += 1
            continue
        c = Concept(
            id=cid,
            principle_statement=spec["principle"],
            domain=spec["domain"],
            examples=spec.get("examples", []),
            invariants=spec.get("invariants", {}),
            conditions=spec.get("conditions", []),
            counter_examples=[],
            confidence=0.85,
            tags=spec.get("tags", []),
        )
        if save_concept(c):
            written += 1
        else:
            skipped += 1
    return {"written": written, "skipped": skipped, "total_specs": len(_SEED_SPECS)}


# ── RETRIEVAL FOR ReAct PRE-CONTEXT ───────────────────────────────────────────

def search_concepts(query: str, top_k: int = 3) -> list[Concept]:
    """Simple keyword/tag overlap search. Return top_k concept yang relevan."""
    q = query.lower()
    q_tokens = set(re.findall(r"[a-z\u00c0-\u024f]+", q))
    if not q_tokens:
        return []
    scored: list[tuple[float, Concept]] = []
    for c in load_all_concepts():
        text_blob = f"{c.principle_statement} {c.domain} {' '.join(c.tags)}".lower()
        tokens = set(re.findall(r"[a-z\u00c0-\u024f]+", text_blob))
        if not tokens:
            continue
        overlap = len(q_tokens & tokens)
        if overlap == 0:
            continue
        score = overlap + c.confidence * 0.5
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def format_concepts_for_pre_context(concepts: list[Concept]) -> str:
    """Format untuk injection ke ReAct pre_context block."""
    if not concepts:
        return ""
    lines = ["Prinsip umum yang mungkin berlaku:"]
    for c in concepts:
        lines.append(f"  • {c.principle_statement} (confidence {c.confidence:.2f}, domain={c.domain})")
    return "\n".join(lines)


# ── SANITY TEST ───────────────────────────────────────────────────────────────

def run_sanity_test() -> dict:
    """Smoke test: extract → generalize → analogize. Simpan report ke .data/concepts/sanity_test.json."""
    report: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "cases": []}

    # Case 1: extract penjumlahan
    examples = [{"input": "1+1", "output": "2"}, {"input": "3+5", "output": "8"}, {"input": "10+20", "output": "30"}]
    c_add = extract_concept_from_examples(examples, domain_hint="math")
    save_concept(c_add)
    report["cases"].append({
        "case": "extract_add",
        "principle": c_add.principle_statement,
        "confidence": c_add.confidence,
        "ok": c_add.invariants.get("operator") == "add" and c_add.confidence >= 0.99,
    })

    # Case 2: generalize 2+200
    pred = generalize(c_add, "2+200")
    report["cases"].append({
        "case": "generalize_2_plus_200",
        "input": "2+200",
        "prediction": pred.prediction,
        "expected": 202,
        "ok": pred.prediction == 202,
        "trace": pred.reasoning_trace,
    })

    # Case 3: generalize 100+500
    pred2 = generalize(c_add, "100+500")
    report["cases"].append({
        "case": "generalize_100_plus_500",
        "prediction": pred2.prediction,
        "expected": 600,
        "ok": pred2.prediction == 600,
    })

    # Case 4: generalize multiply (extract dulu)
    mul_examples = [{"input": "2*3", "output": "6"}, {"input": "4*5", "output": "20"}]
    c_mul = extract_concept_from_examples(mul_examples, domain_hint="math")
    save_concept(c_mul)
    pred3 = generalize(c_mul, "7*8")
    report["cases"].append({
        "case": "generalize_7_x_8",
        "prediction": pred3.prediction,
        "expected": 56,
        "ok": pred3.prediction == 56,
    })

    # Case 5: analogy add → set_theory
    ana = detect_analogy(c_add, "set_theory")
    report["cases"].append({
        "case": "analogy_add_to_set_theory",
        "analogy": ana.to_dict() if ana else None,
        "ok": ana is not None,
    })

    # Case 6: analogy add → cognition
    ana2 = detect_analogy(c_add, "cognition")
    report["cases"].append({
        "case": "analogy_add_to_cognition",
        "analogy": ana2.to_dict() if ana2 else None,
        "ok": ana2 is not None,
    })

    # Case 7: analogy multiply → economy
    ana3 = detect_analogy(c_mul, "economy")
    report["cases"].append({
        "case": "analogy_multiply_to_economy",
        "analogy": ana3.to_dict() if ana3 else None,
        "ok": ana3 is not None,
    })

    # Hierarchy build
    tree = abstract_hierarchy(load_all_concepts())
    report["hierarchy_nodes"] = len(tree["nodes"])
    report["hierarchy_edges"] = len(tree["edges"])

    passed = sum(1 for c in report["cases"] if c.get("ok"))
    report["summary"] = {"passed": passed, "total": len(report["cases"]),
                          "all_pass": passed == len(report["cases"])}
    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    out_path = _concepts_dir() / "sanity_test.json"
    _atomic_write(out_path, json.dumps(report, ensure_ascii=False, indent=2))
    report["report_path"] = str(out_path)
    return report


# ── Public API (untuk serve.py) ───────────────────────────────────────────────

__all__ = [
    "Concept", "Analogy", "Prediction",
    "extract_concept_from_examples",
    "generalize",
    "detect_analogy",
    "abstract_hierarchy",
    "concept_from_research_note",
    "seed_foundational_concepts",
    "search_concepts",
    "format_concepts_for_pre_context",
    "save_concept",
    "load_concept",
    "load_all_concepts",
    "load_hierarchy",
    "run_sanity_test",
]
