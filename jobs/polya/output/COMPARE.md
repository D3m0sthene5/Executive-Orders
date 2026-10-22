# POLYA compare (generated; repo_head 7eabfc9de01a66a6629bd017c540ae52066dc68e)

Pool: 14972 orders, 280 ready, 14692 not ready (3079 decided, 11613 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 14692 | 14692 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 69 | 5 |
| F1_ending_instrument | 1762 | 2694 | 18.3% | 0.42 | 311 | 4.1% | 7.6% | 4.1% | 43 | 5 |
| F2_actor_provision_record | 992 | 971 | 6.6% | 0.45 | 171 | 2.2% | 3.9% | 2.4% | 20 | 3 |
| F3_source_document | 994 | 1048 | 7.1% | 0.05 | 24 | 0.4% | 1.1% | 0.4% | 0 | 5 |
| F4_legal_family_template | 1575 | 3345 | 22.8% | 0.72 | 1041 | 15.4% | 18.5% | 15.6% | 47 | 4 |
| F5_owner_or_codebook_decision | 6 | 13264 | 90.3% | 0.55 | 11613 | 90.3% | 90.3% | 90.3% | 25 | 6 |
| F6_missing_input_type | 10 | 3079 | 21.0% | 0.40 | 1051 | 21.0% | 21.0% | 21.0% | 69 | 4 |
| F7_aux_current_predicate_table | 2178 | 340 | 2.3% | 0.23 | 20 | 0.6% | 1.1% | 0.6% | 0 | 4 |
| F8_work_backwards_reviewer | 164 | 106 | 0.7% | 0.37 | 23 | 0.5% | 0.7% | 0.5% | 69 | 2 |
| F9_single_blocker_frontier | 13 | 4604 | 31.3% | 0.92 | 4560 | 31.3% | 31.3% | 31.3% | 44 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 14692 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: 75e84c2aa16cbb77c9e34af97e5cdf9bb74146922293cef05f5c3d9c552a9c6c

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11613 | 0 | F1/NO_hypothesis_for_undecided 1748 |
| original_text | 8100 | 1047 | F3/claim_kit_source_family 1024 |
| clause_inventory | 14628 | 3015 | F4/x1_text_cluster 1223 |
| ending_or_current_basis | 14670 | 3057 | F4/claim_kit_family 2271, F2/actor_provision_record 971, F1/ending_of_decided_NO 946, F7/current_law_citation 340 |
| savings_residuals | 14637 | 3024 | NONE |
| counterevidence | 12482 | 869 | NONE |
| shared_sources | 27 | 27 | F3/tracker_shared_source 27 |
| opus_media | 719 | 719 | NONE |

Stack: 24 of 3079 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 1339 orders: no frame reaches clause_inventory, savings_residuals
- 541 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 320 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 200 orders: no frame reaches ending_or_current_basis, savings_residuals, counterevidence
- 177 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
- 152 orders: no frame reaches savings_residuals, counterevidence
