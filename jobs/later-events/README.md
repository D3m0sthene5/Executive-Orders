# Later events: which later acts revoked, amended or superseded each order

This job builds a **map of later changes** to executive orders: for each order,
which later instrument (another executive order, a Public Land Order, a
statute, a proclamation, ...) is recorded as revoking, amending, superseding,
continuing, suspending or reinstating it, with the date stated in the data,
the exact quoted wording and where that wording came from.

It replaces the mechanical part of the "ending_or_current_basis" and
"counterevidence" steps of the readiness tracker: a researcher no longer has to
look up the disposition table and the later orders by hand to find the
candidate events. It costs no model tokens to run.

## What it does NOT establish

Everything this job writes is a **lead (a candidate)**, never a legal finding.

- The Office of the Federal Register's "disposition notes" are editorial
  cross-references. They can be wrong, incomplete, or describe only part of an
  order.
- A date shown (`date_candidate`) is the acting instrument's date as stated in
  the note or its signing date in the OFR catalog. It is **not** a proven
  effective date. When the wording itself says "effective <date>", that date is
  listed separately (`stated_effective_date`), never instead of the first one.
- A full revocation found here does not mean the order stopped having effect on
  that date: parts may have ended earlier (sunset, completed task, statute),
  the revoking order may have savings clauses, and the order may have been
  reinstated later (the job lists reinstatement candidates next to each
  revocation, for example EO 13933 revoked in 2021 and reinstated in 2025).
- "See:" items are pointers only (mechanism `cross_reference`).
- It never changes any provisional status, ledger or count.

## Where the information comes from

