# sidix-gateway-security-architecture

**Sumber:** claude-chat  
**Tanggal:** 2026-04-17  
**Tags:** security, gateway, fastapi, rate-limiting, injection-protection, architecture  

## Konteks

Bagaimana arsitektur keamanan terbaik untuk melindungi AI backend dari akses publik?

## Pengetahuan

Pattern Gateway sebagai security layer: semua traffic publik (Telegram, Threads, Web) harus lewat Gateway sebelum menyentuh core AI backend. Gateway bertugas: 1) Rate limiting per IP/user (token bucket, max N req/menit), 2) Input sanitization (strip null bytes, control chars, ANSI escape), 3) Injection detection (regex patterns untuk XSS, SQL injection, path traversal, template injection, eval/exec, subprocess), 4) CORS whitelist (hanya domain resmi), 5) API key auth untuk endpoint admin, 6) Audit log semua request, 7) Block semua route tidak terdaftar. Core backend (brain_qa) hanya listen di 127.0.0.1, tidak pernah diekspos ke publik. Nginx sebagai reverse proxy di depan Gateway. Ini industry standard untuk AI API protection.

---
*Diambil dari SIDIX MCP Knowledge Base*
