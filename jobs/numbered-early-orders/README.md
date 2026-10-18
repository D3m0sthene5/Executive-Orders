# Numbered early orders: printed texts of the undecided orders 1-5075 (1862-1929)

3,324 undecided numbered orders below 5076 have nothing on file (`research/gap-census/census.csv`, every
evidence column `no`; lettered and half orders count by their number). `data/TARGETS.csv` lists them with
the WPA 1944 numbered list's date and summary (`build_targets.py`; hashes in `data/PROVENANCE.json`).

`numbered.py` reads every page of each book and looks for the targets:

- by number: `Executive Order No. 2029`, `E. O. 1234-A`, and the War Department books' `(No. 2275)` after
  "Executive order of ...";
- by date and subject: the exact date as printed (`June 3, 1922`, `23 February, 1916`, `3d day of June`)
  with summary words nearby: two words including a name, three words uncommon in that book, or one rare
  long name. Run-together words in the WPA OCR (`restrictionagainst`) are split against the book's own
  vocabulary.

A hit preceded by "amending", "revoking", "under the provisions of" and the like is another order citing
the target: it goes to `MENTIONS.csv`, not to `texts/`. Several orders of one date claiming one passage
keep only those with the most words, marked `shared_with`.

Books: first what the project already holds (early-orders-hunt's GLO and MR books, the 1912 Indian
reservation and 1911 Isthmian Canal compilations, Richardson VI/VII/IX), then `data/BOOKS.json` in rank
order, one Internet Archive item at a time. Fetching uses early-orders-hunt's code by import, unchanged;
`fetch_copy` here is a copy of its fetcher that refuses lending (access-restricted) copies and reads the
Archive's hOCR search text when the DjVu XML is over 60 MB. HathiTrust is not fetched (bot challenge).

Outputs (`output/`): `texts/` (header, then `----- EXACT SLICE -----`, then page OCR unchanged),
`FRAGMENTS.jsonl` and `SOURCES.jsonl` in jobs/wikisource-texts' shape (grade `government_printed_copy`,
flagged a compiled transcription, `acceptable_as_original=false`, book URL, image, printed page, line span,
hashes), `FOUND.csv`, `NOT_FOUND.csv` with a reason per order, `MENTIONS.csv`, `BOOKS.csv`, `FETCHES.csv`,
`FAILURES.csv`, `SUMMARY.json`.

Nothing here admits an order, decides a status or authenticates a text. A printed copy is never the signed
original; a date-and-subject hit is a machine match to be read against the scan.

Knobs: `NEO_MAX_BOOKS` (40), `NEO_MAX_REQUESTS` (200), `NEO_BOOKS=KAPPLER_IV,...`, `NEO_OFFLINE=1`,
`JOB_CACHE_DIR`. Tests: `python -m unittest -v test_numbered` (offline).

## Status (2026-10-18, local run, stopped early)

Not run on GitHub; no output committed. Held books plus the first five new books gave 80 orders: 41 in
held books (MR 1916 37, MR 1910 2, Richardson IX 2, IR 1912 1), 39 more from Kappler IV (26) and four
Official U.S. Bulletin volumes (13). That is under the 300 stop line, so fetching stopped. Bulletin vol. 1
failed on an Archive HTTP 500. Ranking estimates and what was seen are in HANDOFF/notes-claude.md.
