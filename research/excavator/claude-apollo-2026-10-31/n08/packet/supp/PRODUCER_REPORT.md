# Producer report, batch n08 (NIRA code approvals), packet `supp`

Producer: Claude (Sonnet 5.5), agent column `claude`.
Start: 2026-10-31T22:13:08Z. End: 2026-10-31T22:26:24Z (after apply and batch-check; this report written immediately after).
Final applied directory: `applied-v1` (no second version needed).
Certified count unchanged at 0; nothing here is independent review.

## Outcomes (14 submitted, 9 blocked)

Submitted with first end June 14, 1935 (S.J. Res. 113 section 2 repeal, `SUPPLEMENT:SJRES113`; Schechter recorded as validity characterization only):

- EO 6293 Textile Bag, EO 6310 Textile Machinery Manufacturing, EO 6331-E Throwing, EO 6358 Steel Tubular and Firebox Boiler, EO 6377 Terra Cotta, EO 6386 Steel Casting, EO 6389 Soap and Glycerine Manufacturing, EO 6392 Stock Exchange Firms, EO 6401 Washing and Ironing Machine Manufacturing, EO 6531 Silverware Manufacturing: plain approvals, single whole-order clause, no own terms found, no earlier cancellation, modification-as-end or superseding code in held texts. EO 6293 has a held later amendment (EO 6529), recorded in the earlier-end check as a later event.
- EO 6503 Valve and Fittings: plain approval with one condition (filed price lists open to inspection). The condition depends on the code and has no term, so it ends with the approval.
- EO 6875 Silk Textile amendment: approval of an amendment and modification of the prior approval of the amended portions; both depend on the code. Held EO 6878 and EO 6930 treat the code as in force in 1934; neither ends it.
- EO 6441-A Southern Rice Milling: inventory corrected. The machine inventory made findings 1 to 5 clauses and attached the approval paragraph to finding 5; the corrected single clause is the final "Now, Therefore" paragraph (characters 1486 to 1779). Held EO 6999 (March 30, 1935) treats the code and its approving order as continuing; it is a later administrative event, not an end.
- EO 6393 Toy and Playthings (APP heading reads "Tot"; text and WPA read "Toy"): inventory corrected to three clauses. Approval clause ends June 14, 1935 by repeal. The overtime stay ends on its own terms on January 1, 1934, recorded inclusive under the 2026-10-21 until-date ruling with the exclusive reading stated; end evidence is the own-terms record on the registered APP text, not the clause-drafts copy. The activation clause ("at which time such provisions shall become effective") ends June 14, 1935 by repeal.

Blocked (precise gaps are in each row's `unresolved_material_gaps`):

- EO 6204-B: provisional approval of Sections III, IV, V, IX "after a hearing"; held EO 6331-E approves the Throwing code after hearings and may have superseded it in 1933. EO 6331-E is not carried as dossier evidence and the final code text is not held, so the repeal date cannot be shown to be the first end. Needs a source supplement of EO 6331-E and the code's contents and effective date.
- EO 6209-A and EO 6209-B: section 4 agreements binding an industry to Cotton Textile Code provisions "pending" a code and "subject to cancellation at any time"; outside the shared analysis (section 4(a) category). For 6209-B, held EO 6295 is the likely own-terms end but is not carried and the code's effective date is not held. For 6209-A no held text shows a Textile Finishing code.
- EO 6210-A: provisional approval pending hearing and final approval, with several contingent commands (articles effective, articles ineffective); no held final approval or cancellation.
- EO 6295: approval plus a stay running fourteen days after the code's effective date (not held); held EO 6347 extends the stay.
- EO 6326: condition creating a Planning and Fair Practice Agency with Administrator-appointed members (committee and appointments); no end shown and its dependence on the repealed provisions is not established.
- EO 6347: stay "pending the determination by the Administrator"; the determination is a contingent own-terms end that could precede June 14, 1935, and no held record shows it.
- EO 6445 and EO 6465: plain approvals, but the only registered text is a Wayback-only APP capture, which fails offline custody; no other registered copy held.

## What took the time (one line per order)

- 6293, 6310, 6358, 6377, 6386, 6389, 6392, 6401, 6531: read text (about 1,300 characters), confirm one clause and no own terms, read the LOOKUPS code-name hits; minutes of reading only.
- 6331-E: relating it to 6204-B to confirm the earlier order is not an end.
- 6503: deciding the price-list condition is code-dependent with no term.
- 6875: two-part sentence and the later work-assignment orders (6878, 6930) read to confirm they do not end the code.
- 6441-A: finding the absolute offsets for the one-clause inventory correction.
- 6393: three-way split, offsets, choosing the registered-text own-terms record over the clause-drafts duplicate, until-date wording.
- 6204-B, 6209-A, 6209-B, 6210-A: deciding whether interim approvals and section 4 agreements could ride the repeal route (they could not without ending instruments in the dossier).
- 6295, 6347, 6326: tracing the stay chain and the committee condition; effective date and determination not held.
- 6445, 6465: Wayback capture check only.

## Batch-check

`apply` (applied-v1): 14 assembled proposals, 9 blocked, 23 members, 0 extraction calls, 33 source hashes checked, about 64 seconds.
`batch-check`: 14 claims checked, 14 strict pass, 0 strict fail; actual checker 14 of 14 all checks passed; actionable failures none.

## Tool defects and friction

- `jobs/claim-kit/n08.md` named in the task does not exist; the brief and BATCH.md sufficed.
- `cruden.py search` with a many-term regex scanned the whole corpus in about two minutes and returned mostly unrelated modern orders; the LOOKUPS code-name hits were more useful. A date-range or filename filter would help.
- The sheets pre-fill a second `working_text` confirmation for a clause-drafts copy. I removed it for every submitted order (the claims cite the registered APP text) and apply accepted that.
- `load_packet` returns a tuple (packet, shared), not a dict, and takes Path objects; `PACKET.json` can be read directly as JSON.

## What LOOKUPS.md missed

- It lists later held orders that name a code but does not say whether each is an amendment, an appointment, a transfer of functions or an ending, so the reading was still needed (EO 6529, 6538, 6878, 6930, 6999).
- It does not flag which held later orders are the likely ending instrument for an interim order (EO 6331-E for 6204-B, EO 6295 for 6209-B), nor that those instruments are absent from the dossier's evidence ids and so cannot be cited as `end_id`.
- It has no line for order-type flags (section 4 agreement, committee-creating condition, stay chain).
- The own-text signals for EO 6393 gave the until date but not that the same sentence holds a separate activation command.

## Where the shared analysis did not fit

- Interim or provisional approvals ("pending hearing", "pending approval of a code", "subject to cancellation") and section 4 agreements: the repeal route does not apply without ending instruments, and section 4(a) agreements are outside the analysis.
- Stays inside an approval: the analysis says a stay is a separate clause with its own end; for EO 6295 and EO 6347 the own-terms end cannot be dated from held evidence.
- Committee-creating conditions (EO 6326): the analysis does not say whether the repeal extinguishes a body created to cooperate with the Administrator, who remained in office until 1936.

## Tool-call count

About 40 tool calls (reading, packet inspection, one corpus search, sheet generation by script, apply, batch-check, report).
