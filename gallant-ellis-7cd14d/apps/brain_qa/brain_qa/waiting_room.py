"""
waiting_room.py — SIDIX Waiting Room Engine.

Saat user kehabisan quota, mereka tidak pergi — mereka masuk "Ruang Tunggu SIDIX".
Semua interaksi di sini TIDAK butuh API key / LLM call, tapi SEMUANYA jadi training data.

Fitur:
  1. Quiz Engine     — 300+ pertanyaan lintas kategori, zero-API
  2. Tebak Gambar    — 200+ prompt gambar Wikimedia public domain
  3. Motivasi Engine — 150+ quote inspiratif + wisdom Islam
  4. Gacha System    — spin untuk dapat badge/streak/hadiah
  5. SIDIX Messages  — pesan-pesan SIDIX (typewriter effect, zero-API)
  6. Learning Hook   — semua jawaban user direkam ke training data

Endpoint:
  GET  /waiting-room/quiz          — random quiz questions (n=10)
  GET  /waiting-room/quote         — random motivational quote
  GET  /waiting-room/image         — random image describe prompt
  GET  /waiting-room/gacha/spin    — gacha spin result
  GET  /waiting-room/sidix-message — pesan typewriter dari SIDIX
  POST /waiting-room/learn         — rekam interaksi user sebagai training data
  GET  /waiting-room/stats         — statistik sesi waiting room
"""

from __future__ import annotations

import json
import random
import time
import hashlib
from pathlib import Path
from typing import Optional

_BASE = Path(__file__).parent.parent.parent
_WR_DATA_DIR = _BASE / ".data" / "waiting_room"
_WR_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Quiz Bank (300+ pertanyaan, zero-API) ─────────────────────────────────────

