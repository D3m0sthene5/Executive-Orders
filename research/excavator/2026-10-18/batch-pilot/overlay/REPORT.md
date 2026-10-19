# Reviewed status proposal to claim-kit working dossier

This handoff makes an undecided order usable in the existing claim-kit workflow after an explicit producer decision and a separately pinned independent research review. It never changes the provisional-status table, census, claims, reservations, or human reviews. Every generated proposal starts with owner acceptance **false**. Actual adoption remains an owner-controlled change through the authoritative project process.

Implementation: `jobs/claim-kit/status_overlay.py`; regression tests: `jobs/claim-kit/test_status_overlay.py`. The parent integration owns the CLI and the compiler's additive `OVERLAY_INPUTS.jsonl` hook. This module does not fetch, ingest or excavate the corpus.

## Callable handoff

```python
stats = {}
evidence = freeze_evidence(repo, output, full_history_packet, stats)
decision = extend_decision(full_history_packet, evidence, agent="producer")
# Producer reads the held originals and history, then explicitly fills decision.
review = blank_review(decision, evidence, reviewer="independent-reviewer")
# A separate reviewer checks the exact frozen decision, sources and scope.
proposal = propose(repo, decision, review, evidence)
dossier = experimental_dossier(repo, proposal, decision, review, evidence)
write_bundle(repo, isolated_new_version_directory,
             proposal, decision, review, evidence, stats)
```

`assemble_working(repo, lifecycle_sheet, proposal, decision, review, evidence)` returns the existing assembler's `(claim, errors)` pair, retaining `claim_kit.status_overlay`. `check_working_claim(repo, claim, proposal, decision, review, evidence)` checks that label and the existing exact-span/Stage 19 gates. Neither function writes or publishes a claim.

Only `freeze_evidence` scans compiled shards. Subsequent decision versions reuse its frozen `base_dossier`, validate bounded held sources/current history and authority, and require a new exact-decision review. They do not run `build.build`, `load_corpus`, segmentation, or later-event discovery. A regression test replaces corpus building and shard iteration with deliberate failures during those later steps and still obtains the working dossier.

## What is pinned and what remains judgment

The frozen evidence has schema `eo-status-overlay-evidence/v1`. It pins the included census identity and the unchanged authoritative tables, the complete status-history packet, all held source bytes used by the package, the compiler summary, five compiler-code hashes, and the consumed shard hashes. Reconstruction uses `build.package` with existing `CLAUSES`, `OWN_TERMS`, `ACTING_PROVISIONS`, `CHAINS`, `STATUS_LEADS`, text declarations and the bounded per-order `OVERLAY_INPUTS` context. Large shared actor contexts retain repository-qualified, byte-pinned pointers that remain readable from an isolated bundle. Missing records, unlisted/noncontiguous shards, changed shard bytes, failed runs, old formats and old compiler code fail visibly.

The producer uses `eo-status-history-decision/v1` with the original history pin and the frozen evidence pin. The added blank fields require an express yes/no recommendation, original identity confirmation, source review, earlier-ending/partial-scope/savings checks, noneditorial basis IDs, all history observations reviewed, every history flag explained, a substantive rationale, and no unresolved **status** material gaps. YES additionally requires an exact held `CURRENT:` predicate and an explicit check through 2026-10-14. Historical 1989 snapshot predicates and report-deadline bases are rejected. NO requires held `ACT:`, `TERM:` or `ACTOR_TEXT:` evidence; an unparsed full acting original can support a manual source review without forcing a corpus rebuild. These requirements do not decide whether the researcher's legal judgment is right.

The separate `eo-status-overlay-review/v1` record must pin the entire exact producer sheet, evidence and history. The named reviewer must differ from the producer, expressly confirm independence and source checks, accept the decision, give a substantive reason and identify the original plus every selected basis it checked. The default role is `independent_ai`. This record is never an `eo-lifecycle-review/v1` human certification. Editing the producer decision invalidates the old review.

