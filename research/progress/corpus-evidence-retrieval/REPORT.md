# Cruden corpus-evidence retrieval

Engineering work on branch `sol/corpus-evidence-retrieval`, from main
`f9c6d806ad059dcad7875ab3708715f20ea386df`. The final implementation is
bound by `SOURCE_PINS.json`; independent review is in `challenge/FINAL_REVIEW.json`.
Canonical evidence, claims, statuses, readiness outputs and scientific review
requirements are unchanged.

## Starting evidence and scope

The existing Cruden entrypoint searches every recursive `*.txt` below sorted
`jobs/*/output/texts`, excluding `clause-drafts`. On this frozen checkout that is
33,118 files and 200,530,096 raw bytes. Its number matcher, code-name matcher,
source ordering, own-source exclusion and 40/60 matching-file limits are the
compatibility contract. The old `search` command remains available.

PR104's report at `9fa8432a7a0c3550901c5d2acd23e72ae1eab50a` attributes 113.6 seconds
to a seven-order Cruden lookup. Its fragment-index repair is a separate workload
and contributes no saving to this assignment. The exact retained seven-order
packet was copied byte-for-byte into `native/r1-input/`, with origin and SHA-256.
Its original production machine and corpus version are not recreated here.

The profiling worker compared Namier, `eo_identity.find_mentions`, the
current-law and later-events parsers, and checker/working-text indexes. Namier
searches a fragment-defined universe and has text bounds; the number parsers
recognize different prefixes, lists and suffix forms. Their existing outputs
cannot replace Cruden's exact searches. `profile/PARSER_COMPARISON.json` retains
concrete differences. The repair retains Cruden's discovery and matcher rather
than promoting those tools' leads into exhaustive Cruden coverage.

## Measurement design

`profile/profile_cruden.py` runs the original callable with its native packet
loader. Only its output destination is redirected into this report directory.
The legacy loader calls `batch.load_packet(..., check_sources=False)`; packet
self-fingerprints are checked, while current source/Valla/prior-research freshness
is not asserted. These retained packets are engineering inputs and confer no
fresh research, publication or scientific approval.

A 250-file microprofile of the actual 24-member t5 packet measured 2.2866 seconds;
6,047 regex-search calls consumed 1.146 seconds (50.9%). A full diagnostic t5
profile measured 303.428 seconds, with 794,856 regex-search calls consuming
216.410 seconds (71.3%). It exactly reproduced retained legacy t5 LOOKUPS.json.
The diagnostic runs overlapped; their wall times are contextual. Final causal
comparisons must use the sequential, identically configured receipts below.

## Costs, failures and limits

All three requested workers use configured model `gpt-6.1-sol`, in fresh contexts.
The coordinator retains design, evidence boundaries and integration. Worker
artifacts record available clocks and tool counts. Token/cache/cash telemetry
and coordinator active labor are unavailable; no model-token or total research
hours saving is inferred.

Setup included a failed clone through `git.chatgpt-team.site` (authentication),
then a successful public GitHub blobless clone and explicit source/metadata
materialization. An early `git ls-tree -l` caused avoidable lazy blob reads;
subsequent inventories use names only. These setup costs are separate from
Cruden execution. One profiling attempt was interrupted after its manifest was
written because an additional full native validation probe ran before Cruden;
its unobserved phase is not represented as a gate result. All diagnostic and
interrupted receipts are retained.

Search hits remain leads. A matching number, name or phrase does not establish
identity, applicability or legal effect. An empty result covers only the declared
query and searched snapshot, with all omitted/unreadable and result-limit
qualifications; it does not establish that an event never occurred.

## Implemented result

Cruden now stores disposable per-file decimal-run and code-prefix features in a
content-bound cache outside the repository. Every call rewalks the actual search
inventory and hashes every source, then applies the unchanged matcher to source
bytes from candidate files. A second complete inventory/hash pass refuses
observed mid-call mutations. Source additions, deletions, same-size edits,
unreadability, sparse omissions and search limits remain visible. Cache/schema,
algorithm and compiler-byte changes invalidate extraction features; accidental
cache corruption causes a disclosed rebuild.

