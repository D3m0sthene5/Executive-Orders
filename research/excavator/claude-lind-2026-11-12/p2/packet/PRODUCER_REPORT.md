# Producer report, packet p2 (route: undecided)

Start UTC 2026-11-12T20:57:04Z; end UTC 2026-11-12T21:10:55Z. Final applied directory: applied-v1 (no later version needed).

## Outcomes
Submitted as status proposals plus lifecycle sheets (apply: awaiting_status_review, the expected state): 4. Blocked: 8 (assigned) . Dispatch-blocked, rows left as prepared (unresolved): 3.

- EO:12437 submit, status no. Sole command revokes EO 12217; spent on issue 1983-08-11 (basis OWN_TEXT). Took: reading one paragraph, verifying USC 42 s.8373 note.
- EO:13476 submit, status no. Own-terms expiry 2009-02-20 (sec. 4(d)); 31 inventory scopes; sec. 4(a) clause recorded as ending with the order because no held source gives it a separate end. Took: 31 clause rows.
- EO:12753 submit, status no. Superseded by EO 12791 (signed 1992-03-09, effective date not stated; own period end 1992-03-10 is the alternative). Later-event source is the APP mirror of EO 12791 with a working_text disclosure, because the FR copy of EO 12791 is declared official_printing, acceptable_as_original false in the working-text index, so the checker rejects it as an exact source. Took: tracing the source grade rejection.
- EO:11294 submit, status no. Sec. 3 superseded by EO 11609 sec. 11 (1971-07-22); sections 1, 2, 4 and the whole order revoked by EO 12561 sec. 3 (1986-07-01). EO 12396 revoked other subsections of EO 10621, not (o). Took: reading EO 11609, 12396, 12561 and the USC note.
- EO:12340 blocked: ending instrument EO 12473 (1984-04-13, rescinds the 1969 Manual as amended by EO 12340, effective 1984-08-01; held at jobs/fr-originals/data/full_run/texts/EO_12473.txt) is not in the frozen dossier as ACT/ACTOR_TEXT, so no valid basis can be cited; sec. 13 (transmit to Congress) has no performance source. Needs a source supplement for EO 12473.
- EO:14103 blocked: no CURRENT and no ending record in the dossier; assessment reads it as still operative (amendments to the Manual).
- EO:10755 blocked: no ending/CURRENT record; held original is a multi-document FR issue.
- EO:1538 blocked: no ending/CURRENT; only partial eliminations (EO 1598, 1621, 1782); original needs a page-image check not done.
- EO:2898 blocked: no ending/CURRENT; "until further notification"; ProQuest replica.
- EO:4145 blocked: no exact expiry dates for the 1925 trust periods (own-terms end is only a 1935 bound); ProQuest replica.
- EO:8877 blocked: only partial revocations; no whole-order end or current record; PLO 5001 text not held.
- EO:9159 blocked: amends EO 7126; parent status not held.
- EO:12280, EO:4861, EO:4968: dispatch-blocked, assessment rows only.

## Checks
apply: awaiting_status_review 4, blocked 8, unresolved 3. batch-check: claims_checked 0 (undecided members assemble no claim at apply), actionable failures 0. Because the kit does not assemble claims for undecided members, I checked each of the 4 proposals myself in scratch with status_overlay._decision_errors (no errors) and by assembling a copy of the dossier with the proposed status through the kit's assembler and claim gate (no errors).

## Geddes
GEDDES_LINT.json written by batch-check: 0 flags, 0 coverage gaps; no resolutions file needed.

## Full-packet files opened beyond the views
Per-order undecided/EO_N/DOSSIER.json and EVIDENCE.json for all assigned orders (needed for evidence ids and observations); LOOKUPS.md in full; decisions.csv and clauses.csv; no READ.md, PACKET.json or LOOKUPS.details.json. Held texts opened directly: EO 12473, 12561, 12396, 11609, 12791 (and 11488, 14103 text).

## Tool defects / notes
- Apply and batch-check do not test undecided proposals; the 4 proposals still need the overlay review and assembly.
- Brief precheck said acceptable_as_original false cannot carry a status proposal; the validator has a working_text_basis exception (tracker_original_supported) for 2898 and 4145, but both lack an exact ending anyway.
