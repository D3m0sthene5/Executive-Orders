# Moving research progress and effort tracker

Updated 2026-10-17. Legal cutoff: 2026-10-14 (America/New_York). This tracker separates a bibliographic identity, an authenticated original, a provisional status label, a provision-level causal history, an independently checked source package, and human certification. These are different units of work.

## Current readout

| Metric | Verified value | What it measures |
|---|---:|---|
| Working identities | 14,972 | Deduplicated Stage 17 working bibliography; historical universe remains unknown |
| Stage 17 canonical provisional YES / NO / UNKNOWN | 268 / 2,787 / 11,917 | Legacy v2 overlay actually inside the released SQLite |
| Stage 17 canonical provisional status coverage | 3,055 / 14,972 = 20.404756% | Status labels within the working bibliography |
| Final Opus Stage 11 accepted overlay on GitHub | 597: 116 YES, 481 NO | Includes all 540 Opus decisions already imported into Stage 17, plus 57 new decisions |
| Reconciled provisional YES / NO / UNKNOWN, **not yet rebuilt into canonical SQLite** | 309 / 2,803 / 11,860 | 2,515 prior decisions plus the 597 final Opus decisions on the Stage 17 denominator |
| Reconciled provisional status coverage | 3,112 / 14,972 = 20.785466% | Upper current verified label count, pending a canonical rebuild and source audit |
| Additional decisions needed to reach 25% of current working bibliography | 631 | `ceil(0.25 × 14,972) − 3,112`; threshold is 3,743 |
| Canonical decided cases with a Stage 16 or 17 structured scoped episode/provision | 14 of 3,055 | Presence of structured causal records, **not** whole-order causal completion |
| Canonical decided cases without those structured records | 3,041 of 3,055 | Audit queue; some may contain narrative in raw legacy records |
| Stage 17 scoped prospective first-sunset assertions | 13 | Provision-level claims; none is automatically whole-order first cessation |
| Opus final historical first-cause results | 0 of 597 | Its accepted status records explicitly leave this field unknown |
| Production human review rows | 0 | No independent human-certified conclusions |
| Early included proxies, 1789–1861 | 3 | Too few to estimate historical coverage |
| Early included proxies, 1862–1906 | 617 | Original recovery and census crosswalk needed |

The final Opus ZIP is [`releases/opus_stage11/OPUS_STAGE11_FINITE_STATUS_DELTA.zip`](../../releases/opus_stage11/OPUS_STAGE11_FINITE_STATUS_DELTA.zip). It was fully retrieved from GitHub and passed SHA-256 and ZIP integrity checks. [`OPUS_FINAL_RECONCILIATION.json`](OPUS_FINAL_RECONCILIATION.json) verifies that its first 540 decisions match the Stage 17 import exactly and its other 57 are additive. Do not count all 597 again on top of Stage 17's 3,055. The final Opus package has text extractions and review metadata; its report names a separate original PDF/image companion that has not been verified here.

The [`decision completeness CSV`](DECIDED_CASE_COMPLETENESS_STAGE17.csv) contains one row for each of the **3,055 decisions in the canonical Stage 17 database**. [`DECISION_COMPLETENESS_SUMMARY_STAGE17.json`](DECISION_COMPLETENESS_SUMMARY_STAGE17.json) gives reproducible counts. Its scope is deliberately Stage 17; the [extra 57 final Opus decisions](OPUS_FINAL_57_PENDING_INTEGRATION.csv) remain in their original Opus release until an additive, idempotent integration is built and tested. Generate this audit again with `python research/progress/build_decision_completeness.py PATH_TO_STAGE17.sqlite`.

## Remaining effort and planning windows

| Workstream | Known remaining work | Next measurable gate | Planning window from 2026-10-17 |
|---|---|---|---|
| Ingest a newer Claude/Opus GitHub batch, if published | Remote commit and package not yet observed at this update | Verify remote bytes and manifest; deduplicate IDs; recompute counters | Same day after publication |
| Reconcile final Opus Stage 11 into a new canonical release | 57 additional decisions with unchanged verdicts for prior 540 | Additive migration, source limitation flags, clean rebuild, 57-row diff and rollback test | 1–3 working days after input freeze |
| Complete provisional labels to 25% of current bibliography | 631 additional **valid** determinations after the final Opus overlay | Count distinct, previously UNKNOWN included IDs after review; avoid denominator drift | No reliable calendar estimate until the next batch is inspected |
| Audit decided cases for “how” and first cessation | 3,041 canonical determined cases without linked Stage 16/17 structured scoped records; Opus's 597 historical causes unknown | Stratified source-and-clause pilot, publish field-level gap and adjudication yield | Pilot in 1–2 weeks; total completion not estimable yet |
| Independent legal quality check | 0 production human reviews; existing 120-case sample awaits actual review | Blind independent review with disagreement adjudication and interval estimate | Start in 1–2 weeks if qualified reviewers are available |
| Early historical census | Five 1789–1790 Lord references unresolved; 1,023 OCR markers are leads only; pre-1862 has just 3 included proxies | Authenticate first five and sample 50 dated markers against originals; record duplicates and exclusions | Initial pilot in 1–3 weeks |
| Full 1789–2026 historical universe and causal timeline | Unknown denominator, missing archival originals, and most causal histories open | Estimate source capture and adjudication rates from the pilots before projecting a finish date | **No defensible completion date yet** |

The windows are planning assumptions, not measured throughput forecasts. A later batch must pass identity, source, causal-field, and review-state checks before its nominal count advances this tracker. A 25% status bar would still leave historical enumeration, first-cessation research, and independent review largely unfinished.

## Scientific gates for a decided case

1. Preserve the historical document or identify exactly which representation was reviewed, with URL or archival location, retrieval time, bytes/hash if available, signer/capacity, and date conflicts.
2. Identify every operative clause for a NO; for a YES, show at least one continuing legal predicate and test relevant later changes. Track enduring consequences, formal disposition, and successor policy separately.
3. Link every asserted transition to an actor, affected clause, legal mechanism, effective date or interval, and original evidence. An editorial successor link or later formal revocation is not automatically the first cessation.
4. Record unresolved extensions, savings, accrued rights, host amendments, and contrary evidence. Keep “unknown” rather than filling a causal field by inference.
5. Keep AI assessment and human certification separate. A reviewer must check the source and claim fingerprint before certification.

See [`SCIENTIFIC_STATUS_2026-10-17.md`](SCIENTIFIC_STATUS_2026-10-17.md) for the validity audit and [`EARLY_ORDERS_SOURCE_PLAN.md`](EARLY_ORDERS_SOURCE_PLAN.md) for historical recovery.