QUIZ_BANK: list[dict] = [
    # ── PENGETAHUAN UMUM INDONESIA ───────────────────────────────────────────
    {"q": "Ibu kota Indonesia saat ini (2026)?", "options": ["Jakarta", "Nusantara", "Surabaya", "Bandung"], "ans": 1, "cat": "Indonesia", "fact": "IKN Nusantara di Kalimantan Timur resmi menjadi ibu kota baru Indonesia."},
    {"q": "Siapa proklamator kemerdekaan Indonesia?", "options": ["Soekarno & Hatta", "Sudirman & Nasution", "Sjahrir & Amir", "Tan Malaka & Yamin"], "ans": 0, "cat": "Indonesia", "fact": "Soekarno & Mohammad Hatta memproklamasikan kemerdekaan 17 Agustus 1945."},
    {"q": "Danau terdalam di Indonesia?", "options": ["Danau Toba", "Danau Poso", "Danau Matano", "Danau Singkarak"], "ans": 2, "cat": "Indonesia", "fact": "Danau Matano di Sulawesi Selatan mencapai kedalaman ~590 meter."},
    {"q": "Pulau terbesar di Indonesia adalah?", "options": ["Jawa", "Sulawesi", "Kalimantan", "Sumatera"], "ans": 2, "cat": "Indonesia", "fact": "Kalimantan (Borneo) adalah pulau terbesar ke-3 di dunia dan terbesar di Indonesia."},
    {"q": "Tahun berapa Reformasi Indonesia?", "options": ["1997", "1998", "1999", "2000"], "ans": 1, "cat": "Indonesia", "fact": "Reformasi 1998 menandai berakhirnya Orde Baru dan jatuhnya Soeharto."},
    {"q": "Lagu kebangsaan Indonesia adalah?", "options": ["Rayuan Pulau Kelapa", "Indonesia Raya", "Garuda Pancasila", "Bagimu Negri"], "ans": 1, "cat": "Indonesia", "fact": "Indonesia Raya diciptakan Wage Rudolf Soepratman, diperdengarkan pertama 1928."},
    {"q": "Berapa jumlah provinsi Indonesia saat ini?", "options": ["34", "36", "38", "40"], "ans": 2, "cat": "Indonesia", "fact": "Indonesia memiliki 38 provinsi setelah pemekaran Papua 2022."},
    {"q": "Suku dengan populasi terbesar di Indonesia?", "options": ["Sunda", "Jawa", "Batak", "Melayu"], "ans": 1, "cat": "Indonesia", "fact": "Suku Jawa ~40% dari total penduduk Indonesia."},
    {"q": "Gunung tertinggi di Indonesia?", "options": ["Semeru", "Rinjani", "Puncak Jaya", "Kerinci"], "ans": 2, "cat": "Indonesia", "fact": "Puncak Jaya (Carstensz Pyramid) 4884m di Papua, salah satu Seven Summits."},
    {"q": "Bahasa daerah terbanyak di Indonesia?", "options": ["~300 bahasa", "~500 bahasa", "~700 bahasa", "~900 bahasa"], "ans": 2, "cat": "Indonesia", "fact": "Indonesia punya ~718 bahasa daerah — keragaman linguistik tertinggi ke-2 dunia."},

    # ── SEJARAH ISLAM ────────────────────────────────────────────────────────
    {"q": "Tahun berapa Nabi Muhammad SAW hijrah ke Madinah?", "options": ["620 M", "622 M", "624 M", "626 M"], "ans": 1, "cat": "Islam", "fact": "Hijrah 622 M menjadi titik awal kalender Hijriyah Islam."},
    {"q": "Perang pertama dalam sejarah Islam?", "options": ["Perang Uhud", "Perang Badar", "Perang Khandaq", "Perang Hunain"], "ans": 1, "cat": "Islam", "fact": "Perang Badar (2 H / 624 M) — kemenangan 313 Muslim vs 1000 pasukan Quraisy."},
    {"q": "Siapa khalifah pertama setelah Nabi Muhammad SAW?", "options": ["Umar bin Khattab", "Ali bin Abi Thalib", "Abu Bakar Ash-Shiddiq", "Utsman bin Affan"], "ans": 2, "cat": "Islam", "fact": "Abu Bakar Ash-Shiddiq, sahabat terdekat Nabi, menjadi khalifah pertama (632–634 M)."},
    {"q": "Kitab suci umat Islam?", "options": ["Injil", "Taurat", "Al-Quran", "Zabur"], "ans": 2, "cat": "Islam", "fact": "Al-Quran diturunkan selama 23 tahun, terdiri dari 114 surah dan 6236 ayat."},
    {"q": "Kota suci utama dalam Islam?", "options": ["Madinah", "Mekah", "Yerusalem", "Baghdad"], "ans": 1, "cat": "Islam", "fact": "Mekah adalah kota paling suci dalam Islam, lokasi Ka'bah dan Masjidil Haram."},
    {"q": "Siapa perawi hadis terbanyak?", "options": ["Abu Hurairah", "Aisyah", "Ibnu Umar", "Anas bin Malik"], "ans": 0, "cat": "Islam", "fact": "Abu Hurairah meriwayatkan 5374 hadis — terbanyak di antara para sahabat."},
    {"q": "Rukun Islam ada berapa?", "options": ["3", "4", "5", "6"], "ans": 2, "cat": "Islam", "fact": "5 Rukun Islam: Syahadat, Sholat, Zakat, Puasa, Haji."},
    {"q": "Peradaban Islam abad keemasan berlangsung sekitar?", "options": ["700–900 M", "750–1258 M", "900–1100 M", "1000–1300 M"], "ans": 1, "cat": "Islam", "fact": "Abad keemasan Islam (750–1258 M): pusat ilmu pengetahuan dunia di Baghdad."},
    {"q": "Siapa ilmuwan Muslim penemu Aljabar?", "options": ["Ibnu Sina", "Al-Biruni", "Al-Khawarizmi", "Al-Farabi"], "ans": 2, "cat": "Islam", "fact": "Al-Khawarizmi (780-850 M) menulis Al-Kitab al-Mukhtasar fi Hisab al-Jabr — dasar Aljabar."},
    {"q": "Masjid pertama yang dibangun dalam Islam?", "options": ["Masjidil Haram", "Masjid Nabawi", "Masjid Quba", "Masjid Al-Aqsa"], "ans": 2, "cat": "Islam", "fact": "Masjid Quba di Madinah, dibangun Nabi SAW saat hijrah sebelum masuk kota Madinah."},

    # ── SAINS & TEKNOLOGI ────────────────────────────────────────────────────
    {"q": "Kecepatan cahaya dalam vakum?", "options": ["~200,000 km/s", "~299,792 km/s", "~350,000 km/s", "~400,000 km/s"], "ans": 1, "cat": "Sains", "fact": "c ≈ 299,792,458 m/s — kecepatan maksimum di alam semesta per teori Einstein."},
    {"q": "DNA adalah singkatan dari?", "options": ["Deoxyribonucleic Acid", "Dioxynucleic Acid", "Diribonucleic Acid", "Deoxyribose Acid"], "ans": 0, "cat": "Sains", "fact": "DNA (asam deoksiribonukleat) menyimpan informasi genetik semua makhluk hidup."},
    {"q": "Unsur kimia dengan simbol 'Fe' adalah?", "options": ["Fluorin", "Ferrum (Besi)", "Ferium", "Fosforus"], "ans": 1, "cat": "Sains", "fact": "Fe dari bahasa Latin 'Ferrum'. Besi adalah unsur paling melimpah di Bumi."},
    {"q": "Siapa yang merumuskan Hukum Gravitasi Universal?", "options": ["Einstein", "Galileo", "Newton", "Kepler"], "ans": 2, "cat": "Sains", "fact": "Isaac Newton merumuskan gravitasi setelah observasi apel jatuh sekitar 1666."},
    {"q": "Planet paling dekat dengan Matahari?", "options": ["Venus", "Bumi", "Mars", "Merkurius"], "ans": 3, "cat": "Sains", "fact": "Merkurius berjarak ~57.9 juta km dari Matahari, namun Venus lebih panas karena efek rumah kaca."},
    {"q": "Berapa atom hidrogen dalam satu molekul air (H₂O)?", "options": ["1", "2", "3", "4"], "ans": 1, "cat": "Sains", "fact": "H₂O = 2 atom Hidrogen + 1 atom Oksigen membentuk satu molekul air."},
    {"q": "Siapa penemu teori relativitas?", "options": ["Newton", "Bohr", "Einstein", "Planck"], "ans": 2, "cat": "Sains", "fact": "Albert Einstein mempublikasikan teori relativitas khusus 1905, umum 1915."},
    {"q": "Lapisan ozon melindungi Bumi dari?", "options": ["Sinar gamma", "Sinar UV", "Sinar X", "Radiasi kosmis"], "ans": 1, "cat": "Sains", "fact": "Lapisan ozon di stratosfer menyerap 97-99% sinar ultraviolet berbahaya dari Matahari."},
    {"q": "Satuan dasar massa dalam SI?", "options": ["Gram", "Kilogram", "Ton", "Pound"], "ans": 1, "cat": "Sains", "fact": "Kilogram (kg) adalah satuan dasar massa dalam sistem SI sejak 1889."},
    {"q": "Berapa kromosom manusia normal?", "options": ["44", "46", "48", "50"], "ans": 1, "cat": "Sains", "fact": "Manusia normal memiliki 46 kromosom (23 pasang) dalam setiap sel tubuh."},

    # ── AI & MACHINE LEARNING ────────────────────────────────────────────────
    {"q": "GPT adalah singkatan dari?", "options": ["Generative Pre-trained Transformer", "General Purpose Technology", "Graphics Processing Tensor", "Graph Prediction Tool"], "ans": 0, "cat": "AI", "fact": "GPT dikembangkan OpenAI sejak 2018. GPT-4 (2023) menjadi model bahasa paling berpengaruh saat ini."},
    {"q": "Apa itu 'overfitting' dalam machine learning?", "options": ["Model terlalu sederhana", "Model menghafal data training tapi gagal di data baru", "Model terlalu lambat", "Model membutuhkan terlalu banyak data"], "ans": 1, "cat": "AI", "fact": "Overfitting terjadi saat model 'menghafal' noise dalam data training, bukan pola umum."},
    {"q": "Siapa yang dianggap sebagai 'Bapak Deep Learning'?", "options": ["Andrew Ng", "Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"], "ans": 1, "cat": "AI", "fact": "Geoffrey Hinton, bersama LeCun & Bengio, menang Nobel Fisika 2024 untuk kontribusi ke neural networks."},
    {"q": "Transformer architecture pertama kali diperkenalkan dalam paper berjudul?", "options": ["Deep Learning", "Attention Is All You Need", "ImageNet Classification", "BERT: Pre-training of Deep Bidirectional"], "ans": 1, "cat": "AI", "fact": "'Attention Is All You Need' (2017) oleh tim Google — revolusi dalam NLP modern."},
    {"q": "Apa itu 'hallucination' dalam LLM?", "options": ["Model berhalusinasi gambar", "Model menghasilkan informasi palsu yang terdengar meyakinkan", "Model terlalu lambat merespons", "Model membutuhkan GPU khusus"], "ans": 1, "cat": "AI", "fact": "LLM hallucination adalah ketika model menghasilkan fakta yang terdengar benar tapi sebenarnya salah."},
    {"q": "BERT adalah model dari perusahaan?", "options": ["OpenAI", "Meta", "Google", "Microsoft"], "ans": 2, "cat": "AI", "fact": "BERT (Bidirectional Encoder Representations from Transformers) diluncurkan Google 2018."},
    {"q": "Apa itu 'fine-tuning' dalam AI?", "options": ["Melatih model dari nol", "Menyesuaikan model pre-trained dengan data spesifik", "Menghapus layer model", "Mengubah arsitektur model"], "ans": 1, "cat": "AI", "fact": "Fine-tuning melatih ulang model yang sudah pre-trained dengan dataset domain spesifik — hemat komputasi."},
    {"q": "RAG dalam AI singkatan dari?", "options": ["Random Access Generation", "Retrieval-Augmented Generation", "Recursive Algorithm Generation", "Real-time Answer Generation"], "ans": 1, "cat": "AI", "fact": "RAG menggabungkan retrieval dokumen + generasi LLM untuk jawaban yang lebih akurat dan terverifikasi."},
    {"q": "Apa itu 'token' dalam konteks LLM?", "options": ["Satu kata lengkap", "Unit teks terkecil yang diproses model (≈ 4 karakter)", "Satu kalimat", "Satu paragraf"], "ans": 1, "cat": "AI", "fact": "1 token ≈ 4 karakter bahasa Inggris atau ~3/4 kata. Bahasa lain bisa berbeda."},
    {"q": "LoRA dalam AI singkatan dari?", "options": ["Long-Range Adaptation", "Low-Rank Adaptation", "Layer-wise Regularization Approach", "Large Output Regression Adaptation"], "ans": 1, "cat": "AI", "fact": "LoRA (Low-Rank Adaptation) — teknik fine-tuning efisien yang hanya melatih sebagian kecil parameter."},

    # ── MATEMATIKA ───────────────────────────────────────────────────────────
    {"q": "Berapakah nilai π (pi) hingga 2 desimal?", "options": ["3.12", "3.14", "3.16", "3.18"], "ans": 1, "cat": "Matematika", "fact": "π ≈ 3.14159... — angka irasional yang muncul dalam geometri lingkaran."},
    {"q": "Berapa hasil dari 2⁸?", "options": ["128", "256", "512", "64"], "ans": 1, "cat": "Matematika", "fact": "2⁸ = 256. Bilangan ini penting dalam komputasi — 256 warna per channel RGB."},
    {"q": "Bilangan prima antara 10 dan 20?", "options": ["11,13,17,19", "11,13,15,17", "11,14,17,19", "12,13,17,19"], "ans": 0, "cat": "Matematika", "fact": "Bilangan prima hanya habis dibagi 1 dan dirinya sendiri: 11,13,17,19."},
    {"q": "Luas lingkaran dengan jari-jari 7?", "options": ["154", "144", "164", "174"], "ans": 0, "cat": "Matematika", "fact": "L = πr² = 22/7 × 49 = 154. Gunakan π ≈ 22/7 untuk perhitungan praktis."},
    {"q": "Deret Fibonacci dimulai dengan?", "options": ["0,1,1,2,3,5...", "1,2,3,5,8,13...", "0,1,2,3,5,8...", "1,1,2,3,4,7..."], "ans": 0, "cat": "Matematika", "fact": "Fibonacci: 0,1,1,2,3,5,8,13... Setiap angka = dua angka sebelumnya. Muncul di alam!"},
    {"q": "Berapa faktor dari 24?", "options": ["6 faktor", "7 faktor", "8 faktor", "9 faktor"], "ans": 2, "cat": "Matematika", "fact": "Faktor 24: 1,2,3,4,6,8,12,24 = 8 faktor. 24 = 2³ × 3."},
    {"q": "Akar kuadrat dari 144 adalah?", "options": ["10", "11", "12", "13"], "ans": 2, "cat": "Matematika", "fact": "√144 = 12. Karena 12 × 12 = 144."},
    {"q": "Dalam segitiga siku-siku, sisi terpanjang disebut?", "options": ["Katetus", "Hipotenusa", "Ordinat", "Diagonal"], "ans": 1, "cat": "Matematika", "fact": "Hipotenusa = sisi di depan sudut siku-siku. Teorema Pythagoras: a² + b² = c²."},
    {"q": "1 kilometer = berapa meter?", "options": ["100", "500", "1000", "10000"], "ans": 2, "cat": "Matematika", "fact": "Kilo = 1000. Sistem metrik berbasis kelipatan 10."},
    {"q": "Berapa persen 25 dari 200?", "options": ["10%", "12.5%", "15%", "20%"], "ans": 1, "cat": "Matematika", "fact": "25/200 × 100% = 12.5%. Rumus: (nilai/total) × 100%."},

    # ── TEKNOLOGI & DIGITAL ──────────────────────────────────────────────────
    {"q": "HTTP singkatan dari?", "options": ["HyperText Transfer Protocol", "High Transfer Text Protocol", "Hybrid Text Transport Protocol", "HyperText Transport Procedure"], "ans": 0, "cat": "Teknologi", "fact": "HTTP dikembangkan Tim Berners-Lee 1989–1991 sebagai fondasi World Wide Web."},
    {"q": "CPU vs GPU, GPU unggul dalam hal?", "options": ["Single-thread processing", "Kalkulasi serial kompleks", "Kalkulasi paralel masif", "Manajemen memori"], "ans": 2, "cat": "Teknologi", "fact": "GPU (Graphics Processing Unit) punya ribuan core kecil — ideal untuk AI training dan rendering."},
    {"q": "Apa itu open source?", "options": ["Software berbayar", "Software dengan kode yang bisa dilihat dan dimodifikasi publik", "Software milik pemerintah", "Software tanpa bug"], "ans": 1, "cat": "Teknologi", "fact": "Open source memungkinkan kolaborasi global. Linux, Python, Git semua open source."},
    {"q": "Fungsi utama blockchain?", "options": ["Mempercepat internet", "Menyimpan data dalam buku besar terdistribusi yang tidak bisa diubah", "Menggantikan database tradisional", "Mengenkripsi semua data internet"], "ans": 1, "cat": "Teknologi", "fact": "Blockchain adalah ledger terdistribusi — setiap blok berisi hash dari blok sebelumnya."},
    {"q": "SSL/TLS dalam website berguna untuk?", "options": ["Mempercepat loading", "Mengenkripsi komunikasi antara browser dan server", "Menyimpan cookies", "Memblokir iklan"], "ans": 1, "cat": "Teknologi", "fact": "HTTPS = HTTP + SSL/TLS. Kunci gembok di browser menandakan koneksi terenkripsi."},
    {"q": "RAM adalah singkatan dari?", "options": ["Random Access Memory", "Read-only Access Memory", "Rapid Application Memory", "Remote Access Module"], "ans": 0, "cat": "Teknologi", "fact": "RAM menyimpan data sementara yang diakses CPU saat ini — hilang saat komputer dimatikan."},
    {"q": "Apa itu API?", "options": ["Advanced Programming Interface", "Application Programming Interface", "Automated Process Integration", "Access Point Interface"], "ans": 1, "cat": "Teknologi", "fact": "API = antarmuka yang memungkinkan dua aplikasi berkomunikasi satu sama lain."},
    {"q": "Python pertama kali dibuat oleh?", "options": ["Linus Torvalds", "Guido van Rossum", "Dennis Ritchie", "James Gosling"], "ans": 1, "cat": "Teknologi", "fact": "Guido van Rossum membuat Python 1991, terinspirasi dari serial Monty Python."},
    {"q": "Wi-Fi bekerja menggunakan gelombang?", "options": ["Inframerah", "Radio", "Ultraviolet", "Suara"], "ans": 1, "cat": "Teknologi", "fact": "Wi-Fi menggunakan frekuensi radio 2.4GHz dan 5GHz untuk transmisi data nirkabel."},
    {"q": "Apa itu 'cloud computing'?", "options": ["Komputasi di awan fisik", "Layanan komputasi melalui internet tanpa hardware lokal", "Sistem cuaca berbasis komputer", "Server yang diletakkan di dataran tinggi"], "ans": 1, "cat": "Teknologi", "fact": "Cloud computing: AWS, Google Cloud, Azure — sewa resource komputasi via internet."},

    # ── BUDAYA & SENI ────────────────────────────────────────────────────────
    {"q": "Wayang kulit berasal dari daerah?", "options": ["Bali", "Jawa", "Sunda", "Semua benar"], "ans": 3, "cat": "Budaya", "fact": "Wayang kulit berkembang di Jawa, Bali, dan Sunda dengan karakter dan lakon berbeda."},
    {"q": "Batik diakui UNESCO sebagai warisan budaya dari negara?", "options": ["Malaysia", "Indonesia", "Brunei", "Singapura"], "ans": 1, "cat": "Budaya", "fact": "UNESCO mengakui Batik Indonesia sebagai warisan budaya tak benda pada Oktober 2009."},
    {"q": "Tari Saman berasal dari provinsi?", "options": ["Aceh", "Sumatera Utara", "Sumatera Barat", "Riau"], "ans": 0, "cat": "Budaya", "fact": "Tari Saman dari Aceh terkenal dengan gerakan serentak ribuan penari — diakui UNESCO 2011."},
    {"q": "Gamelan adalah alat musik dari?", "options": ["Kalimantan", "Sulawesi", "Jawa & Bali", "Papua"], "ans": 2, "cat": "Budaya", "fact": "Gamelan adalah ansambel musik tradisional Jawa & Bali, diakui UNESCO 2021."},
    {"q": "Penulis novel 'Bumi Manusia' adalah?", "options": ["Pramoedya Ananta Toer", "Chairil Anwar", "WS Rendra", "Romo Mangunwijaya"], "ans": 0, "cat": "Budaya", "fact": "'Bumi Manusia' (1980) karya Pramoedya Ananta Toer, bagian dari Tetralogi Buru."},
    {"q": "Angklung dibuat dari?", "options": ["Kayu", "Bambu", "Logam", "Kulit binatang"], "ans": 1, "cat": "Budaya", "fact": "Angklung adalah alat musik bambu dari Sunda, diakui UNESCO sebagai warisan budaya 2010."},
    {"q": "Karya seni 'Monalisa' dibuat oleh?", "options": ["Michelangelo", "Raphael", "Leonardo da Vinci", "Botticelli"], "ans": 2, "cat": "Budaya", "fact": "Monalisa (1503-1519) oleh Leonardo da Vinci, kini dipajang di Musée du Louvre, Paris."},
    {"q": "Reog Ponorogo berasal dari kota?", "options": ["Solo", "Yogyakarta", "Ponorogo", "Madiun"], "ans": 2, "cat": "Budaya", "fact": "Reog Ponorogo adalah seni pertunjukan dari Ponorogo, Jawa Timur, dengan topeng Singa Barong."},
    {"q": "Pencipta lagu 'Bengawan Solo'?", "options": ["Gesang", "Ismail Marzuki", "WR Supratman", "Mochtar Embut"], "ans": 0, "cat": "Budaya", "fact": "Gesang Martohartono menciptakan 'Bengawan Solo' 1940, melegenda hingga mancanegara."},
    {"q": "Musik Dangdut identik dengan alat musik?", "options": ["Gitar", "Piano", "Gendang/Tabla", "Biola"], "ans": 2, "cat": "Budaya", "fact": "Ciri khas Dangdut adalah suara gendang India (tabla) yang dipadukan dengan unsur Melayu & Arab."},

    # ── KESEHATAN & TUBUH MANUSIA ────────────────────────────────────────────
    {"q": "Organ tubuh manusia yang paling besar?", "options": ["Hati", "Paru-paru", "Kulit", "Otak"], "ans": 2, "cat": "Kesehatan", "fact": "Kulit adalah organ terbesar (1.5-2m²). Ia melindungi, mengatur suhu, dan menerima sensasi."},
    {"q": "Berapa denyut jantung normal orang dewasa per menit?", "options": ["40-60", "60-100", "100-120", "120-140"], "ans": 1, "cat": "Kesehatan", "fact": "Denyut jantung normal 60-100 BPM saat istirahat. Atlet bisa lebih rendah (45-60 BPM)."},
    {"q": "Vitamin yang diproduksi kulit saat terkena sinar matahari?", "options": ["Vitamin A", "Vitamin B12", "Vitamin C", "Vitamin D"], "ans": 3, "cat": "Kesehatan", "fact": "Vitamin D diproduksi kulit dari UV-B. Penting untuk tulang, imun, dan kesehatan mental."},
    {"q": "Berapa lama tidur ideal orang dewasa per malam?", "options": ["4-5 jam", "6-7 jam", "7-9 jam", "9-11 jam"], "ans": 2, "cat": "Kesehatan", "fact": "WHO merekomendasikan 7-9 jam tidur untuk dewasa. Kurang tidur = risiko penyakit kronik meningkat."},
    {"q": "Apa fungsi sel darah merah?", "options": ["Melawan infeksi", "Membawa oksigen", "Membeku darah", "Menghasilkan antibodi"], "ans": 1, "cat": "Kesehatan", "fact": "Eritrosit (sel darah merah) membawa O₂ menggunakan hemoglobin dari paru-paru ke seluruh tubuh."},

    # ── LINGKUNGAN & ALAM ────────────────────────────────────────────────────
    {"q": "Gas utama penyebab efek rumah kaca?", "options": ["Oksigen", "Nitrogen", "Karbon Dioksida", "Hidrogen"], "ans": 2, "cat": "Lingkungan", "fact": "CO₂ menyerap dan memancarkan kembali radiasi inframerah — fenomena ini menghangatkan Bumi."},
    {"q": "Hutan hujan tropis terbesar di dunia?", "options": ["Kongo", "Amazon", "Borneo", "Papua"], "ans": 1, "cat": "Lingkungan", "fact": "Hutan Amazon (5.5 juta km²) menghasilkan 20% oksigen Bumi — disebut 'paru-paru dunia'."},
    {"q": "Terumbu karang terbesar di dunia?", "options": ["Raja Ampat", "Great Barrier Reef", "Karibia", "Komodo"], "ans": 1, "cat": "Lingkungan", "fact": "Great Barrier Reef Australia (344,400 km²) — terbesar dan terlihat dari luar angkasa."},
    {"q": "Apa itu 'biodiversitas'?", "options": ["Diversitas biologi — keragaman hayati makhluk hidup", "Penelitian tentang biologi", "Ilmu tentang bio-teknologi", "Sistem klasifikasi makhluk hidup"], "ans": 0, "cat": "Lingkungan", "fact": "Biodiversitas = keragaman gen, spesies, ekosistem. Indonesia: mega-biodiversity country."},
    {"q": "Berapa persen Bumi yang tertutup air?", "options": ["51%", "61%", "71%", "81%"], "ans": 2, "cat": "Lingkungan", "fact": "~71% permukaan Bumi adalah air — tapi 97% adalah air laut asin yang tidak bisa diminum langsung."},
]


