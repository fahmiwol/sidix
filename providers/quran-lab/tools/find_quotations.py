"""Find maximal verbatim word runs using read-only, unbundled comparison data.

Usage: python tools/find_quotations.py APP_DATA_DIR --output QUOTATIONS_REPORT.md
APP_DATA_DIR contains surah/ and tafsir/. No source text is written to the report.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import unicodedata

MIN_WORDS = 8
STUDIES_DIR = Path(__file__).resolve().parents[1] / "data" / "studies"
EDITIONS = (
    ("tr.id", "Terjemah Kemenag RI"),
    ("tr.en", "English translation (local tr.en; edition unspecified)"),
    ("kemenag", "Tafsir Kemenag RI"),
    ("jalalain_id", "Tafsir al-Jalalayn (Indonesian)"),
)


def normalize(text):
    """Lowercase, remove punctuation at word boundaries, collapse whitespace.

    Unicode punctuation and symbols become spaces; letters, numbers and their
    diacritics are preserved. No stemming, translation or semantic matching.
    """
    return "".join(" " if unicodedata.category(c)[0] in "PS" else c
                   for c in text.lower()).split()


def string_fields(value, path="$"):
    """Visit every string value, including nested arrays and metadata."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from string_fields(item, path + "." + key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from string_fields(item, f"{path}[{i}]")


def maximal_matches(words, source, minimum=MIN_WORDS):
    """All left/right-maximal exact alignments, as (field start, source start, n).

    An eight-word inverted index seeds matches; extension finds the full run.
    Repeated phrases remain discoverable (no frequency/autojunk heuristic).
    """
    seeds = defaultdict(list)
    for j in range(len(source) - minimum + 1):
        seeds[tuple(source[j:j + minimum])].append(j)
    for i in range(len(words) - minimum + 1):
        for j in seeds.get(tuple(words[i:i + minimum]), ()):
            if i and j and words[i - 1] == source[j - 1]:
                continue
            n = minimum
            while i + n < len(words) and j + n < len(source) and words[i + n] == source[j + n]:
                n += 1
            yield i, j, n


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _streams(ref, surah, tafsir):
    """Join adjacent referenced ayahs within one edition; gaps break the stream."""
    verses = {a["ayah"]: a for a in surah["ayahs"]}
    for key, edition in EDITIONS:
        words, owners = [], []
        for ayah in range(ref["from"], ref["to"] + 1):
            if ayah not in verses:
                raise ValueError(f"Missing comparison ayah {ref['surah']}:{ayah}")
            if key.startswith("tr."):
                text = verses[ayah]["tr"].get(key[3:])
            else:
                text = tafsir["ayahs"].get(str(ayah), {}).get(key)
            if text is not None and not isinstance(text, str):
                raise ValueError(f"Comparison field {key} must be a string")
            if key != "jalalain_id" and not text:
                raise ValueError(f"Missing comparison field {key} at {ref['surah']}:{ayah}")
            tokens = normalize(text or "")
            if not tokens:
                if words:
                    yield edition, words, owners
                words, owners = [], []
            else:
                words.extend(tokens)
                owners.extend([ayah] * len(tokens))
        if words:
            yield edition, words, owners


