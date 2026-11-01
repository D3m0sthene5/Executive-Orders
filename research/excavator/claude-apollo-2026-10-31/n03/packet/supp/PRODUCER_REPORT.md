# Producer report, packet n03 (NIRA code orders)

Producer: Claude (Sonnet 5.5). Start 2026-10-31T22:13:01Z. End 2026-10-31T22:28:11Z.
Final applied directory: research/excavator/claude-apollo-2026-10-31/n03/packet/supp/applied-v1 (single pass; no v2 needed).

## Outcome per order

Submitted (19), each with first end June 14, 1935 by S.J. Res. 113 section 2 (SUPPLEMENT:SJRES113), savings transferred_or_accrued, Schechter and NIRA section 3 recorded in source_notes:

- EO 6206-A: final approval of the Cotton Textile Code; the order withdraws the four-month termination condition, so no own-terms end. Schedule A items are code terms covered by the one clause. The July 9, 1933 conditions accepted by the applicants are not held in text (noted in scope_check).
- EO 6242-B, 6248, 6309, 6384, 6423, 6482, 6509, 6513-D, 6543-F: plain code approvals, no own terms, no held earlier action naming the code (EO 6248: only a later denial of exemption, EO 6296).
- EO 6420-A and EO 6876: approvals of amendments to the Cotton Textile Code; later events only. The held text of EO 6876 does not reproduce the amendment (recorded as a limit in scope_check).
- EO 6487-B and EO 6811: inventory corrected. The machine clauses were numbered findings; the one operative command is the final approval sentence.
- EO 6945, 6954, 7000: approvals of amendments to the distilled-spirits codes; later orders re-approve the code as amended and are later events.
- EO 6684-C: approval of the Electrical Contracting Chapter and modification of the Construction Industry Code approval; no cancellation of that code found.
- EO 6526: inventory corrected into two clauses. The denial of the Southern Plow Manufacturers Association's exemption application is exhausted on December 21, 1933 (end_id is the order's own original text; the June 14, 1935 repeal is a later event). The wording change in Article VI, Section 2 ended with the repeal.

Blocked (4):

- EO 6206-B: approves only some Cotton Thread provisions "subject to the interpretations and conditions imposed by me" on the July 9, 1933 Cotton Textile approval, which is not held. That order carried a four-month termination condition (condition 12), withdrawn for the Cotton Textile Code only, by EO 6206-A. Whether it reaches the thread provisions cannot be read. No hearing or final approval of the thread code is held.
- EO 6369: stays 1 and 3 end on a determination, hearing or further order that no held record shows; item 2 depends on stay 1. The repeal would be only an outer bound.
- EO 6434: the only registered text is a Wayback-only APP capture (fails offline custody). It is also a mixed order: the condition B stay is capped at four months from the code's effective date (not held) and set by the Administrator, and condition A is a compact "if and so long as" condition.
- EO 6533: condition 2 limits approval as a separate code to three months from the effective date, and the effective date is not held. EO 6606-E amends only condition 1.

## What took the time (one line per order)

- 6206A: reading Schedule A, the six cotton-textile stay and amendment orders, EO 6858; deciding the Schedule A report item is a code term.
- 6206B: deciding the incorporation by reference of unheld July 9 conditions blocks.
- 6242B, 6248, 6309, 6384, 6423, 6482, 6509, 6513D, 6543F: reading one short text each; checking the corpus for the code name and any cancellation order.
- 6369: deciding the open-ended stays cannot take the repeal as a first end.
- 6420A, 6876: confirming the later cotton-textile orders; noting the amendment text is not reproduced.
- 6434: confirming the Wayback-only capture and the mixed commands.
- 6487B, 6811: computing absolute spans for the corrected one-clause inventory.
- 6526: splitting denial from the wording change and choosing the end for a denial.
- 6533: searching for the code's effective date (none held); reading EO 6606-E.
- 6684C: surveying Construction Industry orders and the one cancellation order (EO 6925, a different code).
- 6945, 6954, 7000: confirming each later re-approval order is only an amendment.

## batch-check counts

packet members 23; claims checked 19; strict pass 19; strict fail 0; actionable failures 0; actual claim checker: 19 all checks passed, 0 mechanical fail, 0 unverified; blocked 4; human certifications 0. Apply: assembled_proposal 19, blocked 4 (69 seconds).

## Tool defects

None blocking. apply and batch-check take about a minute each on a shared host with other producers running, and `pgrep` patterns must name the packet folder to avoid matching other producers' processes. `kit.py` documentation points to a `jobs/claim-kit/n03.md` that does not exist (the brief says to consult it only for gaps; none arose).

## What LOOKUPS.md missed

- Cancellation orders exist in the corpus (EO 6925 cancels the approval of the Cinders, Ashes and Scavenger code). LOOKUPS only lists code-name mentions, which is enough here, but I ran a separate title scan to confirm no cancellation names these codes.
- LOOKUPS did not flag orders that incorporate an unheld earlier order's conditions (EO 6206-A, 6206-B) or the Construction Industry parent code for EO 6684-C (its code name differs from the chapter title).
- Own-text signals for EO 6206-B and 6369 flag conditions but not that the end events are unheld.
- The page check flags Wayback only as a capture-archive field; it did not mark EO 6434 as failing custody.

## Where the shared analysis did not fit

- Stays and conditions with open-ended own-terms ends (EO 6369, 6434) and provisional approvals incorporating unheld conditions (EO 6206-B): the analysis says each command needs its own end, and the evidence does not supply one, so I blocked rather than use June 14, 1935.
- Denial of exemption: applied as written (exhausted on its date). The kit has no state for this; I used state terminated with the order's own original text as end_id and a free-text mechanism, which the checker accepted.
- Section 3(d) recital in EO 6487-B: the order approves under Title I, so I treated it as a section 3 approval; flag for the reviewer.

## Tool-call count

About 62 tool calls (reads, searches, one build script, apply and batch-check in the background, monitors).

Certified count unchanged at 0.
