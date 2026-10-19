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

## Status (2026-10-18, local run before the first GitHub run)

184 of the 3,324 orders got a text (197 texts): 41 from books the project already held (MR 1916 37,
MR 1910 2, Richardson IX 2, IR 1912 1) and 143 more from new books: Civil Service Commission reports
95 (FY 1914, 1915, 1918, 1922), Kappler IV 26, Official U.S. Bulletin 17, Panama Canal 1921 6.
Kappler III gave none. The 1975 reprint of the Indian-reservation volumes is a lending copy and was not
downloaded. 3,140 orders still have no text; NOT_FOUND.csv gives the reason for each. 30 requests,
47 seconds.

Most of the rest are minor 1908-29 orders (civil-service waivers, national-forest and land-withdrawal
orders). The Civil Service reports print the waivers in full, but the Internet Archive holds only four
of the 1908-29 years; HathiTrust holds the run but is not fetched. One known false positive: EO 860
matched on a later order quoting "Executive Order No. 860 of June 30, 1908".

The Civil Service reports head each order with its date, and the OCR often garbles the year ("August 3,
1022"). For books with a `years` field the job also accepts month and day plus two summary names
(`monthday_and_names`).
