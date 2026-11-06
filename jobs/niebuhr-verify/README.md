# Niebuhr verify

Checks the Niebuhr searchers' work (`research/niebuhr/`). For every source a searcher reported, the runner fetches the page
(robots.txt obeyed), keeps the sha256 and size of the bytes and the page as text (`output/pages/`), and tests whether the
searcher's quote is on the page (`VERIFY.csv`: exact, partial with the share of its words found in order, or no). It also
runs `research/niebuhr/corroborate.py`, which checks each result against the WPA indexes of numbered (1944) and unnumbered
(1943) orders the project already holds (`CORROBORATION.csv`).

A fetched page with a matching quote shows only that the page says what the searcher reported. Nothing here authenticates
an order, admits it to the census, or changes a count or grade.

Runs when files in `research/niebuhr/results/` change. Budget: `JOB_MAX_REQUESTS` (default 1,500).
