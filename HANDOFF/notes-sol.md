# Sol's handoff notes

## 2026-10-18 — checkpoint: infrastructure green; twelve accepted pilot claims

### Done

- Created `sol-claim-kit` from `wire-new-sources` commit `5e3e00b2c1bdb0fcd68202b4aff735f7dd691353`. No merge to main. Read the complete brief and required guides. No authoritative census/status/ledger/codebook edits, human reviews, other agents' claims or notes, Astra-owned code or `.github/` edits.
- Built deterministic offline whole-corpus claim-kit with generic source declarations, exact Unicode/UTF-8 spans, clauses, acting provisions, own terms, chronological chains, savings, current-law leads, conflicts, missing lists, decided-order dossiers, blank sheets and a separate undecided status-lead queue. Deadlines never become ends. Provenance and page-check flags survive ingestion/assembly; missing or hash-mismatched declarations fail closed.
- Added model-neutral CLI, reservations, protocol, contract, pointer-only AGENTS/readiness additions, bounded incremental cache and output shards. Assembler runs the real Stage 19 gate plus exact held-text/hash checks, rejects stale dossiers/conflicts, reconstructs explicit inventory corrections and reports every failed sheet. Internal evidence IDs use reversible marked base64url encoding to prevent checker citation false positives; legal citations and quotes are unchanged.
- 114 local tests pass: synthetic rules, four contract fixture round trips, committed count pins, provenance, tampering, OCR boundaries, chains, cache, sharding and reservations.
- Whole-corpus GitHub run https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39106221293 succeeded on code `3ca7abebf15f6c049b21726b2eea0fbe97032cc7`; immutable output commit `717e0a4bfad161532e54755f9cf2cb97964ac03d`. Cold machine build: **280.517 seconds**, **672,883,621 output bytes**, zero cache hits, no oversized files removed. Completed standard runner without OOM; peak RSS unmeasured. Warm full-corpus runtime not measured.

| Frozen machine coverage | Count |
| --- | ---: |
| Census | 14,972 |
| Decided orders / dossiers | 3,359 |
| Separate undecided status leads | 11,613 |
| Declared representations | 69,615 |
| Distinct valid held artifacts scanned | 18,404 |
| Orders with held text | 6,569 |
| Known target/actor pairs | 13,926 |
| Located actor pairs | 7,296 |
| Families | 3,257 |

There are 1,314 input warnings. This is not a claim that every order has an original or every actor provision was located. Current-law citations/serialization without attributed operative text remain gaps. See FULL_RUN.json and immutable outputs for exact coverage and warnings.

- Evaluated 50 previously unclaimed orders in 12 eligible actor families, excluding all existing claims and specified Astra reservations. Initial outcomes: ten positive candidates, forty unable. Independent initial review: nine accept, one reject (**10%**, baseline about 11%). EO13028 missed partial amendments from EO13131; corrected and separately accepted on rereview. Original rejection preserved.
- All ten candidates were substantively reconfirmed by producers and independently re-reviewed against full frozen dossiers, not blindly rebased. Accepted IDs: **11868,12720,12734,12813,12817,13028,13050,13131,13263,13283**. Approved sheets are under `research/readiness/decisions/sol-2026-10-18/`; accepted assembled lines are in `research/readiness/claims/sol-2026-10-18.jsonl`. FREEZE_MANIFEST.json binds exact sheets, AI review records, dossier fingerprints and claims. No human reviews written.
- Preserved initial 50 deliberately partial local dossier packets, outcomes, pre-freeze sheets, rejection/correction history, ten full reviewed snapshots, source-gap tasks and actual telemetry under `research/production/claim-kit-pilot-2026-10-18/`. Forty unable outcomes are not claims. Some initial missing-context gaps are now supplied by the full job and need fresh review before promotion.
- Appended sixteen deduplicated official-witness requests to FETCH_QUEUE (twelve image/page checks, four custody verifications), preserving the original eighty rows byte-for-byte. No primary sources fetched manually. Twenty-four fact/authority tasks lack verified routes; no URLs guessed. Source-gap report distinguishes indexed context and local hydration from acquisition.
- Exercised CLI reservation on exactly fifty orders; a competing agent got zero. This was a post-research verification, not original dispatch timing. All fifty reservations subsequently released. Independent clones must commit/pull reservations; local locks cannot coordinate uncommunicating branches.

### Full-dossier recheck checkpoint

