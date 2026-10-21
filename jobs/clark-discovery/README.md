# Clark: orders the project cannot yet identify

Lewis (`jobs/lewis-originals`) and Clark are a pair. Lewis starts from an order whose wording is known
and looks for its official original. Clark starts one step earlier, from orders the project knows only
as a number, or does not know at all, and tries to establish what they are: a date, a title, a citing
document, a place to look. Whatever Clark can identify it hands to Lewis (`HANDOFF_TO_LEWIS.jsonl`);
the ProQuest text layers Lewis verifies feed Clark's citation harvest on the next run.

## Four kinds of unknown

| File | What it lists | How Clark finds it |
|---|---|---|
| `NUMBER_GAPS.csv` | Integers from 1 to the highest numbered order with no row in the 14,972-order census (46 on 2026-10-21, 22 of them a single run in June 1932, EO 5853–5879) | Enumerates the numbered series against `IDENTITY_LAYER_PROJECTION_14972.csv`. For each gap: the dates of the nearest known numbers on both sides (the window the missing order falls in), whether the American Presidency Project index, the OFR catalog or the ProQuest list knows the number anyway, and which saved texts cite it. `strength` is `strong` (an index gives a date or title, or a citation states a date), `cited` (named in a text, no date) or `number_only`. |
| `CITED_BUT_UNKNOWN.csv` | Executive-order numbers named in saved order texts and OFR disposition notes that are not in the census | Reads every saved text behind the project's fragment files (fr-originals, APP, Wikisource, HathiTrust, Richardson, the printed compilations, Lewis's ProQuest layers) and every OFR note. One row per (cited id, citing document) with the exact sentence and any date stated beside the number. |
| `IDENTITY_UNKNOWN.csv` | Census orders whose `original_text` step is open with no transcription lead and no date or title in any index: a number and nothing else | Joins the readiness tracker, the fragment files, the OFR catalog, the APP index, the WPA pre-1900 list and the ProQuest link list. Records what little is known (census year group, a ProQuest link and its accession year, a WPA line) and `where_to_look`. |
| `DATED_UNNUMBERED.csv` | "Executive order of <date>" references whose date matches no numbered order and no `census-completeness` cluster | Same text and note harvest; leads for the unnumbered series that census-completeness measures. |

### Plausibility of a citation

OCR produces false numbers in two shapes, and Clark ranks them below the real ones instead of dropping them:

- `likely_ocr_footnote_digit`: a five-digit number whose first four digits are a real order (`86402` is `8640` with a footnote
  marker glued on).
- `likely_ocr_letter_for_digit`: a letter where a digit stood, so the "suffix" plus the following digits re-read as a real
  order (`Executive Order 1T 060` is 11060; `1284S` is 12845). The re-reading is given in `glued_candidate`.
- `exceeds_numbers_issued_by_citing_date`: the cited number is higher than any order signed by the citing document's date.
- `rare_suffix_letter`: a letter the census has seen three times or fewer (the EO 3016 family runs A–X, so these are kept).
- `plausible`: none of the above. On 2026-10-21 this leaves 26 distinct ids, among them EO 27-A (1890), the 1894 run
  36–53 cited by their neighbours on Wikisource, EO 92 (1896), and the June 1932 orders 5855, 5856, 5862, 5867, 5872,
  5873 and 5875 cited by later orders with their dates.

A letter counts as a suffix only when attached or hyphenated (`325A`, `325-A`): the OCR of a small-caps Federal Register
heading spaces out the title's first letter (`EXECUTIVE ORDER 10728 E stablishing`), which must not read as 10728E. A
number after a comma is skipped when it is the volume of an `F.R.`, `Stat.`, `U.S.C.` or `CFR` cite.

## Handoff to Lewis

`HANDOFF_TO_LEWIS.jsonl` has one line per unknown with identity evidence: number gaps of strength `strong` or `cited`,
plausible lettered citations, and identity-unknown census orders that have a ProQuest link, a ProQuest PDF or a WPA line.
Each line says whether the id is in the census (`in_census`), the evidence, and the note that nothing follows from it.
Lewis routes these on its next run (`scope_reason: clark_identified` or `clark_identified_not_in_universe`).

## The web search (online stage)

After the offline pass, Clark hunts the open web in two ways, through the same search layer Lewis uses
(`jobs/_lib/eo_websearch.py`: open engine registry, escalating queries, hits followed and read, state carried forward,
robots.txt obeyed, keys from repository secrets when the owner adds them; see Lewis's README for the rules):

1. **Targets.** Number gaps with evidence and plausible cited-but-unknown ids first, then number-only gaps, then census
   orders known by number only (those on the ProQuest list last, since the PDF is their answer). Each run advances the
   least-searched targets one query strategy across every engine; pages that name the order are read and quoted
   (`WEB_LEADS.csv`), and every order number they name is checked against the census (`WEB_NUMBERS_NAMED.csv`).
2. **List pages.** Every page in `list_pages.txt` (Wikipedia's and Wikisource's lists, the American Presidency Project
   category, the OFR disposition tables, and any page the owner adds) is read, same-site links about executive orders are
   followed, and every order number named is harvested with the date and title printed beside it. Numbers the census
   lacks are in `WEB_LISTED_ORDERS.csv`.

Budget per run: `JOB_MAX_REQUESTS` (default 400, a quarter reserved for list pages) and `JOB_MAX_TARGETS` (default 30); short runs, state carried forward.

## What Clark does not do

Nothing here enters the census, changes a readiness count, or authenticates an identity. A number gap is a lead for the
census intake (`jobs/census-candidates`, the Stage 15 identity layer), never an entry; a citation is a sentence for a person
to read against its source. The June 1932 run shows why: the APP index has those orders with dates and titles, so the
census gap is probably an ingestion miss, but only a person checking the identity layer can say so.

## Outputs

`NUMBER_GAPS.csv`, `CITED_BUT_UNKNOWN.csv`, `IDENTITY_UNKNOWN.csv`, `DATED_UNNUMBERED.csv`, `HANDOFF_TO_LEWIS.jsonl`,
`REPORT.md` (the gaps table, the plausible citations, the web stage), `SUMMARY.json` (counts, input sizes, problems); from the
web stage `WEB_STATE.json`, `WEB_HITS.csv`, `WEB_LEADS.csv`, `WEB_NUMBERS_NAMED.csv`, `WEB_LISTED_ORDERS.csv`, `SOURCES.jsonl`,
`ENGINES.json`, `WEB_SUMMARY.json`. The consolidated table of every order and what is held for it is
`jobs/domesday-register/output/REGISTER.csv`.

## Running

GitHub: Actions → Run jobs → `clark-discovery`. It runs daily, after the tracker and the text-producing jobs when they run
together, and whenever the census or `research/pre-1937-sources/` changes. The offline pass takes about 20 seconds; the web stage runs within its request budget.

Locally, from the repo root:

```sh
REPO_ROOT=. OUTPUT_DIR=/tmp/clark python jobs/clark-discovery/job.py
```

`job.py` runs `test_clark.py` first (synthetic repository, no network) and stops if a test fails. The shared id, date and
mention-parsing helpers both jobs use are in `jobs/_lib/eo_identity.py`.
