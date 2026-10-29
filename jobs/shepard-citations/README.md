# Shepard: which later instruments cite each land and pre-1937 order

Named for Frank Shepard, whose citator (first published in 1873) listed every later court decision that cited a
given case. This job does the same for executive orders: for each target order it lists every later instrument
that cites it, the words printed near the citation ("revoked", "modified", "in lieu of" ...) and where the
citation was found. It costs no model tokens.

**Every row is a lead, not a finding.** A relation word printed near a citation says only that the word is printed
there. It does not establish that the citing instrument did what the word says, to that order, in whole, or on that
date. BLM's tables, the 1989 OFR table and Wikisource notes are editorial finding aids, and the order texts are
mostly OCR. Nothing here changes a provisional status, ledger, count or the codebook. Certified: 0.

## Why

The land probe of 2026-10-28 (`research/excavator/claude-land-probe-2026-10-28/`) found that, once the right index
is consulted, identifying the instrument that ended a land order takes about a minute. The indexes it used were the
1989 OFR disposition table, BLM's Public Land Order (PLO) tables, the Federal Register's daily "codification guide"
and a reverse scan of the held order texts. This job runs all four for every target order, so the
"finding later instruments" step needs no agent time.

## Targets

The target orders are the census orders typed by `jobs/x1-class-engine` (the pre-1937 orders, 8,014 rows), every
other census order dated 1936 or earlier, and census orders of 1937 to 1942 whose OFR title reads like a land order
(withdrawal, reservation, refuge, reserve, public land, national forest, range, restoration). Orders typed `land` by
X1, plus those 1937-1942 land titles, are the land targets counted in `SUMMARY.json`. The 1989 table, the BLM
tables and the codification guides are read for every census order they name, not only targets.

## Sources and evidence types

| `evidence_type` | Source | What is read |
|---|---|---|
| `shepard_ofr1989_table` | `jobs/ofr-codification-1989/output/DISPOSITION_1989.csv` | Rows naming an ending or amending instrument that `ofr-codification-1989` does not already emit: PLOs ("Revoked by PLO 4620"), the amendments column ("Amended by EOs 8536, 9787", "Modified by", "Continued by" and the active "Amended EO 2932"), and the "Revokes ..." direction. |
| `shepard_blm_plo_table` | BLM "Table of Public Land Orders", 24 PDFs, PLOs 1-7898, downloaded each run (`blm.py`) | Each PLO's row: number, signature date, subject heading and FR citation. Within the subject: orders cited by number ("revoking EO No. 5214 of Oct. 30, 1929"), by date ("Partial Revocation to Executive Order Dated April 17, 1926"), by reserve number ("powersite reserve No. 26"), and other PLOs ("Amended by PLO No. 956", "see PLO Nos. 195, 379"). The relation word is the nearest one before the citation in the same ";" clause. "Amended by PLO No. 956" makes PLO 956 the actor. |
| `shepard_text_number` | Held order texts (every text behind the fragment files listed in `jobs/_lib/eo_identity.py`) | "Executive Order No. 6910", "EO Nos. 1, 2 and 3", "The Executive Order (No. 1237) of August 15, 1910". |
| `shepard_text_date` | Same texts | "Executive order of June 6, 1906", "Executive orders dated November 9, 1907, and January 28, 1908", spelled-out dates. Used only when the date maps to exactly one census order and to no unnumbered census cluster (`jobs/census-completeness`). Unnumbered orders outside the census may share the date, so every such row is flagged. |
| `shepard_text_reserve` | Same texts | "Power Site Reserve No. 325", "Public Water Reserve No. 155", reservoir-site, stock-driveway, air-navigation-site, naval petroleum and similar reserves. The reserve is resolved to the earliest-dated target order whose own text (first 4,000 characters) or index title names it (`RESERVE_INDEX.csv`). That is an inference, flagged `reserve_creator_inferred`. |
| `shepard_wikisource_note` | Wikisource pages held by `wikisource-texts` | The editorial "Notes" section: "Amends", "Amended by", "Revoked by", "Revokes (in part)", "Superseded by", "See Related". "See Related" has no direction; the later of the two orders is taken as the citing one. |
| `shepard_fr_contents` | Federal Register issue texts already held by `source-ladder` and `fr-originals` (the source ladder extracts PDF pages 1-6, which hold the codification guide) | Entries such as "4872 (revoked by PLO 4620) ..... 6689" under "Chapter II (Executive orders)" or "Appendix (Public land orders)". The page number after the entry, or the PLO's own entry ("949 ______ 1807"), gives the FR page that prints the acting instrument; these pages also go into `PLO_TABLE.csv` (`fr_contents_pages`). |

