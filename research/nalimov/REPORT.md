# Nalimov tablebase, 2026-11-10: script-completed claims, verification packets, cost per adopted status

Owner Tier A plan, ideas 1-3: generate then verify; batch by acting instrument; dependency order. Coordinator:
Claude Opus 5.5. Tool: `jobs/nalimov-tablebase/`. Data: origin/main 854514831e job outputs (claim-kit generation
2026-11-10T10:36Z), read-only. No model was run on any order, nothing was filed, adopted or certified. Human-certified: 0.

## Result in one paragraph

A script can complete, on main today, **13 of 720** undecided orders that have an express named whole revocation, and
**9** of those pass the kit's own assembler, `check_claim` and **every step of the actual claim checker** with no model
at all (EO 8616, 10779, 11056, 11232, 11274, 11352, 11361, 12737, 13765). The other kinds give 0 today: amendment-only
children wait for the kit's OWN_TEXT route (F5, PR #274) and their parents are all open; own-terms orders reach 0 under
Respondendi's predicate; decided orders give 0 of 2,732 (mostly no ACT record or no acceptable original). A verification
packet is about **4.9k tokens per claim** (32% of the frozen EVIDENCE.json alone, under 1% of the ~751k context per
attempted order on the full route). Projected worker cost per adopted status is **about $0.17 (range $0.10-0.42)
against $7.71 measured** on the full route, 18-80x lower. The pool is the limit, not the unit cost: 9 orders now; the
census names what unlocks more (official copies of revoking orders, the F7 segmenter fix, a drafter tier for recorded
amendments). The calibration run is prepared and Augur refuses it only for the missing independent plan review.

## 1. Fully scriptable orders per kind (zero tokens, on main)

`research/nalimov/census/CENSUS.json`, `CENSUS.csv` (one row per order looked at), `BLOCKER_GROUPS.json`,
`research/nalimov/PRESCREEN.json`.

