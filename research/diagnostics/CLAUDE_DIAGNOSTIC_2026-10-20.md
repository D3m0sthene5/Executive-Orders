# Executive-Orders diagnostic after Claude's interrupted audit
Date: October 20, 2026 (New York). Scope: current GitHub main, Claude's working branch, the integration branch, open PRs and the failed integration execution. This is a diagnosis; no runtime code, accepted finding, claim, source receipt, codebook or readiness output was changed.

## Finding

The repository has a working acquisition/checking pipeline and substantial recoverable unmerged work. Integration is unfinished. A reproducible claim-kit fingerprint defect prevents its build and breaks downstream consumers. Two frozen validation jobs separately reject changed inputs. The integration handoff incorrectly describes work as merged into main.

The latest integration execution ran **22 jobs: 16 succeeded and 6 failed**. Its successful tracker produced 238 ready-for-human-review orders before claim-kit failed later in the same execution. That is a valid observation of that tracker run, not a successful end-to-end integration receipt.

## Exact snapshots

| Snapshot | Commit | Ready for human review | Interpretation |
| --- | --- | ---: | --- |
| main | ed19a06039278c10e5a3ebddccf19d2bd02ac3a2 | 138 | Published default-branch tracker |
| claude/junto-1727 | bd4450ab101cf0c14e736678614cd645c59312f0 | 256 | Later production branch; lacks the integration branch's five new disputed-claim holds |
| claude/dazzling-gates-4xkkzo | da75ca1d85bf9333bffe8b012c7e33c36f9bf688 | 238 | Combined branch, with six failed jobs and five new disputed-claim holds |

All three use 14,972 working identities and 3,359 provisional statuses. These counts describe different snapshots and must not be added or treated as human certification.

GitHub still reports PRs #38, #40 and #42–#45 open. The integration branch includes merge commits for them, but their work is not merged into main. Its newest Claude note says otherwise. The integration branch and the current junto branch have diverged: integration has 52 unique commits and lacks **17 later junto commits**, from their shared e3c9f0d878d149c2d210a3e30a5ebe38c6b4ecd4 ancestor.

The missing commits include Lambertini IV claims and probe outcomes; the R9830 probe and scale registration; new source requests; 98 Pullman emergency-board packets; Tycho II and VIAPAR preparation; and successful production outputs. Reconcile their content before publishing the integration branch. Taking the integration branch alone would omit this later work. Preserve exact preregistration history while resolving ledger collisions.

## What works, with observed limits

The successful jobs in integration run [39475524967](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39475524967) were source-ladder, clause-drafts, official-fixity, claim-checker, family-rules, claim-drafts, readiness-tracker, NORTON, case-bundles, Valla, Hamilton, Junto, Lambertini, Llull, Polya and daily-digest. Success means that execution completed; it does not establish scientific correctness or savings.

- **Source-ladder/Panizzi:** its latest integration run was online, worked 177 of 1,448 queue items, carried forward 364 sources and added 30 receipts, yielding 394 found sources and 27 distinct new hashes. It retained 19 prior quarantines and found no carried source failing that run's checks. The 394 receipts include 307 document-text and 87 report-record tiers. The remaining 127 no-route results, 17 retry-later results and two unresolved request tasks remain work, not evidence of source absence. All **173 source-ladder tests passed locally** on the pinned integration source.
- **Claim-checker:** checked 343 claim lines; 342 mechanically passed and one remained unverified. Structural gate passes were 258; 257 claims passed every check. These are deliberately different measures. No mechanical failure was reported.
- **Readiness-tracker:** succeeded before claim-kit ran and reported 238 ready. Its original-text count remains 2,312; source acquisition does not automatically establish an original or a legal ending.
- **Valla and portfolio holds:** both review histories for EOs 13792, 13101, 13148, 13783 and 13807 were retained. These are five disputed cases with two reviews, not ten distinct discoveries. They need clause-specific performance, scope and earlier-ending evidence before a complete replacement is accepted.
- **NORTON:** the integration job succeeds, but the bounded research pilot established no independently reviewed reusable answer and no expansion case.
- **Junto, Hamilton, Llull and Polya:** their standalone jobs complete on this integration execution. Junto's verified savings remain zero. NEYMAN's historical all-blocked pilot is preserved research evidence; its current rerun failure is described below.

The green road-test workflow is narrower than a whole-system check: test_roads.py runs family-rules, case-bundles, daily-digest, shared-library and freshness tests. It does not execute the full claim-kit suite, so it could pass while this compiler defect remained.

## Repairs, in order

### 1. Fix the claim-kit producer/consumer fingerprint contract

**Confirmed code defect.** jobs/claim-kit/build.py writes compiled_code_sha256 for seven files, including lifecycle_obligations.py. status_overlay.py's CODE_FILES contains only six and omits that file. _manifest() compares the complete dictionaries for equality.

Consequently, freshly built synthetic fixtures fail with:
`old_compiled_outputs:code_fingerprint; run claim-kit build once`