def find_quotations(app_data_dir, studies_dir=STUDIES_DIR):
    """Return location/count metadata only; comparison strings stay in memory."""
    root = Path(app_data_dir)
    paths = sorted(Path(studies_dir).glob("*.json"))
    if not paths:
        raise ValueError("No studies found")
    source_cache = {}
    runs, per_study = [], []
    for path in paths:
        study = _read(path)
        sid, ref = study["id"], study["ref"]
        number = ref["surah"]
        if number not in source_cache:
            source_cache[number] = (_read(root / "surah" / f"{number}.json"),
                                    _read(root / "tafsir" / f"{number}.json"))
        streams = list(_streams(ref, *source_cache[number]))
        study_runs = []
        for field, text in string_fields(study):
            words = normalize(text)
            matches = defaultdict(set)
            for edition, source, owners in streams:
                for start, offset, length in maximal_matches(words, source):
                    matches[(start, start + length)].add(
                        (edition, owners[offset], owners[offset + length - 1]))
            # Maximal in the study field across every available source/edition.
            # A shorter contained match is represented by the longer run only.
            rightmost = -1
            for start, end in sorted(matches, key=lambda span: (span[0], -span[1])):
                if end <= rightmost:
                    continue
                rightmost = end
                study_runs.append({
                    "study_id": sid, "field": field, "start_word": start + 1,
                    "words": end - start,
                    "matches": [{"edition": edition, "surah": number, "from": first, "to": last}
                                for edition, first, last in sorted(matches[(start, end)])],
                })
        runs.extend(study_runs)
        per_study.append({"study_id": sid, "runs": len(study_runs),
                          "words": sum(r["words"] for r in study_runs),
                          "longest_run": max((r["words"] for r in study_runs), default=0)})
    return {
        "totals": {"studies_checked": len(paths),
                   "studies_with_quotations": sum(s["runs"] > 0 for s in per_study),
                   "runs": len(runs), "words": sum(r["words"] for r in runs),
                   "longest_run": max((r["words"] for r in runs), default=0)},
        "studies": per_study, "runs": runs,
    }


def render_report(report):
    totals = report["totals"]
    lines = [
        "# Quotations report", "",
        "Generated by `tools/find_quotations.py` against the packaged studies.", "",
        "## Method and counting", "",
        "Every string value is compared, including nested metadata. Normalisation lowercases, "
        "replaces Unicode punctuation and symbols with spaces, then collapses whitespace; "
        "diacritics remain. Matching is exact, with a minimum of eight consecutive words.", "",
        "Only each study's inclusive `ref` ayahs are compared: `tr.id`, `tr.en`, "
        "Kemenag tafsir and `jalalain_id` when available. Adjacent ayahs may form a run "
        "within one edition; a missing optional ayah breaks that stream. The English "
        "translation's edition is not identified by the local field, so no publisher is inferred.", "",
        "Runs extend as far as possible in both directions. Contained field spans are "
        "discarded across editions; identical spans are one run with all full-length "
        "edition/ayah matches listed in corresponding order. Distinct overlapping spans "
        "and occurrences in different fields count separately. Words are the sum of run "
        "lengths, so overlaps can contribute more than once. Start word is one-based after "
        "normalisation. No quoted text appears below.", "",
        "This detects textual overlap, not permission, authorship or completeness of "
        "attribution. Shorter quotations, paraphrases and editions outside the comparison "
        "set are not measured. Quotations remain in the studies; see [NOTICE](NOTICE.md).", "",
        "## Totals", "", "| Metric | Count |", "|---|---:|",
    ]
    for key, label in (("studies_checked", "Studies checked"),
                       ("studies_with_quotations", "Studies with quotations"),
                       ("runs", "Maximal runs"), ("words", "Words in runs"),
                       ("longest_run", "Longest run (words)")):
        lines.append(f"| {label} | {totals[key]} |")
    lines += ["", "## Per-study totals", "", "| Study id | Runs | Words | Longest run |",
              "|---|---:|---:|---:|"]
    for study in report["studies"]:
        lines.append(f"| {study['study_id']} | {study['runs']} | {study['words']} | {study['longest_run']} |")
    lines += ["", "## Per-run locations", "",
              "| Study id | Field | Start word | Words | Edition | Ayah range |",
              "|---|---|---:|---:|---|---|"]
    for run in report["runs"]:
        editions = "<br>".join(m["edition"] for m in run["matches"])
        refs = "<br>".join(f"QS {m['surah']}:{m['from']}-{m['to']}" for m in run["matches"])
        lines.append(f"| {run['study_id']} | `{run['field']}` | {run['start_word']} | {run['words']} | {editions} | {refs} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_data_dir", type=Path)
    parser.add_argument("--studies-dir", type=Path, default=STUDIES_DIR)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="emit location/count JSON")
    args = parser.parse_args(argv)
    try:
        report = find_quotations(args.app_data_dir, args.studies_dir)
        output = json.dumps(report, ensure_ascii=True, indent=2) + "\n" if args.json else render_report(report)
        if args.output:
            args.output.write_text(output, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Comparison failed ({type(exc).__name__}); check input files.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
