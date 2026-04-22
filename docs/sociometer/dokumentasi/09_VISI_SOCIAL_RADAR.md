# VISI SOCIAL RADAR (Socio-Meter)
## Pivot produk — analitik sosial AI-native

**Versi:** 1.0 | **Status:** Rencana | **Klasifikasi:** Visi produk (disanitasi dari paket arsip kerja)

---

## 1. Ringkasan eksekutif

**Social Radar** memfokuskan Socio-Meter pada **analitik sosial**: pemantauan kompetitor, listening multi-platform, dan laporan padat data — bukan sebagai sekadar “generator konten” semata.

Empat pilar visi:

1. **Dashboard padat informasi** — banyak metrik dalam satu layar (polar kokpit), cocok untuk operator yang sudah nyaman dengan analytics.
2. **Lapisan plugin MCP** — host AI mitra mengonsumsi alat SIDIX lewat profil konektor teknis (stdio/HTTP), tanpa menjadikan merek host sebagai identitas produk.
3. **Ekstensi peramban** — pengumpulan jejak interaksi di bawah **persetujuan bertingkat** dan kebijakan privasi (lihat ERD: `consent_level`).
4. **Self-hosted** — inferensi, korpus, dan media tetap di jalur **standing alone** SIDIX.

---

## 2. Alur nilai

```
Pengguna / operator
  → ekstensi peramban atau konektor MCP (opt-in)
  → Gatekeeper: Maqashid + Naskh + label Sanad
  → Inti SIDIX (Raudah bila orkestrasi multi-langkah)
  → Laporan + metrik + pasangan latih berkualitas (Jariyah)
  → Muhasabah berkala (skor CQF, regresi, rollback model)
```

---

## 3. Anti-scope (fase awal)

- Generator video penuh, autoposting massal, atau fitur yang membutuhkan GPU tier baru **bukan** fokus MVP Social Radar.
- Integrasi di dokumen ini tidak menyebut merek host AI, IDE, atau identitas pribadi; rujukan implementasi memakai **slug konektor** dan **profil host** generik.

---

## 4. Rujukan dokumen

| Topik | File |
|-------|------|
| Strategi & Jariyah | `../strategi/01_STRATEGI_SOCIOMETER.md` |
| PRD & CQF | `../prd/02_PRD_SOCIOMETER.md` |
| Skema data | `../erd/03_ERD_SOCIOMETER.md` |
| Rencana sprint | `../plan/06_IMPLEMENTATION_SOCIOMETER.md` |
