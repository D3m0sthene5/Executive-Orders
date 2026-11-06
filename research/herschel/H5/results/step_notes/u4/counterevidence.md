# counterevidence notes (H5-w32)
Start 2026-11-06T00:22:07Z; end 2026-11-06T00:25:01Z

- EO:11925: done
- EO:12221: done
- EO:9248: done
- EO:9866: done
Time went on grep of held texts for the parent orders (11554, 12044, 9240) and the apply run (13 s); two fixes to the sheet and overlay-propose failures.

## Findings
No counterevidence: no earlier end, revival or extension found for EO 11554, 12044 (no extension before 12291 revoked it, so the 1981-04-30 expiry is not the end), 9240 (EO 9597/9600 amend section IB only) or EO 9866 (EO 10753 supersedes EO 10156, not 9866). No clause rows changed. Dossiers list no conflicts, no prior research and no machine searches, so search_ids [] and conflict_resolutions {}.

## Sheet edits (decisions.csv, the four rows)
research_rationale, search_ids, conflict_resolutions, unresolved_material_gaps, outcome=submit, approved=true. I also CLEARED source_notes for the four: the earlier worker had put plain text there, but apply requires a JSON list of {id,reason,date_qualification}, and all four rows were rejected with JSONDecodeError (applied-v1). The cleared text is saved in /tmp/claude-0/herschel-H5/H5-w32/source_notes_N.txt. EO:9699 row untouched (restored after an accidental clear).

## Apply / finalize
applied-v1 (failed, source_notes) and applied-v2 (good): packet/applied-v2; counts: awaiting_status_review 4 (11925, 12221, 9248, 9866), unresolved 3 (9699, 13672, 14331). Lifecycle sheets: applied-v2/decisions/EO_N.json. Geddes: applied-v2/GEDDES_LINT.json (0 claims, 0 flags) and GEDDES_RESOLUTIONS.json (none needed).
STATUS_REVIEWS lists both reviewers upholding all four, but overlay-propose FAILED for all four, so no overlay/ dirs, no assemble or check:
- review A: status_proposal_rejected:review_must_check_original_and_selected_basis (checked_evidence_ids lacks ORIGINAL:EO:N, the original_source_id of the evidence).
- review B (tried as fallback): review_unknown_checked_evidence (it lists ids, e.g. ORIGINAL:EO:N and ...effective#0, that the evidence file does not contain).
Needed from coordinator: corrected arm A review listing ORIGINAL:EO:N (or evidence file that carries it) for each of the four, then rerun overlay-propose/assemble/check. Reviews are not mine to edit.

## Finalize retry (after corrected reviews)
overlay-propose with the arm A sheets now passes the review check but FAILS for all four with `overlay_destination_must_be_isolated_from_authoritative_inputs`: status_overlay._destination (jobs/claim-kit/status_overlay.py:797-802) only allows --write under jobs/claim-kit/output/overlays or research/excavator, not research/herschel/.../overlay/EO_N/proposal-v1. I did not work around it (no symlinks, no writes outside the packet). No overlay/ dirs, no assemble/check, no CLAIMS.working.all.jsonl written (nothing passed). Producer approval stays true in decisions.csv; not reconfirmed against an overlay proposal.
Needed: coordinator either allows a herschel destination in _destination, or names an allowed destination (e.g. research/excavator/<dir>/overlay/EO_N/proposal-v1); then rerun the same four commands with the arm A review and applied-v2/decisions/EO_N.json.
