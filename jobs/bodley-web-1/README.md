# Bodley web pass: search the web, by name, for every order without an official copy

Five shards run side by side (`bodley-web-1` .. `bodley-web-5`, orders by number mod 5), each batched and checkpointed every 50 orders, stopping new work at 4.5 hours so every run publishes; the next run continues. Each shard may send up to 500 paid queries per run (2,500 across the five, the approved limit for this pass).

Owner-requested one-off (2026-11-11). Every order whose tracker blockers include `NO_OFFICIAL_SOURCE_LOCATED`,
`ONLY_COMPILED_TRANSCRIPTION_FOUND` or `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` is searched once through the shared search
layer (`jobs/_lib/eo_websearch.py`): free engines first, then the owner's paid Brave Search API when the free ones
found nothing worth reading. Google's own API is closed to new customers, so Brave stands in for "Google it".

Owner rulings applied (2026-11-11): the per-run paid limit is lifted to the per-job lifetime limit (2,500) for this
pass; a keyed paid API whose robots.txt answers 401/403 is treated as RFC 9309 "unavailable" (allowed), while an
explicit Disallow still blocks.

Outputs: `WHERE_FOUND.csv` (one row per order: best URL, score, every host it appeared on), `WEB_LEADS.csv`,
`WEB_HITS.csv`, `WEB_STATE.json`, `PAID_SEARCH.json` (the spending ledger), `REPORT.md`. Leads only.

Run: `gh workflow run run-jobs.yml --ref <branch> -f job="bodley-web-1 bodley-web-2 bodley-web-3 bodley-web-4 bodley-web-5" -f only=true`