All forty initial unable outcomes have now been re-evaluated against the full frozen dossiers. EO12687 newly passed separate adversarial review and strict assembly and was added as the eleventh accepted claim. EO12757 received an initial independent rejection for overbroad termination scopes; its corrected inventory split continuing mandates from amended composition rules and passed separate rereview. It is the twelfth committed accepted claim. The other thirty-eight remain unable, with precise evidence gaps retained. Original unable sheets, rejection and correction history are preserved. See FULL_RECHECK_SUMMARY.json and TELEMETRY_RECHECK.json; initial source-gap lists are historical and some context omissions are resolved.

Expanded first-pass rejection is **2/12 (16.7%)**, above the approximately 11% baseline; corrected rereviews do not erase rejections. Final recorded all-phase floor is **348 functions / 372 nested commands / 59 collaboration calls**, kept separate, excluding root orchestration and ambiguous/unrecorded counters: **29 functions per accepted candidate**, **6.96 per evaluated order**. Token/cache billing and complete elapsed pilot time remain unavailable; categorized totals and measured intervals are in TELEMETRY_RECHECK.json. This is not a demonstrated cost win.

### Running

Final branch runner validation of committed decisions, actual checker and tracker effect remains pending. The latest **twelve** claims pass all strict frozen-dossier assembly/exact-span checks. Offline actual checker: **six all-pass, six pass_with_unverified, zero mechanical failures, twelve structural passes**, 501 exact quote checks plus four short-quote warnings. Eighty-eight source references are custody-record-only; no binary custody has been invented. Strict kit validates even the four short inventory spans by exact source offsets/hash. See FINAL_LOCAL_CHECK.json; partial local custody metadata means the full runner supersedes this result. Original ten-claim checkpoint run [39107390253](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39107390253) and eleven-claim checkpoint run [39109698942](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39109698942) were running as of 08:01 UTC. Twelve-claim validation will follow its commit; no final after count is asserted.

Durable remote checkpoints: `e8ca915ca8afae4a9c84bbf282a2cff60e6b29dc` preserves initial fifty packets/reviews and ten accepted claims; `327478535fdf991baf3a1db1f4ca044cde91f95c` preserves all forty full-dossier rechecks and the eleventh claim. This checkpoint adds the independently accepted corrected twelfth claim and its frozen audit. No progress depends only on conversation context.
Tracker baseline is **130 ready**, confirmed at base and frozen output; after value is pending. Accepted AI claims must not be substituted for tracker progress.

### Cost comparison

Baseline: about 33,000 new input tokens, 2.1M cached/reread tokens and eight calls per accepted claim. Model token/cache billing is unavailable here; no token savings can be measured. Complete pilot wall time was not captured; partial parallel intervals and command durations are not elapsed pilot time.

Initial frozen-ten recorded floor: **279 functions.exec**, **300 nested commands**, **49 collaboration calls**, kept separate; **27.9 functions per accepted frozen candidate**, **5.58 per evaluated order**. This includes initial evaluation and recorded freeze confirmation, excludes root orchestration and ambiguous/unrecorded counters. Initial floor204 + categorized freeze63 + previously omitted producer11948 cumulative12, counted once. Exact fields, source hashes, timing windows and limits are in FINAL_TELEMETRY.json and short.md.

This pilot **does not establish substantial cost reduction**. Expanded first-pass rejection is **16.7% (2/12)**, above the approximately 11% baseline; corrected rereview accepts do not erase first-pass rejects. The brief's about-fifty-accepted-claims and cost-proof definition of done is **not met**.

### Next

1. Verify final exact runner commit_run, ASSEMBLY_REPORT, per-claim checker and tracker delta. Older concurrent output runs can overwrite newer output files; immutable frozen commit above is the audit anchor.
2. For the thirty-eight still unable, obtain identified report/receipt/implementation facts, current-law operative spans through cutoff, images and custody through jobs/queue. Deadlines and later cleanup revocations cannot supply actual earlier endings.
3. Reach about fifty accepted committed pilot claims after evidence/review, and capture complete token/timing telemetry before claiming efficiency or scaling.

### Asks

No merge or approval requested. Claude/Danny can inspect the branch and decide integration after remaining pilot work. Genuine token comparison requires a runtime exposing billed model/cache counters.

### Do not

Do not merge main, promote unable sheets, treat machine leads or AI accepts as human verification, change authoritative statuses/counts, edit others' claims/notes, treat local absence as repository absence, infer ends from deadlines, or call this a demonstrated cost win.
