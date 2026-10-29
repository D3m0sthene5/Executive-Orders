# Claim checker job

**What it does, in one line:** it does the mechanical half of reviewing every
claim in `research/readiness/claims/`, so reviewers (Opus, Astra, people) spend
their time only on legal judgment.

It costs no model tokens: it is an ordinary Python script.

## Dashboard refreshes and receipt freshness

Check the combined `research/readiness/claims/` directory before regenerating the
readiness tracker. A successful saved batch replay only checked its selected
claims; it cannot establish a combined total after other batches are merged.
`output/PER_CLAIM.json` binds receipts to exact claim SHA-256 values, and
`output/STATUS.json` identifies the successful generation and input commit.
New or revised claims need matching receipts before they can advance readiness.

Use the shared runner with the complete declared source inputs for this refresh.
A partial local checkout can lack held source bytes and produce different custody
results. Report the published generation's date and any newer unprocessed filings
until a combined checker and tracker run succeeds. Mechanical checks establish
custody, quotations, identity, dates, and structure; human certification remains a
separate measure.

## What it checks

For every claim (Stage 19 format, see `research/stage19/CLAIM_SCHEMA.md`) and every
source reference inside it (`original_representation`, each clause's
`original_source`, `first_end.source`, `current_predicate.source`,
`later_events[].source`, `whole_order_end.source`, `savings_residuals.source`,
and any other `source` / `sources` field):

| Check | What it asks | Possible answers |
|---|---|---|
| `source_held` | Does the project hold a saved copy whose SHA-256 is exactly the one the claim gives? | see "Which custody counts as held" below; also `held_but_different_hash` (the project has this URL, but different bytes: fail), `not_held` (fail), `held_record_but_local_bytes_differ` (a custody record is wrong: fail), `no_hash_in_reference` |
| `source_identity` | Is the original text (`original_representation`) and each clause's `original_source` a copy of **this** order, not another order's? | `recorded_for_this_order` (a custody record names this order: pass); `text_names_this_order` (no record names any order, but the text says "Executive Order <this number>": pass); `recorded_for_other_order` (records name only other orders: fail); `recorded_for_other_order_but_text_names_this_order` and `text_does_not_name_this_order` (warn: a person must look; the step does not count as passed); `no_order_association_or_text` (unverified) |
| `quote_verbatim` | Does every quotation (`original_operative_text`, and any field named `quote`, `quoted_text`, `excerpt`, `verbatim` ...) appear word for word in the saved text of the source it cites? | `exact`; `normalised` (only whitespace, ligatures such as "ﬁ", and words split across a line break with a hyphen were evened out); `not_found` (fail, with a hint such as "would match only if the dash were changed" and how many leading words were found); `too_short_to_verify` (found, but under 6 words and under 30 characters, so it proves nothing: warn, the step does not count as passed); `source_text_not_available` (unverified). The detail always names the URL and the first 12 characters of the SHA-256 that was searched, and how many times the quotation occurs. |
| `date_valid` | Are dates real `YYYY-MM-DD` dates? Legal dates (`date`, `effective_date`, `checked_through`, ...) must not be after the cutoff **2026-10-14**. Research dates (`checked_on`, `retrieved_utc`, ...) may be after the cutoff but not in the future. | pass / fail |
| `date_after_signing` | Is each `first_end.date`, `later_events[].effective_date`, `current_predicate.checked_through` and `whole_order_end.date` on or after the order's own signing date? | pass / fail; when only the year is known (identity layer), a date in an earlier year is a `warn` |
| `order_exists` | Is every executive order cited anywhere in the claim ("EO:12944", "Executive Order No. 12826", "E.O. 12,944", "Executive Orders 12826 and 12886", "Executive Order 106-1") in the 14,972-order universe? Citation parts such as "1995 Comp.", "60 FR 309" or "92 Stat." are not read as order numbers. | pass / fail |
| `structural_gate` | The project's own `research/stage19/code/claim_gate.py` `validate_claim` (imported, not copied), with the order's provisional status. | one row per gate error, or `gate_passed`; `gate_raised_exception` if the gate itself crashed on a value of the wrong type (the claim fails; the run goes on) |

A quotation is checked against the source it sits in (for example a `quote`
inside `sources[0]`), otherwise the nearest enclosing `source` /
`original_source`, otherwise `original_representation`.

Each row also names the readiness step it belongs to (`original_text`,
`clause_inventory`, `ending_or_current_basis`, `savings_residuals`,
`counterevidence`, or `claim_record`), using the readiness tracker's own mapping.

## Which custody counts as "held" (the owner's policy)

| Status | Meaning | Counts as |
|---|---|---|
| `held_bytes_verified` | the saved bytes were re-hashed on this machine and match | pass |
| `held_bytes_in_release_or_repo` | the bytes are committed (a repo file, or a member of the Opus Git LFS release) but are not on this machine, so they were not re-hashed here | pass |
| `custody_record_only` | only a record exists (a hash, perhaps extracted text): for example another job's `SOURCES.jsonl` entry whose bytes are only in that job's download cache, or an Opus fetch record that kept the text but not the bytes | **unverified** (the step does not count as passed) |

