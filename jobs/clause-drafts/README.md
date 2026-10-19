# Job 3: draft clause inventories (`clause-drafts`)

## What it does

For each executive order whose original text is already saved somewhere in the
project, this job splits the text into its **operative parts** ("clauses") and
writes them out as a **draft** clause inventory in the shape the project's claim
format expects (`operative_clauses`, see `research/stage19/CLAIM_SCHEMA.md`).

It is a plain script. It uses **no AI model and no internet**: it only reads
files that are already in the repository.

For every order it:

1. finds the order inside the saved text (a Federal Register PDF, a web page
   copy, or an old Federal Register issue);
2. checks that the text really is that order (see "Wrong-order protection"
   below) and sets the text aside if there is doubt;
3. sets aside the title, the "Whereas ..." and "By the authority vested in me
   ..." recitals (these are recorded as *non-operative*, not clauses) and the
   signature / "THE WHITE HOUSE" / date / filing block (excluded);
4. splits the rest on the order's real structure: `Section 1.` / `Sec. 2.` /
   `SEC. 2 (a)` (with or without a period after the number) / `SECTION I.`,
   the web-page form `Section 1` `.` `Purpose` `.` on separate lines,
   `(a)`, `(1)`, numbered paragraphs `1.`, Carter-style `1-101.`, or, for an
   order with no numbers, its paragraphs (a one-paragraph order becomes a
   single clause `#whole`);