1. **The OFR executive-order catalog** (all 6,939 records from 1937 to now,
   including pre-1994 records), fetched from the documented public API at
   `https://www.federalregister.gov/api/v1/documents.json` in 7 pages of 1,000.
   The Stage 21 bulk snapshot was never stored in the repo (its export address,
   `/documents/search`, is closed to robots by the site's robots.txt), so this
   job uses the API instead. Each record's `disposition_notes` field is parsed:
   "Revoked by: EO 9521, February 13, 1945", "Revokes: EO 6119 (in part)",
   "Superseded by", "Amended by", "Continued by", "Supplemented by", "See",
   "Note: ... nullified by ...", nested "(which was revoked by EO ...)", and so
   on. Every line of a note is read on its own, including lines written
   without a colon ("Revoked by EO 11975, March 7, 1977", "Nullified by treaty
   with Japan on May 15, 1972", "Council terminated by EO 12007", "Commission
   ceased to function on November 15, 1969"). A line the parser does not
   understand is never silently dropped: it goes to
   `UNPARSED_NOTE_SEGMENTS.csv`. Both directions are kept, so the same event
   usually appears twice (on the revoked order's record and on the revoking
   order's record), which is a useful cross-check.
2. **Texts of later orders** that already exist in the repo, scanned for
   operative sentences such as "Executive Order No. 9876 of May 1, 1948, is
   hereby revoked", "Section 3 of Executive Order 11111 is revoked insofar as
   ...", "This order supersedes Executive Order ...", "I hereby revoke ...":
   - texts saved by the `fr-originals` job (read through its `SOURCES.jsonl`;
     used automatically once that job has run),
   - American Presidency Project order pages harvested by `app-executive-orders`
     (live and web-archive captures), read through
     `jobs/app-transcriptions/output/SOURCES.jsonl`, one text per order
     (evidence type `order_text_app_transcriptions`). These are secondary
     transcriptions: their edges are leads like any text edge, and their "in
     part" wording is flagged (`transcription_text_says_partial_end_kept`) but
     never withholds a whole-order end stated in an OFR note, so a transcription
     can never remove a counterevidence lead,
   - the 40 GovInfo PDFs in `research/stage21/original_sources/` (sha256
     checked against the custody file; text read with `pypdf`),
   - order texts inside the Opus Stage 11 release zip (American Presidency
     Project pages and Federal Register excerpts, each with its original URL and
     sha256 from the Opus `.meta.json`). Search-result pages are skipped, and a
     text is used only when its own text or URL names the order.
   Lists ("Nos. 9001, 9002 and 9005"), ranges ("9001-9010", marked as expanded),
   letter suffixes ("325-A") and halves ("1182 1/2") are normalised. Orders named
   only in "as amended by ..." or "which ... revokes ..." phrases are not taken as
   targets. Qualifiers such as "in part", "Section 3 of", "Sections 5 (b), 7,
   and 8 of", "Paragraph 6 of the said", "The prohibitions contained in",
   "insofar as", "to the extent", "with respect to" are kept. Negated wording
   ("is not revoked", "nothing in this order shall be construed ...") is
   ignored, and "revoked or amended" is marked as uncertain. For American
   Presidency Project pages only the document body is read (the site's menus
   and the citation footer are cut off first).

## When is something offered as a "whole-order end"?

Only when all of these hold:

- the mechanism is a revocation, rescission or "superseded or revoked", with no
  qualifier at all (no "in part", section, provision, range, uncertainty ...);
- no other piece of evidence for the **same acting instrument and order** says
  the action was partial (otherwise the item is kept as a later event with the
  flag `full_and_partial_evidence_conflict`);
- an OFR note states it. A revocation found only in an order's text is kept as a
  later event with the flag `text_only_unverified`, not as a whole-order end.

## Outputs (in `output/`)

| File | What it is |
| --- | --- |
| `EDGES.csv` | One row per piece of evidence: acting instrument -> target order, mechanism, qualifier, date candidate and how that date was obtained, any date conflict flags, any stated effective date, evidence type, source id/URL/sha256, page or item, the note label, and the quoted wording. `quote` is always an exact piece of the source (only runs of spaces and line breaks are squeezed to one space): for notes, the note item (with its label when they sit together); for order texts, the whole sentence, with `quote_span` giving its character position in the scanned text. `quote_kind` says which. |
| `FRAGMENTS.jsonl` | Claim fragments for the merge job: `later_event_candidates` for every order with at least one edge, and `whole_order_end_candidates` only under the rules above. Both kinds use the same date fields: `date_candidate` (the acting instrument's date, not an effective date), `date_basis`, and `stated_effective_date_candidates`. |
| `SOURCES.jsonl` | Source records (URL, sha256 of the exact bytes, size, retrieval time, route) for every API page and every text scanned. |
| `CATALOG_INDEX.csv` | The OFR catalog in compact form (order, signing date, FR citation, document URLs, disposition note). Other jobs can use it as an index. |
| `COUNTEREVIDENCE_LEADS.csv` | Orders provisionally marked "still in effect" (YES) that have a full-revocation candidate, with any later reinstatement candidates. |
| `UNPARSED_NOTE_SEGMENTS.csv` | Note text the parser could not turn into an edge (often self-terminating commissions: "Commission to terminate by July 29, 1968"). Worth a human look. |
| `TEXT_SCAN_LOG.csv` | Each text scanned, whether the order's own heading was found in it, whether the American Presidency Project page body was cut out, and how many candidates it gave. |
| `SUMMARY.json` | Counts by mechanism and evidence type, how many of the 3,359 decided orders have candidates, how many full ends were held back and why, and which text inputs were available on the machine that ran the job (`text_inputs_on_this_machine`). |

Evidence types: `ofr_note_on_target` (stated on the changed order's record),
`ofr_note_on_acting` (stated on the acting order's record),
`ofr_note_see_reference`, `ofr_note_nested`, `ofr_note_freetext`,
`order_text_govinfo_pdf`, `order_text_opus_official_copy`,
`order_text_opus_mirror` (a reputable mirror such as the American Presidency
Project, not an official edition), and `order_text_fr_originals` once that job
exists.

## How to run

**On GitHub:** commit a change in this folder (or use Actions -> Run jobs ->
Run workflow and type `later-events`). It needs about 1 minute and makes 7
requests to federalregister.gov. The Opus release zip is not downloaded on
GitHub by default (it is a 208 MB Git LFS file), so on GitHub only the OFR notes
and the Stage 21 PDFs (and fr-originals texts, once present) are used. To
include the Opus texts on GitHub, add an empty file named `PULL_OPUS_LFS` to this
folder; this uses about 208 MB of the repo's Git LFS download allowance per run.

**On the PC** (open a terminal in the repo folder). First, once:
`python -m pip install --user pypdf==6.20.1`

In **PowerShell** (the usual Windows terminal):

```
$env:REPO_ROOT = '.'
$env:OUTPUT_DIR = 'C:\Users\danie\AppData\Local\Temp\eo-jobs\later-events\out'
python jobs\later-events\job.py
```

In the old **Command Prompt** (cmd.exe) the same is:

```
set REPO_ROOT=.
set OUTPUT_DIR=C:\Users\danie\AppData\Local\Temp\eo-jobs\later-events\out
python jobs\later-events\job.py
```

(Do not type the `set` lines into PowerShell: there they do not set anything,
and the job would then write into `jobs\later-events\output` inside the repo.)

In Git Bash: `REPO_ROOT=. OUTPUT_DIR=/c/Users/danie/AppData/Local/Temp/eo-jobs/later-events/out python jobs/later-events/job.py`.

**GitHub and PC results differ.** On the PC the Opus release zip is present,
so about 960 more order texts are scanned; on GitHub (without `PULL_OPUS_LFS`)
they are not. Whichever run is committed last replaces the other's output.
`SUMMARY.json` -> `text_inputs_on_this_machine` records which inputs a run had.

Optional settings:

- `JOB_LIMIT=50` - a small trial: only the first 50 catalog records (one small
  request) and at most 50 texts from each kind of source.
- `JOB_CACHE_DIR=<folder>` - where downloaded API pages are kept (default: a
  `later-events-cache` folder next to the output folder). Reruns reuse them and
  make no requests; set `LATER_EVENTS_REFRESH=1` to fetch fresh copies.
- `LATER_EVENTS_TEXT_JOBS=fr-originals,other-job` (default
  `fr-originals,app-transcriptions`) - other jobs whose
  `SOURCES.jsonl` texts should be scanned (only records naming exactly one
  order are used, and the order is taken to be the text's author).

The job runs its unit tests first and stops if any fails. It writes nothing
outside `OUTPUT_DIR` and the cache folder, with one exception: when the
`PULL_OPUS_LFS` file (or `LATER_EVENTS_PULL_OPUS_LFS=1`) is set and the Opus
zip is only a Git LFS pointer, it runs `git lfs pull` for that one zip, which
downloads the real file into `releases/opus_stage11_complete/` in the checkout.

## Known gaps

- Tables that list bare numbers under "The following Executive Orders are
  revoked:" (no "Executive Order" before each number) are not read from order
  texts; the OFR notes usually cover them.
- Body references such as "that Executive order is hereby revoked" are not
  resolved to a number.
- `FRAGMENTS.jsonl` is about 33 MB and `EDGES.csv` about 17 MB on a full PC
  run, mainly because every source reference must repeat the long API page
  address (the API only returns the disposition notes when the field list is in
  the address). Both stay well under GitHub's 95 MB limit.
