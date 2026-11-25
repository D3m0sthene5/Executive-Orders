# Design challenge, 2026-11-12: are we paying for the wrong workflow?

Question (owner): can the project be finished for substantially less at the same scientific quality? Prior investment
in the current per-order process is no reason to keep it. This page gives a decision. It does not start any repair,
production or job.

Every dollar is a list-price API dollar (allowance, not cash). Labels: **observed** (read from a ledger or report),
**allocated** (an observed total split by a stated rule), **assumed**, **projected** (arithmetic for work not yet
done). Human-certified count: 0. Nothing here changes that count.

## 1. Requirements and implementation choices

The requirements come from owner rulings and standing rules. The implementation choices are how we happen to meet
them today. Some of those choices are expensive, and none of them is required.

| Requirement (keep) | Where it comes from | How it is met today (implementation choice) | Required? |
|---|---|---|---|
| Source support: every claim rests on held, hashed, acceptable sources | `research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md`; claim checker | The producer reads a full frozen dossier (about 751k tokens of context per attempted order, observed, `research/nalimov/PROJECTION.json`) | The reading volume is not required. The source basis is. |
| Case-specific reasoning: each order's clauses, mechanism and dates come from its own text | same ruling, Pothier P2 own-text rule | A Sonnet producer writes prose reasons for every order | Prose written per order is not required. Owner ruling D-20261110-nalimov-script-producer accepts a script as the producer, with the review arms as the source review. |
| Independent review: blind, planted controls, both arms must uphold | `research/excavator/claude-nira-sweep-2026-10-29/REVIEWER_BRIEF.md`; `jobs/claim-kit/COMPLETION.md` | One status reviewer plus two fresh Opus arms read the whole review set and re-search the repository | Two independent arms are required. Tribonian measured the second arm catching 7 extra defects in 85 claims (observed, F-20261104-1). Re-reading a full context on every call is not required. |
| Source custody: the bytes of each cited source are retained | checker `custody_record_only` | Checked only at completion (EO 12753 failed there, observed, Lind) | The check is required. Running it late is a choice. |
| Owner adoption of every new status | standing rule; Respondendi v2 still open (A-20261110-respondendi-standing-rule-v2) | One owner decision per batch | Required. Per-batch adoption is allowed today. |
| Human certification is separate and stays 0 | CLAUDE.md | not touched | Required |
| Choices that are not requirements | | Orders dispatched before their sources are known to be held (22 of 30 in Lind were blocked by missing evidence, observed); each review set paying a large fixed reading cost (about $8.3 per set plus $0.72 per item, an assumed fit to two observed Papinian sets); coordinator-mediated handoffs (Lind coordinator $10.16 of $23.07, 44%, observed); prose rationales that reviewers must check sentence by sentence | Not required |

## 2. The current approach and two alternatives

