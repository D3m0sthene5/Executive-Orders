# Bentham plan: where the next agent tokens go

Ranked by expected dossiers (now plus those the action makes possible later, discounted at a 60-day half-life) per API-equivalent dollar, from measured past waves.

Weekly allowance: not recorded, so no percent-of-week figures. Record one measured week in `jobs/bentham/data/ALLOWANCE.json` (see README).

| # | Action | Kind | Orders | Dossiers now | Later (fecundity) | Cost | Dossiers per $100 | Cumulative cost |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | acquire.shared.EO_4314 | acquisition | 0 | 0.0 | 3.7 | free | ∞ | free |
| 2 | acquire.shared.EO_6868 | acquisition | 0 | 0.0 | 2.8 | free | ∞ | free |
| 3 | acquire.shared.EO_6964 | acquisition | 0 | 0.0 | 0.9 | free | ∞ | free |
| 4 | acquire.shared.EO_6910 | acquisition | 0 | 0.0 | 1.4 | free | ∞ | free |
| 5 | acquire.shared.CFR_26_CFR_458.324 | acquisition | 0 | 0.0 | 0.9 | free | ∞ | free |
| 6 | acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND | acquisition | 0 | 0.0 | 30.3 | free | ∞ | free |
| 7 | recovery.custody_stranded | recovery | 48 | 30.7 | 0.0 | $19 | 159.9 | $19 |
| 8 | acquire.ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 0.5 | $0.38 | 122.3 | $20 |
| 9 | acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 16.7 | $17 | 99.0 | $36 |
| 10 | production.one_step_away | production | 40 | 25.5 | 0.0 | $26 | 98.8 | $62 |
| 11 | production.claim_ready.no.fr | production | 944 | 449.2 | 0.0 | $610 | 73.6 | $672 |
| 12 | zero_agent.opus_media_refetch | zero_agent | 0 | 0.0 | 0.0 | free | 0.0 | $672 |
| 13 | acquire.nea_continuation_notices | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $672 |
| 14 | acquire.current_law_sections | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $672 |

Unranked (a yield or cost is not measured; Bentham will not guess). For a production stratum the next step is a 30-order probe, run under the gate, that measures its yield:

- production.claim_ready.yes.fr (365 orders): yield 'filed_per_attempt.yes.fr' rests on 0/7 attempts, fewer than 30: too thin to rank. Probe: 30 orders, about $19.

The choice of actions within budget does not change between 30- and 180-day discounts.

Each production action runs in batches under `bentham.py gate`, which stops it when its observed yield per dollar falls below the next action's.

