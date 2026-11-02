# Producer report, e1 (Erasmus resubmission, fix round)

Producer: Claude (Sonnet 5.5). Start 2026-11-02T04:24:09Z. End 2026-11-02T04:33Z. About 36 tool calls.
Final applied directory: research/excavator/claude-erasmus-2026-11-02/e1/packet/supp/applied-v3 (applied-v1 and v2 kept, never overwritten).

## Outcome: 4 submitted, 0 blocked
batch-check (v3): 4 packet members, 4 claims checked, strict pass 4, fail 0, actionable failures 0, actual checker gate passed 4. Geddes v3: 0 flags, 0 coverage gaps.

## Per order: brief defects and what was done
- EO:6811 (filed_claim_correction, with second attempt). Defect: the claim named the November 26, 1933 approval "EO 6444". Confirmed: held APP heading and register give EO 6444-A; EO 6444 is the Naval Petroleum Reserve No. 2 order of November 25, 1933. Fixed. Rechecked everything else: the second attempt already dropped the sibling "Approval recommended" sentence (6811 has no such line); EO 6756-D, 7000 and 7018 dates and suffixes agree with INDEX.jsonl; the corrected clause span 1405-1916 was checked against the held text (starts "Now, Therefore," ends "hereby amended."); the inventory reason now says items 1 to 5 are findings and that the fifth machine clause also takes in the closing paragraph. End date kept (June 14, 1935, S.J. Res. 113 sec. 2). Later EO 7000 and 7018 are described as amendments and not entered in later_events (see tool defects).
- EO:7000 (filed_claim_correction, with second attempt). Same 6444 vs 6444-A defect. Confirmed and fixed. Other checks as for 6811; "Before this order" list (6444-A, 6756-D, 6811) and "after" (7018) verified against held texts.
- EO:6684C (filed_claim_correction). Geddes flags: EO 6731 (June 6, 1934) and EO 6925 (December 19, 1934) are EO 6731-A and EO 6925-A. Confirmed and fixed. Also found and fixed: sibling approvals carried no suffix for EO 6988-A and 7025-A; the claim quoted "Approval recommended" but this order's held line is "Approval Recommended:" (now "Approval Recommended"); "a approval" grammar; the claim said the sibling approvals 6750-B, 6988-A, 7025-A were found but only four chapter approvals had been read (I read all seven plus 6731-A, 6925-A and the five Electrical Contracting Division agreement orders 6883-B, 6892-A, 6974-A, 6984-A, 7010-F; none cancels or suspends this chapter). 6731-A is described as the appointment of Sullivan W. Jones, from its held text.
- EO:6321 (filed_claim_correction). Geddes flag: EO 6948 (January 18, 1935) is EO 6948-A. Confirmed and fixed. Rechecked: the 6948-A description (60-day stay of the maintenance code as to retailing-trade members, later determination by the National Industrial Recovery Board) matches its held text; a "Motor Vehicle Retail" text search finds only 6321 and 6948-A. The claim names 6948-A in the reasoning as a later order that is not an end, with a disclosure that no event record is available for later_events.
No defect disputed or left unresolved.

## What took the time (one line each)
- 6811: second attempt was a near-complete draft; time went to suffix checks of 6444-A/6756-D/7000/7018 and verifying the 1405-1916 span.
- 7000: same as 6811, small.
- 6684C: longest; reading seven sibling chapter approvals, 6731-A, 6925-A and five Electrical Contracting agreement orders, and finding the unsuffixed 6988-A/7025-A and the capital-R quotation.
- 6321: small; one suffix fix and the 6948-A text check.

## Tool defects and notes
- later_events cannot be filled for later orders (EO 7000, 7018, 6948-A): the packet's source catalogue holds only ORIGINAL, CLAUSES and SUPPLEMENT ids, so there is no evidence id to cite. The claims say so in plain words instead. A source-supplement declaration for later orders at prepare time would allow real later_events.
- Geddes v1 gave a coverage gap on 6321 for the deictic "the code"; my first rewording (v2) triggered a flag because the sentence read as a negative name claim although it identified EO 6948-A; v3 splits the sentence. Geddes treats "no held order ... names X" as a negative even when the next clause names the one order.
- apply with 4 orders takes about 6 seconds; batch-check about 40 seconds including Geddes.

## What LOOKUPS.md missed
- For 6684C it reports no code-name mentions because its literal is the chapter name; the real sibling and parent-code instruments (EO 6578 parent, six chapters, 6731-A, 6925-A, Electrical agreement orders) need a "Construction Industry" search. For 6321 it lists only the 6948-A mention (correct). For 6811/7000 it lists the Rectifying Industry orders (a different code) among the mentions.
- The slim view omits the full prior-claim text and the later-order text; I read the prior claims with a small script (research/readiness/claims/claude-2026-10-31-apollo-n03.jsonl lines 14, 15, 18; apollo-n06.jsonl line 2) and the second attempt (c1 applied-v1 lines 14 and 17), which the brief names. No suffix information for cited orders is in the view.

## Where the shared analysis did not fit
It fit all four. It does not say how to record later amendments when the packet has no event ids.

## Full-packet files opened beyond the views
supp/LOOKUPS.md (read in step 0), supp/decisions.csv and clauses.csv (edited, as required), supp/PACKET.json (searched by script for later-event evidence ids, not read), supp/READ.md (grep only, to read the search coverage notes for search_ids). Also read jobs/claim-kit/AGENT_PROTOCOL.md lines 100-175 and assemble.py around later_events to learn the later_events field format, which the brief does not cover.

## Geddes
v1: 0 flags, 1 coverage gap (EO:6321, literal_name_unresolved) fixed in v2. v2: 1 flag (b08a7cd28aef1992, EO:6321) fixed in v3. v3: 0 flags, 0 gaps. Resolution recorded in applied-v3/GEDDES_RESOLUTIONS.json.

## Memory-derived facts
None used.
