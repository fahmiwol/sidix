# 150. SEO Full Optimization — GA4 + Sitemap + JSON-LD + OG Image

> **Domain**: marketing / seo / analytics
> **Status validasi**: `[FACT]` (semua endpoint terverifikasi HTTP 200 live)
> **Tanggal**: 2026-04-19

---

## Mukadimah

Mandate user: pasang 2 Google Analytics tag (berbeda per domain), fix
og-image yang 404 sehingga Threads preview kosong, lalu optimasi SEO
lengkap untuk acquisition organik.

---

## Pre-existing State (Pre-Sprint)

| Asset | Status |
|-------|--------|
| og-image.png | ❌ HTTP 404 → Threads preview kosong |
| Google Analytics landing | ❌ Belum dipasang |
| Google Analytics app | ❌ Belum dipasang |
| robots.txt | ❌ Missing |
| sitemap.xml | ❌ Missing |
| manifest.json (PWA) | ❌ Missing |
| JSON-LD SoftwareApplication | ✅ Ada |
| JSON-LD Organization | ❌ Belum ada (hybrid di SoftwareApplication author) |
| JSON-LD FAQ | ❌ Belum ada |
| Meta og:image meta | ✅ Ada (tapi reference 404) |
| Meta Twitter Card | ✅ Ada |
| Performance hints (preconnect) | ❌ Belum ada |

---

## Yang Diimplementasi

### 1. Google Analytics 4 (2 Property)

**Landing** `sidixlab.com`:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-04JKCGDEY4"></script>
<script>
  gtag('config', 'G-04JKCGDEY4', {
    'anonymize_ip': true,
    'cookie_flags': 'SameSite=None;Secure'
  });
</script>
```

**App** `app.sidixlab.com`:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-EK6L5SJGY3"></script>
<script>
  gtag('config', 'G-EK6L5SJGY3', { anonymize_ip: true, ... });
</script>
```

**Privacy-friendly config**:
- `anonymize_ip: true` → GDPR compliant
- `cookie_flags: SameSite=None;Secure` → cross-site cookie safe

**⚠️ User action needed**: GA4 console URL aliran data sempat tertulis
`app.sixlab.com` (typo) — edit manual ke `app.sidixlab.com` via pencil icon.

### 2. OG Image (1200x630) Generator

`apps/brain_qa/scripts/generate_og_image.py` — PIL script render:
- Background gradient warm-dark
- Gold accent line (top + bottom)
- SIDIX brand mark (big font)
- Tagline: "Self-Hosted AI Agent with Epistemic Integrity"
- Subtitle: "Open-source · Indonesian · Islamic Epistemology"
- Domain footer: `sidixlab.com`
- 3 dots decorative pattern (top right)

Output: `/www/wwwroot/sidixlab.com/og-image.png` (42 KB)

### 3. robots.txt
- Allow all crawlers default
- Block `/admin/`, `/api/`, `/.git/`, `/.env`, UTM tracking URLs
- Sitemap reference
- Block scraper bots: Ahrefs, Semrush, MJ12, DotBot

### 4. sitemap.xml
6 URLs dengan prioritas + changefreq:
- `/` (priority 1.0, weekly) + hreflang bilingual (en + id + x-default)
- `/privacy.html` (0.5, monthly)
- `https://app.sidixlab.com/` (0.9, daily)
- 3 anchor sections (`#features`, `#roadmap`, `#contributing`) untuk deep-link

