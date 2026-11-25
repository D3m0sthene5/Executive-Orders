# Producer report, y09 (baldus)

Start UTC 2026-11-25T16:02:10Z; end UTC 2026-11-25T16:12:30Z (clock as reported by the sandbox). Final applied directory: applied-v3.

## Outcomes
- EO:12353 submit (YES). Inventory corrected to nine sections (original inventory stopped before sections 8 and 9, which follow the page-10 break); section 9 split into a performed revocation of EO 10927 (terminated 1982-03-23) and a continuing savings sentence. EOs 12404 and 13743 attached as amendments (later events). Postal Service rule E7-16986 reconciled: it says EO 12353 revoked EO 10927 and does not end this order. Current predicate by the original-plus-bounded-search route, because the CURRENT: records (USC note, eCFR XML) are custody_record_only and failed the first source check (applied-v1).
- EO:12372 dispatch-blocked; decisions row left as prepared; assessment row only.
- EO:12396 blocked: former 10 U.S.C. 5721(c) and renumbered/repealed sections (524, 644, 6323, 3918, 8918) need the repealing statutes and current Title 10 text, none held; EO 13321 provision not located.
- EO:12445 blocked: section 5 (Transportation regulations continue until superseded by Treasury regulations) needs T.D. 86-92 (51 FR 16161) with effective date and the DOT regulations; held sources give only the 1986-05-01 publication.
- EO:12446 blocked: 33 inventory rows with OCR duplicates; each deemed amendment needs comparison with the current Foreign Service Act text and later public laws.
- EO:12500 blocked: delegations under FY1985 appropriation/authorization provisions in amendments to EO 12163; successor texts of EO 12163 (EO 13118 restated Part 1-1) and the 1985 provisions not held; chain events act on EO 12163, not on this order.
- EO:12549 blocked: dated one-time tasks and report deadlines (sections 3, 5, 7) with no held performance evidence; OMB guidelines, 2 CFR 180 CURRENT record, and EO 12689 as acting text missing.
- EO:12564 blocked: section 7(d)(2) cites EO 12356, revoked by EO 12958 section 6.1(d) (held, but not an acting text in the packet so not citable as a later event); inventory also mislabels section 6. Otherwise strongly in force (Pub. L. 118-63 sec. 1218).
- EO:12591 blocked: one-time dated tasks (sections 2, 5, 7) with no held performance evidence.

No order was found not in force on 2026-10-14. Ledger untouched.

## What took the time (one line each)
12353 inventory correction and amendment tracing; 12396 statute renumbering; 12445 section 5 transitional end; 12446 volume of clauses; 12500 EO 12163 amendment chain; 12549 deadlines and EO 12689; 12564 section 7(d)(2) cross-reference; 12591 dated tasks.

## Batch-check (applied-v3)
9 members; 1 claim checked, strict pass 1, fail 0; actual checker all checks passed 1; outcomes: 1 assembled_proposal, 7 blocked, 1 unresolved (dispatch-blocked). applied-v1 failed source custody (CURRENT records); applied-v2 had one Geddes flag; v3 clean.

## Geddes
v2: one flag (later_instrument_named_without_event_source, EO:12353 sec 8 reasoning named EO 12404); fixed in v3. v3: 0 flags, 3 coverage gaps (informational). GEDDES_RESOLUTIONS.json empty.

## Full-packet files opened beyond views
PACKET.json (via script: dossier conflicts, clauses, evidence for EO:12353; keys only otherwise). READ.md, LOOKUPS.details.json not opened. Held texts outside the packet read for the orders: jobs/fr-originals texts for EO 12353, 12404, 13743, 12445, 12396, 12500, 12446, 12549/12564/12591 (greps), 12958; jobs/current-law notes; jobs/selden-fr-citers E7-16986 and E9-17876.

## Tool defects
dispatch/source check treats CURRENT: records as custody_record_only, so CURRENT-based YES claims cannot pass; the apply command prints the full custody report on failure. EO 12564 inventory in the packet mislabels section 6 clauses as sec5-*-dup2.
