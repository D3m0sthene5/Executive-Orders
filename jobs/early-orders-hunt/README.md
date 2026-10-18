# Early orders hunt: getting the printed texts of 18th- and 19th-century orders

Before the numbered series begins in 1862 there is no Federal Register, no disposition table and no
official list. The one census is Clifford Lord's 1943 *List and Index of Presidential Executive Orders,
Unnumbered Series*, and for most of its 1789–1899 entries it says where the order's text was printed:

| Lord writes | Meaning | Copy this job reads |
|---|---|---|
| `X Richardson App. 83` | Richardson, *Messages and Papers of the Presidents* (GPO 1896–99), vol. X, appendix p. 83 | Internet Archive, University of Toronto scan of the GPO edition |
| `1898 MR 23` | War Department, *Military Reservations, National Military Parks, and National Cemeteries* (GPO 1898), p. 23; also the 1907, 1910 and 1916 editions | Internet Archive |
| `1880 GLO 53` | *Annual Report of the Commissioner of the General Land Office* for 1880, p. 53 | Internet Archive, one volume per report year |

Among Lord's 198 pre-1862 entries, 85 cite a GLO report, 43 a reservation book and 17 Richardson; for
1789–1899 as a whole there are about 600 GLO, 200 MR and 70 Richardson citations. The job:

1. **Reads the leads.** Lord's entries (the `wpa-lists` job's parse, or the committed pre-1900 subset in
   `data/lord_subset/` when that branch is not merged), the 1,023 OCR date markers from the Library of
   Congress scan of Lord (`research/stage14/LORD`), and the six curated 1789–1862 candidates from Stage 18.
2. **Parses every citation** into a normalised record: Richardson volume/appendix/page, MR year/page,
   GLO year/page, Statutes at Large, Annals of Congress, American State Papers, Kappler, Sparks,
   congressional documents and newspapers. Sources without a fetchable book get a route URL.
3. **Fetches each cited book once** from the Internet Archive, ranked by how many leads it unlocks (a
   pre-1862 lead counts three times): item metadata, then the page-level OCR (`_djvu.xml`), whose sha1 is
   checked against the checksum the Archive publishes. The item's title, publisher and date are checked
   against the edition Lord cites, because the Bureau of National Literature reprints of Richardson are
   repaginated. For a GLO report the title page is read for the report year. A copy with fewer than
   `min_pages` scanned pages (default 150) is passed over for the next alternate in the registry, since
   an 84-page extract is not the 500-page report Lord cited; every copy tried is recorded. Richardson
   VI, VII and IX are taken from `jobs/richardson-volumes/data/` instead of being downloaded again.
4. **Maps printed pages to scanned images** from the running heads (`84 Messages and Papers of the
   Presidents`, `Appendix 83`, `MILITARY RESERVATIONS, ETC. 27`), using the locally most common offset so
   an OCR misread does not shift the map, and reports how many heads agree.
5. **Cuts the order's passage** from the cited page (or its neighbours): it looks for the lead's date in
   its printed forms (`October 6, 1789`, `6th day of October, A. D. 1789`) and for the subject words of
   Lord's summary, grades the hit, and saves the exact slice with the book, image, page, line span,
   source URL and hash in `texts/`.
6. **Searches the Library of Congress catalog** for pre-1862 leads that have a day-precise date but no
   book text: Chronicling America (newspapers printed orders and "by command of the President" notices)
   within three weeks of the date, and the president's digitized papers for that year. Responses are
   saved by hash. Searches are bounded (`HUNT_LIVE_ROUTES`, default 24) and respect `robots.txt`
   (loc.gov asks for a five-second delay, which the shared fetch pool honours).

It costs no model tokens. All downloads go through `jobs/_lib/fetch_pool.py` (robots, per-host limits,
byte bounds, hashed cache under `JOB_CACHE_DIR`, 2 GiB cap).

## What comes out

