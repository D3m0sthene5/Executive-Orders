# Ulpian: the outer bound for one-person executive orders

Named for Ulpian's life-expectancy table (Digest 35.2.68), the Roman jurist's rule for valuing a legacy that runs
for a person's life: a lifetime is a bounded interval. Research, measurements, review and the owner ask:
`research/ulpian/OUTER_BOUND.md` and `research/ulpian/REVIEW.md`; Kean ask **A-20261110-ulpian-outer-bound**.

A one-person order (a civil-service waiver, a reinstatement or retention authority, a retirement exemption) permits
one thing for one named person. It is exhausted when used and cannot operate after that person dies. The latest
possible death is (order date minus a minimum age `a_min`) plus 122 years 164 days, the longest verified human life.
When that falls before the cutoff (2026-10-14) the order was not in operative force at the cutoff; its first end is
the interval (order date, bound], and use of the permission stays unknown.

```
python -I jobs/ulpian-outer-bound/ulpian.py measure        # writes research/ulpian/CLASS.csv and MEASURE.json (about 3 s)
python -I jobs/ulpian-outer-bound/ulpian.py bound 1915-04-13 14
python -I jobs/ulpian-outer-bound/ulpian.py rule-sha       # the hash an owner approval must cite
python -I jobs/ulpian-outer-bound/ulpian.py tag [--write]  # refuses until the owner approves RULE.md
python -I jobs/ulpian-outer-bound/test_ulpian.py
```

**Inputs** (read, never written): `jobs/pothier/output/MEMBERS.jsonl` and `LEADS.jsonl` (PD-CS-ONE-PERSON branches),
`jobs/namier/output/NAME_LINKS.jsonl` (title-detected one-person orders), index titles through
`jobs/_lib/eo_identity.py`, the status ledger `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, and the
Jacquard L1 rows. `MEASURE.json` pins each input by SHA-256.

**Tiers.** `existing_quoted_fact` and `retirement_age_fact_title`: bounded under the rules already in force
(TR-CS-WAIVER, PD-CS-ONE-PERSON M1), so only an adoption route is missing. `floor_needed`: one named person, every
screen passed, but no quoted age; the draft rule's working-age floor would bound those dated before
`date_threshold(floor)`.

**The lock.** `tag` writes `research/ulpian/TAGS.jsonl` (proposals for the Respondendi lot `ulpian-life-bound`, never
statuses) only when a committed Kean decision and a committed owner-ruling file both cite
`ulpian-rule-sha256:<sha256 of RULE.md>`. No agent writes either; any edit to RULE.md changes the hash.

Zero tokens, standard library only. Changes no status, claim, codebook entry, census row or count; certified 0.