The proposal is `eo-status-promotion-proposal/v1`, with a content-derived version ID, exact decision/review/evidence/history/source pins, the prior authoritative status `null`, a proposed status, the target authoritative file, and `owner_acceptance: {accepted: false, accepted_by: null, accepted_on: null}`. There is no authority-write or owner-acceptance command. A forged accepted proposal cannot be used as an experimental dossier. The working dossier retains the ordinary claim-kit schema and a self-consistent fingerprint but explicitly records `status_overlay.experimental_only=true`, `owner_accepted=false` and the real authoritative status `null`.

`write_bundle` permits only a new isolated directory under `jobs/claim-kit/output/overlays/…` or `research/excavator/…/overlay/…`; it refuses existing versions and protected destinations. It writes evidence, the producer/review/proposal records, the working dossier and a **blank** lifecycle decision. A status review does not fill or approve the later whole-lifecycle judgments.

## Real frozen controls

`EO_4314/EVIDENCE.json` freezes an undecided difficult control: 29 located actor provisions and 12 actor contexts, but no attributed original, no clause inventory and no complete machine later-source search. Its initial status decision remains blank. The proposal gate rejects it, including the missing acceptable original. The dossier retains the missing actor-provision findings for EO 7812 and EO 8067. No status is inferred from the 1989 ended-by observation.

`EO_12331/EVIDENCE.json` freezes a second hard handoff. Original `ORIGINAL:EO:12331` and full actor `ACTOR_TEXT:EO:12537` are present. The acting text says `Sec. 7. �xecutive O rder No. 12331 of October 20,1981 is revoked.`; the machine did not extract an `ACT:` record from this OCR, and that gap remains visible. No complete later-source search is supplied. The initial machine inventory has five clauses and misses the original's section 6 after an interposed FR document marker; the existing producer `inventory_overrides` mechanism is required before asserting a complete lifecycle inventory. The parent producer's source read also identified section 5's never-disclose agreements as a possible survival issue requiring judgment. Revocation alone is not mechanically converted to a no-status decision. Frozen source fields remain exact; no OCR repair or legal interpretation is silently substituted.

`EO_11352/EVIDENCE.json` is the next real candidate for separately conducted producer and independent review: one original suspension paragraph, exact `ACT:EO:11352>EO:11437` evidence expressly revoking EO 11232, EO 11352 and EO 11361, and the full `ACTOR_TEXT:EO:11437`. Its missing complete later-source search remains a lifecycle gap. A narrow provisional status judgment must not assert that this formal revocation proves the first effective end; source, congressional, scope and residual questions remain for the lifecycle decision.

Evidence fingerprints:

- EO 4314: `ef0cfc40efcb34f7c3cd51f5007dc20f133dd00aaae8b7eaa11f6f6f9fe8ab3a`.
- EO 12331: `9da66232c29efd265e22b2771a1703216f6c0f771e3c281a6574f23deeaf62fa`.
- EO 11352: `4e184ac9feece8b5db0c05a825f921664adf5a26ac74af56dc06913b33b59bd8`.

The engineering agent created no real source-review acceptance, provisional status, lifecycle claim or human certification. Any subsequently added real decision/review is the distinct parent producer/reviewer work and must be checked by its exact hashes.

## Verification and measured cost

`VERIFICATION.json` records unchanged before/after hashes for both authoritative tables and the real freezes. All 30 overlay tests passed in 5.284 unittest seconds. They exercise the real compiler and existing assembler, including a complete synthetic lifecycle roundtrip and a large shared actor context, and reject unreviewed/rejected/same-agent reviews, wrong identities, stale evidence, old/missing/extra/noncontiguous/tampered shards, snapshot-only automatic proposals, fabricated quotes, report deadlines, stale reviews and forged owner acceptance. The initial local invocation failed because Windows redirected its temporary directory outside the writable workspace; the successful invocation explicitly set `TEMP` and `TMP` to `work/overlay-test-temp`. That setup failure did not produce a proposal.

