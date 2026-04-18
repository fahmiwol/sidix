"""
note_drafter.py — Dari ResearchBundle ke Draft Research Note (Fase 3)
=====================================================================

Mengubah raw research bundle (dari autonomous_researcher) menjadi draft markdown
dalam format yang konsisten dengan `brain/public/research_notes/*.md`.

Draft TIDAK langsung publish ke corpus publik. Ia disimpan di:
  apps/brain_qa/.data/note_drafts/<draft_id>.{json,md}

Alur:
  1. draft_from_bundle(bundle)            → simpan draft pending
  2. list_drafts()                        → daftar draft untuk review mentor
  3. get_draft(draft_id)                  → ambil konten draft
  4. approve_draft(draft_id)              → publish ke research_notes/ + resolve gap
  5. reject_draft(draft_id, reason="")    → tandai rejected

Format note mengikuti konvensi proyek:
  - Filename: NNN_slug.md (nomor berikutnya)
  - Isi: Apa, Mengapa, Bagaimana, Contoh, Keterbatasan, Sumber
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

from .paths import default_data_dir, workspace_root
from .autonomous_researcher import ResearchBundle, ResearchFinding


# ── Paths ──────────────────────────────────────────────────────────────────────

_DRAFTS_DIR = default_data_dir() / "note_drafts"
_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class DraftRecord:
    draft_id:     str
    topic_hash:   str
    domain:       str
    title:        str
    slug:         str
    markdown:     str
    status:       str   = "pending"   # pending / approved / rejected
    created_at:   float = field(default_factory=time.time)
    published_as: str   = ""          # nama file kalau sudah approved
    reject_reason: str  = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Helpers ────────────────────────────────────────────────────────────────────

_SLUG_BAD = re.compile(r"[^a-zA-Z0-9]+")


def _slugify(text: str, max_len: int = 60) -> str:
    s = text.lower().strip()
    s = _SLUG_BAD.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "topik")[:max_len].rstrip("_")


def _next_note_number() -> int:
    """Cari nomor note berikutnya di brain/public/research_notes/."""
    notes_dir = workspace_root() / "brain" / "public" / "research_notes"
    if not notes_dir.exists():
        return 132
    max_n = 0
    for f in notes_dir.glob("*.md"):
        m = re.match(r"^(\d+)_", f.name)
        if m:
            try:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
            except Exception:
                continue
    return max_n + 1


def _title_from_question(q: str) -> str:
    """Ubah pertanyaan jadi judul note (tanpa tanda tanya)."""
    t = q.strip().rstrip("?").strip()
    # Strip kata tanya berulang: "apa itu", "apa yang", "bagaimana cara", dsb.
    t = re.sub(
        r"^(apa(?:\s+itu|\s+yang|\s+saja)?|apakah|bagaimana(?:\s+cara)?|"
        r"mengapa|kenapa|siapa(?:\s+yang)?|kapan|dimana|bisakah)\s+",
        "", t, flags=re.IGNORECASE,
    )
    t = t[0].upper() + t[1:] if t else "Topik"
    return t[:120]


# ── Markdown Formatter ────────────────────────────────────────────────────────

def _format_bundle_as_markdown(
    bundle: ResearchBundle,
    title:  str,
    note_number: int,
) -> str:
    """Render ResearchBundle → markdown research note."""

    findings = bundle.findings
    llm_findings = [f for f in findings if f.source.startswith("llm:") and ":pov_" not in f.source]
    pov_findings = [f for f in findings if ":pov_" in f.source]
    web_findings = [f for f in findings if f.source.startswith("webfetch:")]

    lines: list[str] = []
    lines.append(f"# {note_number}. {title}")
    lines.append("")
    lines.append(f"> **Domain**: {bundle.domain}  ")
    lines.append(f"> **Status**: Draft riset otomatis (Fase 3 self-learning)  ")
    lines.append(f"> **Pertanyaan utama**: {bundle.main_question}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Narasi SIDIX — cerita utuh dengan sitasi, gaya sendiri
    narrative = getattr(bundle, "narrative", "")
    if narrative:
        lines.append("## SIDIX Bercerita")
        lines.append("")
        lines.append("_Inilah rangkuman pemahamanku setelah membaca beberapa sumber — diceritakan ulang dengan kata-kataku sendiri._")
        lines.append("")
        lines.append(narrative)
        lines.append("")

    # Ringkasan eksekutif
    lines.append("## Poin-Poin Kunci")
    lines.append("")
    if llm_findings:
        preview = llm_findings[0].content[:400]
        lines.append(preview)
    else:
        lines.append("_Belum ada poin kunci — temuan masih kosong._")
    lines.append("")

    # Apa / Mengapa / Bagaimana / Contoh — mapping dari angles
    section_labels = ["Apa & Konsep Dasar", "Mengapa Penting", "Bagaimana Mekanismenya", "Contoh & Keterbatasan"]
    for i, finding in enumerate(llm_findings[:4]):
        label = section_labels[i] if i < len(section_labels) else f"Aspek {i+1}"
        lines.append(f"## {label}")
        lines.append("")
        lines.append(f"**Pertanyaan**: {finding.angle}")
        lines.append("")
        lines.append(finding.content)
        lines.append("")
        lines.append(f"_Sumber: {finding.source} (confidence ≈ {finding.confidence:.2f})_")
        lines.append("")

    # Perspektif beragam — jutaan kepala, banyak POV, tetap relevan
    if pov_findings:
        lines.append("## Perspektif Beragam")
        lines.append("")
        lines.append("_Topik ini dibahas dari beberapa sudut pandang yang berbeda — kritis, kreatif, sistematis, visioner, realistis — untuk menghindari jawaban monolit._")
        lines.append("")
        for pf in pov_findings:
            lines.append(f"### {pf.angle}")
            lines.append("")
            lines.append(pf.content)
            lines.append("")
            lines.append(f"_Sumber: {pf.source}_")
            lines.append("")

    # Sumber eksternal (kalau ada webfetch)
    if web_findings:
        lines.append("## Sumber Eksternal")
        lines.append("")
        for wf in web_findings:
            lines.append(f"### {wf.angle}")
            lines.append("")
            lines.append(wf.content[:800] + ("..." if len(wf.content) > 800 else ""))
            lines.append("")
            lines.append(f"_Sumber: {wf.source}_")
            lines.append("")

    if bundle.urls_used:
        lines.append("## URL Referensi")
        lines.append("")
        for u in bundle.urls_used:
            lines.append(f"- {u}")
        lines.append("")

    # Metadata pencarian (ranking domain — transparansi sumber)
    if getattr(bundle, "search_metadata", None):
        lines.append("## Hasil Pencarian Otomatis (ranked)")
        lines.append("")
        lines.append("_SIDIX mencari sendiri dari Wikipedia + DuckDuckGo, filter domain akademis/terpercaya._")
        lines.append("")
        for m in bundle.search_metadata:
            score = m.get("score", 0)
            lines.append(f"- **{m.get('title','')}** (skor: {score:.2f}, sumber: {m.get('source','')})")
            lines.append(f"  - {m.get('url','')}")
            snip = m.get("snippet", "")
            if snip:
                lines.append(f"  - _{snip[:200]}_")
        lines.append("")

    # Metadata catatan
    lines.append("---")
    lines.append("")
    lines.append("## Catatan Pembuatan")
    lines.append("")
    lines.append("Draft ini dihasilkan otomatis oleh pipeline `autonomous_researcher` + `note_drafter`")
    lines.append("sebagai respon terhadap knowledge gap yang terdeteksi berulang kali di log SIDIX.")
    lines.append("Mentor wajib review sebelum publish — verifikasi akurasi, lengkapi contoh spesifik,")
    lines.append("dan pastikan tidak ada halusinasi dari LLM mentor.")
    lines.append("")
    lines.append(f"- Topic hash: `{bundle.topic_hash}`")
    lines.append(f"- Angles dieksplorasi: {len(bundle.angles)}")
    lines.append(f"- Findings terkumpul: {len(bundle.findings)}")
    lines.append("")

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def draft_from_bundle(bundle: ResearchBundle) -> DraftRecord:
    """Bundle → DraftRecord tersimpan sebagai JSON + MD di _DRAFTS_DIR."""
    title    = _title_from_question(bundle.main_question)
    slug     = _slugify(title)
    next_n   = _next_note_number()
    markdown = _format_bundle_as_markdown(bundle, title, next_n)

    draft_id = f"draft_{int(time.time())}_{bundle.topic_hash}"
    rec = DraftRecord(
        draft_id   = draft_id,
        topic_hash = bundle.topic_hash,
        domain     = bundle.domain,
        title      = title,
        slug       = slug,
        markdown   = markdown,
    )

    # Snapshot bundle → bisa direkonstruksi saat approve untuk bangun sanad
    rec_dict = rec.to_dict()
    rec_dict["bundle_snapshot"] = bundle.to_dict()

    (_DRAFTS_DIR / f"{draft_id}.json").write_text(
        json.dumps(rec_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (_DRAFTS_DIR / f"{draft_id}.md").write_text(markdown, encoding="utf-8")

    print(f"[note_drafter] draft created: {draft_id} ({len(markdown)} chars)")
    return rec


def list_drafts(status: str = "pending") -> list[dict]:
    """List semua draft dengan status tertentu (pending/approved/rejected/all)."""
    results: list[dict] = []
    for f in sorted(_DRAFTS_DIR.glob("draft_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if status != "all" and data.get("status") != status:
            continue
        # Ringkas saja untuk list
        results.append({
            "draft_id":   data.get("draft_id"),
            "topic_hash": data.get("topic_hash"),
            "domain":     data.get("domain"),
            "title":      data.get("title"),
            "status":     data.get("status"),
            "created_at": data.get("created_at"),
            "preview":    (data.get("markdown", "") or "")[:200],
        })
    return results


def get_draft(draft_id: str) -> Optional[dict]:
    path = _DRAFTS_DIR / f"{draft_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_draft(data: dict) -> None:
    draft_id = data["draft_id"]
    (_DRAFTS_DIR / f"{draft_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def approve_draft(
    draft_id: str,
    resolve_gap_note: bool = True,
    register_hafidz:  bool = True,
) -> dict:
    """
    Approve draft → publish sebagai research note numbered + resolve gap terkait.
    Tidak menimpa file existing bila slug bentrok — auto increment nomor.

    Jika `register_hafidz=True` (default): konten final diregistrasikan ke
    Hafidz (CAS + Merkle + Erasure), dapat sanad metadata eksplisit, dan
    sanad di-embed ke bagian akhir markdown note.
    """
    data = get_draft(draft_id)
    if not data:
        return {"ok": False, "error": "draft not found"}
    if data.get("status") == "approved":
        return {"ok": False, "error": "already approved", "published_as": data.get("published_as")}

    notes_dir = workspace_root() / "brain" / "public" / "research_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_n = _next_note_number()
    slug   = data.get("slug") or _slugify(data.get("title", "topik"))
    filename = f"{note_n}_{slug}.md"
    out_path = notes_dir / filename

    # Tulis markdown — tapi update heading nomor dulu biar sinkron
    md = data.get("markdown", "")
    md = re.sub(r"^# \d+\.\s*", f"# {note_n}. ", md, count=1, flags=re.MULTILINE)

    # ── Sanad + Hafidz Integration ─────────────────────────────────────────────
    sanad_info: dict = {}
    if register_hafidz:
        try:
            from .sanad_builder import build_sanad_from_bundle, register_note_with_sanad, persist_sanad
            from .autonomous_researcher import ResearchBundle, ResearchFinding

            # Rekonstruksi bundle minimal dari draft data untuk bangun sanad
            # (draft tidak menyimpan full findings; kita bangun lightweight bundle)
            bundle_dict = data.get("bundle_snapshot") or {}
            findings_list = [
                ResearchFinding(
                    angle      = f.get("angle", ""),
                    content    = f.get("content", ""),
                    source     = f.get("source", ""),
                    confidence = float(f.get("confidence", 0.5)),
                )
                for f in bundle_dict.get("findings", [])
            ]
            bundle = ResearchBundle(
                topic_hash      = data.get("topic_hash", ""),
                domain          = data.get("domain", "umum"),
                main_question   = bundle_dict.get("main_question", ""),
                angles          = bundle_dict.get("angles", []),
                findings        = findings_list,
                urls_used       = bundle_dict.get("urls_used", []),
                search_metadata = bundle_dict.get("search_metadata", []),
                narrative       = bundle_dict.get("narrative", ""),
            )

            sanad = build_sanad_from_bundle(bundle, note_filename=filename)

            # Register ke Hafidz — store MD final (dengan heading yg sudah benar)
            register_note_with_sanad(md, sanad)

            # Embed section Sanad ke akhir markdown
            md = md.rstrip() + "\n\n---\n\n" + sanad.to_markdown_section()

            # Simpan sanad JSON terpisah
            persist_sanad(sanad, out_dir=str(default_data_dir() / "sidix_sanad"))

            sanad_info = {
                "cas_hash":     sanad.hafidz_proof.get("cas_hash", ""),
                "merkle_root":  sanad.hafidz_proof.get("merkle_root", ""),
                "isnad_length": len(sanad.isnad),
            }
        except Exception as e:
            print(f"[note_drafter] hafidz/sanad integration failed: {e}")
            sanad_info = {"error": str(e)}

    out_path.write_text(md, encoding="utf-8")

    data["status"]       = "approved"
    data["published_as"] = str(filename)
    if sanad_info:
        data["sanad"] = sanad_info
    _save_draft(data)

    # Resolve gap terkait
    if resolve_gap_note:
        try:
            from .knowledge_gap_detector import resolve_gap
            resolve_gap(data["topic_hash"], note=f"Published as {filename}")
        except Exception as e:
            print(f"[note_drafter] resolve_gap failed: {e}")

    print(f"[note_drafter] approved & published: {filename} (sanad cas={sanad_info.get('cas_hash','')[:16]}...)")
    return {
        "ok":             True,
        "published_as":   filename,
        "path":           str(out_path),
        "sanad":          sanad_info,
    }


def reject_draft(draft_id: str, reason: str = "") -> dict:
    data = get_draft(draft_id)
    if not data:
        return {"ok": False, "error": "draft not found"}
    data["status"]        = "rejected"
    data["reject_reason"] = reason
    _save_draft(data)
    print(f"[note_drafter] rejected: {draft_id} — {reason[:60]}")
    return {"ok": True, "draft_id": draft_id}


def research_and_draft(topic_hash: str, extra_urls: Optional[list[str]] = None) -> Optional[DraftRecord]:
    """Convenience: end-to-end riset + draft dalam satu panggilan."""
    from .autonomous_researcher import research_gap
    bundle = research_gap(topic_hash, extra_urls=extra_urls)
    if not bundle:
        return None
    return draft_from_bundle(bundle)
