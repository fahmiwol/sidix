# Quran Lab

[English](README.md)

Quran Lab adalah provider SIDIX lokal yang berisi **168 kajian** pembacaan ayat
Al-Qur'an sebagai analogi struktural untuk rekayasa dan desain AI. Snapshot ini
memiliki **33 prinsip lintas-kajian**, **16 lensa**, lapisan **Qur'anic Cognitive
Architecture (QCA)**, dan cakupan sekitar **302 ayat**. Sebagian besar teks kajian
berbahasa Indonesia. Paket berjalan luring dengan Python 3.11+ dan pustaka
standarnya: tidak memerlukan instalasi, unduhan, runtime model, atau layanan jaringan.

## Status dan batasan

Setiap kajian adalah draf LLM di bawah arahan Fahmi Ghani. **Belum ada yang
ditinjau ahli/ulama.** Aplikasi asal memberi seluruh 168 kajian label `published`;
paket ini memberi label **`draft-llm-unreviewed`** dan menambahkan penyangkalan
bahasa Indonesia/Inggris pada setiap kajian dan hasil pencarian/pengambilan data.

Ini adalah interpretasi rekayasa, **bukan tafsir, bukan fatwa, dan bukan otoritas
agama**. Ia mengusulkan resonansi struktural, bukan mukjizat numerik atau ilmiah.
Pembacaan yang diwarisi tetap berupa draf, termasuk klaim yang perlu diperbaiki.
Validasi struktur bukan tinjauan ahli. Baca [penyangkalan lengkap](DISCLAIMER.md).

## Ringkasan metode

1. Landaskan makna agama pada tafsir bersumber terlebih dahulu, termasuk
   konteksnya, sebelum mengusulkan pembacaan rekayasa. Pisahkan makna bersumber
   dari interpretasi; analogi tidak menggantikan makna itu atau mengklaim
   sebagai satu-satunya maksud ayat.
2. Gunakan lensa yang relevan pada perilaku manusia, ciptaan, teks, dan alam.
   QCA memetakan pembacaan ke lapisan kognitif yang diusulkan; ia merupakan
   kerangka interpretasi.
3. Prinsip lintas-kajian membutuhkan sedikitnya **dua kajian independen**.
   Pola berulang mendorong hipotesis desain, bukan membuktikan suatu mekanisme.
4. Jaga **tanzih**: Dzat dan Sifat Allah tidak pernah menjadi analogi, peran,
   komponen, atau properti teknis sistem. Jaga **ghaib**: baca perkara ghaib
   secara deskriptif dari sumber, tanpa mengarang rincian yang tidak dinyatakan.
5. Tandai analogi terbatas dan perbedaan pendapat, pertahankan riwayat revisi,
   dan mintalah tinjauan yang kompeten. Jangan menetapkan hukum agama dari rekayasa.

Ringkasan ini mengikuti metode `tadabbur-lab` dari Lab asal. Isinya menjelaskan
syarat metode, bukan pengesahan bahwa setiap draf telah memenuhinya.

## Data dan lisensi

Kode serta data dan dokumentasi karya Lab [berlisensi MIT](LICENSE),
Copyright (c) 2026 Fahmi Ghani. Kutipan dari Terjemah Kemenag RI, Tafsir
Kemenag RI, Tafsir al-Jalalayn, dan edisi lain tetap menjadi hak penerbitnya
dan **tidak tercakup MIT**. Kutipan tetap disertakan dengan atribusi untuk
komentar/pembahasan. Baca [NOTICE.md](NOTICE.md) dan
[QUOTATIONS_REPORT.md](QUOTATIONS_REPORT.md) sebelum menggunakan ulang data.

Impor mengubah status, menambahkan penyangkalan, membersihkan label edisi yang
merujuk antarmuka aplikasi sambil mempertahankan rujukan ayat, dan mengganti
nama asisten dalam `authors` (termasuk penulis revisi) dengan `LLM draft`.
Makna kajian dan kutipan Kemenag dipertahankan. `taxonomy.json`,
`synthesis.json`, dan `coverage.json` disalin dari sumber. Di `index.json`, medan
`title` dan `theme` dibangun ulang dari berkas kajian, karena indeks aplikasi asal
sudah melenceng dari kajiannya sendiri (27 tema dan 8 judul berbeda); berkas kajian
adalah catatan kanonik. Ligatur hormat ﷺ, yang dipakai di enam ringkasan, adalah
satu-satunya karakter aksara Arab yang diizinkan di kajian. `ayah_counts.json`
berisi 114 bilangan bulat hasil menghitung ayat di setiap berkas surah sumber,
dengan total 6.236. Arsip aplikasi asal serta berkas terjemahan/tafsir lengkap
tidak disertakan.

Teks Arab Al-Qur'an tidak disertakan. Dapatkan dari penerbitnya, misalnya Tanzil
dengan atribusi atau KFGQPC, sesuai ketentuan mereka. Taksonomi yang disalin
tetap memuat istilah kognitif Arab individual.

## Penggunaan

Dari root repositori, masuk ke direktori provider. Tanpa langkah instalasi:

```sh
cd providers/quran-lab
python -m quran_lab search "tabayyun"
python -m quran_lab search "verification" --k 3
python -m quran_lab get hujurat-49-6
python -m quran_lab verse 49 6
python -m quran_lab principles verify
python -m quran_lab principles
python -m quran_lab validate
```

Perintah menghasilkan JSON. Validasi menghasilkan `[]` dan keluar dengan kode 0
jika bersih; pelanggaran menghasilkan kode 1. Id kajian yang tidak ada dan nomor
ayat yang tidak valid menghasilkan galat JSON dan kode 1. Kesalahan argumen/cara
pemakaian mengikuti format bantuan parser baris perintah standar.

