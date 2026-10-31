# Jacquard first wave, 2026-10-31: results

Six lots of pre-1937 orders without a provisional status were reviewed under the owner ruling of 2026-10-31
(`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`) against the rule cards in
`LOT_RULES.md`, which were written before any review. Twenty separate-context Claude reviewers (Sonnet 5.5), each
given one blinded batch, reviewed 325 items: 300 genuine orders and 25 planted errors (wrong-type intruders and
texts swapped under another order's header). **All 25 planted errors were caught**, so every batch is valid.

| Lot | Members | Mode | Reviewed | Upheld | Failed | Lot result |
|---|---:|---|---:|---:|---:|---|
| L1 one-person civil-service waivers, 1917 or earlier | 858 | sample of 59 | 59 | 48 | 11 | rejected as a lot |
| L2 one-person retirement exemptions | 49 | every order | 49 | 29 | 20 | individual |
| L3 closings and mourning | 60 | every order | 60 | 31 | 29 | individual |
| L4 NRA code approvals | 139 | sample of 59 | 59 | 26 | 33 | rejected as a lot |
| L5 Canal Zone orders | 223 | sample of 59 | 59 | 37 | 22 | rejected as a lot |
| L6 Philippine orders | 13 | every order | 13 | 3 | 10 | individual |

No lot passed the zero-miss test, so no unreviewed order is adopted. The **174 orders a reviewer upheld one by one**
(identity, fit, the lot's basis for NO, no outlier, an exact operative quote checked against the text) are
adopted individually as provisional NO statuses in `PROPOSED_STATUS_ROWS.csv`, appended to
`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` by the owner's merge of this pull request. The 126
failures, with reasons, are in `INDIVIDUAL_REVIEW.csv`.

**What the failures show.** They are real misfits, not reviewer noise: X1's types are broader than their labels.
The retirement-exemption type includes class-wide Retirement Act orders; the NRA type includes administrative,
staffing, spending and section 9(c) orders; the waiver type includes waivers for positions or several people; the
Canal Zone type includes Panama Railroad and defensive-sea-area orders; and compiled volumes sometimes supply a
neighbouring order's text. Many failed orders are probably still NO by another route, but this review does not
decide them. A future lot needs deterministic filters for those patterns (named single person, code or agreement
approval, Zone-only scope) and a fresh sample.

Files: `LOTS.csv`, `SAMPLES.json` (seeded), `packets/` (item lists as reviewers saw them; texts are copies of the held
repository texts), `CONTROL_KEY.json` (unblinding key), `reviews/`, `VERIFICATION.json`, `ACCEPTANCE.json`. Statuses
remain provisional AI status hypotheses; human-certified count 0.
