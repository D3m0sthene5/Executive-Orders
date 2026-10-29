# Producer report: batch t5 (claude-t5-producer)

Start 2026-10-29T15:16:34Z. End 2026-10-29T15:38:29Z. Packet: research/excavator/claude-nira-sweep-2026-10-29/t5/packet/supp. Final applied directory: applied-v1 (the first apply passed batch-check, so there is no v2).

## Counts

24 packet members: 13 submitted, 11 blocked. `batch-check`: claims_checked 13, strict_claim_pass 13, strict_claim_fail 0, actionable_failures none; actual checker 13 of 13 all checks passed (mechanical pass 13, unverified 0, fail 0, gate passed 13). Independent human certifications 0.

## Outcome per order

Submitted (first end June 14, 1935 by S.J. Res. 113 section 2; Schechter recorded as a validity characterization only; June 16, 1935 not an end):

- EO 6322 Glass Container, 6394 Funeral Supply, 6422 Hardwood Distillation, 6429 Limestone, 6436 Special Tool, Die, and Machine Shop, 6481 Furniture Manufacturing, 6513-A Set Up Paper Box, 6521 Rolling Steel Door: plain section 3 approvals; one operative clause each; no own-terms end; no later held order names the code or the order.
- EO 6522 Rayon and Silk Dyeing and Printing: plain approval; "to become effective in place of the Code of Labor Provisions" treated as a term of the approval, with no claim about the July 22, 1933 instrument.
- EO 6444-A Distilled Spirits: inventory corrected. The machine inventory made the findings numbered 1 to 5 into five clauses; the corrected inventory is the one approving sentence (characters 1428 to 1715). Held later orders 6756-D, 6811, 7000 and 7018 modify the approval to cover the code "in its entirety as hereby amended" and treat the code as continuing, so they are later events. I read 6756-D and 6811 in full and set the dossier's "target provision not located" notes aside as not material to the first end.
- EO 6685 Distilled Spirits Rectifying (amendments) and EO 7018 Distilled Spirits (amendments): single operative command each; later amending orders are later events (for 6685: 6812, 6945, 6954, 7017, 7022; 6812 recites 6685 by its date).
- EO 6711-A homeworker rules: the machine inventory omitted the introductory ordering sentence and merged rule 2 with the closing paragraph and signature, so the inventory is corrected to four clauses (582 to 910, 912 to 1688, 1690 to 1915, 1917 to 2810). All four are code-dependent (they govern how code provisions are construed, require filing with the Code Authority, and bind those subject to codes that prohibit homework). The duration phrase "until revoked or modified" has no date and no held revocation. This is the most judgment-heavy submission: the order cites Title I generally, and the shared analysis does not decide general rule-prescribing orders (section 10 category). The claim says so in its independent-command check.

Blocked (precise gap recorded in `unresolved_material_gaps` of decisions.csv):

- EO 6254 Iron and Steel: held EO 6730 (May 30, 1934) approves a revised code effective June 11, 1934 and continues the August 19, 1933 code only until then. That is a possible superseding event before June 14, 1935, and the packet has no evidence record for it, so it cannot be cited. A June 14, 1935 end would contradict a held text.
- EO 6271 Wall Paper and EO 6292 Oil Burner: clause 1 creates a committee or Code Authority as a Planning and Fair Practice Agency "to cooperate with the Administrator"; no duration, constitution or dissolution held. Committees need their own end or a block.
- EO 6438 Hotel: conditions 2 and 3 (90 days from an unheld effective date) were struck by held EO 6620-B on February 26, 1934, which is an earlier first end for those clauses, but 6620-B is not in the packet evidence and cannot be cited as an end.
- EO 6513-B Knitted Outerwear and EO 6653 Photographic and Photo Finishing: stays that end on an Administrator determination or further order, with no held determination or order. A stay pending a determination is a contingent command, and a missing record does not show that none was made.
- EO 6647-B Machinery and Allied Products: conditions due 30 and 60 days after the code's effective date, which no held source states; no evidence on performance.
- EO 6756-E: no held text; only the WPA list line.
- EO 6767: clause 3 is a six-month study and report direction (a deadline, not an end), clause 4 modifies prior orders including EO 6646, and clause 2 delegates a power to the Administrator; none has an established end.
- EO 6871: clauses 3 to 5 continue or appoint committees and require reports (November 15, December 1, 1934 and January 15, 1935 are deadlines). Clause 1 (exhausted October 12, 1934) and clause 2 (stay to and including December 1, 1934) have supportable ends, but one outcome cannot carry them while the rest are open.
- EO 6955 Automobile: clause 3 authorizes industry agreements (possibly section 4(a), which ran to April 1, 1936) and clause 4 confirms and continues labor-controversy machinery (section 7(a) or other authority). The shared analysis does not decide either category. Clauses 1 and 2 would end June 14, 1935.

