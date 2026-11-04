# Pinned production baseline and queue coverage

`BASELINE.json` is the machine consumer. Rebuild offline from the repository root:

```sh
python3 research/progress/production-observability-20261104/baseline/build_baseline.py
```

The builder verifies 14 retained native Git blobs and SHA-256 values in `SOURCES.json`, the large native readiness CSV's exact Git blob, and the sanitized eight-tally snapshot before replacing the last good generation. A bad input refuses refresh. It writes only in this directory. It does not invoke any ordinary job, workflow, source acquisition, lock helper, reservation mutation or scientific gate.

## What the frozen census says

Repository source is main `600ae3018f71025b3e53dc8538b8f92e6e159b76`. The native checker and tracker succeeded on the same checkout, `aeafe6ef3b5d53d38d34b6fec7fc25fb8851efd0`, in run 41504614771; checker finished November 2 at 19:13:37 UTC and tracker at 19:33:11 UTC. These are dated generation results, not live production status.

| Checkpoint | First missing in display order | All unfinished at checkpoint |
|---|---:|---:|
| Usable text | 6,228 | 6,228 |
| Every command | 7,892 | 14,120 |
| Legal history | 49 | 14,165 |
| Evidence | 18 | 12,757 |
| Final gates | 1 | 1 |
| Ready for human review | 784 | — |

The first column partitions 14,972 identities. The overlapping second column does not add up to a population. Neither locates workers or implies sequential research. The final-gates count is one unfinished row whose listed checks are closed; it is not a census of work awaiting review, correction or filing. Of the 784 ready dossiers, 460 have original-supported text and 324 are transcription-dependent. Provisional status exists for 4,291 orders. Native Stage19 still documents zero human-certified whole lifecycles; its older provisional-status denominator is not reused.

The sole final-gates residual is EO 14139: all listed checks close, but native `claim_record_errors` says `unresolved_material_gaps`, with no blocker-code cell. It requires examination of that exact hold; there is no evidence here that it merely awaits filing. `final_gate_residuals` preserves this observation for the hub.

`only_missing_checkpoint` counts rows whose listed missing checks lie in just one checkpoint: text0, commands3, lifecycle45, evidence18, gates1. These counts describe remaining check patterns, never automatic achievable gains. The 14,120 command-check openings differ from the 3,393 `NO_CLAUSE_INVENTORY` native blocker records because native detailed research blockers are chiefly reported on decided orders. Missing checks and blocker codes have different reporting scopes.

The major recorded blocker families overlap: 10,681 lack provisional status; 5,943 lack a located official source; 3,667 have only a compiled transcription; 3,393 lack a clause inventory and 3,393 have unclosed savings/residuals; 3,000 have an unproved first end. They do not establish how much labor has already occurred. Source availability, substantive legal research and reviewer capacity cannot be causally apportioned from these counts.

## Observed memberships and unavailable queues

Nine historical reservations are published in `CLAIM_KIT_LOCK.json`, identical on main and the protected branch. Their presence establishes reservation records; it does not establish active workers or current assigned workload.

Readonly GitHub inspection found protected `claude/tribonian-2026-11-04` still at `cacfb8f4af6db949476bd7bec8220a464055c931`. Its published folder contains tools only. Its batch plan names 40 batches and 1,218 unique orders; none is ready in the frozen November 2 census, and none appears in the shared reservation register. All 1,218 planned members remain protected. Missing register entries do not make them available. Local packets, worker phases, current output, tokens, and completion are unavailable; the owner's reported pause waiting for Claude quota remains active work.

Current worker-active, assigned, queued, review, rework and filing population counts remain `null`. The consumer carries typed published reservation/plan membership separately, dated historical outcomes separately, and the owner's pause observation separately. A quiet publication surface establishes no inactivity.

## Recovered historical completion and rework

Eight Erasmus native completion tallies contain 64 attempted member-versions: 52 eligible/published, 11 blocked and 1 rejected mechanically. These are 52 distinct published orders. The report identifies 32 recovered Apollo rejects and 20 superseding corrections, not 52 net new ready dossiers. Exact eligible claim hashes, native source blob identities and URLs are retained in `ERASMUS_TALLIES.json`; control identities and individual reveal markers are omitted. Aggregate control counts remain only as aggregate counts.

The native nine-batch plan contains 65 member assignments and 61 distinct orders. There is no completion tally for e2; the report explicitly records the rejected EO 11303 correction. The failed/retried 64 member-versions must not be treated as 64 unique orders or a current queue. Four initially rejected genuine versions were corrected in later batches; EO 11303 remains rejected in the dated report. Seven Apollo rejects were producer-blocked by missing citable evidence or source grades, and EO 12891 failed completion because the acting PDF bytes were not held. The report also identifies four still-flagged filed Apollo claims. These are distinct historical states and do not supply a project-wide rework denominator.

The 52 eligible tally members all have claims present in the combined native row census. This is a presence join. The global checker summary reports 919 claim records for 898 orders; per-claim exact-hash global receipt reconciliation was not recovered here, so no exact-version global-checker join or run-attributable readiness gain is asserted.

## Job coverage and decisions

`job_coverage` connects the existing acquisition/working-text, command/dossier, later-source/current-law, evidence and completion/checker/tracker routes to actual native consumption evidence and the remaining labor. Consumption counts are records at their native scopes, not unique sources or hours saved. These routes already exist. The measured gap is their linkage to worker phases, queues and exact attempts, plus current observations outside published outputs.

The supported opportunity is to join existing completion/review receipts and ordinary collector interfaces, carry protected plans and timestamped generations explicitly, and improve citable-evidence access for the documented held cohort. Reviewer capacity, integration delay and labor savings need additional observations. No new production wave, legal research, policy relaxation or savings experiment was run for this baseline.

## Recovery and validation

GitHub `fetch_file` returned the native large CSV's blob identity but empty content. The existing hub's `orders.csv` hashes to exactly the same native blob `d1c074ce575749d48b4c6509399f74a2c19cd689`; the builder therefore uses verified identical bytes rather than fetching a large corpus. All other retained inputs were fetched at exact commit SHAs and byte-verified. Native source links are in `SOURCES.json`; sanitized tallies retain their original receipt URLs and Git blobs.

Independent review reproduced checkpoint totals and all eight tally projections. It found nondeterministic blocker tie ordering, unpinned sanitized input and ambiguous assigned/queued labels; these were fixed. It also identified individual reveal markers as control disclosures; these were removed and the sanitized snapshot repinned. Final independent probes found clean rebuild byte-identical and corrupt native/derived inputs refused refresh while retaining the prior generation. Full private/local production coverage remains unavailable.

The coordinator owns Kean registration, handoff integration and publication. This worker modified only this baseline directory and staged/committed nothing. `COSTS.json` retains the bounded observed collection window and unavailable resource fields.
