# Larrey: triage before any agent is dispatched

Named for Dominique Jean Larrey, Napoleon's chief surgeon, who sorted the wounded on the battlefield by what
treatment could do for them, not by rank, and sent his flying ambulances only where it could help.

**Why.** Papinian paid about $0.51 per attempted undecided order and $7.71 per adopted status. 67 of its 84 failed
undecided attempts were blocked at the producer (Respondendi, PR 270), and Herschel found that 76-81% of status,
original-text and ending steps block on missing sources. Agents were being paid to discover that an order could not
be finished. Larrey checks every order for the inputs its route needs, with zero model tokens, before an agent is
sent to it.

Larrey decides no status, adopts nothing and changes no count. A kept-out order is **deferred, not decided**: it
stays open until the missing input is held, and the reason says which input that is. The reason tally is the
acquisition to-do list (`output/TODO.md`). Human-certified stays 0. Nothing is inferred from the absence of evidence.

```
python3 -I jobs/larrey-triage/larrey.py triage [--out DIR] [--no-pools]   # verdicts for every order -> output/
python3 -I jobs/larrey-triage/larrey.py backtest [--diagnosis DIAGNOSIS.csv] # replay on past waves -> BACKTEST.json
python3 -I jobs/larrey-triage/larrey.py project [--out FILE]              # projected cost, with vs without
python -m unittest discover -s jobs/larrey-triage -p "test_*.py"
```

`triage` takes about 8 seconds on the owner's PC. It reads about 1.4 GB of compiled claim-kit outputs.

**Output (Whitworth I1).** `output/GATES.jsonl` has one line per (order, route).
- Fields: `instrument_id`, `route`, `pass`, `missing` (gate ids) and `gates_commit`, plus `pass_hard`, `reasons` and `provisional_status`.
- Readers: claim-kit admission, the Maudslay conveyor (through `kit.py next` and `prepare`) and Bentham.
- `REASONS.json` (`missing_gates_any` by gate id) and `TODO.md` tally the reasons. That tally is the acquisition to-do list.

## Routes and gates

The gates are in Llull's registry (`jobs/llull/llull.py` `GATES`; the per-order inputs come from
`jobs/llull/kit_features.py`), so `llull.py census --requires ...` can count them too. They read the same records the
claim kit freezes into an order's dossier: the compiled decided dossier, or for an undecided order the compiled overlay
inputs assembled the way `build.package` does. On the 120 back-test orders this light reader agrees with the frozen
dossiers on every gate input. The independent review found one later recompile (EO 3748) with the same verdict.

| Route | Bentham actions | Hard gates (the route itself requires them) | Soft gates (measured predictors) |
|---|---|---|---|
| `undecided_full` | `status_assignment.undecided` | `original_usable`, `status_basis_record`, `clause_inventory_present` | `no_page_check_owed`, `later_order_text_held` |
| `status_only` | `status_assignment.*status_only*` (Respondendi status-only tier) | `original_usable`, `status_basis_record` | `no_page_check_owed`, `later_order_text_held` |
| `decided_lifecycle` | `production.claim_ready.*` | `original_usable`, `clause_inventory_present` | `nea_notice_if_emergency` |

- `original_usable`: an acceptable original. On the decided route a working text the transcription ruling credits
  (`working_text.GRADES`) is usable too. On the undecided route a non-original is usable only when
  `status_overlay.working_text_basis(dossier)` credits it (Accursius F6, PR 276); the gate calls that function when
  the kit has it.
- `status_basis_record`: an exact held ACT, TERM, ACTOR_TEXT or CURRENT record that is neither a report deadline nor
  the 1989 OFR snapshot. These are the only bases `status_overlay` accepts.
  - CURRENT records follow `build.package` from `STATUS_LEADS` `current_law_leads` (F3, PR 272).
  - OWN_TEXT and PARENT_END records (F5, PR 274) are framed at freeze time, so the gate calls
    `own_text.records(iid, original, clauses)` itself when the kit has it.
- `clause_inventory_present`: the dossier has a clause inventory.
- `no_page_check_owed` (soft, undecided only): the original does not require a page or image check. The kit accepts
  a producer's page confirmation, and 296 filed orders still carry the flag, so this is a predictor, not a rule. On
  the decided route it is no gate at all.
- `later_order_text_held` (soft): a held text of a later instrument that acts on or cites the order.
- `nea_notice_if_emergency` (soft): a provisional-YES order that invokes a national emergency declared before
  2025-10-14 needs a National Emergencies Act continuation notice through the 2026-10-14 cutoff (50 U.S.C. 1622(d)).
  No such notice is held in the repository yet.

