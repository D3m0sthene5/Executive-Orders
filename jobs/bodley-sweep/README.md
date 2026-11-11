# Bodley: sweep of large public collections for executive orders

Named for Thomas Bodley, who rebuilt Oxford's library from copies gathered wherever they could be found.

Owner-requested (2026-11-11) after Wikimedia Commons turned out never to have been swept. One thread per site, run
concurrently, each at its own low rate and only where the site's robots.txt allows:

| Site | What is read |
|---|---|
| Wikimedia Commons | executive-order and NARA RG 11 categories (depth 4), six file searches, file metadata |
| Internet Archive | scrape API over ten title, subject and creator queries |
| Library of Congress | loc.gov JSON search, five queries |
| Google Books | public full-view volumes only, seven queries |
| HathiTrust | catalog search, full-view filter (robots-checked; never the full-text or page servers) |
| Wikidata | items whose class is an executive-order class, with scan, Wikisource, full-text and image links |

Metadata only: no image or book bytes are downloaded. Each hit's executive-order numbers are parsed and matched to
`READINESS_BY_ORDER.csv` and the Dagron Film 709 manifest.

Outputs: `SUMMARY.json`, `REPORT.md`, `ORDERS.csv` (one row per order number with a lead), `VOLUMES.csv` (books and
scanned volumes, which may hold many orders without naming them in the title), and `<site>/LEADS.jsonl`.

Not covered, and why: DPLA (needs an API key), the NARA Catalog (already read in full from its AWS export,
F-20261106-mabillon-nara), FamilySearch (sign-in only; the owner checks by hand), HeinOnline and ProQuest (licence
bars automation), govinfo and the Federal Register (already used by other jobs).

Run: `gh workflow run run-jobs.yml --ref <branch> -f job=bodley-sweep -f only=true`