| File | Contents |
|---|---|
| `LEADS.csv` | Every lead with date, precision, summary, citation kinds and how many texts were cut for it |
| `CITATIONS.csv` | Every parsed citation, with book key and page or a route URL |
| `BOOKS.csv`, `books/<key>.json` | Per book: status, Archive identifier, edition check, sha1 check, page-map agreement, custody |
| `books/<key>_pages.jsonl.gz` | Every page of a fetched book: image number, section, printed page, text. Same shape as `jobs/richardson-volumes/data/*_pages.jsonl`, so a Richardson volume can be slotted into that job with one `PROVENANCE.json` entry |
| `RESOLVED.csv` | Every book citation: image found, grade, keyword hits, text file |
| `texts/<lead>__<book>_p<page>.txt` | The cut passage, header then `----- EXACT SLICE -----` then the OCR text unchanged |
| `LIVE_ROUTES.csv`, `LIVE_HITS.csv`, `responses/` | Catalog searches run, their saved responses, and the records they returned |
| `SUMMARY.json`, `REPORT.md` | Counts and the table of pre-1862 texts cut |

Grades: `page_date_and_subject` (the page carries the lead's date and its subject words),
`page_and_date`, `page_and_subject`, `page_only` (page found, nothing read on it; the slice is the page
head and needs an eye), `page_not_mapped`, `book_not_held`.

## What it does not do

- It does not admit anything to the census, assign a date, merge identities or change any status. A
  printed compilation is a transcription lead for the `original_text` step, never the signed original
  (Richardson copied department records and newspapers; the GLO and MR books summarise orders and often
  quote only their operative words). A page hit is not an identity: signer, capacity and inclusion
  under the codebook stay with the reviewer.
- A search with no results proves nothing and is never written to `EXHAUSTED.jsonl`.
- It does not download the PDFs (35–90 MB each). `books/<key>.json` records the Archive's PDF URL, size
  and sha1 so the owner can add a volume to `releases/source_books/` under Git LFS when wanted.

## Running

On GitHub: Actions → Run jobs → `early-orders-hunt`. Locally:

```sh
OUTPUT_DIR=/tmp/hunt REPO_ROOT=. python jobs/early-orders-hunt/job.py
```

Knobs: `HUNT_MAX_REQUESTS` (160), `HUNT_MAX_BOOKS` (12 per run; the cache carries fetched books to the
next run), `HUNT_BOOKS=RICH_X,MR_1898` (restrict), `HUNT_LIVE_ROUTES` (24; 0 disables), `HUNT_YEAR_MAX`
(1899), `HUNT_OFFLINE=1`. Tests: `python -m unittest -v jobs/early-orders-hunt/test_hunt.py` (offline;
a fake Archive serves a synthetic book).

**Measured 2026-10-18, first live run from the owner's PC** (6 books, 327 s, 120 MB downloaded, 26
requests): 1,994 leads (320 before 1862); 6,744 citations parsed (4,775 GLO, 1,050 MR, 436 Richardson,
338 Kappler, 131 Statutes at Large); every fetched book's page text matched the Archive's sha1 and its
edition check; running heads agreed with the page map on 93–100 % of readable pages; 2,261 citations
resolved to a page, 1,594 of them with the lead's date and subject on it; **950 leads got a text, 125
of them before 1862.** Twelve Library of Congress searches ran for 1789–1790 leads and returned, among
others, the June 13 and June 20, 1789 issues of the *Gazette of the United-States* for the June 8, 1789
departmental request. Not a measure of orders found: a slice must be read against the scan before use.

## Adding a book

Put its Internet Archive identifier in `data/BOOKS.json` under the key Lord's citation form implies
(`GLO_1886`, `RICH_VIII`). A book with `"ia_identifier": null` gets a bounded Archive search and its
candidates are listed in `books/<key>.json` for a person to choose from; confirm the candidate is the
GPO edition before using it.
