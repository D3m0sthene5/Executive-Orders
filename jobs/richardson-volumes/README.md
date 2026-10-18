# Richardson volumes: printed texts of early orders, and where the two WPA lists point

James D. Richardson's *A Compilation of the Messages and Papers of the Presidents, 1789-1897*
(published by authority of Congress, GPO 1896-99) prints, president by president, the messages,
proclamations and "Executive Orders" of each administration. It is the book the two WPA finding
aids cite most for 19th-century orders: the numbered list writes "IX R 612" (vol. IX, p. 612) and
Lord's 1943 list of unnumbered orders writes "IX Richardson 612". This job reads the volumes we
have, splits their executive-order sections into one text per order, and looks up every one of
those citations: which order on the cited page is meant, or why it can't be told.

**Richardson is a printed compilation, not the signed originals.** He copied department records
and newspapers (his own notes say so: "[From the Daily National Intelligencer, May 17, 1862.]").
Every text here is a transcription lead for the `original_text` step, never the original.

It costs no model tokens and makes no web requests.

## Volumes

| Volume | Covers | PDF pages | Scan |
|---|---|---|---|
| **VI** (GPO 1897) | Lincoln and Andrew Johnson, 1861-1869 | 797 | Google, University of Florida copy, HathiTrust `ufl.31262091102953` |
| **VII** (GPO 1898) | Grant and Hayes, 1869-1881 | 677 | Google, University of Florida copy, HathiTrust `ufl.31262091102805` |
| **IX** (GPO 1898) | Benjamin Harrison and Cleveland's second term, 1889-1897 | 831 | Google, Penn State copy, HathiTrust `pst.000024803533` |

The owner saved the three HathiTrust PDFs to Downloads on 2026-10-17. They are kept unchanged under
Git LFS in `releases/source_books/`. Their text layers are committed in `data/`, so the job never
needs the PDFs; when a real PDF is present its sha256 is checked, and an LFS pointer is reported as
such. `data/PROVENANCE.json` has one entry per volume (hashes, page offsets, the table of contents'
executive-order sections, the presidents' signatures). Adding vol. VIII or X means adding its PDF,
its two text files and one entry there.

## How an order is found

1. **Pages.** Printed page = PDF page minus a fixed offset (it changes where portrait plates are
   inserted). The offsets are checked against every running head the OCR left readable
   ("ΙΟΙ Messages and Papers ofthe Presidents" is p. 101); the run stops if fewer than 99% agree.
   Running heads, sheet marks ("M P-VOL IX-5") and OCR specks are dropped.
2. **Broken pages.** On a few pages the OCR comes one or two words per line and runs words together
   ("inthe office ofregister"). There the job uses a second text layer (pdftotext), committed for
   those pages only, and rejoins the words.
3. **Sections.** The volume is cut at its own headings (EXECUTIVE ORDERS, PROCLAMATIONS, SPECIAL
   MESSAGES ...). The executive-order sections must start on the pages the table of contents gives,
   or the run stops. A title "EXECUTIVE ORDER." inside such a section is an order's title, not a new section.
4. **Orders.** A new order starts at a dateline ("EXECUTIVE MANSION , May 24 , 1895 .") together with
   the title lines above it, or right after the previous order's signature block (the President's
   name, "By the President: / NAME, / Secretary of State.", a Secretary's signature, or "Very
   respectfully, NAME"). Dates inside sentences, weekday dates and "approved January 16, 1883" (the
   Civil Service Act, cited in dozens of orders) never start an order. An order printed inside
   General Orders ("The following order of the President has been received:") is kept as its own
   order and flagged; rules "herewith published" stay with the order that approves them.
5. **Dates.** The President's approval wins ("Approved, May 24, 1895."), then the dateline, then a
   department letterhead, then "this 27th day of April, 1861".
