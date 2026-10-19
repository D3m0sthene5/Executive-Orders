# X1, the lifecycle class engine: build, pilot and recalibration (2026-10-19)

Branch `claude/x1-class-engine`. Design: `research/plans/EXCAVATOR_SERIES_2026-10-19.md` (X1).
Code: `jobs/x1-class-engine/` (zero-token job). Every number below is either **measured**
(named file) or **estimated** (said so). AI reviews here are independent *AI* reviews, never
human reviews; the human-certified whole-lifecycle count stays **0**.

## 1. What X1 does

| Step | What it produces | Result |
|---|---|---|
| Type classifier | a type, class, evidence and confidence for every pre-1937 order | 8,014 orders typed; 198 left `unknown` |
| Type rule book | one reviewed rule per repetitive type (`research/readiness/type-rules/`) | 22 rules, all approved as lead patterns after four rounds of independent AI review; hashes frozen |
| Extinction-event register | 5 mass-ending events, primary sources queued, candidate orders mapped | 8 sources queued; 0 held yet; mapping in `EVENT_CANDIDATES.csv` |
| Look-alike clusterer | near-duplicate clusters, exemplar, per-order diff, cloned clauses | 656 texts in 132 clusters; 187 clean clones, 337 dropped out |
| Batch review sheets | ≤50-row sheets per type, routed to the existing claim-kit path | 128 sheets; 26 rows can go straight to the assembler |

Classes: **spent** (ends by its own performance or terms: one-person civil-service
waivers, retirement exemptions, allotments, closings), **land** (reservations and
withdrawals), **swept** (candidate for one mass-ending event: NRA codes, Canal Zone,
Philippines, First World War), **standing** (known type, order-by-order research),
**unknown**.

## 2. Classifier precision (measured, AI-labelled, blind)

- First sample: 211 orders (stratified, 5 per type, plus 40 uniform), labelled by two
  independent agents who did not see X1's type (`precision/SCORED.csv`, `PRECISION.json`).
  Uniform subsample: exact type 80% (95% CI 65-90%), class 88% (74-95%). Weak types:
  property transfer 1/5, closings 2/6, Philippines 2/5, Canal Zone 6/10.
- Fixes from the error analysis (standing Saturday half-days are not closings; "functions
  transferred" is not a property transfer; incidental Philippine and Canal Zone mentions;
  "duties" no longer triggers customs). These were tuned on that sample, so they were
  re-measured on a **fresh holdout of 80 never-seen orders** (`HOLDOUT_PRECISION.json`):
  **exact type 90% (95% CI 82-95%), class 95% (88-98%)**. On the 38 holdout orders read
  against their own text: 35/38 type and class. The other 42 had no text and were labelled
  from the same WPA summary X1 reads, so their agreement is not independent.
- Per-type precision with n ≤ 6 per type is indicative only (`PRECISION.json`).

## 3. Type rule review

Round 1 (`TYPE_RULES_REVIEW_R1.json`): 2 approved (closings, public water reserves),
19 approved only with required changes, 2 rejected (no exemplar). The reviewer read
41 Stat. 1359 and found a real error: the 1921 joint resolution is a general rule with
named exceptions, not a list of Acts. Other corrections: trust-period extensions outside
the Indian Reorganization Act (s.13 Oklahoma, s.18 opt-outs, Act of June 15, 1935); FLPMA
savings for every land rule; Federal Power Act s.24; Panama Refining; seven wrong or
badly cut exemplars. Round 2 rewrote 20 rules with hand-picked exemplars and exact
quotes, withdrew the stock-driveway rule (no held text; those 4 orders use the land rule),
and left the two approved files byte-for-byte unchanged (hashes re-verified). Round 2:
17 approved, 5 with changes (a new error caught: the Canal Zone liquor provision was repealed
June 19, 1934, not with Prohibition in 1933; Federal Power Act s.24 wording). Round 3: 21
approved. Round 4: the last rule (property transfer: a "or as promptly thereafter" date is
not a delivery date) approved. **Final: 22 of 22 approved as lead patterns**, each pinned by
its file hash in `TYPE_RULES_REVIEW.json`; only changed files were rebuilt between rounds, and
every carried approval was re-hashed. The job marks a rule `reviewed_frozen` only when its
file hash equals the reviewed hash (all 22 do). Review cost: 7.9 + 7.2 + 2.4 + 0.7 minutes.
Non-blocking recommendations from round 3 remain open (`TYPE_RULES_REVIEW.md`).

