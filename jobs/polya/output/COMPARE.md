# POLYA compare (generated; repo_head cad6e4026e8a3736c3f858c69ad945135b56c1cc)

Pool: 14972 orders, 251 ready, 14721 not ready (3108 decided, 11613 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 14721 | 14721 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 69 | 5 |
| F1_ending_instrument | 1762 | 2722 | 18.5% | 0.42 | 326 | 4.3% | 7.8% | 4.3% | 43 | 5 |
| F2_actor_provision_record | 993 | 1020 | 6.9% | 0.47 | 203 | 2.5% | 4.3% | 2.8% | 20 | 3 |
| F3_source_document | 906 | 945 | 6.4% | 0.04 | 19 | 0.4% | 1.0% | 0.4% | 0 | 5 |
| F4_legal_family_template | 1568 | 3320 | 22.6% | 0.72 | 1023 | 15.1% | 18.2% | 15.4% | 47 | 4 |
| F5_owner_or_codebook_decision | 6 | 13257 | 90.1% | 0.56 | 11613 | 90.1% | 90.1% | 90.1% | 25 | 6 |
| F6_missing_input_type | 10 | 3108 | 21.1% | 0.38 | 1051 | 21.1% | 21.1% | 21.1% | 69 | 4 |
| F7_aux_current_predicate_table | 2178 | 340 | 2.3% | 0.23 | 20 | 0.6% | 1.1% | 0.6% | 0 | 4 |
| F8_work_backwards_reviewer | 164 | 106 | 0.7% | 0.37 | 23 | 0.5% | 0.7% | 0.5% | 69 | 2 |
| F9_single_blocker_frontier | 13 | 4604 | 31.3% | 0.92 | 4560 | 31.2% | 31.3% | 31.2% | 44 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 14721 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: 934820a8d9bff74c88c2e5db6cd622825344cde3743133a063ea3d79ee2b4d53

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11613 | 0 | F1/NO_hypothesis_for_undecided 1748 |
| original_text | 8100 | 1047 | F3/claim_kit_source_family 901 |
| clause_inventory | 14657 | 3044 | F4/x1_text_cluster 1223 |
| ending_or_current_basis | 14699 | 3086 | F4/claim_kit_family 2246, F2/actor_provision_record 1020, F1/ending_of_decided_NO 974, F7/current_law_citation 340 |
| savings_residuals | 14666 | 3053 | NONE |
| counterevidence | 12482 | 869 | NONE |
| shared_sources | 46 | 46 | F3/tracker_shared_source 46 |
| opus_media | 723 | 723 | NONE |

Stack: 24 of 3108 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 1361 orders: no frame reaches clause_inventory, savings_residuals
- 545 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 243 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 200 orders: no frame reaches ending_or_current_basis, savings_residuals, counterevidence
- 179 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals
- 152 orders: no frame reaches savings_residuals, counterevidence