Legacy `LOOKUPS.json`, `LOOKUPS.md`, lookup stdout and regex-search stdout retain
their existing contract. A companion adds exact queries, raw-source hashes,
normalized character spans, complete source access, counts before limits,
truncation and bounded negative coverage. New `number` and `literal --write`
commands expose this metadata with a compact stdout descriptor.

| Serialized seven-order arm | Native-call time | Process rchar bytes |
|---|---:|---:|
| Original | 71.010 s | 232,327,605 |
| Repaired, cold construction included | 11.569 s | 511,480,650 |
| Repaired, warm | 5.541 s | 526,929,916 |

This is one matched trial per arm on identical seven-order packet/query and
33,118-source snapshot, with profiling disabled and no competing corpus
benchmark. It establishes a 6.14x cold and 12.82x warm speed ratio for this call.
It does not reproduce Opus's machine-specific 113.6 seconds. Cold construction
costs 7.728 seconds, including 4.644 seconds of feature extraction; final corpus
verification costs 1.634 seconds and cache writing 0.644 seconds. These costs are
inside the 11.569 seconds. Independent harness setup, about two seconds per arm,
is recorded separately and applies to both sides.

The feature cache occupies 15,449,266 bytes. Each new full coverage/details
sidecar is about 7.5 MB; the legacy files stay byte-identical. Read bytes increase
because of full verification. Distinct warm packets t5 (24 orders), t6 (24) and
non-NRA b06 (2) take 6.538, 6.544 and 4.933 seconds, respectively, and exactly
reproduce both legacy files. Their earlier diagnostic legacy timings overlap
and are not used for speed ratios. `profile/SUMMARY.json` preserves all native,
setup, byte, candidate, cache and output-volume measurements.

## Independent challenges and producer exercise

The 11 focused source tests pass. A fresh independent OpenAI-family engineering
review passes 61 overlapping boolean checks across five suites, with no blocking
issue for the exact source/helper pins. It checks output bytes, suffixes, FR
citation confusion, duplicate representations, neighboring-order text, full
source hashes and spans, Unicode/CRLF/invalid UTF-8, counts and truncation,
add/edit/delete invalidation, equal-size edits with restored mtime, unreadability,
tracked omissions, corrupt cache postings, schema/algorithm/compiler changes,
auxiliary input mutation, and construction races. This is engineering review;
scientific and human review requirements retain their existing scope.

A fresh producer used the retained ordinary EO10673/EO10772 packet, two new query
invocations and 19 full hit-source reads. It verified identical legacy output and
retained access to later and potentially contrary passages. Its audit explicitly
records a duplicate-path self-hit, neighboring farm-storage wording in own-text
signals, and an inherited OCR citation miss that the literal route reaches.
These findings demonstrate why retrieval output remains a lead. Retained source
grades and authentication limits are unchanged. The assignment occupied 336.443
observed seconds including waits/corrections; its two query processes took
11.103 seconds. No producer-turn, model-token or total-hours saving is inferred
from a single assignment. Exact counts and limitations are in `producer/`.

All selected native packet held-text pins were made locally accessible from Git
after the benchmark without changing Cruden's searched universe (the additional
paths are excluded clause-drafts or non-search data/page paths). The earlier
full-gate missing-file refusal is retained as a setup failure. This lookup study
does not approve retained packets for current production; the legacy native
loader's `check_sources=False` behavior is disclosed throughout.

## Delivery and adoption

`ADOPTION.md` gives Sol exact source pins, focused regressions, the sequential
comparison, a producer usage example and combined-tree acceptance checks. No PR
is merged. Kean findings use the unique retrieval and producer IDs cited in the
dedicated handoff. The same-family engineering review, source-bound lookup and
bounded producer audit add no lifecycle/status conclusion or certification.
Bulky exact raw outputs are retained losslessly in the indexed archives; source
harnesses, compact receipts, failures and independent reviews remain readable.
