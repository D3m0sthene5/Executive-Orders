# POLYA compare (generated; repo_head 46f91fdac2943f27dca5940ca874132738199104)

Pool: 14972 orders, 135 ready, 14837 not ready (3224 decided, 11613 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 14837 | 14837 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 51 | 5 |
| F1_ending_instrument | 1772 | 2843 | 19.2% | 0.44 | 335 | 4.6% | 8.5% | 4.6% | 43 | 5 |
| F2_actor_provision_record | 1050 | 1212 | 8.2% | 0.50 | 334 | 3.5% | 5.3% | 3.8% | 21 | 3 |
| F3_source_document | 905 | 926 | 6.2% | 0.02 | 10 | 0.2% | 0.8% | 0.2% | 0 | 5 |
| F4_legal_family_template | 1595 | 3431 | 23.1% | 0.71 | 1066 | 15.5% | 18.7% | 15.8% | 47 | 4 |
| F5_owner_or_codebook_decision | 6 | 13265 | 89.4% | 0.58 | 11613 | 89.4% | 89.4% | 89.4% | 14 | 6 |
| F6_missing_input_type | 10 | 3224 | 21.7% | 0.38 | 1213 | 21.7% | 21.7% | 21.7% | 51 | 4 |
| F7_aux_current_predicate_table | 2195 | 346 | 2.3% | 0.23 | 20 | 0.5% | 1.0% | 0.6% | 0 | 4 |
| F8_work_backwards_reviewer | 128 | 90 | 0.6% | 0.37 | 23 | 0.3% | 0.6% | 0.4% | 51 | 2 |
| F9_single_blocker_frontier | 4 | 4586 | 30.9% | 0.75 | 4560 | 30.9% | 30.9% | 30.9% | 26 | 5 |

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11613 | 0 | F1/NO_hypothesis_for_undecided 1748 |
| original_text | 8100 | 1047 | F3/claim_kit_source_family 901 |
| clause_inventory | 14789 | 3176 | F4/x1_text_cluster 1233 |
| ending_or_current_basis | 14833 | 3220 | F4/claim_kit_family 2353, F2/actor_provision_record 1212, F1/ending_of_decided_NO 1095, F7/current_law_citation 346 |
| savings_residuals | 14801 | 3188 | NONE |
| counterevidence | 12497 | 884 | NONE |
| shared_sources | 27 | 27 | F3/tracker_shared_source 27 |
| opus_media | 714 | 714 | NONE |

Stack: 25 of 3224 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 1469 orders: no frame reaches clause_inventory, savings_residuals
- 546 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 266 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 198 orders: no frame reaches ending_or_current_basis, savings_residuals, counterevidence
- 180 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
- 152 orders: no frame reaches savings_residuals, counterevidence
