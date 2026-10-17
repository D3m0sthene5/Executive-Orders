# Current-law scan (U.S. Code and eCFR)

**What it does, in plain words.** This job reads the federal law books by
machine and lists every place that names an executive order: the U.S. Code
(the statute books, with the editors' notes) and the Code of Federal
Regulations (the rule books), both as close as possible to the project's legal
cutoff, **October 14, 2026**. For each order it gives leads for three
questions the researchers ask by hand:

* *What keeps this order operating now?* For example, the Code still prints
  its text as a note, a statute refers to it, or a regulation lists it as its
  authority.
* *When was it, or a part of it, revoked or amended?* For example, an editor's
  note says "Ex. Ord. No. 12133 ... was revoked by Ex. Ord. No. 12368, June 24,
  1982".
* *Which of those statements read as ending the whole order?*

It costs no model tokens. It downloads official files politely (at most about
one request per second per site, robots.txt obeyed), so it does not hammer any
site.

## What it reads

| Source | What | How |
|---|---|---|
| uscode.house.gov (Office of the Law Revision Counsel) | The U.S. Code in USLM XML, one "release point" | By default the job reads release point **119-121**, current through Pub. L. 119-121 of **2026-10-09**, the last one dated on or before the cutoff. The ZIP addresses follow a fixed pattern, so this keeps working after the OLRC website stops listing 119-121. The download pages are still read, and a problem is reported if a newer release point dated on or before 2026-10-14 appears. |
| www.ecfr.gov search API | Every CFR section in force on 2026-10-14 that contains "Executive Order", "Executive Orders", "E.O.", "Ex. Ord." or "Exec. Order" | `date=2026-10-14`, which makes it point-in-time. It returns only an excerpt of each section. |
| www.govinfo.gov eCFR bulk XML | The full current text of each CFR title | Scanned in full. |
| www.ecfr.gov versioner "versions" list | Which sections changed after the cutoff | Mentions in those sections get no "checked through" date. |
| Repo files | `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv` (the 14,972 order ids), `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` (provisional YES/NO), `research/stage19/code/claim_gate.py` (used only by a unit test) | Listed in `needs.txt` |

Why not the eCFR "full XML" endpoint? `www.ecfr.gov/robots.txt` forbids
automated use of `/api/versioner/v1/full/`, so the job does not use it. It
uses the point-in-time search API plus the GovInfo bulk copy and the versions
list instead.

**Bad downloads.** Every download is checked before it is used: a ZIP must be
a real ZIP, XML must be XML (not an HTML error or CAPTCHA page), JSON must
parse. A wrong file is deleted, not cached, and is not listed as a source. If
one title file cannot be downloaded or read, the job writes a line under
"problems" in `SUMMARY.json` and carries on with the others. If a site's
robots.txt answers "forbidden", nothing on that site is fetched; if it cannot
be reached even after a retry, that site is skipped and reported.

## What it writes (to `OUTPUT_DIR`, committed as `output/`)

| File | One row per | Use |
|---|---|---|
| `MENTIONS.csv` | place where a law text names an order | The main list. `role` says what kind of place it is (see below). `instrument_id` is the project id (`EO:10450`). `is_predicate_lead` = yes when the place suggests the order still operates. `caution` explains why a place is *not* counted as such a lead (for example `text_says_revoked_or_superseded`, or a probable State, local or tribal order). `checked_through` is the date up to which the text is known to be current. |
| `EVENT_CANDIDATES.csv` | "revoked / superseded / repealed / amended" statement | Leads for when and how an order, or a part of it, ended or changed. `scope_candidate` says whether it reads as the whole order or a part; `caution` flags doubtful parses. |
| `FRAGMENTS.jsonl` | order x kind | Draft claim parts in the shared format, kinds `current_predicate_candidates`, `later_event_candidates` and `whole_order_end_candidates`. Every entry carries a claim-compatible source `{url, sha256, page_or_item}`. At most 80 entries per fragment; the CSVs have all of them. |
| `SOURCES.jsonl` | downloaded file | Custody: URL, sha256 of the exact bytes, size, retrieval time, content type, route. |
| `ORDERS_CURRENT_LAW.csv` | order named anywhere | Roll-up counts per order, with its provisional status. |
| `POSSIBLE_CONFLICTS.csv` | provisional **NO** order that current law still prints or cites | For review, strongest signal first: `1_printed_as_current_text_in_usc`, `2_cited_by_statute_or_regulation`, `3_printed_text_but_ending_statement_also_found`, `4_only_listed_as_amendment_of_a_printed_order`. |
| `USC_EO_NOTES.jsonl` | order whose text the U.S. Code prints | The full note text, as printed by the Office of the Law Revision Counsel. This is a secondary copy, not the original. |
| `ECFR_SEARCH_HITS.csv` | eCFR search hit | The point-in-time list of sections that matched each query. |
| `SUMMARY.json` | — | All counts, the release point chosen and why, per-title sha256 values, any problems, and `fragment_codes` (what every code in `FRAGMENTS.jsonl` means). |
| `FETCH_LOG.jsonl` | download attempt | Every request, cache hit, robots decision, rejected file and retry. |

The raw downloads (ZIP and XML, about 1.5 GB for a full run) stay in the cache
folder (`JOB_CACHE_DIR`, default `<OUTPUT_DIR>/../current-law-cache`) and are
not committed. Their sha256 values are in `SOURCES.jsonl`, so anyone can
download them again and check them.

### Roles in `MENTIONS.csv`

"Still operating" leads (`is_predicate_lead` = yes, unless a `caution` is set):

* `printed_eo_text`: the Code prints the order's text as a note, and the status line does not say it was revoked.
* `statutory_text_reference`: the statute text itself names the order.
* `references_in_text_note`: an editor's note says the statute text refers to the order.
* `statutory_note_reference`: law not classified to a section (printed as a note) names it.
* `amending_order_in_status_line`: the order amended a printed order. This is a weak lead.
* `cfr_text_reference`, `cfr_authority_citation`, `cfr_source_citation`, `cfr_appendix_text_reference`, `cfr_search_excerpt_reference`: a current regulation names it, lists it as authority, says it issued or amended the text, or reprints it.

Context only:

* `eo_note_ended_status`: a note saying the order was revoked or superseded.
* `ending_order_in_status_line`: the order that did the revoking.
* `mentioned_in_printed_eo_text`: named inside another printed order.
* Editorial, executive-document and other notes.

## Fragment notes for job 8 (the merge job)

* **One fragment per order and kind.** U.S. Code and eCFR entries are merged
  into one fragment; each entry says its `system` (`usc` or `ecfr`) and has its
  own `source`.
* **Names end in `_candidate` on purpose.** Nothing here is a verified claim
  value, so the names do not match the claim fields (`legal_basis`,
  `effective_date`, `date`, `actor`, `mechanism`). A merge has to decide to copy
  them after a human check.
  * `current_predicate_candidates` entries: `legal_basis_candidate` (a short
    label and the citation), `basis_code` (the mention role), `where`,
    `edition`, `snippet`, `checked_through`, `currency_code`, `mention_id`,
    `source`, and `text_path` for printed notes
    (`USC_EO_NOTES.jsonl#note_id=...`).
  * `later_event_candidates` entries: `date_candidate`, `date_basis_code`,
    `actor_candidate`, `mechanism_candidate`, `event_type_candidate`,
    `scope_candidate`, `scope_hint`, `acting_instrument_id`, `acting_raw`,
    `acting_scope`, `acting_fr_citation`, `caution`, `where`, `snippet`,
    `event_id`, `source`.
  * `whole_order_end_candidates` entries: the same date, actor and mechanism
    candidates for statements that name no section, paragraph or qualifier,
    name an actor, and carry no caution.
* **`date_candidate` is the date printed next to the acting order or law**
  (normally its signing date), never a verified effective date. It is null
  when no date is printed.
* **`checked_through`** is `2026-10-09` for U.S. Code entries, because release
  point 119-121 is current only through that law date. So the claim gate's
  "checked through 2026-10-14" test fails on purpose for those entries until a
  human confirms that no law of 2026-10-10 to 2026-10-14 changed them. It is
  `2026-10-14` for eCFR entries known to be point-in-time, and null when the
  section changed after the cutoff or its currency is unknown. If the release
  point read were ever dated after the cutoff, every U.S. Code entry would get
  null.
* **Codes** (`basis_code`, `currency_code`, `date_basis_code`,
  `scope_candidate`, `caution`) are spelled out in `SUMMARY.json` under
  `fragment_codes`.
* **Snippets are not exact quotes.** Whitespace is normalized, and ` | ` joins
  a note heading to its status line (or a search heading to its excerpt).
  Quote from the source itself.
* Events with the caution `chronology_impossible` or
  `subject_inside_prepositional_phrase` stay in `EVENT_CANDIDATES.csv` but are
  left out of the fragments.

## How to run

**On GitHub.** Commit and push the folder. The shared runner starts it. A full
run takes about 15–30 minutes and makes about 120 requests. It downloads about
1.5 GB to the runner's disk. The commit back is estimated at 40–80 MB of CSV
and JSONL (the full U.S. Code part measured 28 MB; the eCFR part is estimated
from a 3-title sample). No secrets are needed.

**On the owner's PC**, from the repo root, in PowerShell:

```
$env:REPO_ROOT='.'; $env:OUTPUT_DIR='C:/Users/danie/AppData/Local/Temp/eo-jobs/current-law/out'; python jobs/current-law/job.py
```

A small sample run reads two Code titles, two CFR titles and two search pages
per query:

```
$env:REPO_ROOT='.'; $env:OUTPUT_DIR='<dir>'; $env:JOB_LIMIT='2'; python jobs/current-law/job.py
```

PowerShell keeps `$env:` settings for the rest of the window; close it or set
them to `''` before a full run. In Git Bash the same commands are written
`REPO_ROOT=. OUTPUT_DIR=<dir> JOB_LIMIT=2 python jobs/current-law/job.py`.

Optional settings:

* `JOB_LIMIT=N`: at most N Code titles, N CFR titles and N search pages per query. `JOB_LIMIT=0` processes nothing.
* `JOB_USC_TITLES` / `JOB_ECFR_TITLES`: choose the titles, e.g. `03,05,50` (also `5` or `05A`) and `3,5,32`.
* `USC_RELEASE_POINT`: by default `119-121`. `auto` picks the newest listed release point dated on or before the cutoff. A point that is no longer listed can be given with its date, e.g. `119-123@2026-10-13`.
* `JOB_SKIP_USC=1` / `JOB_SKIP_ECFR=1`: skip one half.
* `JOB_OFFLINE=1`: use only the cache.
* `JOB_CACHE_DIR`: where downloads go.

A second run reuses the cached files.

The unit tests (`python -m unittest discover -s tests -t .` inside this
folder) run first and use only small files in `tests/fixtures` and short real
sentences, with no network. If a test fails, the scan does not run.

## What it does NOT establish

* **No legal conclusions.** A mention means the text names the order. It does
  not mean the order still has legal effect. A statute may cite a revoked order
  for history, a definition or a savings rule. Nothing here changes a
  provisional status, a ledger or a count. `POSSIBLE_CONFLICTS.csv` is a review
  queue, not a finding.
* **Editorial notes are secondary sources.** The Office of the Law Revision
  Counsel's notes are reliable leads, but the acting order or law is the
  authority.
* **Event dates are not effective dates.** The date given for an event is the
  one printed next to the acting order or law, usually its signing date. The
  legal effective date is not checked.
* **Whole or part.** `scope_candidate` is a reading of the sentence. A partial
  ending (one section, one paragraph) can still be missed when the sentence
  does not say so near the order's name, so a "whole order" candidate must be
  checked in the acting instrument.
* **Currency.**
  * The U.S. Code release point is current through a law of 2026-10-09. Any law
    enacted 2026-10-10 to 2026-10-14 is not reflected. U.S. Code entries
    therefore carry `checked_through: 2026-10-09`, not the cutoff, and a human
    must confirm the gap.
  * CFR entries carry `checked_through: 2026-10-14` only when the point-in-time
    search shows the section, or when the versions list shows no change to it
    after the cutoff.
* **Regex limits.** The job will miss:
  * orders cited without a number ("the Executive order of May 11, 1905");
  * numbers written with a thousands comma;
  * odd spellings.

  It may also produce false hits:
  * State, local or tribal orders, which are flagged in `caution` but not
    always caught;
  * statements about a rule, office or statute named next to an order (some
    are flagged `subject_inside_prepositional_phrase`, not all).

  Mapping to ids is by number, plus a letter suffix where one is given.
* **eCFR search excerpts are partial.** An order named only late in a long
  section is found by the bulk scan, not by the search.
* Sections removed after the cutoff are absent from the bulk file. They appear
  only through the point-in-time search.
