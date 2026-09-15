"""Structural checks for the bundled snapshot; these are not scholarly review."""

from collections import Counter
import json
from pathlib import Path
import unicodedata

from .provider import DATA_DIR, DISCLAIMER, format_ref

REQUIRED = {
    "schema": str, "id": str, "version": int, "title": str, "subtitle": str,
    "ref": dict, "surah_name": str, "theme": str, "sourced_meaning": dict,
    "qca": list, "lenses": list, "inference": str, "authors": list,
    "status": str, "created": str, "history": list, "disclaimer": dict,
}


def _strings(value, field="$"):
    if isinstance(value, str):
        yield field, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield field + ".<key>", key
            yield from _strings(item, field + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{field}[{index}]")


# U+FDFA (the "sallallahu alayhi wa sallam" honorific ligature) is permitted: it is a
# customary honorific in Indonesian prose about the Prophet, not Qur'anic text. Six
# study summaries use it. Every other Arabic-script character is still rejected.
HONORIFICS = {0xFDFA}


def _arabic(char):
    cp = ord(char)
    if cp in HONORIFICS:
        return False
    return "ARABIC" in unicodedata.name(char, "") or any(
        low <= cp <= high for low, high in (
            (0x0600, 0x06FF), (0x0750, 0x077F), (0x0870, 0x089F),
            (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
            (0x10EC0, 0x10EFF), (0x1EE00, 0x1EEFF),
        )
    )


def validate(data_dir=None):
    """Return a list of violations, rereading disk even if retrieval is cached."""
    root = Path(DATA_DIR if data_dir is None else data_dir)
    violations = []

    def read(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            violations.append(f"{path.name}: cannot read JSON ({type(exc).__name__})")
            return None

    counts = read(root / "ayah_counts.json")
    counts_ok = (isinstance(counts, list) and len(counts) == 114
                 and all(type(n) is int and n > 0 for n in counts))
    if not counts_ok:
        violations.append("ayah_counts.json: expected 114 positive integers")
    paths = sorted((root / "studies").glob("*.json"))
    if not paths:
        violations.append("studies: no study files")
    studies = {}
    valid_refs = set()
    for path in paths:
        study = read(path)
        if not isinstance(study, dict):
            violations.append(f"{path.name}: expected an object")
            continue
        for key, kind in REQUIRED.items():
            if key not in study:
                violations.append(f"{path.name}: missing {key}")
            elif type(study[key]) is not kind:
                violations.append(f"{path.name}: invalid type for {key}")
        if study.get("id") != path.stem:
            violations.append(f"{path.name}: id does not match filename")
        studies[path.stem] = study
        if study.get("schema") != "lab-study-v2":
            violations.append(f"{path.name}: expected lab-study-v2")
        if study.get("status") != "draft-llm-unreviewed":
            violations.append(f"{path.name}: status must be draft-llm-unreviewed")
        if study.get("disclaimer") != DISCLAIMER:
            violations.append(f"{path.name}: disclaimer must include the required ID and EN text")
        ref = study.get("ref")
        ref_ok = isinstance(ref, dict) and all(type(ref.get(k)) is int for k in ("surah", "from", "to"))
        if ref_ok and counts_ok:
            ref_ok = (1 <= ref["surah"] <= 114
                      and 1 <= ref["from"] <= ref["to"] <= counts[ref["surah"] - 1])
        if not ref_ok:
            violations.append(f"{path.name}: invalid verse reference")
        elif counts_ok:
            valid_refs.add(path.stem)
        meaning = study.get("sourced_meaning")
        if (not isinstance(meaning, dict) or not isinstance(meaning.get("summary"), str)
                or not isinstance(meaning.get("sources"), list)
                or not meaning["sources"]
                or not all(isinstance(s, str) and s.strip() for s in meaning["sources"])):
            violations.append(f"{path.name}: sourced_meaning requires summary and sources")
        for field, value in _strings(study):
            if any(_arabic(c) for c in value):
                violations.append(f"{path.name}:{field}: Arabic-script character")
            if "via panel tafsir app ini" in " ".join(value.lower().split()):
                violations.append(f"{path.name}:{field}: app-internal source attribution")

    index = read(root / "index.json")
    entries = index.get("studies") if isinstance(index, dict) else None
    if not isinstance(entries, list):
        violations.append("index.json: studies must be a list")
    else:
        ids = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                violations.append("index.json: entry requires a string id")
                continue
            sid = entry["id"]
            ids.append(sid)
            if sid not in studies:
                violations.append(f"index.json: missing study file for {sid}")
                continue
            study = studies[sid]
            for key in ("title", "theme", "created"):
                if entry.get(key) != study.get(key):
                    violations.append(f"index.json:{sid}: {key} does not match study")
            if sid in valid_refs and entry.get("ref") != format_ref(study["ref"]):
                violations.append(f"index.json:{sid}: ref does not match study")
            lenses = study.get("lenses")
            if isinstance(lenses, list) and entry.get("lenses") != len(lenses):
                violations.append(f"index.json:{sid}: lens count does not match study")
        for sid, count in Counter(ids).items():
            if count > 1:
                violations.append(f"index.json: duplicate id {sid}")
        for sid in sorted(set(studies) - set(ids)):
            violations.append(f"index.json: missing entry for {sid}")

    synthesis = read(root / "synthesis.json")
    principles = synthesis.get("principles") if isinstance(synthesis, dict) else None
    if not isinstance(principles, list):
        violations.append("synthesis.json: principles must be a list")
    else:
        for principle in principles:
            if not isinstance(principle, dict) or not isinstance(principle.get("evidence"), list):
                violations.append("synthesis.json: principle requires evidence list")
                continue
            for evidence in principle["evidence"]:
                sid = evidence.get("id") if isinstance(evidence, dict) else None
                if not isinstance(sid, str) or sid not in studies:
                    violations.append(f"synthesis.json:{principle.get('id')}: unknown evidence id {sid}")
    for name in ("taxonomy", "coverage"):
        if not isinstance(read(root / f"{name}.json"), dict):
            violations.append(f"{name}.json: expected an object")
    return violations
