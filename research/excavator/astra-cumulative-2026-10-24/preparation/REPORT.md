# Cumulative preparation repair

Ordinary preparation omitted EO11782's selected October 18 v4 producer claim and
exact-version review even though both were held. The prior implementation attached
only optional Valla context; it did not discover the noncanonical producer/reviewer
and checkpoint records. The actual baseline packet under `before/` contains no
`producer/EO_11782/v4/claim.json` path.

`prior_research.py` is a read-only helper used by the existing `batch.prepare`,
packet validation and source-blocked checkpoint/resume command. It discovers current
lifecycle claims, exact-version review records (including per-claim rows in a shared
review), selected-version manifests, and unfinished producer/source-blocked
checkpoints. It retains version-specific qualifications and rejections, deduplicates
identical claim hashes without selecting the newest proposal, and exposes source
hashes, exact original-quote/source alignment, differing propositions and remaining
current-claim gaps. All decisions remain blank. Recorded approval is attributed to
its exact historical review, never granted to a new claim. The existing frozen
control/reveal records distinguish planted controls from real blind candidates.

The packet fingerprints this context and its current held dependencies. Changed,
added or removed prior work requires preparation again. The current packet's own
output subtree is excluded so `apply` can produce a proposed claim and `batch-check`
can check it without self-invalidating; other earlier packages remain discoverable.
The existing checkpoint/resume CLI similarly excludes only its own current input and
output checkpoints. Its fingerprint reopens a blocked attempt when prior research
changes. Exact matching does not authenticate an original, establish source truth,
resolve legal conflicts or certify a whole history.

The existing `needs.txt` already materializes `research/readiness` (canonical claims,
producer/reviewer work and the selected-version manifest). Two additional roots,
`research/excavator` and `research/production`, materialize the other checkpoint and
reconciliation sessions on narrow workers. BATCH.md instructs normal sparse-checkout
preparation to materialize these existing job dependencies first. Collection states
that it covers materialized current research, not unseen files or Git history.
No ProQuest/corpus scan or new research store, registry, CLI, legal gate or status was
introduced.

## Actual EO11782 before and after

The compiled `jobs/claim-kit/output/dossiers/EO_11782.json` was absent. Both actual
runs therefore used the identical dossier decoded losslessly from the existing PR56
`research/excavator/astra-source-first-2026-10-23/packet/PACKET.json`, retained at
`preparation/inputs/EO_11782.json`. Both call the normal `batch.prepare` function
behind `kit.py prepare`, using its existing `dossier_paths` option and explicit
owner-reviewable replacement routing. No legal or source fields were changed.

- `before/PACKET.json`: 255,571 bytes, lossless round trip, no v4 claim path.
- `after-final/PACKET.json`: 489,557 bytes, same decoded dossier, six distinct
  claim versions including the current PR56 partial and real new frozen proposal.
- v4 canonical hash `0e29f299ba3535ad7b7beb30f39bb7dafee9c709f537eb626239d475b35682dc`
  is exposed with its exact `uphold` review and its explicit limits.
- v3 canonical hash `e9c8b5f3773b1012ccea13fd07af2f7852cbf527d95e958e36dccb4cd7b6d95c`
  retains the exact `reject` review for search provenance.
- `BATCH1_SELECTION.json` and `CHECKPOINT_BATCH1_AUDIT.json` remain attributed
  records, not new approval. The three-section PR56 inventory and older five-unit
  inventory require scope reconciliation; their shared order number is insufficient.
- Current canonical partial hash remains
  `4e58641c1d437da5c72a5d1c8b7a26b84e4f814367e1cdc361ecdc7e47c86634`.
- Decisions remain `approved=false`; automatic approvals are zero.

`BEFORE_AFTER_PROOF-final.json` pins exact input/output/code hashes, observed load
success and metrics. This is a frozen observation: later research or source changes
correctly make the packet stale. `OTHER_CHECKPOINT_PROOF-v2.json` demonstrates actual retained producer checkpoints
for EO10681, EO10739 and EO12145, plus EO11513's existing source-blocked checkpoint
under the Lamm resumption work, with its actual report-date reason and result paths.
No renewed legal research of those four orders is claimed.

## Validation and limits

`VALIDATION.log`: 29 tests pass: eight cumulative-research regressions, seven
existing obligation/resume tests, and fourteen existing batch tests. They cover
selected noncanonical work, rejected/stale review, source change, conflicting
versions, no located history, current valid partial review, frozen planted controls,
ordinary packet invalidation, current-output feedback and default CLI resumption.

The first broader batch run exposed two genuine self-feedback failures from freshly
applied claims; excluding the current output subtree fixed them. A separate existing
Valla test initially failed because its source files were unmaterialized; restoring
those tracked fixtures resolved it. These attempts are costs, not successes omitted
from accounting. Final focused tests did not alter canonical claims, statuses,
reservations, reviews, human certification or other-agent notes.

Preparation adds visible prior context and makes the packet larger. It demonstrates
recovered research visibility, not token, labor, dollar, end-to-end efficiency or
ready-history gains. Model usage is unavailable. Final preparation took approximately
1.01 machine seconds; these machine timings are not agent/reviewer effort.
