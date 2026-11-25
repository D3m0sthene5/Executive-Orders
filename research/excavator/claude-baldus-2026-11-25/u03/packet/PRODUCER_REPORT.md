# Producer report, packet u03 (route: undecided), agent baldus

Start 2026-11-25T15:46:40Z; end 2026-11-25T16:03:51Z. Final applied directory: applied-v3 (applied-v1 and applied-v2 are earlier versions kept, not overwritten: v1 lacked the savings_check text; v2 still carried an EO 13239 submission that the actual checker failed).

## Outcomes (assigned members)

- EO:10695 blocked. The ending-type records all reflect EO 11556 revoking EO 10695-A, a different instrument (the held OFR table lists 10695-A separately); the only CURRENT record is an amender listing the validator refuses. No status proposal. Missing: a held own-terms record showing the two commands were exhausted on issue.
- EO:11241 submit (status no, STATUS_DECISION.json filled and validator-clean). Two clauses; first end 1965-08-26 by performance on issue (amending order, section 3 effective date); regulation text ended 1969-11-26 by EO 11497; EO 12553 (1986-02-25) formal revocation; EO 11360 amendment. A draft assembled with the status set passed the actual claim checker (all checks passed). apply reports awaiting_status_review, as expected.
- EO:12784 blocked (clause 2 report due 1994-06-30 has no held performance source). Status no filled (delegation expired 1994-10-02 by own terms; TERM basis); validator-clean.
- EO:13239 blocked. The only CURRENT record (26 U.S.C. 112 note) is custody_record_only and its quote is not found by the actual checker run on a draft. Missing: held bytes of the usc26.xml note or of 26 U.S.C. 112. STATUS_DECISION.json blank.
- EO:13684 blocked. Section 5 trigger (President's request for the final report) has no held date. STATUS_DECISION.json blank.
- EO:13941 blocked. Dated directives with no held performance source; no ending record; STATUS_DECISION.json blank.
- EO:14151 blocked. CURRENT record is hash-only (same kind as 13239); section 2(b) sixty-day directives have no performance source. STATUS_DECISION.json blank. Best reading yes.
- EO:5553 blocked. No ending or CURRENT record; appointment of Mrs. Plummer not shown.
- EO:6898 blocked. Original is a machine-read government printed copy (not acceptable_as_original, no working-text basis).
- EO:9250 blocked. 31 clauses; EO 9620 abolished the office, EO 9801 terminated wage and salary controls without naming 9250; price and agricultural clauses have no held ending.
- EO:9577A blocked. EO 9603 directs return as soon as practicable; actual return date not held.

Dispatch-blocked members (2124, 2567, 4422, 4945, 5043, 520, 688, 8264, 95): assessment rows only, from the views; decisions.csv rows left as prepared.

## Time per order (one line each)

10695 identity trap (10695 vs 10695-A) and validator reading; 11241 the amending-order performance question and a clean checker run; 12784 two own-terms clauses and EO 12929; 13239 custody-only current record found by a checker run; 13684 searching for the final-report request; 13941 reading directives; 14151 checking 16 later FR documents; 5553 and 6898 short blocks; 9250 reading 31 clause titles and EO 9620/9801; 9577A reading EO 9603.

## batch-check (applied-v3)

packet_members 20; claims_checked 0 (no assembled claim exists because undecided members stop at awaiting_status_review); outcomes: blocked 10, unresolved 9, awaiting_status_review 1; actionable_failures none; actual checker: no submitted claims. A separate scratch run (status injected in memory, no file changed) assembled EO:11241 with no errors and the actual checker passed all checks; the same run failed EO:13239 on the custody-only current source.

## Geddes

GEDDES_LINT.json written by batch-check: 0 flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json needed.

## Opened beyond the views

LOOKUPS.md (head); EVIDENCE.json and DOSSIER.json under undecided/ (read-only) for evidence ids, histories and machine searches; no READ.md, PACKET.json or LOOKUPS.details.json. Held texts read: EO 11360, 11497, 11527, 11537, 11563, 12553, 9620, 9801, 9603, 12929, 13951 (excerpt), 10930 (grep). Other repository work: cruden.py number for EO:10695 and EO:13239, literal search for 21st Century Policing, regex searches for 10695, 12784, 13239 and ceases-to-be-a-combat-zone.

## Tool defects and notes

- The brief says a non-acceptable original blocks a status proposal; the validator has a working_text_basis exception, but none applied to EO 6898.
- For undecided members apply does not assemble a claim, so assembler errors surface only through a scratch simulation; I used one (scratch folder only).
- cruden.py search prints one line per file and a broad regex printed a very large result once; no defect, a cost.
