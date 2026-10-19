# app-footnote-leads: American Presidency Project footnotes as structured leads

The American Presidency Project (APP) prints an editorial footnote under many order pages: the Federal
Register publication note ("This Executive order was published in the Federal Register on April 26"),
press-release and release-place notes, source citations (Kappler), and occasionally a note that a later
order amended or revoked this one. `jobs/app-executive-orders/` keeps each page's footnote in
`DOCUMENTS.jsonl` (live pages) and `MIRROR_DOCUMENTS.jsonl` (web-archive captures). This job splits every
footnote into sentences and types each one. It reads only `jobs/`, never edits `jobs/app-executive-orders/`
and makes no network request.

| note_type | Meaning |
| --- | --- |
| `fr_citation` | A Federal Register publication note about this order: a publication date (`fr_publication_date_inferred` adds the year from the order's own date: the first such day on or after signing), an announced future publication, a note that its annexes or schedules are printed in the FR, or a bare `3 FR 547` citation. An FR citation sitting next to another order's number is that order's citation and is not typed here. |
| `not_published` | The note says the order was not printed or filed in the Federal Register, plus the 47 archive captures with no text at all (`MIRROR_FAILURES.jsonl`, reason `no_usable_text`), which app-executive-orders reports as APP "[Not Published.]" pages; the marker itself is not stored, as the row says. The Weekly Compilation timing note "not filed with the Office of the Federal Register before the cutoff time of this issue" is **not** this type (it is `other`, `weekly_compilation_timing`). |
| `revoked_by`, `amended_by`, `superseded_by` | The note says another order revoked (or rescinded), amended (or modified) or superseded this order; `referenced_eo` lists the acting orders. A note in which this order is the actor ("the orders revoked by Executive Order 11408" on EO 11408's page), or which is about another order, is `other`. |
| `other` | Everything else, with `detail`: `press_release`, `release_place`, `source_citation`, `cross_reference`, `weekly_compilation_timing`, `list_or_table_item`, `app_editorial_note`, `unclassified`. |

## Outputs

| File | What it is |
| --- | --- |
| `FOOTNOTE_LEADS.csv` / `.jsonl` | One row per sentence and note type: instrument_id, APP path and node, note_type, detail, referenced EO numbers, FR volume/page, publication date text and inferred date, the sentence, the raw note, the lanes (live / archive capture) that carry the same note, page sha256, URL. |
| `EDGES.csv` | The revoked/amended/superseded rows as acting order -> this order, in `jobs/later-events/output/EDGES.csv`'s column shape, `evidence_type` `app_footnote_on_target`, flagged `app_editorial_note_not_ofr;lead_only_never_an_ending`. claim-kit reads every job's `output/EDGES.csv` as target/actor pairs. |
| `SUMMARY.json` | Counts by type and detail. |

EO numbers are read with later-events' own `eo_references`, so lists, ranges and letter suffixes normalise
the same way there and here.

## Why this does not go into later-events directly

later-events reads two kinds of evidence: the OFR catalog's disposition notes (fetched from the OFR API) and
order texts (other jobs' `SOURCES.jsonl`), which it scans for the acting order's own words ("Executive Order
No. 9876 is hereby revoked"). An APP footnote is neither: it is a third party's note about the order on whose
page it sits, so passing it as an order text would attribute the note to the wrong order, and passing it as an
OFR note would mislabel its source. Its four edges are therefore published here in later-events' output
shape. The APP order texts themselves do reach later-events, through `jobs/app-transcriptions/output/SOURCES.jsonl`.

## What it does not establish

Footnotes are editorial notes on a secondary transcription. A row is a lead: never an ending, an effective
date, a status finding, or proof that an order was or was not published. Nothing here changes a census,
ledger, codebook or count.

## Running

`REPO_ROOT=. OUTPUT_DIR=jobs/app-footnote-leads/output python jobs/app-footnote-leads/job.py` (about 2 s, after
`test_footnotes.py`, which checks 15 real footnotes copied verbatim).
