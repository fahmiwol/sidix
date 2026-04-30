"""
naskh_handler.py — Penanganan Konflik Knowledge (SIDIX v0.6)

Konsep dari ushul fiqh: Naskh = mekanisme mengetahui "ayat/hadits mana
yang diperbarui oleh yang mana" — sehingga tidak ada kontradiksi tersembunyi.

Diterapkan di sini sebagai mekanisme resolve konflik antara corpus lama
dan knowledge baru, berdasarkan:
  1. Sanad tier (primer > ulama > peer_review > aggregator)
  2. Tanggal (lebih baru menang jika tier sama)
  3. Confidence score (tiebreaker akhir)
  4. Jika benar-benar konflik → KEDUANYA disimpan dengan label [CONFLICT]

Fitur diferensiasi SIDIX vs AI lain:
  - AI lain (termasuk model-model besar) sering "lupa" knowledge lama
    saat retrain. SIDIX SENGAJA mempertahankan frozen core dan hanya
    menandai knowledge baru sebagai "update" — bukan overwrite buta.

Refs:
  - brain/public/research_notes/184_naskh_handler_knowledge_conflict.md
  - docs/SIDIX_BIBLE.md (Pilar 3: Kebenaran Berlapis)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class KnowledgeItem:
    """Satu unit knowledge dalam corpus SIDIX."""
    content:     str
    source:      str                        # path, URL, atau identifier
    sanad_tier:  str                        # primer | ulama | peer_review | aggregator
    date_added:  datetime
    topic:       str                        # slug topik (untuk mencari konflik)
    confidence:  float = 1.0               # 0.0–1.0
    is_frozen:   bool = False              # True = tidak boleh digantikan (wahyu/teks primer)
    naskh_notes: list[str] = field(default_factory=list)  # riwayat resolve


# ── Tier Ranking ──────────────────────────────────────────────────────────────

_TIER_RANK: dict[str, int] = {
    "primer":      4,   # teks primer / wahyu / sumber orisinil
    "ulama":       3,   # scholar / pakar bidang
    "peer_review": 2,   # jurnal / riset terkurasi
    "aggregator":  1,   # Wikipedia, blog, agregator
}


# ── NaskhHandler ──────────────────────────────────────────────────────────────

class NaskhHandler:
    """
    Ketika knowledge baru masuk corpus dan berpotensi kontradiksi knowledge lama,
    NaskhHandler memutuskan:
      - superseded : knowledge lama digantikan (tier baru > lama)
      - updated    : sama tier, lebih baru → update
      - conflict   : sama tier & waktu → keduanya disimpan dengan label [CONFLICT]
      - retained   : knowledge lama lebih kuat → knowledge baru diabaikan

    Catatan: item dengan is_frozen=True tidak pernah di-supersede.
    """

    def resolve(
        self,
        old: KnowledgeItem,
        new: KnowledgeItem,
    ) -> tuple[KnowledgeItem, str, str]:
        """
        Resolve konflik antara dua knowledge item.

        Returns:
            (winning_knowledge, status, reason)
            status: "retained" | "superseded" | "updated" | "conflict"
        """
        # Frozen items tidak bisa digantikan
        if old.is_frozen:
            return (
                old,
                "retained",
                f"[Naskh] '{old.topic}' berstatus frozen (teks primer) — tidak dapat digantikan.",
            )

        old_rank = _TIER_RANK.get(old.sanad_tier, 0)
        new_rank = _TIER_RANK.get(new.sanad_tier, 0)

        # Rule 1: Tier lebih tinggi menang
        if new_rank > old_rank:
            winner = new
            winner.naskh_notes.append(
                f"Menggantikan sumber '{old.source}' "
                f"(tier {old.sanad_tier} → {new.sanad_tier})"
            )
            return (
                winner,
                "superseded",
                f"[Naskh] Tier lebih tinggi: {new.sanad_tier} > {old.sanad_tier}",
            )

        # Rule 2: Tier sama + tanggal lebih baru → update
        if new_rank == old_rank:
            # Tiebreaker: confidence score
            if new.confidence > old.confidence + 0.15:
                winner = new
                winner.naskh_notes.append(
                    f"Menggantikan berdasarkan confidence "
                    f"({new.confidence:.2f} vs {old.confidence:.2f})"
                )
                return (
                    winner,
                    "updated",
                    f"[Naskh] Confidence lebih tinggi: {new.confidence:.2f} > {old.confidence:.2f}",
                )

            if new.date_added > old.date_added:
                winner = new
                winner.naskh_notes.append(
                    f"Menggantikan berdasarkan tanggal "
                    f"({new.date_added.date()} > {old.date_added.date()})"
                )
                return (
                    winner,
                    "updated",
                    f"[Naskh] Lebih baru: {new.date_added.date()} > {old.date_added.date()}",
                )

            # Tier sama, confidence seimbang, tanggal mirip → CONFLICT
            conflict_new = new
            conflict_new.content = (
                f"[CONFLICT: Berbeda dengan sumber '{old.source}' "
                f"(tier {old.sanad_tier}, {old.date_added.date()})]\n"
                + new.content
            )
            conflict_new.naskh_notes.append(
                f"Konflik dengan '{old.source}' — keduanya disimpan"
            )
            return (
                conflict_new,
                "conflict",
                f"[Naskh] Tier & waktu setara — keduanya disimpan dengan label [CONFLICT]",
            )

        # Default: old lebih kuat (tier lebih tinggi)
        return (
            old,
            "retained",
            f"[Naskh] Knowledge lama dipertahankan "
            f"(tier {old.sanad_tier} >= {new.sanad_tier})",
        )

    def add_to_corpus(
        self,
        new_item: KnowledgeItem,
        existing_corpus: list[KnowledgeItem],
    ) -> tuple[list[KnowledgeItem], list[str]]:
        """
        Tambahkan item baru ke corpus dengan naskh resolution.

        Returns:
            (updated_corpus, log_messages)
        """
        logs: list[str] = []

        # Cari semua item lama dengan topic yang sama
        conflicts = [item for item in existing_corpus if item.topic == new_item.topic]

        if not conflicts:
            existing_corpus.append(new_item)
            logs.append(f"[Naskh] Topik baru ditambahkan: '{new_item.topic}'")
            return existing_corpus, logs

        for old in conflicts:
            winner, status, reason = self.resolve(old, new_item)
            logs.append(reason)

            if status in ("superseded", "updated"):
                existing_corpus = [i for i in existing_corpus if i is not old]
                existing_corpus.append(winner)
            elif status == "conflict":
                existing_corpus.append(winner)  # simpan keduanya
            # "retained" → tidak ada perubahan

        return existing_corpus, logs


# ── Helper: build dari research note ──────────────────────────────────────────

def note_to_knowledge_item(
    content: str,
    source_path: str,
    topic: str,
    sanad_tier: str = "peer_review",
    confidence: float = 0.80,
    is_frozen: bool = False,
    date_added: Optional[datetime] = None,
) -> KnowledgeItem:
    """
    Bungkus konten note menjadi KnowledgeItem siap di-resolve.
    Dipakai oleh LearnAgent + corpus ingestion pipeline.
    """
    return KnowledgeItem(
        content=content,
        source=source_path,
        sanad_tier=sanad_tier,
        date_added=date_added or datetime.now(timezone.utc),
        topic=topic,
        confidence=confidence,
        is_frozen=is_frozen,
    )
