# Queued source retention

Retains at most 30 specifically requested PDF URLs through the unchanged source-ladder HTTP client. Every instrument/URL pair must already appear in FETCH_QUEUE.jsonl. REQUESTS.json supplies exact URLs, expected hashes where held, and one-based PDF pages. Nothing is searched or inferred from free-text requests.

The job rehashes cached and downloaded bytes, refuses expected-hash mismatches, preserves source PDFs, extracts requested pages, and renders PNGs if Poppler is present. Fetch failures, renderer gaps and out-of-range pages remain explicit. Existing official-fixity witnesses still need to be checked by researchers. It creates no claims, statuses, exhaustion records or readiness findings. Outputs are machine custody artifacts pending independent visual/source review.

SOURCES.jsonl exposes the actual retained PDF and selected-page text through the existing checker catalogue format. Requested targets are kept in a separate field; they do not establish document identity. The exact queue file is declared through inputs.txt so unrelated research notes do not invalidate acquisition output while a job runs.

Bounds: 90 HTTP requests including robots/retries; 250 MB per response; 40 pages per PDF; one paced downloader for this small same-host batch. The standard runner's bounded cache and oversized-artifact policies apply. No DAILY or broad queue trigger is installed.
