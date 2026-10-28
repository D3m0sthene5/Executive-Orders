# Queued source retention

Retains at most 30 specifically requested PDF URLs through the unchanged source-ladder HTTP client. Every instrument/URL pair must already appear in FETCH_QUEUE.jsonl. REQUESTS.json supplies exact URLs, expected hashes where held, and one-based PDF pages. Nothing is searched or inferred from free-text requests.

The job rehashes cached and downloaded bytes, refuses expected-hash mismatches, preserves source PDFs, extracts requested pages, and renders PNGs if Poppler is present. Fetch failures, renderer gaps and out-of-range pages remain explicit. Existing official-fixity witnesses still need to be checked by researchers. It creates no claims, statuses, exhaustion records or readiness findings. Outputs are machine custody artifacts pending independent visual/source review.

SOURCES.jsonl exposes the actual retained PDF and selected-page text through the existing checker catalogue format. Requested targets are kept in a separate field; they do not establish document identity. The exact queue file is declared through inputs.txt so unrelated research notes do not invalidate acquisition output while a job runs.

Exact already-held files may be imported with `retained_path` relative to the repository and an obligatory `expected_sha256`. The path must stay inside the repository after symlink resolution. Imports and cached copies are rehashed; source bytes are copied into the existing `output/pdf/<sha>.pdf` location and consumed through the unchanged `cache_path` field. An unexpected downloaded version is preserved under `quarantine/` and is not admitted as the requested version.

The runner supplies its prior output via `JOB_PRIOR_OUTPUT_DIR`. Retention preserves that generation with hardlinks, detaches metadata before rewriting, and adds new sources and attempt records. Failed or narrower re-extraction preserves prior text/page artifacts. Complete new extractions get content-addressed subdirectories; existing contents are checked before reuse. No unrelated prior PDF is rehashed merely to carry it forward. Standalone runs preserve the current job output when writing elsewhere.

`RETENTION_MANIFEST` can select another explicitly declared repository input for bounded follow-up batches (still at most 30 URLs each). `RETENTION_RENDER_PAGES=0` skips new PNG rendering for exact-version restoration; it does not waive a required page review or confer a new source grade. Defaults continue to render where Poppler is available. `extractions_completed` is separate from raw PDFs retained, because a retained PDF may still have an extraction error.

Bounds: 90 HTTP requests including robots/retries; 250 MB per response; 40 pages per PDF; one paced downloader for this small same-host batch. The standard runner's bounded cache and oversized-artifact policies apply. No DAILY or broad queue trigger is installed.

This job opts into `MAX_OUTPUT_FILE_BYTES=104857599`, one byte below 100 MiB,
through the existing runner. This permits the exact 104,612,053-byte PL 97-35 PDF
(`aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127`)
to remain in ordinary committed output instead of an expiring run artifact.
The default for other jobs remains 95 MiB. Larger files are still moved to the
run's oversized download and listed in `STATUS.json`; they are not discarded.
