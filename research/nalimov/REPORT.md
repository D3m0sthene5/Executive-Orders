# Nalimov tablebase, 2026-11-10: script-completed claims, verification packets, cost per adopted status

Owner Tier A plan, ideas 1-3: generate then verify; batch by acting instrument; dependency order. Coordinator:
Claude Opus 5.5. Code: `jobs/nalimov-tablebase/` and the Maudslay conveyor's new producer route
(`jobs/maudslay-conveyor/conveyor.py --producer nalimov --controls typed`). Data: origin/main 854514831e job outputs
(claim-kit generation 2026-11-10T10:36Z), read-only. No model was run on any order. Nothing was filed, adopted or
certified. Human-certified: 0.

## Result in one paragraph

On main today a script can complete **12 of 720** undecided orders that have an express named whole revocation.
**8** of those pass the kit's own assembler, `check_claim` and **every step of the actual claim checker** without any
model: EO 10779, 11056, 11232, 11274, 11352, 11361, 12737 and 13765. Every other kind gives 0 today:
- amendment-only children wait for the kit's OWN_TEXT route (F5, PR #274), and all their parents are open;
- own-terms orders reach 0 under Respondendi's predicate;
- decided orders give 0 of 2,732.

A verification packet is about **4.8k tokens per claim**. That is 32% of the frozen EVIDENCE.json alone and under 1%
of the ~751k context per attempted order on the full route. Projected worker cost per adopted status is **about
$0.17, in a range of $0.10-0.42**. The full route measured **$7.71**, so this is 18-80x lower. The limit is the pool,
not the unit cost: 8 orders today. The census names what would unlock more:
- official copies of the revoking orders;
- the F7 segmenter fix;
- a drafter tier for recorded amendments.

The calibration plan is ready. Augur refuses it only because the independent plan review is missing.

## 1. Fully scriptable orders per kind (zero tokens, on main)

`research/nalimov/census/CENSUS.json`, `CENSUS.csv` (one row per order looked at), `BLOCKER_GROUPS.json`,
`research/nalimov/PRESCREEN.json`.

