"""
sanad_builder.py — Bangun Sanad Metadata untuk Setiap Note SIDIX
=================================================================

Filosofi: setiap pengetahuan yang masuk ke corpus SIDIX harus punya **sanad**
— rantai periwayatan — agar dapat diverifikasi asal-usulnya.

Struktur sanad (mengikuti konvensi hadith klasik):

  matn         — konten inti (note markdown)
  isnad        — rantai perawi: dari narator SIDIX ke sumber awal
  tabayyun     — catatan verifikasi (quality gate, confidence, pemeriksaan)
  hafidz_proof — CAS hash + Merkle root (bukti kriptografis integritas)

Sanad ini disimpan bersamaan ke:
  1. Hafidz ledger (untuk verifikasi lintas-node)
  2. Draft JSON (untuk audit trail lokal)
  3. Bagian frontmatter note markdown (untuk pembaca manusia)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class SanadEntry:
    """Satu simpul dalam rantai perawi."""
    role:       str           # "narrator" / "mentor_llm" / "web_source" / "corpus" / "mentor_human"
    name:       str           # "SIDIX", "Groq Llama3", "en.wikipedia.org", dll.
    via:        str = ""      # jalur/channel (misal model version, URL)
    date:       str = ""      # ISO date
    confidence: float = 0.7   # seberapa dipercaya simpul ini
    note:       str = ""      # catatan tambahan

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SanadMetadata:
    """Metadata sanad lengkap untuk satu note."""
    topic_hash:     str
    domain:         str
    main_question:  str
    matn_preview:   str                          # 200 char pertama konten
    isnad:          list[SanadEntry]             # rantai perawi
    tabayyun:       dict                         # verifikasi: findings, narrative_chars, quality_gate
    hafidz_proof:   dict = field(default_factory=dict)  # cas_hash, merkle_root, stored_at
    created_at:     float = field(default_factory=time.time)
    note_filename:  str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["isnad"] = [e.to_dict() if isinstance(e, SanadEntry) else e for e in self.isnad]
        return d

    def to_markdown_section(self) -> str:
        """Render sanad sebagai bagian bertitel di markdown note."""
        lines = []
        lines.append("## Sanad & Verifikasi")
        lines.append("")
        lines.append("_Rantai periwayatan pengetahuan ini — setiap mata rantai dapat ditelusuri._")
        lines.append("")

        # Isnad (rantai perawi)
        lines.append("### Isnad (Rantai Perawi)")
        lines.append("")
        for i, entry in enumerate(self.isnad):
            e = entry.to_dict() if isinstance(entry, SanadEntry) else entry
            arrow = " ← " if i > 0 else ""
            suffix = ""
            if e.get("via"):
                suffix += f" via `{e['via']}`"
            if e.get("date"):
                suffix += f" ({e['date']})"
            lines.append(f"{i+1}. {arrow}**{e.get('role', '?').upper()}**: {e.get('name','?')}{suffix}")
            if e.get("note"):
                lines.append(f"   _{e['note']}_")
        lines.append("")

        # Tabayyun (catatan verifikasi)
        lines.append("### Tabayyun (Verifikasi)")
        lines.append("")
        for k, v in (self.tabayyun or {}).items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

        # Hafidz proof
        if self.hafidz_proof:
            lines.append("### Hafidz Proof (Kriptografis)")
            lines.append("")
            proof = self.hafidz_proof
            if proof.get("cas_hash"):
                lines.append(f"- **CAS hash**: `{proof['cas_hash']}`")
            if proof.get("merkle_root"):
                lines.append(f"- **Merkle root**: `{proof['merkle_root']}`")
            if proof.get("stored_at"):
                dt = datetime.fromtimestamp(proof["stored_at"]).isoformat(timespec="seconds")
                lines.append(f"- **Stored at**: {dt}")
            if proof.get("shares_count"):
                lines.append(f"- **Erasure shares**: {proof['shares_count']}")
            lines.append("")
            lines.append(
                "_Verifikasi: `sha256(konten_note) == cas_hash`. "
                "Integritas kolektif diamankan oleh Merkle root yang mengikat seluruh ledger._"
            )
            lines.append("")

        return "\n".join(lines)


def build_sanad_from_bundle(bundle, note_filename: str = "") -> SanadMetadata:
    """
    Bangun SanadMetadata dari ResearchBundle (dari autonomous_researcher).

    PUBLIC-FACING: nama mentor di-mask via identity_mask.mask_identity()
    agar SIDIX terlihat standing-alone (tidak bocor identitas backbone).
    """
    from .identity_mask import mask_identity

    today = datetime.now().strftime("%Y-%m-%d")
    isnad: list[SanadEntry] = []

    # 1. Narrator SIDIX (paling dekat dengan pembaca)
    isnad.append(SanadEntry(
        role="narrator",
        name="SIDIX",
        via="sidix.synthesis_engine",
        date=today,
        confidence=0.80,
        note="menyintesis & menceritakan ulang dengan gaya Indonesia",
    ))

    # 2. Mentor reasoning engine (di-mask untuk publik)
    llm_sources = set()
    for f in bundle.findings:
        src = getattr(f, "source", "") or ""
        if src.startswith("llm:"):
            llm_sources.add(src.replace("llm:", "").split(":")[0])
        elif src.startswith("comprehended:"):
            # comprehend pakai LLM juga — simpan host web-nya
            pass

    for llm in sorted(llm_sources):
        masked = mask_identity(llm)
        isnad.append(SanadEntry(
            role="reasoning_engine",
            name=masked,
            via=f"sidix.reasoning_pool → {masked}",
            date=today,
            confidence=0.70,
            note="penulis jawaban per-angle dan per-POV",
        ))

    # 3. Sumber web (paling awal di rantai)
    web_hosts = []
    for url in bundle.urls_used or []:
        if "://" in url:
            host = url.split("/")[2]
        else:
            host = url
        if host and host not in [e.name for e in isnad]:
            web_hosts.append(host)

    # Ambil search_metadata kalau ada (punya title + score)
    for meta in bundle.search_metadata or []:
        url = meta.get("url", "")
        if not url:
            continue
        host = url.split("/")[2] if "://" in url else url
        isnad.append(SanadEntry(
            role="web_source",
            name=host,
            via=url,
            date=today,
            confidence=float(meta.get("score", 0.5)),
            note=meta.get("title", "")[:80],
        ))

    # Fallback: kalau search_metadata kosong tapi urls_used ada
    if not bundle.search_metadata and bundle.urls_used:
        for url in bundle.urls_used:
            host = url.split("/")[2] if "://" in url else url
            isnad.append(SanadEntry(
                role="web_source", name=host, via=url, date=today, confidence=0.5,
            ))

    # Tabayyun — verifikasi keadaan
    narrative_len = len(getattr(bundle, "narrative", "") or "")
    confidence_values = [getattr(f, "confidence", 0.5) for f in bundle.findings]
    avg_conf = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0.0

    tabayyun = {
        "findings_count":    len(bundle.findings),
        "narrative_chars":   narrative_len,
        "urls_referenced":   len(bundle.urls_used or []),
        "avg_confidence":    avg_conf,
        "angles_explored":   len(bundle.angles or []),
        "quality_gate":      "passed (auto-approve)" if narrative_len >= 250 and len(bundle.findings) >= 6 else "manual review",
    }

    return SanadMetadata(
        topic_hash=bundle.topic_hash,
        domain=bundle.domain,
        main_question=bundle.main_question,
        matn_preview=(getattr(bundle, "narrative", "") or "")[:200],
        isnad=isnad,
        tabayyun=tabayyun,
        hafidz_proof={},       # diisi setelah register ke Hafidz
        note_filename=note_filename,
    )


# ── Registrar: Register Note ke Hafidz + Attach Sanad ─────────────────────────

def register_note_with_sanad(
    content:       str,
    sanad:         SanadMetadata,
    data_dir:      str = ".data/hafidz",
) -> dict:
    """
    Daftarkan note ke Hafidz (CAS + Merkle + Erasure) dengan sanad sebagai metadata.
    Update sanad.hafidz_proof in-place.

    Returns dict: {cas_hash, merkle_root, stored_at, shares_count}
    """
    try:
        from .hafidz_mvp import get_hafidz_node

        node = get_hafidz_node(data_dir=data_dir)
        metadata_for_ledger = {
            "topic_hash":     sanad.topic_hash,
            "domain":         sanad.domain,
            "main_question":  sanad.main_question,
            "note_filename":  sanad.note_filename,
            "isnad_length":   len(sanad.isnad),
            "tabayyun":       sanad.tabayyun,
            "sidix_sanad_v":  1,   # versi schema
        }
        result = node.store(content, metadata=metadata_for_ledger)

        sanad.hafidz_proof = {
            "cas_hash":    result["cas_hash"],
            "merkle_root": result["merkle_root"],
            "stored_at":   result["stored_at"],
            "shares_count": len(result.get("shares", [])),
        }
        return sanad.hafidz_proof
    except Exception as e:
        print(f"[sanad_builder] register_note_with_sanad failed: {e}")
        return {"error": str(e)}


# ── Persistence: Simpan Sanad Terpisah ────────────────────────────────────────

def persist_sanad(sanad: SanadMetadata, out_dir: str = ".data/sidix_sanad") -> str:
    """Simpan sanad metadata ke JSON file (1 per note)."""
    from pathlib import Path
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    stem = sanad.note_filename.rsplit(".", 1)[0] if sanad.note_filename else sanad.topic_hash
    out = d / f"{stem}.sanad.json"
    out.write_text(json.dumps(sanad.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


def load_sanad(note_filename_or_topic_hash: str, base_dir: str = ".data/sidix_sanad") -> Optional[dict]:
    """Ambil sanad yang tersimpan untuk note tertentu."""
    from pathlib import Path
    stem = note_filename_or_topic_hash.rsplit(".", 1)[0]
    f = Path(base_dir) / f"{stem}.sanad.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None
