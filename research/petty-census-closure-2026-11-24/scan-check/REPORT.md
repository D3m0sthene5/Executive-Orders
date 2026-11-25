# Reading the documents behind the 3,941 ProQuest records missing from the census (2026-11-24)

Coordinator: Claude (Opus 5.5), in the owner's Chrome through NYU's ProQuest subscription, at the owner's request
and with his permission to fetch the documents. The reading of document text and page images was delegated to
Claude Haiku, and a second reading of 344 documents to Claude Sonnet.

## Conclusion

ProQuest holds **2,206 executive orders that the census lacks**, counting only documents that show a presidential act
on their face or that ProQuest marks signed by the President. Another 95 are probable, and 28 records could not be
read. The counted documents come from five sets:

- **2,038 signed unnumbered records.** These are the documents behind the 3,941 unnumbered records that ProQuest
  marks signed by the President and that no census list holds: 1,533 land orders and 505 other operative orders.
  Another 70 are land-order files whose order page cannot be read; every such file checked by eye contained the order.
- **81 land orders on dates the census already covers.** The title matcher set aside 384 signed land records because
  a census entry of the same series, or sharing a distinctive word, carries the same date. A reader compared each
  document with every census entry of that date. 266 are orders the census already holds, 81 are different orders
  (most of them numbered power-site, coal, petroleum, phosphate and public-water orders of 1910 to 1926), 24 cannot be
  decided, and 13 hold no order or are not land orders.
- **30 unsigned unnumbered records.** ProQuest marks these 1,472 records not signed, and their documents were read in
  the same way. 30 turn out to carry the President's signature, approval or name.
- **52 military orders.** ProQuest's separate "Military orders and pardons" collection holds 654 general orders and
  regulations of 1828 to 1936 that no census list holds. The 52 counted are presidential orders such as Navy pay
  orders, Army regulations approved by the President, and Lincoln's approval of the instructions for the government
  of armies in the field (April 24, 1863).
- **5 signed records filed as copies.** ProQuest files five signed records as second copies of an unsigned
  attachment or map, so the matcher passed over them. Each is a signed land order, for example Andrew Johnson's
  light-house reservation at Eagle Bluff, Wisconsin (October 19, 1866).

A second reader of another model size (Claude Sonnet) re-read 344 of the judgments without seeing the first. It
disputes 20 of the 196 text-read operative orders, calling them letters of instruction or statements. It agrees with
every sampled "not an executive order" verdict, every order-language-rule verdict, 25 of 27 text-read land orders and
39 of 40 image-read orders. Carried over to the judgments it did not re-read, that rate puts about 70 of the 2,206 in
dispute, mostly on the line between an operative order and a letter of instruction. A count that drops every disputed
kind is therefore about 2,140.

The other 1,824 signed unnumbered documents are not executive orders: 455 actions on one person, 367 letters of
instruction, 254 other letters, 172 fund approvals, 172 orders a Secretary signed "by command of the President," 132
appointments, 70 proclamations, 33 pardons, 17 treaties and 152 others.

| Era | Land orders | Other operative orders | Land files, order not readable | Not executive orders | Unreadable or no PDF |
|---|---:|---:|---:|---:|---:|
| 1789-1861 | 76 | 84 | 2 | 509 | 4 |
| 1862-1906 | 237 | 373 | 32 | 822 | 4 |
| 1907-1936 | 1,220 | 48 | 36 | 493 | 1 |
| **All** | **1,533** | **505** | **70** | **1,824** | **9** |

The table covers the 3,941 signed records only. The 81 orders on covered dates fall 2 in 1789-1861, 10 in 1862-1906
and 69 in 1907-1936.

The census's identified unnumbered series is 1,405 to 1,816 orders. The 2,206, or about 2,300 with the probable
records, would more than double it.

Examples include:

- Van Buren's transfer of $500,000 to the Mint (July 20, 1838).
- Lincoln's order making Arkansas one revenue collection district (March 1, 1865).
- Grant's order for a new census of New York City (1870).
- Arthur's consolidations of North Carolina and Wisconsin revenue districts.
- McKinley's Philippine government orders of 1899 to 1901.
- Taft's coal-land restorations.
- Harding's order vacating Alaskan Withdrawal No. 1 (May 19, 1921).

Of the 505 operative orders, 341 carry the President's signature, 84 his approval, and 49 are issued in his name.
22 show no presidential act, 6 a Secretary's signature only, and 3 cannot be read.

## Method for the signed unnumbered records

1. **Fetching.** Each record's PDF was fetched inside the ProQuest page from ProQuest's own document link, using the
   address pattern `$2fPT1-<accession>` or, for 133 records of 1874 to 1879 and 1929, `$2f<accession>`. Two records
   have no PDF at either address.