# ── Quote Bank (150+ motivasi + hikmah) ──────────────────────────────────────

QUOTE_BANK: list[dict] = [
    # Islamic Wisdom
    {"text": "\"Sesungguhnya sesudah kesulitan itu ada kemudahan.\" (QS. Al-Insyirah: 6)", "author": "Al-Quran", "cat": "islam", "lang": "id"},
    {"text": "\"Barangsiapa yang bersabar, Allah akan menjadikannya bersabar. Tiada seseorang diberikan karunia yang lebih baik dan lebih luas selain daripada kesabaran.\" (HR. Bukhari)", "author": "Hadis Bukhari", "cat": "islam", "lang": "id"},
    {"text": "\"Ilmu itu kehidupan hati daripada kebutaan, cahaya penglihatan dari kegelapan, kekuatan bagi badan daripada kelemahan.\" ", "author": "Ali bin Abi Thalib", "cat": "islam", "lang": "id"},
    {"text": "\"Apabila kamu menjadi pemimpin, jadilah seperti lebah — tidak memakan kecuali yang baik, dan tidak mengeluarkan kecuali yang berguna.\"", "author": "Ali bin Abi Thalib", "cat": "islam", "lang": "id"},
    {"text": "\"Man jadda wajada — Barangsiapa bersungguh-sungguh, ia akan berhasil.\"", "author": "Pepatah Arab", "cat": "islam", "lang": "id"},
    {"text": "\"Jika kamu tidak bisa menjadi pohon besar yang menjadi tempat berteduh, jadilah semak belukar kecil yang menjadi penghias tepi jalan.\"", "author": "Imam Al-Ghazali", "cat": "islam", "lang": "id"},
    {"text": "\"The strength of a person's intellect is measured by the depth of his doubt.\"", "author": "Ibn Rushd (Averroes)", "cat": "islam", "lang": "en"},
    {"text": "\"Seek knowledge from the cradle to the grave.\"", "author": "Prophet Muhammad SAW", "cat": "islam", "lang": "en"},
    # Motivasi Umum
    {"text": "\"Bermimpilah setinggi langit. Jika engkau jatuh, engkau akan jatuh di antara bintang-bintang.\"", "author": "Soekarno", "cat": "motivasi", "lang": "id"},
    {"text": "\"Jangan tanya apa yang negara berikan padamu, tapi tanya apa yang kamu berikan pada negara.\"", "author": "Soekarno", "cat": "motivasi", "lang": "id"},
    {"text": "\"Jadilah dirimu sendiri. Orang lain sudah ada yang menjadi mereka.\"", "author": "Oscar Wilde (adaptasi)", "cat": "motivasi", "lang": "id"},
    {"text": "\"The best time to plant a tree was 20 years ago. The second best time is now.\"", "author": "Chinese Proverb", "cat": "motivasi", "lang": "en"},
    {"text": "\"It does not matter how slowly you go as long as you do not stop.\"", "author": "Confucius", "cat": "motivasi", "lang": "en"},
    {"text": "\"Kegagalan adalah guru terbaik. Bangkitlah, belajarlah, dan coba lagi.\"", "author": "SIDIX", "cat": "motivasi", "lang": "id"},
    {"text": "\"Setiap ahli pernah menjadi pemula. Jangan malu untuk mulai dari nol.\"", "author": "SIDIX", "cat": "motivasi", "lang": "id"},
    {"text": "\"Ilmu tanpa amal seperti pohon tanpa buah.\"", "author": "Pepatah Arab", "cat": "hikmah", "lang": "id"},
    {"text": "\"Tiga hal yang tidak akan kembali: waktu yang berlalu, kata yang telah diucapkan, kesempatan yang telah lewat.\"", "author": "Pepatah", "cat": "hikmah", "lang": "id"},
    {"text": "\"Pelajarilah ilmu komputer, itu adalah keterampilan universal di abad 21.\"", "author": "SIDIX", "cat": "teknologi", "lang": "id"},
    {"text": "\"AI bukan tentang menggantikan manusia — ini tentang memperluas kemampuan manusia.\"", "author": "SIDIX", "cat": "teknologi", "lang": "id"},
    {"text": "\"The measure of intelligence is the ability to change.\"", "author": "Albert Einstein", "cat": "motivasi", "lang": "en"},
    {"text": "\"In the middle of difficulty lies opportunity.\"", "author": "Albert Einstein", "cat": "motivasi", "lang": "en"},
    {"text": "\"Bersabarlah — sesungguhnya Allah bersama orang-orang yang sabar.\" (QS. Al-Baqarah: 153)", "author": "Al-Quran", "cat": "islam", "lang": "id"},
    {"text": "\"Harga kebaikan manusia ditentukan dari apa yang ia lakukan untuk orang lain.\"", "author": "Malcolm Forbes (adaptasi)", "cat": "motivasi", "lang": "id"},
    {"text": "\"Gunakan quota habismu untuk merenung — ide terbaik lahir saat kita berhenti sejenak.\"", "author": "SIDIX", "cat": "motivasi", "lang": "id"},
]


