#!/usr/bin/env python3
"""Generate docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md from Quran.com chapter API."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "PROJEK_BADAR_AL_AMIN_114_LANGKAH.md"

URL = "https://api.quran.com/api/v4/chapters?language=id"

# Satu tugas teknis per surah — dipetakan bergilir ke lima goal Projek Badar.
# G1 Q&A+web+simpulan | G2 T2I | G3 gambar | G4 kode/mini app | G5 fasih LLM/ops
TASKS: list[tuple[str, str]] = [
    # blok pola 10 x ~11 + sisa = 114
    ("G1", "Charter produk + definisi “selesai rilis”; healthcheck layanan."),
    ("G1", "Endpoint tanya-jawab: alur `no answer` → fallback pencarian web terkontrol."),
    ("G1", "Rantai simpulan: ringkas bukti → usulan → rekomendasi (dengan label ketidakpastian)."),
    ("G1", "Penalaan bahasa natural: deteksi maksud, bahasa campuran, eufemisme ringan."),
    ("G5", "Kartu eval jawaban (golden set) + regresi prompt sistem."),
    ("G1", "Sanad UI: kutip sumber RAG; mode jawaban multi-epistemik."),
    ("G2", "Pipeline text-to-image: API internal + antrian + batas ukuran."),
    ("G2", "Preset prompt visual (gaya, rasio, negatif prompt) tersimpan."),
    ("G3", "Unggah gambar → deskripsi/caption + ekstraksi teks (OCR opsional)."),
    ("G4", "Generator skrip mini (satu file) + sandbox uji aman."),
    ("G5", "Profil inferensi: kuantisasi, VRAM, timeout — dokumentasi operator."),
    ("G1", "Rate limit & antrian pengguna ramai (fairness)."),
    ("G2", "Filter keluaran gambar (NSFW/policy) + logging redaksi."),
    ("G3", "Klasifikasi jenis gambar (diagram/foto/sketsa) untuk routing model."),
    ("G4", "Template repo mini-app (HTML+JS atau Python) satu perintah."),
    ("G5", "Benchmark latensi jawaban vs target “24 jam sprint” internal."),
    ("G1", "Korpus RAG: chunk + metadata + indeks ulang otomatis."),
    ("G1", "Tool “cari di internet”: allowlist domain + kutipan + cache."),
    ("G5", "Ablation prompt: bandingkan 3 system prompt pada set kecil."),
    ("G4", "Linter + formatter + pre-commit untuk kontribusi kode."),
    ("G3", "Endpoint vision: resize, normalisasi format, batas piksel."),
    ("G2", "Integrasi adapter LoRA / style lokal untuk gambar (jika dipakai)."),
    ("G1", "Dialog multi-turn: memori sesi terbatas + tombol “lupakan sesi”."),
    ("G5", "Observabilitas: trace ID, log terstruktur, dashboard error."),
    ("G4", "Snippet coding per bahasa (Python/TS) dari contoh kurikulum internal."),
    ("G1", "Deteksi prompt injection & jawaban aman default."),
    ("G3", "Similarity gambar–teks untuk retrieval hybrid."),
    ("G2", "Batch render rendah prioritas (job malam)."),
    ("G5", "Versi model & hash adapter di `/health` + changelog."),
    ("G1", "Onboarding admin pertama + rotasi secret."),
    ("G4", "CLI operasional: backup RAG, export ledger, status GPU."),
    ("G3", "Bounding box / region crop untuk fokus analisis."),
    ("G2", "Thumbnail & kompresi hasil gambar untuk UI."),
    ("G5", "Load test ringan antrian inferensi."),
    ("G1", "Mode “hanya dari korpus” vs “boleh web” eksplisit di UI."),
    ("G4", "Scaffold API kecil (FastAPI) untuk demo tool."),
    ("G3", "Deteksi wajah/objek — matikan default bila privasi ketat."),
    ("G2", "Prompt variasi A/B untuk kualitas estetika."),
    ("G5", "Dokumentasi operator: restore dari backup volume."),
    ("G1", "Feedback pengguna: 👍/👎 ke metrik tanpa PII."),
    ("G2", "Watermark/metadata output gambar (provenansi)."),
    ("G3", "Ekstraksi tabel dari gambar (pipeline opsional)."),
    ("G4", "Unit test inti path generate + RAG retrieval."),
    ("G5", "Pin image model version di compose/prod."),
    ("G1", "Ringkasan otomatis percakapan panjang."),
    ("G2", "Color grading / palet brand untuk output konsisten."),
    ("G3", "Skor kepercayaan deskripsi vs model vision."),
    ("G4", "Patch keamanan dependensi mingguan."),
    ("G5", "Kalibrasi temperature/top-p per use case."),
    ("G1", "Deteksi bahasa masukan + balasan konsisten."),
    ("G2", "Img2img atau variasi (jika stack mendukung)."),
    ("G3", "Deteksi teks pada diagram alir (flowchart)."),
    ("G4", "Script migrasi skema RAG satu perintah."),
    ("G5", "Profil biaya token per fitur."),
    ("G1", "Kartu “tidak tahu” jujur + arahkan ke sumber."),
    ("G2", "Validasi prompt melanggar kebijakan sebelum render."),
    ("G3", "Side-by-side gambar asli vs analisis teks."),
    ("G4", "Contoh integrasi Webhook keluar (opsional)."),
    ("G5", "Checklist rilis: TLS, firewall, secret vault."),
    ("G1", "Template jawaban: fakta / opini / spekulasi."),
    ("G2", "Resolusi max & aspect ratio enforced."),
    ("G3", "Deteksi gambar low-light → saran preprocessing."),
    ("G4", "Makefile / task runner untuk dev satu perintah."),
    ("G5", "Canary route ke model baru."),
    ("G1", "Glosarium istilah proyek di RAG."),
    ("G2", "Style transfer ringan (opsional vendor OSS)."),
    ("G3", "Icon/logo detection untuk branding check."),
    ("G4", "Dokumentasi ADR satu halaman per keputusan besar."),
    ("G5", "Alarm disk penuh volume model."),
    ("G1", "Mode anak / sederhana: kalimat pendek."),
    ("G2", "Seed reproducible untuk debug gambar."),
    ("G3", "PDF halaman → gambar → caption pipeline."),
    ("G4", "Stub mock LLM untuk CI tanpa GPU."),
    ("G5", "Rotasi log & retensi."),
    ("G1", "Deteksi duplikasi pertanyaan + cache jawaban aman."),
    ("G2", "Gallery hasil + penghapusan massal."),
    ("G3", "Pose estimation opsional (matikan bila tidak perlu)."),
    ("G4", "Package docker inference-only."),
    ("G5", "Runbook insiden 1 halaman."),
    ("G1", "Export percakapan JSON redaksi PII."),
    ("G2", "Limit concurrent image job per user."),
    ("G3", "Bandingkan dua gambar (before/after)."),
    ("G4", "Script validasi env (.env.sample sync)."),
    ("G5", "Synthetic monitor uptime endpoint."),
    ("G1", "Persona “pembimbing” vs “faktual” switch."),
    ("G2", "HDR tone (opsional) — dokumen batal jika tidak dipakai."),
    ("G3", "Sketsa → teknis SVG (manual assist, bukan klaim sempurna)."),
    ("G4", "Lint markdown docs."),
    ("G5", "Quota harian user anon."),
    ("G1", "Ringkas berita web dengan sumber."),
    ("G2", "Tile tekstur untuk game/edu asset."),
    ("G3", "Baca diagram batang dari chart image."),
    ("G4", "Git tag rilis otomatis dari versi."),
    ("G5", "Dashboard biaya API pihak ketiga."),
    ("G1", "Deteksi ujaran kejam → respons netral."),
    ("G2", "Inpainting mask (fase 2 roadmap)."),
    ("G3", "Kualitas blur/sharpness score."),
    ("G4", "Lockfile dependensi UI."),
    ("G5", "Profiling satu request panjang."),
    ("G1", "FAQ statis + RAG override."),
    ("G2", "Poster layout template."),
    ("G3", "Map slide → bullet points."),
    ("G4", "Contoh plugin tool SIDIX."),
    ("G5", "Dokumentasi disaster recovery."),
    ("G1", "Mode multibahasa output eksplisit."),
    ("G2", "Sticker pack square export."),
    ("G3", "Baca papan nama jalan (OCR)."),
    ("G4", "Script seed data demo."),
    ("G5", "Hardening cookie/session WebUI."),
    ("G1", "Confidence score teks agregat."),
    ("G2", "Line art mode."),
    ("G3", "Deteksi screenshot UI app."),
    ("G4", "Coverage test minimal 40% modul kritis."),
    ("G5", "Blue/green switch inference."),
    ("G1", "Deteksi pertanyaan hukum sensitif → disclaimer."),
    ("G2", "Isometric hint prompt library."),
    ("G3", "Crop kartu nama."),
    ("G4", "Release notes template."),
    ("G5", "Capacity plan GPU bulanan."),
    ("G1", "Summarize thread Slack-style."),
    ("G2", "Mascot generator konsisten karakter."),
    ("G3", "Baca notasi musik sederhana (eksperimental)."),
    ("G4", "License compliance scan deps."),
    ("G5", "End-to-end smoke 5 menit."),
    ("G1", "Voice of customer tag pada tiket."),
    ("G2", "Storyboard 4 panel."),
    ("G3", "Medical disclaimer pada gambar medis."),
    ("G4", "SBOM export."),
    ("G5", "Postmortem template."),
    ("G1", "Final sign-off Projek Badar — semua G1–G5 hijau."),
]

# Potong tepat 114 entri (daftar di atas sengaja panjang untuk penyuntingan).
TASKS = TASKS[:114]
assert len(TASKS) == 114


# Pola makna ringkas (bergilir) — menyisipkan judul terjemah resmi; bahasa sehari-hari, bukan istilah syar‘i berat.
_MAKNA_PATTERNS: list[str] = [
    "Citra judul *{t}*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur.",
    "Nada *{t}*: seleksi satu utang teknis dan tutup dalam sprint ini.",
    "Gema *{t}*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim.",
    "Irama *{t}*: perjelas satu alur yang sering salah paham di UI atau API.",
    "Bayang *{t}*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk.",
    "Sentuhan *{t}*: perbaiki satu pesan error atau label yang membingungkan.",
    "Getaran *{t}*: uji satu skenario pinggiran yang sering dilupakan QA.",
    "Warna *{t}*: rapikan satu bagian dokumentasi yang bikin onboarding macet.",
    "Aroma *{t}*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya.",
    "Tekstur *{t}*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko.",
    "Ruang *{t}*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi.",
    "Waktu *{t}*: pasang deadline realistis untuk satu modul dependensi.",
    "Cahaya *{t}*: soroti satu metrik yang belum dimonitor operator.",
    "Suara *{t}*: kumpulkan satu umpan balik pengguna mentah → tindakan.",
    "Hening *{t}*: matikan satu jalur eksperimen yang mengganggu stabilitas.",
    "Gerak *{t}*: percepat satu path panas tanpa mengorbankan keamanan.",
    "Jeda *{t}*: sisipkan jeda/timeout yang wajar pada rantai LLM.",
    "Alih *{t}*: dokumentasikan satu fallback ketika model atau tool gagal.",
    "Tilik *{t}*: audit satu izin (token, role, secret) yang bisa disempitkan.",
    "Lapis *{t}*: tambah satu lapisan validasi input sebelum inferensi.",
    "Peta *{t}*: gambar satu diagram arsitektur yang selama ini cuma lisan.",
    "Benang *{t}*: luruskan satu rantai sanad/sumber untuk jawaban sensitif.",
    "Pintu *{t}*: kunci satu endpoint admin yang belum terlindungi.",
    "Jembatan *{t}*: sambungkan satu celah antara tim data dan tim produk.",
]


def makna_natural(trans_id: str, _name_simple: str, index: int) -> str:
    """Parafrasa ringan + metafora sprint; bukan nukilan tafsir kitab."""
    t = trans_id.replace("\\", "").strip()
    return _MAKNA_PATTERNS[index % len(_MAKNA_PATTERNS)].format(t=t)


def load_chapters() -> list[dict]:
    """Muat daftar surah: file lokal dulu, lalu API (dengan User-Agent)."""
    local = ROOT / "scripts" / "data" / "quran_chapters_id.json"
    if local.exists():
        data = json.loads(local.read_text(encoding="utf-8"))
        return data["chapters"]
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "MighanModel/114-langkah (edukatif; +https://github.com)"},
    )
    raw = urllib.request.urlopen(req, timeout=30).read()
    data = json.loads(raw.decode("utf-8"))
    return data["chapters"]


def main() -> None:
    chapters = load_chapters()
    assert len(chapters) == 114, len(chapters)

    lines: list[str] = []
    lines.append("# Projek Badar — 114 langkah rilis (Al-Amin)\n\n")
    lines.append(
        "> **Al-Amin** = *yang terpercaya* — nama etos produk: output jujur, sumber terkutip, "
        "batas kemampuan diakui.\n\n"
        "> **Projek Badar** = metafora kemenangan operasional dengan sumber daya terbatas: "
        "fokus, strategi, dan eksekusi bertahap (bukan janji teologis di repo teknis).\n\n"
        "> **“24 jam”** di sini = **ritme sprint kerja** tim, bukan literal waktu dunia untuk 114 modul.\n\n"
    )
    lines.append("## Tujuan akhir (setelah 114 modul selesai)\n\n")
    lines.append("| Kode | Goal |\n|------|------|\n")
    lines.append(
        "| **G1** | Tanya-jawab; bila tidak ada jawaban di korpus → **pencarian web** terkontrol; "
        "SIDIX dapat merangkum, memberi **kesimpulan / usul / rekomendasi** dengan label; bahasa lebih natural. |\n"
    )
    lines.append("| **G2** | **Text → image** (generasi gambar) |\n")
    lines.append("| **G3** | **Memahami / mendefinisikan gambar** (caption, OCR, klasifikasi ringan) |\n")
    lines.append("| **G4** | Menulis **baris kode & skrip** + **mini aplikasi** (scaffold aman) |\n")
    lines.append("| **G5** | **Penguasaan LLM operasional** — eval, kuantisasi, antrian, biaya, kualitas |\n\n")
    lines.append("## Sumber nama surah\n\n")
    lines.append(
        "Nama surah & urutan mengikuti **Quran.com API** "
        "(https://api.quran.com/api/v4/chapters?language=id). "
        "Snapshot data lokal: `scripts/data/quran_chapters_id.json`. "
        "Kolom *Makna ringkas* = **metafora sprint** berbahasa Indonesia (bukan kutipan tafsir). "
        "Nama surah di tabel hanya **label modul** Projek Al-Amin.\n\n"
    )
    lines.append("## Daftar 114 modul\n\n")
    lines.append(
        "| # | Surah | Makna ringkas (Indonesia natural) | Tugas teknis (checklist) | Goal |\n"
        "|---|--------|-------------------------------------|---------------------------|------|\n"
    )

    for i, ch in enumerate(chapters):
        tid = ch["translated_name"]["name"]
        name = ch["name_simple"]
        goal, task = TASKS[i]
        m = makna_natural(tid, name, i)
        lines.append(f"| {i + 1} | **{name}** | {m} | {task} | **{goal}** |\n")

    lines.append("\n## Cara pakai checklist\n\n")
    lines.append(
        "1. Centang baris di issue tracker / spreadsheet; atau buat **satu issue GitHub per baris**.\n"
        "2. Prioritas sprint: selesaikan **minimal satu baris per hari** ritme kerja, atau kelompokkan per goal (G1 dulu untuk MVP bicara).\n"
        "3. **SIDIX** = nama produk di repo ini; jika UI memakai varian ejaan, samakan di dokumentasi.\n"
    )
    lines.append("\n## Penafian\n\n")
    lines.append(
        "Dokumen ini **bukan** kitab tafsir. Untuk studi keislaman resmi merujuk ahli dan kitab tafsir "
        "yang sahih. Mapping surah → tugas rekayasa adalah **mnemonik produk** semata.\n"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
