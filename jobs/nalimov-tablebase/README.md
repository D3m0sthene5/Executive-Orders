# Nalimov tablebase

Named for Eugene Nalimov, whose endgame tablebases (1998) computed each chess endgame once, so later games look the
answer up instead of searching. Here the "endgame" is a kind of order whose whole claim follows from records the
claim kit already holds: a script completes the claim, and a model only verifies a small packet. Owner Tier A plan,
2026-11-10: generate then verify, batch by acting instrument, dependency order.

Nothing here files, adopts or certifies. Human-certified stays 0. A status is adopted only through Respondendi's
standing rule (once the owner approves it) or a named owner decision, after the kit's own gates.

## What it does

| Step | Script | Tokens |
|---|---|---|
| Census: which orders a script can complete, per kind, and what blocks the rest | `census.py` | 0 |
| Draft: fill the producer sheet and `STATUS_DECISION.json` from held records, or name the blocker | `drafter.py` | 0 |
| Packets: one actor text per session, every target claim it settles, typed planted controls | `packets.py` | 0 |
| Verify: two blind arms (A, B) and a status-only reader (S), each in a fresh folder outside the repository | `verify.py` | the only model cost |
| Score: upheld only if both arms uphold; a control caught only if both arms name its defect; any miss stops | `verify.py` | 0 |
| Install: only upheld drafts go into the prepared packet; the kit's own apply, checker, overlay-propose and completion follow | `nalimov.py install` | 0 |

The drafter writes exactly what a Maudslay producer writes (one `decisions.csv` row, its `clauses.csv` rows,
`RATIONALES.json`, the filled `STATUS_DECISION.json`), so the kit assembles the claim in the format the checker and
the filing route accept. The kit's `status_overlay._decision_errors` gate passes on every complete draft (tested).

## Kinds

| Kind | Script completes when | Today |
|---|---|---|
| `express_named_revocation` (undecided) | one later order names the order and ends it whole (Respondendi's sentence predicate), with an acceptable original, no page check, no other act, no ending own term, no unread current-law hit, no conflict it cannot resolve mechanically, a catalog second witness, and a clause inventory with nothing operative outside it | measured in `research/nalimov/census/CENSUS.json` |
| `decided_express` | the same, for decided NO orders with no ready claim (decided production route; no status decision) | same file |
| `amendment_only` (Pothier P2) | the kit emits OWN_TEXT / PARENT_END records (F5, Accursius PR #274); then children are drafted after their parent (`packets.topological`) | 0 until F5 |
| `own_terms` | not scripted: a stated term needs the extension and later-act checks a script cannot close | 0 |

Each clause gets one of two states: a standing command ends with the revocation (`express_revocation`, the actor's
date); a clause that only revokes other orders was performed on signing (`task_completed`, the order's own date,
source the original). Anything else (abolition, transfer, amendment of another order, a revocation folded into a
standing clause, a clause that holds another section's heading) blocks the order, so it goes to the producer route.

## Controls

At least two per session, of at least two kinds, at least one status-determining (Respondendi RULE.md
`status_control_kinds`). Mutations of a genuine entry: `date_shift`, `ending_source_swapped`, `wrong_order_text`,
`partial_as_whole`. Decoys: real orders the drafter refused only because another instrument acts on them or the same
actor acts on part of them, drafted with that blocker ignored (`drafter.draft(ignore=...)`), typed
`later_event_removed` or `partial_as_whole`. A decoy draft is never filed (`Draft.decoy`). A control is caught only if
both arms reject it and name the defect code its kind maps to (`packets.CATCH`); any miss stops the batch.

## Commands

```text
python -I jobs/nalimov-tablebase/census.py --data CHECKOUT_WITH_OUTPUTS --out research/nalimov/census --evidence-cache SCRATCH/evidence
python -I jobs/nalimov-tablebase/nalimov.py measure --evidence SCRATCH/evidence --mentions CHECKOUT/jobs/current-law/output/MENTIONS.csv --out research/nalimov/MEASURES.json
# a run (Augur-gated; see research/nalimov/calibration/WAVE.json):
python -I jobs/claim-kit/kit.py prepare --action status_assignment.undecided ...      # the kit's own packet, ADMISSION.json
python -I jobs/nalimov-tablebase/nalimov.py draft --packet BATCH/packet --out SCRATCH/drafts --mentions .../MENTIONS.csv
python -I jobs/nalimov-tablebase/nalimov.py sessions --drafts SCRATCH/drafts --scratch SCRATCH/verify --salt-file SCRATCH/control-salt
python -I jobs/nalimov-tablebase/nalimov.py run --scratch SCRATCH/verify --workers WORKERS.json   # Maudslay workers file
#   or run one fresh agent per SCRATCH/verify/workers/* folder by hand and record each with record-usage
python -I jobs/nalimov-tablebase/nalimov.py score --scratch SCRATCH/verify
python -I jobs/nalimov-tablebase/nalimov.py install --packet BATCH/packet --drafts SCRATCH/drafts --only-upheld SCRATCH/verify/SCORE.json
# then the kit: apply, batch-check, STATUS_REVIEW.json from reader S's accept (named reviewer), overlay-propose, completion
```

`SCRATCH` must be outside the repository (worker folders and the sealed key never enter `research/`). Paid worker
output is never deleted.

## Process points for the owner

- **A script is the producer.** `approved`, `identity_confirmed`, `inventory_confirmed` and the other producer
  confirmations in a draft are mechanical: they say the listed zero-token checks passed, not that a person or model read
  the source. The verification arms are the source review. The draft's rationale says so in its first sentence.
  Respondendi's stratum fingerprint includes the prompts and the kit code, so this route starts its own audit
  probation (every member cross-family audited until 59 clean audits).
- **Status review.** Respondendi needs a status reviewer distinct from both arms; reader S is that reviewer. Its accept
  becomes the kit's `STATUS_REVIEW.json` under its own name.

## Tests

`python -I jobs/nalimov-tablebase/test_nalimov.py` builds every fixture itself (road-tests). The predicate copy in
`predicate.py` is vendored from Respondendi (PR #270); `PredicateParityTests` compares it with the real module whenever
`jobs/respondendi-adoption` is checked out.