| Kind | Candidates | Drafted complete | Pass kit assembler + every checker step | What blocks the rest |
|---|---:|---:|---:|---|
| Express named revocation (undecided) | 720 (an ACT passing Respondendi's sentence predicate) | 12 | **8** | below |
| Decided NO orders with no ready claim | 2,732 | 0 | 0 | 1,275 hold no qualifying ACT; 1,272 have no acceptable original; 75 need page checks; 31 have only a transcription of the ending source |
| Amendment-only children (Pothier P2, undecided) | 601 | 0 | 0 | no OWN_TEXT / PARENT_END records on main (F5, PR #274); every named parent is undecided (EO 209: 267 children, EO 89: 53); 279 leads name no parent |
| Own terms (undecided) | 196 dated whole-scope terms | 0 | 0 | Respondendi's own-terms predicate reaches 0; the extension and later-act checks need a held negative search |

**First blocker** for the express orders not complete:

| First blocker | Orders |
|---|---:|
| Ending source held only as a transcription | 150 |
| Original not acceptable | 113 |
| Another instrument acts on the order | 104 |
| Own term needs reading | 48 |
| Several ending actors | 45 |
| Missing item | 37 |
| Effective wording unparsed | 32 |
| Page check owed | 23 |

**Blocked by one group only** (what a single fix would unlock):

| Blocker group | Orders |
|---|---:|
| Another act on the order | 45 |
| Inventory (segmenter) | 32 |
| A held file missing from the data checkout | 15 |

Pre-screen failures among the 12 drafts:
- EO 10940: quotes not found in the cited PDF.
- EO 11245, 13575, 13805: the checker passes them, but with unverified quotes (clause fragments too short to verify).

Batching by acting instrument is real but small at this tier. The 8 orders have 6 actors; EO 11437 ends 11232, 11352
and 11361 in one sentence. Selden's 16,322 pairs over 5,579 actors include large revokers, but their targets mostly
carry one of the blockers above. Dependency order is built (`packets.topological`). It becomes active when the
amendment-only kind opens.

## 1a. Reach tally: dozens or thousands?

`research/nalimov/tally.py` → `TALLY.json` maps each blocker on each order to what removes it:
- an Accursius fix (F3 #272, F4 #275, F6 #276, F7 #273; F5 #274 opens only the amendment-only kind);
- sources: an acquisition, such as official copies, page images or files missing from the data checkout (Linnaeus);
- a new drafter tier: a reading the current script refuses on purpose;
- another kind of order.

An order counts as unlocked at a level only when every one of its blockers is removed at that level. These are upper
bounds, and each fix is assumed to remove its blockers everywhere it applies.

| Scriptable if... | Express named revocation (720 undecided candidates) | Decided NO, no ready claim (2,730) |
|---|---:|---:|
| today | 12 (8 pass every checker step) | 0 |
| Accursius F3-F7 merged | at most 19 | 0 |
| plus sources (official copies of ending orders, page checks, missing files) | at most 41 | 0 |
| plus new drafter tiers | at most 719 | at most 720 |
| plus other kinds | 720 | 2,730 |

**Answer: F3-F7 and sources move this route from about a dozen orders to a few dozen, not thousands.** Thousands
come only from drafter tiers that turn producer readings into script rules.

Orders needing each tier, express kind:

| Drafter tier | What the script would have to do | Orders |
|---|---|---:|
| one-time commands | date the performance of transfers, appointments and abolitions; Pothier P1 already answers part of this | 412 |
| recorded amendments | map an amending provision to clause labels | 236 |
| read an unlocated acting text | decide whether a held text that names the order acts on it | 229 |
| read current-law notes | read U.S. Code and eCFR notes, once F3 makes them held text | 218 |
| second witness | find a second witness for orders before EO 7532 | 215 |
| own terms before the end | handle an own term that ends before the revocation | 203 |
| delayed effect | handle delayed or dated effectiveness | 156 |

Each tier is a legal reading. It needs the same treatment v1 got: an independent review, a replay against adopted
claims, and probably an owner ruling.

Decided orders, what they hold instead:

| Held evidence | Orders | What it would take |
|---|---:|---|
| no later instrument and no ending own term | 1,483 | not scriptable from held evidence |
| own terms only | 526 | a different kind |
| a named whole act that fails the sentence test | 288 | |
| partial acts only | 288 | |

1,272 decided orders also lack an acceptable original. The tally counts those under F6.

**Re-measuring on a local build with F3-F7 applied was not cheap.** The five branches all change claim-kit compiler
files (`build.py`, `status_overlay.py`, `current_evidence.py`, `excavate.py`), and two of them are still in review. A
merged build is a 15-30 minute, 1.6 GB kit compile after resolving their overlaps. The tally above is the proxy. The
real figure comes from rerunning `census.py` on main after each fix merges.

## 1b. One-question tiers (measured, not built)

This is the coordinator's direction after the calibration. The script does everything it can for an order, then
narrows what is left to single legal questions. Each question comes with a small packet: the decisive held text and
the field the answer fills. One model answer fills the field, and the claim then goes through the conveyor's ordinary
review.

The figures are from `research/nalimov/tiers.py` → `TIERS.json`, on the 693 blocked express candidates whose evidence
froze. All are upper bounds. Cost assumes one Sonnet 5.5 answer per question, plus the mid-case verification ($0.109
per claim) and the coordinator, at 80% upheld.

| Tier, in build order | Question | Orders with it | Questions | Packet tokens (median) | Unlocked with F3-F7 | $ per adopted status |
|---|---|---:|---:|---:|---:|---:|
| one-time commands | was this one-time command performed, and when, per this held text? | 412 | 1,811 | 786 | 27 | 0.20 |
| recorded amendments | does this held amending provision leave the order whole, and which clause does it change? | 236 | 448 | 945 | 1 | 0.19 |
| current-law notes (after F3) | does this held U.S. Code / eCFR text state the order in force or ended? | 218 | 1,462 | 919 | 6 | 0.21 |
| unlocated acting texts (after F4) | does this held text of another order act on this one, and how? | 229 | 472 | 1,301 | 5 | 0.19 |
| own terms before the end | did this own term end the clause before the revocation? | 203 | 675 | 816 | 5 | 0.19 |
| delayed effect | when did the revoking provision take effect? | 156 | 156 | 798 | 7 | 0.18 |

A tier alone unlocks few orders, because most blocked orders need several. Cumulative, with F3-F7:

| Tiers built so far | Orders unlocked (cumulative) |
|---|---:|
| one-time commands | 34 |
| + recorded amendments | 44 |
| + current-law notes | 72 |
| + unlocated acting texts | 106 |
| + own terms before the end | 149 |
| + delayed effect | **189** |

That is about 201 of 720 express orders with today's 12, at 18-21 cents per adopted status against $7.71, roughly
40x lower.

What stops the rest, after all six tiers:
- sources (270);
- a second witness before EO 7532 (215). That needs a source or a Respondendi rule change, not a reading;
- history flags (87) and savings (82);
- smaller groups.

Pothier P1 covers almost none of the 412 one-time-command orders: 395 have no Pothier lead. Pothier covers orders with
no dated history; these all have a revoking act. The one-time question still needs no new ruling. The 2026-10-28
evidence-decides ruling already separates an exhausted command from its surviving consequences, and it requires
evidence that the performance happened: an unrecorded performance stays open. Any question whose answer would need a
doctrine the rulings do not give becomes a Kean ask, never a guess.

Acquisition lists for Linnaeus:
- `ACQUISITION_DECIDED_NO_LATER_INSTRUMENT.csv`: 1,483 decided orders whose dossier holds no later instrument or
  ending term (962 of them before EO 7532).
- `ACQUISITION_OFFICIAL_COPIES_OF_ENDING_ORDERS.csv`: 180 acting orders whose official copy would unblock 219 express
  orders in part.

## 2. What the drafter writes and how it is checked

For each complete order, the drafter fills exactly what a Maudslay producer writes:
- one `decisions.csv` row;
- its `clauses.csv` rows;
- `RATIONALES.json`;
- `STATUS_DECISION.json`: status NO, with the ACT record and the actor text as its basis.

Each clause is one of two kinds:
- a standing command, statement or definition, which ends with the order (`express_revocation` or
  `express_supersession`, from the provision's verb);
- a pure revocation of other orders, performed on signing (`task_completed`).

The checks run in this order:
1. The kit's `_decision_errors` returns nothing on every complete draft.
2. `prescreen.py` assembles each claim with the kit's own assembler on the experimental dossier and runs the actual
   checker.
3. In the conveyor route, the kit's `apply` and `batch-check` run again, unchanged.

Replay on Papinian's 90 frozen undecided dossiers (the full route's own evidence): the drafter completes EO 11957 and
EO 12348. The owner adopted both after full review, and **the drafts equal the reviewed claims clause for clause**
(state, date, mechanism, source). That includes EO 12348 Sec. 8, a revocation performed on signing. EO 9245 (also
adopted) is refused: its only clause transfers functions, which the script will not type.

## 3. Packets versus the current dossier

`research/nalimov/MEASURES.json`, measured on the real frozen evidence of the 8 orders:

| Measure | Value |
|---|---:|
| Sessions | 2 |
| Planted controls | 4 |
| Packet tokens per genuine claim (controls and actor texts included) | **4.8k** |
| Frozen EVIDENCE.json alone, per order | 14.9k (ratio 0.32) |
| Context per attempted order on the full route (Bentham PLAN.md) | about 751k |

A packet entry carries:
- the claim fields;
- every clause's held text, with its assigned state;
- the order's own text outside the clauses;
- every held act on the order;
- every catalog entry and U.S. Code note;
- the resolved flags.

Each actor's held text is sent once per session.

## 4. Verification, controls and the conveyor

Whitworth I4: the drafter is a producer route inside the Maudslay conveyor (`--producer nalimov`).
- **Producer stage:** `Batch.draft_round` writes each order's producer folder from the packet's own frozen evidence,
  at zero tokens. An order the drafter refuses stays unresolved with its blocker, and gets no repair rounds.
- **Later stages:** `kit.py apply`, `batch-check`, plant, blind review, controls, reveal, agree and `complete` are
  unchanged.
- **Typed plants (`--controls typed`, the default for this route):** date shift, later event removed, partial end
  presented as whole, wrong order's text, and swapped ending source.
  - Each plant has its own catch terms.
  - Each review set gets at least 2 plants of 2 kinds, at least one of them status-determining.
  - The planted version replaces its genuine twin in the set.
- **Measures (I6):** `MEASURES.json` reports tokens and dollars per stage. The stages are draft, blind review,
  reveal, repair and adjudication (adjudication marked unmeasured). Dollars are at the
  `jobs/necker-costs/PRICES.json` list prices, per filed claim and per adopted status. The adopted figure stays null
  until Respondendi or the owner adopts.
- **Tests:** the 66 existing conveyor tests pass, and the new route and the typed plants have tests in
  `test_nalimov.py`.

**Gap for undecided orders:** the conveyor has no status-overlay stage. For undecided members, `kit.py apply` returns
`awaiting_status_review` and the conveyor stops at "zero claims assembled". All 8 scriptable orders are undecided, so
the calibration run needs an overlay stage first:
1. an independent status reviewer writes `STATUS_REVIEW.json`;
2. `overlay-propose` runs with the lifecycle sheet;
3. the working claims go into the existing plant → review → complete `--replacement-proposal` path.

The coordinator was told; this is the next piece of work.

The standalone path (`packets.py`, `verify.py`) remains for actor-batched packets and hand-run agents:
- two blind arms and a status-only reader;
- a key folder outside the workers' tree;
- `packets.tells()` refuses any session with a mechanical giveaway;
- the batch stops on a missed control, an invalid arm or a status-reader miss;
- `install` writes only upheld, byte-identical drafts into a still-unworked packet, atomically, with a receipt.

## 5. Independent review

Claude Fable 5.2 reviewed v1 (ff831fdea4). The verdict was changes required, with **7 blocking findings**. All were
real and all are fixed in v2 (28d32adcf7):
1. The clause classifier was defeated by OCR letter-spacing, active voice and commas (11 of 36 drafts).
2. The inventory check passed an order whose text lay outside its only clause (EO 8455).
3. Ending provisions were cited from transcriptions (12 of 36); the kit's assembler rejects these.
4. The savings scan missed EO 9691's reemployment-rights saving.
5. Planted controls had mechanical tells.
6. Blinding receipts were ignored, and the key was one relative path away.
7. `install` could overwrite worked members, half-write, and was not bound to the verified draft.

The re-review of v2 found 2 small blocking findings, both fixed in v3:
- a short first sentence was being removed as if it were a heading;
- "revokeion" appeared in `scope_check`.

The re-review confirmed every v1 fix. Its spot-checks found all 8 pre-screened orders (and EO 8616) correct on
status, actor, end date and clause states against the held text. It noted three points a verifier may raise:
- EO 13243 misdates EO 11274; the number governs;
- EO 14009 sec. 4(b) mentions actions "arising from" EO 13765, which the reviewer did not judge a saving;
- an OCR'd signature date on EO 11232's original.

Non-blocking findings acted on:
- the "no confident operative boundary" waiver (this also drops EO 8616, whose segmentation caution is another form);
- "go into effect";
- "existing regulations shall remain in force".

Still open (non-blocking):
- No decoy survives the stricter drafter, so measured sessions carry only mutation controls.
- Hand-run arms have no tool-call blinding scan.
- A timed-out worker in the standalone runner needs a receipt.

The review is in `side-session-notes/.../nalimov/REVIEW.md` (outside the repository).

## 6. Cost per adopted status

Measured on the full route (Papinian, 2026-11-10, workers only): $0.51 per attempted order, $7.71 per adopted status.

Projected for Nalimov (`research/nalimov/project.py`, `PROJECTION.json`). The verifier sessions are priced at list
(A Sonnet 5.5, B Opus 5.5, S Sonnet 5.5) from the measured packet sizes. The assumptions stated for each case are the
number of turns, output per entry, after-reveal reviews, coordinator time and the upheld rate.

| Case | Worker tokens per claim | Worker $ per claim | $ per adopted status | vs $7.71 |
|---|---:|---:|---:|---:|
| low (2 turns, 95% upheld) | 54k | 0.08 | 0.10 | 80x lower |
| mid (3 turns, 80% upheld) | 78k | 0.11 | 0.17 | 44x lower |
| high (6 turns, 60% upheld) | 161k | 0.17 | 0.42 | 18x lower |

The registered forecast (Whitworth) allows at most $1.00 per filed claim and per adopted status; all three cases are
under it. Two costs are excluded from both routes: Respondendi's cross-family audits (every member while a stratum is
on probation) and owner time. These figures are projections. The calibration run is the measurement.

## 7. Calibration run (not run)

`research/nalimov/calibration/WAVE.json`:
- stage 0, one lane, the 8 pre-screened orders;
- action `status_assignment.undecided`, with all 8 in Bentham's stratum;
- configuration `maudslay-conveyor|anthropic|nalimov-script`;
- budget of 600k units;
- five pre-mortem entries;
- all seven lessons Augur pushed are answered, including this route's own review lesson.

`augur.py check` refuses for one reason only: "review must be bound to this plan" (plan sha256
`6f03cb4309720c7543517d5858eaf61ccfe98862828f9930b0ba5b42c4b0f7f6`). Augur needs a reviewer of another model family,
or the owner. The run also needs the conveyor's overlay stage (section 4).

## 8. What would unlock more orders (ranked by the census)

1. **Official copies of revoking orders.** 150 express orders are blocked first because every held copy of the ending
   provision is a transcription. Fetching the GovInfo FR printings of those acting orders is an acquisition with no
   model cost.
2. **Segmenter fix (Accursius F7).** 32 orders are blocked by the inventory alone.
3. **A drafter tier for recorded amendments.** 45 orders are blocked only because another instrument amends them.
4. **F5 (own-text route)** opens the 601 amendment-only children, in dependency order after their parents.
5. **F6 (working texts)** for the 113 orders whose own original is not acceptable.

## Files

- `jobs/nalimov-tablebase/`: `drafter.py`, `census.py`, `prescreen.py`, `packets.py`, `verify.py`, `nalimov.py`,
  `predicate.py` (Respondendi's predicate, vendored with a parity test), prompts, README, and 47 tests including the
  conveyor route and typed plants.
- `jobs/maudslay-conveyor/conveyor.py`: `--producer nalimov`, `--controls typed`, list-price measures by stage.
- `research/nalimov/`: `census/CENSUS.json`, `CENSUS.csv`, `BLOCKER_GROUPS.json`, `PRESCREEN.json`, `MEASURES.json`,
  `project.py`, `PROJECTION.json`, `calibration/WAVE.json`, and this report.
