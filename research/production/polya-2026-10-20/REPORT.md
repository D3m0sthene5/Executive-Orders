# Polya: reframing the work (2026-10-20)

`compare` and `export` both exited cleanly at repo head `46f91fd`. Of 14,972 orders, 135 are ready and 14,837 are not (3,224 decided, 11,613 undecided). Certified stays 0. "Reach" means the not-ready orders one unit could move forward by one step. It is not the number of orders made ready. Frames overlap, so their reaches must not be added.

## Frames: reach and concentration

| Frame | Units | Reach | % not-ready | Gini | Largest unit | Top 10 cover | Top 100 cover |
|---|---:|---:|---:|---:|---:|---:|---:|
| F0 order (baseline) | 14,837 | 14,837 | 100% | 0.00 | 1 | 0.1% | 0.7% |
| F1 ending instrument | 1,772 | 2,843 | 19.2% | 0.44 | 335 | 4.6% | 8.5% |
| F2 actor provision record | 1,050 | 1,212 | 8.2% | 0.50 | 334 | 3.5% | 5.3% |
| F3 source document | 905 | 926 | 6.2% | 0.02 | 10 | 0.2% | 0.8% |
| F4 legal family / X1 cluster | 1,595 | 3,431 | 23.1% | 0.71 | 1,066 | 15.5% | 18.7% |
| F5 owner/codebook ruling | 6 | 13,265 | 89.4% | 0.58 | 11,613 | 89.4% | 89.4% |
| F6 missing input type | 10 | 3,224 | 21.7% | 0.38 | 1,213 | 21.7% | 21.7% |
| F7 current-law table | 2,195 | 346 | 2.3% | 0.23 | 20 | 0.5% | 1.0% |
| F8 reviewer (work backwards) | 128 | 90 | 0.6% | 0.37 | 23 | 0.3% | 0.6% |
| F9 single blocker | 4 | 4,586 | 30.9% | 0.75 | 4,560 | 30.9% | 30.9% |

## The 10 highest-leverage units (deduplicated across frames)

| # | Unit | Reach | What it would advance | Who |
|---|---|---:|---|---|
| 1 | Q: batch adoption of reviewed status overlays (yes/no) | 11,613 undecided | provisional_status. The answer may be no, and per-order work remains either way. | Owner |
| 2 | Q: send the ProQuest/NYU access request | 6,839 (536 decided) | original_text, as a ceiling | Owner |
| 3 | Q: is a compiled transcription an acceptable copy? (a reading of the codebook, not a change to it) | 3,216 (898 decided) | original_text | Owner |
| 4 | Producer for ACT actor provisions (F6) | 1,213 (685 have it as their only listed gap) | ending_or_current_basis | Agent |
| 5 | Family `own_term:condition` (F4) | 1,066 decided | ending_or_current_basis. At most 8 orders would have no step left open. | Agent |
| 6 | Producer for ORIGINAL text (F6) | 1,051 (738 sole gap) | original_text | Bounded jobs/ fetch (my guess) |
| 7 | Family `own_term:fixed_term` (F4) | 650 | ending_or_current_basis. At most 8 would have no step left open. | Agent |
| 8 | Producer for CURRENT predicates (F6) | 614 (301 sole gap) | ending_or_current_basis (current law) | Bounded jobs/ fetch of USC/CFR (my guess) |
| 9 | `own_term:report_deadline`, which is the same work as Q: report-deadline own-term reading | 562 | ending. The ruling has to come first, since a report deadline never ends an order. | Owner, then an agent |
| 10 | EO:12553, which is the same work in F1 and F2 | 335 decided-NO plus 54 undecided | ending_or_current_basis. 0 orders would have no step left open. | Agent |

Two units are worth naming even though their reach is small:
- **The 23 orders with ending as the only open step (F8/F9).** These are the closest to ready. One agent pass on them is the cheapest real readiness test available.
- **The top X1 clusters, e.g. X1C0001 `nra_code_approval` (150).** These are the only units that reach clause_inventory.

## What the reframing changes about the plan

- **The order is the worst unit.** Its Gini is 0, and the 100 best orders cover only 0.7% of the not-ready pool. By contrast, 6 owner rulings touch 89%, and the 10 largest legal families touch 15.5%.
- **The owner questions come first.** Items 1–3 cost minutes of the owner's time and gate more reach than every agent unit combined. They are ceilings, not yields.
- **Shared source documents are not leverage.** Once orders whose original text is already done are excluded, F3 falls to a largest unit of 10. Do not plan around them.
- **The blocking gap is in what no frame covers.** Only 25 of the 3,224 decided not-ready orders have every open step reachable by some frame.
  - No frame places a unit on savings_residuals (14,801 open), counterevidence (12,497) or opus_media (714).
  - clause_inventory is reached only through X1 clusters (1,233).
  - The median order still has 5 open steps, so advancing one step rarely makes an order ready. That fits Bowditch Y2, where 6% was upheld.
  - The next design question is what unit could carry savings_residuals and counterevidence, which may itself be a ruling or a template.
- **The 4,560 orders whose only blocker is NO_PROVISIONAL_STATUS are not near ready.** They still have 5 open steps each.

## Caveats

- All counts are measured from committed outputs. None of them is a yield, cost or hour estimate; `cost_usd` and `E_ready` are left empty for Llull to fill.
- The export marks every action `agent_probe`, owner questions included. The Owner, Agent and jobs/ labels in the table are my own classification. The two jobs/ labels are a guess.
- Edges and `own_term` wording are leads, not proof that an order has ended. In F2, 959 of the 2,414 actor-target records are "See:" cross-references, which point to a mention rather than an end.
- F6's NONE_listed_missing group (841 orders) comes from reading the dossiers, not from proof.
- AI statuses are hypotheses. The codebook is unchanged, and no tier or certified count changed.

SUMMARY: Treating the order as the unit gives no leverage: Gini 0, and 100 orders cover 0.7%. Six owner rulings touch 89% of not-ready orders, so the owner questions (overlay adoption 11,613, ProQuest 6,839, compiled transcription 3,216) come first. They are ceilings, not yields. The best agent units are the ACT-provision producer (1,213), the own_term families (1,066 and 650) and EO:12553 (335). Shared source documents turned out to have little leverage. The real gap is that no frame reaches savings_residuals or counterevidence, and only 25 of 3,224 decided not-ready orders are fully reachable. The cheapest readiness test is the 23 orders whose only open step is ending. Reach is not yield, and certified stays 0. Outputs are in `/home/user/Executive-Orders/jobs/polya/output/`.
