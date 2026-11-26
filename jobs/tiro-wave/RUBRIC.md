# Reviewer rubric for Tiro waves

Both blind arms of every Tiro wave apply this rubric, so the two arms judge each claim by the same standard and the
coordinator can tell a sinking defect from a note. It adds to the reviewer prompt; it does not replace the reviewer
brief, the claim schema or any owner ruling. Where a ruling and this rubric differ, the ruling governs.

## Verdicts

- **upheld**: every check in your prompt passed and no field of the claim, structured or prose, misstates what the
  held evidence shows. An upheld claim may carry notes.
- **rejected**: the claim has at least one sinking defect (below). List every sinking defect you found, not only the
  first.
- **upheld_after_reveal** (after-reveal step only): the genuine version of a planted control passes the same standard
  as a blind uphold. Do not uphold it because it is the genuine one.
- **Re-check verdicts** (fix-and-recheck step only): `upheld` means the flagged defect is fixed and the edited
  fields are supported by their cited sources; `rejected` means it is not, or the edit introduced a new defect in
  the edited fields.

## What sinks a claim and what is a note

A defect sinks the claim when any field states something the held evidence does not support. That includes prose:
wording that misstates evidence sinks the claim even when the structured fields are right. Examples: a wrong date,
actor, mechanism or state; a missed later event, amendment, revocation, supersession or held Federal Register or CFR
note; a quote that does not match the cited bytes; a source that does not say what it is cited for; a page label that
does not contain the cited span; a count or description in the prose that contradicts the claim's own records or the
sources; two fields of the claim that contradict each other.

A note does not sink the claim. Notes cover style, awkward but accurate wording, repetition, a better source where the
cited one already suffices, suggestions, unheld sources (below) and the open conventions (below). Write notes in the
record's `notes` list, never in `defects`.

## Unheld sources

An unheld source is a document you believe exists, or might exist, that the repository does not hold, so you cannot
read it. It is a note, not a verdict: write `UNHELD: <document> - <why it matters>` in `notes` so the coordinator can
route a source recovery. It can neither sink the claim nor support an uphold. Two cases still sink the claim: a held
source (for example a held "Revoked by" note) shows that the unheld document changed the order and the claim does not
address it; or the claim cites a source whose bytes are not held.

## Open conventions: not settled, record as a note

The owner has not settled the three questions below. Do not reject a claim for its answer to one of them. Record what
the claim did as a note that starts with `CONVENTION:`, naming the clause, so the coordinator can collect the cases for
the owner. A claim that has other sinking defects is still rejected for those.

1. A revocation that takes effect on signing (for example "Executive Order N is hereby revoked") recorded as an
   operative clause rather than as a command exhausted by performance on the signing date.
2. A one-time deadline whose performance no held source shows (for example "within 90 days ... shall recommend")
   closed as operative, rather than left open as an unresolved question.
3. A report cover date used where a transmittal letter date is readable. The board cover-date rule
   D-20261125-board-cover-date governs this case: it allows the clean report cover date, disclosed, when the
   transmittal date line is unreadable. Quote that rule in the note and say whether the letter date line is readable.

## Tagging each rejection

Every object in `defects` carries three tags besides the field and the exact problem:

- `class`, one of:
  - `date`: a date (end, later event, signing, checked-through) is wrong or unsupported.
  - `omission`: something the evidence records is missing (a later event, amendment, revocation, held note, clause).
  - `misdescription`: a clause or the order is described with the wrong operative effect, state, mechanism or actor,
    or prose misstates what happened.
  - `citation`: a cited source, quote or span does not support the statement it is cited for, or a needed citation
    is missing.
  - `page_label`: a page or item label does not contain the cited span.
  - `convention`: the claim breaks a settled owner rule or convention (name its decision id). The three open
    conventions above are notes, never this class.
  - `other`: anything else.
- `locality`:
  - `LOCAL` when the defect can be fixed by editing named fields of this claim without new research: the right value
    is already in the claim's cited sources or the packet's held evidence, and the fix changes no other clause's
    state, the clause inventory, `whole_order_status` or `whole_order_end`.
  - `STRUCTURAL` otherwise, including whenever you cannot name the fields a fix would edit.
- `fields`: the exact claim paths a fix would edit, written as `operative_clauses[<scope_id>].first_end.date`,
  `operative_clauses[<scope_id>].later_events[<actor>]`, `operative_clauses[<scope_id>].current_predicate.source`,
  `whole_order_end.date`, `research_rationale` and so on. Required for a LOCAL defect.

A LOCAL defect whose claim was upheld by the other arm can go through Tiro's fix-and-recheck route (README step 7a):
the producer fixes only that point, and you re-check only that point. Tag honestly; a defect tagged LOCAL that needs
more than its named fields will be refused by `repair-check` and sent back to both arms.
