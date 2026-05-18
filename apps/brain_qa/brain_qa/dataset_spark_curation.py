"""
dataset_spark_curation.py — SIDIX Spark Ethical Dataset Curator
===============================================================
Adobe Firefly-inspired ethical dataset curation pipeline.

Prinsip SIDIX Spark:
  1. LICENSED-ONLY — Hanya data dengan license yang jelas
  2. PROVENANCE — Track sumber setiap gambar
  3. BIAS AUDIT — Deteksi & laporkan bias sebelum training
  4. TRANSPARENCY — Content Credentials untuk setiap output

Sumber yang diizinkan (whitelist):
  ✅ Agency-owned (Google Drive)
  ✅ CC0 / CC-BY / CC-BY-SA (Wikimedia, Unsplash, Pexels)
  ✅ Public domain
  ✅ Self-generated (RunPod image gen)

Sumber yang DITOLAK (blacklist):
  ❌ Pinterest — ToS violation + copyright risk
  ❌ Instagram — ToS Meta violation
  ❌ Shutterstock / Adobe Stock / Getty — copyrighted
  ❌ Canva — proprietary content
  ❌ Tumblr / DeviantArt / ArtStation — user-generated, unclear rights

Content Credentials (C2PA-like):
  - Setiap dataset entry punya manifest: source, license, acquisition_date,
    curator_agent, bias_score, quality_score
  - Manifest di-sign dengan HMAC untuk tamper-evidence
  - Output bisa di-verify kapan saja

Research notes:
  - 322 SIDIX Spark Ethical Dataset Curator
  - Adobe Firefly approach: train only on licensed content + public domain
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Constants ─────────────────────────────────────────────────────────────────

WHITELISTED_LICENSES = {
    "agency_owned",
    "cc0",
    "cc-by",
    "cc-by-sa",
    "unsplash_license",
    "pexels_license",
    "public_domain",
    "self_generated",
}

BLACKLISTED_SOURCES = {
    "pinterest",
    "instagram",
    "tumblr",
    "deviantart",
    "artstation",
    "behance",
    "dribbble",
    "facebook",
    "twitter",
    "x",
}

BIAS_CATEGORIES = ["gender", "race", "age", "western_centric", "professional_only"]


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


# ── 1. License Validator ──────────────────────────────────────────────────────


def validate_license(entry: dict) -> dict:
    """Validate apakah license dari entry di whitelist.

    Returns: is_valid, license_type, risk_level, notes
    """
    source = entry.get("source", "").lower()
    license_str = entry.get("license", "").lower().replace(" ", "_").replace("-", "_")

    # Check blacklisted source
    if source in BLACKLISTED_SOURCES:
        return _ok({
            "is_valid": False,
            "license_type": source,
            "risk_level": "CRITICAL",
            "notes": f"Source '{source}' ada di blacklist. Scraping = ToS violation + copyright risk.",
            "action": "REJECT",
        })

    # Check whitelisted licenses
    for wl in WHITELISTED_LICENSES:
        if wl.lower() in license_str:
            return _ok({
                "is_valid": True,
                "license_type": wl,
                "risk_level": "LOW",
                "notes": f"License '{wl}' di whitelist. Aman untuk training.",
                "action": "ACCEPT",
            })

    # Unknown license
    return _ok({
        "is_valid": False,
        "license_type": license_str or "unknown",
        "risk_level": "HIGH",
        "notes": (
            f"License '{license_str}' tidak dikenal. "
            f"Hanya whitelist: {', '.join(WHITELISTED_LICENSES)}"
        ),
        "action": "REVIEW",
    })


# ── 2. Content Credentials (C2PA-like) ────────────────────────────────────────


def create_content_credential(entry: dict, curator: str = "sidix-spark") -> dict:
    """Create Content Credential manifest untuk satu dataset entry.

    Manifest fields:
      - asset_id: unique identifier
      - source: sumber data
      - license: jenis license
      - acquisition_date: kapan di-collect
      - curator_agent: siapa yang curate
      - provenance_hash: hash dari entry untuk integrity
      - bias_audit: hasil audit bias
      - quality_score: skor kualitas
      - hmac_signature: signature untuk tamper-evidence
    """
    asset_id = hashlib.sha256(
        json.dumps(entry, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]

    manifest = {
        "asset_id": asset_id,
        "source": entry.get("source", "unknown"),
        "license": entry.get("license", "unknown"),
        "acquisition_date": datetime.now(timezone.utc).isoformat(),
        "curator_agent": curator,
        "provenance_hash": hashlib.sha256(
            json.dumps(entry, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "bias_audit": entry.get("bias_audit", {}),
        "quality_score": entry.get("quality_score", {}),
        "dimensions": {
            "width": entry.get("width"),
            "height": entry.get("height"),
        },
        "tags": entry.get("tags", []),
    }

    # HMAC signature (simple: SHA256 dengan secret key)
    secret = os.environ.get("SPARK_CREDENTIAL_SECRET", "sidix-spark-default-secret")
    hmac_input = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    manifest["hmac_signature"] = hashlib.sha256(
        (hmac_input + secret).encode()
    ).hexdigest()[:32]

    return manifest


def verify_content_credential(manifest: dict) -> bool:
    """Verify apakah manifest sudah di-tamper."""
    stored_hmac = manifest.pop("hmac_signature", "")
    secret = os.environ.get("SPARK_CREDENTIAL_SECRET", "sidix-spark-default-secret")
    hmac_input = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    expected = hashlib.sha256((hmac_input + secret).encode()).hexdigest()[:32]
    manifest["hmac_signature"] = stored_hmac
    return stored_hmac == expected


# ── 3. Bias Audit ─────────────────────────────────────────────────────────────


def audit_bias(entries: list[dict]) -> dict:
    """Audit dataset untuk bias indicators.

    Metrik:
      - Gender representation (based on tags/keywords)
      - Western vs non-western content
      - Professional vs amateur style
      - Age diversity
    """
    if not entries:
        return _fallback("No entries to audit")

    # Keyword-based heuristic bias detection
    gender_counts = {"male": 0, "female": 0, "neutral": 0}
    western_indicators = 0
    professional_indicators = 0
    total = len(entries)

    for e in entries:
        text = json.dumps(e).lower()

        # Gender
        if any(kw in text for kw in ["man", "male", "boy", "guy", "pria", "laki"]):
            gender_counts["male"] += 1
        elif any(kw in text for kw in ["woman", "female", "girl", "lady", "wanita", "perempuan"]):
            gender_counts["female"] += 1
        else:
            gender_counts["neutral"] += 1

        # Western-centric
        western_keywords = ["western", "european", "american", "caucasian", "blonde", "blue_eyes"]
        if any(kw in text for kw in western_keywords):
            western_indicators += 1

        # Professional vs amateur
        prof_keywords = ["studio", "professional", "commercial", "corporate", "brand"]
        if any(kw in text for kw in prof_keywords):
            professional_indicators += 1

    # Bias scores (0-100, lower = less biased)
    gender_balance = min(100, round(
        100 - abs(gender_counts["male"] - gender_counts["female"]) / max(total, 1) * 100
    ))
    western_ratio = round(western_indicators / max(total, 1) * 100, 1)
    professional_ratio = round(professional_indicators / max(total, 1) * 100, 1)

    bias_flags = []
    if gender_balance < 60:
        bias_flags.append("GENDER_IMBALANCE — male vs female ratio tidak seimbang")
    if western_ratio > 70:
        bias_flags.append("WESTERN_CENTRIC — >70% konten menunjukkan karakteristik western")
    if professional_ratio > 80:
        bias_flags.append("PROFESSIONAL_HOMOGENIZATION — terlalu banyak konten studio/commercial")

    overall_bias_score = round(
        (gender_balance + (100 - western_ratio) + (100 - professional_ratio)) / 3, 1
    )

    return _ok({
        "total_entries": total,
        "gender_distribution": gender_counts,
        "gender_balance_score": gender_balance,
        "western_content_percentage": western_ratio,
        "professional_content_percentage": professional_ratio,
        "overall_bias_score": overall_bias_score,
        "bias_flags": bias_flags if bias_flags else ["None detected"],
        "recommendation": (
            "Dataset baik untuk training jika: gender_balance >= 60, western <= 70%, "
            "professional <= 80%, overall_bias_score >= 70."
        ),
    })


# ── 4. Ethical Dataset Pipeline ───────────────────────────────────────────────


def curate_ethical_dataset(
    entries: list[dict],
    output_path: str = "dataset/spark_curated.jsonl",
    curator: str = "sidix-spark",
) -> dict:
    """Curate dataset dengan ethical filtering (Adobe Firefly approach).

    Pipeline:
      1. Validate license per entry
      2. Reject blacklisted sources
      3. Audit bias
      4. Create Content Credentials
      5. Export curated dataset
    """
    if not entries:
        return _fallback("No entries to curate")

    accepted = []
    rejected = []
    credentials = []
    license_distribution = {}

    for entry in entries:
        validation = validate_license(entry)
        val_data = validation.get("data", {})

        if val_data.get("is_valid"):
            # Add bias audit to entry
            # (simplified: per-entry audit skipped, batch audit after)
            entry["validated_license"] = val_data.get("license_type")
            entry["risk_level"] = val_data.get("risk_level")

            # Create content credential
            cred = create_content_credential(entry, curator=curator)
            entry["content_credential"] = cred
            credentials.append(cred)

            accepted.append(entry)

            lic = val_data.get("license_type", "unknown")
            license_distribution[lic] = license_distribution.get(lic, 0) + 1
        else:
            rejected.append({
                "entry": entry,
                "reason": val_data.get("notes", "Unknown"),
                "risk_level": val_data.get("risk_level", "HIGH"),
            })

    # Batch bias audit pada accepted entries
    bias_audit = audit_bias(accepted)

    # Export curated dataset
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in accepted:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        return _fallback(f"Export error: {exc}")

    bias_data = bias_audit.get("data", {})

    return _ok({
        "total_input": len(entries),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "acceptance_rate": round(len(accepted) / len(entries) * 100, 1),
        "license_distribution": license_distribution,
        "bias_audit": bias_data,
        "credentials_count": len(credentials),
        "output_path": output_path,
        "ethical_compliance": {
            "licensed_only": True,
            "provenance_tracked": True,
            "bias_audited": True,
            "tamper_evident": True,
        },
        "notes": (
            "Dataset telah di-curate dengan pendekatan Adobe Firefly: "
            "hanya licensed content yang diterima, setiap entry punya Content Credential, "
            "dan telah di-audit untuk bias."
        ),
    })


# ── 5. Source Provenance Report ───────────────────────────────────────────────


def generate_provenance_report(credentials: list[dict]) -> dict:
    """Generate laporan provenance untuk dataset (untuk compliance)."""
    sources = {}
    licenses = {}
    curators = {}
    date_range = {"earliest": None, "latest": None}

    for cred in credentials:
        src = cred.get("source", "unknown")
        lic = cred.get("license", "unknown")
        cur = cred.get("curator_agent", "unknown")
        date = cred.get("acquisition_date", "")

        sources[src] = sources.get(src, 0) + 1
        licenses[lic] = licenses.get(lic, 0) + 1
        curators[cur] = curators.get(cur, 0) + 1

        if date:
            if date_range["earliest"] is None or date < date_range["earliest"]:
                date_range["earliest"] = date
            if date_range["latest"] is None or date > date_range["latest"]:
                date_range["latest"] = date

    return _ok({
        "total_assets": len(credentials),
        "sources": sources,
        "licenses": licenses,
        "curators": curators,
        "date_range": date_range,
        "compliance_standard": "SIDIX Spark Ethical Dataset (Adobe Firefly-inspired)",
        "requirements": [
            "All assets have verifiable license",
            "No blacklisted sources",
            "Provenance tracked per asset",
            "Bias audited",
            "Tamper-evident credentials",
        ],
    })


# ── 6. Pinterest Warning ──────────────────────────────────────────────────────


def get_pinterest_warning() -> dict:
    """Return detailed warning tentang risiko scraping Pinterest.

    Untuk edukasi bos dan preventif.
    """
    return _ok({
        "source": "Pinterest",
        "status": "BLACKLISTED",
        "risk_level": "CRITICAL",
        "reasons": [
            "Pinterest ToS explicit prohibits scraping: 'You may not access or use Pinterest for any purpose other than your own personal use'",
            "Pinterest content = user-generated, tidak selalu free to use",
            "Pinners grant Pinterest broad license, tapi TIDAK memberi license ke pihak ketiga untuk AI training",
            "Scraping Pinterest = breach of contract + potential copyright infringement",
            "Reddit vs Perplexity (2025): scraping dengan bypass rate limits = DMCA Section 1201 violation",
            "Meta v. Bright Data (2023-2024): contract-based claims viable even when CFAA claims fail",
        ],
        "legal_basis": [
            "Pinterest Terms of Service: policy.pinterest.com/en/terms-of-service",
            "DMCA Section 1201: anti-circumvention provisions",
            "Computer Fraud and Abuse Act (CFAA): unauthorized access",
        ],
        "alternatives": [
            "Wikimedia Commons (CC-licensed, 100M+ files)",
            "Unsplash API (free commercial use)",
            "Pexels API (free commercial use)",
            "Google Drive agency assets (100% owned)",
            "LAION-5B metadata (open dataset, CC-BY 4.0)",
            "Self-generated via RunPod (SDXL/Flux)",
        ],
        "recommendation": "Gunakan alternatives di atas. Jangan scrape Pinterest.",
    })
