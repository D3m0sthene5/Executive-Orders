# Nalimov status review

You are the independent status reviewer for claims a script drafted. Two other reviewers check the full claims; you
check only the status. Work only from `PACKET.json` in this folder. Do not open any other file or folder, and do not
use the network.

Every entry proposes status **NO** on the 2026-10-14 cutoff: the order was ended in whole by the acting instrument
named in `claim.whole_order_end.actor`, on `claim.whole_order_end.date`. Some entries are planted controls with a
deliberate defect; judge every entry on its own.

Accept the status only if all of these hold:

1. The quoted sentence (`claim.whole_order_end.quote`) is in that actor's held text in `actors` (whole text or a
   window), and it prints this order's number as an executive order.
2. It ends the whole order: no qualifier (in part, so far as, insofar as, except, to the extent, with respect to, as it
   applies, provided, subject to, until, suspend, reinstate) in the sentence or its section.
3. The actor was signed after the order (`signing_date`), and the end date is the actor's signing date unless its text
   sets a later effective date.
4. Nothing in `other_acts_on_order`, the witnesses or the resolved flags shows the order continued, revived or ended
   only in part.
5. The order's clause texts are this order's text (its subject and number), so the status is about the right order.

Write `VERDICTS.jsonl` in this folder, one line per entry:

```json
{"entry_id": "E-...", "instrument_id": "EO:N", "status_verdict": "accept", "reason": "one or two sentences"}
{"entry_id": "E-...", "instrument_id": "EO:N", "status_verdict": "reject", "reason": "..."}
```

Reply with one line when done: the number of entries, accepted and rejected.
