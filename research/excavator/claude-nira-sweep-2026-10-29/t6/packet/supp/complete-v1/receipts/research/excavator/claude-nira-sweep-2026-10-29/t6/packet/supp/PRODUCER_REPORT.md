# Producer report: claude-t6-producer (batch t6)

Start 2026-10-29T15:16:35Z; end 2026-10-29T15:35:02Z. Final applied directory: `research/excavator/claude-nira-sweep-2026-10-29/t6/packet/supp/applied-v1`.

## Outcomes (24 orders: 16 submitted, 8 blocked)

Submitted, each ended 1935-06-14 by S.J. Res. 113 section 2 (`SUPPLEMENT:SJRES113`), with Schechter and NIRA 3 recorded as source notes and savings `transferred_or_accrued` (`SUPPLEMENT:NIRA5`):
- EO 6242-A, 6317, 6330, 6379, 6416-A, 6428, 6543-E, 6543-K, 6557-A: plain code approvals, no own-terms end, no held earlier action. 6242-A has two later exemption denials (EO 6274, 6331) and 6330 a later amendment (EO 6875); none ends the approval. 6330's "distinctly understood" wage-differential qualification is treated as part of the approval.
- EO 6529: approval of modifications of the Textile Bag code (base approval EO 6293); code-dependent.
- EO 6600: approval with one condition (registration of warehousing enterprises' vehicles with the household-goods code committee/authority). Judgment call: treated as a continuing code condition, not a one-time performance; EO 6684-D (hearing on coverage before June 15, 1934) and EO 6925 (recites the Trucking code in force Dec 19, 1934) noted, neither an end.
- EO 6631-A, 6756-F, 6794: inventory corrected to one clause (the operative approval); the machine inventory had findings 1-5 as five clauses and item 5 swallowed the operative paragraph. 6756-F and 6794 have later amendment orders (6921, 6965, 7019; 6903, 7016) as later events, not ends.
- EO 6921: whole-paragraph clause; later amendments 6965, 7019.
- EO 6678: general order prescribing a code-administration-expense clause for any approved code. Judgment call: not a single-code approval and the shared analysis does not name this type; submitted as a code-dependent standing prescription (each command takes effect only as part of an approved code).

Blocked, with the gap:
- EO 6255: only registered text is an APP live harvest (the sibling .txt has identical bytes); custody not re-provable.
- EO 6457: Wayback-only APP capture fails offline custody.
- EO 6294: condition (2) directs the American Transit Association to amend its By-laws "as soon as possible after the effective date"; effective date and performance not held.
- EO 6601: Administrator's report within 120 days after the code's effective date plus reserved presidential power; effective date not held; report date is a deadline.
- EO 6604-A: 90-day approval (own-terms end about May 16-17, 1934, start date unstated), report for "further order", area-by-area effectiveness conditions; extension or performance not held.
- EO 6604-B: items 1-2 end by own terms (June 1, 1934) but item 4 (stop-loss suspension pending further order) and item 5 (report 90 days after the effective date) cannot be closed.
- EO 6606-G: conditions (1) and (2) are 60-day deadline commands with no held performance; EO 6613 later touches Article VII.
- EO 6813: approval of an employer-employee agreement (section 4(a)/7(b) category the shared analysis leaves undecided).

## What took the time (one line each)
- 6242-A, 6317, 6379, 6416-A, 6428, 6543-E, 6543-K, 6557-A, 6921: read and template; negligible.
- 6330: judged the wage-differential understanding (part of the approval); checked EO 6875.
- 6529: confirmed base code approval EO 6293; template.
- 6600: judging the registration condition; read EO 6684-D and 6925.
- 6631-A, 6756-F, 6794: found the inventory error and computed the corrected span; read later amendment orders for dates.
- 6678: deciding whether a general clause order fits the shared analysis; six clause rows.
- 6255, 6457: custody check (DOCUMENTS.jsonl, LOOKUPS page-check line).
- 6294, 6601, 6604-A, 6604-B, 6606-G: reading each condition against the block rules; 6604-B and 6606-G longest.
- 6813: category check against the shared analysis.

## batch-check
claims_checked 16, strict_claim_pass 16, strict_claim_fail 0, actual checker all 16 passed, blocked 8, actionable_failures none, human certifications 0. Apply: 16 assembled_proposal, 8 blocked, 168 s wall (shared machine busy with another batch's completion run).

## Tool defects
- `kit.py apply` took about 168 s and `batch-check` about 5 minutes on the shared machine; with the background mode and no progress output, only file listing shows it is alive.
- Foreground waiting is blocked and `pgrep -f` inside a Monitor matches the monitor's own command line, so a monitor waiting on a process by name never exits (lost a few calls).
- The scratchpad directory is shared between concurrent producers; my first helper scripts (`load.py`, `dump.py`) were overwritten by another producer's file of the same name. I moved to `scratchpad/t6producer/`.

## What LOOKUPS.md missed
- It lists only held texts naming the code; it does not show dates or operative effect of those texts, so EO 6274/6331 (denials), 6613, 6684-D and 6925 had to be opened to be characterized.
- Code-name mentions are keyed to the title's code name, so 6678 (no code named) got nothing; search for number citations only.
- It does not flag that a packet text is `.live.txt` with a byte-identical sibling `.txt` (6255), nor that a clause-drafts copy is listed as a second working-text confirmation (6294, 6601, 6604-A, 6604-B, 6606-G, 6678). For 6678 only the registered APP text was confirmed; apply accepted that.

## Where the shared analysis did not fit
- Orders with one-time contingent commands beside the approval (6294, 6601, 6604-A/B, 6606-G): the analysis says each needs its own end; no held evidence of performance, so blocked.
- 6678 (general clause-prescribing rule) and 6813 (agreement approval) are not single-code approvals; 6678 submitted on a reasoned extension, 6813 blocked.
- The analysis's ending theory rests on the code's legal effect through section 3; for continuing conditions (6600) I applied it, for one-time commands I did not.
- Own-terms ends before June 14, 1935 appeared in 6604-A and 6604-B; start date and "or until the Administrator reviewed" alternatives keep exact dates unestablished.

## Tool-call count
About 62 tool calls (including background waits and monitors).
