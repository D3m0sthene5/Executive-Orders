# csc-annual-reports

Recovers order texts for gap executive orders that the WPA/Lord numbered list (1944) says were printed in
the **Annual Report of the United States Civil Service Commission** ("1917 CSR 121" = the report for the
fiscal year ended June 30, 1917, page 121). The reports are House Documents in the Congressional Serial
Set, which GovInfo serves publicly as scanned PDFs with an OCR text layer.

Targets: 840 ids from `research/pre-1937-sources/GAP_ROUTES.csv` (`wpa_route = csc_report`). They are the
gap orders with no saved text and no other public source found. Inputs are vendored in `data/`:

- `CITATIONS.csv`: the WPA entries for those ids (date, subject hint, citations, summary).
- `REPORTS.json`: Serial Set package ids for the annual reports, from the GovInfo search API on
  2026-10-19. Title years can be wrong (two packages are titled FY 1915), so the job reads the fiscal year
  from each report's title page.
- `PROVENANCE.json`: where both came from, with sha256s.

## Method

1. Fetch each report whose title year is within one year of a cited year, with `jobs/_lib/fetch_pool.py`
   (robots, three at a time, sha256 custody).
2. Read the PDF text layer. Map printed page numbers to PDF pages from the running heads, filling gaps
   from the nearest consistent offset.
3. For each citation, look for the order's WPA date as a date line on the cited page, then the pages
   around it. Cut from that line to the next date line or heading, running onto the next page if needed.
   An exact date on the cited page is `high`. A neighbouring page or an OCR-damaged year is `medium`.
   Orders sharing a date on one page are paired in number order (`medium`) or picked by overlap with the
   WPA summary (`low`). A date found only inline is `low`.
4. Write `texts/EO_<n>.txt`, `FRAGMENTS.jsonl` (grade `compiled_transcription_lead`,
   `acceptable_as_original: false`, `needs_page_check: true`), `CITATION_RESULTS.csv` (every citation,
   including the ones not found and why), `REPORTS_FETCHED.csv` and `SUMMARY.json`.

An offline trial on the FY 1917 report located 67 of its 68 cited gap orders (54 high, 10 medium, 3 low).
The texts were full orders, not abstracts, but the WPA warns that some reports give only abstracts.

## Limits

- Location leads only. A report printing is not the original order, and the WPA date is a lead, not a
  verified signing date. Nothing here changes the census, ledger, codebook or any status.
- "CSA" citations (Civil Service Act and Rules pamphlets) are not covered; those pamphlets are not in the
  Serial Set.
- No report is listed for FY 1904, and the FY 1916 report may be one of the two packages titled 1915.
  `SUMMARY.json` lists cited years that no fetched report covers.
- A failed download is recorded in `REPORTS_FETCHED.csv`; it is never evidence that an order is absent.

`CSC_MAX_REPORTS=<n>` limits a trial run to the first n packages. Tests: `python -I test_csc.py`.
