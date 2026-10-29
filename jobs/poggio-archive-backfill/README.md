# poggio-archive-backfill (Poggio)

Named for Poggio Bracciolini (1380-1459), who recovered lost classical texts from monastery archives.

The American Presidency Project (APP) texts of 516 orders were harvested live from the APP site and have no archive
capture. A live page changes, so its hash cannot be re-proven, and every claim citing one fails custody. This job runs
the archive-only backfill phases of `jobs/app-executive-orders/app_mirror.py` (`seed`, `backfill-index`,
`backfill-documents`) for the ids in `data/LIVE_ONLY_IDS.txt`, reading only Common Crawl and the Wayback Machine.
`app_mirror.py` refuses every other host, including on redirects, and blocks DNS for presidency.ucsb.edu, so this job
can never request the APP site. Output rows are new MIRROR_* records in this job's own output; the identity check
(listing number equals page heading number) is kept. `jobs/cotton-capture-custody` reads them directly; merge them
into the APP job with `app_mirror.py merge --from jobs/poggio-archive-backfill/output` when convenient.
See `jobs/app-executive-orders/CHANGE_NOTES.md` for details, estimates and risks.