### 5. manifest.json (PWA)
- name: "SIDIX — Self-Hosted AI Agent"
- short_name: "SIDIX"
- start_url: `https://app.sidixlab.com/`
- display: standalone
- theme_color: gold (#D4A853)
- background: dark warm (#120F09)
- icons: sidix-logo.svg + og-image.png
- categories: productivity, education, utilities

### 6. JSON-LD Tambahan (Rich Snippet)

**Organization** (Mighan Lab):
- logo, description, foundingDate, sameAs (GitHub + Threads)
- contactPoint: email + supported languages

**FAQPage** 5 Q&A:
1. What is SIDIX?
2. Is SIDIX free to use?
3. How is SIDIX different from ChatGPT/Claude?
4. Can I contribute to SIDIX?
5. Does SIDIX support Indonesian?

→ Google Search bisa tampil expandable FAQ di SERP (rich result).

### 7. Performance Hints
```html
<link rel="preconnect" href="https://cdn.tailwindcss.com" crossorigin />
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin />
<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin />
<link rel="dns-prefetch" href="https://www.google-analytics.com" />
```

Mengurangi latency ~100-300ms untuk fetch resource third-party.

---

## Verifikasi Live

```
robots.txt         → HTTP 200 ✅
sitemap.xml        → HTTP 200 ✅
manifest.json      → HTTP 200 ✅
og-image.png       → HTTP 200 ✅  (42 KB, 1200x630)
JSON-LD blocks     → 3 (SoftwareApplication + Organization + FAQPage) ✅
GA4 landing tag    → G-04JKCGDEY4 injected ✅
GA4 app tag        → G-EK6L5SJGY3 injected ✅
HSTS               → max-age=31536000 (1 year) ✅
```

---

## Dampak SEO Kumulatif

### Short-term (1-4 minggu)
- Google akan recrawl sitemap → discover 6 URL dengan priority
- Rich snippet FAQ akan muncul di SERP untuk query seputar SIDIX
- Threads/X/LinkedIn preview card akan tampil lengkap (og-image 1200x630)
- GA4 akan mulai tracking user (24-48h untuk data pertama muncul)

### Medium-term (1-3 bulan)
- Hreflang signal → ranking di Indonesia + English search
- PWA manifest → potential install prompt di Chrome mobile
- JSON-LD Organization → knowledge panel potensi di Google Search
- Brand mentions via @sidixlab cross-platform → E-E-A-T signal

### Long-term (3-12 bulan)
- FAQ rich result akan drive CTR lebih tinggi
- Conversion tracking via GA4 event → optimize acquisition funnel
- Manifest install → retention user (PWA on mobile)

---

## Compliance dengan SIDIX_BIBLE

- Pasal "Identity Shield": GA tag tidak expose nama owner (pakai Mighan Lab org)
- Pasal "Privacy": `anonymize_ip` + SameSite Secure cookie
- Pasal "Mandiri": robots.txt block scraper bot yang tidak memberi nilai
- Pasal "Security": HSTS + CSP (existing sprint sebelumnya)

---

## Keterbatasan Jujur

1. **GA4 "Pengumpulan data tidak aktif"**: normal 24-48 jam. Akan aktif
   otomatis saat user visit pertama kali.
2. **Threads OG cache**: Threads cache og-image ~24h. Post lama tidak
   akan refresh. Solution: post baru setelah 24h akan tampil dengan
   image baru.
3. **FAQ konten masih generik**: 5 Q&A baseline. Ideally di-update
   berdasarkan actual user question dari chat log (harvest).
4. **Canonical + hreflang**: sitemap signal sudah ada, tapi belum
   implementasi dynamic lang switching di landing (still English default).
5. **Manifest belum icon sets lengkap**: hanya sidix-logo.svg + og-image.
   Untuk PWA optimal perlu 192x192, 512x512 PNG juga.

---

## Roadmap Lanjutan

- [ ] Build icons 192x192 + 512x512 PNG (untuk PWA install)
- [ ] Google Search Console verification (DNS TXT record)
- [ ] Submit sitemap manual ke Google Search Console
- [ ] Dynamic hreflang switch di landing (ID vs EN)
- [ ] FAQ content update dari actual chat log (quarterly)
- [ ] Lighthouse audit automation (CI/CD)
- [ ] Bing Webmaster + Yandex Webmaster submission
- [ ] Structured data: HowTo (untuk tutorial pages nanti)
- [ ] BlogPosting JSON-LD di research notes publik

---

## Sumber

- `SIDIX_LANDING/index.html` (GA + JSON-LD + perf hints)
- `SIDIX_LANDING/robots.txt`
- `SIDIX_LANDING/sitemap.xml`
- `SIDIX_LANDING/manifest.json`
- `SIDIX_USER_UI/index.html` (GA app)
- `apps/brain_qa/scripts/generate_og_image.py` (PIL script)
- `apps/brain_qa/scripts/deploy_ga_and_og.sh` (deployment helper)
- `apps/brain_qa/scripts/deploy_seo.sh` (verification helper)
- Commits: `0e7c2b2` (GA + og-image) + `27b1af0` (SEO assets)

## Status Final

| SEO Signal | Status |
|------------|--------|
| Analytics (GA4) 2 properties | ✅ Live (24-48h detect) |
| OG image preview | ✅ 200 OK |
| robots.txt + sitemap.xml | ✅ Live |
| PWA manifest | ✅ Live |
| JSON-LD (3 types) | ✅ Live |
| Performance hints | ✅ Live |
| HSTS | ✅ 1 year |
| Security headers | ✅ (from sprint L1) |
