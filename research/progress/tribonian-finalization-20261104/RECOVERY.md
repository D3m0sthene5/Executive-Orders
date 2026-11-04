# Tribonian finalization recovery — November 4, 2026

Continuation of the owner's “Publish readiness totals” assignment. This checkpoint preserves verified reconciliation while the existing production run finishes; it does not declare a new published readiness generation.

## Verified at main a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6

| Measure | Count |
|---|---:|
| Retained main-wave disposition filings | 545 |
| Current effective Tribonian checker rows / distinct orders | 547 / 547 |
| Passing effective Tribonian receipts | 547 |
| Original-supported / transcription-dependent Tribonian text | 344 / 203 |
| Baseline ready | 784 |
| Tribonian overlap with baseline ready | 0 |
| Baseline ready with current passing receipts | 784 |
| Published tracker at this commit | 784 |
| Receipt-union expectation, awaiting actual combined tracker | 1,331 |
| Human-certified whole histories | 0 |

Both a bounded reconciliation worker and a separate independent reviewer reproduced the checker/baseline joins. They used separate OpenAI contexts; exact model identifiers, tokens, cash and full labor were unavailable. Passing checker receipts are mechanical evidence, not fresh substantive review.

The previous finalization branch, sol/tribonian-finalization-publish, was identical to main (zero commits ahead or behind); previous uncommitted local results could not be recovered in this session. This recovery uses a separate branch and does not overwrite that session's branch.

## The 545 / 547 discrepancy

The saved disposition omits the last o27 pair. Published claims and current exact receipts establish EO:13128 and EO:13274. The report and filing commit describe their completion, but no o27 completion or review folders were located under the retained claude/tribonian-state packet. Do not invent or reconstruct those receipts as original evidence.

- EO:13128 canonical claim SHA256: 444e0a010656bdf5540028067bc0daa10fa2e524f182c93b4fbf68d73efd3964
- EO:13274 canonical claim SHA256: e7cd97e90b6313f76c138ad14a5173bb956b60d3da7f31bda092f615e911d1bb

## Separate unfiled mechanical-refusal cohort

These 48 distinct orders are outside the 547 filed orders.

| Cause | Orders | Next action |
|---|---:|---|
| Custody only | 32 | Hold exact source bytes, prepare a fresh packet, recheck retained review applicability |
| Custody plus short quotation | 1 | Repair both custody and exact quotation through normal review |
| Short quotation only | 11 | Supply an adequate exact source span and review any changed claim |
| Quotation not found | 1 | Resolve source/version/span mismatch |
| Quoted order not in instrument universe | 3 | Resolve exact instrument registration/identity; do not infer admission |

Custody-involved total is 33. DISPOSITION contains 579 not-filed attempt rows (531 blocked, 48 mechanically rejected) across 549 distinct IDs; retries overlap, so these are not additive campaign-backlog counts. The report's broad characterization of 47 custody failures does not substitute for exact completion failure reasons.

## Source pins

| Record | Git blob |
|---|---|
| Baseline READINESS_BY_ORDER.csv | d1c074ce575749d48b4c6509399f74a2c19cd689 |
| Current checker PER_CLAIM.json | ab4f9e69495d0f47a3eb1fcd7e6a20cf90a32595 |
| Saved DISPOSITION.json | 9fafd3dedb7db457934f06a810a8d82832c9b4da |
| Published o27 claims | 0dba88aab59ff21fc4bfc0ba618b1b9c5caaa6b9 |

Checker input commit: 2c85459cf38b08dc1eea6d7c84a74268fa45c28e. Checker run41886953010 ran 18:34:23–18:52:37 UTC (13:34:23–13:52:37 Eastern).

## Reproduce the joins

Read the exact baseline CSV and checker JSON blobs. Let baseline_ready be IDs whose ready_for_human_review is yes. Filter checker.claims by file containing claude-2026-11-04-tribonian-. Count rows, distinct instrument_id, effective_for_tracker, all_checks_passed and text_evidence_tier. Intersect Tribonian IDs with baseline_ready; confirm every baseline ID has a current checker.by_instrument passing receipt. Join each final current claim's canonical hash with its receipt before publication.

For refusals flatten DISPOSITION.batches[].not_filed, select rejected_mechanical, and join the retained batch's packet/tally_from/checker/PER_CLAIM.json on instrument_id. Classify exact failure strings custody_record_only, too_short_to_verify, quote_verbatim:not_found and order_exists:not_in_universe. Do not add batch-local tracker gains.

## Existing production and publication

Run41896126390 started on main at 19:21:20 UTC. Its readiness-tracker job ran beginning19:25:42 and the next job began19:27:20. The workflow waits for its other selected jobs before committing. A scheduled run41902988519 is also active. Neither was interrupted or duplicated.

At recovery inspection the saved Site was version4, source1f60df5f98132bbcc15e262c143386067a1d9d31, deployment appgdep_6aeb08a5299081918718b5de988b309f. The control center validates summary/status/order rows from one main commit and refreshes while visible. Its live total can update from a successful main tracker publication without redeployment.

The legacy rocket remains dated October30 (498 dossiers,11.615% modeled work). Its clock must be rebuilt with the maintained build_mission_log.py and frozen MISSION_WEIGHTS.csv, not ready dossiers divided by identities. Preserve the frozen1,314-order census gap:14,972+1,314=16,286 modeled goal orders, despite the retained APP label16,239. Human certification remains separate.

## Execution limits and next step

The session has no usable command execution environment. Read-only GitHub tools and browser inspection work. No new checker, tracker, research, or source acquisition was launched. Await the existing successful combined tracker publication; validate its exact receipt and per-order differences, then run the maintained Mission builder through the repository's supported bounded-job route if local execution remains unavailable. Publish only verified generations.

No complete runtime/token/cash measurement is available. The reconciliation worker observed6.7 seconds of tool-call wall time, excluding reasoning and coordination; it is not whole-task runtime.
