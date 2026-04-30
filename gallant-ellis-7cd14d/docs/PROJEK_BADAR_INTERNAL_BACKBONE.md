# Projek Badar — backbone internal (INTERNAL)

**Status:** INTERNAL — untuk tim / agen. **Bukan** copy pemasaran publik.

## Tujuan dokumen ini

Menyatukan **rujukan nilai** dan **batas narasi** agar produk (SIDIX / brain_qa / Badar) tetap konsisten: ilmu ber-sanad, own-stack, dan komunikasi ke publik yang **ilmiah / metafora**, bukan kampanye identitas agama.

## Rujukan teks (Al-Qur’an, Al-Baqarah 1–5)

Tim menyetujui bahwa **Al-Qur’an** menjadi pedoman etika kerja dan kerangka berpikir (bukan menggantikan disiplin ilmu teknis). Kutipan berikut disimpan sebagai **referensi**; **bukan** dokumen tafsir produk.

- **Alif Lām Mīm.** (2:1)
- **ذَلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِلْمُتَّقِينَ** — Kitab ini tidak ada keraguan padanya; petunjuk bagi orang-orang yang bertakwa. (2:2)
- Ayat 2:3–5 menggambarkan ciri **orang yang bertakwa**: beriman kepada yang gaib, mendirikan salat, menginfakkan rezeki, beriman kepada wahyu yang diturunkan kepada Nabi dan kitab sebelumnya, yakin kepada akhirat; mereka yang mendapat petunjuk dan beruntung.

**Terjemah ringkas** (ringkasan makna, bukan produk tafsir): keteguhan pada kebenaran yang tidak goyah, konsistensi amal rutin, transparansi sumber, dan orientasi akibat jangka panjang — dipetakan ke kerja teknis sebagai **integritas data**, **proses berulang yang dapat diaudit**, **sanad / kutipan**, dan **evaluasi dampak**.

## “Smart contract” dan backbone (metafora operasional)

Dalam dokumen internal proyek, istilah **smart contract** dipakai **secara metafora** untuk:

- manifest rilis / konfigurasi yang **immutable** setelah ditandatangani (hash, tag git, manifest artefak);
- aturan otomatis CI/CD yang **menolak** deploy bila tes / audit gagal;
- ledger / bukti (mis. Merkle, CID) yang tidak boleh diubah tanpa jejak.

Jika suatu saat ada **kontrak hukum** atau **rantai blok** nyata, itu harus didokumentasikan terpisah dengan definisi hukum; jangan mencampur metafora dengan klaim legal tanpa tinjauan.

## Batas narasi ke publik

- **Jangan** menjadikan sudut “keislaman” sebagai angle pemasaran utama atau headline sensasional.
- **Ya:** jelaskan sistem dengan **terminologi ilmiah**, **metafora arsitektur** (sanad, korpus, validasi, provenans), dan **manfaat teknis** (RAG, evaluasi, own-stack).
- Materi **114 langkah** di `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` adalah **checklist sprint** ber-nama surah; **bukan** tafsir Al-Qur’an.

## Tautan kerja

- `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` — master 114 baris.
- `docs/PROJEK_BADAR_BATCH_CURSOR_50.md`, `docs/PROJEK_BADAR_BATCH_CLAUDE_54.md`, `docs/PROJEK_BADAR_BATCH_SISA_10.md` — pecahan urut dependensi.
- `docs/HANDOFF_CLAUDE_PROJEK_BADAR_54.md` — prompt operasional untuk agen Claude.
- `AGENTS.md` — own-stack inference; API vendor hanya jika user memerintahkan eksplisit.