| | Current: an agent writes each claim from a full dossier | (a) Source-first: analyse a shared legal event once, then check each order's applicability | (b) Generate then verify: a script drafts the claim from held records, agents answer only open questions, reviewers get exactly the evidence needed |
|---|---|---|---|
| What repeats today and would disappear | | Finding and interpreting the same ending instrument in every batch | Producer reading and prose writing; reviewers re-reading whole dossiers; prose defects and the corrections and re-reviews they cause |
| What replaces it | | One reviewed shared analysis plus hashed excerpts attached to every packet | Zero-token drafter (`jobs/nalimov-tablebase`), assembler and actual-checker pre-screen; a compact packet (about 4.8k tokens per claim, 0.32 of the dossier, observed in `PROJECTION.json`); each acting instrument's text read once with all its targets; question packets for the open items |
| What remains | Everything | Per-order custody, clause inventory, exceptions; two blind arms; adoption | Two blind arms, a status reviewer, planted controls, completion, adoption. Every order the script refuses goes back to the current route or waits for sources. |
| Existing tools | claim-kit, Maudslay conveyor | family-rules, Norton, X1, Jacquard, Pothier, NIRA shared analysis | Nalimov drafter v3, Maudslay `--producer nalimov`, typed controls, status-overlay stage |
| Record | Undecided route: Papinian 90 attempts, 6 ready, $7.71 per ready in workers and $9.30 with the allocated coordinator (observed/allocated, `research/lind/DECISION_2026-11-12.md`). Lind stage 0: 30 attempts, 0 ready, $23.07 (observed). Of 6 genuine Lind claims, 5 had defects that blind review found. Most were authoring errors: a wrong count, a self-contradicting sentence, the wrong body named for EO 12334, an imprecise date (observed, Lind `FAILURES.md`). | **Worked once:** NIRA, a decided family with one ending statute. At matched batch size it cost 3.26M against 7.01M weighted tokens, quality unchanged (observed, NIRA `REPORT.md`). **Failed or stalled elsewhere:** family rules, 0 of 748 certificates passed, because 552 of 571 targets had no located original (F-20261017-3); Norton produced 0 reviewed reusable answers and found that the ordinary batch already investigates a shared fact once (F-20261021-3, F-20261025-1); X1 led to 5 accepted claims (F-20261019-1); Jacquard's sampled lots did not pass, and a shared wrong premise forced 42 + 556 re-reads (Ulpian corrections); Pothier's 2,139 status leads (0.8% wrong in its pilot) are read by no kit code (Respondendi). | **Built, owner-signed, never run** (D-20261110-nalimov-calibration-v3-signed). v1 review: 17 of 36 real drafts were wrong; fixed in v2/v3 (F-20261110-nalimov-review-v1). Drafts for EO 11957 and 12348 equal the owner-adopted claims clause for clause (observed). Projected $0.10-0.42 per adopted status (projected, `PROJECTION.json`). Scriptable pool on the pre-fix kit: 8-12 of 720 express candidates (observed, census). The census has not been re-run on the 2026-11-12 rebuilt kit. |

**Why Cujas looked cheap** (68 filed for $23.27, `jobs/augur-launch/CONFIGURATIONS.json`): Cujas did not produce new
dossiers. It re-checked already reviewed Tribonian claims, carried over by `tools/carry.py`. The producer's only job
was to compare a transcription word by word with a GPO printing. Worker cost was about $0.41 per filed claim
(observed, Cujas `REPORT.md`). The report's own total is about $39, about $16 of it coordinator, so the rate is
nearer 1.7 filed per dollar. Cujas is not a production rate. It does show the mechanism behind (b): when the
substantive content already exists and agents only verify a narrow question, both arms uphold 91% (68 of 75) at well
under $1 per claim.

**Why (a) is not the chosen alternative.** Its one success was a decided family ending by one statute, and that
pattern is already in ordinary production (Papinian packets carry "Shared source texts"). Every source-first attempt
on the remaining orders stalled on per-order inputs: originals, custody, land and appointment facts. Those are the
same 22 of 30 Lind blocks, and a shared analysis does not remove them. A shared premise also spreads its errors to
every order that uses it (Jacquard). What (a) still offers, reading each acting instrument once for all its targets,
is already inside (b).

## 3. Chosen alternative: (b) generate then verify, on the slice it can reach

**Mechanism.**
1. A script, not a model, writes the claim for orders whose whole claim follows from held hashed records.
2. Drafts the kit's own assembler or the actual checker refuses never reach a paid reviewer.
3. Reviewers read a compact packet grouped by acting instrument.
4. Open legal questions go to agents as small question packets (TIERS, median about 800 tokens).

The repeated work that disappears is producer reading and writing ($0.19-0.20 per attempt, observed in Lind and
Papinian), prose defects with their correction and re-review (about $0.3-0.5 plus $3-5 per re-review set, allocated
in Lind `FAILURES.md`), and full-dossier re-reading by reviewers.

**Plausible size, on the reachable slice only.** Two terms decide the saving: how many claims both arms uphold, and
the fixed reading cost per review set.
- **Full route on an 8-order set where all 8 reach review** (projected from observed Lind unit costs): producers about
  $1.5, status reviewer and arms about $7, lean coordinator about $0.9, so about $9.4 per set. That is $2.4 per ready
  if 4 are upheld, or $9.4 if 1 is.
