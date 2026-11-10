# Ulpian: an outer bound for one-person executive orders (Track 3)

Claude (Opus 5.5), 2026-11-10, session Ulpian, branch `claude/ulpian-outer-bound`. Named for Ulpian's
life-expectancy table (Digest 35.2.68), the Roman rule for valuing a legacy that runs for a person's life.

**Deliverable:** a design and a drafted owner ask (Kean **A-20261110-ulpian-outer-bound**), not an adoption. Nothing
here changes a status, claim, codebook entry or count; human-certified stays 0.

| File | What it is |
|---|---|
| `jobs/ulpian-outer-bound/RULE.md` | the exact text the owner would approve (v2, hash-locked), with the Respondendi lot slot `ulpian-life-bound` |
| `jobs/ulpian-outer-bound/ulpian.py` | zero-token predicate (`measure`), bound arithmetic (`bound`), tagger (`tag`, refuses until the owner approves); 27 tests |
| `research/ulpian/READINGS.csv` | facts read by hand that Pothier's appendix lacks, each anchored by its exact quote (1 so far: EO 1865) |
| `research/ulpian/CLASS.csv` | one row per candidate: gate, tier, basis, birth bound, death bound, required age |
| `research/ulpian/MEASURE.json` | the counts below, with pinned inputs |
| `research/ulpian/JACQUARD_L1.csv` | the 48 owner-merged Jacquard L1 statuses: required age and screen hits |
| `research/ulpian/REVIEW.md`, `REVIEW_ARM_FABLE.md` | the hostile review, its re-check of v2, and what changed |

## 1. What the measurement shows

1. **The latest-possible-death bound is already in force.** TR-CS-WAIVER (reviewed R5-R7 under
   D-20261028-evidence-decides) and Pothier PD-CS-ONE-PERSON M1 compute it from a quoted fact only, and Pothier
   applied it to 99 leads, all still undecided. An "outer bound" rule therefore adds nothing legal for those orders;
   what they lack is an **adoption route**. Run through every gate in this file, 36 of them qualify, plus one fact
   the review found that Pothier missed (EO 1865): a lot of **37**.
2. **The new part the Track 3 framing named, adulthood shown by the order, does not hold up.** A flat working-age
   floor of 14 (v1 of this design) would have bounded 20 more orders (55 at 18, 96 at 21). The hostile review found
   it fatal, and I agree (section 5): the held age tables are from 1883-1900 and the orders are from 1907-1918, under
   the 1903 rules, which left age limits to Commission regulations that are not held; the limits bound examinations,
   which these orders waive; and the floor would be disclosure standing in for evidence. **Version 2 has no floor.**
3. **The useful number per order is the required age r**, the smallest age on the order date that puts the bound
   before the cutoff (order date minus 1904-05-02, rounded up). For the 233 one-person orders without a quoted fact
   it runs from 4 to 33 years: 7 need 10 or less, 20 need 14 or less. Tier 2 is a reading list, not a yield. An
   order leaves it only when a reading quotes a fact that shows the person alive before 1904-05-03 (EO 1865: "served
   four and one-half years ... resigning on August 9, 1907", which Pothier's B13 list missed and which now sits in
   `research/ulpian/READINGS.csv`) or states an age; that is ordinary claim research under the rules in force, not
   something to ask the owner. No rule lets anything less (a title, a marriage, a job) exclude an age below r.
4. **42 of the 48 Jacquard L1 statuses the owner merged on 2026-10-31 need a person older than 0 on the order date**
   (required ages 1 to 14), and the L1 card's stated basis for all of them was "anyone the federal service could
   employ in 1917 or earlier was at least 14 years old", which Pothier later declined and this review found
   unsourced for these dates. That count is a date test, not a reading: the reviewer found quoted facts in several
   (EO 1918 consul "from October 1, 1885"; EO 2648 "as early as 1899"). 11 hit a screen (EO 2070 was a messenger boy
   from 1908); 3 have no exact date. They need a reading, not a bulk decision.

## 2. Where the proposal sits against each ruling

