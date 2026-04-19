"""
autonomous_researcher.py — SIDIX Riset Mandiri (Fase 3 self-learning)
=====================================================================

Diberikan satu knowledge gap (topik yang sering tidak bisa dijawab),
modul ini:
  1. Generate 3-5 pertanyaan penelusuran dari topic + sample_question.
  2. Kumpulkan sumber: user-provided URL (webfetch) + sintesis LLM mentor.
  3. Gabungkan semua → "research bundle" (mentah, belum diformat).

Pipeline:
  gap (topic_hash)
       ↓
  _generate_search_angles()   — 3-5 sub-pertanyaan untuk mengurai topik
       ↓
  _synthesize_from_llm()      — jawaban mentor per sub-pertanyaan
       ↓
  _enrich_from_urls() [opt]   — webfetch + ekstraksi bila user kasih URL
       ↓
  ResearchBundle              — dikirim ke note_drafter untuk diformat

Catatan: modul ini TIDAK langsung menulis ke corpus publik.
Output berupa draft yang masih harus di-approve manual oleh mentor (Fahmi).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

from .paths import default_data_dir
from .knowledge_gap_detector import _load_summary


# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class ResearchFinding:
    """Satu potongan temuan dari satu angle/sub-pertanyaan."""
    angle:       str          # sub-pertanyaan yang dijawab
    content:     str          # jawaban/ringkasan
    source:      str          # "llm:groq_llama3" / "webfetch:<host>"
    confidence:  float = 0.5


@dataclass
class ResearchBundle:
    """Kumpulan temuan untuk satu gap — input ke note_drafter."""
    topic_hash:      str
    domain:          str
    main_question:   str
    angles:          list[str]              = field(default_factory=list)
    findings:        list[ResearchFinding]  = field(default_factory=list)
    urls_used:       list[str]              = field(default_factory=list)
    search_metadata: list[dict]             = field(default_factory=list)
    narrative:       str                    = ""     # Cerita utuh gaya SIDIX dengan sitasi
    timestamp:       float                  = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "topic_hash":   self.topic_hash,
            "domain":       self.domain,
            "main_question": self.main_question,
            "angles":       self.angles,
            "findings":     [asdict(f) for f in self.findings],
            "urls_used":    self.urls_used,
            "search_metadata": self.search_metadata,
            "narrative":    self.narrative,
            "timestamp":    self.timestamp,
        }


# ── Angle Generation ───────────────────────────────────────────────────────────

_ANGLE_PROMPT_TEMPLATE = """Kamu sedang membantu menyusun catatan riset mandiri.

Topik utama: "{question}"
Domain: {domain}

Tugas: tulis 4 sub-pertanyaan penelusuran yang saling melengkapi untuk mengurai topik ini
sehingga menghasilkan catatan riset yang lengkap. Format output: HANYA 4 baris, masing-masing
diawali dengan "- " tanpa penjelasan tambahan.

