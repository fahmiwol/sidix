"""
analogical_reasoning.py — Analogical Reasoning Engine

Find familiar analogies for hard/abstract concepts.
Map domain-specific or abstract ideas to everyday familiar experiences.

Inspired by: Qiyas (Islamic legal analogy) + modern analogical reasoning research.

Use case:
- Explain hard concepts (quantum, blockchain, neural networks) with analogies
- Make technical content accessible (KHITABAH register)
- Cross-domain creative thinking

Jiwa Sprint 4 (Kimi) — 2026-04-25
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Analogy:
    """Satu analogy: source domain → target domain mapping."""
    concept: str                       # concept yang dijelaskan
    familiar_analog: str               # analogi yang familiar
    mapping: dict[str, str] = field(default_factory=dict)  # detail mapping
    source_domain: str = ""            # domain asal analogi
    confidence: float = 0.0            # how good is this analogy (0-1)
    explanation: str = ""              # why this analogy works


@dataclass
class AnalogyResult:
    """Hasil pencarian analogy untuk satu konsep."""
    concept: str
    analogies: list[Analogy]
    best_analogy: Optional[Analogy] = None
    fallback_explanation: str = ""     # kalau tidak ada analogy yang cocok


# ── Knowledge base: concept → analogy mappings ───────────────────────────────

_ANALOGY_KB: dict[str, list[dict]] = {
    # Computing & AI
    "neural network": [
        {
            "analog": "jaringan neuron di otak manusia",
            "domain": "biologi",
            "mapping": {
                "neuron": "sel syaraf",
                "weight": "kekuatan koneksi antar sel",
                "activation": "pemicu sel untuk mengirim sinyal",
                "layer": "lapisan pemrosesan di otak",
            },
            "explanation": "Sama seperti otak belajar dari pengalaman, neural network belajar dari data.",
            "confidence": 0.9,
        },
        {
            "analog": "jaringan pertemanan di sekolah — gossip menyebar dari kelas ke kelas",
            "domain": "sosial",
            "mapping": {
                "neuron": "satu siswa",
                "connection": "pertemanan",
                "signal": "gossip/informasi",
                "layer": "kelas/tingkatan",
            },
            "explanation": "Informasi mengalir melalui jaringan pertemanan, berubah di setiap lapisan.",
            "confidence": 0.7,
        },
    ],
    "blockchain": [
        {
            "analog": "buku kas kelas yang ditulis bersama dan tidak bisa dihapus",
            "domain": "sekolah",
            "mapping": {
                "block": "satu halaman buku kas",
                "chain": "urutan halaman yang saling terkait",
                "hash": "tanda tangan unik di setiap halaman",
                "consensus": "semua anggota kelas setuju sebelum mencatat",
            },
            "explanation": "Semua orang punya salinan buku yang sama, dan perubahan harus disetujui bersama.",
            "confidence": 0.85,
        },
        {
            "analog": "rantai domino — jatuhkan satu, semua tahu urutannya",
            "domain": "permainan",
            "mapping": {
                "block": "satu domino",
                "chain": "urutan domino",
                "tamper": "mencoba menyelipkan domino palsu di tengah",
            },
            "explanation": "Setiap domino bergantung pada yang sebelumnya — sulit menyelipkan tanpa ketahuan.",
            "confidence": 0.75,
        },
    ],
    "gradient descent": [
        {
            "analog": "menuruni gunung dengan mata tertutup — meraba-raba ke arah paling landai",
            "domain": "alam",
            "mapping": {
                "loss function": "ketinggian gunung",
                "gradient": "kemiringan tanah di bawah kaki",
                "learning rate": "ukuran langkah",
                "local minimum": "lembah kecil yang bukan lembah terdalam",
            },
            "explanation": "Kita tidak bisa melihat puncak, tapi kita bisa merasa kemiringan dan berjalan ke bawah.",
            "confidence": 0.9,
        },
    ],
    "attention mechanism": [
        {
            "analog": "membaca buku sambil menyorot bagian penting dengan stabilo",
            "domain": "belajar",
            "mapping": {
                "query": "apa yang sedang kita cari",
                "key": "judul/setiap paragraf",
                "value": "isi paragraf",
                "attention weight": "seberapa banyak stabilo yang dipakai",
            },
            "explanation": "Kita tidak membaca ulang seluruh buku — kita fokus pada bagian yang relevan.",
            "confidence": 0.85,
        },
    ],
    "backpropagation": [
        {
            "analog": "mengoreksi resep kue setelah mencicipi hasilnya",
            "domain": "memasak",
            "mapping": {
                "output error": "rasanya terlalu manis",
                "backward pass": "mengecek setiap bahan dari akhir ke awal",
                "weight update": "mengurangi gula di resep",
                "learning rate": "seberapa drastis perubahan resep",
            },
            "explanation": "Kesalahan di hasil akhir ditelusuri balik ke setiap bahan untuk diperbaiki.",
            "confidence": 0.88,
        },
    ],
    # Physics & Science
    "entropy": [
        {
            "analog": "kamar yang semakin berantakan kalau tidak dibersihkan",
            "domain": "rumah",
            "mapping": {
                "entropy increase": "keberantakan meningkat secara alami",
                "energy input": "usaha membersihkan",
                "equilibrium": "maksimal berantakan — tidak ada lagi yang bisa berantakan",
            },
            "explanation": "Alam semesta cenderung ke arah berantakan — butuh energi untuk menjaga teratur.",
            "confidence": 0.82,
        },
    ],
    "quantum superposition": [
        {
            "analog": "sebuah koin yang berputar di udara — belum heads, belum tails",
            "domain": "permainan",
            "mapping": {
                "superposition": "koin yang masih berputar",
                "measurement": "menangkap koin",
                "collapse": "koin jatuh — jadi heads atau tails",
                "probability": "seberapa mungkin masing-masing sisi",
            },
            "explanation": "Sebelum diukur, partikel ada di banyak keadaan sekaligus — baru 'memilih' saat diamati.",
            "confidence": 0.85,
        },
    ],
    # Islamic concepts
    "qiyas": [
        {
            "analog": "menggunakan resep kue coklat untuk membuat kue vanila — dasarnya sama, bahan berbeda",
            "domain": "memasak",
            "mapping": {
                "asl (original case)": "resep kue coklat yang sudah dikenal",
                "far' (new case)": "resep kue vanila yang baru",
                "'illah (effective cause)": "prinsip dasar pembuatan kue",
                "hukum asl": "kue coklat enak",
                "hukum far'": "kue vanila juga enak",
            },
            "explanation": "Karena prinsip dasarnya sama, hukum yang berlaku juga sama.",
            "confidence": 0.8,
        },
    ],
    "ijtihad": [
        {
            "analog": "dokter yang mendiagnosis penyakit berdasarkan gejala — tidak ada buku yang persis sama",
            "domain": "kedokteran",
            "mapping": {
                "nash (text)": "buku referensi medis",
                "qiyas (analogy)": "membandingkan gejala dengan kasus sebelumnya",
                "maslahah (welfare)": "yang terbaik untuk pasien",
                "ijtihad result": "diagnosis dan resep dokter",
            },
            "explanation": "Dokter menggunakan pengetahuan dan reasoning untuk menemukan solusi terbaik.",
            "confidence": 0.83,
        },
    ],
    # Economics
    "inflation": [
        {
            "analog": "porsi nasi goreng yang mengecil tapi harganya tetap — atau harganya naik untuk porsi sama",
            "domain": "kuliner",
            "mapping": {
                "inflation": "kenaikan harga / penyusutan porsi",
                "purchasing power": "berapa banyak nasi goreng yang bisa dibeli dengan uangmu",
                "currency": "uang yang kamu bawa",
            },
            "explanation": "Uangmu tetap jumlahnya, tapi nilai belinya menurun.",
            "confidence": 0.85,
        },
    ],
    "compound interest": [
        {
            "analog": "semut yang berkembang biak — 2 menjadi 4, 4 menjadi 8, makin lama makin cepat",
            "domain": "alam",
            "mapping": {
                "principal": "semut awal",
                "interest rate": "kecepatan berkembang biak",
                "compound": "anak semut juga berkembang biak",
                "time": "berapa lama dibiarkan",
            },
            "explanation": "Bukan hanya modal yang tumbuh — pertumbuhannya juga ikut tumbuh.",
            "confidence": 0.9,
        },
    ],
}


# ── Synonym/related concept mapping ──────────────────────────────────────────

_CONCEPT_SYNONYMS: dict[str, str] = {
    "deep learning": "neural network",
    "ann": "neural network",
    "bitcoin": "blockchain",
    "crypto": "blockchain",
    "optimizer": "gradient descent",
    "transformer attention": "attention mechanism",
    "self-attention": "attention mechanism",
    "llm": "attention mechanism",
    "training": "backpropagation",
    "learning": "backpropagation",
    "thermal dynamics": "entropy",
    "superposisi": "quantum superposition",
    "bunga berbunga": "compound interest",
    "riba": "compound interest",
}


def _normalize_concept(concept: str) -> str:
    """Normalize concept string for KB lookup."""
    normalized = concept.lower().strip().rstrip("?").rstrip(".")
    # Check synonyms
    if normalized in _CONCEPT_SYNONYMS:
        return _CONCEPT_SYNONYMS[normalized]
    return normalized


def _fuzzy_match_concept(query: str) -> str | None:
    """Fuzzy match concept dari query string."""
    q_lower = query.lower()

    # Exact match dulu
    for concept in _ANALOGY_KB:
        if concept in q_lower:
            return concept

    # Word-by-word match
    words = re.findall(r"\w+", q_lower)
    for concept in _ANALOGY_KB:
        concept_words = set(re.findall(r"\w+", concept))
        query_words = set(words)
        overlap = concept_words & query_words
        if len(overlap) >= max(1, len(concept_words) - 1):
            return concept

    return None


# ── Core function ────────────────────────────────────────────────────────────

def find_analogy(
    concept: str,
    preferred_domain: str = "",
    max_results: int = 3,
) -> AnalogyResult:
    """
    Cari analogy untuk sebuah konsep.

    Args:
        concept: konsep yang ingin dijelaskan
        preferred_domain: preferensi domain analogi (biologi, sosial, alam, dll)
        max_results: jumlah analogy maksimal yang dikembalikan

    Returns:
        AnalogyResult dengan list analogy + best match
    """
    normalized = _normalize_concept(concept)

    # Try direct lookup
    entries = _ANALOGY_KB.get(normalized, [])

    # If no direct match, try fuzzy
    if not entries:
        fuzzy = _fuzzy_match_concept(concept)
        if fuzzy:
            entries = _ANALOGY_KB.get(fuzzy, [])

    if not entries:
        return AnalogyResult(
            concept=concept,
            analogies=[],
            fallback_explanation=f"Belum ada analogy untuk '{concept}' di knowledge base.",
        )

    analogies: list[Analogy] = []
    for e in entries:
        analogy = Analogy(
            concept=concept,
            familiar_analog=e["analog"],
            mapping=e.get("mapping", {}),
            source_domain=e.get("domain", ""),
            confidence=e.get("confidence", 0.5),
            explanation=e.get("explanation", ""),
        )
        analogies.append(analogy)

    # Sort by confidence
    analogies.sort(key=lambda a: a.confidence, reverse=True)

    # Filter by preferred domain if specified
    if preferred_domain:
        domain_matches = [a for a in analogies if a.source_domain == preferred_domain]
        if domain_matches:
            analogies = domain_matches

    best = analogies[0] if analogies else None

    return AnalogyResult(
        concept=concept,
        analogies=analogies[:max_results],
        best_analogy=best,
        fallback_explanation="",
    )


def explain_with_analogy(
    concept: str,
    detail_level: str = "medium",  # "brief" | "medium" | "detailed"
    preferred_domain: str = "",
) -> str:
    """
    One-shot: generate human-readable explanation with analogy.

    Args:
        concept: konsep yang dijelaskan
        detail_level: seberapa detail penjelasannya
        preferred_domain: preferensi domain analogi

    Returns:
        String penjelasan dengan analogy
    """
    result = find_analogy(concept, preferred_domain=preferred_domain)

    if not result.best_analogy:
        return f"Konsep '{concept}' belum punya analogy di knowledge base. Penjelasan langsung: [TODO: generate direct explanation]"

    a = result.best_analogy

    if detail_level == "brief":
        return f"{concept} itu seperti {a.familiar_analog}. {a.explanation}"

    lines = [
        f"## {concept.title()}",
        f"",
        f"**Analogi:** {a.familiar_analog}",
        f"",
        f"{a.explanation}",
    ]

    if detail_level == "detailed" and a.mapping:
        lines.extend(["", "**Detail mapping:**"])
        for src, tgt in a.mapping.items():
            lines.append(f"  - {src} → {tgt}")

    return "\n".join(lines)


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Analogical Reasoning Self-Test ===\n")

    test_concepts = [
        "neural network",
        "blockchain",
        "gradient descent",
        "quantum superposition",
        "compound interest",
        "attention mechanism",
        "qiyas",
        "entropy",
        "unknown concept xyz",
    ]

    for concept in test_concepts:
        result = find_analogy(concept)
        if result.best_analogy:
            print(f"[{concept}] → {result.best_analogy.familiar_analog}")
            print(f"  confidence={result.best_analogy.confidence} | domain={result.best_analogy.source_domain}")
        else:
            print(f"[{concept}] → (no analogy found)")
        print()

    print("\n--- Brief explanations ---\n")
    for concept in ["neural network", "blockchain", "compound interest"]:
        print(explain_with_analogy(concept, detail_level="brief"))
        print()

    print("[OK] Self-test complete")
