# clause_inventory — H6-w14

Started 2026-11-05T23:47:58Z, ended 2026-11-05T23:52:38Z.

## EO:4114
- Result: done
- ProQuest PDF page 1 inspected against the OCR layer (text agrees, page 2 is the map diagram); five clauses (establish, name, administration, War Dept use reserved, military laws continue); original_confirmed false because the replica grade is not acceptable_as_original.

## EO:5454
- Result: done
- APP mirror row (node 373034) agrees with the held text on heading, date and text hash; three partial revocations (PSW No.1/PSR No.1, PSR 174, PSR 235); Hathi printed copy agrees in structure.

## EO:2858
- Result: done
- Wikisource text names EO 2858 and the Hammar nickel sale; two clauses (authorization, manner of sale), reasons (a)-(c) treated as non-operative; the register date 1918-05-07 differs from the text's 9 May 1918 and is left for the status/ending steps.

## EO:5757
- Result: done
- OFR OCR text identifies EO 5757 (16 Dec 1931); two clauses (transfer from Madison and Deerlodge to Beaverhead, no-change-of-status disclaimer); the source PDF is a Git LFS pointer so no page image was inspected and original columns are left blank.

## EO:6131A
- Result: done
- APP mirror row (node 376989) agrees on heading, date and hash; three clauses (attach naval surgeons with schedule, call with priority, payroll and funding by EO 6101).

## EO:130
- Result: done
- Wikisource text is a one-paragraph special civil-service rule on Navy yeomen; one clause; no page record exists for Wikisource so pages_confirmed is false.

## EO:29
- Result: done
- ProQuest OCR layer is unusable noise, so I read the handwritten ProQuest page images against the Richardson text (they agree) and inventoried from Richardson; three clauses (30-day mourning and half-staff, suspension of business, honors).

## EO:819½
- Result: blocked:identify EO 819½ and retain its text (no text, date or title is held; the register has the number with suffix ½ only)
- No text held and no title or date in the register; nothing to inventory.

## Sources opened
Bundles HAND/EO_N.json; the held text files named in clauses.csv; ProQuest PT1-1924-EO-4114.pdf and PT1-1893-EO-29.pdf (rasterized, pages viewed); jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl (rows for 5454 and 6131A); FRAGMENTS jsonl files for grades.

## Defects and cautions
- status/ and original_text/ folders in U3 were empty, so there were no earlier proposals to keep or correct.
- releases/source_books OFR (EO 5757) and Richardson v9 PDFs are Git LFS pointers (133 bytes), so their pages could not be inspected; the OFR/Richardson text layers are unverified OCR.
- DOCUMENTS.jsonl had no rows for these orders; only MIRROR_DOCUMENTS.jsonl did.
- clause_id left blank; inventory_source_id uses FILE:<path>@0-<file length> with the clause offsets in inventory_char_start/end (absolute Unicode offsets, file read as UTF-8 without newline translation).
- Splitting choices (e.g. one scope per sentence in EO 5454, naming kept separate in EO 4114) are judgments a reviewer may adjust.
