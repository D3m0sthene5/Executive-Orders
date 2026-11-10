# POLYA compare (generated; repo_head 97d287c63f4cb759f6faf78de30a2ce822ac2167)

Pool: 14998 orders, 1248 ready, 13750 not ready (3059 decided, 10691 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13750 | 13750 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 245 | 5 |
| F1_ending_instrument | 1730 | 2493 | 18.1% | 0.39 | 242 | 3.7% | 7.1% | 3.7% | 210 | 5 |
| F2_actor_provision_record | 1463 | 1064 | 7.7% | 0.40 | 132 | 2.5% | 3.8% | 2.7% | 86 | 4 |
| F3_source_document | 519 | 760 | 5.5% | 0.31 | 50 | 1.6% | 2.5% | 1.6% | 1 | 5 |
| F4_legal_family_template | 1608 | 2728 | 19.8% | 0.69 | 998 | 12.8% | 15.2% | 13.1% | 209 | 4 |
| F5_owner_or_codebook_decision | 6 | 12054 | 87.7% | 0.62 | 10691 | 87.7% | 87.7% | 87.7% | 163 | 5 |
| F6_missing_input_type | 12 | 3059 | 22.2% | 0.51 | 1633 | 22.2% | 22.2% | 22.2% | 245 | 4 |
| F7_aux_current_predicate_table | 1988 | 276 | 2.0% | 0.23 | 16 | 0.5% | 0.9% | 0.6% | 0 | 3 |
| F8_work_backwards_reviewer | 472 | 345 | 2.5% | 0.51 | 188 | 1.8% | 2.1% | 1.9% | 245 | 1 |
| F9_single_blocker_frontier | 14 | 9347 | 68.0% | 0.92 | 9132 | 68.0% | 68.0% | 68.0% | 215 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13750 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: e6cebf88db31933bc2a6ec48104a3c72e9676056b7ff4fd1957a78f01a96e225

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 10691 | 0 | F1/NO_hypothesis_for_undecided 1692 |
| original_text | 2300 | 741 | F3/claim_kit_source_family 736 |
| clause_inventory | 13510 | 2819 | F4/x1_text_cluster 911 |
| ending_or_current_basis | 13721 | 3030 | F4/claim_kit_family 1896, F2/actor_provision_record 1064, F1/ending_of_decided_NO 801, F7/current_law_citation 276 |
| savings_residuals | 13523 | 2832 | NONE |
| counterevidence | 12118 | 1427 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 663 | 663 | NONE |

Stack: 187 of 3059 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 743 orders: no frame reaches clause_inventory, savings_residuals
- 594 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 585 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 480 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 187 orders: no frame reaches (none)
- 92 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
