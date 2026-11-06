# Selden FR citers: later Federal Register documents that act on an order, 1994 on

Named for John Selden (1584-1654), who went back to the records for the actual texts of statutes and precedents.
This job holds the **official text of later instruments that act on an order** and locates the sentence that does
it, so a claim can quote that sentence and the claim checker can verify it. It costs no model tokens.

For every census order whose ending/current-basis or counterevidence step is open (orders whose own official text
and status are held go first, newest first), it searches the Federal Register's full text (federalregister.gov API
v1, which covers 1994 on) for `"Executive Order N"` between the order's publication and the legal cutoff
(2026-10-14), reads each hit's full text, and finds every sentence that prints the order's number with
`jobs/shepard-citations/cites.py` (citation forms, relation words, sentence bounds), through
`jobs/selden-common/selden_common.py`. A sentence acts on the order when an ending or modifying word governs the
citation, it is not negated, and the order is not the one printed as acting ("as amended by Executive Order N").

## What is kept

The text of each citing document that is a presidential document, prints an acting word near the citation, or is
the newest agency document citing the order, up to 400 KB a document and `SELDEN_COMMIT_BYTES` (120 MB) a run. The
kept bytes are exactly the bytes fetched; `sha256` and `cache_path` in `SOURCES.jsonl` let the claim checker
re-hash them (`held_bytes_verified`). `instrument_ids` lists the acting instrument first, then the target orders,
so a citing document never reads as an order's own text.

## Outputs

| File | Contents |
|---|---|
| `SOURCES.jsonl` | Kept document texts (shared source format). Grade `fr_document_full_text`: federalregister.gov's full text built from GPO's XML; the govinfo PDF named in `pdf_url` is the official edition. |
| `FRAGMENTS.jsonl` | `later_event_candidates`, one per (order, kept citing document): `acting_id` (census EO when the document is one, else `FRDOC:<number>`), `mechanism` (the printed relation if it acts on the order, else `cross_reference`), exact `quote` and `quote_span` (character offsets into the kept text), `citation_span`, `date_matches_target`, flags. |
| `CITATIONS.csv` | Every located citation, kept or not. |
| `SEARCHES.jsonl` | One bounded search record per order: query URLs, window, hits, documents examined, documents citing, documents acting. `complete` is false when hits exceeded the per-order cap (40). |
| `CONTROLS.json` | Planted controls (below). |
| `STATE.json` | Orders already searched; the next run continues with the rest. |

## Planted controls, every run

Positives: up to 80 pairs in which OFR's editorial notes (`jobs/later-events`, not the full-text route) say a 1994
or later order revoked, superseded or amended an earlier census order. The locator must find a sentence citing the
target in the acting order's own text. Negatives: in each positive text, near-miss numbers the text does not print
(the number less its last digit, with a digit appended, plus one) and another positive's target that the text does
not print. Any negative located fails the run's controls, and then every fragment is written as `cross_reference`.

## Limits

Leads only. A printed relation word near a citation says the word is printed there; whether the instrument ended
the order, in whole, and when, is a legal reading for the claim. Full-text search starts in 1994: older citers come
from `jobs/selden-fr-acting` and the other finding jobs. An order cited only by date or by a title is not found. No
status, census, codebook or count changes. Certified: 0.

**Registration.** `jobs/claim-kit/inputs.py` discovers every `jobs/*/output/FRAGMENTS*.jsonl` and `SOURCES.jsonl`,
so merging this job's output to `main` registers it with the claim kit and, through it, the readiness tracker. That
can change counts and waits for the owner's merge.

## Running

On a push to this folder, daily (`DAILY`), and after `readiness-tracker` and `later-events`. Budget per run:
`JOB_MAX_REQUESTS` (12,000), `JOB_TIME_BUDGET_MIN` (100), `JOB_WORKERS` (4; at most 4 requests in flight to the
Federal Register, 0.2 s apart, robots.txt obeyed). Tests (`test_citers.py`, offline) run first.