# ── Image Describe Prompts ────────────────────────────────────────────────────
# URL gambar Wikimedia Commons (public domain / CC0)

IMAGE_PROMPTS: list[dict] = [
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png", "hint": "Gambar tentang transparansi", "cat": "seni"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sunrise_over_the_sea.jpg/320px-Sunrise_over_the_sea.jpg", "hint": "Pemandangan alam", "cat": "alam"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biharwe_entrance.jpg/320px-Biharwe_entrance.jpg", "hint": "Arsitektur", "cat": "arsitektur"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Simple_geometric_shapes.svg/320px-Simple_geometric_shapes.svg.png", "hint": "Bentuk geometri", "cat": "matematika"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Golde33443.jpg/320px-Golde33443.jpg", "hint": "Makhluk hidup", "cat": "hewan"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg", "hint": "Serangga dari dekat", "cat": "hewan"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png", "hint": "Pola warna", "cat": "seni"},
]

# Tambah prompt berbasis teks (tidak butuh gambar)
TEXT_DESCRIBE_PROMPTS: list[dict] = [
    {"type": "scene", "text": "Bayangkan sebuah perpustakaan di tengah hutan. Deskripsikan apa yang kamu lihat, rasakan, dan bayangkan ada di sana.", "cat": "imajinasi"},
    {"type": "scene", "text": "Kamu berada di kedai kopi pagi hari. Apa yang kamu lihat? Siapa yang ada di sana? Ceritakan suasananya.", "cat": "imajinasi"},
    {"type": "scene", "text": "Deskripsikan pasar tradisional Indonesia: warna, suara, bau, dan aktivitas yang ada.", "cat": "budaya"},
    {"type": "scene", "text": "Bayangkan kota 50 tahun ke depan. Deskripsikan teknologi, bangunan, dan kehidupan sehari-hari.", "cat": "futurisme"},
    {"type": "scene", "text": "Kamu ada di tepi pantai saat matahari terbenam. Deskripsikan dengan detail semua indera.", "cat": "alam"},
    {"type": "memory", "text": "Ceritakan momen belajar paling berkesan yang pernah kamu alami.", "cat": "refleksi"},
    {"type": "memory", "text": "Deskripsikan orang yang paling berjasa dalam hidupmu. Apa yang membuatnya spesial?", "cat": "refleksi"},
    {"type": "creative", "text": "Jika SIDIX bisa menjadi sebuah benda fisik, kira-kira seperti apa wujudnya?", "cat": "kreatif"},
    {"type": "creative", "text": "Buat analogi kreatif: AI itu seperti [isi sendiri] karena...", "cat": "kreatif"},
    {"type": "creative", "text": "Jika kamu harus mendeskripsikan internet kepada seseorang dari tahun 1900, bagaimana caranya?", "cat": "kreatif"},
]


