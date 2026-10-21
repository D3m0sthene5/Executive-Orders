# Pinakes: wiring the ProQuest PDFs in

Named for Callimachus's Pinakes, the catalogue of the Library of Alexandria. This job takes every PDF the owner
uploaded from ProQuest Congressional (the "Replica of Original" scans of pre-1937 orders) and does, by machine, the
work of making them part of the project: it verifies each file, chooses one file per order, gets a text for it, and
writes the records the other jobs read. No agent reads a PDF; no tokens are spent per order.

It reads both ProQuest folders: the upload at the repo root, `ProQuest Pre-1937 Orders/`, and the research folder
`research/pre-1937-sources/ProQuest Pre-1937 Orders/`. File names are read as `[PT1-]<year>-EO-<number>[-<letter>]
[_From_<a>_to_<b>][ (<n>)].pdf`; Chrome's ` (1)` copies are recognized as duplicates by SHA-256 and the plain copy
is chosen. Files whose names are not accessions, or that are not PDFs, are listed in `STRAY_FILES.csv` and left alone.

## Text

A PDF's own text layer is used when it is usable: at least 80 characters, mostly word-shaped tokens, and at least
40% common English or order vocabulary. Otherwise the pages are rendered with `pdftoppm` and read with `tesseract`
(installed by `job.sh` on the runner). OCR is bounded per run (`JOB_OCR_PAGES`, default 4,000 pages) and resumes:
texts already produced for the same PDF bytes are carried forward from the last committed output, so the backlog
shrinks every run until every order has a text. OCR of a handwritten original gives word-shaped nonsense; the same
quality screen flags it (`text_usable: no`) rather than hiding it, and `REPORT.md` counts them.

## Outputs (`output/`)

| File | What it is |
|---|---|
| `INVENTORY.csv` | Every file: parsed year/number/suffix, bytes, SHA-256, `%PDF-` signature, pages, text-layer size and quality, duplicate-of, page range in the name. |
| `ORDERS.csv` | One row per order: the chosen file, hash, pages, copies, `text_source` (`layer`, `ocr`, `none`), text path, text SHA-256, length, quality, usability, OCR pages or error, signing date and title from the project's indexes, whether the owner's link list has it, the accession URL. |
| `texts/EO_<n>.txt` | The text, one file per order. Clark harvests these; Lewis routes on them. |
| `FRAGMENTS.jsonl` | One project fragment per order, `produced_by: pinakes-proquest-ingest`, grade `archival_replica_scan_pending_codebook`, `acceptable_as_original: false`, `needs_page_check: true`. |
| `SUPPLIED_LINKS_RECONCILED.csv`, `MISSING_FROM_UPLOAD.csv` | The owner's 2,765-link list against the files: which orders now have a PDF and which are still missing. |
| `STRAY_FILES.csv` | Files left alone: non-accession names, non-PDF bytes (an "Access is denied" page saved as .pdf, say). |
| `PROGRESS_EVENTS.jsonl` | `verified_repository` events in the acquisition folder's audit format, for the owner to append to `_resume/progress.jsonl` if wanted. |
| `REPORT.md`, `SUMMARY.json` | Counts. |

## What it wires into

- **The readiness tracker** reads `FRAGMENTS.jsonl` as a new lead class: an order with a replica scan and no counted
  original gets the blocker `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` and the shared-unlock action "compare the pages
  and decide the custody grade". A replica scan never counts as the original here; letting one count after a page
  check is a codebook decision for the owner and would be one more rule in `tracker.py`.
- **Lewis** (`jobs/lewis-originals`) takes `ORDERS.csv` as the ProQuest authority: every order with a verified PDF is
  routed `proquest_local` / `file_verified_pages_unchecked`.
- **Clark** (`jobs/clark-discovery`) reads the texts through the shared fragment loader and harvests every order
  number they cite.
- **Domesday** (`jobs/domesday-register`) shows the file, hash, text source and usability per order.

## Running

Daily, and whenever either ProQuest folder changes. `job.sh` installs tesseract and poppler, then `job.py` runs
`test_ingest.py` (synthetic PDFs, a fake OCR function) and the ingest. Locally, with tesseract and pdftoppm installed:

```sh
REPO_ROOT=. OUTPUT_DIR=/tmp/pinakes JOB_OCR_PAGES=200 python jobs/pinakes-proquest-ingest/job.py
```
