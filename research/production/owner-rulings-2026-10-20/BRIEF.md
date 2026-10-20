# Owner rulings brief: three method questions (2026-10-20)

For Danny. This brief decides nothing, writes no claims, and changes no codebook, status or count.
Certified whole-lifecycle count: **0**. All counts below are AI hypotheses taken from the files cited.

## Counts at a glance

| Question | Option | Orders claimable now | Committed claims to re-check |
|---|---|---|---|
| 1. Report deadline | A (ends on report) | 64 (63 core + 1 extra) | up to 17 claim lines in 10 files |
| | B (ends report + 30 days) | 64, minus LMRA boards; RLA boards only | same 17 lines, plus EO 12581 |
| | C (only EO 12553 ends it) | 97 (88 core + 9 extra); 98 if EO 10449 is covered | 0 |
| 2. Strike-and-insert | A (struck item ends) | 4 | 28 "continues" clauses in 11 orders |
| | B (continues, amended) | 3 | 43 "ends" clauses in 26 orders |
| | C (continues only if verbatim/renaming) | 3 | about 71 clauses, one by one |
| 3. Unnamed-instrument ends | A (only naming ends) | 15 (11 clean; 4 also need Q2) | 0 |
| | B (unnamed ends if it displaces the whole subject, source held) | up to 11 after a per-order finding (7 clean) | 6 claims |
| | C (EO 12553 end + disclosed earlier candidate) | 15 (11 clean), each flagged for human review | 6 claims get a flag, end dates unchanged |

## 1. Report deadline

**Question.** An emergency-board order says the board "shall report ... within thirty days"; when does the order first stop operating?

- **A.** On the date the board made its report.
- **B.** When the RLA sec. 10 standstill ends, 30 days after the report (does not fit LMRA boards of inquiry).
- **C.** Only on express revocation by EO 12553 (1986-02-25); the report and standstill are spent facts, not ends.
  This matches the existing line in `jobs/claim-kit/AGENT_PROTOCOL.md` step 3, "A report deadline is never an end", which you have not confirmed for this case.