## 4. How much of the 7,065 "type unknown" hours moved (estimated with the effort model)

The plan's 7,065 h included 2,431 h of census-gap rows (orders APP counts but the project
does not hold). The plan meant to count those as land, but `cls("land")` returned "other";
`excavator_scenarios.py` now says so and, with X1, splits gap rows by the class mix of
Lord's 1943 unnumbered list (an estimate: the rows name no order).

| Where the 7,065 h went | Hours |
|---|---:|
| Held orders now in a class path (land 1,013, spent 629, swept 441) | 2,083 |
| Held orders now of a known standing type (no class path yet) | 2,275 |
| Held orders still unknown or unclassified | 276 |
| Census-gap rows, estimated into class paths (land 1,366, spent 185, swept 27) | 1,578 |
| Census-gap rows, estimated other | 854 |

So about 3,660 h moved into class paths (2,083 h order by order) and 2,275 h became
known types; about 1,130 h stay unknown.

## 5. Pilot: two complete batches (measured)

**The ceiling.** The claim-kit assembler emits only complete claims, and only for orders
with a provisional status and a dossier. Of 8,014 pre-1937 orders, only **52** have both a
provisional status and a held text. The pilot ran all 52:

- **P1** (20): spent and swept types (retirement exemptions, civil-service waivers, closings,
  allotment, alien property, Canal Zone).
- **P2** (32): land (9) plus a control group of 23 known types without a class rule.

Path: `kit.py prepare` → producer agent (decisions, `apply`, `batch-check` with the actual
claim-checker) → separate independent AI reviewer → accepted lines only →
`research/readiness/claims/claude-2026-10-19-x1-pilot.jsonl` → claim-checker → tracker.

| | P1 | P2 | Total |
|---|---:|---:|---:|
| Orders | 20 | 32 | 52 |
| Submitted by producer | 3 | 3 | 6 |
| Upheld by independent reviewer | 3 | 2 | **5** |
| Rejected by reviewer | 0 | 1 (EO 5825: earlier end by 1936-38 leave rules not excluded) | 1 |
| Blocked, block confirmed justified by reviewer | 17 | 29 | 46 |

Accepted complete claims: EO 5881, 5981, 5982 (retirement exemptions ending on their own
stated dates), EO 5614 (revoked by EO 8512, 1940-08-13), EO 5707 (revoked by EO 8189,
1939-07-05). The actual claim-checker passes all 5 on every step (42 quotations exact).

**Time and tokens** (harness telemetry of each agent: wall time and tokens, not self-reports):

| Step | Minutes | Tokens |
|---|---:|---:|
| Producers (P1 7.2, P2 8.1) | 15.3 | 405,765 |
| Independent reviewers (P1 5.2, P2 4.9) | 10.1 | 358,203 |
| **Per order screened** | **0.49** | 14,692 |
| **Per accepted complete claim** | **5.1** | 152,794 |

Not counted: the orchestrating agent's own time; building X1; precision checks (5.3 min);
rule reviews (7.9 min in round 1).

**Against the effort model.** The model's tiers for these orders (text held, no machine
history, before 1937) total about 60 agent-minutes per order for the four legal steps. The
pilot's 5.1 minutes per accepted claim is far below that, but it is **selection-biased**:
only the easiest 10% got through. The other 90% were blocked by missing evidence, not by
review effort.

**Rejection rate: 1 of 6 = 17%, above the claim swarm's 11%.** On the plan's success test
(minutes per accepted claim fall **and** rejections ≤ 11%), the pilot **does not pass**.
With 6 submissions the rate is very uncertain either way.

