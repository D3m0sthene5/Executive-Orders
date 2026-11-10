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

`triage` takes under a minute on the owner's PC (it reads about 1.4 GB of compiled claim-kit outputs).

## Routes and gates

The gates are in Llull's registry (`jobs/llull/llull.py` `GATES`; the per-order inputs come from
`jobs/llull/kit_features.py`), so `llull.py census --requires ...` can count them too. They read the same records the
claim kit freezes into an order's dossier: the compiled decided dossier, or for an undecided order the compiled overlay
inputs assembled the way `build.package` does. On the 120 back-test orders this light reader agrees with the frozen
dossiers on every gate input.

| Route | Bentham actions | Hard gates (the route itself requires them) | Soft gate (measured predictor) |
|---|---|---|---|
| `undecided_full` | `status_assignment.undecided` | `original_usable`, `no_page_check_owed`, `status_basis_record`, `clause_inventory_present` | `later_order_text_held` |
| `status_only` | `status_assignment.*status_only*` (Respondendi status-only tier) | `original_usable`, `no_page_check_owed`, `status_basis_record` | `later_order_text_held` |
| `decided_lifecycle` | `production.claim_ready.*` | `original_usable`, `no_page_check_owed`, `clause_inventory_present` | `nea_notice_if_emergency` |

- `original_usable`: an acceptable original. On the decided route a working text the transcription ruling credits
  (`working_text.GRADES`) is usable too. On the undecided route only a frozen `working_text_basis` is
  (Accursius F6, PR 276), because `status_overlay` requires an acceptable original today.
- `no_page_check_owed`: the selected original does not require a page or image check, which cannot be made from held text.
- `status_basis_record`: an exact held ACT, TERM, ACTOR_TEXT or CURRENT record that is not a report deadline. These
  are the only bases `status_overlay` accepts. OWN_TEXT and PARENT_END records (F5, PR 274) count once a dossier carries them.
- `clause_inventory_present`: the dossier has a clause inventory.
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

- Success: filed proposal 9, status accepted 13, producer status only 11 (33 in all).
- Failure: failed after dispatch 73, dispatch-blocked 14 (87 in all).

| Gates (cumulative) | Admitted | Failures kept out | Successes lost |
|---|---:|---:|---:|
| none | 120 | 0 / 87 | 0 / 33 |
| + original_usable | 103 | 17 / 87 | 0 / 33 |
| + no_page_check_owed | 95 | 25 / 87 | 0 / 33 |
| + status_basis_record (route minimum) | 85 | 35 / 87 | 0 / 33 |
| + clause_inventory_present | 85 | 35 / 87 | 0 / 33 |
| **+ later_order_text_held (operating point)** | **57** | **63 / 87** (51 of 73 dispatched) | **0 / 33** |

Split by wave at the operating point:

- Papinian: 43 of 64 failures kept out, 0 of 26 successes lost.
- Haloander: 20 of 23 failures kept out, 0 of 7 successes lost.

A gate that also required an ACT naming the order, or an ending-verb ACT, would lose 7-8 of the 33 successes, so the
curve stops at the operating point. Respondendi diagnosed 63 of the kept-out failures:

- 21 needed a later event no held source records.
- 19 were route or tool defects: 10 where the held evidence leans NO, 9 YES.
- 11 hit a rule too strict for what is knowable.
- 6 were missing a later event the evidence leans NO on, and 2 were producer errors.

The route defects and too-strict rules are the orders the Accursius fixes (F3-F7) target. Larrey keeps them out
because the route cannot finish them today. They come back in when those fixes land and Larrey is recalibrated.

**Decided lifecycle route: Papinian y01-y14 (YES) and c01 (370 orders).**

- Success: filed 61, submitted but not filed 36 (97 in all).
- Failure: blocked 273.

| Gates (cumulative) | Admitted | Failures kept out | Successes lost |
|---|---:|---:|---:|
| none | 370 | 0 / 273 | 0 / 97 |
| + original_usable | 370 | 0 / 273 | 0 / 97 |
| + no_page_check_owed | 358 | 12 / 273 | 0 / 97 |
| + clause_inventory_present | 358 | 12 / 273 | 0 / 97 |
| **+ nea_notice_if_emergency (operating point)** | **262** | **108 / 273** | **0 / 97** |

The two filed YES orders that invoke an emergency (EO 14373 and 14404) were signed in 2026, less than a year before
the cutoff, so they need no continuation notice and pass.

**Limits.**

- The samples are small. 0 of 33 lost has a 95% upper bound of about 9% (rule of three); 0 of 97 has one of about 3%.
- The soft gates were chosen on these same waves. The Haloander split is a partial held-out check, not an independent one.
- An action's projected yield therefore uses the rule-of-succession share (kept+1)/(of+2), 34/35 and 98/99, not 1.0.
- The gate keeps out no order that reached review, so review spend is not reduced.