How a relation word is chosen in order texts: a word printed right before the citation wins ("in lieu of Executive
Order No. 1304", "Revocation of Executive Order No. 4810"); then a word after it introduced by "hereby" ("... is
hereby revoked"); then the nearest word before it, then after it, in the same sentence. When the sentence has none,
the next "hereby <verb>" within 4,000 characters is used if no other order is cited in between (long land
descriptions separate the citation from the verb), flagged `relation_word_far_after_citation`. A citation after
"as amended by" names an earlier amender, not a target; it is kept as `cross_reference` and flagged. "In part",
"partial", "insofar as" set `qualifier` to "in part". Negations ("shall not revoke", "nothing in this order") are
flagged `negation_in_sentence`. With no relation word the mechanism is `cross_reference`.

Safeguards against false citations: an order never cites itself; a citing order dated before the target, or with a
lower number than the target, is skipped (numbers run in date order, so these are almost always a neighbouring
document on the same printed page); Federal Register page texts are cut to the citing order's own span, from its
heading or closing tag "[No. 7532]" to the filing line "[F. R. Doc. ...]" (with `source-ladder/fr_pages.py`), and
flagged when the span cannot be found; Wikisource navigation ("Executive Order 708 / Executive Order 710") is cut
away.

De-duplication: a row is not written when `jobs/later-events/output/EDGES.csv` or
`jobs/ofr-codification-1989/output/FRAGMENTS.jsonl` already has the same acting instrument, target and mechanism
(`SUMMARY.json` counts these under `skipped_already_in_later_events_or_codification`). The same citation found
again in the same source raises `occurrences=N` in `date_flags` instead of adding a row.

## Outputs (`output/`)

| File | Contents |
|---|---|
| `EDGES.csv` | One row per citation lead, in the column layout of `jobs/later-events/output/EDGES.csv`, so `jobs/claim-kit/inputs.py` reads it automatically (it reads `target_id` and `acting_id`). `note_label` holds the citation form and relation words; `date_flags` holds the flags; `date_candidate` is the acting instrument's signing date (PLOs: the BLM table's signature date), never an effective date. |
| `PLO_TABLE.csv` | One row per PLO in the BLM tables: number, signature date, FR citation (volume and page), subject heading, the orders it cites with dates and relation words (`eo_refs`, e.g. `EO:5214@1929-10-30=revocation`), date phrases that did not resolve, other PLOs and reserves cited, the FR pages named by held codification guides, the source PDF, its sha256 and the PDF page. `jobs/fr-pages` reads it to turn a PLO number into an FR citation. |
| `RESERVE_INDEX.csv` | Each reserve number seen in a target order's own text or title, the candidate creating orders and the one chosen (or why none was). |
| `UNRESOLVED.csv` | Date citations that matched no single census order (with the reason and candidates), capped at 20,000 rows. |
| `SOURCES.jsonl` | One record per BLM table PDF (url, sha256, bytes, `text_path`, `cache_path` when the PDF is committed). `instrument_ids` is empty on purpose: a table is a finding aid for many orders, never an order's text. |
| `texts/blm/plo_<range>.txt` | The text layer of each BLM PDF, with "=== PDF page N of M ===" markers. |
| `blm/plo_<range>.pdf` | The PDF itself when it is at most `BLM_COMMIT_MAX_BYTES` (default 2,000,000). |
| `SUMMARY.json` | Counts by evidence type and mechanism, targets and land targets with any lead or an ending lead, skips, BLM fetch status, and `probe_check_30_orders`: the ending leads found for the 30 land-probe orders. |

## Running

On GitHub: change anything in this folder, or Actions -> Run jobs -> `shepard-citations`. It also runs after the
producers in `after.txt` and when the census changes (`triggers.txt`). The unit tests run first and the job stops if
one fails. Web requests: robots.txt and the listing page of blm.gov plus the 24 PDFs, at most `JOB_MAX_REQUESTS`
(default 60), one at a time, 1.5 seconds apart; PDFs are cached under `JOB_CACHE_DIR` (`CACHE_MB` 128), so a rerun
fetches only robots.txt and the listing page. If a PDF cannot be downloaded, the previous run's text is carried
forward and flagged. When no BLM table at all can be read or carried forward, the run fails if a previous
`PLO_TABLE.csv` had rows (so the runner keeps it); on a first run the other sources' leads are still published.

Locally, from the repo root:

```
python -m pip install --user pypdf==6.20.1
REPO_ROOT=. OUTPUT_DIR=/tmp/shepard/out JOB_CACHE_DIR=/tmp/shepard/cache python jobs/shepard-citations/job.py
```

`SHEPARD_OFFLINE=1` makes no web request (BLM tables then come only from `JOB_PRIOR_OUTPUT_DIR`);
`SHEPARD_TEXT_LIMIT=500` scans only 500 held texts. Tests alone: `python -I -m unittest -v test_shepard` in this
folder. The fixtures in `fixtures/` are short reconstructions of the BLM table layout (from WebFetch excerpts), a
held codification-guide excerpt and a Wikisource page excerpt; they are test data, not sources.

Build notes, what was verified about each source, sizes and open risks: `BUILD_NOTES.md`.
