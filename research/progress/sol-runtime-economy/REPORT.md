# Session B: smaller source-index construction

Implemented a bounded memory repair in the existing claim checker. The ordinary
checker and `kit.py batch-check` consume it without CLI glue. This does **not**
establish a fix for reported 10–30 minute apply rounds or a model-token saving.

Base: `2c85459cf38b08dc1eea6d7c84a74268fa45c28e` (PR138). Branch:
`sol/runtime-economy-20261104`. Implementation is confined to
`jobs/claim-checker/sources.py` and its new `test_runtime_economy.py`.

## What changed

`load_job_sources` previously kept every parsed dictionary from one
`SOURCES.jsonl` while constructing the index. It now stages compact tuples of
the eight fields it actually consumes, then releases each tuple as its index
entry is constructed. Parsing uses the existing JSONL logic; the existing
list-returning helper remains available to other callers.

Reading and closing the entire file still precedes path/custody checks and
index mutation. An unreadable file contributes no entries. Record ordering,
duplicates, path confinement, custody, malformed-line notes, exception behavior
and independent checker execution are preserved. There is no persistent cache,
new verifier, new dispatch policy or reduced source revalidation.

## Measured retained-input result

Twenty actual source manifests contain 51,595 lines / 59,192,917 bytes. With the
materialized historical context they produce 87,855 indexed copies. Two already
filed Tribonian claims, EO13128 and EO13274, pass all checks in both versions.
All four output files (`CLAIM_CHECKS.csv`, `PER_CLAIM.json`, `SUMMARY.json`,
`REPORT.md`) are byte-identical. **No output normalization was needed.**

| Measurement | Baseline | Repaired |
|---|---:|---:|
| Ordinary checker peak RSS, two fresh processes | 178,668 / 178,588 KiB | 167,660 / 167,488 KiB |
| Ordinary checker wall time | 11.015 / 12.143 s | 12.231 / 10.060 s |
| Separately measured index-build wall time, two builds | 8.623 / 8.352 s | 6.199 / 5.702 s |
| Separate index-probe process peak RSS | 163,252 KiB | 152,860 KiB |

The retained ordinary route used about **6.2% less peak memory**. Wall times
overlap, so no reliable whole-command speedup is claimed. Some measurement
windows overlapped other validation; the receipts preserve the observed values.
The separate index probe is baseline-first and is not an independent timing
trial. Both arms still read approximately the same source bytes and construct
one index per process; repeated source hashing and double index construction
across process boundaries were not removed.

Four additional runs under a 256 MiB Linux address-space cap all succeed with
identical checker output. Application caches start empty in each subprocess;
the host filesystem cache was not flushed, so these are not cold-disk timings.
A refusal replay preserves two passing claims, three mechanically failing
variants and one malformed JSON line, with identical output in both arms.
The modified variants are engineering controls, never filings.

The ordinary `kit.py batch-check` CLI independently rechecked the two unchanged
filed claims against a fresh packet: two strict passes, two actual checker
passes, no actionable failures, no downloads or publication. Archived root
decision sheets still say `unresolved`; their separate prepare/apply/check
attempt correctly produced zero claims. This limitation is retained rather
than represented as a successful submitted-row apply or renewed review.

The 100,000-record synthetic probe reduced peak RSS from 190,372 to 127,092 KiB.
That illustrates scaling on the stated fixture; it is not a corpus forecast.
Memory remains proportional to consumed fields for one manifest plus the
accumulated index. This is not a constant-memory or OOM guarantee.

## Review, failures and validation

Independent engineering review binds exact source SHA256
`7bb63fdb6f154ee67a568bc690a3d3c081f3d6d39137ec7bb55b7d551695679b`
and test SHA256
`d38cef189fa6ccd2d2d7d451a7c82d55d92f2745e35ce6d5c7666778e327594f`.
Twenty-nine differential checks cover 1,200 varied records, complete index
values and ordering, malformed/invalid UTF-8 input, partial insertion failures,
read/open/close interruptions and concurrent cache-file appearance/removal.
The focused six regression cases and complete 76-case checker suite pass.
Broader claim-kit validation and the initial sparse-fixture failure are recorded
in `evidence/VALIDATION.json`; hosted checks are separate from local passes.

The first streaming design resolved custody paths before EOF and was rejected
after a deterministic concurrent-write probe. The corrected design retains the
original ordering. Its original source/replay bytes were not retained; the
reported discrepancy is explicitly an attributed observation. The initial
review seal incorrectly described an empty rejected-results file; revision 2
corrects that claim and preserves the superseded seal. Use the current seal,
SHA256 `346adbf0bf80a29815d27a2acf0dc5f61976a0d9ee75248f3edf86c19829031c`.

## Costs, eligibility and limits

Every ordinary checker/dispatch/completion invocation loading job source
manifests automatically uses this adapter. The benefit is smaller transient
manifest memory; larger manifests or large unused fields can benefit more.
Small-input performance is covered by the checker suite but was not separately
benchmarked. Original-source examination and independent legal review are
unchanged. Fresh tokens, cache reads/writes, output tokens, worker active labor
and cash are unavailable for this session; none are zero or inferred from
machine time. Worker configurations and measurement coverage are in `COSTS.json`.

Preparation itself had avoidable overhead: initial cone sparsity materialized
about 1.5 GB of compiled output before it was pruned. Subsequent reproduction
uses `SPARSE_CHECKOUT.txt` and avoids those outputs. No LFS payload was hydrated,
full source corpus copied or global generation dispatched. Network transfer and
total setup labor were not measured. No full historical completion was replayed.

The fallback-cache defect remains open with an exact audit in `RUNNER_AUDIT.md`.
Blanket exclusions could hide genuine reads by uncertified code; neither general
`.gitignore` nor runner policy was changed. Session A implementation, main,
active production state, frozen reviews, claims, scientific standards, counts,
job schedules and hosting remain untouched by the proposed implementation.

See `INTEGRATION.md` for the first executable next step and exact reproduction.
