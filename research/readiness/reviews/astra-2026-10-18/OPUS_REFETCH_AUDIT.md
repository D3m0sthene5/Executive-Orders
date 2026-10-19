# T1: current Opus re-fetch pickup

`reviewer_role: ai_review`. Astra, 2026-10-18 ET. Base
`0d860bde15538d38fafea26cea03f152d0127f5e`.

All 848 nonblank REFETCH_LIST.jsonl rows have nonempty instrument_ids and an HTTPS
URL; zero have empty IDs. There are 696 distinct nonempty expected SHA-256 values.
The current `ladder_queue.opus_refetch_wanted` emits **774 requests, no errors**:
696 hash-keyed files plus 78 URL-keyed files without an expected hash.

The brief's zero-pickup premise is obsolete. Current `jobs/source-ladder/output/log.txt`
says “774 Opus originals to re-fetch”; current job.py actually combines queue_items,
shared and opus before selecting its bounded plan. The current output records ten
new sources, and the plan contains Opus wanted IDs. PR #24 was already merged when
this session checked GitHub (2026-10-19T00:35:22Z).

No duplicate fallback requests were appended: the requested repair is present on
main, and another 696 requests would duplicate its work while losing native expected
hash validation if the hash only appeared in citation prose. No EXHAUSTED line was
written; the one-route EO4314 proposal remains insufficient under the brief.

There is a **summary telemetry defect**: job.py's `items_in_queue` is only
len(queue_items)+len(shared), and it has no Opus count. The current SUMMARY reports
83+90=173 even though the combined queue has 947 request objects before selection.
This is a count of request objects, not unique underlying URLs or orders; the
readiness plan selected 12. Source discovery/pickup works; its SUMMARY denominator
omits the 774 Opus items.

Ask Claude to report `from_opus_refetch=774` and `items_in_queue=947` for these pinned
inputs and preserve deduplication/expected-hash checks. The next actual ladder
SUMMARY remains an external acceptance check; no claim that it has already changed.
No job file/output was edited. T1 is resolved upstream for pickup, with summary
verification still pending; this note does not claim all Opus bytes were recovered.
