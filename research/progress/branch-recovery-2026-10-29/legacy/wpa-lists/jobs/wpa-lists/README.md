# WPA lists of executive orders (census backbone before 1938)

Two federal Works Projects Administration finding aids, supplied by the owner as PDFs on
2026-10-17. The PDFs are kept under Git LFS in `releases/source_books/`; their text layers
are committed in `data/` with hashes in `data/PROVENANCE.json`.

| Book | Covers | Pages |
|---|---|---|
| *Presidential Executive Orders*, vol. 1: List (Historical Records Survey, New York, 1944; Google Books scan) | Numbered orders 1-8030, 1862-1938 | 695 |
| Clifford L. Lord, ed., *List and Index of Presidential Executive Orders, Unnumbered Series* (New Jersey Historical Records Survey, 1943; HathiTrust, University of Michigan copy) | Unnumbered orders, 1789-1941 | 433 |

Each entry gives the order's date, a one-line summary and, often, where its text is
printed: Civil Service Commission reports (CSR, CSA), General Land Office reports (GLO),
War Department military reservation lists (MR), Commissioner of Indian Affairs reports
(CIA), Kappler, Richardson's *Messages and Papers*, the Statutes at Large, and early CFR.

## Outputs

| File | Contents |
|---|---|
| `NUMBERED_ENTRIES.csv` | Every numbered entry: id, date, page, family hint, printed sources, summary |
| `NUMBERED_CENSUS_CROSSCHECK.csv` | Every census order numbered 1-8030: found in the list or not, year agreement, page, sources, summary |
| `WPA_ORDERS_NOT_IN_CENSUS.csv` | Listed orders the census does not hold (possible gaps, or OCR misreads) |
| `UNNUMBERED_ENTRIES.csv` | Every unnumbered entry: year, date (only when the date column pairs one-to-one with the entries), page, family hint, sources, summary |
| `UNNUMBERED_BLOCKS.csv` | Per year-block date and entry counts; `paired` false means the dates were not assigned |
| `SUMMARY.json` | Counts, coverage, families, printed-source kinds |

**Measured 2026-10-17:**
- Numbered list: 8,437 entries. 99.4% of the census's numbered orders 1-8030 were found (8,427 of 8,479); 55 have year disagreements, and 5 listed orders are not in the census.
- Unnumbered list: 1,562 entries for 1789-1941, 700 of them with a confidently paired date. The census holds only about 20 unnumbered identities today.

**Known limit, and the next step.** The unnumbered book prints a column of dates beside
the entries. Plain text can't always line the two up (multi-line entries, page breaks), so
an unpaired block keeps its year and gets no date rather than a guessed one. Pairing by
position on the page (pdfplumber word coordinates of the date column against each entry's
first line) should date nearly all of them. This belongs to the census identity engine.

Family hints are keyword groupings for the rule library (for example
`civil_service_individual`, `military_reservation`, `land_withdrawal`), not classifications.
Census leads only: no identity is admitted, merged or changed by this job.
