# OFR Codification 1989: which orders were still in force on January 20, 1989

In 1989 the Office of the Federal Register published the *Codification of Presidential Proclamations
and Executive Orders, April 13, 1945 – January 20, 1989* (GPO; SuDoc AE 2.113:945-89). The book has
two parts:

- **The codified texts.** Every proclamation and Executive order that still had general effect on
  January 20, 1989 is printed, arranged in 50 subject chapters (like the CFR), **as amended up to that
  day**. Each text opens with a SOURCE line that gives the order's exact date and Federal Register
  citation.
- **The disposition tables.** These list every order of 1945–1989, plus any earlier order that a later one
  amended or ended, with its status on January 20, 1989: "Codified at Chapter 22, p. 382", "Revoked by EO
  10810", "Superseded by …", "Temporary", "Public lands", and so on.

**These texts are not the originals.** They are the editors' consolidated texts, so this job never offers
them as original texts. It is a *status* job. It reports what was in force in 1989, what had ended by then
and which document ended it, the exact dates, and how all of that compares with the census and with the
project's provisional YES/NO statuses.

It costs no model tokens and makes no web requests.

## Source

| | |
|---|---|
| Book | *Codification of Presidential Proclamations and Executive Orders, April 13, 1945 – January 20, 1989*, Office of the Federal Register, NARA (GPO 1989) |
| Copy | Google scan of the University of Illinois copy, HathiTrust `2027/uiug.30112026470077` (public domain). The owner downloaded it from HathiTrust on 2026-10-17. |
| PDF | `releases/source_books/OFR_1989_Codification_..._uiug.30112026470077.pdf` (Git LFS; 1,137 pages, 244,906,528 bytes) |
| Text | `data/codification_1989_pages.jsonl`: the PDF's text layer (Google's OCR), one line per PDF page |
| Table chunks | `data/codification_1989_eo_table_chunks.jsonl`: every piece of OCR text on PDF pages 1032–1103 (the Executive Orders table), with its x/y position on the page |

`data/PROVENANCE.json` records both sha256 values. The job checks them on every run. It checks the PDF's hash
only when the real file is present. On GitHub the PDF is an LFS pointer, and the job runs from the
committed text files alone. Both files were extracted again from the PDF on 2026-10-17 and came out
byte-identical.

## How orders are found

**Codified texts (PDF pages 12–980).**
1. Each page loses its running head and its printed page number. The running head is "Codification of
   Presidential …" on left-hand pages and "Chapter 5- Federal Civilian Personnel" on right-hand pages.
   The page number is kept for citations.
2. pypdf breaks 151 pages into a few words per line. All searching is therefore done on text with the
   spaces removed ("SOURCE:TheprovisionsofExecutiveOrder8248ofSept.8,1939,appearat4FR3864").
