# POLYA compare (generated; repo_head 4fa3b3d659edf00490d5c794fe33215deb8a674c)

Pool: 14998 orders, 1255 ready, 13743 not ready (2533 decided, 11210 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13743 | 13743 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 249 | 5 |
| F1_ending_instrument | 1730 | 2493 | 18.1% | 0.39 | 242 | 3.7% | 7.1% | 3.7% | 210 | 5 |
| F2_actor_provision_record | 1348 | 975 | 7.1% | 0.41 | 132 | 2.5% | 3.8% | 2.7% | 86 | 4 |
| F3_source_document | 518 | 759 | 5.5% | 0.31 | 50 | 1.6% | 2.5% | 1.6% | 1 | 6 |
| F4_legal_family_template | 1597 | 2669 | 19.4% | 0.69 | 987 | 12.5% | 14.8% | 12.7% | 209 | 4 |
| F5_owner_or_codebook_decision | 6 | 12074 | 87.9% | 0.62 | 11210 | 87.9% | 87.9% | 87.9% | 164 | 5 |
| F6_missing_input_type | 12 | 2533 | 18.4% | 0.46 | 1128 | 18.4% | 18.4% | 18.4% | 248 | 4 |
| F7_aux_current_predicate_table | 1989 | 276 | 2.0% | 0.23 | 16 | 0.5% | 0.9% | 0.6% | 0 | 3 |
| F8_work_backwards_reviewer | 476 | 349 | 2.5% | 0.51 | 188 | 1.9% | 2.1% | 1.9% | 249 | 1 |
| F9_single_blocker_frontier | 14 | 9363 | 68.1% | 0.92 | 9145 | 68.1% | 68.1% | 68.1% | 219 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13743 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: dc8be743fbc1171a2b935cd5e6cea95407e104292487fc075e9e5975ea29c723

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11210 | 0 | F1/NO_hypothesis_for_undecided 1692 |
| original_text | 2307 | 242 | F3/claim_kit_source_family 735 |
| clause_inventory | 13499 | 2290 | F4/x1_text_cluster 911 |
| ending_or_current_basis | 13710 | 2501 | F4/claim_kit_family 1835, F2/actor_provision_record 975, F1/ending_of_decided_NO 801, F7/current_law_citation 276 |
| savings_residuals | 13512 | 2303 | NONE |
| counterevidence | 12113 | 904 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 663 | 663 | NONE |

Stack: 187 of 2533 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 740 orders: no frame reaches clause_inventory, savings_residuals
- 477 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 453 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 213 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 187 orders: no frame reaches (none)
- 92 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