Python, dari direktori yang sama (atau tambahkan direktori itu ke `PYTHONPATH`):

```python
from quran_lab import load_lab, search, get_study, studies_for_verse, principles

hits = search("tabayyun", k=5)
study = get_study("hujurat-49-6")
nearby = studies_for_verse(49, 6)
rules = principles("verify")
lab = load_lab()  # Lab di-cache; len(lab) == 168; lab.studies mengembalikan salinan
# Opsional: lab = load_lab("path/to/data")
# Objek Lab menyediakan empat metode kueri yang sama.
```

Pencarian memakai indeks BM25 buatan tangan atas judul, subjudul, tema, inferensi,
pembacaan lensa, dan pernyataan prinsip yang dilekatkan pada kajian buktinya.
Tokenisasi pencarian mengabaikan kapitalisasi dan diakritik; ia tidak
menerjemahkan atau memakai embedding semantik. Kueri kosong atau tanpa kecocokan
menghasilkan `[]`; `k` harus bilangan bulat nonnegatif. `get_study` memunculkan
`KeyError` untuk id yang tidak ada, dan pencarian ayat memunculkan `ValueError`
untuk rujukan yang tidak valid. Filter prinsip mencocokkan potongan teks tanpa
membedakan kapitalisasi pada id, judul, klaster, pernyataan, dan implikasi.

Setiap dict hasil memiliki `citations` dengan id kajian, rujukan ayat, sumber
`Quran Lab (engineering interpretation, not tafsir)`, lisensi `MIT`, dan
`sanad_tier: interpretation-draft`, serta penyangkalan dwibahasa. Prinsip mengutip
kajian buktinya. MIT pada sitasi mengacu pada karya Lab sendiri; pengecualian
kutipan dalam NOTICE tetap berlaku. Kajian lengkap mempertahankan objek `ref`;
hasil pencarian memakai `QS s:a-b` (atau `QS s:a` untuk satu ayat).

Pemuatan di-cache berdasarkan path direktori data yang telah diresolusikan selama
proses berjalan. Mulai ulang setelah mengubah data; hasil kueri publik berupa
salinan. Validasi membaca ulang berkas di disk.

### Integrasi SIDIX

`plugin.json` menyatakan entrypoint Python dan pemetaan tool ke fungsi berikut:

| Tool | Fungsi Python |
|---|---|
| `quran_lab_search` | `quran_lab.search(query, k=5)` |
| `quran_lab_get_study` | `quran_lab.get_study(id)` |
| `quran_lab_for_verse` | `quran_lab.studies_for_verse(surah, ayah)` |
| `quran_lab_principles` | `quran_lab.principles(topic=None)` |

Provider nonaktif secara default, hanya membaca data lokal, dan tidak menyatakan
konektor atau panel UI. Registrasi oleh host harus memakai pemetaan di atas;
manifest tidak menjalankan layanan atau otomatis mengaktifkan integrasi SIDIX.

## Verifikasi dan laporan kutipan

Dari root repositori:

```sh
python -m unittest discover -s providers/quran-lab/tests
```

Dari `providers/quran-lab`:

```sh
python -m quran_lab validate
python tools/find_quotations.py PATH_TO_APP_DATA --output QUOTATIONS_REPORT.md
```

`PATH_TO_APP_DATA` adalah direktori lokal yang sudah tersedia, hanya dibaca,
dan berisi `surah/` serta `tafsir/`. Detektor laporan memerlukan berkas
pembanding ini; penggunaan provider dan pengujiannya tidak memerlukannya.
`--json` menghasilkan jumlah dan lokasi dalam JSON; `--studies-dir` memilih
direktori kajian lain. Detektor memeriksa setiap field string untuk rangkaian
verbatim maksimal dengan sedikitnya delapan kata ternormalisasi dalam ayat
rujukan kajian. Laporan menjelaskan normalisasi, penghitungan tumpang tindih,
dan atribusi edisi. Ia tidak mencetak teks kutipan, menetapkan hak, atau
mengidentifikasi seluruh kutipan.

Validasi memeriksa field wajib, kecocokan nama berkas/id, batas ayat, status
belum ditinjau, penyangkalan, ketiadaan karakter aksara Arab dalam kajian,
pembersihan label sumber, id bukti prinsip, dan konsistensi indeks. Pengujian
juga mencakup asal-usul hasil, isolasi cache, keluaran CLI, data tidak valid,
dan deteksi kutipan.

## Tinjauan ahli

Buka satu [issue SIDIX](https://github.com/fahmiwol/sidix/issues) per id kajian.
Sertakan id, field dan ayat terkait, koreksi bersumber, batas analogi, dan usulan
keputusan (revisi, tolak, atau dukung). Sebutkan kualifikasi peninjau dan cakupan
yang benar-benar ditinjau. Usulan atau pemeriksaan otomatis tidak mengubah
status tinjauan; maintainer harus mencatat tinjauan nyata dengan atribusi.

## Hubungan dengan MiganCore

Lab menjadi sumber **hipotesis** desain bagi pekerjaan evaluasi dan gerbang
keputusan MiganCore, **tidak pernah sebagai bukti**. Eksperimen harus menguji
mekanisme yang diusulkan; analogi tidak memvalidasi kinerja atau menetapkan
hasil. Lihat [metode riset MiganCore](https://github.com/fahmiwol/migancore-research-method),
[Inspiration with guardrails](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/06-inspiration-with-guardrails.md)
dan [Ilham berpagar](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/06-ilham-berpagar.md).
Kebijakan kutipan paket ini dijelaskan di sini: kutipan dipertahankan dengan
atribusi dan dilaporkan.
