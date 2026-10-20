# Polya

Named for George Polya, *How to Solve It* (1945): if you cannot solve the problem, change it. Find an
auxiliary problem, specialize, generalize, work backwards. Design: `research/plans/POLYA_DESIGN.md`.

Every plan so far used the **order** as the unit of work and missed (series plan 4,134 h assumed vs
463 measured; Bowditch Y2 6% upheld vs at least 50% expected). Polya lists other units ("frames"), and
measures from committed job outputs how many not-ready orders one unit of each frame could move forward
one step. Sister tools: Llull (scores a plan before it runs), Junto (token savers).

## Hard rules

- **Reach is not yield.** A count is the orders a unit could advance one step. Nothing here estimates
  orders made ready, hours or dollars. `cost_usd` and `E_ready` stay null in the export.
- Reads committed files only (python3 -I, standard library). Writes only `jobs/polya/output/`
  (counts and unit ids; no per-order lists; the order frame is histogram-only).
- Never changes the codebook, a status, a tier or the certified count (0). AI statuses are hypotheses.
- Frames overlap: do not add reaches across frames. `compare` reports the union.

## Commands

Run from the repo root, `python3 -I jobs/polya/polya.py [--repo DIR] [--output DIR] <command>` (about 3 s).

```
frames [--json]            the 10 frames: Polya move, unit, step advanced
leverage <frame> [--top N] units ranked by not-ready orders reached, with the step advanced
                           (F3, F3_source_document, or "source" all resolve)
compare                    all frames: units, orders reachable, Gini, top-20, share of not-ready covered by
                           top 10 / 100 units (by leverage, and greedy max-coverage), orders near ready,
                           step matrix (which frame touches which open step), and stack coverage
export [--top N] [--min-reach N]   candidate actions for Llull -> output/CANDIDATE_ACTIONS.json
```

Outputs: `COMPARE.json`, `COMPARE.md`, `LEVERAGE_<frame>.json`, `CANDIDATE_ACTIONS.json`.
Same commit gives the same output (no timestamps). A frame whose input file is missing is reported
`unavailable` and the rest run.

## Frames

| Frame | Unit | Step advanced | Input |
|---|---|---|---|
| F0 order | one order (baseline) | all | `readiness-tracker/READINESS_BY_ORDER.csv` |
| F1 ending instrument | an acting instrument that ends others | ending (decided NO); NO status (undecided) | `later-events/EDGES.csv` |
| F2 actor provision record | an acting order whose target-naming provision is not located | ending | `claim-kit/MISSING_SOURCES.jsonl` |
| F3 source document | a shared held source | original_text, shared_sources | `claim-kit/FAMILIES.json` (`source:`), tracker blockers |
| F4 legal family | an own_term/parent/actor family; an X1 text cluster | ending; clause_inventory | `claim-kit/FAMILIES.json`, `x1-class-engine/CLUSTER_MEMBERS.csv` |
| F5 owner or codebook question | one ruling (never a codebook change) | the blocker it gates | tracker blockers |
| F6 missing input type | ORIGINAL / ACT / CURRENT / INVENTORY | by type | `claim-kit/dossiers/*.json` |
| F7 current-law table | a USC/CFR slice, for YES orders | ending/current basis | `current-law/MENTIONS.csv` |
| F8 reviewer | a source URL the human reads; a near-ready step set | review cost; ready | `research/readiness/claims/*.jsonl` |
| F9 single blocker | the only recorded blocker category; it can require many research actions | conditional step completion only | tracker blockers |

Columns of `leverage` and `compare`: `units`, `distinct_orders_reached`, `sum_leverage` (double-counts
overlap; `overlap_factor` = sum / distinct), `gini` (0 = flat, toward 1 = a few units hold the reach),
`coverage.top10/top100` (union reached by the k highest-leverage units, share of the view's pool),
`coverage.greedy10/100` (best k units by marginal gain), `reached_with_le2_open_steps`,
`reached_with_no_other_open_step_upper_bound` (reached orders whose only open steps are the ones this view
advances; conditional completion potential if those steps really are completed,
not measured yield or a generally established upper bound on legal readiness).

Every view includes remaining open prerequisites, deduplicated beneficiary
counts, and an explicitly null realized readiness change. The tracker supplies
all step states; Polya creates no second readiness calculation. `input_snapshot`
pins the bytes actually read as well as the repository head; changed inputs
stop output publication. An incomplete dossier checkout marks F6 unavailable
instead of quietly shrinking its universe. Use corpus-excavator's existing
`measure.py` for a paired actual-tracker replay when a specific acquisition has
receipts; hypothetical grouping cannot substitute for that measurement.

## The export format (for Llull)

Llull now exists. Polya retains its compatible `polya.actions/1` export and
adds input pins and prerequisite accounting. Its reach fields are planning
inputs; a measured pilot and verified registration are still separate:

```json
{"schema": "polya.actions/1", "repo_head": "...", "pool": {...}, "actions": [
 {"action_id": "POLYA:F1:ending_of_decided_NO:EO:12553", "frame": "F1_ending_instrument",
  "view": "ending_of_decided_NO", "unit": "EO:12553", "rank_in_view": 1, "title": "...",
  "tier_hint": "agent_probe", "advances_step": ["ending_or_current_basis"],
  "reach_orders": 335, "reach_decided_not_ready": 335, "reach_undecided": 0, "reach_already_ready": 0,
  "steps_complete_if_done_upper_bound": 0, "ceiling_orders": 335,
  "same_unit_actions": ["POLYA:F2:actor_provision_record:EO:12553"],
  "cost_usd": null, "E_ready": null, "reference_class": null,
  "requires_unmeasured": ["..."], "status": "hypothesis", "caveat": "...", "repo_head": "..."}]}
```

Mapping to Llull: `ceiling_orders` is the historical name for screened not-ready reach (not a forecast or proven population bound;
F8 reviewer URLs also serve already-ready orders, counted in `reach_already_ready` and excluded).
Never sum reach across actions: `same_unit_actions` names the same unit under another frame;
`E_ready = ceiling x p(accepted) x p(ready | accepted)` and `cost_usd` are Llull's to fill from
measured reference classes; `tier_hint` is a suggestion. Keep compatible fields
when improving the export; do not turn screened memberships into expected
readiness or savings.

## Tests

`python3 -I jobs/polya/test_polya.py` (17 tests: statistics by hand, exact reach on a fixture repo, a missing
input degrades one frame, a unit counts only orders whose advanced step is open, cross-frame
duplicate units are linked, aggregate-only outputs, null forecasts in the export, live-data bounds).
