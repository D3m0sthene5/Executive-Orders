# Bentham plan: where the next agent tokens go

Ranked by expected dossiers (now plus those the action makes possible later, discounted at a 60-day half-life) per API-equivalent dollar, from measured past waves.

Weekly allowance: not recorded, so no percent-of-week figures. Record one measured week in `jobs/bentham/data/ALLOWANCE.json` (see README).

| # | Action | Kind | Orders | Dossiers now | Later (fecundity) | Cost | Dossiers per $100 | Cumulative cost |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | acquire.shared.EO_4314 | acquisition | 0 | 0.0 | 0.3 | free | ∞ | free |
| 2 | acquire.shared.EO_6868 | acquisition | 0 | 0.0 | 0.2 | free | ∞ | free |
| 3 | acquire.shared.EO_6964 | acquisition | 0 | 0.0 | 0.1 | free | ∞ | free |
| 4 | acquire.shared.EO_6910 | acquisition | 0 | 0.0 | 0.1 | free | ∞ | free |
| 5 | acquire.shared.CFR_26_CFR_458.324 | acquisition | 0 | 0.0 | 0.1 | free | ∞ | free |
| 6 | acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND | acquisition | 0 | 0.0 | 0.1 | free | ∞ | free |
| 7 | probe.status_assignment.undecided | probe | 30 | 0.0 | 0.0 | $19 | ∞ | $19 |
| 8 | recovery.custody_stranded | recovery | 48 | 30.7 | 0.0 | $19 | 159.9 | $39 |
| 9 | production.one_step_away (over budget) | production | 219 | 139.8 | 0.0 | $142 | 98.8 | $39 |
| 10 | production.claim_ready.yes.fr (over budget) | production | 345 | 80.5 | 0.0 | $223 | 36.1 | $39 |
| 11 | acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 3.2 | $17 | 19.3 | $55 |
| 12 | production.claim_ready.no.fr (over budget) | production | 1193 | 39.8 | 0.0 | $771 | 5.2 | $55 |
| 13 | acquire.ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $55 |
| 14 | zero_agent.opus_media_refetch | zero_agent | 0 | 0.0 | 0.0 | free | 0.0 | $55 |
| 15 | acquire.nea_continuation_notices | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $55 |
| 16 | acquire.current_law_sections | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $55 |

Unranked (a yield or cost is not measured; Bentham will not guess). For a production stratum the next step is a 30-order probe, run under the gate, that measures its yield:

- status_assignment.undecided (10700 orders): no measured yield for 'filed_per_attempt.undecided': unranked. Ranked above as `probe.status_assignment.undecided`: 30 orders, about $19; an unmeasured stratum is never left unranked for a second plan.

Context per attempted order (last measured production wave): 751,017 tokens, of which 723,973 cache reads; 3.6 model turns. Smaller packets and fewer turns lower every production cost above.

Ranking by subscription window tokens (cache reads weighted 1.0 and 0.1; the plan's real weighting is not published):

- cache_read_weight_1.0: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.custody_stranded ...
- cache_read_weight_0.1: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.custody_stranded ...
- **Rank flips against the dollar ranking: 6** cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before recovery.custody_stranded; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.one_step_away; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.claim_ready.yes.fr; cache_read_weight_0.1: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before recovery.custody_stranded; cache_read_weight_0.1: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.one_step_away; cache_read_weight_0.1: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.claim_ready.yes.fr

Budget line moves with the delay discount:

- at 30 days: enters none, leaves ['probe.status_assignment.undecided']
- at 180 days: enters none, leaves ['probe.status_assignment.undecided']

Each production action runs in batches under `bentham.py gate`, which stops it when its observed yield per dollar falls below the next action's.

