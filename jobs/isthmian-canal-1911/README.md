# Isthmian Canal Commission orders, 1904-1911: official texts from the 1911 compilation

In 1911 the Government Printing Office printed *Executive Orders Relating to the Isthmian Canal
Commission, March, 1904, to June 12, 1911, inclusive* for the Commission that was building the
Panama Canal. The book prints the **full text** of 177 documents that governed the Canal Zone: the
President's orders, the Secretary of War's orders (many issued "by direction of the President"),
a few letters, one proclamation, one Commission resolution and one War Department circular. This
job turns the book into one text per document, checks each date against the document itself, and
compares the President's orders with the census.

It costs no model tokens and makes no web requests.

## The source

| | |
|---|---|
| Book | *Executive Orders Relating to the Isthmian Canal Commission, March, 1904, to June 12, 1911, inclusive* (Washington: GPO, 1911), 237 printed pages plus a 10-page table of contents |
| Copy | University of Florida (gift of the Panama Canal Museum), scanned for HathiTrust: [`2027/ufl1.ark:/13960/t3dz15k02`](https://hdl.handle.net/2027/ufl1.ark:/13960/t3dz15k02) |
| PDF | 253 pages, kept under Git LFS in `releases/source_books/` |
| Text | the scan's own OCR, extracted page by page into `data/ic1911_pages.jsonl` |

Both sha256 values are in `data/PROVENANCE.json`, so the job never needs the PDF itself. When the
PDF has been pulled, the job checks its hash too.

## How a document is found

The book is harder than the later Federal Register compilations: **it prints no EO numbers, no
headings and no closing tags.** So the job works from the table of contents.

1. **Contents.** Each contents line ("Order of the President, Mar. 26, 1904, prescribing compensation
   of commissioners ... 3") gives the kind of document, who issued it, the date and the page. The
   category comes from these words, never from the signature. The OCR misreads are fixed by rule:
   "Mai-." is March, "Dcic." is December, "2.5" is 25, and a damaged year such as "1V)07" or "19U" is
   limited to 1904-1911. When more than one year still fits, the year the document's own dateline
   shows is used. Entry 129 has no date in the contents, so its date (March 23, 1909) comes from the body.
2. **Pages.** PDF page = printed page + 13. The running heads ("6 EXECUTIVE ORDERS.", "ISTHMIAN CANAL
   COMMISSION. 7", OCR'd as "OEDEES", "C0MMI6SI0N", "rSTHMTAK"...) and the printer's marks
   ("98987—11 2") are removed.
3. **Where a document ends.** It runs from its own page to the page before the next document's page,
   with two exceptions found on this book:
   - Two documents start on printed p. 40 (entries 19 and 20). The page is split after the first
     closing dateline, "April 3, 1905."
   - Two presidential orders (entries 17 and 89) end at the top of the next document's first page,
     above a War Department letter. The job sees that the order has no closing line and the next page
     doesn't open a new document. It then moves the lines down to the President's signature back to
     the order. If no signature is found, both documents are flagged instead.
4. **Dates are checked against the body.** For each document the job looks for its date in the
   closing lines: "The White House, March 26, 1906.", "Oyster Bay, August 31, 1905.", "War
   Department, Washington, D. C., March 12, 1907." The check accepts OCR spellings such as
   "Septemier", "Decemler", "Ajyril" and "March I4". A day it cannot read ("August lf>", "March W")
   is reported as `damaged_day`, not guessed. A document whose date is not confirmed this way is
   `needs_page_check`.
5. **EO numbers.** Because the book prints none, the number of each presidential order comes only
   from `data/ic1911_crosswalk.csv`. That table was made by hand on 2026-10-17 by matching each order
   to the WPA numbered list on the same date and subject. It also records four matches to Lord's 1943
   list of *unnumbered* orders. The job and its tests check that every crosswalk date equals the
   book's date. `build_crosswalk.py` shows how the table was made; the job does not run it.

## Outputs

| File | Contents |
|---|---|
| `IC1911_DOCUMENTS.csv` | All 177 contents entries: category, date and where it came from, body date check, printed and PDF pages, boundary notes, signers, "by direction of the President" flag, EO id or Lord number, confidence, text path and sha256 |
| `IC1911_ORDERS.csv` | The President's documents (107 orders, 2 letters, 1 proclamation; entry 6 holds two orders): census state, readiness status and `original_text` step **before** this job, text path and sha256 |
| `texts/EO_<n>.txt` | The order's text with a header naming the book, PDF sha256, pages, date check, confidence, how the EO number was assigned, and the sha256 of the body below the header. EO 577½ and 680½ are written `EO_577-half.txt` and `EO_680-half.txt` |
| `texts/LORD_<seq>.txt`, `texts/<date>_<category>_seq<nnn>.txt` | Documents matched to Lord's unnumbered list, and every other document, with the same header |
| `FRAGMENTS.jsonl` | One `original_representation` fragment per **census** order, in the shape `jobs/ofr-compilations` uses (route `official/ic_compilation_1911`, `location_verified: false`, `needs_page_check` when the date is not confirmed or the boundary is unclear) |
| `CENSUS_LEADS.csv` | Census orders with a blank date that the book dates; unnumbered presidential documents not in the census; matches to Lord's list; canal orders in the WPA list that the book does not print (`IN_LIST_NOT_IN_VOLUME`); Secretary of War orders issued "by direction of the President" (candidates only) |
| `IC1911_WPA_LORD_MATCH.csv` | Every presidential document and every "by direction" order: matched to a numbered EO, matched to Lord, or unmatched, with the list's own date, citations and wording |
| `IC1911_AFFECTED_DOCUMENTS.csv` | Amend, revoke, repeal, supersede and modify leads, from the contents wording and from dated references in the bodies ("the Executive Order of June 11, 1907, ... is hereby revoked"). A target is named only when one document of that date (or, without a date, one document's subject) clearly fits. Ties are reported as ambiguous |
| `SUMMARY.json` | Every count below |

**Measured 2026-10-17:**
- **177 contents entries:** 107 orders of the President, 62 of the Secretary of War, 2 letters of the President, 3 of the Secretary, 1 proclamation, 1 Commission action and 1 War Department circular.
- **Pages:** 147 documents fill a single page; the longest are the May 9, 1904 letter (pp. 4-11) and the Nov. 5, 1905 accounting rules (pp. 53-61). In 220 running heads with a readable number, the number equals PDF page − 13 except three OCR misreads (PDF 78 "66", PDF 176 "1153", PDF 193 "130").
- **Contents order is book order, not date order.** There are 5 inversions; for example, transmittal letters are printed after the orders they sent.
- **Dates:** 103 of the 107 presidential orders are confirmed by their own closing dateline (80 by an exact "White House, Month D, YYYY" line). Four need a page check: 6 (printed inside a Civil Service Commission notice), 78 and 171 (day unreadable) and 129 (no date in the contents). Two Secretary of War orders have a body dateline that differs from the contents (entries 86 and 104). Both are flagged and neither is changed.
- **Crosswalk:** 105 EO ids for 104 entries (entry 6 is EO 273 and EO 274). All 105 are in the census: 102 have a year-only date there and 3 have a blank date that the book supplies (EO 577½, EO 680½, EO 1345). There are 0 year conflicts. 104 WPA dates equal the book's date; EO 1345's WPA entry has no day ("Hay 2").
- **Readiness before this job:** all 105 had the `original_text` step open. Two of them are decided (`no`): EO 283 and EO 1153.
- **Unnumbered documents:** 3 presidential orders (entries 2, 14, 65), 2 letters and the proclamation are not in the census. Lord's 1943 list has 4 of the book's documents: entries 2, 14 and 65, and the Secretary of War's deeds order of Mar. 12, 1907 (entry 55, issued by direction of the President).
- **Secretary of War orders:** 31 say "by direction of the President", 1 is "approved" by the President, and 30 are the Secretary's own.
- **Not printed:** 8 canal-related orders in the WPA list fall inside the book's dates but are not in it: EO 307, 308, 354, 401, 556, 582, 992 and 1035. Most are civil-service eligibility orders for individual employees. The assessor counted 9. The difference is EO 547 (the Isthmus of *Tehuantepec*, Mexico), and the WPA row for EO 680, whose canal text belongs to 680½.
- **Amend/revoke leads:** 58 rows (43 from the contents, 14 from dated references in bodies, 1 "orders in conflict are revoked" clause). 22 name a target document in the book, 16 of them an order with an EO id. 21 amend rules or codes rather than a document. 8 are ambiguous, 4 unresolved and 2 cite a date the book does not contain.

## Limits

The text is the scan's OCR, with misread letters ("Classificatiun", "apjjomted") and run-together
words. Wording, page boundaries and identities are **not human-verified**. The EO numbers rest on the
hand-made crosswalk, not on the book. I checked by regex that the contents and the "White House"
lines agree, but I did not prove page by page that the contents lists every document. The
"by direction of the President" split comes from a pattern and can miss OCR-damaged wording. Nothing
here is from before 1900, so the book does not help with the pre-1900 unnumbered gap. The census
holds 19 undated, untitled `EO:UN…` ids, so the job cannot tell whether any of them is one of the
book's unnumbered documents.

**Census leads only:** no identity is admitted, merged or re-dated, and no status changes. The
readiness tracker does not read these fragments yet; wiring it to do so is a separate change.
Tests whose counts depend on the census or the readiness output run only while those files still
match the hashes recorded in `PROVENANCE.json`. After those files change, the job reports the new
counts instead of failing.
