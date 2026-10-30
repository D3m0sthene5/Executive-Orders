# Bounded FetchPool cache operations probe

Date: 2026-10-29 UTC. Baseline repository: `f9c6d806ad059dcad7875ab3708715f20ea386df`.

## Scope and consumers

Read-only consumer inventory before changes found shared FetchPool use in the
source ladder, early-order hunt, Shepard BLM acquisition, CSC annual reports,
early-ranger transcription/facsimile/original/full-page jobs, EO web search,
Wikisource, APP, FR pages, and the Hathi-GPO access check. The source ladder
passes `pool.request` to its document validator; web search also uses `request`
directly. Changes are limited to shared instrumentation in
`jobs/_lib/fetch_pool.py` and its tests. No caller has been changed to export
new receipt fields, so this does not yet measure a production cache hit rate.

## Bounded baseline and outcome

`benchmark_fetch_pool.py` compares the exact baseline source loaded from the
specified Git commit with the instrumented working tree against a loopback HTTP
server through the injected transport. Two exact URLs return deterministic 4
KiB and 8 KiB bodies; each is requested twice. No public requests or source
evidence are involved.

Both versions returned four outputs with two unique hashes; each downloaded
12,288 body bytes in three server requests, read and checksum-validated 12,288
persistent body bytes over two cache hits, and retained exact URLs, body hashes
and synthetic `Last-Modified` headers. The instrumented counters attribute two
cold misses and two hits, with 12,288 body-read and checksum bytes. Measured
times were 6.046 ms baseline and 4.124 ms instrumented; the small noisy delta
does not establish a speedup. See [RECEIPT.json](RECEIPT.json).

I briefly tried same-instance verified-body reuse. Its preliminary synthetic
receipt showed about 2 ms in a tiny case, but production repeat frequency was
unknown and safe reuse required bounded memory plus checks for body/metadata
replacement, eviction, and caller header mutation. After review, I removed that
optimization. The current work adds counters only; all existing persistent
checksum validation and cache behavior remains.

## Instrumentation

`cache_stats()` reports request count, bytes downloaded, bytes read from
persistent bodies and checksum-verified, cache hit count, and misses by cause
(`cold`, missing member, or invalid). It does not claim a cache makes a mutable
URL fresh: the existing cache remains no-TTL, and callers must use
version-specific URLs or their existing document validators when freshness is
required.

## H11 runner-cache recommendation (workflow owner: root)

The current workflow key and restore prefix contain `github.ref_name`. Consider
adding a second restore prefix using the default branch name, after the current
branch prefix. That may let a new branch restore an existing bounded snapshot;
every body still passes FetchPool SHA-256 validation and source-specific
validators. Keep current-branch preference, per-job caps and source custody.
This is an unmeasured recommendation, not implemented here. Cross-branch
restore carries the same no-TTL/mutable-URL semantics as the existing cache.

## H12 retained cost metadata and H15/H16 procedure

The NRA `COSTS.json` coordinator row reports Claude Opus 5.5, 267 API calls,
113,985,255 cache-read input tokens and 114,673,813 total tokens. Under that
report's stated weighting (uncached input + 1.25 cache-write + 0.1 cache-read +
5 output), the total is 13,014,610 weighted tokens; cache-read tokens are 87.6%
of that amount. Mean cache-read volume is 426,911 tokens per call. This is
retained transcript usage metadata, not evidence of re-downloaded bytes. H12's
avoidable fraction is unknown. This worker's token and cash telemetry are not
exposed.

For H15/H16 launches, use a worker/version-specific scratch directory; keep
control keys outside reviewer-visible paths. Before dispatch, compare exact
packet agent label, package/version and artifact hash against the launch
record. Stop and retain the failed attempt if they differ. Record the exact
shell session, Actions run ID or job ID returned by the launcher, then wait on
that handle only; avoid self-matching `pgrep` and repeated foreground-limit
calls. I did not reproduce a launch because coordination and workflows are
outside this assignment.

## Verification and costs

All 27 tests in `jobs/_lib/test_*.py` passed, including the new counter test for
cold misses and persistent-body checksum reads. Benchmark output is bounded
synthetic evidence only; no production acquisition, canonical output, workflow,
claim, legal finding, source grade, or readiness count changed.

Worker model: `gpt-6-luna` (assigned). Prospective marker: 2026-10-29
19:35:55 UTC; final completion at 19:38:14 UTC. This interval is a lower bound
that omits work before the marker and includes tool waits. Tokens and cash are
unavailable; no exclusive labor estimate or net savings is claimed.

The `bytes_downloaded` counter covers successful payload blocks; robots, redirect and error-response bodies are excluded. `cache_disk_reads` is a count; `cache_disk_read_bytes` and `cache_hash_bytes` count persistent validation bytes. Neither is a physical-disk cache-miss measurement.
