# October 20 pipeline repair and pull-request reconciliation

The repair combines the interrupted integration, later Claude production, final
NORTON work and all six outstanding research pull-request heads. Generated files
were restored from coherent successful snapshots before rebuilding. The report
will record the final observed pipeline result rather than combine ready counts
from different branches.

## Repairs

| Area | Failure | Repair |
| --- | --- | --- |
| Claim-kit fingerprints | Writer hashed seven compiler files; overlay reader hashed six. | One shared compiler inventory includes `lifecycle_obligations.py`; changing it invalidates a frozen snapshot. |
| Runner publication | A failed run could erase a healthy generation. | Transactional generation preserves prior output, retains failed attempts and blocks same-run consumers of failed jobs. Independent successful jobs still publish after freshness checks. |
| Branch reconciliation | Later production and final NORTON work were absent; generated outputs and ledgers conflicted. | Preserve all branch histories, reconcile authored inputs and ledger IDs, rebuild coherent output generations. |
| Source custody | Integration and production held different source generations. | Import pinned production receipts, preserve exact quarantines and failed history, and revalidate every imported receipt under current rules. |
| Portfolio validation | A historical sealed packet was treated as current. | Preserve that experiment and its provenance; prepare a separately sealed current packet and execute the real checker and tracker requirements. |
| NEYMAN validation | The frozen historical manifest rejected newer current inputs. | Freeze the preceding current frame manifest before current attempts, verify all pins, and preserve historical results unchanged. |
| Producer checksums | Four producers declared body-only hashes for saved header-plus-body text artifacts. | Declare the hash of exact saved bytes; retain a separate body hash. No source-byte or hash verification bypass. |
| Corpus ingestion | Family-rule counterexample originals were inherited by the target identity. | Exclude `family_rule_checks` from original-text ingestion, with a regression test. |
| Tracker inputs | Three derivative feeds were omitted. | Add their compiled-transcription leads without promoting them to original sources. |
| Operational digest | A healthy retained generation could be mistaken for a successful latest attempt. | Label published output status explicitly, link the current workflow and retained failure receipts, and order NEYMAN consumers before the final digest. |
| Valla current pilot | Historical attestations correctly refused reuse after a protocol change; the pilot assumed five reusable components. | Keep refusals explicit, validate current exact-claim holds and review bytes, and verify that all five cases remain blocked in the actual tracker. Frozen experiments are unchanged. |

The full first run completed without cancellation. Claim drafting took 52m02s and succeeded; 25 of 27 jobs succeeded, portfolio validation failed and daily-digest was correctly blocked. Successful outputs and failed receipts were published in `1ebe65b501a886ba959c6c38d214da0cc1e3e9e2`. See `PRIMARY_RUN_RESULT.json` and `SAFE_STALL_DIAGNOSTIC.md`. The two validation integration defects were repaired separately: validated runner inventory annotations now retain their meaning in backups/attempts, and the historical gate replays its exact ledger snapshot while preserving the merged current ledger.

## Reconciliation

Original PRs: #38 (ProQuest handoff), #40 (Claude production), #42 (NEYMAN),
#43 (Valla), #44 (portfolio repair) and #45 (NORTON). Their exact heads are
ancestors of repair code `ec13121674cec5b92d910fe18dd361415e072ee4`.
PR #41 was already superseded and remains closed.

The integration preserves the existing Llull ledger prefixes. Incoming forecast
`L-20261020-65` becomes `L-20261020-78`, retaining its prior identifier as
provenance; incoming outcomes `O-20261020-49` through `52` become `59` through
`62`, with references updated. There are 78 forecast and 62 outcome records.
Three unseen raw fetch requests were appended without rewriting the prior queue.
Both sets of review holds on the five disputed claims are retained.

## Validation

Final run receipts, output commits, readiness measurements and merge dispositions
are recorded in `REPAIR_EVIDENCE.json` after completion. The combined workflow is
[39490062770](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39490062770).
The Valla follow-up passed its complete bounded smoke in [run 39492197443](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39492197443), with Ubuntu/Windows road tests also passing. `CURRENT_VALLA_SMOKE.json` retains the exact result: all five existing claims passed the schema gate, zero passed every mechanical check in that sparse smoke, and all five remained blocked by verified source-audit holds. No historical attestation was renewed. The current portfolio job separately requires its full six-claim mechanical and ten-source verification.

Local regression suites passed for claim-kit (187 tests; four sparse-data skips),
source-ladder (175), runner freshness/publication (29), tracker (23), portfolio
validation (16), Junto (40), Valla current validation (25), and the four affected
producers (8/23/42/33, with four sparse-data skips across those producer suites).
The road suite passed on GitHub Ubuntu and Windows, including failure retention,
blocked consumers, independent publication and freshness races.

## Late production head

A final head refresh found 20 additional commits in PR #40, published in `874f970f5564b81135e6ff939ff77b56f8972a5a` while validation was running. The preceding repair had already passed all ten downstream jobs in run 39503891853, including 445 portfolio tests and seven integration stages, and published output commit e643172c.

The new integration retains those results and incorporates the new source-page coverage and lettered-identity fixes, 27 authored provisional claims, ACT reviews, pending owner-method questions and original experiment bytes. It preserves the ledger prefixes and registration commits, projects incoming L-78 to L-88 and O-59 through O-62 to O-76 through O-79, and retains original identifiers as provenance. The ledgers contain 88 forecasts and 79 outcomes. Nested derived-rate pointers now agree with their actual source outcomes; the existing 7/10 corrected plant rate remains controlling. New source acquisition and downstream validation are pending for this later head; 251 remains the earlier measured snapshot, not a new combined claim. See `LATE_PRODUCTION_RECONCILIATION.json`.

## Research boundaries

The authoritative 14,972-row identity projection, provisional-status table and
both codebook documents have identical Git blobs to pre-repair main. No pending
NO-status proposal is adopted by this integration. Existing source-audit holds,
including EO 9789 and the five disputed first-cessation cases, remain controlling.
No research claim is independently human-certified by a software merge. No new
legal ending, model-cost saving or population completion estimate is established.
Remaining legal and source work belongs in the ordinary reviewed workflow.

This repair performs no new per-order legal research. Session token/cash totals
and per-order active effort are unavailable.

## GitHub review disposition

The connected account, `D3m0sthene5`, authored these PRs. GitHub rejected the
formal APPROVE request with HTTP 422 (self-approval is prohibited). Validation
is recorded in a review comment, not misrepresented as an independent approval.
The owner explicitly authorized software repair and integration in this session;
final merge states and SHAs are recorded in `REPAIR_EVIDENCE.json`.