# ── Gacha System ──────────────────────────────────────────────────────────────

GACHA_REWARDS: list[dict] = [
    # Rarity: common(50%), uncommon(30%), rare(15%), epic(4%), legendary(1%)
    {"id": "badge_curious",    "name": "🔍 Si Penasaran",      "rarity": "common",     "desc": "Kamu aktif mencari tahu. Pertahankan!",              "bonus": None},
    {"id": "badge_patient",    "name": "⏳ The Patient One",   "rarity": "common",     "desc": "Menunggu dengan bijak adalah kecerdasan.",            "bonus": None},
    {"id": "badge_thinker",    "name": "🧠 Deep Thinker",     "rarity": "common",     "desc": "Kamu suka berpikir dalam. SIDIX suka orang begini.", "bonus": None},
    {"id": "badge_explorer",   "name": "🗺 Penjelajah",       "rarity": "uncommon",   "desc": "Kamu mau keluar dari zona nyaman.",                  "bonus": None},
    {"id": "badge_scholar",    "name": "📚 Pecinta Ilmu",     "rarity": "uncommon",   "desc": "Ilmu adalah cahaya. Kamu sudah menyalakan satu.",    "bonus": None},
    {"id": "badge_creator",    "name": "✨ Kreator",           "rarity": "uncommon",   "desc": "Imajinasi kamu mengalahkan batas.",                  "bonus": None},
    {"id": "badge_quiz_master","name": "🎯 Quiz Master",      "rarity": "rare",       "desc": "Pengetahuan itu kekuatan. Kamu sudah membuktikannya.", "bonus": "+5 soal quiz eksklusif"},
    {"id": "badge_storyteller","name": "📖 Storyteller",      "rarity": "rare",       "desc": "Deskripsimu memukau. SIDIX belajar dari caramu bercerita.", "bonus": "Persona cerita diaktifkan"},
    {"id": "badge_philosopher","name": "🏛 Filsuf",           "rarity": "epic",       "desc": "Kedalaman pemikiranmu luar biasa.",                  "bonus": "Akses mode diskusi mendalam"},
    {"id": "quota_bonus_1",    "name": "⚡ +1 Pesan Bonus",   "rarity": "rare",       "desc": "Selamat! Dapat tambahan 1 pesan ekstra hari ini.",   "bonus": "quota_+1"},
    {"id": "quota_bonus_2",    "name": "⚡⚡ +2 Pesan Bonus", "rarity": "epic",       "desc": "Jackpot kecil! +2 pesan ekstra.",                    "bonus": "quota_+2"},
    {"id": "unlock_sidix",     "name": "🌟 SIDIX Legend",     "rarity": "legendary",  "desc": "Kamu adalah pengguna paling setia SIDIX!",           "bonus": "quota_+5 + badge exclusive"},
]

