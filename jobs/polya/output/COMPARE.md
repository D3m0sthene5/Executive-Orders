# POLYA compare (generated; repo_head cbf9694a8430e2a67afd67a204073571afb327d6)

Pool: 14998 orders, 1083 ready, 13915 not ready (3218 decided, 10697 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13915 | 13915 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 247 | 5 |
| F1_ending_instrument | 1738 | 2504 | 18.0% | 0.39 | 242 | 3.6% | 7.0% | 3.6% | 212 | 5 |
| F2_actor_provision_record | 1482 | 1106 | 8.0% | 0.39 | 132 | 2.5% | 3.9% | 2.7% | 92 | 4 |
| F3_source_document | 517 | 758 | 5.5% | 0.31 | 50 | 1.6% | 2.5% | 1.6% | 1 | 5 |
| F4_legal_family_template | 1586 | 2845 | 20.4% | 0.70 | 1052 | 14.0% | 16.2% | 14.2% | 215 | 4 |
| F5_owner_or_codebook_decision | 6 | 12071 | 86.8% | 0.62 | 10697 | 86.8% | 86.8% | 86.8% | 161 | 5 |
| F6_missing_input_type | 12 | 3218 | 23.1% | 0.53 | 1705 | 23.1% | 23.1% | 23.1% | 247 | 4 |
| F7_aux_current_predicate_table | 2060 | 319 | 2.3% | 0.23 | 20 | 0.6% | 1.0% | 0.6% | 0 | 3 |
| F8_work_backwards_reviewer | 586 | 447 | 3.2% | 0.47 | 194 | 1.8% | 2.2% | 1.9% | 247 | 2 |
| F9_single_blocker_frontier | 13 | 9355 | 67.2% | 0.92 | 9138 | 67.2% | 67.2% | 67.2% | 217 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13915 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: b3c0844894201165cca7e5c45185cfc30dfd56e27bb1a04de02998b5d8222f55

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 10697 | 0 | F1/NO_hypothesis_for_undecided 1698 |
| original_text | 2298 | 739 | F3/claim_kit_source_family 734 |
| clause_inventory | 13673 | 2976 | F4/x1_text_cluster 827 |
| ending_or_current_basis | 13890 | 3193 | F4/claim_kit_family 2075, F2/actor_provision_record 1106, F1/ending_of_decided_NO 806, F7/current_law_citation 319 |
| savings_residuals | 13686 | 2989 | NONE |
| counterevidence | 12124 | 1427 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 700 | 700 | NONE |

Stack: 193 of 3218 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 856 orders: no frame reaches clause_inventory, savings_residuals
- 629 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 588 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 516 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 193 orders: no frame reaches (none)
- 97 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
