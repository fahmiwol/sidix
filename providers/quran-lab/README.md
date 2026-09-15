# Quran Lab

[Bahasa Indonesia](README.id.md)

Quran Lab is a local SIDIX provider containing **168 studies** that read Qur'anic
verses as structural analogies for engineering and AI design. Its snapshot has
**33 cross-study principles**, **16 lenses**, a **Qur'anic Cognitive Architecture
(QCA)** layer, and coverage of approximately **302 ayahs**. Most study text is
in Indonesian. The package works offline with Python 3.11+ and its standard
library: no installation, downloads, model runtime or network service is needed.

## Status and boundaries

Every study is an LLM draft directed by Fahmi Ghani. **None has been reviewed by
scholars.** The original application labelled all 168 studies `published`; this
package labels them **`draft-llm-unreviewed`** and adds an Indonesian/English
disclaimer to every study and retrieval result.

This is engineering interpretation, **not tafsir, not a fatwa, and not a
religious authority**. It proposes structural resonance, not a numerical or
scientific miracle. The inherited readings remain drafts, including any claims
that need correction. Structural validation is not scholarly review. Read the
full [disclaimer](DISCLAIMER.md).

## Method in brief

1. Ground the religious meaning in sourced tafsir first, including context,
   before proposing an engineering reading. Keep that sourced meaning distinct
   from the interpretation; an analogy neither replaces it nor claims to be the
   verse's single intended meaning.
2. Apply relevant lenses to human conduct, creation, text and nature. QCA maps
   readings to proposed cognitive layers; it is an interpretive framework.
3. A cross-study principle needs at least **two independent studies**. Repeated
   patterns motivate a design hypothesis, not proof of a mechanism.
4. Respect **tanzih**: God's essence and attributes are never an analogy, system
   role, component or technical property. Respect **ghaib**: read matters of the
   unseen descriptively from sources, without inventing unstated details.
5. Mark bounded analogies and disagreements, preserve revision history, and
   seek qualified review. Do not derive religious rulings from engineering.

This summary follows the source Lab's `tadabbur-lab` method. It describes the
method's requirements, not a certification that every draft satisfies them.

## Data and licensing

The code and Lab-authored data and documentation are [MIT-licensed](LICENSE),
Copyright (c) 2026 Fahmi Ghani. Quoted passages from Terjemah Kemenag RI, Tafsir
Kemenag RI, Tafsir al-Jalalayn and other editions retain their publishers'
rights and are **not covered by MIT**. They remain included with attribution
for commentary. Read [NOTICE.md](NOTICE.md) and
[QUOTATIONS_REPORT.md](QUOTATIONS_REPORT.md) before reusing the data.

The import changes status, adds disclaimers, cleans app-internal edition labels
while retaining verse references, and replaces assistant names in `authors`
(including revision authors) with `LLM draft`. Study meanings and Kemenag
quotations are retained. `taxonomy.json`, `synthesis.json` and `coverage.json`
are copied from the source. In `index.json`, the `title` and `theme` fields were
rebuilt from the study files, because the source application's index had drifted
from its own studies (27 themes and 8 titles differed); the study files are the
canonical record. The honorific ligature ﷺ, used in six summaries, is the only
Arabic-script character permitted in studies. `ayah_counts.json` contains 114
integers derived by counting each source surah file's ayahs, totalling 6,236.
The source application's archive and full translation/tafsir files are excluded.

No Arabic Qur'an text is bundled. Obtain it from its publishers, such as Tanzil
with attribution or KFGQPC, under their terms. The copied taxonomy retains
individual Arabic cognitive terms.

## Usage

From the repository root, enter the provider directory. No install step:

```sh
cd providers/quran-lab
python -m quran_lab search "tabayyun"
python -m quran_lab search "verification" --k 3
python -m quran_lab get hujurat-49-6
python -m quran_lab verse 49 6
python -m quran_lab principles verify
python -m quran_lab principles
python -m quran_lab validate
```

Commands emit JSON. Validation emits `[]` and exits 0 when clean; violations
exit 1. Unknown study ids and invalid verse numbers emit JSON errors and exit 1.
Argument/usage errors follow the standard command-line parser's help format.