| Ruling | What it says (short) | The proposal (v2) |
|---|---|---|
| **D-20261028-evidence-decides** (pinned) | Record what the evidence establishes, with the best date or interval; "within an interval" needs evidence that it happened; disclosure never fills a gap; do not route method questions to the owner. | **Applies it.** The death within (order date, bound] is shown by a fact in the order (the person alive on a date, or of a stated age) plus the record of the longest documented life. Use of a permission is never claimed and stays open. The v1 floor would have **narrowed** point 2 and asked the owner for a method answer (point 5); it is withdrawn. The ask is only about an adoption route and a correction, which are the owner's to give. |
| **TR-CS-WAIVER** | `a_min` = 0 unless a quoted fact fixes it; a position or title alone fixes no adult age; state the smallest `a_min` that would put the bound before the cutoff. | **Applies it unchanged.** The required age r in CLASS.csv is that "smallest a_min". |
| **F-20261028-6** (waiver research) | CSC reports never record use; no general rewrite ends a waiver; the latest possible death bounds the end only on a quoted age fact. | **Applies it.** |
| **F-20261028-11 (Namier)** | A name match is a lead, not an identity. | Used only to find post-1936 candidates by title (none enters the lot: their held texts are not linked) and to warn that a later order naming the person may give an earlier end. Never used for identity. |
| **D-20261021-unnamed-instruments** (partly superseded by D-20261106-justinian-r3) | An instrument not naming the target does not end it. | **Not engaged.** The end is the death of the one person the command reaches, not an instrument; no statute or general order is used as an end. |
| **D-20261021-report-deadline**, "functionally spent" (superseded where it conflicts by D-20261106-justinian-r3; D-20261108-board-rule) | A board ended on express revocation, with the report date as a "functionally spent" note; later, a board command ends on completion of its task. | **Consistent with the current reading.** The 2026-10-21 reasoning ("why would there be a cleanup order?") does not reach these orders: no later order cleans up one-person waivers (EO 7916, 8743, 9830 and 10577 list none). As with the board rule, the command ends when its object is gone. Formal validity (unrevoked on the books) stays a separate column under D-20261106-justinian-r1. |
| **D-20261031-jacquard** and its L1 lot | Sampled class adoption of provisional NO; L1's card used the 14-year premise. | The L1 premise is **not** used and should stop being cited; part 3 of the ask is the correction. |
| **A-20261106-pothier** (answered 2026-11-09) | Doctrines adopted as first-step guidance; sampled adoption of a family's `no` leads is a later ask. | Part 1 of the ask is that later ask, for the life-of-person leads, narrowed by every gate here. |
| **Respondendi v1** (PR #270, draft) | Only express named revocations; every other end kind needs its own lot and rule. | The lot slot `ulpian-life-bound` (RULE.md parameters `respondendi_lot`) is that lot, for Respondendi v2 to reference. |

## 3. The bound and its sources

**Longest human life: 44,724 days (122 years 164 days).** Jeanne Calment, born 1875-02-21 in Arles, died 1997-08-04;
listed by Guinness World Records and the Gerontology Research Group (Pothier S1, read on the web, not held). The bound
is an empirical premise, not a legal maximum. Read on the web 2026-11-10 and not held: a 2018-19 challenge (Zak, that
the decedent was her daughter Yvonne) was rejected by Calment's validators and, per LongeviQuest, by its Global
Validation Commission in 2023; if the challenge were right the record would fall to about 119 years, which only makes
every bound earlier. The Social Security Administration's life tables (Actuarial Study 120 and later) end at age 119.
Counting in days matters: "plus 122 years plus 164 days" gives 44,723 or 44,725 days depending on leap years, so the
tool adds 44,724 days to the birth bound (`test_ulpian.py`; Pothier's year arithmetic can differ by one day, which
changes no status).

**What fixes the birth bound** (Pothier M1, unchanged): a dated presence (born no later than that date), a stated age
or exceeded age limit with its figure (order date minus that age), or the postmaster examination's 65th-birthday bar
(order date minus 64). Nothing else: not a title, "Mrs.", "widow of", a reinstatement, or an age limit without a
figure. When no fact is quoted, the order stays open and CLASS.csv gives its required age.

**Why not a working-age floor** (v1, withdrawn). The held Civil Service Rules do set a lowest entrance age of 14
(EO 284, 1883, and EO 307, 1884: postal "junior assistants, who must not be under 14 years of age"; EO 94, 1897, and
EO 128, 1900: "Page, messenger boy, apprentice ... or student, 14-20"; other departmental positions 20). But EO 209
(1903) replaced those rules and left age limits to Commission regulation; the limits governed admission to
examination, which these orders waive; veterans and R.S. 1754 preference claimants were exempt from them; and some
orders rest on the labor regulations, outside the rules altogether. A floor from those texts would be a presumption,
which the owner's ruling does not allow as evidence.

**Interval end and wording.** bound = birth bound + 44,724 days; status `no` only when bound < 2026-10-14; first end
(order date, bound], `end_kind: not_later_than`, wording in RULE.md section 3; never an exact date. For a permission,
"use unknown"; for a retirement exemption, it ended with separation or death, whichever came first.

## 4. The class, the predicate and the measurement (main at 854514831e)

**Candidates (1,178 undecided):** the 1,015 undecided Pothier PD-CS-ONE-PERSON members (X1 `cs_waiver_individual`,
`personnel_designation`, `patent_signing_designation`, `retirement_exemption`) and 163 undecided title-detected
one-person orders from Namier. `ulpian.py measure` takes about 3 seconds and no tokens.

**Gates, in order** (the first that fails keeps the order out):

1. undecided in `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`;
2. Pothier branch: out if B09 (retirement lists), B12b (Commission narrative, no command), B20 (held text not the
   order's), B21, B22, B04, B25, B27, B26 (possible minors), B23 (designation to an office), B24 (patent signer), or
   decided by another mechanism (own terms, express revocation, amendment); B10, B11, B12, B13 are tier 1; B99 is tier 2;
3. exact order date; exactly one parsed person; held text of at least 80 characters;
4. screens on the held text: text not located; several persons; rule or order amended; confirms, approves or
   ratifies; second clause (suspension, reduction); conditional (subject to, when a vacancy, probation); labor
   regulations; general or continuing; position not person; property, money or estate (estate, heirs, annuity,
   lands, back pay, with pay, be paid); office designation; and, for tier 2 only, age mentioned and possible minor
   (tier 1 rests on an age fact, so those words are expected there);
5. the person's surname in the held text; the held text not cut off mid-sentence (it ends with sentence punctuation,
   a signature, the White House line or the printed order number); the order's year legible in the held text;
6. tier 1: a birth bound from Pothier's branch (B10 minus 64, B12 minus 0), from Appendix A (B11, B13), or from
   `research/ulpian/READINGS.csv` (each reading counts only while its exact quote is in the held text), and a death
   bound before the cutoff.

**Counts.**

| | Orders |
|---|---:|
| Candidates (undecided) | 1,178 |
| Pass gates 1-5 (one person, one command, clean text, legible date) | **270** |
| **Tier 1, the lot: bounded on a quoted fact before the cutoff** | **37** (33 dated presence, 3 stated age, 1 postmaster age bar; all waivers; dated 1913-12-05 to 1933-03-01; bounds 1986-07-27 to 2026-03-10) |
| Tier 2, required-age reading list (no quoted fact yet) | 233 (r from 4 to 33; 7 need 10 or less, 20 need 14 or less) |
| Post-1936 retirement exemptions by title, held text not linked | 25 (1937-1948; would be bounded 1998-2010 at Pothier B09's minimum age 61 once each text is read) |
| A flat floor would have reached (withdrawn) | 20 at 14, 29 at 16, 55 at 18, 96 at 21 |

Of the 99 Pothier life-of-person leads, 36 pass; the rest fail on person count (32, mostly no parsed name), Pothier
branch B09 or B12b (9), no exact date (5), several persons (6), an amendment, money, second clause or condition (6),
the year not legible in the held text (4: EO 3096, 4541, 4743, 4769, held for a page check) or surname (1). The
reviewer read nine of the excluded leads as sound (EO 325, 1863, 1983, 2083, 2151, 2197, 3460, 4794, 5128); they
fail on person parsing or a false screen hit and are left for individual review rather than loosening the gates.

**Kept out (908 undecided).** No single parsed person 185; post-1936 titles without an age fact 120; designations
to an office 74 (B23) plus 17 by screen; held text not the order's 73 (B20); class or rule instruments 65 (B22) plus
16 amendments by screen; other family 44 (B21); decided by another mechanism 42; possible minors 21 (B26) plus 40 by
screen; no exact date 31; age mentioned without a figure 30; lists 25 (B27) plus 15 by screen; retirement titles
needing their text 25; patent signers 16; year not legible in the held text 10 (EO 3872A's text says 1928, its row
1923); position not person 9; property or money 8; truncated 5; conditional 5;
surname 5; retirement lists 5 (B09); special rules 5 (B04); Commission narratives 4 (B12b); labor regulations 4;
retirement class orders 3 (B25); second clause 2; other 4.

**Predicate failure modes (what a zero-token predicate gets wrong, and which way).**

- *Hidden second person* (EO 226 "Mrs. Annie M. West and Mrs. Sadie B. Yates ... respectively", parsed as one): the
  several-persons screen catches "and Mrs.", "respectively", "they"; a list without those words would pass. Lot control
  `second_person_hidden`.
- *A quoted fact about another person* (a husband's or father's service): Pothier rejected these by reading; the lot
  reviewer must confirm the fact concerns the beneficiary. Control `fact_about_another_person`.
- *Neighbour text* (Commission-report slices; EO 3432 holds two orders): the person-count and surname gates catch
  some; a slice holding both orders can pass. Control `wrong_order_text`.
- *Second clause or general clause* (EO 1017 suspension; EO 679 "In similar cases ..."): screened; other wordings can
  pass. Controls `second_clause_hidden`, `class_clause_hidden`.
- *Truncated slices* (EO 2063, 2793, 2835): the end test catches a slice that stops mid-sentence but not one cut at a
  sentence end.
- *Over-exclusion* is common and safe: "they", "persons", "age", "designated", "subject to" hit innocent texts. Those
  orders stay open; nothing is decided by a screen.
- *Dates*: member dates come from the WPA list or index; held texts sometimes lack the day (EO 776). The lot reviewer
  confirms the order date in the held text (control `date_shift`); the tool already refuses a row whose year is not
  legible in its text; tier-1 margins are at least 7 months (latest bound 2026-03-10, EO 2165).

## 5. Hostile review

`research/ulpian/REVIEW.md` records the review (Fable 5.2, separate context), my adjudication of each point and the
changes. Main objections: the floor was unsourced for the orders' dates and asked the owner for a method answer
(fatal, accepted: floor withdrawn); tier 1 bypassed the predicate and two thirds of it failed the rule's own tests
(accepted: gated; 99 became 36, plus EO 1865 by reading); missing gates for second clauses, ratification, conditions and truncation (accepted:
added); the Jacquard "42" was a date test (accepted: reworded; reading required); year-plus-day arithmetic a day short
(accepted: days); the wording was wrong for retirement exemptions and ratifying orders (accepted: reworded; ratifying
orders excluded).

## 6. The ask

Kean **A-20261110-ulpian-outer-bound** (full text in `HANDOFF/KEAN_ASKS.md`):

1. Approve `jobs/ulpian-outer-bound/RULE.md` v2 (the lot `ulpian-life-bound`, 37 orders now, quoted facts only) as a
   Respondendi lot, adopted only with its audits and controls. **Recommended.**
2. The working-age floor: **decline (recommended)**; or approve 14 for civil-service waivers only (20 more orders; the
   review found it fatal; "waivers only" changes nothing, since all are waivers); or 18 or 21 (55 or 96; weaker still).
3. The 42 Jacquard L1 statuses: **read each and keep those whose text quotes a sufficient fact, returning the rest to
   undecided by a correction pull request the owner merges (recommended)**; or ratify the L1 premise (the same as
   approving the floor); or leave them, which keeps an unsourced basis in the ledger.

Trade-off for part 1: an interval end ("not later than 2026-03-10"), not a date, and "use unknown" stays open; in
return, 37 orders can get a provisional status on evidence already held, and every later reading that finds a dated
fact adds to the lot at no new legal cost.
