# PRODUCER_REPORT r03 (Theophilus correction run)

Start 2026-11-05T22:01:08Z; end 2026-11-05T22:17:50Z. Final applied directory: applied-v3 (applied-v1 pre-existed from the failed run; applied-v2 was my first attempt, which rejected 7 orders: see below).

## Outcomes (12 submitted, 4 blocked)
- EO 8341, 8613, 8639: BLOCKED. The only registered text is the OCR text layer whose whole-page span carries garbled neighbouring-order numbers (83231, 85721, 74581) that the checker's order_exists rejects when quoted as the first-end source. Narrower spans (clause CLAUSES ids or inventory-override ids) avoid the token but carry no actor, so the assembler fails the gate (clause_first_end / whole_order_end_evidence; seen in applied-v2). Legal reading unchanged.
- EO 10570: BLOCKED. Registered original is EO_10570.recheck.txt (pdfplumber reading-order text); the checker can match that sha256 only against OCR copies with different words/line order, so original_representation.quote and the clause quote fail quote_verbatim; the kit offers no way to quote a narrower representation.
- EO 12771, 12914, 12922: SUBMITTED. Short lead-in/heading clauses ("I hereby order:", bare "Sec. 6.") folded into adjacent clauses by inventory overrides; counts and rationale updated.
- EO 12323, 12546, 12864, 12944, 14012, 14013, 14052, 14075, 14082: SUBMITTED. Rows rebuilt from prior reviewed claims against this packet's ids (all ids still resolved), short clauses (<6 words and <30 chars) folded into neighbours by overrides, source notes carried over, WHOLE_END_ACTOR_DISAGREEMENT resolutions written for 14012/14013/14075/14082 (concurrent same-day revocations; EO 14148 first-end actor, same date 2025-01-20). New actors read: EO 12960, 12945 (unrelated/no effect), 14159, 14154, 14163, 14168 (same-day concurrent revocations), 14096, 14126 (recitals only), 13985, 13988 (earlier orders cited by 14075).

## What took the time
8341/8613/8639/10570: tracing why the checker fails (order_exists, text-copy matching) and the actor requirement; 12771/12914/12922: inventory merges; 12323-14082: row conversion from prior claims, merges, conflict resolution; apply/batch-check waits.

## batch-check (applied-v3)
claims_checked 12, all_checks_passed 12, mechanical fail 0, unverified 0, gate passed 12, strict failures 0; outcomes: 12 assembled_proposal, 4 blocked.

## Geddes
GEDDES_LINT.json: 0 defect flags, 6 advisory coverage gaps (EO 12323, 12546, 12864). GEDDES_RESOLUTIONS.json: no flags to resolve.

## Full-packet files opened beyond views
CORRECTION_BRIEF.json, PRIOR_REVIEWED_CLAIMS.jsonl, PACKET.json (via load_packet, once per script), applied-v1 audit files, decisions.csv, clauses.csv. No other batch folders opened.

## Tool defects / notes
- cruden.py number EO:N --write dumps a ~7 MB corpus manifest, not the order text; I read held fr-originals text files directly instead.
- Assembler event() takes the actor from the evidence record's actor_id/instrument_id, so clause/override records cannot be first-end sources; ORIGINAL ids are required.
- Checker thresholds are <6 words and <30 characters (the brief says 8+/40+).
