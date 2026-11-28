# POLYA compare (generated; repo_head 9114d26127ece6a867b5e3b8d9619221c54625c1)

Pool: 15003 orders, 1395 ready, 13608 not ready (2406 decided, 11202 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13608 | 13608 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 224 | 5 |
| F1_ending_instrument | 1728 | 2459 | 18.1% | 0.39 | 212 | 3.5% | 6.9% | 3.5% | 180 | 5 |
| F2_actor_provision_record | 1333 | 927 | 6.8% | 0.40 | 127 | 2.2% | 3.6% | 2.5% | 79 | 4 |
| F3_source_document | 22 | 42 | 0.3% | 0.40 | 10 | 0.2% | 0.3% | 0.2% | 1 | 5 |
| F4_legal_family_template | 1675 | 3193 | 23.5% | 0.66 | 868 | 12.0% | 16.1% | 12.7% | 180 | 4 |
| F5_owner_or_codebook_decision | 6 | 11766 | 86.5% | 0.78 | 11202 | 86.5% | 86.5% | 86.5% | 135 | 5 |
| F6_missing_input_type | 12 | 2406 | 17.7% | 0.50 | 1166 | 17.7% | 17.7% | 17.7% | 223 | 4 |
| F7_aux_current_predicate_table | 1726 | 210 | 1.5% | 0.20 | 13 | 0.4% | 0.8% | 0.5% | 0 | 3 |
| F8_work_backwards_reviewer | 442 | 302 | 2.2% | 0.50 | 158 | 1.7% | 1.9% | 1.8% | 224 | 1 |
| F9_single_blocker_frontier | 13 | 11176 | 82.1% | 0.92 | 10983 | 82.1% | 82.1% | 82.1% | 194 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13608 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: ffea25fdf45cf3bfa35949f14e5f000c5f20388f069f4bd700bc2e86e83d53ce

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11202 | 0 | F1/NO_hypothesis_for_undecided 1689 |
| original_text | 240 | 21 | F3/claim_kit_source_family 18 |
| clause_inventory | 13389 | 2188 | F4/x1_text_cluster 1589 |
| ending_or_current_basis | 13570 | 2369 | F4/claim_kit_family 1675, F2/actor_provision_record 927, F1/ending_of_decided_NO 770, F7/current_law_citation 210 |
| savings_residuals | 13402 | 2201 | NONE |
| counterevidence | 12103 | 902 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 638 | 638 | NONE |

Stack: 157 of 2406 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 671 orders: no frame reaches clause_inventory, savings_residuals
- 448 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 448 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 211 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 157 orders: no frame reaches (none)
- 89 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
