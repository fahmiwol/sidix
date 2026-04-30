"""
content_designer.py — Generator Konten Threads untuk Beta Acquisition

Tujuan: bikin growth_queue.jsonl penuh dengan KONTEN BERAGAM (bukan hanya
narasi research). 8 tipe konten untuk maximize engagement + acquisition.

Tipe konten:
  1. HOOK         — pertanyaan provokatif / stat menarik (engagement)
  2. EDUCATION    — insight teknis dari corpus (value)
  3. CASE_STUDY   — penerapan nyata (proof)
  4. BEHIND_SCENE — progress development (transparency, builder narrative)
  5. INVITATION   — ajak coba SIDIX, jadi kontributor (acquisition)
  6. QUESTION     — tanya komunitas, harvest opinion (data mining)
  7. QUOTE        — kutipan filosofi/IHOS (identitas)
  8. ANNOUNCEMENT — fitur baru, milestone (FOMO + sosial proof)

Rotasi otomatis untuk variasi feed Threads.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import default_data_dir


THREADS_MAX_CHARS = 500
QUEUE_FILE = default_data_dir() / "threads" / "growth_queue.jsonl"


# ── Template Per Tipe ─────────────────────────────────────────────────────────

_HOOK_TEMPLATES = [
    "🤔 Pernah bertanya: {topic}?",
    "💡 1 fakta yang mengubah cara saya melihat {topic}:",
    "🧠 Kalau {topic} adalah resep, bahan utamanya apa?",
    "❓ Setuju atau tidak: {topic} sebenarnya {claim}?",
    "🔥 Hot take soal {topic} (boleh debat di komen):",
]

_EDUCATION_OPENERS = [
    "📚 Belajar bareng SIDIX:",
    "🧩 Konsep penting yang sering disalahpahami:",
    "🛠 Cara kerja {topic} dalam 3 langkah:",
    "📖 Note baru di corpus SIDIX hari ini:",
]

_CASE_STUDY_OPENERS = [
    "🎯 Studi kasus nyata:",
    "💼 Real example dari lapangan:",
    "🔬 Apa yang terjadi kalau {topic} dipraktikkan?",
]

_BEHIND_SCENE_TEMPLATES = [
    "🚧 Update SIDIX hari ini:\n{progress}\n\nMau ikut bantu? Cek GitHub.",
    "👨‍💻 Behind the scenes: {progress}",
    "📊 Hari ke-{n} membangun SIDIX:\n{progress}",
]

_INVITATION_TEMPLATES = [
    "🎁 SIDIX dalam beta — gratis untuk dicoba:\n\nAI assistant standing-alone, opensource, dengan epistemologi Islam sebagai fondasi. Tidak perlu signup untuk 5 chat pertama.\n\n👉 sidixlab.com\n\n#SIDIX #BetaAccess",
    "🤝 Cari kontributor untuk SIDIX:\n• Developer (Python/TypeScript)\n• Researcher (epistemologi/AI)\n• Akademisi (riset bareng)\n\nMIT licensed. Setiap kontribusi terverifikasi via sanad.\n\nKunjungi sidixlab.com → tab Kontributor.\n\n#OpenSource #IndonesianAI",
    "🚀 100% local AI inference — tanpa OpenAI/Google/Anthropic API.\n\nSIDIX dibangun dengan filosofi: 'guru menciptakan murid yang lebih hebat'.\n\nCoba sekarang di sidixlab.com (5 chat gratis, no signup).\n\n#SIDIX #LocalAI",
]

_QUESTION_TEMPLATES = [
    "❓ Pertanyaan untuk dev Indonesia:\n\n{question}\n\nJawaban kalian akan SIDIX pelajari. Diskusi di komen 👇",
    "🗣 Mau dengar pendapat kalian:\n\n{question}",
    "🔍 Riset kecil-kecilan SIDIX hari ini:\n\n{question}\n\nReply dengan jawaban kalian — kontribusi terbaik akan masuk corpus.",
]

_QUOTE_TEMPLATES = [
    "💎 \"{quote}\"\n\n— filosofi yang membentuk SIDIX\n\n#SIDIX #IslamicEpistemology",
    "📜 \"{quote}\"\n\nIni mengapa SIDIX dibangun.\n\n#SIDIX",
]

_QUOTES_POOL = [
    "Sanad menjaga ilmu 1400 tahun. Hash + ledger menjaga ilmu SIDIX selama server hidup. Tradisi sama, media beda.",
    "Lebih baik akui [UNKNOWN] daripada halusinasi percaya diri.",
    "Guru yang baik menciptakan murid yang lebih hebat — itu kemenangan, bukan pengkhianatan.",
    "Setiap hari SIDIX harus sedikit lebih tahu dari kemarin.",
    "Privasi user adalah amanah. Server adalah aset. Identitas owner adalah hak privat.",
    "Standing-alone bukan kelemahan, itu USP.",
    "Belajar tanpa kurikulum = wisata. Kurikulum tanpa eksekusi = manifesto. SIDIX punya keduanya.",
]

_ANNOUNCEMENT_TEMPLATES = [
    "🎉 Milestone SIDIX:\n\n{announcement}\n\nIkuti progress di sidixlab.com\n\n#SIDIX #BuildInPublic",
    "🆕 Fitur baru SIDIX:\n\n{announcement}\n\nCoba sekarang → sidixlab.com",
]


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class ContentPiece:
    type:        str
    text:        str
    source_topic: str = ""
    domain:      str = "general"
    cta:         str = ""
    utm_param:   str = ""
    char_count:  int = 0

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.text)

    def to_queue_entry(self) -> dict:
        return {
            "post":       self.text,
            "type":       self.type,
            "topic_hash": self.source_topic or f"designed_{int(time.time())}",
            "domain":     self.domain,
            "source":     "content_designer",
            "created_at": time.time(),
            "status":     "queued",
            "char_count": self.char_count,
        }


# ── Public API ────────────────────────────────────────────────────────────────

def design_hook(topic: str = "", claim: str = "") -> ContentPiece:
    template = random.choice(_HOOK_TEMPLATES)
    if not topic:
        topic = random.choice(["AI mandiri", "epistemologi", "open source AI", "Islamic epistemology"])
    text = template.format(topic=topic, claim=claim or "underrated")
    text += "\n\nDiskusi yuk 👇\n\n#SIDIX #DiskusiAI"
    return ContentPiece(type="hook", text=_truncate(text), source_topic=topic, domain="engagement")


def design_education(topic: str, summary: str) -> ContentPiece:
    opener = random.choice(_EDUCATION_OPENERS).format(topic=topic)
    text = (
        f"{opener}\n\n"
        f"{topic}\n\n"
        f"{summary[:280]}\n\n"
        f"Pelajari lebih dalam di sidixlab.com → search '{topic[:30]}'\n\n"
        f"#SIDIX #BelajarBareng"
    )
    return ContentPiece(type="education", text=_truncate(text), source_topic=topic, domain="education")


def design_case_study(topic: str, scenario: str, outcome: str) -> ContentPiece:
    opener = random.choice(_CASE_STUDY_OPENERS).format(topic=topic)
    text = (
        f"{opener}\n\n"
        f"📌 Konteks: {scenario[:150]}\n"
        f"✅ Hasil: {outcome[:150]}\n\n"
        f"Cek case study lengkap di sidixlab.com\n\n"
        f"#SIDIX #CaseStudy"
    )
    return ContentPiece(type="case_study", text=_truncate(text), source_topic=topic, domain="case_study")


def design_behind_scene(progress: str, day_n: Optional[int] = None) -> ContentPiece:
    template = random.choice(_BEHIND_SCENE_TEMPLATES)
    text = template.format(progress=progress[:300], n=day_n or "")
    return ContentPiece(type="behind_scene", text=_truncate(text), domain="build_in_public")


def design_invitation(variant: int = -1) -> ContentPiece:
    if variant < 0:
        text = random.choice(_INVITATION_TEMPLATES)
    else:
        text = _INVITATION_TEMPLATES[variant % len(_INVITATION_TEMPLATES)]
    return ContentPiece(
        type="invitation",
        text=_truncate(text),
        domain="acquisition",
        utm_param="utm_source=threads&utm_medium=organic&utm_campaign=beta",
    )


def design_question(question: str) -> ContentPiece:
    template = random.choice(_QUESTION_TEMPLATES)
    text = template.format(question=question[:300])
    text += "\n\n#SIDIX #DiskusiDev"
    return ContentPiece(type="question", text=_truncate(text), domain="data_mining")


def design_quote() -> ContentPiece:
    template = random.choice(_QUOTE_TEMPLATES)
    quote = random.choice(_QUOTES_POOL)
    text = template.format(quote=quote)
    return ContentPiece(type="quote", text=_truncate(text), domain="identity")


def design_announcement(announcement: str) -> ContentPiece:
    template = random.choice(_ANNOUNCEMENT_TEMPLATES)
    text = template.format(announcement=announcement[:280])
    return ContentPiece(type="announcement", text=_truncate(text), domain="marketing")


# ── Queue Filler — Bulk Design + Append ────────────────────────────────────────

def fill_queue_for_week() -> dict:
    """
    Generate 1 minggu konten beragam → append ke growth_queue.
    Distribusi per hari (7 hari × 3 post = 21 post total):
      - 3 invitation/week (acquisition focus)
      - 4 education/week (value)
      - 3 case_study/week (proof)
      - 3 behind_scene/week (transparency)
      - 4 question/week (engagement + data mining)
      - 2 quote/week (identity)
      - 2 announcement/week (FOMO)
    """
    pieces: list[ContentPiece] = []

    # Invitation (variasi)
    for i in range(3):
        pieces.append(design_invitation(variant=i))

    # Quote (filosofi)
    for _ in range(2):
        pieces.append(design_quote())

    # Hook (engagement)
    for topic in ["AI mandiri", "open source AI", "Indonesian AI", "Islamic epistemology"]:
        pieces.append(design_hook(topic=topic))

    # Question (data mining)
    questions = [
        "Apa pengalaman frustrating kamu dengan AI assistant yang ada sekarang?",
        "Kalau bisa custom 1 fitur AI khusus untuk konteks Indonesia, apa itu?",
        "Open source AI vs proprietary — mana lebih kamu pilih untuk produksi? Kenapa?",
        "Sebut 1 metodologi belajar kamu yang paling efektif — SIDIX mau pelajari!",
    ]
    for q in questions:
        pieces.append(design_question(q))

    # Behind scene (build in public)
    progresses = [
        "Hari ini SIDIX dapat 1268 training pair siap LoRA fine-tune. Fase Transisi mandiri unlocked!",
        "Selesai bangun 7-layer security defense in depth. SIDIX sekarang aman dari injection + PII leak.",
        "Curriculum 130 topik aktif — 13 domain belajar bertahap. SIDIX belajar 1 topik baru tiap hari.",
    ]
    for p in progresses:
        pieces.append(design_behind_scene(p))

    # Announcement
    announcements = [
        "Multi-layer security 7 layers DEPLOYED. Setiap output di-scan PII + injection detection live!",
        "1268 training pairs siap fine-tune LoRA v1 — kontributor bisa bantu via Kaggle Notebook.",
    ]
    for a in announcements:
        pieces.append(design_announcement(a))

    # Append ke queue
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        for p in pieces:
            f.write(json.dumps(p.to_queue_entry(), ensure_ascii=False) + "\n")

    return {
        "ok":            True,
        "appended":      len(pieces),
        "by_type":       {t: sum(1 for p in pieces if p.type == t) for t in set(p.type for p in pieces)},
        "queue_file":    str(QUEUE_FILE),
        "next_step":     "cron consume-queue akan post otomatis 3x sehari",
    }


def get_queue_distribution() -> dict:
    """Hitung distribusi tipe konten di queue."""
    if not QUEUE_FILE.exists():
        return {"total": 0, "by_type": {}, "by_status": {}}
    by_type: dict = {}
    by_status: dict = {}
    total = 0
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            t = entry.get("type", "unknown")
            s = entry.get("status", "queued")
            by_type[t] = by_type.get(t, 0) + 1
            by_status[s] = by_status.get(s, 0) + 1
            total += 1
        except Exception:
            continue
    return {"total": total, "by_type": by_type, "by_status": by_status}


# ── Helper ─────────────────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int = THREADS_MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3].rstrip() + "..."