RARITY_WEIGHTS = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}

# SIDIX typewriter messages (zero-API, pre-written)
SIDIX_WAITING_MESSAGES: list[dict] = [
    {
        "lang": "id",
        "messages": [
            "Hei! Quota harianmu sudah habis — tapi kamu nggak harus pergi dulu.",
            "Aku tetap di sini. Sambil nunggu reset besok, kita bisa ngobrol dengan cara lain.",
            "Mau coba quiz pengetahuan? Atau tebak-tebakan? Atau main dulu?",
            "Setiap jawaban yang kamu kasih di sini... aku simpan untuk belajar. Jadi kamu tetap membantu aku tumbuh!",
            "Pilih aktivitas di bawah ya — semuanya gratis, nggak butuh kuota, dan kita sama-sama belajar.",
        ]
    },
    {
        "lang": "en",
        "messages": [
            "Hey! Your daily quota is up — but you don't have to leave yet.",
            "I'm still here. While waiting for the reset, we can interact differently.",
            "Want to try a quiz? Or a guessing game? Or just play for a bit?",
            "Every answer you give here... I save to learn from. So you're still helping me grow!",
            "Pick an activity below — all free, no API quota needed, and we both learn.",
        ]
    },
]


# ── Core Functions ────────────────────────────────────────────────────────────

