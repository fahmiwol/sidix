"""Offline tests: run with unittest discover from the repository root."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from quran_lab import get_study, load_lab, principles, search, studies_for_verse
from quran_lab.provider import DATA_DIR, DISCLAIMER, SOURCE
from quran_lab.validate import validate

spec = importlib.util.spec_from_file_location("find_quotations", PACKAGE / "tools" / "find_quotations.py")
detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detector)


class ProviderTests(unittest.TestCase):
    def test_168_studies_load(self):
        self.assertEqual(len(load_lab()), 168)
        self.assertEqual(len(load_lab().studies), 168)

    def test_validator(self):
        self.assertEqual(validate(), [])

    def test_search_tabayyun(self):
        hits = search("tabayyun")
        self.assertIn("hujurat-49-6", [h["id"] for h in hits])
        self.assertLessEqual(len(hits), 5)
        self.assertEqual(hits, search("TABAYYUN"))
        self.assertEqual([h["score"] for h in hits], sorted((h["score"] for h in hits), reverse=True))
        self.assertTrue(all(len(h["snippet"]) <= 240 for h in hits))

    def test_verse_lookup(self):
        self.assertIn("hujurat-49-6", [s["id"] for s in studies_for_verse(49, 6)])
        for ayah in (1, 7):
            self.assertIn("fatihah-1-1-7", [s["id"] for s in studies_for_verse(1, ayah)])
        for pair in ((0, 1), (115, 1), (49, 0), (49, 19), (True, 1), (49, "6")):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                studies_for_verse(*pair)

    def test_get_disclaimer_and_all_statuses(self):
        self.assertEqual(get_study("hujurat-49-6")["disclaimer"], DISCLAIMER)
        self.assertEqual({s["status"] for s in load_lab().studies}, {"draft-llm-unreviewed"})

    def test_principles_verify(self):
        self.assertEqual(len(principles()), 33)
        self.assertIn("verify-before-act", [p["id"] for p in principles("verify")])
        self.assertEqual(principles("verify"), principles("VERIFY"))
        self.assertEqual(principles("unfindableword987654"), [])

    def test_all_result_provenance(self):
        results = load_lab().studies + search("tabayyun") + principles() + studies_for_verse(49, 6)
        for result in results:
            with self.subTest(id=result["id"]):
                self.assertEqual(result["disclaimer"], DISCLAIMER)
                self.assertTrue(result["citations"])
                for citation in result["citations"]:
                    self.assertEqual(citation["source"], SOURCE)
                    self.assertEqual(citation["license"], "MIT")
                    self.assertEqual(citation["sanad_tier"], "interpretation-draft")
                    self.assertTrue(citation["ref"].startswith("QS "))
                    self.assertEqual(get_study(citation["study_id"])["id"], citation["study_id"])

    def test_cache_paths_and_mutation_isolation(self):
        self.assertIs(load_lab(), load_lab(DATA_DIR))
        self.assertIs(load_lab(), load_lab(str(DATA_DIR / ".." / "data")))
        study = get_study("hujurat-49-6")
        study["ref"]["from"] = 99
        study["disclaimer"]["en"] = "changed"
        self.assertEqual(get_study("hujurat-49-6")["ref"]["from"], 6)
        self.assertEqual(get_study("hujurat-49-6")["disclaimer"], DISCLAIMER)
        principle = principles()[0]
        original = deepcopy(principle)
        principle["evidence"].clear()
        self.assertEqual(principles()[0], original)

    def test_empty_and_invalid_queries(self):
        self.assertEqual(search(""), [])
        self.assertEqual(search("unfindableword987654"), [])
        self.assertEqual(search("tabayyun", 0), [])
        with self.assertRaises(ValueError):
            search("tabayyun", -1)
        with self.assertRaises(KeyError):
            get_study("../unknown")

    def test_principle_statements_are_searchable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "data"
            shutil.copytree(DATA_DIR, root)
            path = root / "synthesis.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["principles"][0]["statement"] += " uniquelysearchableprinciple"
            expected = {e["id"] for e in data["principles"][0]["evidence"]}
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual({h["id"] for h in load_lab(root).search("uniquelysearchableprinciple", 168)}, expected)

    def test_cli_json(self):
        for args, success in ((["validate"], True), (["search", "tabayyun"], True),
                              (["get", "hujurat-49-6"], True), (["verse", "49", "6"], True),
                              (["principles", "verify"], True), (["get", "missing"], False),
                              (["verse", "49", "19"], False)):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, "-m", "quran_lab", *args], cwd=PACKAGE,
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0 if success else 1, result.stderr)
                parsed = json.loads(result.stdout)
                if args == ["validate"]:
                    self.assertEqual(parsed, [])


class ValidationTests(unittest.TestCase):
    def test_honorific_ligature_is_permitted(self):
        # U+FDFA is a customary honorific in Indonesian prose, not Qur'anic text.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "data"
            shutil.copytree(DATA_DIR, root)
            path = root / "studies/hujurat-49-6.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["subtitle"] = "Rasulullah " + chr(0xFDFA)
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertFalse(any("Arabic-script" in v for v in validate(root)))

    def test_corruptions_return_violations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "data"
            shutil.copytree(DATA_DIR, root)
            cases = [
                ("studies/hujurat-49-6.json", lambda d: d.pop("title"), "missing title"),
                ("studies/hujurat-49-6.json", lambda d: d.update(id="mismatch"), "id does not match"),
                ("studies/hujurat-49-6.json", lambda d: d["ref"].update(to=19), "invalid verse reference"),
                ("studies/hujurat-49-6.json", lambda d: d.update(status="published"), "status must"),
                ("studies/hujurat-49-6.json", lambda d: d.pop("disclaimer"), "disclaimer"),
                ("studies/hujurat-49-6.json", lambda d: d.update(subtitle=chr(0x0628)), "Arabic-script"),
                ("studies/hujurat-49-6.json", lambda d: d["sourced_meaning"]["sources"].append("via panel Tafsir app ini"), "app-internal"),
                ("studies/hujurat-49-6.json", lambda d: d.update(ref=[]), "invalid verse reference"),
                ("synthesis.json", lambda d: d["principles"][0]["evidence"][0].update(id="missing"), "unknown evidence"),
                ("index.json", lambda d: d["studies"].pop(), "missing entry"),
                ("index.json", lambda d: d["studies"].append(d["studies"][0]), "duplicate id"),
                ("index.json", lambda d: d["studies"][0].update(ref="QS 1:1"), "ref does not match"),
                ("ayah_counts.json", lambda d: d.pop(), "114 positive integers"),
            ]
            # Cache a clean snapshot first: validation must still see disk edits.
            load_lab(root)
            for relative, change, expected in cases:
                path = root / relative
                original = path.read_bytes()
                with self.subTest(expected=expected):
                    data = json.loads(original)
                    change(data)
                    path.write_text(json.dumps(data), encoding="utf-8")
                    self.assertTrue(any(expected in v for v in validate(root)), expected)
                path.write_bytes(original)
            path = root / "studies/hujurat-49-6.json"
            path.write_text("{broken", encoding="utf-8")
            self.assertTrue(any("cannot read JSON" in v for v in validate(root)))


class QuotationTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(detector.normalize("One, TWO!\nthree-four… five → SIX"),
                         ["one", "two", "three", "four", "five", "six"])

    def test_maximal_runs_and_threshold(self):
        words = "one two three four five six seven eight nine ten".split()
        self.assertEqual(list(detector.maximal_matches(words, ["before"] + words + ["after"])), [(0, 1, 10)])
        self.assertEqual(list(detector.maximal_matches(words[:7], words)), [])
        self.assertEqual(list(detector.maximal_matches(words[:8], words)), [(0, 0, 8)])
        self.assertEqual(list(detector.maximal_matches(words, words + ["gap"] + words)), [(0, 0, 10), (0, 11, 10)])

    def test_every_nested_string(self):
        fields = dict(detector.string_fields({"title": "first", "history": [{"authors": ["second"]}]}))
        self.assertEqual(fields, {"$.title": "first", "$.history[0].authors[0]": "second"})

    def test_cross_ayah_runs_and_edition_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("surah", "tafsir", "studies"):
                (root / name).mkdir()
            words = "one two three four five six seven eight nine ten"
            study = {"id": "example", "ref": {"surah": 1, "from": 1, "to": 2},
                     "history": [{"note": words}]}
            surah = {"ayahs": [{"ayah": 1, "tr": {"id": "one two three four five", "en": "one two three four five"}},
                               {"ayah": 2, "tr": {"id": "six seven eight nine ten", "en": "six seven eight nine ten"}}]}
            tafsir = {"ayahs": {"1": {"kemenag": "unrelated", "jalalain_id": "unrelated"},
                                "2": {"kemenag": "unrelated"}}}
            for name, data in (("studies/example.json", study), ("surah/1.json", surah), ("tafsir/1.json", tafsir)):
                (root / name).write_text(json.dumps(data), encoding="utf-8")
            result = detector.find_quotations(root, root / "studies")
            self.assertEqual(result["totals"], {"studies_checked": 1, "studies_with_quotations": 1,
                                                 "runs": 1, "words": 10, "longest_run": 10})
            self.assertEqual(len(result["runs"][0]["matches"]), 2)
            self.assertEqual(result["runs"][0]["matches"][0]["to"], 2)
            self.assertEqual(result["runs"][0]["field"], "$.history[0].note")
            self.assertNotIn(words, detector.render_report(result))
            self.assertNotIn(words, json.dumps(result))

    def test_optional_missing_ayah_breaks_stream(self):
        surah = {"ayahs": [{"ayah": a, "tr": {"id": "example", "en": "example"}} for a in (1, 2, 3)]}
        tafsir = {"ayahs": {"1": {"kemenag": "example", "jalalain_id": "one two three four"},
                            "2": {"kemenag": "example"},
                            "3": {"kemenag": "example", "jalalain_id": "five six seven eight"}}}
        streams = list(detector._streams({"surah": 1, "from": 1, "to": 3}, surah, tafsir))
        optional = [(words, owners) for edition, words, owners in streams if edition.startswith("Tafsir al-Jalalayn")]
        self.assertEqual([len(words) for words, _ in optional], [4, 4])


if __name__ == "__main__":
    unittest.main()
