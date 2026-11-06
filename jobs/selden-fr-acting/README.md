# Selden FR acting: Federal Register pages of later non-EO instruments that act on an order, 1936-1993

Part of Selden (see `jobs/selden-fr-citers/README.md` for the name). For each later instrument that the finding
jobs name as ending or changing a census order, and that is **not** an executive order (Public Land Orders above
all; also Canal Zone orders, agency regulations and reorganization plans printed in the Federal Register), this job
holds the official Federal Register page and locates the sentence that cites the order. It costs no model tokens.

**Wanted list** (built each run, `WANTED.jsonl`): edges in `jobs/later-events/output/EDGES.csv` and
`jobs/shepard-citations/output/EDGES.csv` with an ending or modifying relation, a census target and a Federal
Register citation in volumes 1-58 (1936-1993), from BLM's PLO table or the printed label. On 2026-11-05: 827 pages
(807 PLOs) acting on 620 orders. Executive orders as acting instruments are the order-originals lane and are left out.

**Route.** govinfo's link service (`/link/fr/<vol>/<page>`) names the daily-issue PDF and usually a page hint; the
issue is downloaded through `jobs/_lib/fetch_pool.py` (robots.txt, at most 4 requests in flight, 0.25 s apart,
sha256 of every body); its pages are read and the instrument found with `jobs/fr-pages/frpages.py` (source-ladder's
printed-page locator; a window around the page hint first, the whole issue only if that fails); the issue's SHA-256
is compared with the one GPO publishes in the package's PREMIS record (`jobs/official-fixity/fixity.py`); then the
sentence citing each target is located with `jobs/selden-common/selden_common.py`. Pages that `jobs/fr-pages`
already holds are read from its committed text with no request.

**Custody.** Two source records per page: the issue (`fr-issue:`; issue sha256, `gpo_premis_match`, the
instrument's page text in `text_path`; bytes not committed, so the claim checker accepts it as
`gpo_published_hash_match` once `official-fixity` has listed it), and, up to 1.5 MB each and 80 MB a run, a
deterministic pypdf extract of just those pages (`fr-extract:`, committed under `captures/`, re-hashable as
`held_bytes_verified`). Fragments cite the extract when there is one, otherwise the issue.

**Outputs.** `SOURCES.jsonl`, `FRAGMENTS.jsonl` (`later_event_candidates` with exact `quote_span` into the page
text), `LOCATED.csv` (every wanted pair, located or not), `texts/FR_<vol>_<page>.txt`, `captures/`, `WANTED.jsonl`,
`FAILURES.jsonl`, `CONTROLS.json`, `SUMMARY.json`.

**Planted controls.** Positives: PLOs whose subject in BLM's table (independent of the page OCR) names an order by
number with an ending or modifying word; the page text must cite that order. Negatives: near-miss numbers and
another page's target, which must never be located. One false location writes every fragment as `cross_reference`.

**Limits.** OCR text; machine location of the page and the sentence; a reserve or a date cited without a number is
not located (it shows as `located: false` in `LOCATED.csv`). Leads only: no status, census, codebook or count
change. Merging registers the output with the claim kit (it reads every `FRAGMENTS*.jsonl`), which waits for the
owner. Certified: 0.

**Running.** On a push to this folder or by hand; after `shepard-citations`, `later-events`, `fr-pages`. Budget:
`JOB_MAX_REQUESTS` 3,000, `JOB_TIME_BUDGET_MIN` 130 (later runs continue), about 15 GB of issue downloads for the full list (1980s issues
are 30-100 MB). Tests (`test_acting.py`, offline) run first.

## Overlap with Ptolemy and Pothier (checked 2026-11-06, `research/selden/tools/overlap.py`, `research/selden/census/OVERLAP.json`)

74 of the 1,360 source records name a daily-issue URL that is also on Ptolemy's request list (`jobs/ptolemy-custody/REQUESTS.jsonl`), with the same sha256; none is in Pothier's sources. Later runs carry every held page or text forward with no request, so none of these is fetched again.
