# Ulpian: hostile review and adjudication

**Reviewer:** Claude Fable 5.2, separate context, a different model from the author (Claude Opus 5.5). Same model
family, so this is not the different-family review some routes require; the Respondendi audits that adopt any
status supply that. The reviewer was given the files, not the author's conclusions. Its own text, unedited:
`research/ulpian/REVIEW_ARM_FABLE.md` (round 1 on v1; "Re-check of v2" on v2).

**Cost.** Round 1: 162,462 tokens, 16 tool calls, 304 s, 48 held order texts read. Round 2: 192,354 tokens
(cumulative context), 6 tool calls, 98 s, 50 held texts read. Coordinator (Opus 5.5): design, tool, measurement and
adjudication in this session; tokens not separately metered.

## Round 1 (v1, with a flat 14-year floor): verdicts and what changed

| | Objection | Verdict | Change |
|---|---|---|---|
| B | The 14-year floor is quoted from the 1883-1900 rules (EO 284, 307, 94, 128), but the orders it unlocks are 1907-1918, under EO 209 (1903), which left age limits to Commission regulations that are not held; the limits bound examinations, which these orders waive; veterans and R.S. 1754 claimants were exempt; some orders rest on the labor regulations; and the ask asks the owner for a method answer (ruling point 5) with disclosure standing in for evidence (point 4). | **Fatal: accepted.** | Floor withdrawn (RULE.md v2). The ask now recommends declining it. |
| B | The floor is not needed: the required age is order date minus 1904-05-02, 3-11 years for most early orders. | Accepted as a measure, not as a rule. | Per-order required age `r` in CLASS.csv (TR-CS-WAIVER already asks for "the smallest a_min"). Tier 2 is a reading list; no fact short of a dated presence or a stated age moves an order out of it. |
| D | Tier 1 bypassed the predicate: 65 of 99 Pothier life leads fail the tool's own tests (EO 162, 223, 226, 3432, 5896 wrong). "370 pass" was false. | **Must-fix: accepted.** | Every tier-1 row runs every gate; B09 and B12b excluded. 99 became 36. |
| D | 9 of 30 floor rows defective (EO 2002 no text, 1017 suspension clause, 776 ratification, 1892/2108 labor regulations, 2063/2793/2835 truncated, 1865 already datable). | Accepted. | New gates: text not located, second clause, ratifies or confirms, conditional, labor regulations, truncation. Each named row is now out, except EO 1865, which enters tier 1 by a recorded reading. |
| C | Second clauses and rule amendments: exclude, do not split; detection was insufficient. | Accepted. | Policy kept (exclude; an amending clause belongs to its parent under Pothier P2); detection added as above. |
| A | "Accrued effect of the action" is wrong for status orders (retirement exemption, classification) and ratifications; the accrued-effects assessment in TR-CS-WAIVER is unreviewed; money screen missed "with pay", "back pay". | Should-fix: accepted. | Lot narrowed to permissions (no retirement exemption is in it); ratifications excluded; RULE.md section 4 says the assessment is not adopted; money screen widened. |
| E | "Plus 122 years plus 164 days" is a day short for some spans; branch-level bounds stood in for per-order bounds; lifespan source not held. | Accepted. | Life counted as 44,724 days; per-member birth bounds from Pothier Appendix A; source stated as an empirical premise, not held (open gap). |
| F | "42 Jacquard L1 rows rest only on the premise" was a date test, not a reading. | Accepted. | Reworded; JACQUARD_L1.csv gives each row's required age and screen hits; part 3 of the ask is a reading-based correction. |
| G | Higher floors are worse; "waivers only" changes nothing; dangling references. | Accepted. | Alternatives reported with their counts; REVIEW.md and the Kean ask now exist. |

## Round 2 (v2): verdicts and what changed

The reviewer read all 40 then-tier-1 rows in full and found the lot **sound in substance**: one beneficiary and one
command in each, and the quoted fact concerns the beneficiary in each (checked where a husband's service is also
recited: EO 4379, 4541, 4906, 6058). No remaining conflict with the 2026-10-28 ruling for the lot.

| Objection | Verdict | Change |
|---|---|---|
| EO 2853 waives the consular order of June 27, 1906, not a civil-service rule. | Accepted as a wording point: the command still reaches one person. | Section 1 now covers the civil, consular and diplomatic service and orders governing appointments. Row kept. |
| EO 4541 (text "November 18, 1996", a death in 1928 in an order of 1926), EO 3096 and EO 4769: order date not legible. | Accepted. | New gate: the order's year must be legible in the held text. It holds those three, EO 4743 (OCR "1987") and six tier-2 rows, including EO 3872A, whose text says 1928 against the row's 1923. Tier 1: 37. |
| Section 2 required periods "ending on a stated date"; EO 1961, 3114, 3175, 4769 rest on periods ending at the order date or on non-Government experience; "approximately minus five years" is a convention. | Accepted. | Section 2 widened in terms (work or experience; periods ending no later than the order date) and the five-year cut called a convention. |
| Section 3 wording "shows alive on {born_by}" is false for age-based rows; retirement language and the B12 basis describe no row. | Accepted. | Wording now "places the birth no later than"; retirement language removed; B12 basis replaced by the reading basis. |
| EO 1865 fits section 2 but sits in tier 2. | Accepted. | `research/ulpian/READINGS.csv`: per-order facts with exact quotes, counted only while the quote is in the held text. EO 1865 is the first. |
| Tier 2 is a reading list, not a yield. | Accepted. | Reported as such; never counted as unlockable. |
| Nine sound leads lost to false screen hits or person parsing (EO 325, 1863, 1983, 2083, 2151, 2197, 3460, 4794, 5128). | Accepted as a cost. | Gates not loosened; listed for individual review (or a READINGS entry after a second read). |
| Lifespan source not held; Jacquard L1 not read per row. | Open. | Both are named as open work in the ask and the notes. |

## What the review did not change

- The class excludes rather than splits orders with a second clause: one living clause keeps the whole order open.
- Formal validity stays a separate column: an unrevoked order is still unrevoked.
- "Use unknown" stays open on every row; the lot never claims a permission was used.
