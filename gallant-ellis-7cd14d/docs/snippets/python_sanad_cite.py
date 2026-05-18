# -*- coding: utf-8 -*-
"""
Snippet: Menambah metadata sanad/sitasi ke knowledge claim dalam format SIDIX.

Format klaim SIDIX mengikuti epistemologi Islam:
- Disiplin klaim: fact / interpretation / hypothesis / instruction
- Sanad: rantai periwayatan / sumber primer
- Maqasid relevance: relevansi terhadap maqasid syariah (opsional)

Dependensi: tidak ada (stdlib only)

Cara menggunakan:
    python python_sanad_cite.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ── Tipe klaim ─────────────────────────────────────────────────────────────────
class ClaimDiscipline(str, Enum):
    """
    Disiplin epistemologis klaim pengetahuan.

    fact        — Fakta empiris yang dapat diverifikasi
    interpretation — Penafsiran teks atau data (ta'wil / ijtihad)
    hypothesis  — Hipotesis yang belum dikonfirmasi
    instruction — Perintah / hukum normatif (amr / nahy)
    """
    FACT = "fact"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"
    INSTRUCTION = "instruction"


# ── Model sanad/sumber ─────────────────────────────────────────────────────────
@dataclass
class SanadLink:
    """
    Satu mata rantai dalam sanad (isnad).

    Attributes:
        transmitter: Nama perawi / penulis / institusi
        source_title: Judul kitab / dokumen / URL
        source_type: Tipe sumber (kitab_turath, hadith, ijmak, qiyas, modern_paper, url)
        page_or_ref:  Halaman / nomor hadith / URL fragment (opsional)
        year_hijri:   Tahun Hijriah (opsional, untuk sumber turath)
    """
    transmitter: str
    source_title: str
    source_type: str = "kitab_turath"
    page_or_ref: Optional[str] = None
    year_hijri: Optional[int] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


# ── Model klaim pengetahuan ────────────────────────────────────────────────────
@dataclass
class KnowledgeClaim:
    """
    Klaim pengetahuan dalam format SIDIX dengan metadata sanad.

    Attributes:
        claim_text:    Isi klaim (teks)
        discipline:    Disiplin klaim (ClaimDiscipline)
        sanad:         Rantai sumber (list SanadLink)
        confidence:    Tingkat kepercayaan 0.0–1.0
        maqasid_tags:  Relevansi maqasid (nafs, aql, din, nasl, mal)
        created_at:    Timestamp pembuatan (ISO 8601)
        tags:          Tag bebas untuk pencarian
    """
    claim_text: str
    discipline: ClaimDiscipline
    sanad: list[SanadLink] = field(default_factory=list)
    confidence: float = 1.0
    maqasid_tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    tags: list[str] = field(default_factory=list)

    # Validasi maqasid yang diizinkan
    VALID_MAQASID = {"din", "nafs", "aql", "nasl", "mal"}

    def add_sanad(self, link: SanadLink) -> "KnowledgeClaim":
        """Tambah satu link sanad (fluent interface)."""
        self.sanad.append(link)
        return self

    def add_maqasid(self, *tags: str) -> "KnowledgeClaim":
        """Tambah tag maqasid syariah (fluent interface)."""
        for tag in tags:
            if tag not in self.VALID_MAQASID:
                raise ValueError(
                    f"Maqasid tidak valid: '{tag}'. Pilih dari: {self.VALID_MAQASID}"
                )
            if tag not in self.maqasid_tags:
                self.maqasid_tags.append(tag)
        return self

    def to_dict(self) -> dict:
        """Konversi ke dict yang siap di-serialize ke JSON."""
        return {
            "claim_text": self.claim_text,
            "discipline": self.discipline.value,
            "confidence": self.confidence,
            "sanad": [s.to_dict() for s in self.sanad],
            "maqasid_tags": self.maqasid_tags,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Kembalikan representasi JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ── Contoh penggunaan ──────────────────────────────────────────────────────────
def main() -> None:
    # Contoh 1: Klaim fiqh dengan sanad turath
    klaim_zakat = (
        KnowledgeClaim(
            claim_text="Zakat fitrah wajib atas setiap Muslim yang merdeka, berakal, dan memiliki kelebihan makanan pokok di malam Idul Fitri.",
            discipline=ClaimDiscipline.INSTRUCTION,
            confidence=0.99,
            tags=["zakat", "fitrah", "syafi'i"],
        )
        .add_sanad(SanadLink(
            transmitter="Imam al-Nawawi",
            source_title="al-Majmu' Sharh al-Muhadhdhab",
            source_type="kitab_turath",
            page_or_ref="Juz 6, hal. 103",
            year_hijri=676,
        ))
        .add_sanad(SanadLink(
            transmitter="Ibn Hajar al-Asqalani",
            source_title="Fath al-Bari Sharh Sahih al-Bukhari",
            source_type="hadith",
            page_or_ref="Hadith no. 1503",
        ))
        .add_maqasid("din", "nafs")
    )

    print("=== Klaim 1: Fiqh Zakat Fitrah ===")
    print(klaim_zakat.to_json())

    # Contoh 2: Klaim saintifik modern (hypothesis)
    klaim_iptek = (
        KnowledgeClaim(
            claim_text="Model bahasa besar (LLM) dengan parameter 7B dapat menjalankan inferensi secara efisien di GPU consumer-grade dengan teknik QLoRA.",
            discipline=ClaimDiscipline.FACT,
            confidence=0.85,
            tags=["llm", "qlora", "inferensi"],
        )
        .add_sanad(SanadLink(
            transmitter="Dettmers et al.",
            source_title="QLoRA: Efficient Finetuning of Quantized LLMs",
            source_type="modern_paper",
            page_or_ref="arXiv:2305.14314",
        ))
        .add_maqasid("aql")
    )

    print("\n=== Klaim 2: Fakta Saintifik LLM ===")
    print(klaim_iptek.to_json())


if __name__ == "__main__":
    main()