## Pools per Bentham action on main (2026-11-10, claim-kit outputs of 2026-11-10T10:36Z)

| Action | Members | Admitted | Hard gates only | Top reasons kept out |
|---|---:|---:|---:|---|
| status_assignment.undecided | 10,697 | 2,545 | 3,559 | no later-order text 6,374; original not usable 5,995; no status basis 3,800; page check 2,431 |
| production.claim_ready.yes.fr | 351 | 243 | 339 | NEA continuation notices 96; page check 12 |
| production.claim_ready.no.fr | 1,034 | 966 | 966 | page check 67; original not usable 1 |
| production.one_step_away, recovery.* | 250 | not triaged | | (corrections of existing claims; their routes are not modelled) |

`output/TODO.md` has the full reason tally by route. Its sole-reason counts show which single acquisition would admit
an order. For example, 1,234 decided orders lack only a page check, and 99 YES orders lack only the NEA notices.

## Projected cost (`PROJECTION.json`; a projection, not a measurement)

These figures are what the measured waves would have cost had the gate run first. Model P counts producer dollars only:
the gate removes the producer cost of each kept-out dispatched order, and review cost is unchanged. Model A scales all
worker dollars with attempted orders. Coordinator dollars are excluded.

| Wave | Measured | Model P | Model A |
|---|---:|---:|---:|
| Papinian undecided (90 attempted, 6 adopted) | $7.71 per adopted status | $6.34 | $4.02 |
| Papinian undecided, per accepted status (16) | $2.89 | $2.38 | $1.51 |
| Haloander probe (30 attempted, 3 proposals) | $4.04 per proposal | | $1.35 |
| Papinian YES y01-y14 (347 attempted, 55 filed) | $3.29 per filed claim | $2.94 | $2.26 |

Review is 61% of the undecided worker spend, so producer-side triage alone cuts about a sixth of the cost per adopted
status. The larger lever is in Bentham's ranking. Its cost of the undecided action falls from $3,557 for 10,697 orders
to $846 for 2,545, with projected dossiers 1,070 → 1,039, so dossiers per $100 go from 30.1 to 122.8. The YES
production action goes from 70.2 to 100.3.

## Wiring

- **Claim-kit admission** (`jobs/claim-kit/admission.py`). This covers `kit.py next` (pick), `kit.py prepare`, and
  therefore the Maudslay conveyor, which reserves and prepares through the kit.
  - An order Larrey keeps out of the action's route is refused, and the refusal names the missing input.
  - pick reserves only admitted orders.
  - `ADMISSION.json` records the triage receipt.
  - Fail-closed: an order with no verdict on the route is refused (`no_compiled_inputs`). So is a checkout with no
    triage output, or one computed on other claim-kit outputs (re-run `larrey.py triage`).
- **Bentham** (`candidates.apply_triage`, `bentham.score`).
  - For a triaged action, `orders` is the admitted count and `orders_before_triage` the member count.
  - Cost is priced on admitted orders.
  - Yield is projected as the untriaged rate × members × the back-test's retained share, and labelled as such in the plan.
  - Bentham's strata keep every member, because admission applies Larrey itself.
- **Calibration.** Each route records the sha256 of the kit file its gates mirror, as it was when back-tested:
  `status_overlay.py` for the undecided routes and `assemble.py` for the decided route. When that file changes (for
  example when an Accursius PR merges), the route turns advisory: it is not enforced, and Bentham notes it. Then
  check that the gates still mirror the route, run `backtest` again and commit `BACKTEST.json`. A stale gate could
  keep out orders a fixed route can finish, so the safe default is not to enforce it.
- **Job.** `job.py` runs the tests, then `triage --no-pools` after `claim-kit` and `readiness-tracker` (`after.txt`).
  Bentham runs after Larrey. Larrey does not read Bentham's strata in the job, so neither job is an input of the other.

## Follow-ups

- When F3 (CURRENT records), F5 (OWN_TEXT) and F6 (working-text basis) merge, the undecided routes turn advisory.
  Extend `kit_features.from_overlay` to frame the records those fixes freeze, then recalibrate. Respondendi's
  diagnosis says about 30 of the kept-out failures would then be decidable.
- The soft gates' lost yield can only be measured by dispatching soft-gated orders. Run a deliberate
  `LARREY_LEVEL=hard` probe of at most 30 such orders when the owner wants that measured.
- `production.one_step_away` and `recovery.*` have their own blockers (custody, Opus media, quarantines) and are not
  yet triaged.
