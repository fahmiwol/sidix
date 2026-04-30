# Contribution Policy — Corpus Publik

Dokumen ini mengatur kontribusi ke **corpus publik** yang akan di-index oleh `brain_qa`.

## Prinsip utama

- **Evidence-first**: klaim penting harus bisa ditelusuri sumbernya.
- **Sanad/provenance**: asal materi jelas (URL/judul/tanggal/lisensi).
- **Lisensi aman**: jangan salin konten berlisensi tertutup. Tulis ringkasan sendiri + tautkan sumber.
- **Safety & privacy**: tidak ada PII dan tidak ada secrets.

## Apa yang boleh ditambahkan

- Catatan riset (`brain/public/research_notes/`)
- Prinsip/metodologi (`brain/public/principles/`)
- Glossary (`brain/public/glossary/`)
- Web clips publik (`brain/public/sources/web_clips/`) — **hasil kurasi**

## Multi-perspektif (boleh) vs kontradiksi aturan (tidak boleh)

Corpus boleh memuat **berbagai perspektif** (pro/kontra, ikhtilaf, tradeoff), selama:
- setiap perspektif ditulis sebagai **perspektif** (bukan “satu-satunya kebenaran”),
- bukti/sumber dan asumsi disebut,
- dan tidak melanggar *rules/invariants* proyek (safety, lisensi, provenance).

Untuk topik yang contested, gunakan template:
- `brain/public/research_notes/00_template_contested_topic.md`

## Format minimum metadata (untuk web clips)

Setiap web clip publik idealnya punya header ringkas (boleh frontmatter `---` atau section awal) yang memuat:
- Judul sumber
- URL
- Tanggal akses (atau tanggal publikasi jika ada)
- Lisensi (jika diketahui)
- “Dipakai untuk apa” (1–2 kalimat)

## Larangan

- ❌ Copy-paste panjang dari sumber berlisensi tertutup/paywall
- ❌ Data pribadi (nama/email/nomor/invoice/credential)
- ❌ Konten ilegal atau instruksi berbahaya

## Jalur kontribusi

- Untuk konten/corpus: PR langsung ke `brain/public/**`
- Untuk plugin/connector: lihat `docs/CONTRIBUTING.md` (manual review, default disabled)

