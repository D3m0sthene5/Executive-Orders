# POLYA compare (generated; repo_head c6cf0a9544831894ebfee175d2fb19dabfeb9c88)

Pool: 14972 orders, 287 ready, 14685 not ready (3116 decided, 11569 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 14685 | 14685 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 70 | 5 |
| F1_ending_instrument | 1777 | 2691 | 18.3% | 0.42 | 312 | 4.1% | 7.6% | 4.1% | 48 | 5 |
| F2_actor_provision_record | 1018 | 992 | 6.8% | 0.45 | 173 | 2.2% | 4.0% | 2.4% | 23 | 3 |
| F3_source_document | 993 | 1047 | 7.1% | 0.05 | 24 | 0.4% | 1.1% | 0.4% | 0 | 5 |
| F4_legal_family_template | 1657 | 3386 | 23.1% | 0.72 | 1063 | 15.2% | 18.7% | 15.8% | 52 | 4 |
| F5_owner_or_codebook_decision | 6 | 13222 | 90.0% | 0.55 | 11569 | 90.0% | 90.0% | 90.0% | 27 | 6 |
| F6_missing_input_type | 11 | 3116 | 21.2% | 0.43 | 1051 | 21.2% | 21.2% | 21.2% | 70 | 4 |
| F7_aux_current_predicate_table | 2178 | 340 | 2.3% | 0.23 | 20 | 0.6% | 1.1% | 0.6% | 0 | 4 |
| F8_work_backwards_reviewer | 165 | 108 | 0.7% | 0.38 | 23 | 0.5% | 0.7% | 0.5% | 70 | 2 |
| F9_single_blocker_frontier | 12 | 4556 | 31.0% | 0.91 | 4516 | 31.0% | 31.0% | 31.0% | 40 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 14685 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: 2e1673e7d6aaa995e01db07ea8df2faf12df4b0c09c65949ed412fd3b64a031e

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11569 | 0 | F1/NO_hypothesis_for_undecided 1712 |
| original_text | 8099 | 1046 | F3/claim_kit_source_family 1023 |
| clause_inventory | 14621 | 3052 | F4/x1_text_cluster 1223 |
| ending_or_current_basis | 14667 | 3098 | F4/claim_kit_family 2312, F2/actor_provision_record 992, F1/ending_of_decided_NO 979, F7/current_law_citation 340 |
| savings_residuals | 14634 | 3065 | NONE |
| counterevidence | 12438 | 869 | NONE |
| shared_sources | 27 | 27 | F3/tracker_shared_source 27 |
| opus_media | 714 | 714 | NONE |

Stack: 24 of 3116 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 1375 orders: no frame reaches clause_inventory, savings_residuals
- 541 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 320 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 200 orders: no frame reaches ending_or_current_basis, savings_residuals, counterevidence
- 177 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
- 152 orders: no frame reaches savings_residuals, counterevidence
