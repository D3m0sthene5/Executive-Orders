# Lane A report: numbered-series catalog cross-check (Sonnet worker, 2026-11-24)

Worker: Claude Sonnet subagent, about 143k tokens, 22 tool calls, about 5 minutes of measured wall time (the worker
estimated 15). The worker's report is reproduced here by the coordinator, because subagents cannot write report files.

## Outputs

- `crosswalk.py`, run with `python3 -I`. It takes about 1 second, and two runs gave identical SHA-256 hashes for
  the CSV and the JSON.
- `NUMBERED_CROSSWALK.csv`, with 15,006 rows: 14,983 numbered labels in the census, 20 whole numbers absent from it,
  and 5 labels that something names but the census lacks, less the overlap between those groups.
- `SOURCES.csv`: path, SHA-256, rows, coverage and independence for each listing.
- `EXCEPTIONS.csv`: 2,417 labels named by no independent listing or by only one, each with a reason.
- `ABSENT_NUMBERS.csv`, `DATE_CONFLICTS.csv` and `SUMMARY.json`.

## Listings found on disk

- **WPA 1944 numbered list** (Lord, *Presidential Executive Orders, Numbered 1-8030*):
  `jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv`. It covers EO 1 to 8030, and its hash matches the one recorded
  for the unmerged wpa-lists branch.
- **Office of the Federal Register catalog:** `jobs/fr-originals/data/ofr_index/fedreg_bulk_01..07.json.gz`. It covers
  EO 7532 to 14435, with 6,937 distinct labels.
- **ProQuest:** only the owner's list of 2,765 links (`SUPPLIED_LINKS_RECONCILED.csv`) plus 2,750 PDFs. This is a partial
  sample of the 9,503 numbered records ProQuest says it holds. Ten listed labels (for example EO 8302 and 9457) are
  numbered after 7531, outside the list's stated pre-1937 range; the worker did not investigate them.
- **Not counted as independent:** the American Presidency Project index, Wikisource, the leads from Civil Service
  Commission reports, and the numbered-early-orders matches.
- **Official printings,** counted together as one family: Hoover Table 2, the Federal Register originals, the OFR Hoover
  compilation, the Isthmian Canal and Indian-reservation books, the GPO bound slip orders, and 6 Civil Service
  Commission printings that passed checks. HathiTrust GPO volumes and Richardson are counted as a second family of
  printed books.

## Headline counts, over the 14,983 numbered labels in the census

- **Independent source families naming each label:** none for 42, one for 2,375, two for 10,002, three or more for
  2,564.
- **Independent catalogs only** (WPA, OFR, ProQuest): none for 90, one for 11,653, two for 3,240, three for none. The
  ranges explain this. WPA and OFR overlap only between EO 7532 and 8030, so numbers 1 to 7531 rest on WPA alone,
  plus the partial ProQuest sample, and numbers above 8030 rest on OFR alone.
- **Pre-1907 orders are the most thinly supported:** 424 of 622 labels have at most one independent listing.
- **30 census labels** are named by no held listing and have no text held (for example EO 21, 106½, 396, 1601,
  3054 and 2539).
- **Whole numbers in 1..14435 absent from the census:** 20 (EO 36-49, 51-53, 92, 2103 and 6585). Only two are named by
  a held listing: EO 2103 by WPA, and EO 6585 by APP and the GPO slip-order volume.
- **Labels something names but the census lacks:** EO 2103, 5151A, 6585, 7010F and 8606A (the last three by APP only).
  No held listing names 130A or 2687A.
- **Date conflicts of more than one day:** 132 of 23,208 listing-to-listing comparisons, and 82 of 31,921 comparisons
  against the census date. Each is a nearest-date test, none is adjudicated, and all 214 detail rows are written.

## Limits

- Which listings count as independent is the worker's judgment. Treating ProQuest and WPA as one source would lower
  the counts.
- Whether an official text is held comes from the register fields and the Photius files, and many of those are still
  machine matches waiting for a page check.
- Some "within WPA range but the WPA parse does not name this label" reasons in `EXCEPTIONS.csv` may be lines the OCR
  of the WPA list dropped.
- The era of an absent number is taken from the neighbouring census label.
