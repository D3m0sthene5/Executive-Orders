# Reading the documents behind the 3,941 ProQuest records missing from the census (2026-11-24)

Coordinator: Claude (Opus 5.5), in the owner's Chrome through NYU's ProQuest subscription, at the owner's request
and with his permission to fetch the documents. Model reading of document text was delegated to Claude Haiku.

## Conclusion

The documents behind 3,939 of the 3,941 records were fetched, and the text of 2,687 could be read. Of those,
**1,507 are executive orders on their face**: 1,311 land orders and 196 other operative orders. Another 70 are
land-order files in which the order page cannot be read. Every such file that was checked by eye turned out to
contain the order.

The other 1,110 readable documents are not executive orders. They are:

- letters and letters of instruction;
- actions on one person;
- orders a Secretary signed "by command of the President";
- fund approvals, appointments, proclamations, pardons and treaties.

The 1,254 handwritten or illegible documents, almost all from before 1907, could not be read as text. Applying the
rates seen in readable documents of the same era and title kind gives about 375 more executive orders among them.
Applying the rate seen when handwritten pages were read by eye gives about 630.

**The census therefore lacks about 2,000 executive orders from this collection, between roughly 1,950 and 2,200.**
About 1,500 of them are land orders, most from 1907 to 1936.

## Method

1. **Fetching.** Each record's PDF was fetched inside the ProQuest page from ProQuest's own document link, using the
   address pattern `$2fPT1-<accession>` or, for 133 records of 1874 to 1879 and 1929, `$2f<accession>`. Two records
   have no PDF at either address.
2. **Text.** ProQuest's PDFs carry an invisible text layer made by optical character recognition (OCR). A browser
   script extracted it. The full text of every document is saved in `PQ_TEXT_LAYER_3941.jsonl.gz`.
3. **Legibility.** A document counts as unreadable when fewer than 8% of its words are common English words. That
   happens with handwriting, which the OCR cannot read. 1,019 documents fall below the line.
4. **Order-language rule.** A record whose title marks it as a land order and whose text contains order language
   ("hereby withdrawn", "hereby restored", "it is hereby ordered", "Order of Restoration" and the like) was counted
   as a land order without further reading. 838 records qualify. All 9 of them in the hand-read sample are land
   orders.
5. **Model reading.** The remaining 2,082 documents went to six Claude Haiku readers, about 350 each. Each reader
   got an excerpt of up to about 2,600 characters: the opening, the passages around order language, and the end.
   The readers classified each document under a fixed rubric (`READER_RUBRIC.md`), quoting evidence from the text.
   They marked 233 documents illegible.
   - A 60-document probe run first. On 37 documents that Claude had judged by reading the scans, the probe agreed
     on whether the document is an executive order for 31. The disagreements were land files whose order page sat
     in the part of the text the excerpt left out, so the excerpt was then rebuilt around order language.
   - In the full run, the readers agree with the scan judgments for 26 of 28 documents.
   - Readers' tokens: 1,486,842 (probe 170,865; six readers 1,315,977). The six readers ran in parallel in about
     18 minutes.
6. **Land files without a visible order.** Land-titled records that a reader called a letter or "other" are listed
   as probable land orders (70). In the hand-read sample, all five such files contained a signed order on a page the
   OCR could not read.

Results for every record are in `FULL_READING_3941.csv`, which gives the kind, presidential act, date on the
document, evidence and note for each record. The earlier hand reading of 50 random records, from page images where
needed, is in `RESULTS.csv` and `SAMPLE_50.csv`.

## Results

| Era | Land orders | Other operative orders | Land files, order not readable | Not executive orders | Not readable |
|---|---:|---:|---:|---:|---:|
| 1789-1861 | 4 | 20 | 2 | 248 | 401 |
| 1862-1906 | 136 | 136 | 32 | 424 | 740 |
| 1907-1936 | 1,171 | 40 | 36 | 438 | 113 |
| **All** | **1,311** | **196** | **70** | **1,110** | **1,254** |

The readable documents that are not executive orders break down as follows:

| Kind | Documents |
|---|---:|
| Action on one person | 239 |
| Letter of instruction | 216 |
| Other letter | 150 |
| Other | 126 |
| Order signed by a Secretary by the President's command | 118 |
| Fund approval | 89 |
| Appointment | 75 |
| Proclamation | 60 |
| Pardon | 20 |
| Treaty | 17 |

Of the 196 operative orders:

| Presidential act shown | Orders |
|---|---:|
| Signed by the President | 108 |
| Approved by the President | 42 |
| Issued in his name | 19 |
| No presidential act visible | 21 |
| Signed by a Secretary only | 5 |
| Illegible | 1 |

The operative orders include:

- McKinley's Philippine and Cuban government orders of 1899 to 1901.
- Roosevelt's 1902 order for a census of the Philippines.
- An "Executive Order" of September 1, 1911 naming a board on wireless telegraphy in the Philippines.
- Lincoln's additional instructions to the South Carolina direct-tax commissioners (December 31, 1863).
- Arthur's and Cleveland's consolidations of revenue districts.

## Limits

- **Unread documents.** The 1,254 unreadable documents are estimated, not read. Reading them would mean viewing
  page images, about 1,250 documents and several thousand pages. The two estimates for them differ by about 250.
- **Reader judgments.** The readers worked from excerpts and OCR errors. Their agreement with the scan judgments,
  26 of 28, leaves room for a few hundred misjudgments across 2,000 documents. A spot check of 15 operative-order
  verdicts found two doubtful ones: a flag order signed by the President's secretary, and census regulations with
  no visible presidential act.
- **Definition.** Letters of instruction (216), orders signed by a Secretary by command (118), appointments and
  fund approvals are excluded. Including them is a ruling for the owner (Kean A-20261124-3), and it would add
  several hundred documents.
- **Accidental download.** Navigating a browser tab to a ProQuest PDF link makes Chrome download the file, because
  Chrome's built-in PDF viewer is turned off. One file, `PT1-1838-12-25.pdf`, was downloaded that way to the owner's
  computer early on. Every other PDF was fetched inside the page script.