This table is `SOURCE_STATUS_RESULT` at the top of `checker.py`. If you want, for
example, `custody_record_only` to count as passed, ask an agent to change that
one line; nothing else needs to change. Note what it means today: on GitHub,
other jobs' download caches are thrown away after each run, so a source that
only another job's cache holds is `custody_record_only` there. On the PC, with
`CLAIM_CHECKER_CACHE_ROOTS` pointing at those caches, the same source can be
`held_bytes_verified`.

## Where "held" copies are looked up

All saved copies the project records, matched by SHA-256 (and by URL to detect
"different bytes"):

- `jobs/*/output/SOURCES.jsonl` of every job (the shared source-record format;
  their extracted text at `text_path` is used for quotations; malformed lines
  are skipped and counted in the log, never fatal),
- printed volumes committed under `releases/` (Git LFS) that a job's `data/PROVENANCE.json` names by `pdf` and
  `pdf_sha256` (the source-book jobs: ofr-compilations, isthmian-canal-1911, indian-reservations-1912,
  richardson-volumes, ofr-codification-1989). A volume is held only when the file is in the checkout and either is
  those bytes (re-hashed here when cited) or is an LFS pointer whose `oid` is exactly that sha256
  (`held_bytes_in_release_or_repo`). The job's per-order OCR texts (`original_representation` fragments citing the
  volume, with a `text_path`) are text copies of it, recorded for that order, so quotations and order identity are
  checked against them. Being held says nothing about whether a volume is an original (that is the tracker's and
  claim-drafts' rule),
- `research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv` and
  `ACQUISITION_LOG.jsonl` (the official PDFs in that folder are re-hashed),
- `research/stage20/output/STATUTE_FETCH_INDEX.csv` (Statutes at Large PDFs) and
  `OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv` (Opus images/PDFs),
- `research/stage18/SOURCE_MANIFEST.json` (early FR, LoC, Statutes excerpts),
- the Opus Stage 11 release manifest: read from the 207 MB Opus zip when it is on
  the machine (the owner's PC), otherwise from the small committed index
  `data/opus_manifest_index.csv.gz` (27,237 files plus 9,203 URL→hash fetch
  records; provenance in `data/opus_manifest_index.json`).

Signing dates come from the Stage 21 crosswalk (`signing_date_from_cached_index`),
the Stage 14 official fetch manifest, any `jobs/*/output/*.csv` that has
`instrument_id` and `signing_date` columns (for example a future OFR index job),
and, as a year only, the identity layer.

## Outputs (in `output/`)

- `REPORT.md`: read this first. Counts and the claims with problems.
- `PER_CLAIM.json`: a summary per claim (`claims`), and `by_instrument`: for each
  order, the claim the tracker would use (the last line, by file name then line)
  with its `claim_sha256`, `mechanical_result` (`pass`, `pass_with_unverified`,
  `fail`), `gate_passed`, `all_checks_passed` and `steps_checker_passed`. Each
  claim also has `check_counts` (how many checks of each kind passed, failed,
  warned or were skipped), `failures` and `unverified` (first 50 of each).
- `CLAIM_CHECKS.csv`: the rows that did **not** pass (fail, warn, skip), one per
  claim × check × field: `claim_key` (file:line), `instrument_id`,
  `effective_for_tracker`, `step`, `check`, `field`, `result`, `status`,
  `detail`. Passing rows are left out to keep the file small (their counts are
  in `PER_CLAIM.json`); set `CLAIM_CHECKER_CSV_ALL_ROWS=1` to include them. If
  the file would still be over 50 MB (`CLAIM_CHECKER_CSV_MAX_MB`), it keeps only
  the claims the tracker uses, then only their failures, and `SUMMARY.json`
  (`claim_checks_csv.mode`) says so. GitHub cannot commit files over 95 MB.
- `SUMMARY.json`: counts (no timestamps, so the daily run commits only on change).
- `FETCH_ATTEMPTS.jsonl`: only with `--fetch`.

## How to run

**On GitHub:** nothing to do. It runs every day (the `DAILY` file) and whenever
this folder changes. It downloads nothing. GitHub only reruns it when this
folder changes or daily, so a new claim is checked at the latest the next day;
to check at once, open Actions → Run jobs → Run workflow, type `claim-checker`.

**On the PC** (from the repo folder), in PowerShell:

```
$env:REPO_ROOT='.'; $env:OUTPUT_DIR='C:/Users/danie/AppData/Local/Temp/eo-jobs/claim-checker/out'; python jobs/claim-checker/job.py
```

or in Git Bash:

```
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/AppData/Local/Temp/eo-jobs/claim-checker/out python jobs/claim-checker/job.py
```

Use a folder outside the repo for `OUTPUT_DIR` on the PC. (In PowerShell the
`$env:` settings stay for the rest of that window; close it or set them to `''`
afterwards.)

Options (environment variables):

- `JOB_LIMIT=20`: check only the first 20 claim lines.
- `JOB_CACHE_DIR=<folder>`: where extracted PDF text is cached (default: next to
  the output folder, `claim-checker-cache`). Never committed.
- `CLAIM_CHECKER_CLAIMS=<glob>`: check claims somewhere else (for trying out
  drafts). The `claim_key` of such claims is then their full path on this PC.
- `CLAIM_CHECKER_CACHE_ROOTS=<folder>`: where other jobs' download caches live,
  so their saved bytes can be re-hashed.
- `CLAIM_CHECKER_CSV_ALL_ROWS=1`, `CLAIM_CHECKER_CSV_MAX_MB=50`: see Outputs.

`--fetch` (off by default and on GitHub): for every source that is not held,
ask the source ladder (`jobs/source-ladder/fetch_ladder.py`) to download it,
politely, and record in `FETCH_ATTEMPTS.jsonl` whether the downloaded bytes
match the claim's hash. It does **not** make anything "held": to keep a copy,
put the URL through the source-ladder job, whose `SOURCES.jsonl` is then found
here. `CLAIM_CHECKER_FETCH_MAX_REQUESTS` caps requests (default 300).

The unit tests (`test_checker.py`, no network) run first; if they fail, nothing
is checked.

### If it fails

- On GitHub, open `jobs/claim-checker/output/log.txt`. A bad claim line does
  **not** stop the run: it is reported as `CHECKER ERROR on claim
  <file>:<line>` or `could not read claim <file>:<line>`, and that line appears
  in `REPORT.md` with `checker_error`, `gate_raised_exception` or `parse`. Fix
  that line of the claim file; the next run checks it again.
- If the whole run stops, the last lines of `log.txt` say why (for example
  "Unit tests failed"). Ask an agent to look at it; nothing in the research
  files is changed by a failed run.

## Opus sources on GitHub (the text pack)

The tracker reads the copy of `output/PER_CLAIM.json` that the GitHub run
commits. GitHub does not have the 207 MB Opus zip, so for sources held only by
Opus it would never see their text. To fix that, after agents add claims that
cite Opus sources, run this on the PC and commit the change in
`jobs/claim-checker/data/`:

```
python jobs/claim-checker/build_opus_index.py --text-pack
```

It writes `data/opus_text_pack.jsonl.gz`: the extracted text of only those Opus
sources that the claims cite (it refuses to write more than 20 MB), and
`data/opus_text_pack.json` (what went in). The GitHub run then checks those
quotations too. Without it, such quotations show `source_text_not_available`
on GitHub and the step stays unverified, even though a PC run may pass it; the
committed GitHub result is the one that counts.

`python jobs/claim-checker/build_opus_index.py` (no option) rebuilds
`data/opus_manifest_index.csv.gz`; needed only if the Opus release changes.

## How the readiness tracker could require "claim-checker passed"

Not done yet (the tracker is not changed by this job). To do it, in
`jobs/readiness-tracker/tracker.py`:

1. Add `"checker": "jobs/claim-checker/output/PER_CLAIM.json"` to `P` and load
   `by_instrument` (if the file is missing, treat every order as not checked).
2. In `from_claim(step)`, also require
   `checked = by_instrument.get(i)` with
   `checked["claim_sha256"] == claim_gate.claim_sha(claim)` (so a claim edited
   after the last check does not count) and
   `checked["steps_checker_passed"][step] is True`.
3. Add a blocker code such as `CLAIM_CHECK_FAILED:<step>` and a test.
4. Note: the tracker also calls `claim_gate.validate_claim` itself, so a claim
   with a wrongly typed value (for example `"scope_id": ["s1"]`) would stop the
   tracker too; it should catch that the way this checker does.

`steps_checker_passed[step]` is true only when that part of the claim is
present, every mechanical check on it passed (an unverifiable or too-short
item counts as not passed), its gate errors are clear, the gate did not crash,
and no claim-wide check failed (for example the order id itself is not in the
universe).

## What it does NOT establish

- Nothing legal. A pass means the sources are held, belong to the order, the
  quotations are word for word, the dates and order numbers are possible and
  the structure is complete. It does not mean the clause inventory is complete,
  the ending is right, the source is authentic, or the quotation is the
  operative one.
- It never changes a provisional status, a ledger or a count.
- `source_identity` relies on custody records and on the order number appearing
  in the text; it cannot tell a correct page from a wrong page of the same
  document, and it does not check that ending sources are the ending order.
- Quotations are checked against text extracted from the saved copy (pypdf for
  PDFs). A scan without a text layer cannot be checked (no OCR); a bad text
  layer can make a true quotation look "not found": the detail says how much
  matched, and a person decides.
- A quotation is searched in the whole document; `page_or_item` is not checked
  against the page where it was found (the detail reports the page).
- Cited order numbers are found by pattern. Unnumbered orders cited by date,
  and unusual spellings, are not checked.