3. **An order is identified by its SOURCE line, not by its heading.** On some broken-up pages the
   heading does not start a line. The text starts at the heading ("Executive Order 10860 —Coat of arms
   …", with any kind of dash) found just before the SOURCE line. The book has no closing tag, so the
   text ends at the next heading or chapter heading.
4. *high* means the heading was found and no broken-up page was involved. *medium* means a page in the
   text came out a few words per line; those lines were joined back into paragraphs.

**Disposition table (PDF pages 1032–1103).** The plain text layer jumbles the table's three columns, so
the job works from the position of each piece of text:
1. The table has three columns: number or date (x≈56), amendments (x≈126) and disposition (x≈266). On
   each page the job measures where those columns are. Running heads, column heads and the page number
   are dropped.
2. A printed line belongs to a row when it sits within 3.6 points of the row's number. Rows are about 7
   points apart. An indented line continues the row above it. A line at the top of a page continues the
   last row of the page before.
3. The OCR often glues text together, and the job repairs only what it can repair safely:
   - "10070 AmendedEO 9975 Revokedby EO 10810" holds all three columns in one piece. It is split at
     the first status phrase.
   - "Revokedby EO 8036641" carries the row's own number, 641. "5924...........5925" is two numbers.
     A glued number is split off only when exactly one split puts a number where the page has none,
     in the right order.
   - "22452" is read as 2245½, but only when the census has EO 2245½ and the number would otherwise be
     out of order. "9-2" stays EO 9-2.
4. Unnumbered orders appear as dates. The month-day and the year are often separate pieces ("Aug." +
   "12,1898"). Once the date was even swallowed by the status ("Revokedby EO 9521Dec. 31"). These
   pieces are joined back together.
5. An italic "Revoked EO 9000" in the amendments column lists what a dead order had itself revoked. It is
   not the order's own status, and the job does not treat it as one. Neither is "Revoked in part by".

Anything that cannot be paired is listed in `DISPOSITION_ORPHANS.csv`, not guessed.

## Outputs

| File | Contents |
|---|---|
| `CODIFIED_1989.csv` | One row per codified EO. Columns: exact date and FR citation from its SOURCE line; 3 CFR compilation page; the "revised and restated" and "not in the Federal Register system" notes; chapter and subchapter; PDF and printed pages; number of bracketed amendment notes; the table's own row for it; census state; provisional status and the `original_text` and `ending_or_current_basis` steps; and an `agreement` column (`agrees` or `CHECK`, with the reasons). |
| `texts/EO_<n>.txt` | The codified text. Its header says **AS AMENDED TO JAN 20, 1989; EDITORIAL CODIFICATION; NOT THE ORIGINAL TEXT** and names the book, the PDF sha256, the pages, the confidence and the sha256 of the body. |
| `DISPOSITION_1989.csv` | Every row of the Executive Orders table. Columns: id or date; census id; amendments; disposition as printed (OCR); category and group; chapter and page when it is codified; acting documents (EO, Proc, PLO, Pub. L., act of …, U.S.C., CFR); pairing confidence; repair flags; and whether `jobs/later-events` (the OFR's online data) names the same revoking or superseding order. |
| `STATUS_LEADS.csv` | Three kinds of lead. Decided-NO orders that were in force in 1989, split by whether `later-events` knows an ending after 1989. Decided-YES orders that had ended by 1989. Undecided census orders that the table shows ended or in force in 1989. |
| `CENSUS_LEADS.csv` | Exact dates for year-only census orders (from SOURCE lines, and separately from references such as "EO 9397 of Nov. 22, 1943" in the texts). Also: orders the census lacks, dates for the unnumbered census rows, ambiguous matches, and census orders in EO 9538–12667 that the table was not read to contain. |
| `UNNUMBERED_ROWS.csv` | The 18 dated rows of the table, matched to the census's unnumbered rows (`research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv`) and to Lord's 1943 list (`research/stage14/LORD`): match, ambiguous or unmatched, never forced |
| `REFERENCE_DATES.csv` | Every dated reference "EO N of <date>" inside the codified texts, with the number of mentions and any variant dates |
| `FRAGMENTS.jsonl` | `later_event_candidates` only (evidence type `ofr_codification_1989_table`): "revoked / superseded / terminated by" a named EO or proclamation, for census orders. The date is the acting order's date from its own SOURCE line here, or from the OFR catalog that `later-events` reads, when known. **No `original_representation` fragments.** |
| `DISPOSITION_ORPHANS.csv`, `SUMMARY.json` | Unpaired table fragments; all counts |

## Measured on 2026-10-17

**Codified texts**
- 555 Executive Orders and 47 proclamations have SOURCE lines. Every one also has its heading.
- 554 EOs have an exact date. EO 10631 has none.
- 3 EOs (1888, 4601 and 6166) "do not appear in the Federal Register system". 4 were restated in full by a later order.
- Confidence: 420 high and 135 medium.
- By decade: 1910s 2, 1920s 1, 1930s 3, 1940s 42, 1950s 95, 1960s 94, 1970s 154, 1980s 163.
- All 554 dates agree with the census year, and the census has only the year for every one of them. These give 554 exact-date leads.
- Provisional status of the 555: 210 YES, **89 NO**, 256 undecided.
- Of the 89 NO orders, `later-events` knows a post-1989 ending for 15. That leaves **84 orders decided NO with no known ending after the book**. These are counterevidence leads.

**Disposition table**
- 4,224 rows: 4,206 numbered orders and 18 dated unnumbered orders. Every one of the 4,206 numbered ids is in the census.
- Pairing confidence: 4,056 high, 162 medium and 6 low. No row is without a disposition, and 2 fragments are unpaired.
- The table's 555 "Codified at Chapter" rows are exactly the 555 codified texts.
- EO 9538–12667 should be complete. Four numbers (10217, 10275, 10288 and 10595) are missing from the OCR of the table itself: the rows around them are contiguous.
- Groups:
  - ended by 1989: 2,860 (revoked 1,540, superseded 416, temporary 299, executed and obsolete 195, authority repealed 150, …)
  - in force: 578 (codified here 555, codified elsewhere 23)
  - effect merged into another order: 408
  - excluded but not ended: 281 (public lands 273, tariff 8)
  - other: 97
- **Cross-check.** For 1,669 revoked or superseded rows, the OFR's online data (via `jobs/later-events`) also names a revoking or superseding order. It names the same order for 1,663 of them (99.6%).
- **Unnumbered rows.** 16 of the 18 dated rows match exactly one census row, all of which have a blank census date. 2 rows (Aug. 8, 1914) share a date with two census rows and are left ambiguous.
- **Status leads.** 1,298 undecided census orders had ended by 1989, and 261 were in force. 3 decided-YES orders had ended by 1989 (two through repeal of their authority).
- **Not in the census.** One order, EO 6585 (Feb. 6, 1934), appears only in a dated reference.
- **Reference dates.** 533 more exact-date leads come from dated references for year-only census orders that have no SOURCE line.
- **Fragments.** 1,970 later-event items for 1,924 census orders, 1,829 of them with an acting-order date.

## Limits

- Everything is Google's OCR, and nothing was checked against the page images. Status phrases and numbers can be misread (one "p. 62C" stands for p. 620).
- Statuses are as of January 20, 1989. Anything after that date is not in the book.
- Medium- and low-confidence pairings carry `needs_page_check` in the fragments.
- The proclamation disposition table (PDF 982–1032) is not parsed. Proclamations are not census items.
- The 1989 "in force" snapshot is not emitted as a fragment, because claim-drafts has no fragment kind for it yet. It is in `CODIFIED_1989.csv` and `DISPOSITION_1989.csv`.
- **Leads only.** No census identity is admitted, merged or re-dated, and no status changes.
