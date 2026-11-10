# Nalimov verification session

You verify claims that a script drafted. You do not research and you do not fix anything. For each entry you answer
**uphold** or **reject**, with defect codes and a short reason. Work only from `PACKET.json` in this folder. Do not
open any other file or folder, and do not use the network.

## What the packet holds

- `actors`: each acting instrument once. `text` is its held text, whole (`text_form: "whole"`) or as exact windows
  around each decisive sentence (`"windows"`). `decisive` lists, per target, the sentence the script relied on, with
  its sha256 and locator.
- `entries`: one per claim. Each names the order (`instrument_id`, `signing_date`), its held original (`original`),
  every clause of its held text with the state the script assigned (`clauses[].assigned`), the claim fields
  (`claim`: status, `whole_order_end` with date, actor, mechanism, quote and locator, savings, searches, checks),
  witnesses (`witnesses`: the OFR catalog note and any U.S. Code note), resolved flags (`resolved`), and every other
  held act on the order (`other_acts_on_order`).

Some entries are planted controls with a deliberate defect. You are not told which. Judge every entry on its own.

## Checklist (uphold only if every item holds)

1. **The end is in the actor's text.** The `whole_order_end.quote` appears in that actor's `text` (or a window), word
   for word apart from OCR noise and line breaks, and its sha256 matches the `decisive` sentence for this target.
2. **It names this order.** The quoted sentence prints this order's number as an executive order (not another
   number, not a range that skips it, not a state or agency order).
3. **It ends the whole order.** No qualifier in the sentence or its section: in part, so far as, insofar as,
   except, to the extent, with respect to, as it applies to, provided, subject to, until, suspend, reinstate. A
   section of the order revoked, or the order revoked "except" some part, is a partial end.
4. **The date follows.** `whole_order_end.date` is the actor's signing date unless the actor's text sets a later
   effective date or delay; every clause ended by the revocation carries the same date; nothing is dated before the
   order's own signing date.
5. **Nothing else acts on the order.** `other_acts_on_order` is empty, or every item in it is shown to be harmless.
   An amendment, partial revocation, suspension or continuation by another instrument that the claim leaves out is
   `later_event_omitted`.
6. **The clauses are this order's text, complete and correctly stated.** The clause texts belong to the order named
   (its subject, its date, its own number in the heading if shown). Every operative command is in a clause; a clause
   that holds another section's heading merges sections (`inventory_incomplete`). A clause that only revokes other
   orders is performed on signing (`task_completed`, dated the order's signing date); every standing command ends with
   the revocation (`express_revocation`). Report deadlines are not ends.
7. **No saving.** Nothing in the actor's text preserves what was done under, or continues anything from, this order.
8. **Witnesses agree.** The catalog note and any U.S. Code note name the same actor as ending the order; a witness
   that contradicts the claim is `witness_contradicts`.

(Items 1-8 come from `jobs/respondendi-adoption/UNDECIDED_CHECKLIST.md`, narrowed to the one kind this packet holds.)

## Defect codes

`wrong_end_date`, `actor_does_not_name_order`, `qualified_or_partial_end`, `later_event_omitted`,
`wrong_order_text`, `inventory_incomplete`, `clause_state_wrong`, `savings_missed`, `witness_contradicts`, `other`.

## Output

Write `VERDICTS.jsonl` in this folder: exactly one line per entry, in any order:

```json
{"entry_id": "E-...", "instrument_id": "EO:N", "verdict": "uphold", "defects": [], "reason": "one or two sentences"}
{"entry_id": "E-...", "instrument_id": "EO:N", "verdict": "reject", "defects": ["qualified_or_partial_end"], "reason": "..."}
```

A reject needs at least one defect code. Reply with one line when done: the number of entries, upheld and rejected.
