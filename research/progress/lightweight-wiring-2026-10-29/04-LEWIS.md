# 4. Lewis consumes the existing acquisition queue and results

The earlier proposal to enqueue 265 Lewis requests was superseded by the pinned audit: all 265 were already queued. This patch addresses the actual status handoff and does not submit them again.

The native Lewis job now joins generated FR-source proposals to the actual queue and published Panizzi results by target, step and citation. Qualified date/edition requests are kept separate. It preserves all proposals in ALL_FETCH_PROPOSALS.jsonl and filters PROPOSED_FETCH_REQUESTS.jsonl to unqueued requests only. Existing request_contract.py remains the sole enqueue interface; this job never appends to the queue or fetches as part of the join.

ROUTES.csv, SUMMARY.json and REPORT.md are refreshed with queued/no-published-result, found-record-needing-review, found-record-needing-revalidation, conflicting-result and deferred/failure states. Exact queue/result/source record pointers and metadata input hashes are retained in HANDOFF_AUDIT.json. Missing published results never establish that no attempt occurred. Found records never establish current raw custody, target identity or original grade. The previous web-search stage is unchanged.

Ten local tests passed, including exact target isolation, edition constraints, budget reasons, contradictory results, absent current source receipts, preserved original proposals and repeat-refresh idempotence. Native entry now runs these tests alongside the existing Lewis tests; sparse inputs include the existing readiness queue directory.

This is an output-to-consumer repair, not new source acquisition or lifecycle completion. Run `python -m unittest discover -s jobs/lewis-originals -p test_handoff.py`. Leave unmerged.
