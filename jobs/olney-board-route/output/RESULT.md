# Olney result

Rule D-20261108-board-rule; zero model tokens. Universe 117 board orders in production.one_step_away (57 were in cloud lanes c01-c12, 0 in PC lanes, 60 unassigned after the PC repack).

- Selected: 12
- Exceptions: 105 (an order can carry several reasons)
- Prepared: 12
- Checker-passing: 11
- Failing: 1

## Exceptions, one primary reason per order

| Primary reason | Orders |
|---|---:|
| letter_date_unreadable_or_unlocated | 37 |
| report_date_not_corroborated | 29 |
| dossier_inventory_not_single_clause | 12 |
| report_shared_with_follow_on_order | 9 |
| clause_inventory_doubt | 7 |
| congressional_action | 4 |
| report_bytes_pergamon_only_kit_gap | 3 |
| follow_on_order | 2 |
| reconvened_or_supplemental_report | 1 |
| multi_clause_claim | 1 |

## Exceptions, every reason (an order can carry several)

| Reason | Orders |
|---|---:|
| report_bytes_pergamon_only_kit_gap | 41 |
| report_date_not_corroborated | 35 |
| letter_date_not_located | 27 |
| letter_date_ocr_damaged_cover_clean | 16 |
| dossier_inventory_not_single_clause | 15 |
| report_shared_with_follow_on_order | 11 |
| board_creation_sentences | 8 |
| standstill_sentence_ambiguous | 7 |
| other_command_wording | 5 |
| text_after_standstill | 5 |
| congressional_action | 4 |
| letter_date_not_found_after_cover | 4 |
| nmb_lists_extra_documents | 4 |
| no_change_wording_without_standstill_pattern | 3 |
| standstill_sentence_lacks_no_change_or_agreement | 3 |
| submission_sentence_not_found | 3 |
| follow_on_order | 2 |
| multi_clause_claim | 2 |
| cover_date_differs_from_letter | 1 |
| letter_date_ocr_damaged | 1 |
| other_order_number_in_span | 1 |
| reconvened_or_supplemental_report | 1 |

## Batches

| Batch | Orders | Passing | Wall seconds by step |
|---|---:|---:|---|
| s0 | 8 | 7 | {"apply":15.97,"batch_check":48.01,"prepare":10.61,"supplement":16.54,"write_sheets":0.0} |
| s1 | 4 | 4 | {"apply":14.16,"batch_check":33.74,"prepare":9.61,"supplement":14.81,"write_sheets":0.0} |

## Failing

- EO:10874: {"apply_outcome":"blocked","batch":"s0","outcome":"blocked","problems":["dispatch_source_blocked"]}
