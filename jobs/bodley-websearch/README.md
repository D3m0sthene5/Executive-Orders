# Bodley web pass: search the web, by name, for every order without an official copy

Owner-requested one-off (2026-11-11). Every order whose tracker blockers include `NO_OFFICIAL_SOURCE_LOCATED`,
`ONLY_COMPILED_TRANSCRIPTION_FOUND` or `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` is searched once through the shared search
layer (`jobs/_lib/eo_websearch.py`): free engines first, then the owner's paid Brave Search API when the free ones
found nothing worth reading. Google's own API is closed to new customers, so Brave stands in for "Google it".

Owner rulings applied (2026-11-11): the per-run paid limit is lifted to the per-job lifetime limit (2,500) for this
pass; a keyed paid API whose robots.txt answers 401/403 is treated as RFC 9309 "unavailable" (allowed), while an
explicit Disallow still blocks.

Outputs: `WHERE_FOUND.csv` (one row per order: best URL, score, every host it appeared on), `WEB_LEADS.csv`,
`WEB_HITS.csv`, `WEB_STATE.json`, `PAID_SEARCH.json` (the spending ledger), `REPORT.md`. Leads only.

Run: `gh workflow run run-jobs.yml --ref <branch> -f job=bodley-websearch -f only=true`