| Kind | Candidates | Drafted complete | Pass kit assembler + every checker step | What blocks the rest |
|---|---:|---:|---:|---|
| Express named revocation (undecided) | 720 (an ACT passing Respondendi's sentence predicate) | 13 | **9** | below |
| Decided NO orders with no ready claim | 2,732 | 0 | 0 | 1,275 hold no qualifying ACT; 1,272 no acceptable original; 75 page checks; 31 ending source only a transcription |
| Amendment-only children (Pothier P2, undecided) | 601 | 0 | 0 | no OWN_TEXT / PARENT_END records on main (F5, PR #274); every named parent is undecided (EO 209: 267 children, EO 89: 53); 279 leads name no parent |
| Own terms (undecided) | 196 dated whole-scope terms | 0 | 0 | Respondendi's own-terms predicate reaches 0; extension and later-act checks need a held negative search |

Express kind, first blocker of the 707 not complete: ending source is a transcription 150; original not acceptable 113;
another instrument acts 104; own term needs reading 48; several ending actors 45; missing item 35; effective wording
unparsed 32; page check owed 23. Orders blocked by **one group only** (what one fix would unlock): another act on the
order 45, inventory (segmenter) 32, a held file missing from the data checkout 15, effective date 6, own terms 5.
Pre-screen failures among the 13: EO 10940 (quotes not found in the cited PDF), EO 11245, 13575, 13805 (checker
passes with unverified quotes: clause fragments too short to verify).

Batching by acting instrument is real but small at this tier: the 9 orders have 7 actors (EO 11437 ends 11232, 11352
and 11361 in one sentence). Selden's 16,322 pairs over 5,579 actors include large revokers, but their targets mostly
carry one of the blockers above. Dependency order is built (`packets.topological`) and becomes active when the
amendment-only kind opens.

## 2. What the drafter writes and how it is checked

For each complete order the drafter fills exactly what a Maudslay producer writes: one `decisions.csv` row, its
`clauses.csv` rows, `RATIONALES.json`, and `STATUS_DECISION.json` (status NO, basis the ACT record and the actor text).
Each clause is either a standing command ending with the order (`express_revocation` or `express_supersession` from the
provision's verb) or a pure revocation of other orders performed on signing (`task_completed`). The kit's
`_decision_errors` returns nothing on every complete draft; `prescreen.py` assembles each claim with the kit's own
assembler on the experimental dossier and runs the actual checker.

Replay on Papinian's 90 frozen undecided dossiers (the full route's own evidence): the drafter completes EO 11957 and
EO 12348, both adopted by the owner after full review, and **its drafts equal the reviewed claims clause for clause**
(state, date, mechanism, source), including EO 12348 Sec. 8, a revocation performed on signing. EO 9245 (also adopted)
is now refused: its only clause transfers functions, which the script will not type.

## 3. Packets versus the current dossier

`research/nalimov/MEASURES.json`, measured on real frozen evidence of the 9 orders: 2 sessions, 4 planted controls,
44k tokens of packet in all, **4.9k tokens per genuine claim** (controls and actor texts included) against 15.2k tokens
for the frozen EVIDENCE.json alone (ratio 0.32) and about 751k tokens of context per attempted order on the full route
(Bentham PLAN.md). A packet entry carries the claim fields, every clause's held text with its assigned state, the order's
own text outside the clauses, every held act on the order, every catalog entry and U.S. Code note, and resolved flags;
each actor's held text is sent once per session.

## 4. Verification and controls

Two blind arms (A, B) and a status-only reader (S, Respondendi's independent status reviewer, distinct from both arms),
each a fresh folder outside the repository holding only a prompt and its packet. The sealed key sits in a separate
folder outside the repository and the scratch tree. Controls: at least 2 per session and one per 15 claims, two kinds,
one status-determining; mutations (`date_shift`, `ending_source_swapped`, `wrong_order_text`, `partial_as_whole`)
are planted in a session that does not hold their genuine twin, with the actor text edited consistently; decoys (real
refused orders drafted with one blocker ignored) when the census supplies them (none at this tier). `packets.tells`
refuses any session with a mechanical giveaway. The batch stops on any missed control, any arm whose run receipt shows a
blinding violation, a non-zero exit or no result, and a status reader that accepts a status-determining control.
`install` writes only upheld, byte-identical drafts into a still-unworked packet, atomically, with a receipt.

## 5. Independent review

Claude Fable 5.2 reviewed v1 (commit ff831fdea4): changes required, 7 blocking findings, all real, all fixed in v2:
clause classifier defeated by OCR spacing, active voice and commas (11 of 36 drafts); inventory passing an order whose
text lay outside its only clause (EO 8455); ending provisions cited from transcriptions (12 of 36; the kit's assembler
rejects them); a savings scan that missed EO 9691's "Nothing in this order shall be construed to affect reemployment
rights heretofore acquired"; mechanical control tells (duplicate order ids, a field only decoys filled); blinding
receipts ignored by scoring and the key one relative path away; `install` overwriting worked members, half-writing on
failure and not bound to what was verified. Non-blocking findings fixed: catalog entries other than the witness, wider
delayed-effect forms, same-actor non-ending acts, witness date against the actor's date (EO 10014), actor text required,
own terms by allow-list, conflict texts shown in the packet, mechanism from the verb, the status reader in the stop rule,
usage counted once, the "no confident operative boundary" missing line. The review is
`side-session-notes/.../nalimov/REVIEW.md` (outside the repository); its findings are summarized here.

## 6. Cost per adopted status

Measured on the full route (Papinian, 2026-11-10, workers only): $0.51 per attempted order, $7.71 per adopted status.

Projected for Nalimov (`research/nalimov/project.py`, `PROJECTION.json`): verifier sessions priced at list (A Sonnet 5.5,
B Opus 5.5, S Sonnet 5.5) from the measured packet sizes, with stated assumptions for turns, output per entry,
after-reveal reviews, coordinator time and the upheld rate:

| Case | Worker tokens per claim | Worker $ per claim | $ per adopted status | vs $7.71 |
|---|---:|---:|---:|---:|
| low (2 turns, 95% upheld) | 54k | 0.08 | 0.10 | 80x lower |
| mid (3 turns, 80% upheld) | 79k | 0.11 | 0.17 | 45x lower |
| high (6 turns, 60% upheld) | 162k | 0.17 | 0.42 | 18x lower |

Not included on either side: Respondendi's cross-family audits (every member while a stratum is on probation) and owner
time. These are projections; the calibration run is the measurement.

## 7. Calibration run (not run)

`research/nalimov/calibration/WAVE.json`: stage 0, one lane, the 9 pre-screened orders, action
`status_assignment.undecided` (all 9 in Bentham's stratum), configuration `nalimov-tablebase|anthropic|nalimov-script`,
budget 600k units, five pre-mortem entries, all six lessons Augur pushed answered. `augur.py check` refuses only for:
"review must be bound to this plan" (plan sha256 `b77fd9a64e90fa0185d2b9c7c034629ab4d6ff13e1ea56c03c96bac3a27af128`).
Augur needs a reviewer of another model family or the owner; the owner's signature was requested through the
coordinating session. Forecast by Bentham's undecided rate: 0.9 filed for $2.99; the Nalimov projection is about 7
upheld for about $1.

## 8. What would unlock more orders (ranked by the census)

1. **Official copies of revoking orders.** 150 express orders are blocked first because every held copy of the ending
   provision is a transcription (219 carry the blocker at all). Fetching the GovInfo FR printings of those actors is an
   acquisition with no model cost.
2. **Segmenter fix (Accursius F7).** 32 orders are blocked by the inventory alone; 503 carry an inventory blocker.
3. **A drafter tier for recorded amendments.** 45 are blocked only because another instrument amends the order; when
   the amending provision names sections that map to clause labels, a script could write the later events.
4. **F5 (own-text route)** opens the 601 amendment-only children, in dependency order after their parents.
5. **F6 (working texts)** for the 113 whose own original is not acceptable.

## Files

- `jobs/nalimov-tablebase/`: `drafter.py`, `census.py`, `prescreen.py`, `packets.py`, `verify.py`, `nalimov.py`,
  `predicate.py` (Respondendi's predicate, vendored with a parity test), prompts, README, 41 tests.
- `research/nalimov/`: `census/CENSUS.json`, `CENSUS.csv`, `BLOCKER_GROUPS.json`, `PRESCREEN.json`, `MEASURES.json`,
  `project.py`, `PROJECTION.json`, `calibration/WAVE.json`, this report.
