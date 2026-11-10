# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261110-ulpian-outer-bound (2026-11-10, Claude)

Ulpian outer bound for one-person orders (Track 3); three parts. (1) Approve as a Respondendi lot, adopted only with Respondendi's audits and typed controls: 'An order whose command reaches only one named natural person (a permission to appoint, reinstate, transfer, promote, retain, classify or employ that person), with one command, no condition, class, list, office, property or money, a clean held text and a legible date, and whose text places the person's birth no later than a date B (alive on a date, a stated age, or a stated age bar), was not in operative force at the 2026-10-14 cutoff when B plus 44,724 days (the longest verified human life, Jeanne Calment) falls before the cutoff; its first end is the interval (order date, B + 44,724 days], not_later_than, with use of the permission unknown.' Exact text: jobs/ulpian-outer-bound/RULE.md v2, ulpian-rule-sha256:57a95ba0c11e7207c27de317d7f522c24d05b9aedda91eea261ea2f9c0f64699. 37 orders qualify now (all civil-service waivers, 1913-1933, bounds 1986-2026). Recommended: yes. (2) A flat working-age floor (treat the person as at least 14 because the 1883-1900 Civil Service Rules set no entrance age below 14): recommended DECLINE. Alternatives: approve 14 for civil-service waivers only (20 more orders; a separate-context review found it fatal: the 1903 rules that governed these orders set no age table, the limits bound examinations these orders waive, and it would be a presumption in place of evidence); approve 18 or 21 (55 or 96 more; weaker still). (3) 42 of the 48 Jacquard L1 statuses you merged on 2026-10-31 rested on that 14-year premise: recommended, read each and keep those whose own text quotes a sufficient fact, returning the rest to undecided by a correction PR you merge; alternatives: ratify the premise (the same as approving the floor), or leave them.

*Why:* The life bound is already the rule (TR-CS-WAIVER, Pothier M1) but its 99 Pothier leads have no adoption route; Respondendi v1 covers only express revocations. Gated by a zero-token predicate (research/ulpian/CLASS.csv), 37 qualify. The adulthood floor the Track 3 framing named adds 20 at most and fails the evidence rule. Trade-off: an interval end ('not later than'), never a date; use stays open. Approving (1) records a decision citing the rule hash; ulpian.py tag refuses until then. Certified stays 0.

Sources: `jobs/ulpian-outer-bound/RULE.md`, `research/ulpian/OUTER_BOUND.md`, `research/ulpian/REVIEW.md`
