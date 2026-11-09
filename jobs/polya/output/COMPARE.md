# POLYA compare (generated; repo_head dafadcb0ba604a1e123b25c5f32ac66fade7e9df)

Pool: 14998 orders, 1179 ready, 13819 not ready (3122 decided, 10697 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13819 | 13819 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 246 | 5 |
| F1_ending_instrument | 1736 | 2505 | 18.1% | 0.39 | 242 | 3.6% | 7.1% | 3.6% | 211 | 5 |
| F2_actor_provision_record | 1447 | 1078 | 7.8% | 0.40 | 132 | 2.5% | 3.9% | 2.7% | 92 | 4 |
| F3_source_document | 506 | 755 | 5.5% | 0.32 | 50 | 1.6% | 2.5% | 1.6% | 1 | 5 |
| F4_legal_family_template | 1586 | 2752 | 19.9% | 0.70 | 1053 | 13.4% | 15.7% | 13.6% | 214 | 4 |
| F5_owner_or_codebook_decision | 6 | 12074 | 87.4% | 0.62 | 10697 | 87.4% | 87.4% | 87.4% | 161 | 5 |
| F6_missing_input_type | 12 | 3122 | 22.6% | 0.52 | 1605 | 22.6% | 22.6% | 22.6% | 246 | 4 |
| F7_aux_current_predicate_table | 2060 | 319 | 2.3% | 0.23 | 20 | 0.6% | 1.1% | 0.6% | 0 | 3 |
| F8_work_backwards_reviewer | 483 | 351 | 2.5% | 0.51 | 193 | 1.8% | 2.1% | 1.9% | 246 | 1 |
| F9_single_blocker_frontier | 13 | 9406 | 68.1% | 0.92 | 9190 | 68.0% | 68.1% | 68.0% | 216 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13819 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: d7d0052adcf999d376528acbc76fa66a25ca9d816361a7b5d8baec50ba91feed

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 10697 | 0 | F1/NO_hypothesis_for_undecided 1698 |
| original_text | 2243 | 736 | F3/claim_kit_source_family 731 |
| clause_inventory | 13578 | 2881 | F4/x1_text_cluster 829 |
| ending_or_current_basis | 13794 | 3097 | F4/claim_kit_family 1980, F2/actor_provision_record 1078, F1/ending_of_decided_NO 807, F7/current_law_citation 319 |
| savings_residuals | 13591 | 2894 | NONE |
| counterevidence | 12124 | 1427 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 700 | 700 | NONE |

Stack: 192 of 3122 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 762 orders: no frame reaches clause_inventory, savings_residuals
- 629 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 588 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 516 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 192 orders: no frame reaches (none)
- 97 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
