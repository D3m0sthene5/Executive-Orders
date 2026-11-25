# Olney result (run v3)

Rules D-20261108-board-rule and D-20261125-board-cover-date; zero model tokens. The universe is the 117 board orders in production.one_step_away (Lind candidates). The 10 orders upheld by both blind arms in earlier runs are not rerun (EO:9702, EO:10032, EO:10056, EO:10071, EO:10105, EO:10112, EO:10140, EO:10757, EO:10872, EO:11663), so 107 orders were judged.

- Selected: 7 (0 dated by the letter of transmittal, 7 by the cover under D-20261125-board-cover-date; 1 with recorded report-time extensions)
- Prepared: 7
- Checker-passing: 6
- Exceptions: 101 (including orders the kit refused at dispatch)

## Checker-passing packets for blind review

| Batch | Packet | Orders |
|---|---|---|
| s5 | `research/excavator/claude-bracton-2026-11-25/olney/s5/supplemented` | EO:10050, EO:10067, EO:10150, EO:10630, EO:11445, EO:9918 |

## Exceptions, one primary reason per order, and what each needs

| Primary reason | Orders | Needs |
|---|---:|---|
| report_date_not_corroborated | 29 | Lind's report date is not corroborated (image check needed or held readings conflict); needs a page-image check of the cover and letter (Lind UNREAD_IMAGE_CHECK_NEEDED/CONFLICT_IMAGE_CHECK_NEEDED). |
| report_extension_not_scriptable | 20 | The report records a report-time extension Olney cannot carry as a later event: outside the held pages (needs a held text of the later pages), several extensions, an unparsed or ambiguous approval date or deadline, or (run v3) no printed approval date or new deadline. Needs a producer to record each extension, or a held text of the pages. |
| dossier_inventory_not_single_clause | 12 | The kit dossier splits the order into several clauses (often FR layout or added commands); a producer must reconcile the inventory before the scripted split applies. |
| report_shared_with_follow_on_order | 9 | One report answers two orders (a board order and its follow-on); a producer must assign the report to each order and decide whether the follow-on reset the deadline. Needs a two-order claim, reviewed together. |
| letter_reading_doubt | 7 | Olney's reading of the held letter (its date line or its address to the President) disagrees with Lind's, or a 'no date line' statement would not hold of the quoted span; needs a page-image reading of the letter. |
| submission_sentence_not_found | 6 | The letter is held but no submission sentence was found; needs a manual span or a page check. |
| letter_and_cover_dates_conflict | 5 | The letter date line reads cleanly as a date other than the cover date (an OCR misreading or a real difference); needs a page-image reading of both lines. D-20261125-board-cover-date covers only an unreadable line. |
| congressional_action | 4 | Congress legislated on the dispute (NMB inventory); a producer must decide whether the statute ended or displaced the board or the no-change period. Owner rule does not cover it. |
| report_procedural_event | 3 | The report records a stipulation about the proceedings, a reconstituted board or changed member, a reconvening or a report period restarted from a later date (o2 review, EO 10760). The board rule does not say which act completed the task or when the no-change period ran; needs a producer claim that records the event. |
| follow_on_order | 2 | A producer claim: the order amends or extends another board order, so its end follows the parent board and the instrument that names it (not covered by the board rule as written). |
| multi_clause_claim | 1 | The filed claim has more than two clauses (extra commands); each needs its own end beyond the board rule. |
| filed_claim_changed_since_lind | 1 | A claim file newer than the one Lind read names the order (EO 11343 was filed by standing auto-adoption after the v2 review); Olney does not replace it. |
| reconvened_or_supplemental_report | 1 | The board reconvened or filed a supplemental report; which report completed the task needs a producer judgment and a second span. |
| original_bytes_not_held | 1 | The order's own Federal Register bytes are only a custody record; needs the original PDF kept (dispatch refuses the packet). |

## Exceptions, every reason (an order can carry several)

| Reason | Orders |
|---|---:|
| report_date_not_corroborated | 35 |
| report_procedural_event | 25 |
| report_extension_outside_held_text | 23 |
| dossier_inventory_not_single_clause | 15 |
| report_extension_multiple | 12 |
| report_procedural_event_outside_held_text | 11 |
| report_shared_with_follow_on_order | 11 |
| board_creation_sentences | 8 |
| savings_source_not_the_revoking_order | 7 |
| letter_date_not_located | 6 |
| report_extension_deadline_not_printed | 6 |
| cover_date_differs_from_letter | 5 |
| letter_held_submission_not_found | 5 |
| other_command_wording | 5 |
| report_extension_approval_date_unparsed | 5 |
| savings_source_table_not_found | 5 |
| standstill_sentence_ambiguous | 5 |
| text_after_standstill | 5 |
| congressional_action | 4 |
| letter_address_not_located | 4 |
| nmb_lists_extra_documents | 4 |
| report_extension_approval_date_not_printed | 4 |
| no_change_wording_without_standstill_pattern | 3 |
| report_extension_deadline_ambiguous | 3 |
| submission_sentence_not_found | 3 |
| follow_on_order | 2 |
| letter_date_line_status_uncertain | 2 |
| multi_clause_claim | 2 |
| other_order_number_in_span | 2 |
| standstill_sentence_lacks_no_change_or_agreement | 2 |
| filed_claim_changed_since_lind | 1 |
| letter_date_line_location_disagrees | 1 |
| letter_date_line_reads_cleanly_but_lind_did_not | 1 |
| letter_date_ocr_damaged | 1 |
| order_identity_not_in_span | 1 |
| reconvened_or_supplemental_report | 1 |

## Batches

| Batch | Orders | Passing | Wall seconds by step |
|---|---:|---:|---|
| s5 | 7 | 6 | {"apply":24.16,"batch_check":43.84,"prepare":17.92,"supplement":26.13,"write_sheets":0.0} |

## Not checker-passing

- EO:9991: {"apply_outcome":"blocked","batch":"s5","outcome":"blocked","problems":["dispatch_source_blocked"]}