6. **Outside the sections.** An order quoted in a message ("the following Executive order was
   issued on the 4th day of September, 1890:", EO 28) is picked up; one hand-located document with
   no dateline (vol. VII's civil service rules of December 19, 1871) is configured in PROVENANCE.json.
7. **Confidence.** *high* = a start, a signature and a date were all found, under 300 lines, not
   printed inside another document. Everything else is *medium* and marked `needs_page_check`.

## How a citation is located

Each WPA or Lord citation is compared with the orders on the cited page: first by date, then (when
several orders share the date, or Lord gives none) by the words of the list's summary, weighting
rare words and the rule named ("Postal Rule IV"). The answer is `match`, `ambiguous` (the
candidates are listed) or `unmatched` (the reason is given). Nothing is forced. The `method`
column says how: `date_and_page`, `date_page_and_subject`, `subject_on_page`, `date_on_other_page`
(the list's page is off), `subject_list_year_wrong` (the list's year is one off), and so on.
The parsed lists are repaired as they are read: merged WPA rows are split again ("28-1: Jan. 30");
Lord rows that swallowed the previous entry are split; OCR spellings ("Richarăson", "kichardson",
"VII E 218") are folded. Each repair is reported as a `LIST_PARSE_CORRECTION` lead.

The lists come from `jobs/wpa-lists/output` when that job's output is there; until it is merged,
from `data/lists_subset` (its rows that matter here, copied unchanged, hashes in PROVENANCE.json).
Both give the same results.

## Outputs

| File | Contents |
|---|---|
| `CITATIONS.csv` | Every WPA and Lord citation into the three volumes: entry, cited page, status, method, the order(s) found, a note, and the cited page's text file. Also the WPA's numbered orders of these years that cite no page here, tried on date and subject |
| `<VOL>_ORDERS.csv` | One row per document found: date and where it came from, all datelines, PDF and printed pages, signer (President / by direction of the President / department), form, title, WPA numbers, Lord entries, census state, provisional status and `original_text` step before this job, confidence, text path and sha256 |
| `texts/<VOL>/EO_<n>.txt`, `texts/<VOL>/<date>_<title>_<doc>.txt` | One text per order, with a header naming the volume, PDF sha256, pages, date, confidence, the compilation warning and the sha256 of the body |
| `pages/<VOL>/p<page>.txt` | The text of every page a list cites |
| `FRAGMENTS.jsonl` | One `original_representation` fragment per **census** order found, in the `fr-originals` shape: `location_verified: false`, route `compilation/richardson_messages_and_papers`, and `identified_by` (`wpa_citation`, or `date_and_subject_only`, which always needs a page check) |
| `CENSUS_LEADS.csv` | `DATE_FILL` (census has only the year), `NOT_IN_CENSUS_numbered`, `NOT_IN_CENSUS_unnumbered` (orders signed by or for the President, or cited by Lord), `IN_CENSUS_NOT_FOUND_IN_VOLUME`, `CANDIDATE_TEXT_DATE_ONLY`, `LIST_PARSE_CORRECTION` |
| `ENDING_LEADS.csv` | Sentences in the orders that revoke, rescind, supersede, amend, extend or suspend something: later-event leads |
| `SUMMARY.json` | Counts per volume |

**Measured 2026-10-17:**
- Page maps: 751 of 751 (VI), 632 of 632 (VII) and 792 of 792 (IX) readable running heads agree with the offsets. All 39 executive-order sections start and end on the pages the contents give.
- Orders: 213 (VI), 75 (VII), 154 (IX); 442 texts. High confidence: 167, 55 and 142.
- WPA citations: VI 3 of 3 matched (EO 1, 3, 4); VII 11 of 11; IX 72 of 76, and the other 4 are 1910 entries whose "IX R" is a misread of another source. In vol. IX that places 73 WPA numbers in 59 orders (one order can carry several numbers, e.g. EO 40-42).
- Lord citations: VI 42 matched of 44 (1 ambiguous, 1 unmatched); VII 33 of 35 (1 and 1); IX 77 of 79 (2 ambiguous).
- Census: 68 census orders get a text and a fragment (5 + 11 + 52); 65 through a WPA citation, 3 (EO 2, 5, 28) on date and subject only. All 68 census dates are year-only and the volume gives the day. 2 of them are decided (EO 5 and EO 9, both NO) with `original_text` open.
- 21 numbered orders of vol. IX are not in the census (EO 36-49, 51-53, 92, 92-1 to 92-3). 305 unnumbered orders are leads for the census owner (151 of them matched by a Lord entry).
- Census orders of these years not found: EO 6 (VI); EO 10, 12, 14, 15 and 21 (VII); EO 28A (IX). EO 7 (VI), 30-1 and 54 (IX) have several orders of the same day and stay ambiguous.
- Compared with the three readers who first looked at these volumes: of the citations they resolved by hand, the job agrees on 45 of 47 (VI) and on 32 of 35 Lord and 9 of 9 WPA citations (VII); for IX it agrees with their table on all 77 Lord citations and 71 of 72 WPA ones (for EO 29 the job takes Hayes's death order inside General Orders No. 4, dated Jan 18, not the wrapper of Jan 19). The disagreements are left ambiguous or unmatched here rather than guessed.
- Lord and the WPA list also cite Richardson vols. II-V, VIII and X (218 citations), which this job does not hold yet. Lord's vol. X citations run to 1904, so they point at a later printing of that volume.

## Limits

The text is Google's OCR: expect misread letters and scrambled tables (the court-martial lists and
the 1896 civil service codification are medium confidence for that reason). Order boundaries are
found by rules and checked on samples, not proofread page by page; a few documents still split at
the wrong line, and a later paragraph of a General Orders ("II. On the day of the funeral ...") is
kept as a fragment, not an order. The signer and form columns are rough. Whether a department's
order "by direction of the President" is a presidential executive order is a human call.
Subject-only matches (Lord gives no date in many rows) are weaker than date matches. The Project
Gutenberg text of vol. X, section 1 (the appendix of papers omitted from vols. I-IX) is not
included: it has no page numbers, so the lists' page citations can't be checked against it; it
belongs in its own job. **Leads only:** no identity is admitted, merged or re-dated and no status
changes. The readiness tracker does not read these fragments yet.