`LARREY_LEVEL=hard` applies only the hard gates, for example to run a deliberate, measured probe of soft-gated orders.
There is no "off" setting.

## Back-test on real outcomes (`BACKTEST.json`)

Every gate was evaluated on each order's **frozen** dossier, exactly as its producer received it: the overlay
`EVIDENCE.json`, or the decoded `PACKET.json`. Outcomes come from the same folders: dispatch checks, producer
decisions, independent status reviews, both-arm replacement proposals and completion's publishable claims.

**Undecided route: Papinian u01b, u02 and u03 (90 orders) and Haloander u01-u03 (30).**
- Success (33): filed proposal 9, status accepted 13, producer status only 11.
- Failure (87): failed after dispatch 73, dispatch-blocked 14.

| Gates (cumulative) | Admitted | Failures kept out | Successes lost |
|---|---:|---:|---:|
| none | 120 | 0 / 87 | 0 / 33 |
| + original_usable | 103 | 17 / 87 | 0 / 33 |
| + no_page_check_owed | 95 | 25 / 87 | 0 / 33 |
| + status_basis_record | 85 | 35 / 87 | 0 / 33 |
| + clause_inventory_present | 85 | 35 / 87 | 0 / 33 |
| **+ later_order_text_held (operating point)** | **57** | **63 / 87** (51 of 73 dispatched) | **0 / 33** |

By wave at the operating point:
- Papinian: 43 of 64 failures kept out, 0 of 26 successes lost.
- Haloander: 20 of 23 failures kept out, 0 of 7 successes lost.

A gate that also required an ACT naming the order, or an ending-verb ACT, would lose 7-8 of the 33 successes, so the
curve stops at the operating point.

Respondendi diagnosed 63 of the kept-out failures:
- 21 needed a later event no held source records.
- 19 were route or tool defects: 10 where the held evidence leans NO, 9 YES.
- 11 hit a rule too strict for what is knowable.
- 6 were missing a later event the evidence leans NO on.
- 2 were producer errors.

The route defects and too-strict rules are what the Accursius fixes (F3-F7) target. Larrey keeps those orders out
because the route cannot finish them today.

**Decided lifecycle route: Papinian y01-y14 (YES) and c01 (370 orders).**
- Success (97): filed 61, submitted but not filed 36.
- Failure: blocked 273.

| Gates (cumulative) | Admitted | Failures kept out | Successes lost |
|---|---:|---:|---:|
| none | 370 | 0 / 273 | 0 / 97 |
| + original_usable | 370 | 0 / 273 | 0 / 97 |
| + clause_inventory_present | 370 | 0 / 273 | 0 / 97 |
| **+ nea_notice_if_emergency (operating point)** | **274** | **96 / 273** | **0 / 97** |

The two filed YES orders that invoke an emergency (EO 14373 and 14404) were signed in 2026, less than a year before
the cutoff. They need no continuation notice, so they pass.

**Limits.**
- 0 of 33 lost has a 95% upper bound of about 9% (rule of three); 0 of 97, about 3%.
- The soft gates were chosen on these same waves, and the Haloander split is only a partial held-out check.
  `later_order_text_held` is fitted on 28 orders and alone defers 1,014 undecided orders. Its lost yield can only be
  measured by dispatching orders it keeps out. The independent review recommends a 30-order `LARREY_LEVEL=hard`
  probe of soft-gated orders before relying on it at scale; that is the first follow-up.

## Pools per Bentham action on main (claim-kit outputs of 2026-11-10T10:36Z)

| Action | Members | Admitted | Hard gates only | Kept out, by reason |
|---|---:|---:|---:|---|
| status_assignment.undecided | 10,697 | 2,546 | 3,729 | no later-order text 6,396; original not usable 5,995; no status basis 3,822; page check 2,431; no held text 57; decided in the tracker 6 |
| production.claim_ready.yes.fr | 351 | 255 | 351 | NEA continuation notices 96 |
| production.claim_ready.no.fr | 1,034 | 1,033 | 1,033 | original not usable 1 |
| production.one_step_away, recovery.* | 250 | not triaged | | corrections of existing claims; their routes are not modelled |

`output/TODO.md` has the full tally by route, with sole-reason counts: which single acquisition would admit an order.
- 99 decided YES orders lack only the NEA notices (`acquire.nea_continuation_notices`).
- 907 undecided orders lack only a usable original.
- 129 undecided orders lack only a page check.

