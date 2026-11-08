# Bracton source custody: 81 fixed APP captures

`output/captures/` contains the exact HTML response bodies from 78 Common Crawl
WARC records and three Wayback captures already named in
`jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl`.
Each body was re-fetched through Cotton's `fetch_capture`, checked against the
recorded target URL, and SHA-256 checked against its frozen source reference.
`output/PROVENANCE.jsonl` records each WARC filename and byte range, or the
Wayback capture URL, together with its capture time.
`output/SOURCES.jsonl` registers the retained bytes with the existing claim
checker. These are APP editorial transcriptions, not original Executive Orders.

`output/upstream/` retains eight exact GovInfo eCFR bulk-title XML files and
four exact OLRC release-point ZIP files named in Theophilus source notes.
`output/UPSTREAM.jsonl` records each verified upstream hash. The held CFR and
US Code text extracts match their own hashes, but their extraction from these
raw artifacts has not yet been independently reproduced. These upstream
artifacts are not registered in `SOURCES.jsonl` as substitutes for those
extracts, and they do not establish a current-law predicate or page check.

The public Federal Register and National Mediation Board PDFs for the staged
Bracton packets were independently re-fetched and hash-checked into local job
caches. Those caches are not committed in this staging change. A fresh checkout
must acquire those exact bytes before an offline dispatch check can pass.

No legal finding, provisional status, claim, or human review is made here.
