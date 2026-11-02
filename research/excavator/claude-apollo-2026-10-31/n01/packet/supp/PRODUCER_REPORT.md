# Producer report, batch n01 (NIRA code approvals)

Producer: Claude (Sonnet 5.5), as producer-n01. Start 2026-10-31T22:12:30Z; end 2026-10-31T22:28:28Z (batch-check finished; wall clock includes waiting for a heavily loaded machine).
Final applied directory: `research/excavator/claude-apollo-2026-10-31/n01/packet/supp/applied-v1` (only version; no fixes were needed).
Counts: 23 members; 14 submitted (assembled proposals), 9 blocked. Batch-check: claims checked 14, strict pass 14, strict fail 0, actionable failures none; the actual checker passed 14 of 14 with no network downloads. Certified count unchanged at 0.

## Outcome per order

Submitted (first end June 14, 1935 by S.J. Res. 113 section 2, unless noted):

- EO:6258A (Automobile Manufacturing Industry code approval): submit. The held amendments EO 6513-K, 6837, 6895 and 6955 each moved the code's expiration date before the date then in force arrived, up to June 16, 1935, so the code did not lapse by its own terms; the amendments and the EO 6417 supplement are later events. EO 6895 recites November 3, 1934 where EO 6837 states November 5, 1934; no lapse results either way.
- EO:6308 (Boiler Manufacturing Industry): submit. Approval "except that subparagraph (a) of article VII must be eliminated"; the exception narrows the approval and is not a separate command.
- EO:6381 (Asbestos), EO:6406 (Asphalt Shingle and Roofing), EO:6426 (Air Transport), EO:6430 (All-Metal Insect Screen), EO:6543N (American Match): submit; plain one-command approvals with no own terms and no earlier action in the held corpus.
- EO:6403 (denial of the Kaplan Brothers exemption application, Artificial Flower and Feather code): submit as exhausted on its own date, 1933-11-04 (`self_executing_dispositive_act_completed`, end id the order's own original), with the June 14, 1935 repeal recorded as a later event (id `SUPPLEMENT:SJRES113`, accepted by the checker).
- EO:6471A (Alcoholic Beverages Importing) and EO:6487A (Alcoholic Beverage Wholesale): submit, with the machine inventory corrected. The machine inventory split each order into four or five clauses, but the numbered items are findings, not commands; the corrected inventory is the one final approval command. Amendments EO 6794, 6903, 7016 (importing) and EO 6922, 7014, 7015 (wholesale) approve amendments and "modify my previous approval" to cover the code as amended; they are later events. EO 6487A recites section 3(d) as the route by which the Secretary of Agriculture presented the code; the repeal reaches power "to approve or prescribe" codes.
- EO:6790 (Auction and Loose-Leaf Tobacco Warehouse code): submit, two clauses after inventory correction. The approval ends on June 14, 1935. The proviso staying Section 24 of Article VII "for a period of twenty days" ends by its own terms on 1934-07-20 (`own_terms_fixed_term`; if June 30 is counted as day one, the last day is July 19). No held order exercises the reservation "unless I shall otherwise order".
- EO:6922, EO:7014 (Alcoholic Beverage Wholesale amendments) and EO:7016 (Alcoholic Beverages Importing amendments): submit. Each approves amendments (text not in the order) and modifies the prior approval; treated as continuing approvals that end on June 14, 1935, with the other amendment orders as later events, because "modify" enlarges the approval and the held text does not show any amendment replacing an earlier one.

Blocked (precise gap):

- EO:6368 (Advertising Specialty): mixed order. Condition (2) creates a committee (five industry members, three non-voting appointees) whose end no held source shows and the repeal does not obviously reach; condition (1) supersedes printing wage-and-hour provisions when the Printing code becomes effective, and that date is not held.
- EO:6446 (Anti-Friction Bearing): only registered text is a Wayback-only APP capture; fails offline custody.
- EO:6486 (Asphalt and Mastic Tile): only registered text is a live APP harvest with no archived capture.
- EO:6684F (Barber Shop Trade): no held text, only a WPA line stating a conditional approval; no inventory possible.
- EO:6513K and EO:6837 (automobile code amendments): each rewrites only the seventh paragraph of Article I (expiration date), "effective immediately". The next held amendment (EO 6837 for 6513-K; EO 6895 for 6837) rewrites that same paragraph and recites the earlier wording, so the clause's first end is that replacement (August 31, 1934 and November 2, 1934), not the June 14, 1935 repeal. The dossier registers no evidence id for the replacing order, so it cannot be cited as the ending instrument. EO 6895's text is Wayback-only, and its recital of the prior date (November 3) conflicts with EO 6837's text (November 5).
- EO:6895 (automobile code amendment): Wayback-only capture; and EO 6955 (January 31, 1935) replaces its paragraph, an ending the dossier does not register.
- EO:6543M (Blouse and Skirt): approval with a stay pending a hearing on a neckwear and scarf code and the Administrator's determination, plus a direction to the Administrator. Searches found no record of the hearing or determination, so the stay's end before June 14, 1935 is not established and a bounded interval cannot be claimed.
- EO:6725A (Baking): approval with two stays "pending my further order" and a 90-day report direction. Held EO 6743 (June 16, 1934) eliminates the second stay, stays the code's effective date to July 9, 1934 and extends the report date to November 15, 1934, but is not registered as evidence; the first stay's end event is alternative and contingent; no held record shows the report made.

## What took the time (one line per order)

- 6258A: tracing the four held expiration-date amendments to confirm no lapse before June 14, 1935.
- 6308: deciding that the article VII exception is part of the approval, not an independent command.
- 6368: reading the committee and the Printing-code condition as separate commands; no end evidence.
- 6381, 6406, 6426, 6430, 6543N: routine; quote verification only.
- 6403: applying the exhausted-denial rule and finding a format for the repeal as a later event.
- 6446, 6486: reading LOOKUPS page check (Wayback, live harvest) and blocking.
- 6471A, 6487A: correcting the inventory (findings versus the one command); checking Federal Alcohol Control Administration orders for any cancellation.
- 6513K, 6837, 6895: working out that each later amendment replaces the same paragraph; the 6837 and 6895 date discrepancy; the missing evidence ids.
- 6543M, 6725A: searching the corpus for the neckwear and scarf determination and for orders affecting the Baking code; reading EO 6743.
- 6684F: no text; blocked immediately.
- 6790: computing the 20-day stay end and checking for orders reserved by "unless I shall otherwise order".
- 6922, 7014, 7016: deciding that "modify my previous approval" is a continuing approval, not a replacement.

## Tool defects and friction

- `apply` and `batch-check` each took several minutes under machine load (20 or more concurrent processes); apply itself reported 57.8 seconds of work. Running ten `kit.py view --order` calls in parallel stalled all of them, so I killed them and worked from the held texts and the clause spans in the assembler instead.
- The `view` output prints dossier evidence ids and compressed `@eo:ref` records; `load_packet` without a view returns compressed objects, so the readable view is the only practical way to see clause spans.
- `load_packet` requires `pathlib.Path` arguments (a plain string raises a TypeError).
- Held later orders are not registered as ending or later-event evidence in the dossiers (the chain is empty), which forces a block whenever the true first end is a later held order (6513K, 6837, 6895, 6725A stay 2). This is a coverage gap in the dossiers, not a gap in the held corpus.

## What LOOKUPS.md missed

- It lists code-name mentions but does not say how a later order relates to the clause (replaces a paragraph versus adds to a code); I read each mentioning order myself. It does not show that EO 6743 changes EO 6725A's stays and report date, nor that EO 6955 extends the expiration date to June 16, 1935; I found those by reading the mentioning orders.
- It reported no hit for the neckwear and scarf code; a corpus search confirmed no record, so that was not a miss.
- Its own-text signals flagged "effective" in EO 6368 for the Printing-code supersession but did not note that the order creates a committee.

## Where the shared analysis did not fit

- Amendment orders that rewrite one paragraph of a code (6513K, 6837, 6895) are not covered by "amendments are later events": their own command is replaced word for word by the next amendment. I blocked them rather than claim June 14, 1935.
- Denials of exemption fit the analysis cleanly (EO 6403).
- Orders approving amendments with "modify my previous approval" (6922, 7014, 7016) are not addressed; I treated them as continuing approvals that end on repeal.
- A stay pending a contingent event with no held record of the event (6543M, 6725A) is not addressed; I blocked it under the owner ruling that known-within-an-interval differs from not-established.

## Tool-call count

About 55 tool calls (including reads, searches, edits, the apply and batch-check runs and background waits). No git state was changed. No files outside this packet were written, apart from scratch files in the session scratchpad.
