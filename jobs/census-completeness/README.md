# Census completeness: how many early orders have the lists not found?

Nobody can prove that the search for 1789–1899 executive orders is exhausted. What can be measured is how
well the independent enumerations the project holds overlap, and from that overlap how many orders
none of them has seen. This job does that measurement and keeps a series-level map of where orders
could still be and what has been searched.

## Lists read

| List | What it enumerates | Independence |
|---|---|---|
| `LORD` | Lord's 1943 unnumbered list, 1789–1899 (`wpa-lists` parse or the committed subset) | The backbone. Lord cites the GLO, MR, Indian-reservation and Richardson volumes as his sources, so he is **not** independent of them |
| `WPA` | The numbered series 1862–1899 (105 entries) | Disjoint from Lord by design; kept for the 1862–1899 picture |
| `RICH_VI`, `RICH_VII`, `RICH_IX` | Documents in Richardson's *Executive Orders* sections, split by `richardson-volumes` | Richardson copied department records and newspapers; Lord cites him |
| `IR1912` | Orders in *Executive Orders Relating to Indian Reservations* (GPO 1912), split by `indian-reservations-1912` | Lord cites it |
| `MR_*`, `GLO_*` | Dated "Executive order" mentions read from the reservation and land-office books `early-orders-hunt` fetched | Lord cites them |

Two kinds of cross-list match are kept apart. A **citation link** is one the earlier job already made
from Lord's page citation. A **blind match** needs the same day-precise date and at least one shared
distinctive word (two words for a year-only Lord entry); a date alone never matches, and same-date pairs
with no shared word are written to `AMBIGUOUS_MATCHES.csv`. Estimates are reported on both.

## Estimators

- **Lord's coverage of each list**: of the orders a list names, the share Lord also names, with a Wilson
  interval. The most direct miss rate.
- **Chapman (Lincoln–Petersen)**: the two-list population estimate from Lord and each other list.
- **Chao1**: the all-lists lower bound from the counts of orders seen in exactly one and exactly two
  lists, with Chao's log-normal interval.

All three assume independent captures. Lord drew on these books, so the dependence is positive and
every estimate here **under-states** the undiscovered remainder. The assumptions and the direction of
each bias are written into `ESTIMATES.json` and `REPORT.md` with the numbers. Orders that never
reached a printed compilation are invisible to every list here and cannot be counted by overlap; that
remainder is what the archival audit below is for.

## Outputs

`MENTIONS.csv` (every dated mention, its tokens and citation links), `MATCHES.csv`,
`AMBIGUOUS_MATCHES.csv`, `CLUSTERS.csv` (one row per presumed distinct order with its capture
history), `OVERLAP_MATRIX.csv`, `RICHARDSON_COVERAGE_BY_SIGNER.csv` (what Lord listed of each
Richardson volume, by signer), `ESTIMATES.json`, `COVERAGE_BY_SERIES.csv` (the source universe map
with this run's counts), `REPORT.md` (the completeness claim in its defensible form), `SUMMARY.json`.

## The source universe map and the archival audit

`data/SOURCE_UNIVERSE.csv` lists every archival and printed series that could hold an order, by era,
with repository, access route, whether it is digitized, and its search status in this project:
`searched_to_end`, `sampled`, `planned`, `not_searched`, `inaccessible_online`. The completeness claim
is only as strong as the rows that are not `searched_to_end`.

The step no job can do is the **random archival audit**: draw a random sample of cells (for example
sixty random months of War Department letters received, 1801–1861), read each exhaustively, and count
order-like documents absent from the census. That gives a measured miss rate for everything upstream of
the printed compilations. Draft reference and scan-request emails for the series involved are in
`research/plans/SCAN_REQUESTS_2026-10-18.md`; they are drafts for the owner to check and send.

## Running

GitHub: Actions → Run jobs → `census-completeness` (it runs after `early-orders-hunt`,
`richardson-volumes` and `indian-reservations-1912`). Locally:

```sh
OUTPUT_DIR=/tmp/cc REPO_ROOT=. COMPLETENESS_BOOKS_DIR=jobs/early-orders-hunt/output/books python jobs/census-completeness/job.py
```

Tests (`test_complete.py`) check the estimators against textbook values, the matcher's refusal to match
on a date alone, and recovery of a synthetic hidden population of 400 orders within the intervals.

## Measured 2026-10-18 (first local run, books from the hunt's first six fetches)

2,553 dated mentions from 11 lists; 2,297 cross-list matches (1,066 blind by date and word, 901 by year
and two words, 330 citation links); 1,215 same-date pairs left unmatched. 1,394 distinct unnumbered
orders dated 1789–1899 observed, 57 numbered clusters set aside.

| Era | Observed | Mt total (95% CI) | Undiscovered, strict | Undiscovered, same-date pairs as matches |
|---|---:|---|---:|---:|
| 1789–1800 | 7 | too few lists | – | – |
| 1801–1861 | 213 | 316 (269–362) | 103 | 43 |
| 1862–1899 | 1,174 | 1,729 (1,634–1,825) | 555 | 295 |

Read these as: *of the kinds of orders these printed sources catch*, the lists together have probably
missed somewhere between a fifth and a third more than they hold for 1801–1861, and the same order of
magnitude for 1862–1899, before allowing for the dependence that makes every number here a lower bound.
Lord lists only 31 % of the president-signed documents in Richardson's Civil War volume and 51 % in the
Harrison–Cleveland volume, so the Richardson gap is where a reviewer should look first. The land-office
schedule rows are OCR tables whose names sit lines away from the date, so many of their "unmatched"
mentions are matcher failures, which is why the bracket is wide; `AMBIGUOUS_MATCHES.csv` (260 pre-1862
pairs involving Lord) is the list to settle to narrow it.

Nothing here admits an order, assigns a date, merges identities, or changes a status, the ledger, the
codebook or any count. The estimates describe the population, never a case.
