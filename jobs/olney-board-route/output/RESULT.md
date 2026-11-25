# Olney result (run v2)

Rules D-20261108-board-rule and D-20261125-board-cover-date; zero model tokens. The universe is the 117 board orders in production.one_step_away (Lind candidates). The 8 orders upheld by both blind arms in the first run are not rerun (EO:10032, EO:10056, EO:10071, EO:10112, EO:10140, EO:10757, EO:10872, EO:11663), so 109 orders were judged.

- Selected: 9 (3 dated by the letter of transmittal, 6 by the cover under D-20261125-board-cover-date; 0 with recorded report-time extensions)
- Prepared: 9
- Checker-passing: 8
- Exceptions: 101 (including orders the kit refused at dispatch)

## Checker-passing packets for blind review

| Batch | Packet | Orders |
|---|---|---|
| s2 | `research/excavator/claude-bracton-2026-11-25/olney/s2/supplemented` | EO:10050, EO:10067, EO:10105, EO:10147, EO:10150, EO:10630, EO:10760, EO:10969 |

## Exceptions, one primary reason per order, and what each needs

| Primary reason | Orders | Needs |
|---|---:|---|
| report_date_not_corroborated | 29 | Lind's report date is not corroborated (image check needed or held readings conflict); needs a page-image check of the cover and letter (Lind UNREAD_IMAGE_CHECK_NEEDED/CONFLICT_IMAGE_CHECK_NEEDED). |
| report_extension_not_scriptable | 14 | The report records a report-time extension Olney cannot carry as a later event: outside the held pages (needs a held text of the later pages), several extensions, an unparsed or ambiguous approval date or deadline. Needs a producer to record each extension, or a held text of the pages. |
| report_bytes_pergamon_only_kit_gap | 12 | The report bytes are only in the Pergamon store; needs the claim-kit change on branch claude/olney-v2 merged, then an Olney rerun. |
| dossier_inventory_not_single_clause | 12 | The kit dossier splits the order into several clauses (often FR layout or added commands); a producer must reconcile the inventory before the scripted split applies. |
| report_shared_with_follow_on_order | 9 | One report answers two orders (a board order and its follow-on); a producer must assign the report to each order and decide whether the follow-on reset the deadline. Needs a two-order claim, reviewed together. |
| clause_inventory_doubt | 6 | The order text has wording beyond create-investigate-report and the no-change sentence (another command, damaged or interleaved FR text); needs a producer clause inventory. |
| letter_and_cover_dates_conflict | 5 | The letter date line reads cleanly as a date other than the cover date (an OCR misreading or a real difference); needs a page-image reading of both lines. D-20261125-board-cover-date covers only an unreadable line. |
| congressional_action | 4 | Congress legislated on the dispute (NMB inventory); a producer must decide whether the statute ended or displaced the board or the no-change period. Owner rule does not cover it. |
| report_identity_doubt | 3 | The quoted span does not name the order (number, or appointment date with the board number), or names another order; needs a producer identity check. |
| submission_sentence_not_found | 2 | The letter is held but no submission sentence was found; needs a manual span or a page check. |
| follow_on_order | 2 | A producer claim: the order amends or extends another board order, so its end follows the parent board and the instrument that names it (not covered by the board rule as written). |
| multi_clause_claim | 1 | The filed claim has more than two clauses (extra commands); each needs its own end beyond the board rule. |
| reconvened_or_supplemental_report | 1 | The board reconvened or filed a supplemental report; which report completed the task needs a producer judgment and a second span. |
| original_bytes_not_held | 1 | The order's own Federal Register bytes are only a custody record; needs the original PDF kept (dispatch refuses the packet). |

## Exceptions, every reason (an order can carry several)

| Reason | Orders |
|---|---:|
| report_bytes_pergamon_only_kit_gap | 41 |
| report_date_not_corroborated | 35 |
| dossier_inventory_not_single_clause | 15 |
| report_extension_multiple | 11 |
| report_shared_with_follow_on_order | 11 |
| board_creation_sentences | 8 |
| report_extension_outside_held_text | 8 |
| letter_date_not_located | 6 |
| cover_date_differs_from_letter | 5 |
| other_command_wording | 5 |
| standstill_sentence_ambiguous | 5 |
| text_after_standstill | 5 |
| congressional_action | 4 |
| nmb_lists_extra_documents | 4 |
| report_extension_deadline_not_printed | 4 |
| no_change_wording_without_standstill_pattern | 3 |
| order_identity_not_in_span | 3 |
| submission_sentence_not_found | 3 |
| follow_on_order | 2 |
| multi_clause_claim | 2 |
| other_order_number_in_span | 2 |
| report_extension_approval_date_unparsed | 2 |
| standstill_sentence_lacks_no_change_or_agreement | 2 |
| letter_date_ocr_damaged | 1 |
| reconvened_or_supplemental_report | 1 |
| report_extension_deadline_ambiguous | 1 |

## After the claim-kit Pergamon change is merged

A preview selection with the change assumed selects 15 orders, adding 6: EO:11343, EO:11445, EO:9702, EO:9918, EO:9936, EO:9991. Selection with the claim-kit Pergamon change assumed merged (select --out, OLNEY_ASSUME_PERGAMON_KIT=1); no packet was prepared for these orders.

## Batches

| Batch | Orders | Passing | Wall seconds by step |
|---|---:|---:|---|
| s2 | 9 | 8 | {"apply":23.85,"batch_check":42.8,"prepare":17.24,"supplement":25.94,"write_sheets":0.0} |

## Not checker-passing

- EO:10874: {"apply_outcome":"blocked","batch":"s2","outcome":"blocked","problems":["dispatch_source_blocked"]}