## What took the time, one line per order

- 6254: first read as a plain approval; the extra search for the code's short name found EO 6730, which turned it into a block.
- 6271, 6292: deciding whether the committee condition is a section 3(a) condition of the approval or an independent body; blocked on the pitfall list.
- 6322, 6394, 6422, 6429, 6436, 6481, 6513-A, 6521: routine read, page check from LOOKUPS, short-name search for later orders.
- 6438: reading EO 6620-B, which strikes conditions 2 and 3, and finding no way to cite it.
- 6444-A: inventory correction (findings versus commands), reading 6756-D and 6811, and settling that restated approvals are later events.
- 6513-B, 6653: judging the "until determination" and "pending further order" stays; no later order found.
- 6522: judging the "in place of the Code of Labor Provisions" wording.
- 6647-B: checking whether the code's effective date is held (it is not).
- 6685: false-positive report-deadline leads; later amending orders.
- 6711-A: rebuilding the four-clause inventory and deciding the section 10 category question (the longest single item).
- 6756-E: confirming no text exists.
- 6767, 6871, 6955: clause-by-clause reading of mixed orders.
- 7018: restated approval versus amendment.

## Tool defects

- `batch.load_packet(folder, repo, check_sources=False)` raises `TypeError: unsupported operand type(s) for /: 'str' and 'str'` when given absolute path strings; it needs `pathlib.Path` objects. The prompt says "absolute paths" without saying they must be Path objects. It returns a tuple (packet, second object), and the loaded dossiers still contain unexpanded `@eo:ref` pointers, so it did not replace reading READ.md.
- `kit.py apply` took 262.7 seconds of wall time, and `batch-check` several minutes, against the roughly 20 seconds quoted for `view --order`. Other batches (t2 complete, t6 batch-check) were running on the same machine at the same time, so load is the likely cause, not the tool.
- No apply refusal and no "changed Valla review context".

## What LOOKUPS.md missed

- EO 6730 (iron and steel revised code, effective June 11, 1934) for EO 6254. The code-name pattern is "Code of Fair Competition for the ...", and 6730 says "Code of Fair Competition of the Iron and Steel Industry". A shorter name search found it.
- LOOKUPS did list EO 6620-B under EO 6438, but only as a code-name mention with the snippet cut before "striking therefrom the conditions numbered two (2) and three (3)", so its significance is not visible from LOOKUPS.md.
- For EO 6444-A and EO 6685 the "code-name mentions" mix two different codes (Distilled Spirits and Distilled Spirits Rectifying), which makes the lists look longer than they are.
- Structural gap: the dossier chain is empty ("generic_refs_excluded" 221), so an earlier end that exists in held texts (6620-B for 6438; 6730 for 6254) cannot be cited as `end_id` or a later event without an ACT override record with independent review. This will recur in later batches.

## Where the shared analysis did not fit

- Committees, stays and conditions: the held NIRA excerpt says the President "may, as a condition of his approval of any such code, impose such conditions ... and may provide such exceptions to and exemptions from the provisions of such code", so conditions, stays and exceptions in an approval are arguably within the approval power that section 2 of S.J. Res. 113 repealed. The brief's pitfall list says committees and "pending further order" stays need their own end or a block, and I followed the pitfall list (6271, 6292, 6513-B, 6653 blocked). A coordinator ruling on that point would unblock up to four orders.
- Restated or revised code approvals: the shared analysis says amendments are later events. EO 6730 explicitly continues the old code only until the revised code takes effect, which reads as supersession; the distilled spirits orders only "modify my previous approval", which reads as amendment. The analysis does not say where the line is.
- Section 4(a) agreement authorizations and labor-board continuations inside an approval order (6955) are in the analysis's undecided list but appear inside plain approvals.
- General rule-prescribing orders under Title I (6711-A) are not covered.

## Tool-call count

About 75 tool calls, counted from memory and not tracked exactly: roughly 62 file reads, searches and shell commands, 2 background runs (apply, batch-check), and 6 monitor or wait calls.
