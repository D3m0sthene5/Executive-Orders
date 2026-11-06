# POLYA compare (generated; repo_head f6035841319f3df5dde98d6f60e7ad9a0fe40f21)

Pool: 14972 orders, 1323 ready, 13649 not ready (2968 decided, 10681 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13649 | 13649 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 72 | 5 |
| F1_ending_instrument | 1741 | 2337 | 17.1% | 0.36 | 99 | 2.6% | 5.9% | 2.6% | 45 | 5 |
| F2_actor_provision_record | 1426 | 1004 | 7.4% | 0.38 | 79 | 2.1% | 3.6% | 2.4% | 23 | 4 |
| F3_source_document | 803 | 1063 | 7.8% | 0.24 | 50 | 1.7% | 2.6% | 1.7% | 1 | 5 |
| F4_legal_family_template | 1641 | 3069 | 22.5% | 0.68 | 998 | 12.9% | 16.2% | 13.2% | 49 | 5 |
| F5_owner_or_codebook_decision | 6 | 12194 | 89.3% | 0.58 | 10681 | 89.3% | 89.3% | 89.3% | 24 | 5 |
| F6_missing_input_type | 12 | 2968 | 21.8% | 0.55 | 1707 | 21.8% | 21.8% | 21.8% | 72 | 4 |
| F7_aux_current_predicate_table | 2162 | 338 | 2.5% | 0.23 | 20 | 0.6% | 1.1% | 0.7% | 0 | 4 |
| F8_work_backwards_reviewer | 280 | 182 | 1.3% | 0.32 | 22 | 0.6% | 0.9% | 0.6% | 72 | 3 |
| F9_single_blocker_frontier | 15 | 6228 | 45.6% | 0.93 | 6188 | 45.6% | 45.6% | 45.6% | 40 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13649 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: c5b6b22134a3850485bb8ee60a1f61267abdf3de3ff7887d35ea3bddeb71aa78

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 10681 | 0 | F1/NO_hypothesis_for_undecided 1705 |
| original_text | 5559 | 1066 | F3/claim_kit_source_family 1041 |
| clause_inventory | 13584 | 2903 | F4/x1_text_cluster 1331 |
| ending_or_current_basis | 13626 | 2945 | F4/claim_kit_family 1777, F2/actor_provision_record 1004, F1/ending_of_decided_NO 632, F7/current_law_citation 338 |
| savings_residuals | 13596 | 2915 | NONE |
| counterevidence | 12116 | 1435 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 714 | 714 | NONE |

Stack: 21 of 2968 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 756 orders: no frame reaches clause_inventory, savings_residuals
- 612 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 608 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 535 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 99 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
- 85 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
