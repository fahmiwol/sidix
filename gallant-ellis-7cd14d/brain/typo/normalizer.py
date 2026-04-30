"""
Layer 1: Text Normalizer
Koreksi typo + ekspansi abbreviasi untuk input Bahasa Indonesia.
Prinsip: jangan mempermalukan user — koreksi diam-diam, laporkan hanya kalau diminta.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# TYPO DICTIONARY — 120+ entri
# ---------------------------------------------------------------------------
TYPO_DICTIONARY: dict[str, str] = {
    # Informal / gaul Indonesia
    "gmn": "bagaimana",
    "bgmn": "bagaimana",
    "gimana": "bagaimana",
    "knp": "kenapa",
    "dmn": "dimana",
    "dg": "dengan",
    "dgn": "dengan",
    "tdk": "tidak",
    "udh": "sudah",
    "sdh": "sudah",
    "blm": "belum",
    "blom": "belum",
    "msh": "masih",
    "msih": "masih",
    "utk": "untuk",
    "krn": "karena",
    "karna": "karena",
    "spy": "supaya",
    "jg": "juga",
    "jga": "juga",
    "tp": "tapi",
    "tpi": "tapi",
    "sm": "sama",
    "yg": "yang",
    "ny": "nya",
    "gw": "saya",
    "gue": "saya",
    "gw": "saya",
    "lu": "kamu",
    "lo": "kamu",
    "loe": "kamu",
    "nih": "ini",
    "tuh": "itu",
    "nggak": "tidak",
    "gak": "tidak",
    "enggak": "tidak",
    "ga": "tidak",
    "emang": "memang",
    "banget": "sekali",
    "bgt": "sekali",
    "aja": "saja",
    "doang": "saja",
    "cuma": "hanya",
    "klo": "kalau",
    "klu": "kalau",
    "kl": "kalau",
    "kal": "kalau",
    "biar": "supaya",
    "bgt": "sekali",
    "byk": "banyak",
    "bnyk": "banyak",
    "lsg": "langsung",
    "lngsng": "langsung",
    "mksd": "maksud",
    "mksud": "maksud",
    "sjrh": "sejarah",
    "ktmu": "ketemu",
    "ktemu": "ketemu",
    "trs": "terus",
    "ters": "terus",
    "terus2": "terus-menerus",
    "skrg": "sekarang",
    "skrang": "sekarang",
    "dlu": "dulu",
    "dl": "dulu",
    "bs": "bisa",
    "bsa": "bisa",
    "jd": "jadi",
    "jdi": "jadi",
    "td": "tadi",
    "tdi": "tadi",
    "gt": "begitu",
    "gitu": "begitu",
    "gini": "begini",
    "pke": "pakai",
    "pkai": "pakai",
    "pkek": "pakai",
    "lbh": "lebih",
    "lebh": "lebih",
    "hrs": "harus",
    "hrus": "harus",
    "sdkt": "sedikit",
    "sdikit": "sedikit",
    "bener": "benar",
    "bnr": "benar",
    "mnrut": "menurut",
    "mngkin": "mungkin",
    "mgkin": "mungkin",
    "sbnrnya": "sebenarnya",
    "sbnarnya": "sebenarnya",
    # Typo teknis
    "srvr": "server",
    "sever": "server",
    "servr": "server",
    "vsp": "vps",
    "deploi": "deploy",
    "dipploy": "deploy",
    "deploymen": "deployment",
    "makashid": "maqashid",
    "maqasid": "maqashid",
    "maqosid": "maqashid",
    "maqasihd": "maqashid",
    "nasf": "nafs",
    "jiawa": "jiwa",
    "jiawa": "jiwa",
    "raudha": "raudah",
    "rawdah": "raudah",
    "sanand": "sanad",
    "sannad": "sanad",
    "jariyya": "jariyah",
    "jariya": "jariyah",
    "jariyyah": "jariyah",
    "cppu": "cpu",
    "intal": "install",
    "installl": "install",
    "instal": "install",
    "pythoon": "python",
    "pyton": "python",
    "pythn": "python",
    "javascipt": "javascript",
    "javasript": "javascript",
    "javascrpit": "javascript",
    "reakt": "react",
    "fasttapi": "fastapi",
    "fastaapi": "fastapi",
    "datbase": "database",
    "databse": "database",
    "postges": "postgresql",
    "postgress": "postgresql",
    "posgresql": "postgresql",
    "mongdb": "mongodb",
    "mongoDB": "mongodb",
    "gitub": "github",
    "githb": "github",
    "dokcer": "docker",
    "docekr": "docker",
    "kubernetess": "kubernetes",
    "kuberntes": "kubernetes",
    "nginxx": "nginx",
    "nignx": "nginx",
    # Typo perintah / request
    "tlong": "tolong",
    "tlg": "tolong",
    "bikinin": "buatkan",
    "jelasin": "jelaskan",
    "jlskan": "jelaskan",
    "tunjukin": "tunjukkan",
    "kasih": "beri",
    "kasiin": "berikan",
    "lanjutin": "lanjutkan",
    "lnjtkan": "lanjutkan",
    "bantu": "bantu",
    "bantuin": "bantu",
    "cobain": "coba",
    "buatin": "buatkan",
    "bikinin": "buatkan",
    "ajarin": "ajarkan",
    "ajari": "ajarkan",
    "tanyain": "tanyakan",
    "cekkin": "cek",
    "liat": "lihat",
    "liat2": "lihat-lihat",
}

# ---------------------------------------------------------------------------
# ABBREVIATION EXPANSION — 70+ entri
# ---------------------------------------------------------------------------
ABBREVIATION_EXPANSION: dict[str, str] = {
    "mcp": "Model Context Protocol",
    "llm": "Large Language Model",
    "api": "Application Programming Interface",
    "gpu": "Graphics Processing Unit",
    "cpu": "Central Processing Unit",
    "vps": "Virtual Private Server",
    "ui": "User Interface",
    "ux": "User Experience",
    "db": "Database",
    "sql": "Structured Query Language",
    "nosql": "Non-Relational Database",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "rag": "Retrieval Augmented Generation",
    "lora": "Low-Rank Adaptation",
    "qlora": "Quantized Low-Rank Adaptation",
    "tts": "Text-to-Speech",
    "stt": "Speech-to-Text",
    "asr": "Automatic Speech Recognition",
    "ci": "Continuous Integration",
    "cd": "Continuous Deployment",
    "cicd": "Continuous Integration and Deployment",
    "cqf": "Content Quality Framework",
    "ihos": "Islamic Human Operating System",
    "dag": "Directed Acyclic Graph",
    "pm2": "Process Manager 2",
    "sdk": "Software Development Kit",
    "ide": "Integrated Development Environment",
    "rest": "Representational State Transfer",
    "grpc": "Google Remote Procedure Call",
    "jwt": "JSON Web Token",
    "oauth": "Open Authorization",
    "cors": "Cross-Origin Resource Sharing",
    "csrf": "Cross-Site Request Forgery",
    "xss": "Cross-Site Scripting",
    "rbac": "Role-Based Access Control",
    "orm": "Object Relational Mapper",
    "cqrs": "Command Query Responsibility Segregation",
    "ddd": "Domain-Driven Design",
    "tdd": "Test-Driven Development",
    "bdd": "Behavior-Driven Development",
    "mvp": "Minimum Viable Product",
    "poc": "Proof of Concept",
    "sla": "Service Level Agreement",
    "slo": "Service Level Objective",
    "sli": "Service Level Indicator",
    "p95": "95th Percentile",
    "p99": "99th Percentile",
    "rca": "Root Cause Analysis",
    "iac": "Infrastructure as Code",
    "k8s": "Kubernetes",
    "ecs": "Elastic Container Service",
    "ec2": "Elastic Compute Cloud",
    "s3": "Simple Storage Service",
    "cdn": "Content Delivery Network",
    "dns": "Domain Name System",
    "tls": "Transport Layer Security",
    "ssl": "Secure Sockets Layer",
    "http": "Hypertext Transfer Protocol",
    "https": "HTTP Secure",
    "ws": "WebSocket",
    "wss": "WebSocket Secure",
    "jsonl": "JSON Lines",
    "csv": "Comma-Separated Values",
    "tsv": "Tab-Separated Values",
    "xml": "Extensible Markup Language",
    "yaml": "YAML Ain't Markup Language",
    "toml": "Tom's Obvious Minimal Language",
    "regex": "Regular Expression",
    "fp": "Functional Programming",
    "oop": "Object-Oriented Programming",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class NormalizationMeta:
    original: str
    normalized: str
    corrections_made: list[str] = field(default_factory=list)
    abbrev_expanded: list[str] = field(default_factory=list)
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# TextNormalizer
# ---------------------------------------------------------------------------
class TextNormalizer:
    """Layer 1 — normalize teks informal/typo-heavy Indonesia menjadi teks baku."""

    def __init__(
        self,
        typo_dict: dict[str, str] | None = None,
        abbrev_dict: dict[str, str] | None = None,
        max_levenshtein: int = 2,
    ) -> None:
        self._typo = typo_dict if typo_dict is not None else TYPO_DICTIONARY
        self._abbrev = abbrev_dict if abbrev_dict is not None else ABBREVIATION_EXPANSION
        self._max_lev = max_levenshtein

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def normalize(self, text: str) -> tuple[str, NormalizationMeta]:
        """Full normalization pipeline. Returns (normalized_text, meta)."""
        original = text or ""

        # Unicode NFC
        step = unicodedata.normalize("NFC", original)

        # Typo correction
        step, corrections = self._correct_typos(step)

        # Abbreviation expansion
        step, abbrevs = self._expand_abbreviations(step)

        # Whitespace cleanup
        step = re.sub(r"\s+", " ", step).strip()

        # Confidence: reduce per correction needed
        base_conf = 1.0
        n_total = len(corrections) + len(abbrevs)
        word_count = max(1, len(original.split()))
        correction_ratio = min(n_total / word_count, 1.0)
        confidence = round(base_conf - correction_ratio * 0.4, 4)

        meta = NormalizationMeta(
            original=original,
            normalized=step,
            corrections_made=corrections,
            abbrev_expanded=abbrevs,
            confidence=confidence,
        )
        return step, meta

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _correct_typos(self, text: str) -> tuple[str, list[str]]:
        """Word-level typo correction. Dict lookup first, then Levenshtein fallback."""
        corrections: list[str] = []
        words = text.split()
        result: list[str] = []

        for word in words:
            cleaned = re.sub(r"[^\w]", "", word.lower())
            suffix = word[len(re.sub(r"^[\w]+", "", word[::-1])[::-1]):]  # punctuation tail

            if cleaned in self._typo:
                corrected = self._typo[cleaned]
                corrections.append(f"{cleaned}→{corrected}")
                # Preserve trailing punctuation
                tail = re.sub(r"[\w]+", "", word)
                result.append(corrected + tail)
            else:
                # Levenshtein fallback for longer words (avoid false positives on short words)
                if len(cleaned) >= 4:
                    best_word, best_dist = self._find_closest(cleaned)
                    if best_dist is not None and best_dist <= self._max_lev:
                        tail = re.sub(r"[\w]+", "", word)
                        corrections.append(f"{cleaned}→{best_word}(lev{best_dist})")
                        result.append(best_word + tail)
                        continue
                result.append(word)

        return " ".join(result), corrections

    def _find_closest(self, word: str) -> tuple[str, int | None]:
        """Find the closest word in the typo dictionary using Levenshtein distance."""
        best_word = word
        best_dist: int | None = None

        for candidate, replacement in self._typo.items():
            if abs(len(candidate) - len(word)) > self._max_lev:
                continue
            dist = self._levenshtein(word, candidate)
            if dist <= self._max_lev:
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_word = replacement

        return best_word, best_dist

    def _expand_abbreviations(self, text: str) -> tuple[str, list[str]]:
        """Expand known abbreviations in text."""
        expanded: list[str] = []
        words = text.split()
        result: list[str] = []

        for word in words:
            cleaned = re.sub(r"[^\w]", "", word.lower())
            tail = word[len(cleaned):]

            if cleaned in self._abbrev:
                full = self._abbrev[cleaned]
                expanded.append(f"{cleaned}→{full}")
                result.append(full + tail)
            else:
                result.append(word)

        return " ".join(result), expanded

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        """Implementasi manual Levenshtein distance (tanpa library eksternal)."""
        m, n = len(a), len(b)
        # Optimasi: gunakan 1D array (rolling)
        prev = list(range(n + 1))
        curr = [0] * (n + 1)

        for i in range(1, m + 1):
            curr[0] = i
            for j in range(1, n + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                curr[j] = min(
                    curr[j - 1] + 1,       # insert
                    prev[j] + 1,           # delete
                    prev[j - 1] + cost,    # substitute
                )
            prev, curr = curr, [0] * (n + 1)

        return prev[n]
