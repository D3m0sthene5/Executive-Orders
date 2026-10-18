# OFR compilations: official texts of orders from before the Federal Register

In 1974 the Office of the Federal Register published, through GPO, *Proclamations and Executive
Orders* volumes that print the **full text** of every numbered order of an administration from
before the Federal Register began in 1936. The Federal Register index that `jobs/fr-originals`
uses starts in 1937, so it can't reach these orders. This job turns each volume into one text
per order, with exact dates and page citations, and compares the result with the census.

It costs no model tokens and makes no web requests.

## Volumes

| Volume | Covers | Pages |
|---|---|---|
| *Proclamations and Executive Orders: Herbert Hoover, March 4, 1929 to March 4, 1933*, **vol. II** (OFR / GPO 1974; Google scan of the University of California copy, HathiTrust `2027/uc1.c025504761`) | Full texts of EO 5550–6070 (Feb 1931 – Mar 1933); Table 2 lists all of Hoover's EOs 5076–6070 | 801 |

The PDF is kept under Git LFS in `releases/source_books/`. Its text layer is committed in
`data/hoover_v2_pages.jsonl`, with both sha256 values in `data/PROVENANCE.json`, so the job never
needs the PDF itself. When the PDF has been pulled, the job checks its hash too. Volume I (EO
5076–5549 and the proclamations) is not here yet. Adding another volume means adding its PDF,
its text layer and one entry in `PROVENANCE.json`.

## How an order is found

1. Each page loses its running head ("Herbert Hoover, 1929-1933 EO 5550", "EO 5551 Executive Orders") and its printed page number. The page number is kept for citations.
2. An order starts at its heading, "Executive Order 5550. February 6, 1931". The OCR sometimes spells it "6022 -A ." or wraps the date onto the next line. References inside a text, such as "Executive Order No. 5327 of April 15, 1930", are never taken as headings.
3. An order ends at its own closing tag, "[No. 5550]". The tag may wrap: "[No. 5634" / "]".
   - **high** means the heading and the matching tag were both found.
   - **medium** means the tag was missing or carried another number (an OCR misread), so the text runs to the next heading. Every medium order has `needs_page_check: true`.
4. Table 2 (every order of the administration) and Table 3 (earlier documents that this volume's orders amended or revoked) are read too. In Table 3 a number and its comment are paired only when the OCR kept them on one line. Split lines are counted as unpaired rather than guessed.

## Outputs

| File | Contents |
|---|---|
| `<VOL>_ORDERS.csv` | One row per printed order: exact date, PDF and printed pages, closing tag, confidence, census state (`census_year_only`, `census_date_blank`, `NOT_IN_CENSUS`, `YEAR_CONFLICT`…), provisional status and the `original_text` step before this job, text path and sha256 |
| `texts/EO_<n>.txt` | The order's text, with a header naming the volume, PDF sha256, pages, confidence and the sha256 of the body below the header |
| `FRAGMENTS.jsonl` | One `original_representation` claim fragment per **census** order, in the same shape as `jobs/fr-originals` (`location_verified: false`, `needs_page_check` for medium) |
| `CENSUS_LEADS.csv` | Orders printed or listed here that the census lacks, census orders with a blank date that the volume dates, any year conflicts, and census orders in range that the volume does not print |
| `<VOL>_TABLE2.csv` | Table 2: number, year, month, day (blank when the OCR moved it), subject when it stayed on the same line |
| `<VOL>_AFFECTED_DOCUMENTS.csv` | Table 3: earlier proclamations and EOs, with the action (revoked, amended, superseded…) and the Hoover document that did it. These are later-event leads |
| `SUMMARY.json` | Counts per volume |

**Measured 2026-10-17 (Hoover vol. II):**
- 526 orders printed: all of EO 5550–6070, plus 5605-A, 5638-A, 5855-A, 6005-A and 6022-A. 523 are high confidence and 3 medium.
- All 500 census ids in the range have a text.
- 29 decided orders (all NO) had `original_text` open and get an official text here.
- 26 printed orders are **not in the census**. 22 of them are EO 5853–5879 (June–July 1932): the WPA numbered list's scan skips printed pages 486–487, and the census shares that gap. Table 2 adds a 27th, EO 5151A (vol. I's range).
- The volume dates 11 census orders whose date is blank.
- Table 3 gives 174 paired lines on earlier executive orders (86 revoked, 57 amended, 8 superseded…).

## Limits

The text is Google's OCR. Expect misread letters ("Junc 3") and, in tables, columns pulled apart.
Wording, identity and page boundaries are not human-verified. **Census leads only:** no identity
is admitted, merged or re-dated and no status changes. The 27 missing orders go to the census
owner as candidates. The readiness tracker does not read these fragments yet; wiring it to do so
is a separate change.
