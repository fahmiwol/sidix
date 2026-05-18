# Security Policy — SIDIX

> **Maintained by:** Tiranyx × Mighan Lab
> **Contact:** security@sidixlab.com · contact@sidixlab.com
> **Last updated:** 2026-04-23

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.7.x (current) | ✅ Active |
| v0.6.x | ✅ Critical fixes only |
| < v0.6 | ❌ End of life |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Send a private report to **security@sidixlab.com** with:

1. **Description** — what is the vulnerability and where
2. **Steps to reproduce** — minimal reproduction steps
3. **Impact** — what an attacker could do
4. **Suggested fix** (optional but welcome)

We will acknowledge within **48 hours** and aim to patch within **7 days** for critical issues.

---

## Security Architecture

SIDIX is built standing-alone — no cloud vendor dependency in the inference path.
All data processing happens on self-hosted infrastructure.

### What we protect

| Asset | Protection |
|-------|-----------|
| User conversations | Not logged to public files. Session data in-memory only. |
| Corpus knowledge | Hafidz Merkle ledger — tamper-evident, CAS-hashed |
| API endpoints | Rate limiting per IP + Maqashid ethical gate |
| Identity | Provider masking — no external service names exposed to users |
| Code | Pre-commit audit: no credentials, IPs, or personal identifiers |

### Security layers active

- **HTTP headers**: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Rate limiting**: per-IP and per-client-id daily quota
- **Prompt injection detection**: `g1_policy.detect_prompt_injection()`
- **Ethical filter**: Maqashid mode gate — 6 exit paths in ReAct loop
- **Network middleware**: Multi-layer request filtering

---

## Responsible Disclosure

We follow a **90-day coordinated disclosure** policy:

1. Reporter submits privately → we confirm receipt (≤48h)
2. We investigate and develop fix (≤7 days for critical, ≤30 days for others)
3. Fix deployed to production
4. Public disclosure after fix is live (coordinated with reporter)

We will credit reporters in our security advisories unless anonymity is requested.

---

## Out of Scope

The following are **not** considered vulnerabilities for this project:

- Rate limiting bypasses via legitimate distributed clients
- Missing security headers on non-production subdomains
- Theoretical attacks requiring physical server access
- Denial of service via extremely large legitimate inputs (report as bug instead)
- Issues in third-party dependencies — report directly to upstream

---

## Build & Dependency Security

- Dependencies declared in `requirements.txt` (Python) and `package.json` (Node)
- No vendored / bundled copies of dependencies
- Environment secrets loaded via `os.getenv()` only — never hardcoded
- `.env` files excluded from git via `.gitignore`
- Pre-commit audit pattern: `grep -E "api_key=|password=|secret=|Bearer\s" --include=*.py`

---

*SIDIX is open source (MIT License). Security is a shared responsibility.*
*Collaboration: [tiranyx.co.id](https://tiranyx.co.id) × [mighan.com](https://mighan.com)*
