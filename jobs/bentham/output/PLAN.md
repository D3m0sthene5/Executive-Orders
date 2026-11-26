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
| 6 | recovery.working_text_stale | recovery | 2 | 1.3 | 0.0 | $0.46 | 276.7 | $0.46 |
| 7 | recovery.custody_stranded | recovery | 5 | 3.2 | 0.0 | $1.15 | 276.7 | $1.61 |
| 8 | production.one_step_away | production | 192 | 122.6 | 0.0 | $64 | 192.0 | $65 |
| 9 | acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK | acquisition | 1 | 0.0 | 0.2 | $0.18 | 128.0 | $66 |
| 10 | production.claim_ready.yes.fr | production | 223 | 52.0 | 0.0 | $74 | 70.2 | $140 |
| 11 | status_assignment.undecided | status_assignment | 11202 | 1120.2 | 0.0 | $3,725 | 30.1 | $3,864 |
| 12 | production.claim_ready.no.fr | production | 1042 | 34.7 | 0.0 | $346 | 10.0 | $4,211 |
| 13 | acquire.ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |
| 14 | acquire.ONLY_COMPILED_TRANSCRIPTION_FOUND | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |
| 15 | zero_agent.opus_media_refetch | zero_agent | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |
| 16 | acquire.nea_continuation_notices | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |
| 17 | acquire.current_law_sections | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |
| 18 | acquire.cruden_fr_statute_concordance | acquisition | 0 | 0.0 | 0.0 | free | 0.0 | $4,211 |

Context per attempted order (last measured production wave): 751,017 tokens, of which 723,973 cache reads; 3.6 model turns. Smaller packets and fewer turns lower every production cost above.

Untested savers that would lower every cost above (Junto, measured cost at stake in past waves; not savings until a two-arm `junto.py add-test` verifies them; see jobs/junto/output/OPEN_TESTS.md):

- `lean_coordination`: $694 spent in this pattern (unverified)
- `revere_phase_handoff`: $249 spent in this pattern (unverified)
- `idle_cache_avoidance`: $137 spent in this pattern (unverified)

Measured waves (Kean findings' structured measures; list-price dollars; not pooled into the rates above):

| Wave | $ total | Coordinator share | Attempted | Filed | $ per filed | Controls missed |
|---|---:|---:|---:|---:|---:|---:|
| 2026-11-10-mommsen-1 |  |  | 288 | 7 |  | 0 of 5 |
| 2026-11-10-mommsen-2 |  |  | 0 | 0 |  | 0 of 0 |
| 2026-11-10-mommsen-3 |  |  | 30 | 0 |  | 0 of 1 |
| 2026-11-10-mommsen-4-c15 |  |  | 0 | 0 |  | 0 of 0 |
| 2026-11-10-papinian | $297 | 17% | 467 | 63 | $4.71 | 0 of 18 |
| 2026-11-10-respondendi | $273 | 7% | 0 | 0 |  | 0 of 0 |
| accursius-2026-11-10 | $182 | 28% |  |  |  |  |
| bracton-2026-11-25 | $107 |  | 161 | 8 | $13 | 0 of 13 |
| cujas-2026-11-08 | $23 | 34% | 75 | 68 | $0.34 | 0 of 6 |
| gutenberg-2026-11-09 | $28 | 100% |  |  |  |  |
| haloander-2026-11-07 | $63 | 72% |  |  |  |  |
| junto-lean-2026-11-25 |  |  | 59 | 8 |  | 0 of 5 |
| kiaer-2026-11-18 | $65 |  | 80 | 0 |  | 1 of 9 |
| lind-stage0-2026-11-12 | $23 | 44% | 30 | 0 |  | 0 of 1 |
| photius-peiresc-2026-11-25-full | $35 |  | 2084 | 0 |  | 0 of 0 |
| photius-peiresc-2026-11-25-s0 | $1.15 |  | 17 | 0 |  | 0 of 0 |
| stateless-gauge-2026-11-25 | $25 |  | 55 | 0 |  | 0 of 16 |

Ranking by subscription window tokens (cache reads weighted 1.0 and 0.1; the plan's real weighting is not published):

- cache_read_weight_1.0: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, recovery.working_text_stale, recovery.custody_stranded, production.one_step_away ...
- cache_read_weight_0.1: acquire.shared.EO_4314, acquire.shared.EO_6868, acquire.shared.EO_6964, acquire.shared.EO_6910, acquire.shared.CFR_26_CFR_458.324, recovery.working_text_stale, recovery.custody_stranded, production.one_step_away ...
- No rank flips against the dollar ranking.

The choice of actions within budget does not change between 30- and 180-day discounts.

Each production action runs in batches under `bentham.py gate`, which stops it when its observed yield per dollar falls below the next action's.