- **Nalimov:**
  - with Lind-like fixed arm overhead ($2-2.7 per arm, observed): about $5-7 per set, so $1.3-1.7 per ready if 4-5
    are upheld (projected);
  - with the small arm overhead its projection assumes: $0.10-0.42 per ready (projected).
- **Credible range:** about 2-6 times cheaper per accepted ready on the same orders (projected). 18-80 times is the
  optimistic bound. This is no population forecast.

**Break-even** (projected): the drafter, packets, conveyor overlay stage and two independent reviews are already
built. Future cost is building each new drafter tier and having it reviewed. That cost is not measured; assume $20-40
per tier, by analogy to the about $31-39 optimization sessions recorded in `research/lind/DECISION_2026-11-12.md` and
Lind `RECOVERY.md`. At a saving of $2-7 per ready, a tier pays back after 3-20 adopted orders. TIERS.json reach with
F3-F7, upper bounds: one-time commands 27; delayed effect 7; current law 6; actor 5; own terms 5; recorded amendments
1. Only the base express kind and the one-time-commands tier clearly repay their build. The rest are marginal.

**Fatal constraints found.**
1. **The pool is small, and evidence binds the bulk.** 8-12 scriptable orders on the pre-fix kit (observed). The
   coarse upper bound with every tier is 1,633 of 10,691 undecided; 9,058 need a source or a rule (`POOL_TALLY.json`,
   upper bounds). For most remaining orders no workflow saves anything until sources are held. Acquisition is
   required work, not a saving.
2. **Selection.** A script only drafts easy kinds. On the same easy orders the full route may also be cheap: 7 of 9
   past owner adoptions sit in Respondendi's express lot (observed). Only a paired test separates a route saving from
   picking easy orders.
3. **Review may not shrink.** Tribonian found that review cost is reading sources and judging law, and mechanical
   receipts removed none of it (F-20261104-1). If arms re-read full sources whatever the packet, (b) saves only the
   producer and the prose defects.
4. **Correlated script errors.** One drafter bug repeats across every member (v1: 17 of 36). Typed controls and the
   checker pre-screen are the guard.
5. **Untested plumbing.** The conveyor's status-overlay stage has run only on a fake kit (F-20261110-nalimov-overlay-stage).

## 4. The smallest executable comparison (specified, not run)

**Cases.**
- Run Nalimov `census.py` and `prescreen.py` on main's rebuilt claim-kit build (after 2026-11-12, zero tokens).
- Take every undecided order whose draft passes the kit assembler, `check_claim` and the actual checker, up to 12,
  grouped by acting instrument. Start from the signed eight (EO 10779, 11056, 11232, 11274, 11352, 11361, 12737,
  13765) if they still pass; the draw step must confirm none was attempted before.
- Natural unit: express named revocations, and amendment-only children if F5 is live. This is a narrow, mostly
  post-1936 slice. The result applies only to scriptable kinds.
- **Gate:** if fewer than 6 pass, spend nothing. The answer is then that the binding constraint is evidence and
  routing, not workflow.

**Arms (paired, every order in both):**
- **N:** conveyor `--producer nalimov`.
- **F:** the same conveyor with a Sonnet 5.5 producer, current route.
- Run N first.

**Held constant:**
- the same claim-kit build hash and frozen `EVIDENCE.json`;
- an Opus 5.5 status reviewer and two fresh Opus 5.5 blind arms in each arm, separate sessions, blind to arm;
- 2 typed planted controls per set, at least 1 status-determining;
- one review set per arm;
- the both-uphold rule, the actual checker, completion with isolated tracker replay;
- one owner adoption decision for the batch.

**Endpoints.**
- **Primary:** accepted ready dossiers (6/6) per arm, and all-in dollars per accepted ready.
- **Secondary, reported apart:**
  - accepted statuses;
  - defects by category (authoring versus legal);
  - reviewer tokens per genuine claim;
  - coordinator dollars per attempt;
  - orders where the two arms reach different statuses (each adjudicated against the held text).
- Only one claim per order files. Where both pass, the N version files, and the F version stays as measurement.

