# Projek Badar — Batch Cursor (50 tugas, urut dependensi)
> Urutan = **dependensi kasar** (bukan DAG formal). Nomor asal surah tetap di kolom *Asal #*.

| # kerja | Asal # | Surah | Makna ringkas | Tugas teknis | Goal |
|---:|---:|--------|---------------|--------------|------|
| 1 | 1 | **Al-Fatihah** | Citra judul *Pembukaan*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Charter produk + definisi “selesai rilis”; healthcheck layanan. | **G1** |
| 2 | 2 | **Al-Baqarah** | Nada *Sapi Betina*: seleksi satu utang teknis dan tutup dalam sprint ini. | Endpoint tanya-jawab: alur `no answer` → fallback pencarian web terkontrol. | **G1** |
| 3 | 3 | **Ali 'Imran** | Gema *Keluarga Imran*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Rantai simpulan: ringkas bukti → usulan → rekomendasi (dengan label ketidakpastian). | **G1** |
| 4 | 4 | **An-Nisa** | Irama *Wanita*: perjelas satu alur yang sering salah paham di UI atau API. | Penalaan bahasa natural: deteksi maksud, bahasa campuran, eufemisme ringan. | **G1** |
| 5 | 6 | **Al-An'am** | Sentuhan *Binatang Ternak*: perbaiki satu pesan error atau label yang membingungkan. | Sanad UI: kutip sumber RAG; mode jawaban multi-epistemik. | **G1** |
| 6 | 12 | **Yusuf** | Waktu *Yusuf*: pasang deadline realistis untuk satu modul dependensi. | Rate limit & antrian pengguna ramai (fairness). | **G1** |
| 7 | 17 | **Al-Isra** | Jeda *Perjalanan Malam*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Korpus RAG: chunk + metadata + indeks ulang otomatis. | **G1** |
| 8 | 18 | **Al-Kahf** | Alih *Para Penghuni Gua*: dokumentasikan satu fallback ketika model atau tool gagal. | Tool “cari di internet”: allowlist domain + kutipan + cache. | **G1** |
| 9 | 23 | **Al-Mu'minun** | Pintu *Orang-orang Mukmin*: kunci satu endpoint admin yang belum terlindungi. | Dialog multi-turn: memori sesi terbatas + tombol “lupakan sesi”. | **G1** |
| 10 | 26 | **Ash-Shu'ara** | Nada *Penyair*: seleksi satu utang teknis dan tutup dalam sprint ini. | Deteksi prompt injection & jawaban aman default. | **G1** |
| 11 | 30 | **Ar-Rum** | Sentuhan *Bangsa Romawi*: perbaiki satu pesan error atau label yang membingungkan. | Onboarding admin pertama + rotasi secret. | **G1** |
| 12 | 35 | **Fatir** | Ruang *Pencipta*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Mode “hanya dari korpus” vs “boleh web” eksplisit di UI. | **G1** |
| 13 | 40 | **Ghafir** | Gerak *Sang Maha Pengampun*: percepat satu path panas tanpa mengorbankan keamanan. | Feedback pengguna: 👍/👎 ke metrik tanpa PII. | **G1** |
| 14 | 45 | **Al-Jathiyah** | Peta *Yang Bertekuk Lutut*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Ringkasan otomatis percakapan panjang. | **G1** |
| 15 | 50 | **Qaf** | Nada *Qaf*: seleksi satu utang teknis dan tutup dalam sprint ini. | Deteksi bahasa masukan + balasan konsisten. | **G1** |
| 16 | 55 | **Ar-Rahman** | Getaran *Yang Maha Pemurah*: uji satu skenario pinggiran yang sering dilupakan QA. | Kartu “tidak tahu” jujur + arahkan ke sumber. | **G1** |
| 17 | 60 | **Al-Mumtahanah** | Waktu *Wanita yang Diuji*: pasang deadline realistis untuk satu modul dependensi. | Template jawaban: fakta / opini / spekulasi. | **G1** |
| 18 | 65 | **At-Talaq** | Jeda *Perceraian*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Glosarium istilah proyek di RAG. | **G1** |
| 19 | 70 | **Al-Ma'arij** | Benang *Tempat yang Naik*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Mode anak / sederhana: kalimat pendek. | **G1** |
| 20 | 75 | **Al-Qiyamah** | Gema *Hari Berbangkit*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Deteksi duplikasi pertanyaan + cache jawaban aman. | **G1** |
| 21 | 80 | **'Abasa** | Warna *Ia Bermuka Masam*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Export percakapan JSON redaksi PII. | **G1** |
| 22 | 85 | **Al-Buruj** | Cahaya *Gugusan Bintang*: soroti satu metrik yang belum dimonitor operator. | Persona “pembimbing” vs “faktual” switch. | **G1** |
| 23 | 90 | **Al-Balad** | Alih *Negeri*: dokumentasikan satu fallback ketika model atau tool gagal. | Ringkas berita web dengan sumber. | **G1** |
| 24 | 95 | **At-Tin** | Pintu *Buah Tin*: kunci satu endpoint admin yang belum terlindungi. | Deteksi ujaran kejam → respons netral. | **G1** |
| 25 | 100 | **Al-'Adiyat** | Irama *Berlari Kencang*: perjelas satu alur yang sering salah paham di UI atau API. | FAQ statis + RAG override. | **G1** |
| 26 | 105 | **Al-Fil** | Aroma *Gajah*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Mode multibahasa output eksplisit. | **G1** |
| 27 | 110 | **An-Nasr** | Suara *Pertolongan*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Confidence score teks agregat. | **G1** |
| 28 | 5 | **Al-Ma'idah** | Bayang *Jamuan (Hidangan Makanan)*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Kartu eval jawaban (golden set) + regresi prompt sistem. | **G5** |
| 29 | 11 | **Hud** | Ruang *Hud*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Profil inferensi: kuantisasi, VRAM, timeout — dokumentasi operator. | **G5** |
| 30 | 16 | **An-Nahl** | Gerak *Lebah Madu*: percepat satu path panas tanpa mengorbankan keamanan. | Benchmark latensi jawaban vs target “24 jam sprint” internal. | **G5** |
| 31 | 19 | **Maryam** | Tilik *Maryam*: audit satu izin (token, role, secret) yang bisa disempitkan. | Ablation prompt: bandingkan 3 system prompt pada set kecil. | **G5** |
| 32 | 24 | **An-Nur** | Jembatan *Cahaya*: sambungkan satu celah antara tim data dan tim produk. | Observabilitas: trace ID, log terstruktur, dashboard error. | **G5** |
| 33 | 29 | **Al-'Ankabut** | Bayang *Laba-laba*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Versi model & hash adapter di `/health` + changelog. | **G5** |
| 34 | 34 | **Saba** | Tekstur *Saba'*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Load test ringan antrian inferensi. | **G5** |
| 35 | 39 | **Az-Zumar** | Hening *Para Rombongan*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Dokumentasi operator: restore dari backup volume. | **G5** |
| 36 | 44 | **Ad-Dukhan** | Lapis *Kabut*: tambah satu lapisan validasi input sebelum inferensi. | Pin image model version di compose/prod. | **G5** |
| 37 | 49 | **Al-Hujurat** | Citra judul *Kamar-kamar*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Kalibrasi temperature/top-p per use case. | **G5** |
| 38 | 54 | **Al-Qamar** | Sentuhan *Bulan*: perbaiki satu pesan error atau label yang membingungkan. | Profil biaya token per fitur. | **G5** |
| 39 | 59 | **Al-Hashr** | Ruang *Pengusiran*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Checklist rilis: TLS, firewall, secret vault. | **G5** |
| 40 | 64 | **At-Taghabun** | Gerak *Hari Dinampakkan Kesalahan*: percepat satu path panas tanpa mengorbankan keamanan. | Canary route ke model baru. | **G5** |
| 41 | 69 | **Al-Haqqah** | Peta *Kenyataan (Hari Kiamat)*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Alarm disk penuh volume model. | **G5** |
| 42 | 74 | **Al-Muddaththir** | Nada *Orang yang Berkemul*: seleksi satu utang teknis dan tutup dalam sprint ini. | Rotasi log & retensi. | **G5** |
| 43 | 79 | **An-Nazi'at** | Getaran *Malaikat yang Mencabut*: uji satu skenario pinggiran yang sering dilupakan QA. | Runbook insiden 1 halaman. | **G5** |
| 44 | 84 | **Al-Inshiqaq** | Waktu *Terbelah*: pasang deadline realistis untuk satu modul dependensi. | Synthetic monitor uptime endpoint. | **G5** |
| 45 | 89 | **Al-Fajr** | Jeda *Fajar*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Quota harian user anon. | **G5** |
| 46 | 94 | **Ash-Sharh** | Benang *Melapangkan*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Dashboard biaya API pihak ketiga. | **G5** |
| 47 | 99 | **Az-Zalzalah** | Gema *Kegoncangan*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Profiling satu request panjang. | **G5** |
| 48 | 104 | **Al-Humazah** | Warna *Pengumpat*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Dokumentasi disaster recovery. | **G5** |
| 49 | 109 | **Al-Kafirun** | Cahaya *Orang-orang Kafir*: soroti satu metrik yang belum dimonitor operator. | Hardening cookie/session WebUI. | **G5** |
| 50 | 114 | **An-Nas** | Alih *Umat Manusia*: dokumentasikan satu fallback ketika model atau tool gagal. | Blue/green switch inference. | **G5** |
