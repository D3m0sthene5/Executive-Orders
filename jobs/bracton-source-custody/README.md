# Bracton source custody: four fixed APP captures

`output/captures/` contains the exact HTML response bodies from four Common Crawl
WARC records already named in `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl`.
Each body was re-fetched through Cotton's `fetch_capture`, checked against the
recorded target URL, and SHA-256 checked against its frozen source reference.
`output/PROVENANCE.jsonl` records the WARC filename, byte range, and capture time.
`output/SOURCES.jsonl` registers the retained bytes with the existing claim
checker. These are APP editorial transcriptions, not original Executive Orders.

The public Federal Register and National Mediation Board PDFs for the two
Bracton packets were independently re-fetched and hash-checked into local job
caches. Those caches are not committed in this staging change. A fresh checkout
must acquire those exact bytes before an offline dispatch check can pass.

No legal finding, provisional status, claim, or human review is made here.
