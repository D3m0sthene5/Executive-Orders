# Shared-source campaign: incomplete recovery checkpoint

Status at 2026-10-23 (America/New_York): **incomplete; no published downstream readiness gain**. The execution environment reset before the evidence bundle and complete-input consumer run were published. The local checkout, execution receipts and publication-state map are no longer available. This is a recovery checkpoint, not a successful end-to-end campaign.

## What is durably recovered

- Exact runtime changes from Git tree `83b350a416781472202512c1ebb37b1f29d5f627`, preserved in commit `8adcf363301d76ea80b3048f7de4a6312e8ed5f4`.
- `RECOVERED_RUNTIME.patch`: the shared retention repair to the existing runner, retention job and README. It imports exact existing objects, retains previous generations, quarantines differing bytes, and stages complete extraction generations. It adds no downloader or evidence store.
- `RECOVERED_SHARED_REQUESTS.json`: the exact twelve shared GovInfo demands recovered from the same uploaded tree, including three existing repository imports.
- The patch was freshly checked against PR55 head `523ac593267a65723f94e980030dbd0813b004e6` with `git apply --check`, applied in a bounded reconstruction, and both Python files compiled successfully. These checks are not source-to-consumer validation.
- Original PR55 runtime, request manifest, inputs and outputs remain unchanged at this checkpoint. The recovered patch is archived rather than activating an incomplete input/output generation. The complete recovered six-file tree remains in commit ancestry.

## Observations before session loss — receipts not recovered

The preceding execution recorded these results. They cannot presently be independently reproduced from this checkpoint and are **not delivered completion credit**:

| Observation | Recorded result |
| --- | --- |
| Exact custody-only join | 94 distinct source objects, 78 claims, 3,781 failed custody fields |
| Selected shared cohort | 12 exact GovInfo objects, 66 existing claims, 2,055 repeated custody fields |
| Whole-claim input completion | 68 further exact objects for the same 66 claims |
| Raw recovery | 80 PDFs / 15,119,211 bytes: 6 existing imports and 74 recovered objects |
| Comparable warm-source check | 2,055 reads / 396,188,016 bytes before; 12 reads / 2,149,748 bytes after |
| Local actual checker and tracker | All 66 selected claims mechanically passed; 53 prior-ready cases restored; 219 to 272 ready |
| New legal histories | Zero |
| Legal holds | Five selected Valla holds remained; existing EO9789 hold also unchanged |

The local replay had sparse unrelated input omissions: missing EO10390 transcription-debt input and three unrelated quote text packs. Its global debt/failure counts were not final. A complete-input GitHub run was planned but **never triggered**. No claim, legal status, source grade, review or human certification was changed. Byte identity is not legal correctness.

Earlier acquisition and measurement timings were recorded locally, but their full manifests are lost. Tokens, aggregate active agent time and dollars were unknown. No net-efficiency or dollar saving is established. The elapsed delay included excessive implementation/verification/publication work and a failed publication path; it must not be described as fifteen hours of measured productive work.

## Selection retained from execution context

Shared availability was selected over the Pullman report family, a new source-to-dossier bridge, and Mansfield provision/inventory repairs. Twelve exact repeated GovInfo versions had a working bounded recovery route and could restore unchanged reviewed claims without new legal production. Pullman's required factual claims remained unsupported, while Mansfield involved substantive source association and scope defects beyond the already-fixed spacing issue. This was an input reproducibility intervention, not new legal reasoning or blanket inference across orders.

The initial single-object preflight and subsequent recovery succeeded locally. Six demanded objects were already tracked but invisible through the normal source catalogue; other missing versions were recovered through the existing source-ladder Fetcher. The retention repair makes those objects durable through the existing SOURCES/cache_path consumer path and reuses the checker's existing immutable-file verification memoization. Changed bytes, source identity, ambiguous applicability and substantive holds remain separate.

## Publication failure and exact resumption point

Native git push had no credentials. GitHub connector uploads created sixteen text trees and part of the binary objects, but their mapping was held only in the session. Only the first tree SHA survived in visible execution context. PR55 remained at 523ac593 until this recovery checkpoint. The first tree has now been anchored in commit ancestry, so the recovered implementation cannot be lost in the same way.

Start from the current PR55 branch in a fresh isolated checkout, read AGENTS.md/current owner rulings, and pin current heads/reservations before resuming:

```bash
git fetch origin astra/leverage-campaign-20261022
git switch -c astra/shared-source-resume origin/astra/leverage-campaign-20261022
git apply --check research/production/astra-shared-dependencies-20261022/RECOVERED_RUNTIME.patch
git apply research/production/astra-shared-dependencies-20261022/RECOVERED_RUNTIME.patch
python -m py_compile .github/scripts/run_jobs.py jobs/astra-source-retention/job.py
```

Next concrete checkpoint: reconstruct the exact dependency join from the retained PR55 offline checker receipt (run39885190210) and unchanged canonical claims; reconnect the twelve recovered demands to all exact dependent claims, then recover remaining demanded inputs through the existing bounded queue/retention path. Preserve old requests and enqueue supported new requests using the existing contract. Reconstruct the missing retention regression tests and checker→tracker wrapper changes before scheduling execution. Recover uploaded objects when their identity can be established; otherwise record any repeated acquisition as additional cost.

Publish each bounded evidence batch and its manifest as a complete reachable commit before proceeding. Then explicitly execute the affected checker and tracker with all declared inputs; reconcile the recorded 53 restored cases and remaining obligations against that fresh run. Reuse unchanged valid reviews, keep exact-version holds, and obtain independent legal review only for new or materially changed claims. Do not assert 272 as the published result until that execution succeeds.

Main remains `46a29e15d6ed4c252416b28e0ccc0590fcf6abc2`; PR55 baseline was `523ac593267a65723f94e980030dbd0813b004e6`. No merge, legal production, status adoption or unattended continuation is claimed.