The measured freezes read eight compiled shard files, 274,042,707 bytes and 147,349 JSONL records each. This is a bounded record reconstruction, not a new corpus analysis. EO 4314 took 1.504751 seconds; EO 12331 took 1.306134 seconds; EO 11352 took 1.326292 seconds. Bounded revalidation of the first two frozen evidence objects took 0.111319 and 0.073386 seconds respectively. They reuse the same already compiled corpus, with zero rebuilds.

`FREEZE_TELEMETRY_v2.json` distinguishes selected-text reads, exact-span validation reads and history-source pinning. The first telemetry files' `held_source_opens` count represented selected-text opens only; it did **not** measure total source I/O. The v2 fields replace that ambiguous label. History validation's internal source opens and actual billed/model tokens are unmeasured (`null`). These timings are engineering observations, not a legal-review speedup, agent labor total or billing-savings claim.

## Bounded independent followup: receipt reuse and CLI

The parent changed evidence reuse to compare the current compiler schema/code/file set and **consumed shard manifest**, retaining the original exact `SUMMARY.json` hash as a receipt. A runner input-commit or timing-only change no longer invalidates a frozen legal review. The bounded review found no material bug in that change: sealed frozen records, original held bytes, current history, authority, failure flags and consumed manifests remain checked. Generated shards are not parsed or reopened during reuse; a changed consumed manifest still requires new evidence and review. Unconsumed generated records do not change the already frozen status basis.

The receipt regression now forbids opening any compiled JSONL shard and requires the entire proposal to stay identical. Additional tests cover an unrelated unconsumed manifest, a later runner failure and a missing consumed shard. A synthetic CLI test runs `kit.py overlay-assemble` followed by `overlay-check`, verifies the experimental/owner-unaccepted labels and unchanged preexisting files, and rejects canonical output destinations, overwrites, a blank lifecycle sheet and a stripped label. **35 overlay tests passed in 8.058 unittest seconds.** No production-code fix or change to the five pinned compiler files was needed.

`FOLLOWUP_VERIFICATION.json` records the actual independently reviewed EO 11352 proposal, fingerprint `210b5afb660d3a5b97fdd3dacb2b4c3d77187946dad84cb13de93be97ef0e771`, reproducing exactly under normal validation and an in-memory receipt-only change. The latter control opened zero compiled shards and made no canonical file edit. Normal validation took 0.084298 seconds; the receipt-only control reproduced both proposal and dossier in 0.155347 seconds. Its owner acceptance remains false. Both authoritative-table hashes remain unchanged. This software check does not redo or certify the separate legal review.

Own-rollout runtime usage is now exposed in `TELEMETRY.json`, exported with the existing `capture_telemetry.py` from this agent's exact `CODEX_THREAD_ID` log. This corrects the earlier blanket statement that model-token counters were unmeasured: **runtime token counters are available; billed-token classification, billed dollars and complete active labor remain unavailable**. The freeze fields named `billed_*` correctly remain null.

At the 2026-10-18 13:48:39.543 UTC snapshot, the 53 observed responses total 6,108,457 input tokens (5,961,600 cached; 146,857 uncached by subtraction), 47,386 output tokens, including 13,026 reasoning tokens, and 6,155,843 total tokens. Runtime cumulative counters match these per-response sums. Reasoning is included in output and is not added again.

| Own-agent phase | Input | Cached input | Output | Reasoning included in output | Outer tool calls |
|---|---:|---:|---:|---:|---:|
| Initial implementation/handoff | 4,628,988 | 4,505,984 | 38,731 | 9,492 | 43 |
| Bounded followup through snapshot | 1,479,469 | 1,455,616 | 8,655 | 3,534 | 9 |

Phase boundaries are the exact first/second own-rollout turn-context timestamps. Initial observed wall span is 969.444 seconds, ending at its first final response; followup span through the token snapshot is 223.199 seconds. Intervening idle time is excluded, and these spans are not complete active labor. The snapshot excludes subsequent responses and other agents; outer-call counts do not expand nested `functions.exec` calls. These are implementation/review costs, with no equal-quality legal-adjudication baseline or claimed savings.
