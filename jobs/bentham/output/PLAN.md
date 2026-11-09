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
| 6 | acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND | acquisition | 0 | 0.0 | 0.0 | free | ∞ | free |
| 7 | recovery.custody_stranded | recovery | 8 | 5.1 | 0.0 | $1.85 | 276.7 | $1.85 |
| 8 | recovery.working_text_stale | recovery | 26 | 16.6 | 0.0 | $6.00 | 276.7 | $7.85 |
| 9 | production.one_step_away | production | 216 | 137.9 | 0.0 | $72 | 192.0 | $80 |
| 10 | production.claim_ready.yes.fr | production | 351 | 81.9 | 0.0 | $117 | 70.2 | $196 |
| 11 | acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 1.2 | $3.21 | 36.6 | $200 |
| 12 | status_assignment.undecided | status_assignment | 10697 | 1069.7 | 0.0 | $3,557 | 30.1 | $3,756 |
| 13 | production.claim_ready.no.fr | production | 1034 | 34.5 | 0.0 | $344 | 10.0 | $4,100 |
| 14 | acquire.ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,100 |
| 15 | zero_agent.opus_media_refetch | zero_agent | 0 | 0.0 | 0.0 | free | 0.0 | $4,100 |
| 16 | acquire.nea_continuation_notices | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,100 |
| 17 | acquire.current_law_sections | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,100 |

Context per attempted order (last measured production wave): 751,017 tokens, of which 723,973 cache reads; 3.6 model turns. Smaller packets and fewer turns lower every production cost above.

Untested savers that would lower every cost above (Junto, measured cost at stake in past waves; not savings until a two-arm `junto.py add-test` verifies them; see jobs/junto/output/OPEN_TESTS.md):

- `lean_coordination`: $694 spent in this pattern (unverified)
- `revere_phase_handoff`: $249 spent in this pattern (unverified)
- `idle_cache_avoidance`: $137 spent in this pattern (unverified)

Measured waves (Kean findings' structured measures; list-price dollars; not pooled into the rates above):

| Wave | $ total | Coordinator share | Attempted | Filed | $ per filed | Controls missed |
|---|---:|---:|---:|---:|---:|---:|
| cujas-2026-11-08 | $23 | 34% | 75 | 68 | $0.34 | 0 of 6 |
| gutenberg-2026-11-09 | $28 | 100% |  |  |  |  |
| haloander-2026-11-07 | $63 | 72% |  |  |  |  |

Ranking by subscription window tokens (cache reads weighted 1.0 and 0.1; the plan's real weighting is not published):

- cache_read_weight_1.0: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.working_text_stale, recovery.custody_stranded ...
- cache_read_weight_0.1: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK, recovery.working_text_stale, recovery.custody_stranded ...
- **Rank flips against the dollar ranking: 24** cache_read_weight_1.0: recovery.custody_stranded before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND; cache_read_weight_1.0: recovery.working_text_stale before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND; cache_read_weight_1.0: production.one_step_away before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND; cache_read_weight_1.0: production.claim_ready.yes.fr before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND; cache_read_weight_1.0: acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND; cache_read_weight_1.0: status_assignment.undecided before acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND

The choice of actions within budget does not change between 30- and 180-day discounts.

Each production action runs in batches under `bentham.py gate`, which stops it when its observed yield per dollar falls below the next action's.