## Projected cost (`PROJECTION.json`; a projection, not a measurement)

These figures show what the measured waves would have cost had the gate run first.
- **Model P** (producer dollars only): the gate removes the producer cost of each kept-out dispatched order; review cost is unchanged.
- **Model A**: all worker dollars scale with attempted orders.
- Coordinator dollars are excluded from both.

| Wave | Measured | Model P | Model A |
|---|---:|---:|---:|
| Papinian undecided (90 attempted, 6 adopted), per adopted status | $7.71 | $6.34 | $4.02 |
| Papinian undecided, per accepted status (16) | $2.89 | $2.38 | $1.51 |
| Haloander probe (30 attempted, 3 proposals), per proposal | $4.04 | | $1.35 |
| Papinian YES y01-y14 (347 attempted, 55 filed), per filed claim | $3.29 | $2.98 | $2.38 |
| **All three waves (64 filed claims, $239.20 of workers), per filed claim** | **$3.74** | **$3.22** | **$2.48** |

Review is 61% of the undecided worker spend. Producer-side triage alone therefore cuts about a sixth of the cost per
adopted status. To reach $1 per filed claim, review must get cheaper too.

**Bentham** (projection): undecided goes from 30.1 to 39.0 dossiers per $100, YES production from 70.2 to 74.9, and NO
production is unchanged; the rank order does not change. Bentham does not scale the members by the old rate, which
would overstate, because the pool's admitted share (24%) is lower than the draws' (33-52%). Instead it uses:
- the back-test's rate among admitted orders relative to all attempted (`yield_lift`: 2.05 undecided, 1.34 decided);
- the Model P cost per admitted attempt (`cost_lift`: 1.58 and 1.25);
- both capped by the action's own members/admitted ratio.

## Wiring

- **Claim-kit admission** (`jobs/claim-kit/admission.py`). This covers `kit.py next` (pick), `kit.py prepare` and
  therefore the Maudslay conveyor.
  - A kept-out order is refused with the missing input named.
  - pick reserves only admitted orders.
  - `ADMISSION.json` records the triage receipt.
  - It is fail-closed: refused are an order with no verdict on the route, a checkout with no triage output, output
    from other claim-kit outputs or other gate code, and a project checkout (AGENTS.md) that leaves
    `jobs/larrey-triage` out.
  - Not yet gated (a pre-existing gap, flagged by the review): `kit.py overlay-prepare`, `sheet` and `status-sheet`
    never call admission.
- **Bentham** (`candidates.apply_triage`, `bentham.score`).
  - `orders` is the admitted count, and `orders_before_triage` the member count.
  - Yield and cost are projected with the lifts above.
  - A measured rate row marked `"gated": true` turns the lifts off.
  - Bentham's strata keep every member; admission applies Larrey.
- **Calibration.** A route is enforced only while two conditions hold:
  1. Every kit file its gates mirror matches the committed back-test: `status_overlay.py` and `build.py` for the
     undecided routes, `assemble.py` and `working_text.py` for the decided route.
  2. Neither the committed back-test nor the job's re-run of it on the current code loses a success.

  The job's re-run can switch a route off but never on. The frozen outcomes were produced under the old rules, so a
  looser new rule cannot show up there as a lost success. After a kit change, re-enable a route by checking that the
  gates still mirror it, then committing `larrey.py backtest` (zero tokens, seconds). An advisory route warns at
  admission.
- **Job.** `job.py` runs the tests, re-runs the back-test (`needs.txt` lists the two wave folders), then
  `triage --no-pools` after `claim-kit` and `readiness-tracker` (`after.txt`). Bentham runs after Larrey, and neither
  job reads the other's output in its run. If the job fails after claim-kit's results land, triaged actions are refused
  as stale until `triage` runs again, which needs a checkout with the claim-kit outputs.

## Follow-ups

1. Probe `later_order_text_held` and the undecided page-check gate: 30 soft-gated orders under `LARREY_LEVEL=hard`.
2. When F3, F5 and F6 merge, `status_overlay.py` and `build.py` change and the undecided routes turn advisory. The
   gates already call the fixes' own functions. Commit a fresh `larrey.py backtest` to re-enable the routes, then check
   that about 30 of the Respondendi-diagnosed kept-out failures are now admitted. F4 (routed ACTOR_TEXT) arrives
   through the compiled outputs.
3. Gate `kit.py overlay-prepare`, `sheet` and `status-sheet` through admission.
4. Triage `production.one_step_away` and `recovery.*` (custody, Opus media and quarantine blockers).
