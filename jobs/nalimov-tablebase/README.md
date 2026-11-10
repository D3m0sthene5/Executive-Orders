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
| Pre-screen: the kit's own assembler, `check_claim` and the actual claim checker on every draft | `prescreen.py` | 0 |
| Packets: one actor text per session, every target claim it settles, typed planted controls, no mechanical tells | `packets.py` | 0 |
| Verify: two blind arms (A, B) and a status-only reader (S), each in a fresh folder outside the repository | `verify.py` | the only model cost |
| Score: upheld only if both arms uphold; a control caught only if both arms name its defect; any miss, invalid arm or status-reader miss stops | `verify.py` | 0 |
| Install: only upheld, unchanged drafts go into the still-unworked prepared packet; the kit's own apply, checker, overlay-propose and completion follow | `nalimov.py install` | 0 |

The drafter writes exactly what a Maudslay producer writes (one `decisions.csv` row, its `clauses.csv` rows,
`RATIONALES.json`, the filled `STATUS_DECISION.json`), so the kit assembles the claim in the format the checker and
the filing route accept. The kit's `status_overlay._decision_errors` gate passes on every complete draft (tested).

## Kinds

| Kind | Script completes when | Today |
|---|---|---|
| `express_named_revocation` (undecided) | one later order names the order and ends it whole (Respondendi's sentence predicate), from an official copy of the ending order, with an acceptable original, no page check, no other act, no ending own term, no unread current-law hit, no conflict it cannot show, a catalog second witness with the same date, and a clause inventory anchored on the order's own text with every clause typed positively | 720 candidates, 12 complete drafts, 8 pass the kit's assembler and every checker step (`research/nalimov/`) |
| `decided_express` | the same, for decided NO orders with no ready claim (decided production route; no status decision; no catalog tests, since there is no history packet) | 0 of 2,732 |
| `amendment_only` (Pothier P2) | the kit emits OWN_TEXT / PARENT_END records (F5, Accursius PR #274); then children are drafted after their parent (`packets.topological`) | 0 until F5 |
| `own_terms` | not scripted: a stated term needs the extension and later-act checks a script cannot close | 0 |

Each clause gets one of two states: a standing command, a statement of policy or a definition ends with the order
(`express_revocation` or `express_supersession` from the provision's verb, the actor's date); a clause that only revokes
other orders was performed on signing (`task_completed`, the order's own date, source the original). Wording tests run
after OCR letter-spacing is collapsed, and a clause is standing only on a positive pattern ("shall", "is hereby
established", "it is ordered", a list item under a standing lead-in). Anything else (abolition, transfer, appointment,
amendment of another order, a revocation folded into a standing clause, a clause that holds another section's heading,
a clause in the kit's file header) blocks the order, so it goes to the producer route. v2 follows an independent review
of v1 (Claude Fable 5.2, 7 blocking findings, all fixed; see `research/nalimov/REPORT.md`).

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
python -I jobs/nalimov-tablebase/prescreen.py --data CHECKOUT_WITH_OUTPUTS --evidence SCRATCH/evidence --out SCRATCH/prescreen --mentions CHECKOUT/jobs/current-law/output/MENTIONS.csv
python -I jobs/nalimov-tablebase/nalimov.py measure --evidence SCRATCH/evidence --only SCRATCH/prescreen/PRESCREEN.json --mentions .../MENTIONS.csv --out research/nalimov/MEASURES.json
# a run (Augur-gated; see research/nalimov/calibration/WAVE.json):
python -I jobs/claim-kit/kit.py prepare --action status_assignment.undecided ...      # the kit's own packet, ADMISSION.json
python -I jobs/nalimov-tablebase/nalimov.py draft --packet BATCH/packet --out SCRATCH/drafts --mentions .../MENTIONS.csv
python -I jobs/nalimov-tablebase/nalimov.py sessions --drafts SCRATCH/drafts --scratch SCRATCH/verify --key-dir KEYS/batch
python -I jobs/nalimov-tablebase/nalimov.py run --scratch SCRATCH/verify --key-dir KEYS/batch --workers WORKERS.json   # Maudslay workers file
#   or run one fresh agent per SCRATCH/verify/workers/* folder by hand and record each with record-usage
python -I jobs/nalimov-tablebase/nalimov.py score --scratch SCRATCH/verify --key-dir KEYS/batch
python -I jobs/nalimov-tablebase/nalimov.py reveal --scratch SCRATCH/verify --key-dir KEYS/batch   # genuine twins for after-reveal review
python -I jobs/nalimov-tablebase/nalimov.py install --packet BATCH/packet --drafts SCRATCH/drafts --only-upheld SCRATCH/verify/SCORE.json
# then the kit: apply, batch-check, STATUS_REVIEW.json from reader S's accept (named reviewer), overlay-propose, completion
```

`SCRATCH` must be outside the repository, and `KEYS/batch` outside both the repository and `SCRATCH`, so no relative
path from a worker folder reaches the sealed key. Each worker attempt keeps its own event file; paid worker output is
never deleted.

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

## In the Maudslay conveyor (Whitworth I4)

`jobs/maudslay-conveyor/conveyor.py run ... --producer nalimov` replaces the producer stage with this drafter
(`Batch.draft_round`, zero tokens, no repair rounds) and plants typed controls by default (`--controls typed`: date
shift, later event removed, partial end presented as whole, wrong order's text, swapped ending source; each with its
own catch terms, at least two kinds per review set, one status-determining). Every later stage (`apply`,
`batch-check`, plant, blind review, controls, reveal, agree, `complete`) is the conveyor's own, unchanged.
`MEASURES.json` gains the draft stage, list-price dollars per stage from `jobs/necker-costs/PRICES.json`, and per
filed claim; dollars per adopted status are filled after adoption. Gap: the conveyor has no status-overlay stage
yet, so undecided members stop after `apply` (`awaiting_status_review`); that stage is the next piece of work.
