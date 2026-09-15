"""Offline retrieval of Quran Lab's unreviewed engineering interpretations."""

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import unicodedata

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DISCLAIMER = {
    "id": "Interpretasi rekayasa — bukan tafsir, bukan fatwa. Draf LLM di bawah arahan Fahmi Ghani; belum ditinjau ahli.",
    "en": "Engineering interpretation — not tafsir, not a fatwa. LLM draft directed by Fahmi Ghani; not reviewed by scholars.",
}
SOURCE = "Quran Lab (engineering interpretation, not tafsir)"


def _tokens(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"[^\W_]+", text, flags=re.UNICODE)


def format_ref(ref):
    end = f"-{ref['to']}" if ref["to"] != ref["from"] else ""
    return f"QS {ref['surah']}:{ref['from']}{end}"


class Lab:
    """A cached local corpus. Public results are copies, safe for callers to edit."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self._studies = {}
        for path in sorted((self.data_dir / "studies").glob("*.json")):
            study = json.loads(path.read_text(encoding="utf-8"))
            self._studies[study["id"]] = study
        if not self._studies:
            raise ValueError("No Quran Lab studies found")
        self._principles = json.loads(
            (self.data_dir / "synthesis.json").read_text(encoding="utf-8")
        )["principles"]
        self._ayah_counts = json.loads(
            (self.data_dir / "ayah_counts.json").read_text(encoding="utf-8")
        )
        statements = {sid: [] for sid in self._studies}
        for principle in self._principles:
            for sid in {e["id"] for e in principle["evidence"]}:
                if sid in statements:
                    statements[sid].append(principle["statement"])
        self._fields = {}
        self._terms = {}
        self._df = Counter()
        for sid, study in self._studies.items():
            fields = [study[k] for k in ("title", "subtitle", "theme", "inference")]
            fields += [lens["reading"] for lens in study["lenses"]]
            fields += statements[sid]
            self._fields[sid] = fields
            terms = Counter(_tokens(" ".join(fields)))
            self._terms[sid] = terms
            self._df.update(terms.keys())
        self._lengths = {sid: sum(t.values()) for sid, t in self._terms.items()}
        self._avg_length = sum(self._lengths.values()) / len(self._studies) or 1

    def __len__(self):
        return len(self._studies)

    @property
    def studies(self):
        return [self.get_study(sid) for sid in self._studies]

    def _citation(self, sid):
        return {
            "study_id": sid,
            "ref": format_ref(self._studies[sid]["ref"]),
            "source": SOURCE,
            "license": "MIT",
            "sanad_tier": "interpretation-draft",
        }

    def _result(self, result, study_ids):
        result = deepcopy(result)
        result["citations"] = [self._citation(sid) for sid in dict.fromkeys(study_ids)]
        result["disclaimer"] = deepcopy(DISCLAIMER)
        return result

    def get_study(self, id):
        """Return a full study with provenance; raise KeyError for an unknown id."""
        return self._result(self._studies[id], [id])

    def search(self, query, k=5):
        """Rank study documents with BM25 (k1=1.5, b=0.75), without a model."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if type(k) is not int or k < 0:
            raise ValueError("k must be a non-negative integer")
        query_terms = set(_tokens(query))
        if not query_terms or not k:
            return []
        ranked = []
        count = len(self._studies)
        for sid, terms in self._terms.items():
            score = 0.0
            norm = 1.5 * (1 - 0.75 + 0.75 * self._lengths[sid] / self._avg_length)
            for term in sorted(query_terms):
                tf = terms[term]
                if tf:
                    df = self._df[term]
                    idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
                    score += idf * tf * 2.5 / (tf + norm)
            if score > 0:
                ranked.append((score, sid))
        results = []
        for score, sid in sorted(ranked, key=lambda item: (-item[0], item[1]))[:k]:
            study = self._studies[sid]
            field = max(self._fields[sid], key=lambda f: len(query_terms & set(_tokens(f))))
            snippet = " ".join(field.split())
            if len(snippet) > 240:
                snippet = snippet[:237].rsplit(" ", 1)[0] + "..."
            results.append(self._result({
                "id": sid, "title": study["title"], "ref": format_ref(study["ref"]),
                "theme": study["theme"], "snippet": snippet, "score": round(score, 8),
            }, [sid]))
        return results

    def studies_for_verse(self, surah, ayah):
        """Return studies whose inclusive reference contains a valid verse."""
        if (type(surah) is not int or type(ayah) is not int
                or not 1 <= surah <= len(self._ayah_counts)
                or not 1 <= ayah <= self._ayah_counts[surah - 1]):
            raise ValueError("Verse is outside the ayah counts")
        return [self.get_study(sid) for sid, study in self._studies.items()
                if study["ref"]["surah"] == surah
                and study["ref"]["from"] <= ayah <= study["ref"]["to"]]

    def principles(self, topic=None):
        """Filter principle ids and text by case-insensitive substring."""
        if topic is not None and not isinstance(topic, str):
            raise TypeError("topic must be a string or None")
        needle = (topic or "").casefold().strip()
        return [self._result(p, [e["id"] for e in p["evidence"]])
                for p in self._principles
                if not needle or needle in " ".join(
                    p.get(k, "") for k in ("id", "title", "cluster", "statement", "implication")
                ).casefold()]


@lru_cache(maxsize=8)
def _load_cached(data_dir):
    return Lab(data_dir)


def load_lab(data_dir=None):
    """Cache by resolved data directory; returns a Lab with the same query methods.

    The snapshot lasts for this process. Restart after changing data on disk.
    """
    return _load_cached(Path(DATA_DIR if data_dir is None else data_dir).resolve())


def search(query, k=5):
    return load_lab().search(query, k)


def get_study(id):
    return load_lab().get_study(id)


def studies_for_verse(surah, ayah):
    return load_lab().studies_for_verse(surah, ayah)


def principles(topic=None):
    return load_lab().principles(topic)
