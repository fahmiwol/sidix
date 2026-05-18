# Jariyah Hub (contoh OSS)

Stack ringan **Ollama + Open WebUI** untuk replikasi komunitas (edukasi / amal teknis). **Terpisah** dari inti Python `apps/brain_qa` — lihat `AGENTS.md` dan `brain/public/research_notes/31_sidix_feeding_log.md`.

## Langkah cepat

1. `cp docker-compose.example.yml docker-compose.yml` (atau salin manual di Windows).
2. `cp .env.example .env` lalu set `WEBUI_SECRET_KEY` (mis. output `openssl rand -hex 32`).
3. `docker compose up -d` dari folder ini.
4. Buka `http://localhost:${OPEN_WEBUI_PORT:-3000}` — konfigurasi admin & RAG mengikuti dokumentasi upstream Open WebUI.

## Keamanan

- Jangan publish `.env` atau `WEBUI_SECRET_KEY` lemah.
- Port UI ke internet publik = permukaan serangan: gunakan TLS, batas akses, dan kebijakan signup sesuai docs Open WebUI.
