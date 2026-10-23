# POLYA compare (generated; repo_head 49e79c2f6bc7ea6d7b29669b9e9d361ce7ce7c54)

Pool: 14972 orders, 280 ready, 14692 not ready (3123 decided, 11569 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 14692 | 14692 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 71 | 5 |
| F1_ending_instrument | 1777 | 2693 | 18.3% | 0.42 | 312 | 4.1% | 7.6% | 4.1% | 44 | 5 |
| F2_actor_provision_record | 1018 | 992 | 6.8% | 0.45 | 173 | 2.2% | 4.0% | 2.4% | 20 | 3 |
| F3_source_document | 994 | 1048 | 7.1% | 0.05 | 24 | 0.4% | 1.1% | 0.4% | 0 | 5 |
| F4_legal_family_template | 1664 | 3388 | 23.1% | 0.72 | 1064 | 15.2% | 18.7% | 15.8% | 48 | 4 |
| F5_owner_or_codebook_decision | 6 | 13225 | 90.0% | 0.55 | 11569 | 90.0% | 90.0% | 90.0% | 26 | 6 |
| F6_missing_input_type | 10 | 3123 | 21.3% | 0.40 | 1051 | 21.3% | 21.3% | 21.3% | 71 | 4 |
| F7_aux_current_predicate_table | 2178 | 340 | 2.3% | 0.23 | 20 | 0.6% | 1.1% | 0.6% | 0 | 4 |
| F8_work_backwards_reviewer | 169 | 108 | 0.7% | 0.37 | 23 | 0.5% | 0.7% | 0.5% | 71 | 2 |
| F9_single_blocker_frontier | 13 | 4561 | 31.0% | 0.92 | 4516 | 31.0% | 31.0% | 31.0% | 45 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 14692 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: 164d5849cd8c4a1fbb64249288ec1502b1aed1da75cbb8cba1e110545cb92444

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11569 | 0 | F1/NO_hypothesis_for_undecided 1712 |
| original_text | 8100 | 1047 | F3/claim_kit_source_family 1024 |
| clause_inventory | 14627 | 3058 | F4/x1_text_cluster 1223 |
| ending_or_current_basis | 14669 | 3100 | F4/claim_kit_family 2314, F2/actor_provision_record 992, F1/ending_of_decided_NO 981, F7/current_law_citation 340 |
| savings_residuals | 14636 | 3067 | NONE |
| counterevidence | 12438 | 869 | NONE |
| shared_sources | 27 | 27 | F3/tracker_shared_source 27 |
| opus_media | 719 | 719 | NONE |

Stack: 24 of 3123 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 1381 orders: no frame reaches clause_inventory, savings_residuals
- 541 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 320 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 200 orders: no frame reaches ending_or_current_basis, savings_residuals, counterevidence
- 177 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
- 152 orders: no frame reaches savings_residuals, counterevidence