5. labels each clause with a guessed kind, for example `amends_other_order`
   or `revokes_or_supersedes_other_order` (with the other order's number),
   `general_provisions`, `definitions`, `purpose_or_policy`, `effective_date`;
6. copies the clause text **exactly** (character for character) from the saved
   text, and checks this again at the end.

Every clause gets a stable id such as `EO:12944#sec5(b)` and a source
reference (web address, SHA-256 of the original file, page or item), ready to
paste into a claim. The legal fields (`state_at_cutoff`, `first_end`,
`current_predicate`, `later_events`) are left **empty** and marked
`needs_judgment`.

## What "good" and "partial" mean

Every draft says `segmentation_quality: good` or `partial`. This is only about
**how well the text was cut up**, never about the law.

- **good** means the automatic checks found **no structural problem**: the
  heading, body and signature were found; every `Sec. N.` line starts its own
  clause; no clause is longer than 6,000 characters; no clause still holds two
  or more `(a)`/`(b)` or `(1)`/`(2)` items of its own series that were not split
  out; section numbers run without a gap; and, for old scanned Federal Register
  issues, nothing suggests text from other columns was mixed in. A person must
  still check it.
- **partial** means at least one of those checks failed. The reasons are listed
  in `segmentation_warnings` (for example `incomplete_clause_over_6000_chars_...`,
  `incomplete_section_markers_not_split_2`, `section_number_gap_4->7`,
  `ocr_columns_may_be_interleaved:...`, `no_signature_block_found`). Treat
  partial drafts as rough starting points.

## Wrong-order protection

Some saved copies are not what their file name or web address says. The job
does not let those into `FRAGMENTS.jsonl` or `SOURCES.jsonl`:

- web pages whose saved record says the server answered with an error (for
  example 404), and texts that read like an error or block page ("Page Not
  Found", "Access Denied", CAPTCHA ...), are skipped;
- an American Presidency Project page counts **only for the order in its own
  title** (for example the page at `.../executive-order-4359-...` whose title
  is "Executive Order 4359-A" is used for EO:4359A, never for EO:4359). Numbers
  found inside the body of a page never create a draft for that number; pages
  whose title is a statement, proclamation or letter are skipped;
- a draft is moved to `IDENTITY_QUARANTINE.csv` instead of `FRAGMENTS.jsonl`
  when: the text cites its own number in a recital or as an order being
  amended/revoked (a page holding a later order), the text has no heading so
  the identity would come from the web address only, the page title and the
  web address name different orders, or the printed date / the signing
  president do not fit the order's year (one year of tolerance).
- American Presidency Project pages harvested by `app-executive-orders` (whose
  held text is the page body; the heading is in the record) count only for the
  order their **own heading** names: a heading that is not a numbered executive
  order, or names another order than the record, is refused; an address naming
  another order, or a page date more than a year from the census year, is
  quarantined; a record whose text file does not hash to its `text_sha256` (the
  file holds another capture of the page) is refused.

## What it does NOT establish

- It does not decide whether any part of any order was in force on the legal
  cutoff (14 October 2026), or when or how it ended. Those fields stay empty.
- Clause boundaries, kinds and "target" orders are machine guesses (leads).
  A person must check each inventory against the source before using it.
- It does not prove that a saved copy is authentic. Web copies (American
  Presidency Project) are transcriptions, not official editions. The checks
  above catch common wrong-order cases, not all of them.
- FR page numbers for old scanned issues are **candidates** read from the OCR
  page numbers (marked as such); they must be checked against the page image.
- It never changes any provisional status, ledger or count.

## Inputs (read only)

| Input | What is used |
|---|---|
| `research/stage21/original_sources/*.pdf` + `CASE_ORIGINAL_SOURCE_CUSTODY.csv` | Official GovInfo Federal Register PDFs (40). Text is extracted with `pypdf` (pinned in `requirements.txt`); page headers, page numbers and print codes are removed. The SHA-256 of each PDF is checked against the custody list. |
| `research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv` | The FR citation (e.g. `60 FR 309`) so each clause gets an FR page. |
| `releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip` | Text extractions saved by the Opus research, read one file at a time without unpacking. Only texts whose `.meta.json` records an https address, the SHA-256 of the original bytes and a 200 (OK) answer, from GovInfo, FederalRegister.gov or the American Presidency Project, are used. Column-layout texts are skipped; texts flattened onto one line (all paragraph and section breaks lost) are not split and are listed in `NOT_SEGMENTED.csv`. The SHA-256 of each text file in the zip is compared with the text hash in its meta file (reported in `SUMMARY.json`). |
| `jobs/fr-originals/output/`, `jobs/source-ladder/output/` | SOURCES.jsonl records (shared SOURCE RECORD format) and their `texts/`. If their output is not there yet, the job simply notes it. Other job names can be added with `CLAUSE_INPUT_JOBS=a,b`. |
| `jobs/app-executive-orders/output/` `DOCUMENTS.jsonl`, `MIRROR_DOCUMENTS.jsonl`, `texts/` | American Presidency Project pages, live and from web-archive captures: **transcriptions, a fallback input only**. The draft text is the page heading line, a blank line, then the held body text. Turn off with `CLAUSE_APP_INPUT=0`. |
| `research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv` | Valid order ids, years and eras. |
| `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` | Only to mark which orders are among the 3,359 provisional cases. |

When an order has several copies, the job prefers, in this order: official
born-digital FR PDF (1994 on), the GovInfo HTML version of the same FR
document, FederalRegister.gov text, American Presidency Project transcription,
and last the OCR text of old scanned FR issues. Among copies that can be used,
one without identity doubt wins over one with doubt, and a "good" one over a
"partial" one. The other copies are listed under `alternate_sources`.
An APP page from `app-executive-orders` is used only when no other copy of the
order gives a usable draft without identity doubt (a "partial" official copy
still wins over a "good" APP page). Its draft goes to `FRAGMENTS_APP.jsonl`,
labelled `transcription_based: true`, `acceptable_as_original: false`,
`representation_type: secondary_compilation_transcription`, with a
`confidence_note` that starts "TRANSCRIPTION-BASED". Every clause must be checked
against the official original before it is used in a claim.

**If the Opus zip or the universe list cannot be read** (for example because
`git lfs pull` failed on GitHub), the job **stops with an error** and builds
nothing, so that a broken download never replaces a full earlier result with a
small one. To build anyway from what is there, set
`CLAUSE_ALLOW_PARTIAL_INPUTS=1`.

## Outputs (in `output/`)

| File | What it is |
|---|---|
| `FRAGMENTS.jsonl` | One line per order: `{"instrument_id", "kind": "operative_clauses", "data": [clauses], "sources", "confidence_note", "produced_by": "clause-drafts", ...}`. Extra keys: `non_operative` (title, recitals), `excluded` (signature block), `segmentation_quality` (`good` or `partial`, see above), `segmentation_warnings`, `identity_evidence` (how identity was found, signature line, printed year, expected year), `alternate_sources`, `era`. |
| `FRAGMENTS_APP.jsonl` | The same shape, for drafts cut from American Presidency Project transcriptions (fallback input; see above). Kept separate so neither file passes GitHub's 95 MB limit; claim-kit and claim-drafts read both. |
| `CLAUSES.csv` | The same clauses, one row each (opens in Excel), with the first 200 characters of each clause as `text_preview`. The full text is in `FRAGMENTS.jsonl` and `texts/`; it is not repeated here to keep the files small. |
| `SOURCES.jsonl` | One SOURCE RECORD per saved text used (shared format). `bytes` is the size of the original file when Opus recorded it, otherwise `null` (the notes then say so). For Opus copies the original bytes are not in the repo, so the SHA-256 can only be checked by fetching the address again. |
| `texts/` | The exact text of each order that the clauses were cut from (UTF-8). For web pages it runs from the order's own heading to the end of the order (no site menus or footers). |
| `IDENTITY_QUARANTINE.csv` | Orders whose best text may be a different order, with the reasons, the signature line, printed year and expected year. Nothing from these is in `FRAGMENTS.jsonl` or `SOURCES.jsonl`. |
| `NOT_SEGMENTED.csv` | Orders that had a saved text but could not be split usefully, and why (each copy tried). |
| `INPUT_PROBLEMS.csv` | Inputs that could not be used (missing PDF, no SHA-256, wrong year, text hash differs from meta ...). |
| `SUMMARY.json` | Counts by era, kind, structure, source grade and quality; which inputs were available; quarantine reasons; drafts from APP transcriptions; `segmentation_outcomes_by_input` (good / partial / unusable / identity doubt / not located, one count per candidate copy; with the `MEASURE_ALL` file in this folder every copy of every order is segmented, otherwise copies after the first good one are skipped); the self-check (every clause text must be an exact substring of its saved text; the job fails if not) and the zip-text-versus-meta hash comparison. |

Each clause in `data` looks like:

```json
{"scope_id": "EO:12944#sec5(b)", "label": "Sec. 5(b)", "heading": "Interim geographic adjustments",
 "clause_kind": "operative", "related_orders": [],
 "original_operative_text": "(b)(1) The Office of Personnel Management shall prescribe ...",
 "original_source": {"url": "https://www.govinfo.gov/...", "sha256": "...", "page_or_item": "60 FR 309-310 (PDF pp. 1-2); Sec. 5(b)"},
 "text_offsets": {"text_path": "texts/....txt", "start": 2100, "end": 3170},
 "contains_page_furniture": false,
 "state_at_cutoff": null, "first_end": null, "current_predicate": null, "later_events": [],
 "needs_judgment": ["state_at_cutoff", "first_end_or_current_predicate", "later_events", "clause_boundaries_and_completeness"],
 "draft_status": "machine_draft_unverified"}
```

In `related_orders`, `target_candidate` means "this clause seems to amend or
revoke that order" (a lead for that order's history), and
`mentioned_as_prior_amender` means the order is only named as an earlier
amendment ("as amended by Executive Order Nos. 12887 and 12912").

If a clause runs across a page break in a text saved by another job, the exact
text keeps the page header (`contains_page_furniture: true`) and a cleaned
`reading_text` is added for reading.

## How to run

**On GitHub:** commit a change to this folder (or use Actions → Run jobs →
type `clause-drafts`). The runner downloads the folders in `needs.txt`, fetches
the Opus zip from Git LFS itself (about 200 MB), runs the tests, then the job.
A full run takes a few minutes, most of it the download.

**On the PC** (from the repository folder, in Git Bash):

```
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/AppData/Local/Temp/eo-jobs/clause-drafts/output python jobs/clause-drafts/job.py
```

Options (environment variables):

- `JOB_LIMIT=40` – process at most 40 orders (spread across eras). It must be
  a whole number of 1 or more; leave it unset to process everything.
- `JOB_IDS=EO:9066,EO:12944` – only these orders.
- `JOB_CACHE_DIR=...` – where the job keeps its scan index of the Opus zip
  (default: next to `OUTPUT_DIR`, in `clause-drafts-cache`). Nothing is
  downloaded.
- `CLAUSE_INPUT_JOBS=fr-originals,source-ladder` – other jobs whose saved texts
  are read.
- `CLAUSE_ALLOW_PARTIAL_INPUTS=1` – build even if the Opus zip or the universe
  list is missing (not recommended on GitHub).
- `CLAUSE_APP_INPUT=0` – do not read the American Presidency Project pages.
- `CLAUSE_MEASURE_ALL=1` (or a `MEASURE_ALL` file in this folder) – segment
  every candidate copy to measure each source's outcomes; the choice of copy is
  unchanged. Adds about 40 seconds.

The tests (`test_segment.py`, `test_build.py`, `test_regressions.py`) run first
and use small excerpts from several eras, including the real texts that the
first version got wrong; if any test fails, nothing is built.
