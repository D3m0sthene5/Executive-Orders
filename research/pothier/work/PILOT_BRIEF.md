# Pothier pilot: blind check of 30 status leads per doctrine

You are an independent reviewer. You did not write the doctrine or the leads. The repository is
`/home/claude/Executive-Orders` (read-only for you; write only your output file). Do not open
`/home/claude/pothier-sealed/` or `/home/claude/pothier-review/`, and do not use git.

The job `jobs/pothier` applied a family doctrine (`research/pothier/doctrines/<ID>.md` and `.json`; rules in
`research/pothier/COORDINATOR_RULINGS.md`) to every member and wrote one **status lead** per member: `no` (the order
ended before the cutoff 2026-10-14, basis TERM = its own terms or ACT = a later instrument), `yes` (in force on the
cutoff, basis CURRENT), or `open` (not decidable from the fields held). Your packet
`research/pothier/pilot/<ID>/PACKET.jsonl` holds about 32 leads: 30 drawn at random from the doctrine's members,
**plus a few deliberately falsified leads** that you must catch. Judge every record on the evidence, not on whether it
looks like the doctrine's output.

For each record, open the member's own held text (`member_texts`; the first is the one the engine read) and, where
the lead relies on one, the later instrument's held text or table row (`sources`, `later_edges`, and
`python3 -I jobs/pothier/held.py WORDS` to find held sources). Decide:

- **correct**: the order fits the branch, the lead and basis are supported, the date or interval is right, and the
  gaps are stated truthfully;
- **wrong_lead**: the status lead is wrong (a `no` without a sound ending basis, a `yes` without a current
  predicate, or an `open` that held evidence clearly decides; cite it);
- **wrong_date**: the lead is right but its date or interval is wrong;
- **wrong_branch**: the lead may be right but the order is not what the branch says (wrong type, another order's
  text, a second operative act);
- **gaps_misstated**: the lead is right but a material gap is missing or a stated gap is false.

Write `research/pothier/pilot/<ID>/PILOT_REVIEW.jsonl`, one line per record:
`{"pilot_id": "...", "instrument_id": "...", "verdict": "...", "evidence": "what you read (paths, quotes, dates)",
"correct_lead": "what the lead should be, if different"}`. Then reply with the count of each verdict and the pilot ids
you judged not correct, one line each.
