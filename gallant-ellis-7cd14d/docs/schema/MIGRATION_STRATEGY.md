# SIDIX Agency OS — Database Migration Strategy (Sprint 8a)

> **Status:** Blueprint — siap dieksekusi saat PostgreSQL instance tersedia  
> **Schema source:** `docs/schema/SIDIX_AGENCY_OS_CORE.sql`  
> **Tanggal:** 2026-04-24

---

## Prinsip

1. **Non-destructive by default** — migration baru selalu `ADD COLUMN` / `CREATE TABLE IF NOT EXISTS`, bukan `DROP`/`ALTER TYPE`.
2. **No hardcode credentials** — gunakan env var `DATABASE_URL` (format: `postgresql://user:pass@host:port/db`).
3. **Reversible** — tiap migration punya file `up.sql` dan `down.sql`.
4. **Audit trail** — tabel `audit_logs` (sudah ada di schema) mencatat setiap operasi DDL/DML signifikan.

---

## Tooling yang Dipilih: `psql` + file SQL manual (MVP)

Untuk Sprint 8a, migration dilakukan secara manual via `psql`. Alasan:
- Tidak perlu dependency tambahan (Alembic, Flyway) di fase awal
- Schema masih berubah cepat — otomatisasi bisa ditambahkan di Sprint 8c setelah schema stabil

### Cara Apply (Sprint 8a)

```bash
# 1. Pastikan DATABASE_URL tersedia
export DATABASE_URL="postgresql://sidix_user:secret@localhost:5432/sidix_db"

# 2. Apply schema
psql "$DATABASE_URL" -f docs/schema/SIDIX_AGENCY_OS_CORE.sql

# 3. Verifikasi tabel
psql "$DATABASE_URL" -c "\dt"
```

### Cara Rollback (jika diperlukan)

```bash
# Hapus semua tabel SIDIX (HATI-HATI: data hilang)
psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

---

## Urutan Tabel (dependency order)

```
agencies
  └── clients (FK: agency_id)
        └── conversations (FK: client_id)
              └── messages (FK: conversation_id)
                    └── training_pairs (FK: message_id — opsional)

kg_nodes (independent)
  └── kg_relationships (FK: source_id, target_id)

health_checks (independent)
audit_logs (independent)
```

---

## Environment Variables yang Diperlukan

| Var | Keterangan | Contoh |
|-----|------------|--------|
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql://sidix:secret@localhost:5432/sidix_db` |
| `SIDIX_DB_POOL_SIZE` | Connection pool size (opsional, default 5) | `5` |
| `SIDIX_DB_ECHO` | Log semua SQL query (opsional, default off) | `0` |

**Jangan commit nilai aktual** — simpan di `.env` (sudah di `.gitignore`).

---

## Rencana Migrasi Bertahap

| Sprint | Perubahan Schema | Status |
|--------|-----------------|--------|
| 8a | Core tables: agencies, clients, conversations, messages, training_pairs, kg_nodes, kg_relationships, health_checks, audit_logs | **Siap (blueprint)** |
| 8b | Tambah tabel `assets` (image/video/audio generated) | Planned |
| 8c | Tambah tabel `brand_guidelines`, `campaigns` | Planned |
| 8d | Indeks full-text search, partisi `messages` by client_id | Planned |

---

## Koneksi dari `brain_qa`

Saat Sprint 8b, `apps/brain_qa/brain_qa/db/` akan berisi:
- `connection.py` — pool manager (asyncpg atau psycopg2)
- `repositories/` — satu file per domain (branch_repo.py, feedback_repo.py, training_repo.py)

Sampai Sprint 8b selesai, feedback tetap disimpan ke file JSONL (`data/feedback.jsonl`) — lihat `agent_serve.py` endpoint `/agent/feedback`.
