# Reading the documents behind the 3,941 ProQuest records missing from the census (2026-11-24)

Coordinator: Claude (Opus 5.5), in the owner's Chrome through NYU's ProQuest subscription, at the owner's request
and with his permission to fetch the documents. The reading of document text and page images was delegated to
Claude Haiku.

## Conclusion

The documents behind 3,939 of the 3,941 records were fetched and read: 2,687 from their text, 1,223 from images of
their pages, and 29 that proved unreadable. **2,032 are executive orders on their face, and the census lacks every
one of them.** They are 1,531 land orders and 501 other operative orders signed, approved or issued by the
President. Another 70 are land-order files whose order page cannot be read; every such file checked by eye
contained the order.

The other 1,808 documents are not executive orders: 451 actions on one person, 366 letters of instruction, 247 other
letters, 172 fund approvals, 171 orders a Secretary signed "by command of the President," 132 appointments, 70
proclamations, 32 pardons, 17 treaties and 150 others.

| Era | Land orders | Other operative orders | Land files, order not readable | Not executive orders | Unreadable or no PDF |
|---|---:|---:|---:|---:|---:|
| 1789-1861 | 75 | 80 | 2 | 497 | 21 |
| 1862-1906 | 237 | 373 | 32 | 818 | 8 |
| 1907-1936 | 1,219 | 48 | 36 | 493 | 2 |
| **All** | **1,531** | **501** | **70** | **1,808** | **31** |

The census's identified unnumbered series is 1,405 to 1,816 orders. These 2,032, or about 2,100 with the probable
land files, would more than double it.

Examples include:

- Van Buren's transfer of $500,000 to the Mint (July 20, 1838).
- Lincoln's order making Arkansas one revenue collection district (March 1, 1865).
- Grant's order for a new census of New York City (1870).
- Arthur's consolidations of North Carolina and Wisconsin revenue districts.
- McKinley's Philippine government orders of 1899 to 1901.
- Taft's coal-land restorations.
- Harding's order vacating Alaskan Withdrawal No. 1 (May 19, 1921).

Of the 501 operative orders, 339 carry the President's signature, 82 his approval, and 49 are issued in his name.
22 show no presidential act, 6 a Secretary's signature only, and 3 cannot be read.

## Method

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

## Limits

- **Reader error.** The readers agreed with Claude's own judgments for 36 of 40 documents across both modes, so a
  few hundred of the 3,939 judgments may be wrong in either direction. In a spot check of 15 text verdicts of
  "operative order", 2 were doubtful. In a spot check of 6 image verdicts of the same kind, all were correct; one
  was Lincoln's March 1, 1865 order for Arkansas.
- **Pages read.** Only the first and last page of each handwritten document were read. ProQuest's scans come from
  microfilm, and several first or last frames belong to a neighboring document; the readers flagged those cases in
  the note. A presidential endorsement on a middle page would be missed.
- **Date checks.** The readers report several ProQuest dates that differ from the page, for example a
  1894 order filed under 1891. Those are in the notes but have not been checked.
- **Definition.** Letters of instruction (366), orders a Secretary signed by command (171), appointments and fund
  approvals are excluded. Counting them is a ruling for the owner (Kean A-20261124-3).
- **Accidental download.** Navigating a browser tab to a ProQuest PDF link makes Chrome download the file, because
  Chrome's built-in PDF viewer is turned off. One file, `PT1-1838-12-25.pdf`, was downloaded that way to the owner's
  computer early on. Every other PDF was fetched inside the page script.
