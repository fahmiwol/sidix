# Prompt permohonan bantuan ke Claude (siap tempel)

Salin **seluruh blok di bawah** (dari `---MULAI---` sampai `---SELESAI---`) ke percakapan Claude.

---

## ---MULAI---

Assalamu’alaikum. Saya Fahmi / pemilik arah proyek **Mighan Model** (SIDIX + `brain_qa`). Saya akan tidur dan menyerahkan pekerjaan batch **Projek Badar** kepadamu.

**Mohon bantuanmu** untuk mengeksekusi **54 tugas** yang sudah diurutkan menurut dependensi kasar, dengan tetap menjaga **tujuan produk** (bukan sekadar menyelesaikan daftar). Saya percaya kamu bisa bekerja hati-hati: **jangan hapus folder**, **jangan pindah atau ubah struktur folder** tanpa izin eksplisit dari saya.

### Yang saya minta kamu lakukan

1. Baca dulu **`docs/PROJEK_BADAR_GOALS_ALIGNMENT.md`** — ini kontrak: batchmu harus **mendekatkan repo ke G1–G5** + etos **Al-Amin** + **own-stack** (`AGENTS.md`).
2. Kerjakan **54 baris** di **`docs/PROJEK_BADAR_BATCH_CLAUDE_54.md`** (# kerja 51–104). Satu baris = satu hasil konkret (kode/skrip/tes/dok operasional) + sebut **goal Gx** + **bukti** (perintah uji atau ringkasan di log).
3. Rujukan internal nilai & batas narasi publik: **`docs/PROJEK_BADAR_INTERNAL_BACKBONE.md`**. Ke publik: **metafora ilmiah**, bukan angle pemasaran keislaman berlebihan.
4. Setelah pekerjaan bermakna: **append** **`docs/LIVING_LOG.md`** (tag wajib: `IMPL:` / `FIX:` / `DOC:` / dll.). Perbarui **`docs/CHANGELOG.md`** bila perlu.
5. **Inference inti:** default stack kami sendiri; jangan jadikan API Claude/OpenAI/Gemini sebagai default arsitektur kecuali saya tulis eksplisit untuk POC (lihat `AGENTS.md`).
6. **10 tugas sisa** ada di **`docs/PROJEK_BADAR_BATCH_SISA_10.md`** — **jangan** kerjakan kecuali saya minta lanjut; fokus **54** dulu.

### Konteks teknis singkat

- Produk UI: **SIDIX**. Backend/RAG: **`apps/brain_qa/`** — CLI `python -m brain_qa`.
- Master 114 modul: **`docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md`** (makna kolom = metafora sprint, bukan tafsir).
- Orientasi repo: **`docs/00_START_HERE.md`**, **`docs/STATUS_TODAY.md`**.
- Log feeding SIDIX: **`brain/public/research_notes/31_sidix_feeding_log.md`**.
- OSS lokal opsional: **`jariyah-hub/`** (tanpa secret di repo).

### Instruksi operasional detail (wajib ikuti)

Kamu adalah agen pengembang pada repositori **Mighan Model** (root contoh: `D:\MIGHAN Model` — sesuaikan path lokalmu). Proyek fokus: **SIDIX** + **`brain_qa`** (RAG, sanad/kutipan, ledger, storage terdistribusi), own-stack inference sesuai `AGENTS.md`.

**Tujuan kerja batchmu bukan “habiskan 54 baris”, melainkan mendekatkan repo ke outcome G1–G5** yang didefinisikan di `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` dan dijabarkan per batch di `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md`. Setiap tugas yang kamu selesaikan harus punya: **goal (Gx)**, **artefak**, **bukti uji atau log**, selaras own-stack.

**Fundamental & batas narasi**

- Tim menyandarkan **etika dan kerangka berpikir** pada Al-Qur’an; rujukan ringkas internal ada di `docs/PROJEK_BADAR_INTERNAL_BACKBONE.md` (termasuk konteks Al-Baqarah 1–5 sebagai **referensi**, bukan tafsir produk).
- **Ke publik / pemasaran:** jangan gunakan angle “keislaman” berlebihan. Sampaikan dengan **metafora ilmiah** dan **terminologi sistem** (validasi sumber, provenans, korpus, evaluasi).
- Istilah **smart contract** di dokumen internal dipakai **metafora** untuk manifest rilis / aturan CI-immutable / bukti hash — jangan campur dengan klaim hukum blockchain kecuali ada dokumen hukum terpisah.

**Aturan keras operasional**

1. **Jangan menghapus folder** atau isi besar secara destruktif.
2. **Jangan memindahkan atau mengubah struktur folder** tanpa izin eksplisit pemilik repo.
3. **Inference inti:** default **own-stack**; API Claude/OpenAI/Gemini hanya jika user memerintahkan eksplisit untuk POC (lihat `AGENTS.md`).
4. Setelah perubahan bermakna: tambahkan entri di **`docs/LIVING_LOG.md`** (append-only, tag wajib). Perbarui **`docs/CHANGELOG.md`** bila perlu ringkasan rilis.

**Tugasmu: 54 item (urut dependensi)**

Kerjakan **tepat 54 tugas** yang tercantum dalam file:

**`docs/PROJEK_BADAR_BATCH_CLAUDE_54.md`**

Kolom **# kerja** 51–104 adalah urutan eksekusi yang disepakati (dependensi kasar: G1 → G5 → G4 → G2 → G3). Kolom **Asal #** adalah nomor surah asal di master 114 baris — gunakan untuk lacak konteks di `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` bila perlu.

Untuk **setiap** baris:

1. Terjemahkan “Tugas teknis” menjadi **hasil konkret** (kode, skrip, tes, atau dokumen operasional) yang cocok dengan repo ini.
2. Jika tugas sudah terpenuhi sebagian, **perketat / rapikan / uji** — jangan duplikasi besar tanpa manfaat.
3. Prioritaskan **`apps/brain_qa/`**, **`SIDIX_USER_UI/`**, **`docs/`**, **`scripts/`** — sesuai isi baris.
4. **Jangan** mengubah narasi publik menjadi kampanye agama; tetap pada manfaat teknis dan metodologi.

**Setelah 54 selesai (opsional)**

File **`docs/PROJEK_BADAR_BATCH_SISA_10.md`** berisi 10 tugas sisa (# kerja 105–114). Lakukan hanya jika pemilik repo memintamu melanjutkan atau serahkan ke Cursor.

**Verifikasi**

Sebelum mengklaim selesai: jalankan smoke yang relevan (mis. `python -m brain_qa --help` atau tes yang sudah ada di repo) untuk area yang kamu sentuh; catat hasil di `docs/LIVING_LOG.md`.

Terima kasih. Wassalamu’alaikum.

## ---SELESAI---

File ini juga bisa dibuka di repo: `docs/PROMPT_PERMINTAAN_BANTUAN_CLAUDE_MALAM_INI.md`.