Rebuilding alone cannot resolve unequal file sets. The integration runner executes the tests before build(), so the 35 overlay setup errors prevent the real corpus rebuild.

Local reproduction: 185 tests ran, with 35 errors and four corpus-dependent skips caused by the sparse checkout. All 35 errors match the GitHub failure. In a separate process, adding only lifecycle_obligations.py to CODE_FILES **in memory** made all **35 overlay tests pass**. No file was patched and this is not a completed full-pipeline repair.

Use one consistent file inventory for producer and reader, retain stale-code rejection, rerun the complete suite with hydrated data, then rebuild claim-kit.

### 2. Protect previous successful outputs when a job fails

**Confirmed runner behavior with consequential output loss.** .github/scripts/run_jobs.sh removes a job's output directory before testing it. The workflow commits results even when jobs fail. After claim-kit stopped, the bot committed a failed STATUS/log directory in place of its previous dossiers and indices.

This caused corpus-excavator (missing INDEX.json), X1 (missing TEXT_REPRESENTATIONS.jsonl) and NEYMAN (missing FAMILIES.json) to fail. Llull's standalone job succeeded using earlier available data, while its later portfolio regression tests failed after claim-kit output had been removed. This explains apparently contradictory pass/fail results.

Prior output bytes remain recoverable in Git history. Stage a new generation and publish it only after success; retain failure receipts separately and explicitly identify stale successful generations. Do not silently present an older generation as current. Then rerun consumers in dependency order with actual input receipts.

### 3. Reconcile the 17 missing production commits and finish integration

**Confirmed branch divergence and incorrect handoff.** Integrate the later junto work while preserving both sets of holds, claim ownership, append-only histories and preregistration evidence. Regenerate outputs from combined inputs rather than choosing a generated file merely because one side is newer.

Do not publish 256 or an arithmetic adjustment as the merged result. Run the actual checker/tracker on the reconciled branch. Correct the merged-main claim in a new handoff entry by its author or an explicit cross-agent correction in our own notes.

### 4. Separate frozen historical validation from current integration validation

**Expected protections currently block reusable jobs.**

- portfolio-repair-check loads its old bounded packet and verifies every frozen input pin. The merged/renumbered jobs/llull/ledger/forecasts.jsonl differs, producing an input-hash mismatch before its evidence-to-tracker stages run. Preserve the historical packet. Supply an explicitly versioned current integration packet or execute historical replay against its pinned snapshot; do not disable pin checks or overwrite the original experiment.
- neyman-pilot/job.py always loads research/neyman/pilot-20261020/MANIFEST.json. Its check_pins() correctly rejects changed compiler, checker, corpus and tracker inputs. Repairing claim-kit alone will not satisfy that historical manifest. Keep the old sample/results intact and use a separate current manifest/run or a pinned historical replay.
- The standalone NEYMAN generation failed because claim-kit data was absent; that dependency failure is distinct from the frozen pilot mismatch.

### 5. Repair evidence-feed coverage and refresh the diagnostic plan

Claude's latest successful claim-kit summary contains **1,268 warnings**, including **1,266 text-hash mismatches**: family-rules 538, ofr-compilations 500, isthmian-canal-1911 105, richardson-volumes 68 and indian-reservations-1912 55. Two additional provenance paths are missing. These are skipped declarations, not 1,266 unique lost orders; overlapping valid representations may remain. Regenerate affected producer records against exact current held bytes and measure the net per-order impact. Do not merely rewrite hashes to silence warnings.

The tracker has a fixed list of acquisition feeds. Its compiled-transcription list omits hathi-gpo-orders, numbered-early-orders and wikisource-texts. Claim-kit already discovers attributed source records generically, and the integration checker explicitly indexes these producers, so they are **not unused everywhere**. Inspect the gap at the tracker layer and preserve derivative/lead grades. Adding such a feed cannot make a derivative into a verified original.

Domesday's 225-ready headline and statement that the last source-ladder run was offline and worked three items are superseded by the later 238-ready/online-177-item run. Its 890-draft opportunity and cost range are planning estimates; a judgment-only label does not prove that a complete lifecycle can be supported. Earlier Bowditch/Y2 trials failed their yield gates. Refresh prerequisite intersections and run a bounded trial before expanding production.

## Repair completion criteria

1. All full claim-kit tests pass, including the original stale-source and stale-code rejection tests; the real corpus build succeeds.
2. Successful prior generations survive a forced test/build failure; failures remain visible and current consumers reject stale incompatible inputs.
3. The 17 later commits are accounted for, both sets of disputed-case reviews survive, and no ledger ID/reference or preregistration evidence is lost.
4. Frozen historical experiments remain reproducible; a separately pinned current validation reaches its checker/tracker stages.
5. One combined checker/tracker execution establishes the new ready count. Failed job receipts and missing telemetry remain explicit.

Audit artifacts: DIAGNOSTIC_EVIDENCE_2026-10-20.json contains the exact snapshots, job results and local verification records. No new legal research, status adoption, census change, human certification or measured savings resulted from this diagnostic.
