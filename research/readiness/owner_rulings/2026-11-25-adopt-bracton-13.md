# Owner decision on the Bracton replacement proposals (2026-11-25)

The owner (Danny) answered Kean ask A-20261125-2 in the coordinating Claude session on 2026-11-25 (AskUserQuestion):
"Owner adopted all 13". Kean records the answer as decision D-20261125-adopt-bracton-13.

**Adopt as claims of record the 13 replacement proposals that both blind arms upheld:** EO 12376, 13101, 13148,
11812 and 12162, and the board orders EO 10032, 10056, 10071, 10112, 10140, 10757, 10872 and 11663. The reviewed
claims are in research/excavator/claude-bracton-2026-11-25/{c09-refresh,c10-refresh2,o0-refresh,o1-refresh,p02}/REPLACEMENT_PROPOSAL.jsonl.
Each replaces another agent's claim (Justinian's r3-retag claims, two Lambertini i06 claims and one codif-b4 claim),
so the claim kit could publish it only as a replacement proposal for owner acceptance.

Carrying the adoption out: `jobs/claim-kit/adopt_replacement.py` files the 13 reviewed lines canonically,
byte-identical, in a new claims file that sorts after every replaced claim's file, and writes an adoption receipt
naming this decision. The ledger statuses are unchanged (each claim's status equals the provisional ledger status),
so no status-adoption rows or population-contract entry are needed. These are AI-reviewed claims; human
certification is unchanged at 0.
