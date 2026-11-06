# B2 report: identity class catalogued_unnumbered (owner ruling R10)

Branch `claude/dorotheus-b2`. No numbered-series count changed. Nothing pushed. The codebook, claim files, provisional statuses, ProQuest paths and `pinakes-proquest-ingest` were not touched.

## What changed, file by file
- `jobs/domesday-register/unnumbered.py` (new): builds the seed, deduplicates Lord rows against the completeness clusters, computes the capture-recapture estimate, writes outputs and the targets file. `python3 -I unnumbered.py --rebuild-seed` (with `REPO_ROOT`) regenerates the seed.
- `jobs/domesday-register/data/UNNUMBERED_SEED.csv` (new): 1,562 rows `seed_id,lord_page,date,date_certainty,subject,cluster_id`. Dates: 699 day, 1 month, 862 year. 1,158 rows carry a completeness cluster id; 404 (years 1900-1941) have none because the cluster list reads nothing after 1899. Subject is whitespace-normalised and cut to 300 characters.
- `jobs/domesday-register/register.py`: `main()` also calls `unnumbered.run` (outputs `UNNUMBERED.csv`, `UNNUMBERED_SUMMARY.json`, `TARGETS_NON_LORD_RESIDUE.txt`). `job.py` runs `test_unnumbered` as well. `needs.txt`, `triggers.txt` and `after.txt` (adds `census-completeness`, no cycle: checked over all 41 `after.txt` files) updated.
- `jobs/domesday-register/test_unnumbered.py` (new, 10 tests).
- `jobs/readiness-tracker/tracker.py`, `inputs.txt`, `test_tracker.py`: new summary keys `numbered_series_orders` (= `orders_total`), `unnumbered_series_observed`, `unnumbered_series_estimate_95` (null until the domesday output exists), read from the committed `jobs/domesday-register/output/UNNUMBERED_SUMMARY.json`. TRACKER.md headline is now "Numbered series: ready for human review X of N" with an unnumbered line beneath. One new test. Domesday runs after the tracker (its `after.txt`), so the tracker reads the previous committed output; adding domesday to the tracker's `after.txt` would create a cycle.
- `jobs/daily-digest/dashboard.py`: new `unnumbered_series` report block and a table row (optional input outside `PATHS`, so a missing file is not an input problem). The digest headline is the first 18 lines of TRACKER.md, so it carries the new line with no digest change.
- `jobs/gessner-cards/build_cards.py`, `template.html`, `test_build_cards.py`: summary adds `numbered_series_orders` and unnumbered fields; the lede states the second denominator; the title says "numbered".
- `README.md`: one "Two denominators" line under the dashboard line.
- `jobs/clark-discovery/targets.txt`, `jobs/census-candidates/targets.txt` (new, identical): 487 residue ids under a comment header. **Neither job reads `targets.txt` today; I did not rewire them.**

## Dedup rule (documented in `unnumbered.py`)
Lord row + cluster mention = one identity iff both dates are day-precise and equal AND they share at least 2 distinctive words (5+ letters, not on the completeness stop list; the tokens are the ones in `MENTIONS.csv`). Month- or year-precise Lord dates never merge. Same-date pairs with fewer than 2 shared words stay separate. The completeness job's own rule is looser (1 word, or 2 words on year-only dates, or a page citation). Non-Lord mentions keep the completeness grouping among themselves. Lord rows reaching the same group join (17 Lord rows folded into another Lord identity).

## Counts (run on the main checkout's committed inputs)
- 2,334 identities observed: 1,545 hold a Lord row, 789 are cluster-list only, 117 are on both lists. Firm EO:UN census matches: 0 (the one Lord-derived census id, `EO:UNN:LORD1944:p1:1863-03-10`, matches no Lord row; the 18 NARA EO:UN rows have no title, and a date alone is never a match).
- Capture-recapture, 1789-1899, day-precise identities: n1=459, n2=879, m=117, observed union 1,221; Chapman N=3,429.5, 95% interval 2,988-3,982. Total for the unnumbered series is reported as 2,334 observed (lower bound), 95% interval **4,101-5,095** (Chapman interval plus every other observed identity taken as observed only). Overlap years: 1789-1899, because the cluster list reads no source after 1899.
- By era: 1789-1861 N=399 (299-572); 1862-1899 N=2,959 (2,548-3,482).
- **The estimate is very sensitive to the matching threshold**: at 1 shared word N=2,601 (2,326-2,942, m=150); at 3 words N=8,568 (6,690-11,102, m=48). The interval covers sampling error at the chosen threshold of 2 only. Assumptions (closed population, independence, equal catchability, correct matches) are written into the summary with the direction of each bias; Lord cites the printed sources, so independence fails and N is likely under-stated, while OCR failures to match push the other way.
- 68 Lord rows sit in clusters that hold a numbered-series mention; they keep their unnumbered identity but are left out of the estimate (as the completeness job leaves those clusters out).
- Targets: 789 cluster-only identities; 302 are left out of the targets because their cluster contains a Lord row that failed the stricter rule (may be Lord's); 487 written.

## Tests
- `jobs/domesday-register`: 13 tests OK (3 existing + new). `jobs/readiness-tracker`: 56 OK (55 existing unchanged + 1 new). `jobs/gessner-cards`: 6 OK. `jobs/daily-digest`: 19 OK. `jobs/clark-discovery`: 20 OK. `jobs/census-candidates`: 2 OK. `python3 .github/scripts/test_pick_jobs.py`: 23 OK (1 skipped).
- Tracker comparison (`REPO_ROOT=/home/user/Executive-Orders OUTPUT_DIR=/tmp/claude-0/b2-tracker`): `ready_for_human_review` 1,368 = 1,368, `orders_total` 14,972 = 14,972, `orders_with_provisional_status` 4,291 = 4,291; no other pre-existing summary key differs (only the three new keys, null).

## Exceptions
- Job outputs under `jobs/domesday-register/output/` are not committed by me (CI produces them); until it runs, the tracker, dashboard and Gessner show the unnumbered series as "not measured yet". The numbers above come from a local run.
- Seed date of CU:911 is printed "July 37" in the source; recorded as `1891-07` (month), not an invented day (the Justinian seed has `1891-07-37`).
- Seed text for the 404 rows from 1900 on differs trivially from the Justinian seed only in whitespace handling; no row of mine contradicts its date, page, or cluster id except CU:911.
- The daily-digest `after.txt` was not changed (it reads committed output).
- The daily-digest and Gessner tests need `research/progress` in the checkout (sparse paths added locally only).