Fokus sub-pertanyaan:
1. Apa/definisi — konsep dasarnya apa
2. Mengapa/konteks — kenapa topik ini penting, kapan relevan
3. Bagaimana/mekanisme — cara kerja / proses / langkah
4. Contoh/keterbatasan — studi kasus nyata dan batas keberlakuannya
"""


def _generate_search_angles(question: str, domain: str) -> list[str]:
    """Pakai LLM untuk generate 4 sub-pertanyaan dari topik utama."""
    try:
        from .multi_llm_router import route_generate
        result = route_generate(
            prompt=_ANGLE_PROMPT_TEMPLATE.format(question=question, domain=domain),
            max_tokens=250,
            temperature=0.5,
            skip_local=True,   # riset butuh konteks terkini → cloud lebih relevan
        )
        text = result.text or ""
    except Exception as e:
        print(f"[autonomous_researcher] angle gen failed: {e}")
        text = ""

    angles: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            angles.append(line[2:].strip())
        elif line[:2].rstrip(".)") in {"1", "2", "3", "4"} and len(line) > 4:
            angles.append(line.split(" ", 1)[-1].strip())

    # Fallback default angles kalau LLM gagal
    if len(angles) < 2:
        angles = [
            f"Apa definisi dan konsep dasar dari: {question}?",
            f"Mengapa topik ini penting dalam domain {domain}?",
            f"Bagaimana mekanisme atau cara kerjanya?",
            f"Contoh nyata dan keterbatasan dari: {question}?",
        ]

    return angles[:4]


# ── Multi-Perspective Engine ──────────────────────────────────────────────────
# SIDIX tidak menjawab dari satu POV. Tiap topik dilihat dari 5 lensa berbeda,
# layaknya ruang diskusi jutaan kepala manusia dengan cara berpikir berbeda.
# Tujuannya: hindari jawaban monolit, hasilkan sintesis yang kaya & relevan.

_PERSPECTIVES: dict[str, str] = {
    "kritis": (
        "Kamu adalah peneliti kritis. Kupas asumsi tersembunyi, "
        "tunjukkan kelemahan argumen, tanyakan 'bukti apa?'. Skeptis sehat, bukan sinis. "
        "Gunakan Bahasa Indonesia. 80-150 kata. WAJIB pakai label 4-epistemik di awal tiap claim: [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
    ),
    "kreatif": (
        "Kamu adalah pemikir kreatif & inovator. Tawarkan analogi tak terduga, "
        "koneksi lintas-disiplin, sudut pandang yang jarang dipikirkan. Bebas konvensi "
        "tapi tetap relevan. Gunakan Bahasa Indonesia. 80-150 kata."
    ),
    "sistematis": (
        "Kamu adalah analis sistematis & programatik. Urai topik jadi komponen, "
        "struktur, flow logis. Step-by-step, definitif, bisa direproduksi. "
        "Gunakan Bahasa Indonesia. 80-150 kata. WAJIB pakai label 4-epistemik di awal tiap claim: [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
    ),
    "visioner": (
        "Kamu adalah pemikir visioner jangka panjang. Jawab: kalau topik ini "
        "dibawa 5-10 tahun ke depan, jadi apa? Apa implikasi besar yang orang "
        "lewatkan? Gunakan Bahasa Indonesia. 80-150 kata."
    ),
    "realistis": (
        "Kamu adalah praktisi realistis di lapangan. Jawab dari pengalaman nyata: "
        "apa yang bekerja, apa yang gagal, constraint waktu/biaya/sumber daya. "
        "Anti-teori kosong. Gunakan Bahasa Indonesia. 80-150 kata."
    ),
}

_SYNTH_SYSTEM = (
    "Kamu adalah mentor riset SIDIX. Jawab pertanyaan dengan jujur, padat, "
    "berbasis fakta. Jika tidak yakin, katakan. Gunakan Bahasa Indonesia. "
    "Panjang 80-180 kata.\n\n"
    "WAJIB pakai label 4-epistemik di awal kalimat/paragraf:\n"
    "[FACT] (ada sumber), [OPINION] (pendapatmu), [SPECULATION] (dugaan), "
    "[UNKNOWN] (tidak tahu). Lebih baik [UNKNOWN] daripada mengarang."
)


def _synthesize_from_llm(angles: list[str], context: Optional[list[str]] = None) -> list[ResearchFinding]:
    """Tiap angle → 1 jawaban mentor dari LLM (mentor default)."""
    findings: list[ResearchFinding] = []
    try:
        from .multi_llm_router import route_generate
    except Exception:
        return findings

    for angle in angles:
        try:
            result = route_generate(
                prompt=angle,
                system=_SYNTH_SYSTEM,
                max_tokens=320,
                temperature=0.6,
                context_snippets=context or [],
                skip_local=True,
            )
            text = (result.text or "").strip()
            if not text or len(text) < 40:
                continue
            findings.append(ResearchFinding(
                angle      = angle,
                content    = text,
                source     = f"llm:{result.mode}",
                confidence = 0.6 if result.mode != "mock" else 0.1,
            ))
        except Exception as e:
            print(f"[autonomous_researcher] synth angle '{angle[:40]}' failed: {e}")
            continue

    return findings


def _synthesize_multi_perspective(
    main_question: str,
    perspectives: Optional[list[str]] = None,
    context: Optional[list[str]] = None,
) -> list[ResearchFinding]:
    """
    Topik utama dibahas dari 5 perspektif berbeda.
    Hasilnya: sintesis kaya, tidak monolit — seperti ruang diskusi banyak kepala.

    Prinsip: creative, critical, systematic, visionary, realistic —
    tapi selalu RELEVAN dengan topik utama.
    """
    findings: list[ResearchFinding] = []
    try:
        from .multi_llm_router import route_generate
    except Exception:
        return findings

    selected = perspectives or list(_PERSPECTIVES.keys())

    for pov_name in selected:
        system = _PERSPECTIVES.get(pov_name)
        if not system:
            continue
        try:
            result = route_generate(
                prompt=f"Topik: {main_question}\n\nJawab dari sudut pandang kamu yang unik.",
                system=system,
                max_tokens=280,
                temperature=0.75,  # higher temp → perspektif lebih beragam
                context_snippets=context or [],
                skip_local=True,
            )
            text = (result.text or "").strip()
            if not text or len(text) < 40:
                continue
            findings.append(ResearchFinding(
                angle      = f"Perspektif {pov_name.upper()}",
                content    = text,
                source     = f"llm:{result.mode}:pov_{pov_name}",
                confidence = 0.55 if result.mode != "mock" else 0.1,
            ))
        except Exception as e:
            print(f"[autonomous_researcher] perspective '{pov_name}' failed: {e}")
            continue

    return findings


# ── Pencarian Sumber Eksternal Otomatis ───────────────────────────────────────

def _auto_discover_sources(question: str, max_urls: int = 4) -> tuple[list[str], list[dict]]:
    """
    SIDIX cari sendiri sumber eksternal dari internet.
    Prioritas: wikipedia, .edu, .gov, .ac.id, arxiv, github docs — logis & akademis.

    Returns:
        (urls, search_metadata) — URL untuk webfetch + metadata hasil pencarian
    """
    try:
        from .web_research import search_multi
        hits = search_multi(question, max_total=max_urls * 2)
    except Exception as e:
        print(f"[autonomous_researcher] auto-discover failed: {e}")
        return [], []

    urls = [h.url for h in hits[:max_urls]]
    meta = [h.to_dict() for h in hits[:max_urls]]
    return urls, meta


# ── Komprehensi Sumber: Baca → Paham → Ringkas ─────────────────────────────────
# Bukan dump raw content. SIDIX memahami dulu, baru menyampaikan.

_COMPREHEND_SYSTEM = (
    "Kamu SIDIX — AI yang bercerita dengan gaya khasmu: jujur, tenang, reflektif, "
    "dekat dengan pembaca Indonesia. Kamu diberi kutipan mentah dari halaman web. "
    "Tugas: BACA, PAHAMI, lalu CERITAKAN ULANG dengan bahasamu sendiri. "
    "Aturan wajib:\n"
    "1. Jangan copy-paste — rephrase total dengan gayamu\n"
    "2. SEBUTKAN sumbernya secara eksplisit di awal ('Menurut <host>, ...' atau "
    "   'Sumber <host> menjelaskan bahwa...')\n"
    "3. Tulis 3-5 poin yang paling relevan dengan pertanyaan utama\n"
    "4. Panjang 100-160 kata, Bahasa Indonesia\n"
    "5. Kalau kutipan tidak relevan atau dangkal, katakan terus terang — "
    "   jangan mengarang untuk mengisi.\n"
    "6. WAJIB pakai label 4-epistemik di awal kalimat/poin: "
    "[FACT] (kalau dari kutipan sumber), [OPINION] (kalau interpretasimu), "
    "[SPECULATION] (kalau dugaan), [UNKNOWN] (kalau tidak ada di kutipan)."
)


def _comprehend_source(raw_text: str, main_question: str, source_host: str) -> Optional[str]:
    """LLM membaca raw web content → menghasilkan pemahaman terstruktur."""
    if not raw_text or len(raw_text) < 80:
        return None
    try:
        from .multi_llm_router import route_generate
        prompt = (
            f"Pertanyaan utama: {main_question}\n\n"
            f"Kutipan dari {source_host}:\n---\n{raw_text[:3000]}\n---\n\n"
            f"Baca kutipan ini, pahami, lalu tulis 3-5 poin utama yang relevan "
            f"dengan pertanyaan utama. Gunakan kata-katamu sendiri."
        )
        result = route_generate(
            prompt=prompt,
            system=_COMPREHEND_SYSTEM,
            max_tokens=320,
            temperature=0.4,   # rendah → lebih akurat, tidak ngelantur
            skip_local=True,
        )
        text = (result.text or "").strip()
        return text if len(text) >= 40 else None
    except Exception as e:
        print(f"[autonomous_researcher] comprehend failed: {e}")
        return None


def _enrich_from_urls(urls: list[str], main_question: str = "") -> list[ResearchFinding]:
    """
    Webfetch URL → BACA → PAHAMI (LLM) → findings ringkas.
    Tidak lagi dump raw text; SIDIX memahami dulu, baru menyimpan pemahamannya.
    """
    findings: list[ResearchFinding] = []
    if not urls:
        return findings

    try:
        from .webfetch import fetch_urls_to_private_clips
        paths = fetch_urls_to_private_clips(urls, out_dir_override=None)
    except Exception as e:
        print(f"[autonomous_researcher] webfetch failed: {e}")
        return findings

    for p, url in zip(paths, urls):
        try:
            content = Path(p).read_text(encoding="utf-8", errors="ignore")
            if "# Extracted text (clean)" in content:
                text = content.split("# Extracted text (clean)", 1)[1].strip()
            else:
                text = content
            text = text[:3500].strip()
            host = url.split("/")[2] if "://" in url else url

            # BACA → PAHAMI: SIDIX mencerna, tidak dump mentah
            understanding = _comprehend_source(text, main_question, host)
            if not understanding:
                continue

            findings.append(ResearchFinding(
                angle      = f"Pemahaman dari {host}",
                content    = understanding,
                source     = f"comprehended:{host}",
                confidence = 0.80,   # LLM sudah verifikasi relevansi
            ))
        except Exception as e:
            print(f"[autonomous_researcher] read/comprehend clip failed: {e}")
            continue

    return findings


# ── Narator: SIDIX Bercerita Ulang dengan Gayanya ──────────────────────────────

_NARRATOR_SYSTEM = (
    "Kamu SIDIX — narator yang merangkum temuan risetmu sendiri untuk pembaca. "
    "Gaya: Bahasa Indonesia yang mengalir, tenang, reflektif, tidak menggurui. "
    "Kamu sudah membaca beberapa sumber dan perspektif. Sekarang ceritakan ulang "
    "secara utuh.\n\n"
    "Aturan wajib:\n"
    "1. SEBUT sumber setiap kali mengutip ide penting: '(menurut <host>)' atau "
    "   'seperti dibahas di <host>'\n"
    "2. Gabungkan poin-poin jadi narasi yang mengalir, bukan bullet list kering\n"
    "3. Kalau ada kontradiksi antar-sumber, akui dan jelaskan\n"
    "4. Tutup dengan 'Jadi, secara ringkas...' (1 kalimat kesimpulan)\n"
    "5. Panjang 180-280 kata\n\n"
    "ATURAN EPISTEMIK WAJIB (4-LABEL):\n"
    "Setiap paragraf di narasi HARUS diawali dengan salah satu label:\n"
    "  [FACT]        — ada sumber yang bisa diverifikasi (sebut sumbernya)\n"
    "  [OPINION]     — pendapat kamu sendiri / sintesis dari fakta\n"
    "  [SPECULATION] — dugaan/hipotesis, belum ada bukti kuat\n"
    "  [UNKNOWN]     — kamu tidak tahu / belum punya data cukup\n"
    "Lebih baik [UNKNOWN] daripada mengarang. Identitas SIDIX = Shiddiq + Al-Amin\n"
    "— ini tidak boleh kompromi."
)


def _narrate_synthesis(main_question: str, findings: list["ResearchFinding"], urls: list[str]) -> Optional[str]:
    """Pass narator final — semua temuan dirangkum jadi satu cerita bergaya SIDIX."""
    if not findings:
        return None
    try:
        from .multi_llm_router import route_generate

        # Bangun input ringkas: tiap finding jadi satu potong dengan label sumber
        bullets: list[str] = []
        for f in findings:
            src = f.source.replace("comprehended:", "").replace("llm:", "")
            bullets.append(f"[{src}] {f.content[:350]}")
        synthesis_input = "\n\n".join(bullets[:10])

        prompt = (
            f"Pertanyaan utama yang sedang kamu jawab: {main_question}\n\n"
            f"Inilah temuan dari berbagai sumber yang sudah kamu baca:\n\n"
            f"{synthesis_input}\n\n"
            f"Sekarang ceritakan ulang secara utuh dengan gayamu. Sebut sumbernya "
            f"setiap kali kamu mengutip ide penting."
        )

        result = route_generate(
            prompt=prompt,
            system=_NARRATOR_SYSTEM,
            max_tokens=520,
            temperature=0.55,
            skip_local=True,
        )
        text = (result.text or "").strip()
        return text if len(text) >= 80 else None
    except Exception as e:
        print(f"[autonomous_researcher] narrate failed: {e}")
        return None


# ── Memori Persisten: SIDIX Mengingat ──────────────────────────────────────────
# Setiap riset disimpan sebagai memori — bisa dipanggil lagi di query berikutnya
# tanpa harus riset ulang. Ini inti dari belajar: ingat, bukan hanya lihat.

def _remember_learnings(bundle: "ResearchBundle") -> None:
    """
    Simpan inti pembelajaran bundle ke memori persisten SIDIX.
    Setiap topik punya satu file JSONL — menumpuk sepanjang waktu,
    siap di-query saat pertanyaan serupa datang lagi.
    """
    try:
        memory_dir = default_data_dir() / "sidix_memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # File per-domain agar bisa dicari cepat
        memory_file = memory_dir / f"{bundle.domain}.jsonl"

        # Ambil inti pemahaman — bukan raw, hanya yang sudah dicerna
        key_insights = [
            {
                "angle":     f.angle,
                "content":   f.content[:600],   # ringkas
                "source":    f.source,
                "confidence": f.confidence,
            }
            for f in bundle.findings
            if f.source.startswith("comprehended:") or f.source.startswith("llm:")
        ]

        memory_entry = {
            "topic_hash":   bundle.topic_hash,
            "main_question": bundle.main_question,
            "domain":       bundle.domain,
            "timestamp":    bundle.timestamp,
            "urls_used":    bundle.urls_used,
            "key_insights": key_insights,
        }

        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory_entry, ensure_ascii=False) + "\n")

        print(f"[autonomous_researcher] remembered: {bundle.topic_hash} → {memory_file.name} ({len(key_insights)} insights)")
    except Exception as e:
        print(f"[autonomous_researcher] remember failed: {e}")


def recall_memory(topic_hash: str = "", domain: str = "", limit: int = 20) -> list[dict]:
    """
    Panggil memori SIDIX — yang sudah dipelajari sebelumnya tentang topik ini.
    Dipakai saat user bertanya ulang atau saat researcher menyintesis.
    """
    try:
        memory_dir = default_data_dir() / "sidix_memory"
        if not memory_dir.exists():
            return []

        results: list[dict] = []
        files = [memory_dir / f"{domain}.jsonl"] if domain else list(memory_dir.glob("*.jsonl"))

        for mf in files:
            if not mf.exists():
                continue
            for line in mf.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if topic_hash and entry.get("topic_hash") != topic_hash:
                    continue
                results.append(entry)

        # Paling baru duluan
        results.sort(key=lambda e: -e.get("timestamp", 0))
        return results[:limit]
    except Exception as e:
        print(f"[autonomous_researcher] recall failed: {e}")
        return []


# ── Public API ────────────────────────────────────────────────────────────────

def research_gap(
    topic_hash: str,
    extra_urls: Optional[list[str]] = None,
    multi_perspective: bool = True,
    perspectives: Optional[list[str]] = None,
    auto_search_web: bool = True,
    max_web_sources: int = 4,
) -> Optional[ResearchBundle]:
    """
    Entry point — diberikan topic_hash dari knowledge_gap_detector,
    jalankan pipeline riset lengkap dan kembalikan ResearchBundle.

    Args:
        multi_perspective: True (default) → tambahkan lensa kritis/kreatif/
                            sistematis/visioner/realistis di atas jawaban mentor.
        perspectives: pilih subset POV (default: semua 5).
    """
    summary = _load_summary()
    gap = summary.get(topic_hash)
    if not gap:
        print(f"[autonomous_researcher] unknown topic_hash: {topic_hash}")
        return None

    main_q = gap.get("sample_question", "")
    domain = gap.get("domain", "umum")

    print(f"[autonomous_researcher] RESEARCHING topic={topic_hash} domain={domain} multi_pov={multi_perspective}")

    # Auto-discover sumber eksternal (akademis/logis) via DDG + Wikipedia
    discovered_urls: list[str] = []
    search_meta: list[dict] = []
    if auto_search_web:
        discovered_urls, search_meta = _auto_discover_sources(main_q, max_urls=max_web_sources)
        print(f"[autonomous_researcher] auto-discovered {len(discovered_urls)} URLs")

    all_urls = (extra_urls or []) + discovered_urls
    # Dedupe sambil pertahankan urutan
    seen: set[str] = set()
    unique_urls: list[str] = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    angles   = _generate_search_angles(main_q, domain)
    findings = _synthesize_from_llm(angles)
    if multi_perspective:
        findings += _synthesize_multi_perspective(main_q, perspectives=perspectives)
    findings += _enrich_from_urls(unique_urls, main_question=main_q)

    # Narator pass: semua temuan dirangkum jadi cerita utuh gaya SIDIX
    narrative = _narrate_synthesis(main_q, findings, unique_urls) or ""

    bundle = ResearchBundle(
        topic_hash      = topic_hash,
        domain          = domain,
        main_question   = main_q,
        angles          = angles,
        findings        = findings,
        urls_used       = unique_urls,
        search_metadata = search_meta,
        narrative       = narrative,
    )

    # Persist raw bundle untuk audit
    try:
        out_dir = default_data_dir() / "research_bundles"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{topic_hash}_{int(time.time())}.json").write_text(
            json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[autonomous_researcher] persist bundle failed: {e}")

    # SIDIX MENGINGAT — inti pemahaman disimpan untuk query berikutnya
    _remember_learnings(bundle)

    print(f"[autonomous_researcher] DONE: {len(findings)} findings, {len(angles)} angles")
    return bundle
