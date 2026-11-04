# Producer report, packet o17 (Tribonian, claude)

Start 2026-11-04T06:27:55Z. End 2026-11-04T11:10Z (the run spanned a usage-limit pause; apply took 44 s of machine time, batch-check about 20 minutes).

## Outcomes (30 orders: 6 submitted, 24 blocked)

Submitted (exhausted by performance or own terms, evidence held):
- EO 11439: one-time revocation of EO 11372, exhausted on signing 1968-12-07.
- EO 11549: one-time revocation of EO 10361, exhausted on signing 1970-07-28.
- EO 11408: one-time revocations (sections 1 and 2), exhausted on signing 1968-04-25; the OFR cross-reference to EO 11222 is a 1965 order and not an event.
- EO 11496: Honduran meat regulation ends by own term, remainder of calendar 1969, recorded 1969-12-31 inclusive.
- EO 11568: own-terms until February 29, 1972 (inclusive 1972-02-29); EO 11642 recorded as a later further exemption.
- EO 11462: inventory corrected to add section 1; sections 1 and 2 end 1969-03-31, section 3 ends 1969-03-28.

Blocked, with the precise gap (each in decisions.csv):
- EO 11383, 11457, 11461, 11465, 11483, 11505, 11535, 11584, 11611: inspection orders limited to "during the Nth Congress"; no held source fixes the end date of that Congress (Twentieth Amendment or congressional-term record not held).
- EO 11413, 11474: superseded by EO 11811, whose effectiveness is a pay-period formula, not a date; inventory incomplete; saved-pay clause not shown extinguished.
- EO 11425: study and advisory committee have no term and no held end.
- EO 11464: restated by EO 11754 and 11766; end of the interest equalization tax not held.
- EO 11467: delegation with no term; EO 12608 only amends section 2.
- EO 11469: substituted termination sentence in EO 11412; report and termination dates not held.
- EO 11503, 11573: section 2 leave-policy period undefined.
- EO 11536, 11546: report deadlines are not ends; actual report and termination dates not held.
- EO 11538: delegation with no term; statute and exposition end not held.
- EO 11551: substitutes section 1 of EO 11399; Council end not held; PL:91-125 identity unresolved.
- EO 11557: only substitutes membership of EO 11546; registered text offsets are wrong.
- EO 11577: registered text has blank pages; EO 11812 effectiveness not confirmed.
- EO 11619: indefinite exemption; no end shown.

## What took the time
- Reading rulings and views: about 30 minutes. Block-reading the nine Congress-term orders was quick; the decisive question was whether any held source dates a Congress (none; one corpus search of about 30 s).
- Drafting the six claims: most of the effort, in one generated sheet script.
- Apply and batch-check: wait on a busy machine.

## batch-check
claims_checked 6; strict pass 6, fail 0; actual checker all checks passed 6; actionable failures none; independent human certifications 0.

## Geddes
Lint ran inside batch-check: 0 flags, 0 coverage gaps (applied-v1/GEDDES_LINT.json). No resolutions file needed.

## Full-packet files opened beyond the views
LOOKUPS.md and LOOKUPS.json (number citations), PACKET.json (EO 11408 status-history pointers), decisions.csv and clauses.csv. Also read held texts EO_12553, EO_11811, EO_11812, EO_12608, EO_11642 and the status-history event files for 11408 and 11568.

## Tool defects
None blocking. One shell call timed out into the background; no state lost.