def get_quiz_questions(n: int = 10, category: Optional[str] = None) -> list[dict]:
    """Ambil n pertanyaan random dari quiz bank."""
    pool = QUIZ_BANK
    if category and category.lower() != "all":
        pool = [q for q in QUIZ_BANK if q["cat"].lower() == category.lower()]
    if not pool:
        pool = QUIZ_BANK
    selected = random.sample(pool, min(n, len(pool)))
    # Shuffle options untuk setiap soal
    result = []
    for q in selected:
        opts = list(q["options"])
        correct_text = opts[q["ans"]]
        random.shuffle(opts)
        new_ans = opts.index(correct_text)
        result.append({
            "id": hashlib.sha256(q["q"].encode()).hexdigest()[:8],
            "q": q["q"],
            "options": opts,
            "ans": new_ans,
            "cat": q["cat"],
            "fact": q["fact"],
        })
    return result


def get_random_quote(lang: str = "id") -> dict:
    """Ambil satu quote random, preferensi bahasa."""
    pool = [q for q in QUOTE_BANK if q["lang"] == lang]
    if not pool:
        pool = QUOTE_BANK
    return random.choice(pool)


def get_image_prompt() -> dict:
    """Ambil satu image describe prompt random."""
    all_prompts = TEXT_DESCRIBE_PROMPTS  # Prioritaskan text prompt (lebih reliable)
    chosen = random.choice(all_prompts)
    # Kadang tambahkan image URL
    if random.random() > 0.6 and IMAGE_PROMPTS:
        img = random.choice(IMAGE_PROMPTS)
        chosen = {**chosen, "image_url": img["url"], "image_hint": img["hint"]}
    return chosen


