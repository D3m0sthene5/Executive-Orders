# Pothier doctrine author brief (common to every family)

You are writing one **family doctrine** for the Executive-Orders project (repository root
`/home/claude/Executive-Orders`, branch `claude/pothier-family-doctrine`). The project traces the legal lifecycle of
every U.S. executive order from 1789 to the cutoff **2026-10-14**. 5,918 undecided orders, almost all from 1862-1936,
have no dated status history: the 1989 Office of the Federal Register disposition tables do not reach them and most
were never expressly revoked. The owner ruled on 2026-11-05 (`research/readiness/owner_rulings/2026-11-05-empty-status-history.md`)
that such an order may enter the claim kit with an explicit, noted empty history; its status must then rest on the
order's own terms and on law that applies to its whole class. Your job is to work out that law **once for your
family**, so a deterministic job can apply it to every member.

## What to deliver (only these paths; do not edit anything else in the repository)

1. `research/pothier/doctrines/<ID>.md`: the doctrine in plain English, **conclusions first** (what the doctrine
   decides for how many members and on what basis), then:
   (a) the legal mechanisms by which members end or persist: own terms, statute, later blanket instruments, review
   programs, life of a named person, class-wide events; for each, when it applies and how its date is fixed;
   (b) the exact primary sources that establish each mechanism (statute with Statutes at Large page, U.S. Code
   section, executive order number and Federal Register or compilation citation, case with U.S. Reports page),
   saying for each whether the project **holds** it (path and sha256) or how to **acquire** it (exact URL);
   (c) the decision procedure a machine can apply to each member from the fields we hold, branch by branch, each
   branch stating its provisional **status lead** (`no`, `yes`, `open`), its basis and its evidence gaps;
   (d) the members the procedure cannot decide, how many, and why.
2. `research/pothier/doctrines/<ID>.json`: the same procedure in machine form. Format and condition language:
   `research/pothier/DOCTRINE_SCHEMA.md`. Validate and measure it with
   `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/<ID>.json --hints` and iterate until the branch
   counts make sense. Report the final counts in the .md.
3. `research/pothier/work/<ID>/FETCH_PROPOSED.jsonl`: one line per primary source the doctrine needs that is not held,
   in the shape `{"instrument_id": null, "urls": ["https://..."], "citation": "...", "requested_by": "Pothier <ID> 2026-11-05", "note": "why"}`.
   Prefer govinfo.gov Statutes at Large PDFs (`https://www.govinfo.gov/content/pkg/STATUTE-<vol>/pdf/STATUTE-<vol>-Pg<page>.pdf`),
   govinfo U.S. Reports, govinfo Federal Register volumes (`https://www.govinfo.gov/content/pkg/FR-YYYY-MM-DD/pdf/...`),
   uscode.house.gov, ecfr.gov.
4. `research/pothier/work/<ID>/NOTES.md`: what you read (paths, URLs), what you tried and rejected, and your
   time and rough effort.

## Inputs

- Your members: `research/pothier/work/<ID>/MEMBERS.csv` (id, date, X1 type, WPA hint, text grade and path, held
  later-event edges, title, WPA 1944 summary). Full member records with features:
  `jobs/pothier/output/MEMBERS.jsonl` (filter by `x1_type`). Read a good number of real member texts (the
  `primary_text_path` files): the doctrine must fit the orders as they are, not as their labels suggest. Earlier
  work found X1 types broader than their labels (Kean F-20261031-jacquard-wave1): define branches by text features.
- Prior project work to reuse, not redo: the type rule(s) for your family in `research/readiness/type-rules/`
  (reviewed research patterns: ending pattern, required evidence, outlier conditions), the X1 event register
  `jobs/x1-class-engine/data/EVENTS.json` and `jobs/x1-class-engine/output/EVENT_SOURCES_STATE.json`, the Jacquard
  lot cards `research/excavator/jacquard-2026-10-31/LOT_RULES.md` and failures
  `research/excavator/jacquard-2026-10-31-w2/INDIVIDUAL_REVIEW.csv`, and
  `python3 -I jobs/kean/kean.py search <words>` for earlier results.
- Is a source held? `python3 -I jobs/pothier/held.py WORDS` (add `--text` to search text heads). A source counts as
  held only when its text file is in the repository and you have opened it and found the phrase you cite (`pin`).
- The web: you may use WebSearch and WebFetch to read primary sources and reliable secondary works (agency histories,
  law reviews) to find the mechanisms. The shell cannot reach the web. A source read only on the web is
  `held: false` with its exact URL: the job cannot rely on it until it is acquired, and every lead resting on it says
  so in its gaps automatically.

## Legal rules you must apply (owner decisions; non-negotiable)

- **Evidence decides** (D-20261028-evidence-decides): record what the evidence establishes, with the best supported
  date or interval. A claim that an order ended within an interval needs evidence that it ended; otherwise the order
  stays open on that question. Separate an exhausted command from surviving consequences. **A later general rule ends
  an order only if something shows it extinguished that order.** A savings clause, a continuation clause or a repeal
  of the *authority* (not of existing orders) is not an end. Disclosure keeps a gap visible but never fills it.
- **Absence is not evidence.** Not finding a revocation does not make an order in force. A `yes` lead needs a
  current-law predicate (`CURRENT`: a statute, regulation or official current record that shows the order or its
  operative effect in force on 2026-10-14). If no such predicate can be applied by the machine, the lead is `open`
  with the acquisition that would decide it.
- A `no` lead needs an ending basis that is the order's own terms (`TERM`: its stated period, condition, single act
  performed, its own fiscal year) or a later instrument or statute (`ACT`) that, by its terms, reaches this member.
  State the date rule (fixed date, order date, order date plus a stated period, or an interval) and the source.
- An order that only revokes, restores or amends another order is spent on issue as a command (its effect is evidence
  for the other order's lifecycle); say so where it applies.
- Leads are proposals for the owner. Write nothing that changes a status, the codebook, the census, the certified
  count (0), FETCH_QUEUE.jsonl or any other agent's files.

## Quality bar

- Every mechanism has a primary source with an exact citation. Never invent a citation, a Statutes at Large page, a
  date or a section number; if you cannot verify one, say "unverified" and keep the branch `open`.
- Prefer a smaller doctrine that is right to a larger one that guesses. Two blind reviewers will check your doctrine
  against the sources with planted errors; a branch that rests on an unverified claim will fail.
- The procedure must be machine-applicable with the fields listed in `DOCTRINE_SCHEMA.md`. If deciding a branch needs
  a field we do not hold, say which field and which source would supply it, and route those members to `open`.
- Write the .md for an intelligent reader without legal training: define terms of art at first use, full sentences,
  no filler.

When finished, reply with: the paths written, the branch counts from `try`, the number of members decided
(`no`/`yes`) and not decided, the sources held vs to acquire, and anything the coordinator must decide.
