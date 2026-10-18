# Text acquisition for orders 5076–7531

This producer holds attributed texts for the fixed 1,712 previously all-no
orders in `data/TARGETS.json`. It continues the existing HathiTrust inventory
through independent, permitted sources. The route plan and human actions are
in `research/orders-1929-1936/`. `output/SUMMARY.json` gives current counts;
`RESULTS.csv` accounts for every target, and `MISSING.csv` lists the remainder.
These are text-acquisition results, with no legal-status conclusions.

## Sources and representation

- Internet Archive's unrestricted two-volume 1974 GPO Hoover compilation:
  reuse `early-orders-hunt.hunt.fetch_copy`, edition checks, published checksum,
  DjVu XML parser and printed-page mapper. Dated captions or exact closing
  numbers identify orders. Bottom folios are supplied to the unchanged mapper.
- GovInfo's 1936 Federal Register daily issues: reuse `fr-originals` and its
  `source-ladder.fr_pages` locator/filing-end checks. Page context is retained.
- Wikimedia Commons' eight independent GPO DjVu scans: follow the public file
  page's Original file offer and government-work notice. They lack embedded
  OCR, so render locally with DjVuLibre and read with Tesseract. Match signed
  order passages to exact closing numbers, preserving letter suffixes.
- Remaining routes inspect only missing identities. Finding aids, tables and
  abbreviated reprints are not saved as complete orders. Any Wikisource match
  on a standalone titled order uses the unchanged Wikisource identity helper
  and source-ladder extractor. Existing `Page:` transcriptions instead require
  their own order heading, exact closing number, dateline and contiguous
  source pages. Every page revision is retained; these are volunteer website
  transcriptions, including pages that have not been independently validated.

Every saved text is UTF-8/LF, with copy type, source and page in its header.
`SOURCES.jsonl` has singleton identity, original source-byte SHA-256, text hash,
page locator, source URL and copy type. `FRAGMENTS.jsonl` uses the established
producer schema so claim-kit discovers it without registration. Its historical
`kind: original_representation` schema field **does not certify originality**:
every record and nested declaration explicitly has
`acceptable_as_original: false`. No record is a signed-original authentication.

OCR spelling, broken Gothic headings, library stamps, page furniture and some
adjacent order context remain. Boundary methods and page-check flags are
recorded. A readable exact closing number can identify a passage even when
its Gothic heading is damaged; otherwise it stays missing. A saved text needs
comparison with its scan before supporting a substantive claim. Number hits
in `PAGE_CHECK_QUEUE.csv` are navigation leads only, never recovered texts.

## Reproduce or resume

Run commands explicitly from the repository root. Python 3.12 and `pypdf`
were used. Shared tools remain unchanged. Downloads are sequential, at least
two seconds apart, with longer robots delays honored. Challenges, throttling
and access denials stop that host; there is no login or bypass. APP's explicit
OpenAI exclusions and wildcard robots restrictions are enforced by the local
adapter. HathiTrust is excluded. No automatic `job.py` is installed because
the generic runner clears output, which would destroy the accumulated corpus.

```text
python jobs/hathi-gpo-orders/harvest.py --hoover
python jobs/hathi-gpo-orders/harvest.py --federal-register
python jobs/hathi-gpo-orders/setup_djvu.py
python jobs/hathi-gpo-orders/setup_ocr.py
python jobs/hathi-gpo-orders/commons_scan.py
python jobs/hathi-gpo-orders/supplementary_routes.py --route all
python jobs/hathi-gpo-orders/supplementary_routes.py --route followup
python jobs/hathi-gpo-orders/wikisource_residual.py
python jobs/hathi-gpo-orders/finish_report.py
python jobs/hathi-gpo-orders/wikisource_scan_pages.py
python jobs/hathi-gpo-orders/finish_report.py
```

Setup scripts confine vendor packages to ignored `.cache/`; package URLs,
hashes and engine versions are in `DECODER.json` and `OCR_ENGINE.json`.
This Windows run used DjVuLibre 3.5.30, Tesseract 5.5.3, tesserocr 2.11.0 and
the pinned `tessdata_fast` 4.1.0 English model. On other platforms, equivalent
native runtimes must be supplied; the Windows package bootstrap is not a
portable installer. Each downloaded GPO volume is held once in `output/books/`,
with its OCR page dump. Only FR issues that supplied saved texts are retained.
Network cache and commercial FDR book OCR are excluded from Git; no whole
commercial book is republished. `reextract_cached.py` performs the offline
boundary pass over existing government page dumps without new downloads.

The scripts skip saved identities. FR issue and Wikisource attempt logs also
avoid repeating completed checks. Do not rerun discovery or setup unnecessarily.
`ROUTE_ATTEMPTS.jsonl`, policy snapshots and `BLOCKED_HOSTS.json` preserve
access decisions. `EXTRACTION_FAILURES.jsonl` is historical and may mention an
order later recovered elsewhere; `FAILURES.jsonl` is the current unresolved set.
The original HathiTrust refusal is preserved in `HATHI_ACCESS_STOP.json` and
`VOLUME_FAILURES.jsonl`; it is not a failure of an independent copy.

## Files supplied by a person

Put lawful downloads in `incoming/`, copy `manifest.example.json` to
`manifest.json`, and replace its placeholders with the real URL and permission
note. The importer rejects example domains and files outside this job.

```text
python jobs/hathi-gpo-orders/import_local.py --folder jobs/hathi-gpo-orders/incoming
python jobs/hathi-gpo-orders/finish_report.py
```

Formats: `pdf` (text layer or local OCR), `djvu`, `djvu_xml`, `pages_jsonl`
(optionally gzip), `text` (form-feed page breaks), and `orders_jsonl`.
Each per-order JSONL row has `instrument_id`, `text`, `url`, `page_or_item`;
its text must contain the exact order number. For manually checked government
transcriptions set manifest `copy_kind` to
`human_verified_transcription_of_government_printed_copy`. All remain
unacceptable as authenticated originals. Keep supplied files while using
their source records; incoming files are ignored to avoid publishing material
without review. The importer itself makes no network requests.

## Verification

`finish_report.py` checks the exact 1,712-row partition, uniqueness, UTF-8/LF,
source/text hashes, held source artifacts, derivative flags and full read-only
claim-kit discovery. It checks the shared tools, census and status input bytes
against Git and the prior receipt, and compares claim-kit output before/after.
It writes only this producer's reports. It does not run the claim-kit job or
write into `jobs/claim-kit/output/`.
