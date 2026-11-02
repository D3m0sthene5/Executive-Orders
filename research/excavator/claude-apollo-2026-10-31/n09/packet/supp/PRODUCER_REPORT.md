# Producer report, packet n09 (NIRA code orders), applied-v1

Producer: Claude (Sonnet 5.5), agent column `claude`.
Start UTC: 2026-10-31T22:13:15Z. End UTC: 2026-10-31T22:26:17Z.

## Outcome per order

Submitted (4): EO:6539A, EO:6847A, EO:6925A, EO:7020. Blocked (13): the rest. No Valla "changed review context" refusal occurred.

- EO:6539A submit. Wine Industry code approval; the five numbered findings are recitals, so the inventory was replaced by one corrected clause (the approval sentence, chars 1402-1676). Ends 1935-06-14 by S.J. Res. 113 section 2. EO 6900 and EO 7020 amend the code and are later events, not ends.
- EO:7020 submit. Approval of Wine Code amendments of 1935-04-19 (before the repeal); one corrected clause (370-778); ends 1935-06-14 by repeal.
- EO:6847A submit. Two corrected clauses: clause 1 (753-1059), termination of the stay of Section 1 of Article IX, is exhausted by performance on 1934-09-14 (repeal recorded as a later event); clause 2 (1060-1201), "shall remain in full force and effect", ends 1935-06-14 with the approval it preserves.
- EO:6925A submit. Cancellation of the Cinders, Ashes and Scavenger Trade code approval; exhausted by performance on 1934-12-19. The repeal is not its end and is not a later event (the approval had already ended); the surviving consequence (approval stands cancelled) is separated from the command.
- EO:6221A blocked. Condition (1) creates a Wool Textile Industry Committee (elected members plus appointees); no held end or evidence of its dependence on the code.
- EO:6355, EO:6479, EO:6606F blocked. The one command reaches section 4(a) agreements and section 4(b) licenses as well as codes; shared analysis item 5 leaves those undecided and S.J. Res. 113 section 2 supplies a reason only for the code reach. 6479 also preserves "any existing obligation to furnish reports"; 6606F has a good-cause contingency on its effective date. EO 6606-A (1934-02-17) supplements 6355 (later event, not an end).
- EO:6460, EO:6466, EO:6536 blocked. No held text; only the WPA 1944 list line.
- EO:6549A blocked. Conditions (1) and (2) run 30 days from the code's effective date, which is not held; conditions (3) and (4) are directions to the Administrator with no held performance; condition (6) has no end source.
- EO:6711 blocked. Registered original is a live-harvest APP page (fails offline custody; the Common Crawl mirror row has a different source sha256 the dossier does not cite); a section 10(a) regulation is outside the shared analysis.
- EO:6723 blocked. Suspension "until further orders" of codes of later-designated service trades (no designation held), local-agreement authority (section 4(a) type), insignia entitlement, supplementing power.
- EO:6734A blocked. Stay of Section 4 of Article VII "pending the further order of the Secretary of Agriculture" and Article IX conditional on the Secretary's written emergency declaration: no such order or declaration is held, and EO 6999 (1935-03-30) transferred the Secretary's functions to the National Industrial Recovery Board. The 20-day stay of Section 3 has a computable own-terms end (June 28 or 29, 1934) but cannot carry the order alone.
- EO:6750C blocked. Reaches agreements (section 4(a)); Secretary of Labor agency, Committee and rulemaking power are independent commands; July 15, 1934 effectiveness depends on a good-cause contingency.
- EO:6756A blocked. An offer to enter section 4(a)-type agreements with later-designated service trades; no designation, acceptance or end held.

## What took the time

- 6539A: inventory correction (findings versus operative paragraph), checking EO 6900/7020/6829 as non-ends.
- 7020: inventory correction; confirming no earlier cancellation.
- 6847A: splitting into an exhausted clause and a continuation clause; reading EO 6999 and deciding the continuation clause's end.
- 6925A: exhaustion on issuance versus repeal; savings source choice.
- 6221A: deciding that the committee condition is a separate command; searching for the committee elsewhere.
- 6355, 6479, 6606F: deciding the agreement/license reach blocks submission; reading EO 6606-A and EO 6829.
- 6460, 6466, 6536: confirming no text is held (quick).
- 6549A: reading conditions for the effective-date dependency.
- 6711: tracing which sha256 the registered original cites versus the Common Crawl mirror row.
- 6723, 6756A: reading the agreement-offer mechanics.
- 6734A: stays, Secretary of Agriculture contingency, EO 6847A and EO 6999 effects.
- 6750C: committee, Secretary of Labor agency, good-cause effective date.

## Batch-check

apply v1: 13 blocked, 4 assembled_proposal, 17 members, 0 extraction calls. batch-check v1: claims_checked 4, strict_claim_pass 4, strict_claim_fail 0, actionable_failures none, actual checker all checks passed 4, mechanical fail 0, gate passed 4, independent human certifications 0. Only applied-v1 exists; no correction version was needed.

## Tool defects and friction

- `apply` took about 31 s and `batch-check` took many minutes of wall time because many other packets ran `batch-check` concurrently (load average above 20 during this run).
- `later_events` can only cite evidence ids already in a member's dossier. EO 6900 and EO 7020 (amendments of 6539A's code) and EO 6999 (transfer of functions for 6847A's code) are held texts but have no dossier evidence id, so they appear in the earlier-end check text and not as later_events.
- The dossier's `own_terms` leads for 6847A are recital wording of the earlier order's stay (sunset_date, until_event); they are not terms of the order's own commands.
- The 6711 dossier offers three working-text confirmations (live copy, mirror copy, clause-drafts copy) for a single order; which one the ORIGINAL cites is visible only through LOOKUPS.json.

## What LOOKUPS.md missed

- No flag for mixed commands (committee, agreement offers, contingent stays).
- It did not show that EO 6999 (1935-03-30) names the Wheat Flour Milling code, nor that EO 6606-A and EO 6829 name EO 6355; I found these through the dossier's actor contexts and Cruden search.
- Own-text signals hid the effective-date dependency in 6549A conditions (OCR typos "fhis", "ater" break exact phrase matching).
- The 6711 page check reported only the live-harvest row, not that a Common Crawl mirror row exists under another sha256.

## Where the shared analysis did not fit

- General orders that modify or construe "any code, agreement, or license" (6355, 6479, 6606F, 6750C): the analysis excludes section 4(a) agreements and 4(b) licenses but selects such orders by title; the single command cannot be split.
- Stays and conditions that depend on a named officer's later act (6734A, 6723): the repeal is a plausible final end but not shown to be the first end.
- Cancellation orders (6925A): the analysis covers denials and one-time determinations; I applied the same exhaustion rule to a cancellation under section 10(b)/code Article VIII.
- Stay-termination orders (6847A): applied the one-time-determination rule to the termination clause only.

## Tool-call count

About 60 tool calls (reading rules and sources about 20; searches and text reads about 15; building sheets 3; apply/batch-check and waiting about 20). Estimated from the transcript.