**Why rows were blocked (the real constraint).** No acceptable original held (19); an end
date that lives only in a record not held (6 civil-service waivers: the appointment date);
an ending instrument held but not located as a provision in the dossier (6: EO 7968 and
EO 5707 provisions); serial extension orders not held (2); own-terms ends the kit cannot
cite (2: EO 5763 closing, EO 5930: no own-terms evidence record and no mechanism column);
earlier-end questions needing statutes (Nationality Act of 1940; 1936 leave acts); no land
revocation or PLO evidence (9 land orders: X2's job).

**What X1 did and did not do in the pilot.** The retirement-exemption rule's serial-extension
warning caught two traps (EO 6013, 6030). Types were wrong for 3 of 20 P1 rows and several
control rows (fixed in the classifier where general). The Canal Zone event was the first end
for none of the 4 Canal Zone orders (all ended earlier). No clone was used; one clone pair
(EO 6143/6276) hid different partial revocations.

## 6. Recalibration (measured values in `MEASURED.json`)

`excavator_scenarios.py` now reads X1's own types and `MEASURED.json`:

- Type tribunal: hit rate 0.19 (3 of 16 spent orders reached an accepted claim, assumed
  0.85); legal-step minutes from the measured 5.1 per accepted claim.
- Extinction-event mapper: hit rate 0 (0 of 4; assumed 0.8).
- Look-alike cloning: no saving demonstrated (assumed a saving).
- Risk-tiered review: **excluded** (not approved by the owner); reported separately.

| | Before (assumed) | After (measured) |
|---|---:|---:|
| X1 hours saved, without risk-tiered review | 4,134 incl. review change | **463** |
| Hours left after X1 | 13,010 | **16,681** |
| Hours left after the whole series, without risk-tiered review | 9,082 incl. review change | **11,256** |
| Same, if risk-tiered review were approved (assumption, not measured) | | 10,027 |

The baseline is unchanged at 17,144 h (`build_effort.py` rerun; same output).

## 7. What this means

X1 types the old orders well (90% exact on a fresh holdout), which removes most of the
"unknown" pool. But typing does not by itself cut hours: the pre-1937 work is blocked by
missing originals, missing end instruments and missing provisional statuses, not by
deciding what kind of order it is. X1's leverage depends on those inputs arriving: X3
(texts), X2 (land revocations), the event sources (queued), and a status path for the
7,339 undecided pre-1937 orders.

## 8. Queue for what remains

- `jobs/x1-class-engine/output/sheets/`: 128 sheets; 5,297 rows need a provisional status
  first (`status_first`), 561 need a text (`text_first`).
- 28 fetch requests in `research/readiness/FETCH_QUEUE.jsonl` (8 event sources, 20 pilot
  sources).
- The two own-terms rows (EO 5763, 5930) and six "provision not located" rows become
  submittable if claim-kit gets an own-terms end mechanism and locates EO 7968 / EO 5707
  provisions (ask to the claim-kit owner).
- EO 5825: correction version after EO 7013, EOs 7409/7321 and the 1936 leave act are held.
- P1 reviewer: the three upheld P1 claims should, in a correction version, list the pre-1937
  WPA/Hoover-text search as its own structured search entry.

## 9. Files

- Job and outputs: `jobs/x1-class-engine/` (`output/` is written by the GitHub run).
- Rules: `research/readiness/type-rules/`; reviews `TYPE_RULES_REVIEW_R1..R3.json` and the
  current `TYPE_RULES_REVIEW.json` (round 4).
- Precision: `precision/` (blind samples, labels, scores).
- Pilot: `research/excavator/x1-pilot-2026-10-19/P1`, `P2` (packets, decisions, applied
  versions, `review/AI_REVIEW.json`); claims `research/readiness/claims/claude-2026-10-19-x1-pilot.jsonl`.
- Telemetry: `AGENT_TELEMETRY.jsonl`; measured values `MEASURED.json`.
