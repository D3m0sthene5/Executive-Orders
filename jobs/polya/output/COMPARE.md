# POLYA compare (generated; repo_head 238a3f7e65058d41075d9191a3dc4af4c13fbe3f)

Pool: 15003 orders, 1393 ready, 13610 not ready (2408 decided, 11202 undecided). Reach is not yield.

| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_order | 13610 | 13610 | 100.0% | 0.00 | 1 | 0.1% | 0.7% | 0.1% | 223 | 5 |
| F1_ending_instrument | 1729 | 2463 | 18.1% | 0.39 | 212 | 3.5% | 6.9% | 3.5% | 179 | 5 |
| F2_actor_provision_record | 1328 | 925 | 6.8% | 0.40 | 127 | 2.2% | 3.6% | 2.5% | 79 | 4 |
| F3_source_document | 10 | 30 | 0.2% | 0.44 | 10 | 0.2% | 0.2% | 0.2% | 1 | 5 |
| F4_legal_family_template | 1679 | 3218 | 23.6% | 0.66 | 888 | 12.3% | 16.4% | 12.9% | 179 | 4 |
| F5_owner_or_codebook_decision | 6 | 11771 | 86.5% | 0.80 | 11202 | 86.5% | 86.5% | 86.5% | 135 | 5 |
| F6_missing_input_type | 12 | 2408 | 17.7% | 0.50 | 1164 | 17.7% | 17.7% | 17.7% | 222 | 4 |
| F7_aux_current_predicate_table | 1716 | 208 | 1.5% | 0.20 | 13 | 0.4% | 0.8% | 0.5% | 0 | 3 |
| F8_work_backwards_reviewer | 435 | 304 | 2.2% | 0.50 | 157 | 1.7% | 1.9% | 1.8% | 223 | 1 |
| F9_single_blocker_frontier | 13 | 11240 | 82.6% | 0.92 | 11048 | 82.6% | 82.6% | 82.6% | 193 | 5 |

Distinct not-ready orders reached across nonbaseline frames: 13610 (deduplicated union).
Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.
Input snapshot SHA-256: f742bb9189ea2834967d1fa7ec970179f05c4739d31cca313f689a532308ba06

| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |
|---|---:|---:|---|
| provisional_status | 11202 | 0 | F1/NO_hypothesis_for_undecided 1689 |
| original_text | 163 | 9 | F3/claim_kit_source_family 6 |
| clause_inventory | 13392 | 2191 | F4/x1_text_cluster 1574 |
| ending_or_current_basis | 13572 | 2371 | F4/claim_kit_family 1715, F2/actor_provision_record 925, F1/ending_of_decided_NO 774, F7/current_law_citation 208 |
| savings_residuals | 13405 | 2204 | NONE |
| counterevidence | 12103 | 902 | NONE |
| shared_sources | 24 | 24 | F3/tracker_shared_source 24 |
| opus_media | 638 | 638 | NONE |

Stack: 156 of 2408 decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers.
- 674 orders: no frame reaches clause_inventory, savings_residuals
- 466 orders: no frame reaches clause_inventory, savings_residuals, counterevidence
- 448 orders: no frame reaches clause_inventory, savings_residuals, opus_media
- 193 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, counterevidence
- 156 orders: no frame reaches (none)
- 89 orders: no frame reaches clause_inventory, ending_or_current_basis, savings_residuals, opus_media
