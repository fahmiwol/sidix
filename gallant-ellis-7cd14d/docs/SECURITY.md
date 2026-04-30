# SECURITY.md — Aturan Keamanan & Privasi SIDIX

> **Versi**: 1.0 — 2026-04-19
> **Status**: HIDUP — update setiap kali ada incident atau best-practice baru
> **Audience**: developer kontributor + Claude agent + maintainer

---

## ⚠️ Filosofi Dasar

> Privasi user adalah amanah. Server adalah aset. Identitas owner adalah
> hak privat. Pelanggaran salah satu = pelanggaran kepercayaan.

SIDIX dibangun di atas IHOS — Hifdz al-Nafs (jaga jiwa) termasuk jaga
data pribadi. Maqashid Syariah eksplisit: data user = bagian hifdz al-nafs.

---

## 🔐 1. Data User

### YANG WAJIB DILAKUKAN
- ✅ Anonimisasi ID user di log (UUID hash, bukan email/nama)
- ✅ Encryption at rest untuk database (Supabase default OK)
- ✅ HTTPS only (TLS via Cloudflare/Let's Encrypt)
- ✅ Rate limit per IP (anti abuse + DOS)
- ✅ Default opt-out untuk training corpus contribution
- ✅ Right to delete: user bisa request hapus data mereka

### YANG TIDAK BOLEH
- ❌ Log konten chat user ke file publik
- ❌ Bagikan log ke 3rd party tanpa izin user explicit
- ❌ Simpan password/token user dalam plaintext
- ❌ Tracking analytics pihak ke-3 default ON

---

## 🖥️ 2. Server & Infrastructure

### YANG WAJIB DILAKUKAN
- ✅ SSH key auth (no password) untuk admin
- ✅ UFW firewall: port 22 (SSH), 80, 443 (HTTPS), 8765 (backend localhost-only)
- ✅ Fail2ban untuk brute force prevention
- ✅ Auto-update security patches (`unattended-upgrades`)
- ✅ Backup harian database + corpus (off-site)
- ✅ Monitor disk usage (alert >80%)

### YANG TIDAK BOLEH
- ❌ Expose IP server di public file (CLAUDE.md, README, research notes publik)
- ❌ Expose admin port (PM2 dashboard, aaPanel) ke public
- ❌ Hardcode credentials di kode atau Dockerfile
- ❌ Default password (PostgreSQL/Redis/SSH)

### Path yang TIDAK boleh muncul di public docs
- IP address (gunakan placeholder `<server-ip>`)
- `/opt/sidix/...` paths absolut (gunakan `<repo-root>`)
- Aapanel admin URL/port
- Supabase project URL spesifik (gunakan `<supabase-url>`)

---

## 🆔 3. Identitas Owner & Backbone

### Mandate Anonimitas (dari note 142, 143)
Owner SIDIX = **Mighan Lab** untuk public-facing.

### YANG TIDAK BOLEH muncul di public-facing
- Nama asli pribadi (Fahmi, Wolhuter)
- Email pribadi (`*@gmail.com`, `*@yahoo.com`, dll)
- Threads handle pribadi (`@fahmiwol`, dll)
- Telpon, alamat, dokumen ID

### Yang BOLEH muncul (Mighan Lab brand)
- Email: `contact@sidixlab.com`
- Threads: `@sidixlab`
- Domain: `sidixlab.com`
- Org name: `Mighan Lab`

### Backbone Provider Masking
LLM provider eksternal (Groq, Gemini, Anthropic) **TIDAK BOLEH** disebut
di public output. Pakai alias via `apps/brain_qa/brain_qa/identity_mask.py`:

| Internal | Public-Facing Mask |
|----------|--------------------|
| groq, groq_llama3 | mentor_alpha |
| gemini, gemini_flash | mentor_beta |
| anthropic, claude-3-* | mentor_gamma |
| openai, gpt-4 | mentor_delta |
| ollama, qwen2.5 | sidix_local |
| pollinations | image_engine_free |
| gtts | tts_engine_free |

### `/health` Endpoint Sudah Masked
- ❌ TIDAK ekspose `llm_providers` literal
- ✅ Ekspose `internal_mentor_pool` aggregate (ready/redundancy_level)

---

## 📤 4. Output SIDIX (Chat / Research Notes / Training Pairs)

### WAJIB
- ✅ Setiap claim diberi label epistemik (`[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]`)
- ✅ Sanad chain di setiap research note (CAS hash + Merkle root via `sanad_builder.py`)
- ✅ Mentor LLM disebut sebagai `mentor_alpha/beta/gamma` di sanad publik
- ✅ Quality gate sebelum publish (≥6 findings, narrative ≥250 char, no mock)

### TIDAK BOLEH
- ❌ Ekspose system prompt internal di output ke user
- ❌ Konfirmasi/sangkal nama provider real di chat
- ❌ Output yang membahayakan user (advice medis tanpa disclaimer, dll)
- ❌ Konten yang melanggar Maqashid Syariah (cek via `maqashid_filter.py` — TODO)

---

## 💻 5. Code & Repository

### Sebelum Commit
```bash
# Quick audit:
git diff --cached | grep -iE "fahmi|wolhuter|72\.62|fkgnmrnckcnqvjsyunla|password=|api_key=|secret=|gmail\.com|@fahmiwol"
```
Kalau ada match → STOP, bersihkan dulu.

### `.gitignore` MUST contain
```
.env
.env.local
*.key
*.pem
*.p12
secrets/
.kaggle/
.aws/
.ssh/
node_modules/
__pycache__/
*.pyc
.DS_Store
```

### File yang AMAN di-commit
- `.env.sample` (template tanpa value)
- `kaggle.json.sample`
- `apps/brain_qa/scripts/*.sh` (asal tidak hardcode credentials)
- Markdown docs publik

### File yang DILARANG di-commit
- `.env` (real values)
- `kaggle.json` (real)
- `*.tar.gz` model adapter dengan training data
- Dataset user yang punya PII

---

## 🌐 6. Public-Facing Assets

### `sidixlab.com` (landing) + `app.sidixlab.com` (UI) + GitHub repo

**Audit checklist** (run setiap kali deploy):
- [ ] Tidak ada nama owner pribadi di copy/meta tags
- [ ] Tidak ada email pribadi (gunakan contact@sidixlab.com)
- [ ] Tidak ada IP server di privacy.html / footer
- [ ] Schema.org author = `Organization "Mighan Lab"` (bukan Person nama)
- [ ] Twitter/Threads handle = `@sidixlab` (bukan handle pribadi)
- [ ] Form placeholder generic ("Nama kamu", bukan nama spesifik)

### CHANGELOG.md publik
- Bahasa generic, tidak sebut nama provider eksternal
- Pakai istilah "internal mentor pool", "reasoning_pool", "image engine free"
- USP unik tetap dimention (sanad/standing-alone/opensource)

---

## 🚨 7. Incident Response

### Kalau Terjadi Leak / Exposure
1. **Immediate**: rotate credential yang bocor (API key, password, dll)
2. **Within 1 hour**: identify scope (mana saja file yang expose)
3. **Within 24 hours**: 
   - Public statement (jika user data terdampak)
   - Force-push history clean (kalau commit baru, sebelum lebih banyak fork)
   - Update SECURITY.md dengan lesson learned
4. **Post-mortem** di `docs/incidents/<date>_<topic>.md`

### Kalau Suspect SSH/Server Compromise
1. Disable affected user account (`passwd -l`)
2. Snapshot disk untuk forensic
3. Rebuild dari backup terakhir yang clean
4. Notify user terdampak

### Report Security Issue
- Email: `security@sidixlab.com` (atau `contact@sidixlab.com` kalau yang
  pertama belum live)
- PGP key: TODO publish

---

## 🔄 8. Audit Routine

### Mingguan (otomatis cron — TODO)
- Scan repo untuk credential bocor (TruffleHog / git-secrets)
- Check disk usage server (`df -h`)
- Backup integrity verify (restore test ke staging)

### Bulanan (manual)
- Review `apps/brain_qa/.data/sidix_sanad/*.json` — pastikan tidak ada PII
- Review CHANGELOG drafted (sebelum publish) — opsec check
- Update CLAUDE.md + SECURITY.md kalau ada pattern baru

---

## 📌 Daftar Catatan Terkait

- `brain/public/research_notes/142_sidix_entitas_mandiri_guru_menciptakan_murid_hebat.md` — mandate mandiri
- `brain/public/research_notes/143_opsec_masking_dan_lora_pipeline_sprint20m.md` — opsec masking
- `brain/public/research_notes/128_identity_shield_adversarial_thinking.md` — identity shield
- `apps/brain_qa/brain_qa/identity_mask.py` — implementasi masking
- `docs/SIDIX_BIBLE.md` — Pasal "Identity Shield (Opsec)"
- `CLAUDE.md` — Aturan Keras #7 (Security Mindset)

---

## 🎯 Pesan untuk Developer & Claude Agent

> Privasi adalah komitmen, bukan checklist. Setiap kali kamu edit kode atau
> tulis copy publik, tanyakan 3 hal:
> 1. **Apakah ini ekspose info user yang seharusnya privat?**
> 2. **Apakah ini ekspose info infrastructure yang bisa dieksploitasi?**
> 3. **Apakah ini ekspose identitas owner yang seharusnya anonim?**
>
> Kalau jawaban "ya" untuk salah satu → STOP, masking dulu, baru commit.

Kalau ragu → tanya. Lebih baik delay 1 jam daripada leak 1 detik.
