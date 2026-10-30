# Shared byte-custody fetch pool

`FetchPool(cache, workers=12, per_host=6)` uses only the Python standard library.
It enforces at most six concurrent requests per hostname, robots exclusions and
crawl delays, HTTPS without embedded credentials, byte bounds, manual redirects,
SHA-256 cache verification, per-URL coalescing and deterministic map ordering.
Failed robots queries remain retryable. Robots exclusions never become accepted
source evidence or an exhaustion claim.

Completed bodies are content-hashed with URL/response metadata. Interrupted
requests retain `.part` bytes; ETag plus a verified Content-Range is required to
resume. A range mismatch discards the partial body. The source-ladder keeps its
existing document, expected-hash and identity validators. It prewarms one route
per uncarried item, then walks remaining routes in their original order. Runs
with `JOB_MAX_REQUESTS` skip prewarming to preserve their request budget.

The runner restores `.job-cache/<job>/` using actions/cache, passes that directory
as `JOB_CACHE_DIR`, then enforces each job's `CACHE_MB` (1–4096 MiB; default 1024).
These caches are disposable and never evidence acceptance. The source ladder
uses 2048 MiB; original-page and facsimile downloaders 256; XML/metadata 64 each.
The snapshot cache key is unique per branch/run/attempt; restore keys choose the
last available branch snapshot. All per-job directories have independent caps.

`benchmark_fetch.py` measures 48 mocked 20 ms downloads across two hosts, including
SHA-256 and disk writes, versus one worker and then a warm offline cache. It does
not predict production network latency. `test_fetch_pool.py` uses injected byte
responses, and the road test runner disables sockets.

Each persistent cache hit still reads and SHA-256 verifies the complete body.
`cache_stats()` reports request attempts and successful 200/206 payload bytes, persistent body
read count, read bytes, checksum bytes, and miss causes so future production measurements can
establish whether repeated cache validation merits an optimization. It changes
no cache freshness or reuse behavior; mutable URLs retain their existing
no-TTL semantics. Downloaded bytes exclude robots, redirect and error-response
bodies; they are not total network transfer.

Optional matrix sharding was deferred: the existing runner orders dependent jobs
and reconciles one commit; changing that commit model needs its own design and
stale-output protections. No fr-originals source file is modified.
