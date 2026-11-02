# Producer report, packet n05 (NIRA code approvals), producer: Claude (Sonnet 5.5)

Start UTC: 2026-10-31T22:13:03Z
End UTC: 2026-10-31T22:26:55Z
Final applied directory: research/excavator/claude-apollo-2026-10-31/n05/packet/supp/applied-v1 (no actionable failures, so no applied-v2)

## Outcomes (14 submitted, 9 blocked)

Submitted (first end 1935-06-14, SUPPLEMENT:SJRES113, mechanism statutory_repeal_of_code_approval_and_enforcement_provisions; savings transferred_or_accrued on SJRES113; Schechter and NIRA3 in source_notes):
- EO 6250 Theatrical code approval; EO 6258-D Men's Clothing; EO 6273 Leather; EO 6311 Knitting/Braiding/Wire Covering Machine; EO 6314 Laundry and Dry Cleaning Machinery; EO 6318 Luggage and Fancy Leather Goods; EO 6356 Industrial Supplies and Machinery Distributors; EO 6412 Ladder; EO 6485 Machined Waste; EO 6523 Brass and Bronze Ingot. Each is a bare approval with no other command; page check was a Common Crawl mirror with matching number, date and text hash.
- EO 6423-A Imported Date Packing: the machine inventory held only the five findings paragraphs and omitted the approval. Corrected to one scope, characters 1486-1777 (inventory override, new scope EO:6423A#corrected-1).
- EO 6539 Lace amendment and EO 6654 Lumber amendment: amendment approvals, no other command; later and earlier orders naming the code are recorded as non-ends.
- EO 6684-E Mason Contractors Chapter: approval of the chapter plus modification of the Construction Industry code approval, both code-dependent in one sentence. Later Mason agreement-approval orders (labelled EO 6813, 6949, 6985) are recorded as later events, not ends.

Blocked (precise gap):
- EO 6249: item (1) condition creates a Lace Manufacturing Industry Committee (5 elected, 3 appointed without vote); no held end for that command. Held text also gives both August 7 and July 7, 1933 as the amended-code submission date.
- EO 6306: condition directs the National Lime Association to amend its bylaws "as soon as practicable"; no date, no evidence of performance.
- EO 6349: condition creates a Marking Devices Industry Code Authority (11 elected, 3 appointed); no held end.
- EO 6391: only registered source is the APP live harvest (.live.txt), which fails offline custody. The Common Crawl mirror row for the same text (source sha256 394b92c5...) exists but is not registered in the packet. No legal gap.
- EO 6456: no held text, no clause inventory, no page record; only the WPA list line.
- EO 6487: only page record is a Wayback capture, which fails offline custody. No legal gap.
- EO 6513-J: mixed order: Inter-Code Committee appointment and powers, report due by June 30, 1934 (deadline, not an end), contribution arrangement direction, two codes, effective-date command; inventory has duplicate scopes.
- EO 6652: includes a section 4(a) agreement (Article X) and a condition delegating standing modification power to the Administrator; both are outside the shared analysis categories.
- EO 6659: three conditions with election periods running from the code's effective date (not held), an exemption from other codes, and a direction to two associations to submit membership lists.

## What took the time (one line per order)
- EO 6250, 6258-D, 6273, 6311, 6314, 6318, 6356, 6412, 6485, 6523: reading a one-paragraph text; the explanations are generated from one template with per-order quotes (script, quotes asserted against the held text).
- EO 6423-A: found the inventory omission and computed the correct span.
- EO 6539, 6654, 6684-E: reading for hidden commands; tracing lumber and mason related held orders (cruden search).
- EO 6249, 6306, 6349: deciding whether a creation/direction condition is code-dependent; no held evidence, so blocked.
- EO 6391, 6487: custody check via DOCUMENTS.jsonl and MIRROR_DOCUMENTS.jsonl.
- EO 6456: confirmed nothing held.
- EO 6513-J, 6652, 6659: reading long mixed texts and identifying each separate command.

## batch-check counts
packet_members 23; claims_checked 14; strict_claim_pass 14; strict_claim_fail 0; actual checker claims_all_checks_passed 14, mechanical fail 0, unverified 0, gate passed 14; blocked 9; actionable_failures []; independent_human_certifications 0. Apply took 75 s.

## Tool defects
- batch.load_packet takes Path objects and returns a tuple (meta, dossiers, ...); passing strings raised TypeError. The brief's signature was not enough to use it without trial.
- apply and batch-check write nothing to stdout until finished, and batch-check takes several minutes (about 2-3 min here, with several other batches running), so polling is slow; the output file stays empty until exit.
- No "changed Valla review context" refusal occurred.

## What LOOKUPS.md missed
- It reports code-name mentions only for the exact title phrase; it missed the three later Mason Contractors agreement orders for EO 6684-E (found with a separate search on "Mason Contractors").
- It does not say that EO 6391's mirror capture exists in MIRROR_DOCUMENTS.jsonl even though the packet registered the live harvest; I found it by grep.
- Its "Own-text signals" list shows false positives ("Suspender", "effective date of the Code") and misses conditions that create committees or direct associations; those were found only by reading each text.
- It does not flag that the held COUNTS of clauses mis-segment findings (EO 6423-A) or duplicate scopes (EO 6513-J).

## Where the shared analysis did not fit
- Conditions in an approval that create a body (committee, Code Authority) or direct a private association (EO 6249, 6306, 6349): the analysis lists mixed orders as needing each command's own end but gives no rule on whether such conditions fall with the approval; blocked rather than assumed.
- Section 4(a) agreements inside an amendment (EO 6652) and election periods running from an unheld effective date (EO 6659) are in its undecided categories.
- A recorded date was not needed for the Schechter note beyond the supplied wording; used as given.

## Other notes
- Evidence quality caveat: all 14 claims rest on APP transcriptions (grade mirror_transcription, acceptable_as_original false) with the standing note; certified count stays 0.
- EO 6249's operative sentence cites "July 7, 1933" while its recital says "August 7, 1933"; recorded in the block, not resolved.
- Working files (generator script and backups of the blank sheets) are in the session scratchpad, not in the repository. Nothing outside this packet was written.
- Tool-call count: about 58.