**Orders claimable now** (from Pullman's 98 packets: 89 core EO 12553 targets plus 9 extras):
- C: 88 core (89 minus EO 10449, a board that was never constituted) plus 9 extras = 97. EO 10449 runs only if the ruling covers it.
- A or B: 63 core + 1 extra `staged_complete` = 64. Then 8 need a reviewer or page check (EO 10045, 10109, 10874, 10811, 11040, 11042, 10286, 10509), and 25 (17 core + 8 extra) need a report source first. 9 of the 17 are LMRA boards, which B does not fit.
- A or B also need sub-rulings: which date is "made its report"; what ends a never-constituted board; whether missed or extended deadlines matter. 52 of 70 core report dates fall after the order's own deadline, and most extension papers are not held.
- Also waiting: 25 Lamm III report-relative sunsets and EO 9691 (two clauses, R9830 scale); Tycho counted 47 orders depending on this ruling.

**Committed claims to re-check under A or B.** A grep of tracked `research/readiness/claims/` finds 17 claim lines in 10 files that say a report deadline or duty is not an end (for example EO 8467 sec. 7(c) in R9830). Most are recurring report duties that A or B, as worded for boards, would not reach; each still needs a look. Under C: none.

**Evidence.** `research/excavator/pullman-2026-10-20/README.md` and `PACKETS.jsonl`; `research/production/day-review-2026-10-20/RERANK-evening.md` (Tycho, Lamm III).

## 2. Strike-and-insert

**Question.** When a later order strikes an item and inserts replacement text, does the struck clause end then, or continue amended until the parent ends?

- **A.** The struck item ends on the amendment's date; the replacement belongs to the amending order.
- **B.** It continues, amended; the amendment is a `later_event`.
- **C.** It continues only if the new text is verbatim or only renumbers, repunctuates or renames the same office; otherwise it ends as in A.

**Orders claimable now** (from Blackstone's `AFFECTED.jsonl`, 7 rows):
- A: 4 (EO 14052, 11898, 11908, 12581).
- B: 3 (EO 14052, 11898, 11908); EO 12581 joins only if the report-deadline ruling goes the C way.
- C: 3 (EO 14052, 11908, 12581); EO 11898 needs a same-office finding first.
- Under every option EO 11877 and 11983 stay blocked by other commands, and EO 11927 needs re-production.

**Committed claims are already split, so some re-checking is unavoidable.** A scan of tracked claim files found 43 clauses in 26 orders treated as **ending** (codif-b0, b4, b7, i06, i08, rastell-c01, bowditch-y2-02) and 28 clauses in 11 orders treated as **continuing** (codif-b4, b5, i05, i08, iv01, p1, rastell-c01). A re-checks the 28, B re-checks the 43, C re-checks both lists (about 71), though most already fit C. The plainest conflict: "amended to read" rewrites continue in i05 (EO 10204, 10821) but end in codif-b7 and i06.

**Evidence.** `research/excavator/blackstone-2026-10-20/README.md` and `AFFECTED.jsonl`; precedent `research/readiness/claims/claude-lambertini-i08-2026-10-20.jsonl`.

## 3. Unnamed-instrument ends

**Question.** Does a statute or order that does not name the target (EO 12287 oil decontrol, EO 10804 sec. 2 host-order revocation with savings, a whole-text restatement such as EO 12189, the Tax Reform Act of 1976, the Housing and Community Development Act of 1974) end it before the order that names it (EO 12553, EO 9830)?

- **A.** Only express naming ends an order. EO 12553 is the end; earlier unnamed events are recorded as `later_events` or context.
- **B.** An unnamed instrument ends the order when it clearly displaces the order's whole subject matter and its source is held.
- **C.** Record EO 12553 as the end and the unnamed event as a disclosed earlier upper-bound candidate for human review.

**Blocked orders: 19** (counted from the R12553NB probe and the s1-s6 `ACT_REVIEW.jsonl` lines that cite the open method question):

| Group | Orders | Unnamed lead |
|---|---|---|
| ACT upheld, lead held (11) | EO 9949, 10103, 11138 | EO 10804 sec. 2 / EO 11552 (host-order revocation, savings) |
| | EO 12140, 12189, 12209 | EO 12287 decontrol |
| | EO 12153, 12187, 12186 | whole-text restatement (EO 12189 / 12209) plus EO 12287 |
| | EO 12376, 12398 | EO 12415 end of the parent commission; EO 12429 restatement; EO 12534 parent revocation |
| ACT upheld, lead not held (4) | EO 10328 | Selective Service regulations |
| | EO 11206, 11213 | Tax Reform Act 1976 sec. 1202 |
| | EO 11237 (open-space limbs only) | Housing and Community Development Act 1974 |
| No upheld ACT record yet (4) | EO 12257, 12263, 12297 (s5, `owner_method_question_nonexpress_end`); EO 11284 (probe) | JTPA 1982; tin and coffee agreements expiring; DOPMA 1980 |

Related, not counted: R9830 orders with unheld statutory leads that are also blocked by inventory or D6 gaps (EO 8083, 8705, 9027).

**Orders claimable now.**
- A: the 15 orders with an upheld ACT record. 4 of them (EO 12153, 12187, 12186, 12398) also turn on whole-text restatement, which overlaps Question 2, so 11 are clean. The other 4 need an ACT re-review before claims.
- B: up to the 11 held-lead orders, each only after a reviewer finds whole-subject displacement (7 clean of Question 2). The 8 unheld-lead orders wait for fetches.
- C: same as A (15, 11 clean), and every claim carries the earlier-candidate flag.

**Committed claims to re-check under B** (each sets aside a named-nothing lead): EO 8427 (Postal Reorganization Act 1970), 11307 (Rural Development Act 1972), 11422 (CETA 1973) in `claude-r12553nb-{01,s2}`; EO 8423, 8425, 8894 (War Service Regulations overlay) in `claude-r9830-{s1,s2}`. Under C these 6 get a disclosure flag only. Under A: none.

**Evidence.** `research/excavator/rastell-2026-10-20/r12553nb/REPORT.md`, `OUTCOME.json`, `s1`-`s6/ACT_REVIEW.jsonl`, `review/`; `r12553nbs/OUTCOME.json`; `r9830/review/REVIEW.jsonl`, `r9830/s1`-`s3/ACT_REVIEW.jsonl`.

## Other pending owner asks (from `HANDOFF/notes-claude.md`)

1. Adopt the 56 NO proposals (Bowditch 15, Sinclair 41) by batch pull request?
2. Transcription-as-copy: is a compiled transcription an acceptable copy? (Lamm retirement exemptions wait on it.)
3. Lamm "further exempt" and "until" readings: EO 8554, 8392, 8828, 8058, 7300, 6933.
4. Send the drafted NYU bulk-ProQuest access request (`ACCESS_REQUESTS.md`)?

## If you only decide one thing

Recommendation, not a decision: rule on the report deadline first. Under any option it opens the most orders (64 now under A or B, 97 under C, against at most 15 for unnamed-instrument ends and 4 for strike-and-insert).