2. **Text.** ProQuest's PDFs carry an invisible text layer made by optical character recognition (OCR). A browser
   script extracted it, and the full text of every document is saved in `PQ_TEXT_LAYER_3941.jsonl.gz`.
   - A record whose title marks it as a land order and whose text contains order language ("hereby withdrawn",
     "hereby restored", "it is hereby ordered", "Order of Restoration" and the like) was counted as a land order
     (838 records).
   - The rest of the legible documents (2,082) went to six Claude Haiku readers. They classified each document under
     a fixed rubric (`READER_RUBRIC.md`), working from an excerpt built around its order language and quoting
     evidence.
   - The readers agreed with Claude's own scan judgments for 26 of 28 documents. They used 1,486,842 tokens.
3. **Page images.** A document was sent to page reading in either of two cases:
   - fewer than 8% of its text-layer words are common English words, which is what handwriting produces (1,019);
   - a text reader marked it illegible (233).

   The page images are 1-bit CCITT Group 4 scans, which Chrome cannot display. A decoder written for this job
   (`g4_page_decoder.js`) ran inside the page. It decoded the first and last page of each document, reduced each to
   about 800 pixels wide, and saved it as a PNG of about 20 KB. Of these, 1,911 images (36 MB) were copied to the
   workspace. Ten Claude Haiku readers judged them under `IMAGE_READER_RUBRIC.md`.
   - A 30-document probe ran first, with Haiku and Sonnet in parallel. The two models agreed with each other on
     whether a document is an executive order for all 30. Each agreed with Claude's own scan judgments for 10 of the
     12 documents Claude had read.
   - Image readers used at least 2.44 million tokens, including the probes. Four readers were interrupted by a
     server restart and resumed, and their pre-restart usage is not included in that figure.
4. **Land files without a visible order.** Land-titled records that a text reader called a letter or "other" are
   listed as probable land orders (70). In the hand-read sample, all five such files contained a signed order on a
   page the OCR could not read.

Results for every record are in `FULL_READING_3941.csv`. For each record it gives who or what read it, the kind of
document, the presidential act shown, the date on the document, the evidence and a note. The earlier hand reading of
50 random records is in `RESULTS.csv` and `SAMPLE_50.csv`.

## The rest of ProQuest's presidential collections

**Records the first reading missed.** The first page-by-page reading of the unnumbered collection, oldest first,
captured 19,918 of its 20,028 records. A second reading, newest first, captured all 20,028. The 111 records added
are maps, attachments and second copies, and none is a new candidate (`../proquest-scan/PQ_UNNUMBERED_1789_1936.psv`
now has all of them).

**Unsigned unnumbered records.** The 1,472 records that ProQuest marks not signed and that match nothing in the
census were fetched and read like the signed ones. They break down as follows:

- 590 are Federal Power Commission restorations under section 24 of the Federal Water Power Act. Their titles
  identify them as Commission acts, so they were not read.
- 291 are orders a Secretary signed by the President's command.
- 152 are land or operative orders that a department issued with no presidential act shown.
- 30 are presidential orders. Examples include the 1813 embargo implementation, Polk's enlargement of the Seminole
  reservation (1845), Johnson's claims procedure for the reward for capturing Lincoln's assassins (1865), and
  Roosevelt's 1935 gold-clause and currency-exchange regulations, and two land-office removals of 1839 and 1842.
- 58 more, read from up to eight page images each, are Secretary orders, actions on one person, letters and
  departmental orders.
- 18 are unreadable or have no PDF.

**Military orders.** ProQuest's "Military orders and pardons" collection has 3,907 records, of which 2,716 are dated
before 1937 (`../proquest-scan/PQ_MILITARY_ORDERS_1789_1983.psv`). The same title rules and census match left 2,132
that no census list holds (`../proquest-scan/MILITARY_CANDIDATES_MISSING.csv`). A further rule set aside courts-martial,
medals, assignments, commands and other actions on one person. The remaining 654 general orders and regulations were
fetched and read:

- 325 are orders a Secretary signed by the President's command.
- 169 are departmental orders with no presidential act.
- 52 are presidential orders. Examples include Navy pay orders, Army uniform and ration regulations, rules for the
  Army and Navy Hospital at Hot Springs, ROTC unit establishments, and the renaming of Porto Rico as Puerto Rico
  (1899).
- 14 more, read from up to eight page images each, are not presidential orders.
- 1 (1874-54-6, approving Army headquarters at St. Louis) has no PDF.

Results for both sets are in `UNSIGNED_AND_MILITARY_READING.csv`.

**Land orders on dates the census already covers.** The title matcher counts a ProQuest record as held when a census
entry has the same date and the same order number, or shares two distinctive words. It set aside 384 signed land
records whose date matches a census land entry but whose number or subject does not. Their text was fetched (382 have
a PDF) and a Claude Haiku reader compared each document with every census entry of the same date under
`G_MATCH_RUBRIC.md`, naming the matching entry when there is one. The census's power-site date groups list their
reserve numbers, so a reserve missing from the list counts as a different order. The coordinator checked the
different-order verdicts that rest on a date or number discrepancy and moved two to "already held": Jackman Creek
Restoration No. 85, which the census dates a month later, and the Clark Fork River modification, where the census
reads reserve 364 and the document 384. Four more were not land orders by any reading (two fund approvals, the
removal of one land-office register, and an Army general order on Fort Walla Walla). The results:

