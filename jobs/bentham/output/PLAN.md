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
| 7 | recovery.custody_stranded | recovery | 6 | 3.8 | 0.0 | $1.38 | 276.7 | $1.38 |
| 8 | recovery.working_text_stale | recovery | 26 | 16.6 | 0.0 | $6.00 | 276.7 | $7.38 |
| 9 | production.one_step_away | production | 215 | 137.3 | 0.0 | $71 | 192.0 | $79 |
| 10 | production.claim_ready.yes.fr | production | 296 | 69.1 | 0.0 | $98 | 70.2 | $177 |
| 11 | acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 1.3 | $3.74 | 33.9 | $181 |
| 12 | status_assignment.undecided | status_assignment | 10691 | 1069.1 | 0.0 | $3,555 | 30.1 | $3,736 |
| 13 | production.claim_ready.no.fr | production | 1024 | 34.1 | 0.0 | $340 | 10.0 | $4,076 |
| 14 | acquire.ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,076 |
| 15 | zero_agent.opus_media_refetch | zero_agent | 0 | 0.0 | 0.0 | free | 0.0 | $4,076 |
| 16 | acquire.nea_continuation_notices | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,076 |
| 17 | acquire.current_law_sections | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,076 |

Context per attempted order (last measured production wave): 751,017 tokens, of which 723,973 cache reads; 3.6 model turns. Smaller packets and fewer turns lower every production cost above.

Untested savers that would lower every cost above (Junto, measured cost at stake in past waves; not savings until a two-arm `junto.py add-test` verifies them; see jobs/junto/output/OPEN_TESTS.md):

- `lean_coordination`: $694 spent in this pattern (unverified)
- `revere_phase_handoff`: $249 spent in this pattern (unverified)
- `idle_cache_avoidance`: $137 spent in this pattern (unverified)

Measured waves (Kean findings' structured measures; list-price dollars; not pooled into the rates above):

| Wave | $ total | Coordinator share | Attempted | Filed | $ per filed | Controls missed |
|---|---:|---:|---:|---:|---:|---:|
| 2026-11-10-papinian | $297 | 17% | 467 | 63 | $4.71 | 0 of 18 |
| cujas-2026-11-08 | $23 | 34% | 75 | 68 | $0.34 | 0 of 6 |
| gutenberg-2026-11-09 | $28 | 100% |  |  |  |  |
| haloander-2026-11-07 | $63 | 72% |  |  |  |  |

Ranking by subscription window tokens (cache reads weighted 1.0 and 0.1; the plan's real weighting is not published):

- cache_read_weight_1.0: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.working_text_stale ...
- cache_read_weight_0.1: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.working_text_stale ...
- **Rank flips against the dollar ranking: 10** cache_read_weight_1.0: recovery.working_text_stale before recovery.custody_stranded; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before recovery.custody_stranded; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before recovery.working_text_stale; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.one_step_away; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before production.claim_ready.yes.fr; cache_read_weight_0.1: recovery.working_text_stale before recovery.custody_stranded

The choice of actions within budget does not change between 30- and 180-day discounts.

Each production action runs in batches under `bentham.py gate`, which stops it when its observed yield per dollar falls below the next action's.

