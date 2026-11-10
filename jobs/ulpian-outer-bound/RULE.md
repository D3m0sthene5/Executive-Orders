# Ulpian life-bound lot for one-person orders, version 2 (DRAFT: not in force)

This text is what the owner approves or declines (Kean ask A-20261110-ulpian-outer-bound, part 1). `ulpian.py tag`
refuses to tag anything until a committed Kean decision and a committed owner-ruling file under
`research/readiness/owner_rulings/` both cite `ulpian-rule-sha256:` followed by the SHA-256 of this exact file
(`python -I jobs/ulpian-outer-bound/ulpian.py rule-sha`). Any edit to this file, the parameters included, changes the
hash and needs a new owner decision. Research, measurements and review: `research/ulpian/OUTER_BOUND.md`,
`research/ulpian/REVIEW.md`.

Version 1 also proposed a flat working-age floor of 14 years. The hostile review found it fatal (its source, the
age tables of 1883-1900, did not govern orders of 1907-1918, and it set aside the evidence rule), so version 2 has
no floor. Every bound here rests on a fact quoted from the order's own held text.

## The rule

**1. Class.** An executive order is in the lot when every one of these holds:

- the sole beneficiary of its command is one named natural person: a permission to appoint, reinstate, transfer,
  promote, retain, classify or employ that person in the federal civil, consular or diplomatic service, usually
  without regard to a civil-service rule or to an order governing such appointments (for example the consular order
  of June 27, 1906); other persons may be named in the text (a husband, a predecessor, the recommending official)
  but the command reaches no one else;
- it has one command: no second operative clause of another kind (a suspension, a reduction, a detail), no
  condition (a later test, a future vacancy, probation), and it does not confirm, approve or ratify another act;
- it does not amend, revoke or modify a rule, a schedule or another order; does not speak of a class, a list,
  "similar cases" or future persons; does not fill or classify a position as such; does not designate an officer to
  act in an office; does not rest on the labor regulations instead of the civil-service rules; and does not grant,
  pay or convey money, land or other property, or benefit an estate or heirs;
- its held text is the order's own (not a neighbour's slice, a disambiguation page or "text not located"), is not
  cut off mid-sentence and contains the person's surname; the order has an exact date and its year is legible in
  the held text (otherwise the order waits for a page check);
- a fact quoted from that text fixes when the person was alive or how old the person was (paragraph 2).

**2. Quoted facts that bound the life.** Only these, as Pothier PD-CS-ONE-PERSON M1 applies them:

- *alive on a date X*: the text says the person was appointed, employed, serving or working (in the Government or
  elsewhere, including stated experience) on or since X, or for a stated number of years ending on a stated date
  or, when no end date is stated, ending no later than the order date; then the person was born no later than X.
  By convention an "approximately" or "about" period is shortened by five years;
- *a stated age, or a stated age limit the person exceeds*: born no later than the order date minus that age;
- *an age bar the order waives*, stated with its figure in another held order (the postmaster examination's "sixty-fifth
  birthday" bar of EO 3455, 1921, as restated by EO 4538, 1926): born no later than the order date minus 64.

A position or title, "Mrs.", "widow of", "wife of", a reinstatement, a later order naming someone of the same name,
or an age limit without its figure fixes nothing. Facts come from Pothier PD-CS-ONE-PERSON Appendix A or from
`research/ulpian/READINGS.csv`; each counts only while its exact quote is still in the held text.

**3. Outer bound.** The person died no later than the birth bound plus **44,724 days**, the longest verified human
life (Jeanne Calment, 1875-02-21 to 1997-08-04, 122 years 164 days). This is an empirical premise, the record of
the longest documented life, not a legal maximum; a successful challenge to the record would only make every bound
earlier. A permission or exemption for one named person cannot operate after that person's death. When the bound
falls before the cutoff (October 14, 2026), the order's provisional status is **no** (not in operative force at the
cutoff), and its first end is the interval (order date, bound], `end_kind: not_later_than`, worded:

> Not in force by {bound} at the latest: the order's command reached only {person}, whose birth its text places no
> later than {born_by} ({quoted fact: alive on that date, or a stated age or age bar}), so that person died no
> later than {bound} (longest verified human life, 44,724 days). Whether and when the permission was used is
> unknown; if used, it was exhausted earlier, and any appointment or status it produced is an effect of that
> action, not the order's command.

**4. What the rule does not do.** It gives no exact end date and never says a permission was used. It never bounds
an order with a second operative clause, a class, a list, an office, property or money. It changes no
formal-validity column: an unrevoked order stays unrevoked on the books (D-20261106-justinian-r1). It does not adopt
the assessment that accrued effects survive independently (TR-CS-WAIVER `exceptions_savings`, not yet reviewed); it
only records that no such effect keeps the order's own command in force. It certifies nothing (certified stays 0)
and changes no codebook entry.

**5. Adoption.** Statuses under this rule are adopted only through the Respondendi standing adoption rule as the lot
below, with its audits, typed controls and owner report; this rule is not itself an adoption. A reviewer confirms
from the held text, for every order, the single beneficiary, the single command, the order date and the quoted fact.

## Parameters

```json
{
 "rule_id": "ulpian-life-bound/v2",
 "lot_id": "ulpian-life-bound",
 "life_days": 44724,
 "cutoff": "2026-10-14",
 "statuses_allowed": ["no"],
 "mechanism": "life_of_named_person",
 "end_kind": "not_later_than",
 "bases": ["pothier_B13_dated_fact", "pothier_B11_dated_fact", "pothier_B10_a_min_64", "ulpian_reading_dated_fact"],
 "end_wording": "Not in force by {bound} at the latest: the order's text places the named person's birth no later than {born_by} (quoted fact), so that person died no later than {bound} (longest verified human life, 44,724 days); use of the permission unknown.",
 "respondendi_lot": {
  "id": "ulpian-life-bound",
  "mechanisms": ["life_of_named_person"],
  "requires": ["research/ulpian/CLASS.csv row with tier quoted_fact and a bound before the cutoff",
               "claim end is not_later_than the Ulpian bound, never an exact date",
               "claim quotes the fact that fixes the birth bound and discloses 'use unknown'",
               "reviewer confirms from the held text: one beneficiary, one command, the order date, the quoted fact"],
  "control_kinds": ["second_person_hidden", "second_clause_hidden", "class_clause_hidden", "fact_about_another_person",
                    "wrong_order_text", "date_shift"],
  "status_control_kinds": ["second_person_hidden", "second_clause_hidden", "fact_about_another_person"]
 }
}
```
