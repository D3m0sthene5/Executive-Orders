# Producer report, packet n02 (NIRA code approvals), producer: Claude (Sonnet 5.5)

Start UTC: 2026-10-31T22:13:02Z
End UTC: 2026-10-31T22:26:56Z
Final applied directory: research/excavator/claude-apollo-2026-10-31/n02/packet/supp/applied-v1 (the packet is the supp folder; the decision sheets decisions.csv and clauses.csv in it were filled in place; the blank originals were kept outside the repository).

## Outcome per order

Submitted (15), each terminated by S.J. Res. 113 section 2 on 1935-06-14, with Schechter recorded as a validity characterization only:
- EO:6275 Cast Iron Soil Pipe: plain approval; later amendment (EO 6513, Dec 18, 1933) is a later event.
- EO:6312 Builders Supplies Trade: plain approval; EO 6885 (Oct 25, 1934) amends and continues the approval, not an end.
- EO:6313 Boot and Shoe: approval plus condition eliminating article IV (two clauses, both code content).
- EO:6350 Cap and Closure; EO:6378 Canning and Packing Machinery; EO:6395 Business Furniture; EO:6397 Buffing and Polishing Composition; EO:6543D Concrete Pipe; EO:6543H Coated Abrasives; EO:6647A Bowling and Billiard: plain approvals.
- EO:6398 Buff and Polishing Wheel: approval except section (n) of article VII (code content). The dossier's EO 6670 actor context is a number match to a 1930 order and was left out of the confirmations.
- EO:6502 Can Manufacturers: approval with two additions to the code text.
- EO:6539B Commercial and Breeder Hatchery: inventory corrected from five findings items to the one operative approval sentence (chars 1530-1831); order acts under Title I only.
- EO:6578 Construction Industry: plain approval; many later orders act under the code, none cancels it (EO 6925 moves cinders/scavenger construction work under it).
- EO:6965 Brewing amendment: approval of an amendment and modification of the earlier approval; EO 7019 (Apr 19, 1935) is a later amendment event.

Blocked (8):
- EO:6451, EO:6453: no text held (WPA title row only).
- EO:6452: only text rests on a Wayback-only APP capture (fails offline custody).
- EO:6543J: cancelled by EO 6925 on 1934-12-19 ("do hereby cancel my order approving said Code"), an earlier first end than the repeal. EO 6925 is not an evidence item in the packet and the supplement route refuses an already supplemented parent, so no end_id can cite it. Needs a fresh packet with a supplement excerpt of EO 6925.
- EO:6557B: stay of Article VII section 19(a) "pending further investigation and determination by the Administrator"; no held determination; repeal is only an upper bound.
- EO:6733A: report direction "six months after effective date of this Code"; effective date not held; a report date is a deadline, not an end.
- EO:6736: stays "pending my further order" (two), a ten-day stay of Rule 19, a hearing authorization before 1934-09-15; no held further order; single machine clause cannot carry separate ends.
- EO:6744B: items 1 and 4 end 1934-06-25 on their own terms, but items 2 and 3 are stays until a further order or satisfactory arrangements, with no held record.

## What took the time (one line per order)
- 6275, 6312, 6350, 6378, 6395, 6397, 6543D, 6543H, 6647A: reading the one-paragraph text and confirming no later cancellation; template reuse.
- 6312, 6578, 6965: reading later amending orders (6885, 6925/6731 and others, 7019) to decide amendment versus end.
- 6313, 6398, 6502: deciding that the conditions and exceptions are code content, not independent commands; 6398 also checking the EO 6670 number match.
- 6539B: locating the operative sentence and computing the corrected inventory span.
- 6543J: finding EO 6925, which the lookup missed, and working out that the packet cannot cite it.
- 6451, 6453, 6452: confirming no usable text or custody.
- 6557B, 6733A, 6736, 6744B: deciding whether open stays and report directions have a supportable end; blocked after weighing the owner ruling of 2026-10-28.

## batch-check counts
packet members 23; claims checked 15; strict pass 15; strict fail 0; blocked 8; actionable failures none; actual claim checker: 15 all checks passed, 0 unverified, 0 failed, network downloads disabled. apply: 15 assembled_proposal, 8 blocked, 41 s. Only applied-v1 was needed.

## Tool defects
- apply and batch-check write nothing to stdout until they finish and each took roughly one to several minutes of wall time while other producers ran on the same machine; a progress line would help.
- The dossier's actor context for EO:6398 links an unrelated order (EO 6670) by number match; the blank sheet carried it into working_text confirmations.
- The blank sheet listed Cotton custody copies (cd-job texts) as extra working_text confirmations for six orders; only the registered text is cited, so I kept only that entry.

## What LOOKUPS.md missed
- EO:6543J: its code-name search reported zero mentions because EO 6925 spells the trade name "Cinders, Ashes and Scavenger Trade" without the comma, and so missed the cancellation, the one earlier end in the packet. Code-name matching should ignore punctuation (I used a normalized scan of all held order texts to check every code).
- Number-citation hits for 6398, 6578 and 6965 are different instruments (1930 order, Public Land Orders); the lookup does not say so.
- It did not flag the EO:6539B inventory problem (findings items listed as operative clauses) or the stays and report direction in 6557B, 6733A, 6736, 6744B beyond own-text signals.

## Where the shared analysis did not fit
- It decides code approvals, stays and exemptions together, but not a stay that is "pending further order" or a report direction that runs from an unheld effective date; I blocked those orders rather than use the repeal date as a default end (owner ruling 2026-10-28, rule 3).
- It says nothing about a cancellation under the code's own article (EO 6925 for 6543J); the earlier-end rule in the brief covered it, but the packet had no way to cite the cancelling order.
- Whether S.J. Res. 113's proviso narrowed the section 5 exemption for past action stays open, as the shared analysis says; the savings text says so.

## Tool-call count
About 40 tool calls (reads, searches, one generator script, apply, batch-check, and waiting on background jobs).
