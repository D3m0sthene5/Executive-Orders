# Pothier: revising a doctrine after blind review

Two blind Opus reviewers checked a copy of your doctrine. **Each copy carried two planted errors** (a wrong citation and
a wrong date rule) that are not in your file; your assignment message lists them so you can ignore those findings.
Every other finding is about your real doctrine.

1. Read both reviews: `/home/claude/pothier-review/<ID>-A/REVIEW.json` and `/home/claude/pothier-review/<ID>-B/REVIEW.json`.
2. For every finding that is not a planted error, check it against the source yourself and either fix the doctrine
   (json and md) or, if you find the reviewer wrong, say why in NOTES.md with the evidence. Fix wrong member decisions
   the reviewers name, and look for others of the same kind.
3. `jobs/pothier/output/MEMBERS.jsonl` now carries Shepard and later-events edges, with any qualifier that confines an
   act to part of the order (tracts, sections, "in part", "in so far as") marked `partial_<mechanism>`. A held
   whole-order revocation that names a member by number (an executive order text, or a Public Land Order as BLM's
   official table states it) decides that member `no`, basis ACT, with the gap that the PLO text is not held where it
   is not. A `no` must never rest on a `partial_` edge.
4. Run `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/<ID>.json`. State the current contradiction
   count in the .md and explain every remaining flag (which member, which edge, why it does not change the lead).
5. Apply research/pothier/COORDINATOR_RULINGS.md P1-P8 throughout (P7 and P8 are new: abolition of the member's only
   subject; delegations of a statutory power that ceased, and periods a statute continued).
6. A revocation that takes effect only on a future event (filing of a resurvey plat, a notice by the Secretary) is not
   spent on its signing date: the lead is `open` unless the event's date is held.
7. The .md must stand alone: current findings and their basis, no "revised" labels, no change tables. Record what you
   changed and why in NOTES.md. Do not run git; write only your doctrine's files.

Reply with the new branch counts, the decided and open totals, the contradiction count, and any finding you rejected.