**Costs counted:**
- preparation (census, prescreen, freeze, packets; runner or local minutes recorded);
- production;
- independent review, including after-reveal review;
- corrections (none run in the test; each rejection priced at Lind's allocated unit costs);
- coordination (from the transcript);
- integration (PR, completion, tracker);
- owner minutes (plan signature, adoption, merge);
- the Augur cross-family plan review.

**Cap: $30 all-in** (projected budget):

| Setup | N review | F production | F review | Coordination | Integration | Augur review |
|---:|---:|---:|---:|---:|---:|---:|
| $2 | $6 | $3 | $9 | $6 | $2 | $1 |

**Stops:**
- any missed control stops that arm for adjudication;
- if N exceeds $10, stop: (b) is already falsified;
- if coordinator dollars exceed $0.25 per attempt after the N set, stop;
- hard stop at $30.

**Outcomes** (n = N ready, f = F ready, on the same orders):

| Result | What it changes |
|---|---|
| **Better:** N dollars per ready at most 1/3 of F's, n ≥ f − 1, 0 missed controls, no adjudicated status contradiction | Scriptable orders go to Nalimov by default. Re-run the census on every build. Build only the tiers whose measured saving times reach exceeds their recorded build cost. Augur stage 1. |
| **Comparable:** ratio between 1/3 and 1 | Use N only where it is free, the express kind. Build no more tiers. Remaining savings come from triage, pooled review and the conveyor: the existing workflow made cheaper. |
| **Worse:** N dollars per ready ≥ F's, n ≤ f − 2, or a missed N control | Retire script drafting on the undecided route. Record a Kean failure. |
| **Inconclusive:** n + f ≤ 2, or adjudication changes a count | No tier investment. At most one repeat at the same cap, on a new approval. |
| **Separate readout:** F's dollars per ready against Papinian's $9.30 | Any gap is order selection plus orchestration, not a saving. The harder orders still need sources. |

**Falsified if:**
- N's reviewer tokens per genuine claim are at least half of F's;
- N's upheld rate is below 60% (the projection's high case);
- both arms reject any N draft for a drafter defect;
- N's all-in cost exceeds $1.00 per accepted ready (Whitworth forecast, `research/plans/WHITWORTH_LINE_2026-11-10.md`)
  or $2.50 (its stop line).

**Approvals needed.** No standing rule changes. Needed:
1. A new Augur plan signed by the owner or reviewed by another model family. It replaces the v3 calibration hash:
   Opus verifiers instead of Codex, and an added F arm.
2. Owner confirmation that this paired test is not the stage 1 that Lind's result forbids. The zero-cost diagnosis
   (Lind `FAILURES.md`) is done.
3. Owner consent to attempt each order twice and file one claim.
4. A Bentham gate pass for `status_assignment.undecided`. An unranked refusal is a stop.

Respondendi v2 is not needed.

## 5. Decision

- **Assumption to challenge:** that a model must author every claim in prose from a full-context dossier. That
  choice, not the review standard, generates the authoring defects (5 of 6 genuine Lind claims) and the full-context
  re-reading.
- **Best-supported alternative:** generate then verify (Nalimov). It is already built and owner-signed, but never run.
  Source-first worked once (NIRA, decided) and is already in production; elsewhere it stalled on per-order inputs.
- **Mechanism and size:**
  - removes producer authoring, the prose defects with their corrections and re-reviews, and full-dossier reading by
    reviewers;
  - plausibly 2-6 times cheaper per accepted ready on scriptable orders (projected);
  - applies only to a small slice (8-12 orders today; the coarse upper bound is a few hundred to 1,633).
  - Evidence, not workflow, binds most remaining orders.
- **What would falsify it:**
  - N costs more than $1.00 per accepted ready, or more than 1/3 of F's on the same orders;
  - N's review tokens are at least half of F's;
  - its upheld rate is below 60%;
  - any drafter defect gets past the pre-screen;
  - fewer than 6 orders are scriptable on the rebuilt kit.
- **Smallest comparison:** paired N-versus-F on the 6-12 orders scriptable on the rebuilt kit, with identical sources,
  reviewers, controls and acceptance. N runs first. Capped at $30 all-in, with zero spend if the census finds fewer
  than 6.