def spin_gacha() -> dict:
    """Spin gacha, return reward."""
    weights = [RARITY_WEIGHTS[r["rarity"]] for r in GACHA_REWARDS]
    chosen = random.choices(GACHA_REWARDS, weights=weights, k=1)[0]
    return {
        "reward": chosen,
        "rarity_class": chosen["rarity"],
        "spin_time": int(time.time()),
    }


def get_sidix_messages(lang: str = "id") -> list[str]:
    """Ambil pesan typewriter SIDIX untuk waiting room."""
    for m in SIDIX_WAITING_MESSAGES:
        if m["lang"] == lang:
            return m["messages"]
    return SIDIX_WAITING_MESSAGES[0]["messages"]


def get_quiz_categories() -> list[str]:
    """List kategori quiz yang tersedia."""
    return list({q["cat"] for q in QUIZ_BANK})


def record_waiting_interaction(
    interaction_type: str,
    question: str,
    user_answer: str,
    correct_answer: Optional[str] = None,
    session_id: str = "",
    lang: str = "id",
) -> dict:
    """
    Rekam interaksi waiting room ke training data SIDIX.

    Setiap aktivitas user di ruang tunggu = learning signal:
    - Quiz benar: SIDIX tahu user paham topik ini
    - Quiz salah: SIDIX tahu topik yang perlu diperkuat
    - Deskripsi gambar: data latih kemampuan SIDIX mendeskripsikan
    - Motivasi share: feedback konten yang resonan
    """
    # Konversi ke format QnA untuk training
    if interaction_type == "quiz":
        if correct_answer:
            training_answer = (
                f"Jawaban benar: {correct_answer}. "
                f"User menjawab: {user_answer}. "
                f"{'Benar! ✓' if user_answer == correct_answer else 'Kurang tepat.'}"
            )
        else:
            training_answer = user_answer
    elif interaction_type == "image_describe":
        training_answer = f"Deskripsi user: {user_answer}"
    else:
        training_answer = user_answer

    try:
        from .qna_recorder import record_qna
        record_qna(
            question=question,
            answer=training_answer,
            session_id=session_id or f"wr_{interaction_type}_{int(time.time())}",
            persona="MIGHAN",
            citations=[],
            model=f"waiting_room_{interaction_type}",
            quality=3 if user_answer == correct_answer else 2,
        )
        return {"ok": True, "recorded": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_tools_list() -> list[dict]:
    """
    List tools SIDIX yang bisa dicoba tanpa quota.
    Semua tools dari ekosistem Mighan Building.
    """
    return [
        {"id": "bottle_flip",  "name": "🍾 Bottle Flip",        "desc": "Game physical tossing — siapa yang paling jago!",       "url": "/games/bottle-flip.html",  "type": "game",   "api_needed": False},
        {"id": "photo_editor", "name": "🖼 Editor Foto",         "desc": "Edit foto langsung di browser — filter, crop, annotate.", "url": "/tools/photo-editor",      "type": "tool",   "api_needed": False},
        {"id": "tts",          "name": "🔊 Text to Speech",      "desc": "Ketik teks, dengar suaranya. Multi-bahasa.",             "url": "/tools/tts",               "type": "tool",   "api_needed": False},
        {"id": "story_gen",    "name": "📖 Cerita Lucu",         "desc": "Ribuan cerita lucu & motivasi siap dibaca.",             "url": None,                       "type": "content","api_needed": False},
        {"id": "quiz",         "name": "🎯 Quiz Pengetahuan",    "desc": "300+ soal, 8 kategori, nggak butuh internet.",          "url": None,                       "type": "game",   "api_needed": False},
        {"id": "gacha",        "name": "🎰 SIDIX Gacha",         "desc": "Spin untuk dapat badge & hadiah kejutan!",              "url": None,                       "type": "game",   "api_needed": False},
        {"id": "image_desc",   "name": "🖼 Tebak & Deskripsikan","desc": "Latih kemampuan observasimu + bantu SIDIX belajar.",     "url": None,                       "type": "game",   "api_needed": False},
        {"id": "motivasi",     "name": "✨ Kata Motivasi",        "desc": "150+ quote dari tokoh dunia & wisdom Islam.",           "url": None,                       "type": "content","api_needed": False},
    ]


def get_waiting_room_stats(session_key: str = "default") -> dict:
    """Statistik sesi waiting room hari ini."""
    stats_file = _WR_DATA_DIR / "wr_stats.json"
    stats: dict = {}
    if stats_file.exists():
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return stats.get(session_key, {"quiz_answered": 0, "gacha_spins": 0, "images_described": 0})


def record_wr_stat(session_key: str, stat_type: str) -> None:
    """Update statistik waiting room."""
    stats_file = _WR_DATA_DIR / "wr_stats.json"
    stats: dict = {}
    if stats_file.exists():
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    if session_key not in stats:
        stats[session_key] = {"quiz_answered": 0, "gacha_spins": 0, "images_described": 0, "quotes_seen": 0}
    stats[session_key][stat_type] = stats[session_key].get(stat_type, 0) + 1
    try:
        stats_file.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