Python, from the same directory (or add that directory to `PYTHONPATH`):

```python
from quran_lab import load_lab, search, get_study, studies_for_verse, principles

hits = search("tabayyun", k=5)
study = get_study("hujurat-49-6")
nearby = studies_for_verse(49, 6)
rules = principles("verify")
lab = load_lab()  # cached Lab; len(lab) == 168; lab.studies returns copies
# Optional: lab = load_lab("path/to/data")
# The Lab object exposes the same four query methods.
```

Search uses a hand-written BM25 index over title, subtitle, theme, inference,
lens readings and principle statements attached to their evidence studies.
Search tokenisation ignores case and diacritics; it does not translate or use
semantic embeddings. An empty or unmatched query returns `[]`; `k` must be a
non-negative integer. `get_study` raises `KeyError` for an unknown id and verse
lookup raises `ValueError` for an invalid reference. Principle filtering is a
case-insensitive substring match on id, title, cluster, statement and implication.

Each result dict has `citations` with study id, verse reference, source
`Quran Lab (engineering interpretation, not tafsir)`, license `MIT` and
`sanad_tier: interpretation-draft`, plus the bilingual disclaimer. A principle
cites its evidence studies. MIT in a citation refers to the Lab's own work;
the quotation exclusions in NOTICE still apply. Full studies keep their object
`ref`; search hits use `QS s:a-b` (or `QS s:a` for a single ayah).

Loading is cached by resolved data directory for the process lifetime. Restart
after changing data; public query results are copies. Validation rereads disk.

### SIDIX integration

`plugin.json` declares the Python entrypoint and these tool-to-function mappings:

| Tool | Python function |
|---|---|
| `quran_lab_search` | `quran_lab.search(query, k=5)` |
| `quran_lab_get_study` | `quran_lab.get_study(id)` |
| `quran_lab_for_verse` | `quran_lab.studies_for_verse(surah, ayah)` |
| `quran_lab_principles` | `quran_lab.principles(topic=None)` |

The provider is disabled by default, reads local data only, and declares no
connectors or UI panels. Host registration must use the mappings above; the
manifest does not start a service or automatically enable a SIDIX integration.

## Verification and quotation report

From the repository root:

```sh
python -m unittest discover -s providers/quran-lab/tests
```

From `providers/quran-lab`:

```sh
python -m quran_lab validate
python tools/find_quotations.py PATH_TO_APP_DATA --output QUOTATIONS_REPORT.md
```

`PATH_TO_APP_DATA` is an existing, read-only local directory containing `surah/`
and `tafsir/`. The report detector needs these comparison files; using the
provider or running its tests does not. `--json` emits counts and locations as
JSON; `--studies-dir` selects a different study directory. It checks every
string field for maximal exact runs of at least eight normalised words within
the study's referenced ayahs. The report defines normalisation, overlap counting
and edition attribution. It prints no quotation text and does not establish
rights or identify every quotation.

Validation checks required fields, filename/id agreement, verse bounds,
unreviewed status, disclaimers, Arabic-script absence in studies, source label
cleanup, principle evidence ids and index consistency. Tests also cover result
provenance, cache isolation, CLI output, invalid data and quotation detection.

## Scholarly review

Open one [SIDIX issue](https://github.com/fahmiwol/sidix/issues) per study id.
Include the id, relevant field and verse, sourced corrections, analogy limits,
and a proposed disposition (revise, reject or endorse). Identify the reviewer's
qualifications and the scope actually reviewed. A proposal or automated check
does not change review status; a maintainer must record a real attributed review.

## Relationship to MiganCore

The Lab is a source of design **hypotheses** for MiganCore's evaluation and
gating work, **never evidence**. An experiment must test the proposed mechanism;
an analogy does not validate performance or establish a result. See
[MiganCore research method](https://github.com/fahmiwol/migancore-research-method),
[Inspiration with guardrails](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/06-inspiration-with-guardrails.md)
and [Ilham berpagar](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/06-ilham-berpagar.md).
This package's quotation policy is documented here: quotations are retained
with attribution and reported.