- 266 are orders the census already holds.
- 81 are different orders. Examples include Coal Land Withdrawals Arizona No. 1, North Dakota Nos. 1 and 2, South
  Dakota No. 1, Washington No. 1 and Oregon No. 1 (1910); Power Site Reserves Nos. 43 to 74 and 76 to 97 (1910);
  Petroleum Reserves Nos. 52 and 55 (1917); Fort Dakota Military Reservation (1867); the abolition of Fort Bridger
  (1890) and Fort Marcy (1891); and Alaska Railroad Executive Order No. 3 (1915).
- 24 cannot be decided, usually because the text is garbled and the census entry is a bare date group.
- 13 hold no order text or are not land orders.

**Records not read in the first pass.** 124 records had no readable text, no PDF, or an unreadable first and last
page. Their documents were fetched again and up to eight pages of each were read. Six of the signed records and two
of the unsigned are presidential orders, for example the restoration of the Fort Mitchell lands in Alabama (1838) and
a Treasury directive of 1836. Nine signed attachment and map records proved to be parts of a base record. Reading the
base records found five signed records that ProQuest files as copies of an unsigned attachment, and all five are land
orders. 28 records remain unread: 9 signed and 18 unsigned records whose pages cannot be read or that have no PDF,
and 1 military order without a PDF. Four other identifiers in the unsigned list are 1935 and 1936 government
publications (airport circulars, vital statistics and notices to airmen), not orders. Results are in
`FINISH_READING.csv`.

**Second reader.** Claude Sonnet re-read 344 documents under the same rubrics, without seeing the first verdicts:
a random 120 from the text readings and the order-language rule, all 184 other text-read operative orders, and a random
40 from the image readings (`SECOND_READER.csv`).

| First verdict | Re-read | Second reader agrees | Disputes | Cannot read |
|---|---:|---:|---:|---:|
| Not an executive order (text) | 35 | 33 | 0 | 2 |
| Land order (text) | 33 | 25 | 2 | 6 |
| Operative order (text) | 196 | 176 | 20 | 0 |
| Land order (order-language rule) | 30 | 30 | 0 | 0 |
| Executive order (page images) | 40 | 39 | 1 | 0 |
| Probable land file | 10 | 1 calls it an order | 9 see no order | 0 |

The 20 disputed operative orders are listed by name in `SECOND_READER.csv`. Ten are presidential letters giving one
official instructions, such as Jefferson's instructions to Commodore Barron (1804) and the 1898 instructions to the
Cuba and Porto Rico evacuation commissioners. Others are statements (Wilson's warning to office-seekers, 1913),
Secretary-signed circulars and a fund order. The two disputed land orders are files in which the reader found only
the transmittal letter. Of the probable land files, the second reader also saw no order in nine, which is expected:
these are the files whose order page the OCR could not read.

**Collections not read, and why.**

- *Unnumbered presidential documents after 1936 (25,735 records).* From 1936 every executive order was numbered and
  published in the Federal Register. The unnumbered records ProQuest files after 1936 are messages, memoranda,
  nominations, statements and similar documents. A sample of 600 of the most recent confirms this.
- *Presidential pardons (18,547 records), nominations and appointments, proclamations, and signing statements.* These
  are other kinds of presidential act. ProQuest's numbered executive orders were checked against the census in an
  earlier pass.

## Limits

- **Reader error.** A second reader disputes 23 of 344 judgments (table above). Carried over to the 1,500 judgments
  it did not re-read, that rate puts about 70 of the 2,206 in dispute, almost all on the line between an operative
  order and a letter of instruction or a transmittal. Readers of the same model family share blind spots, so a
  reviewer of another family or a human sample would test the count further.
- **Pages read.** Handwritten documents in the first pass were read from their first and last pages; the 124
  re-read records were read from up to eight pages. ProQuest's scans come from microfilm, and several first or last
  frames belong to a neighboring document; the readers flagged those cases in the note. A presidential endorsement on
  an unread middle page would be missed.
- **Covered dates.** The 81 orders on covered dates rest on one reader's comparison with the census entries of the
  same date. An order the census holds under a date more than a week away from ProQuest's can be counted as missing,
  as with Jackman Creek, and some of the 81 may be such cases.
- **Date checks.** The readers report several ProQuest dates that differ from the page, for example a
  1894 order filed under 1891. Those are in the notes but have not been checked.
- **Definition.** Letters of instruction (367), orders a Secretary signed by command (171), appointments and fund
  approvals are excluded. Counting them is a ruling for the owner (Kean A-20261124-3).
- **Accidental download.** Navigating a browser tab to a ProQuest PDF link makes Chrome download the file, because
  Chrome's built-in PDF viewer is turned off. One file, `PT1-1838-12-25.pdf`, was downloaded that way to the owner's
  computer early on. Every other PDF was fetched inside the page script.
