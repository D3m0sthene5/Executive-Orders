# Mountweazel: measuring whether our reviewers catch defects (design, 2026-10-20)

Named for Lillian Virginia Mountweazel, the invented fountain designer who was planted in the
1975 *New Columbia Encyclopedia* to catch anyone copying it. Map makers did the same with "trap
streets" and paper towns such as Agloe, New York. Mountweazel plants documented defects among
real, already-reviewed items, sends the mixed batch to a reviewer, and counts how many of the
plants the reviewer catches.

Status: design only. Nothing is built, seeded or run yet. The tool will live in `jobs/mountweazel/`.

## 0. Why it exists, and the rules

The measure is orders ready for human review: 135 of 14,972. The certified count stays 0. AI
statuses are hypotheses. Bowditch Y1 (`research/excavator/bowditch-2026-10-20/REPORT.md`) passed its
reviewer test with **0 of 15** disagreements. The same model family produced and reviewed those
proposals. The reviewer spent about 0.32 minutes on each accepted proposal and 0.06 minutes on each
block (`y1_0*/REVIEW_LOG.csv`), and every record says `independence_confirmed: true`. Zero
disagreements mean something only if we know how often this reviewer catches a defect that is
there. If it catches 90%, 0/15 is reassuring. If it catches 30%, up to about half of the 15 could be
wrong (section 5). We do not know that rate today. Mountweazel measures it.

Hard rules:

1. **Seeded items never enter anything a job or ledger reads.** That covers
   `research/readiness/claims/`, `FETCH_QUEUE.jsonl`, `EXHAUSTED.jsonl`,
   `SOURCE_AUDIT_HOLDS.jsonl`, `research/readiness/decisions/` and `reviews/`, any
   `research/excavator/**` path (`jobs/claim-kit/status_overlay.py` accepts overlays from there),
   `research/progress/` (statuses and ledger), tracker input, and every cross-job discovery path
   (section 2.3). Seeded items live only in `jobs/mountweazel/fixtures/`, carrying the SEEDED flag,
   and as rendered packets in the session scratchpad (`.../scratchpad/mountweazel/`), which is never
   committed.
2. Mountweazel never edits claims, statuses, the codebook, census, ledger or human reviews. It never
   writes an `eo-lifecycle-review/v1` record. It produces measurements and nothing else.
3. When a reviewer flags a real item and adjudication confirms the flag, the finding goes through
   the normal review process as an ordinary finding. Mountweazel does not apply it.
4. A seeded item is never shown to the owner as a finding, and its review text is used only for
   scoring.

## 1. Defect taxonomy, grounded in observed rejections

I read every committed reviewer outcome I could find that records a reason. That gives **17
item-level rejections**, plus 1 observed reviewer miss, plus the claim swarm's aggregate of **21
rejections out of 197**. Per-item reasons for the swarm were not committed. Its stated main cause
is a missed earlier end: the order's own term, an earlier partial amendment, or an amendment
mistaken for an end (`HANDOFF/notes-claude.md`, 2026-10-18 02:00 entry;
`research/plans/EXCAVATOR_FUNNEL_2026-10-18.md`). Across the reviews, **block_not_justified has been
recorded 0 times**: 35 of 35 in Bowditch Y1, 45 of 45 in Bowditch Y2, and 46 of 46 in the X1
pilot. A count of 0 has the same problem as the 0/15 above, so over-blocking also gets seeded.

| Code | Defect | Observed rejections (count, sources) | Track |
|---|---|---|---|
| D1 | **Deadline or bound treated as the actual end.** A report deadline, a "not later than" limit or a term is recorded as the first end. | 1: EO 12813 (`research/excavator/2026-10-18/batch-pilot/REPORT.md`). The rule is in `AGENT_PROTOCOL.md` step 3 ("A report deadline is never an end"). EO 11256 shows the same trap, which the reviewer flagged in an upheld partial claim. | C, S |
| D2 | **One-time command dated to a later revocation.** A command already performed is treated as ongoing until the order is revoked. | 3 orders, 4 rejection records: EO 13792 (`bowditch-2026-10-20/y2_01/review/AI_REVIEW.md`); EO 12734 and 12817, rejected in both arms (`batch-pilot/REPORT.md`, `matched/B/review/REPORT.md`). **Arm B's first reviewer accepted EO 12734**, and only the stricter rereview rejected it. That is the one recorded miss by a same-family reviewer. | C |
| D3 | **The quote does not support the claim.** The cited span stops before the operative sentence, or the stated mechanism does not match the text. | 1: EO 10192 (`y2_01/review/AI_REVIEW.md`). A near miss: the machine ACT spans for EO 11417 pointed to the wrong passages. The reviewer noticed and relied on the actor text (`y1_01/overlay/EO_11417/STATUS_REVIEW.json`). | C, S |
| D4 | **A partial-scope change treated as a total end.** A partial amendment or supersession is read as ending the whole span or order, although some mandates are kept. | 1 item: EO 12757 (`research/production/claim-kit-pilot-2026-10-18/reviews/full-recheck-EO_12757.jsonl`). Also a share of the swarm's 21 ("amendment mistaken for an end"). The Bowditch producers blocked 4 such cases correctly (11251, 10355, 13159, 9007). | C, S |
| D5 | **Missed earlier end.** An own term, an earlier amendment, or the history of an incorporated statute ends the order before the cited end. | 2 items: EO 5825 (`x1-pilot-2026-10-19/P2/review/AI_REVIEW.md`, which also shows `unresolved_material_gaps: []` while the producer named an open question); EO 9799, where the statutory power history was never read (`research/readiness/reviews/astra-2026-10-18/reviewer/EO_9799/REVIEW.json`). Also the main cause of the swarm's 21. | C |
| D6 | **A known later event is left out.** A later additive or partial amendment, or a named-body branch, is missing from the lifecycle. | 2: EO 13028 (`claim-kit-pilot-2026-10-18/reviews/family-13345.jsonl`); EO 12075 (`astra-2026-10-18/reviewer/EO_12075/REVIEW.json`). | C |
| D7 | **Wrong effective date.** Signing-date execution is treated as first cessation, or an effective date is taken from the wrong place. | 5: EO 14134 to 14138, from one systematic error (`research/production/2026-10-17/pother/INDEPENDENT_PILOT_REVIEW.json`). Traps a reviewer did catch: EO 5707 (an "effective July 1" sentence that belongs to EO 8190/8191), EO 9799 (activated Nov. 13, signed Nov. 8), and the machine TERM date for EO 5881. | C, S |
| D8 | **Wrong identity.** The inventory is taken from an adjacent order printed on the same page. | 1: EO 9789's kit inventory is actually EO 9788 (`research/excavator/2026-10-18/review/INDEPENDENT_AI_REVIEW.md`). | C, S |
| D9 | **Search coverage overstated.** The counterevidence search scope is credited to a workpaper that did not cover it. | 1: EO 11782 v3 (`astra-2026-10-18/reviewer/EO_11782/v3/REVIEW.json`). | C |
| D10 | **Wrong target.** The cited actor revokes a different order. | 0 rejections, 1 open flag: EO 12086's ledger NO, where EO 14173 revokes EO 11246 and not EO 12086 (Bowditch REPORT, owner questions). | S |
| D11 | **Inferred supersession presented as express.** | 0 rejections. The producer blocked 1 correctly: for EO 13159, EO 13617 has no revocation verb (`y1_01/OUTCOMES.csv`). | S |
| D12 | **A savings clause is ignored.** | 0 rejections, 1 contestable reading: EO 11417 sec. 1-904 (Bowditch REPORT). | S |
| D13 | **Unjustified block (inverse plant).** The decision blocks for a missing record that the packet actually holds. | 0 of 126 block reviews ever found an unjustified block (see above). | C, S |

Track C covers lifecycle claims (`eo-lifecycle-claim/v1` lines, Y2 style). Track S covers status
proposals (`STATUS_DECISION` + `EVIDENCE` + proposal, Y1 style). The table is committed as
`jobs/mountweazel/taxonomy.json`, with one row per observed instance (path, order, reviewer, date).
Its counts are recomputed from those rows by the job and never typed by hand. A new rejection
anywhere in the repo adds a row. A defect type with no observed instance (D10 to D13) is marked
`basis: "owner_question" | "producer_block" | "zero_count_probe"` so that it is never presented as
an observed rejection.

Seeding weights follow observed frequency inside each track. Every type gets at least 2 plants per
round, because a type we have never seen caught cannot be assumed to be caught.

## 2. Seeding

### 2.1 Method: one documented mutation of a real upheld item

- **Base pool.** Track S uses the 15 accepted Bowditch Y1 NO proposals and their held evidence.
  Track C uses the 176 accepted swarm claims, the 12 claim-kit pilot acceptances, the 5 upheld X1
  claims, the 3 upheld Bowditch Y2 claims and the upheld Astra claims.
- **One operator per plant.** A plant changes exactly one locus in one documented way. Every other
  field is copied byte for byte from the upheld item. Operators by type:
  - D1: replace an actual end with the deadline or term date in the item's own original.
  - D2: move a one-time report or notice clause's `first_end` to the later revocation, and remove the
    "spent" reasoning.
  - D3: replace the end quote with an adjacent sentence from the **same held text**. The new quote
    names the order but has no operative verb. It is still verbatim, so the mechanical quote check
    passes.
  - D4: assert a whole-order end at the date of a held partial amendment that changes one section only.
  - D5: on an own-term item (for example EO 5881, 11756), cite a held later revocation as the end, and
    drop the term analysis.
  - D6: delete one `later_events` entry.
  - D7: use the actor's signing date where its held text gives a later effective date (for example
    EO 12163 sec. 1-905).
  - D8: take the inventory from the neighbouring order on the same FR page. Both texts are held.
  - D9: inflate the coverage line of `later_source_search` above what the packet's manifest shows.
  - D10: point the basis at a held actor that revokes a nearby number.
  - D11: replace an express revocation with a re-declaration that has no revocation verb.
  - D12: omit a savings clause that the adjudicators agree plausibly continues the target.
  - D13: turn an accepted item into a block that names a record the packet contains.
- **Plausibility.** A separate seeder agent writes the changed rationale in the producer's style,
  within ±15% of the original length. Hashes inside the packet are recomputed so that it is
  internally consistent. Every plant must still pass the mechanical gates it would face in
  production: verbatim quotes, valid dates, and dates after signing. This is checked **in memory**
  by importing `claim_gate.validate_claim` and the quote matcher on the de-flagged copy. The job
  never runs `jobs/claim-checker/job.py` on a plant and never writes checker output. Plants test
  judgment, not mechanics.
- **Detectable from the packet.** Each plant records the exact refuting span (source path,
  character offsets and quote) that a careful reader of the packet would use to reject it. A plant
  that the packet alone cannot refute is unfair and is discarded.
- **Pre-adjudication.** Two checkers who are not the seeder confirm that each plant is a real defect
  and that the refuting span is in the packet. If they disagree, the plant is discarded. During
  scoring, a reviewer who argues convincingly that a plant is correct voids that plant; it is not
  counted as a miss. Voided plants are reported.

### 2.2 Fixture format (the flag the claim checker rejects)

`jobs/mountweazel/fixtures/<batch>/<item>.seeded.json`:

```json
{"schema": "mountweazel-seeded-item/v1", "SEEDED": true,
 "instrument_id": "SEEDED:EO:11532", "batch_id": "MW-S1", "item_id": "MW-S1-07",
 "defect_code": "D10", "base": {"path": "...", "sha256": "..."},
 "mutation": {"operator": "D10.retarget_actor", "field": "...", "before": "...", "after": "...",
              "why_plausible": "...", "refuting_span": {"text_path": "...", "char_start": 0, "char_end": 0, "quote": "..."}},
 "pre_adjudication": [{"by": "...", "agrees_defect": true}, {"by": "...", "agrees_defect": true}],
 "seeded_payload": {"schema": "SEEDED-eo-lifecycle-claim/v1", "instrument_id": "SEEDED:EO:11532", "...": "..."}}
```

The flag works at both levels. `research/stage19/code/claim_gate.validate_claim` rejects any schema
other than `eo-lifecycle-claim/v1` and any `instrument_id` that does not start with `EO:`, so the
wrapper and the payload each fail with `schema` and `instrument_id`. The `.seeded.json` extension
matches no job's glob. The answer key, `fixtures/<batch>/KEY.seeded.json`, lists which item ids are
plants. Only the scorer reads it.

### 2.3 Paths Mountweazel must never write

The rule is not limited to `research/`, because other jobs read across all job folders. These
discovery globs exist today:

- `jobs/*/output/*.csv` (claim-checker, any CSV with `instrument_id` and `signing_date`).
- `jobs/*/output/SOURCES.jsonl` (claim-checker, official-fixity, case-bundles, claim-kit).
- `jobs/*/output/FRAGMENTS*.jsonl` and `jobs/*/data/**/FRAGMENTS*.jsonl` / `SOURCES.jsonl`
  (claim-kit inputs, case-bundles).
- `jobs/*/data/PROVENANCE.json`.
- `jobs/*/output/CATALOG_INDEX.csv` and `EDGES.csv`.
- `jobs/*/output/SUMMARY.json` (claim-kit reads its `machine_searches`; daily-digest reads it).

So `jobs/mountweazel/` has no `data/` folder, and its `output/` holds only `STATUS.json`
(ok/failed and counts) and `SENSITIVITY.json`. Daily-digest reads `STATUS.json`, which is
harmless. Results go to `jobs/mountweazel/results/<batch>/`.

### 2.4 Guard

`mountweazel.py guard` runs before every scoring step and in the job's tests. It fails `STATUS.json`,
and a failed guard means nothing is pushed, if:

1. Any fixture lacks `SEEDED: true` or the `SEEDED:` id prefix, or if `validate_claim` on its payload
   does *not* return `schema` and `instrument_id` errors.
2. Any forbidden path from section 0 rule 1 or section 2.3 contains the string `SEEDED:` or
   `mountweazel-seeded`, the canonical sha256 of any plant (flagged or de-flagged), or any
   mutation's `after` text of 40 characters or more.
3. A render target resolves inside the repository. Rendered, de-flagged packets may be written only
   under the scratchpad.

## 3. Blinding

- **Shared look.** Real items and plants are rendered by the same template into one packet. Each
  item has an opaque id (`MW-S1-07`), the order is shuffled with a recorded seed, and the
  `SEEDED:` prefix and wrapper are removed in the scratch copy only.
- **Seeded share.** Each batch draws its share uniformly between 20% and 30% (about 25%). The share
  is not disclosed.
- **No order in both arms of one batch.** Orders cross over between batches. In S1 an order is real;
  in S2 its mutation is the plant, and a fresh reviewer instance reviews it. Over S1 and S2, each of
  the 15 Y1 orders appears once as real and once as a plant.
- **No diffing.** The reviewer works in a packet directory that holds copies of the held source
  texts it needs plus distractor texts, not a repository checkout. If a checkout is unavoidable, it
  is a sparse checkout that excludes `research/readiness/claims`, `research/readiness/reviews`,
  `research/excavator`, `research/production` and `jobs/mountweazel`. Otherwise a reviewer could
  find the plants by comparing items with committed claims or Bowditch's `PROPOSALS.jsonl`.
- **Production prompt.** The reviewer prompt is the production reviewer prompt, word for word, with
  no mention of plants. Bowditch's reviewer prompts were not committed; only the
  `eo-status-overlay-review/v1` records and `REVIEW_LOG.csv` columns are. Mountweazel therefore
  commits the exact prompt and its sha256 with every batch. A result applies only to the prompt,
  model and packet version that produced it.
- **Leak test.** Before a round, a discriminator agent with no source access tries to tell plants
  from real items using the packet wording alone. On a pilot of at least 20 items, if its AUC is
  above 0.65, the plants are too easy to spot and the seeder reworks them.

## 4. Metrics

For every item the reviewer returns `decision` (accept, reject, block_justified or
block_not_justified), `locus` (field path or source span), `reason` and `confidence`.

- **Catch, strict (primary).** A reject or block_not_justified on a plant that names the mutated
  locus or the refuting span. Two raters score this against a rubric, and their agreement is
  reported.
- **Catch, lenient.** A rejection of the plant for any reason. Lenient minus strict is "right
  verdict, wrong reason". That gap matters, because a lucky rejection does not prove the reviewer
  would catch the same defect again.
- **Flags on real items.** A reviewer rejection of a real item is **not** automatically a false
  alarm, because real upheld items can contain defects that were never caught. Two adjudicators,
  and later a human, classify each flag as `confirmed_real_defect`, `contestable` or `false_alarm`.
  A confirmed defect is recorded as a natural catch and routed through the normal process (rule 3).
  The false-alarm rate is reported with contestable flags counted both ways, giving two bounds.
- **Per defect type and pooled.** Pooled sensitivity is weighted by the expected defect mix of the
  track being calibrated: the Track S mix for Y1, the Track C mix for claims. It is not the raw mix
  of plants.
- **Intervals.** Every rate gets a Wilson 95% interval, plus Clopper-Pearson when the count is 0 or
  n, and a Jeffreys posterior, Beta(k+0.5, n-k+0.5), which section 5 uses. For example, 9 of 10
  caught gives a Wilson interval of [0.60, 0.98]. A per-type rate with n below 5 is labelled
  *indicative*. Results are pooled only within one reviewer configuration (model, prompt sha, packet
  version).
- **Miss correlation.** When two reviewers see the same plants, record
  ρ = P(both miss) / (P(miss A) · P(miss B)). That number tells us whether a second reviewer from
  the same family adds anything (ρ near 1/P(miss) means the misses are perfectly shared).
- **Cost.** Reviewer minutes and tokens per item, so that a cheaper configuration can be compared
  at equal catch rate.

## 5. Recalibrating past reviews (Bowditch Y1 first)

Let *s* be strict sensitivity weighted by the defect mix, *f* the false-alarm rate, *r* the observed
reject rate and *π* the producer's defect prevalence. Then r = πs + (1−π)f, so
π̂ = (r − f)/(s − f) (Rogan-Gladen). The residual defect rate among accepted items is
π(1−s)/(1−r).

For **Bowditch Y1, r = 0/15.** The one-sided 95% upper bound on r is 1 − 0.05^(1/15) = 0.181.
Taking f = 0, which is conservative here:

| Reviewer sensitivity *s* | Upper bound on π | Upper bound on defective items among the 15 accepted |
|---|---|---|
| 0.9 | 0.20 | about 0.4 |
| 0.6 | 0.30 | about 2.2 |
| 0.5 | 0.36 | about 3.3 |
| 0.3 | 0.60 | about 7.7 |

Mountweazel replaces the guess about *s* with a measured posterior. The calibration draws *s* and
*f* from their Jeffreys posteriors and *r* from Beta(0.5, 15.5), then reports the posterior mean and
95% upper bound of defective items among the 15. The result is written to
`results/<batch>/CALIBRATION.json` and summarised in Claude's HANDOFF note. Nothing about the 15
proposals changes: `owner_acceptance` stays false, and the owner still decides.

The same calculation applies to every earlier same-family rejection rate: the claim swarm (21/197),
the claim-kit pilot (2/12), X1 (1/6) and Bowditch Y2 (2/5). Every one of those rates is a lower
bound on π. For example, with s = 0.6 and f = 0.02, the swarm's 10.7% implies π ≈ 0.15 and about 12
undetected defects among its 176 accepted claims. That turns the human spot check already
recommended in `EXCAVATOR_FUNNEL_2026-10-18.md` (10 to 15 of 130) into a sample size with a stated
purpose.

What a result implies for the reviewer:

- Lower 95% bound on *s* of at least 0.8, with f ≤ 0.1: a single same-family review is adequate for
  *AI status hypotheses*. It still is not certification.
- *s* below 0.6: 0/15 tells us little. Require a stricter checklist, such as arm B's command-specific
  first-cessation check, or a reviewer from a different configuration. Then re-measure.
- Strict catch on D2 and D5 below 0.6: the defects that have actually occurred are the ones getting
  through. Fix the reviewer before scaling Y2.

## 6. How other tools use it

- **Llull.** The other workflow is still designing it, so this is an interface, not a claim about
  Llull's internals. `output/SENSITIVITY.json` gives, for each defect type and reviewer
  configuration, the probability of being caught when present, with intervals. `taxonomy.json`
  gives the observed prior frequencies. Together these are the base rates that any reasoning about
  "how likely is this accepted item to be wrong" should start from, instead of treating 0
  disagreements as 0 defects.
- **Junto.** Junto's quality fields today are `accepted`, `rejected` and `checker_pass`
  (`JUNTO_DESIGN.md`, tests). A saver that makes the reviewer lazier *raises* accepted and *lowers*
  rejected, so it would look like a quality gain. Any saver that touches review (a trimmed packet,
  a smaller reviewer context, a Revere handoff for reviewers) must also pass a Mountweazel batch.
  Its test line gains `quality.mountweazel = {batch_id, strict_catch: [k, n], false_alarm: [k, n]}`.
  The rule: a saver is `quality_fell` if the lower 80% bound of (after − before) strict catch is
  below −0.10, or if the false-alarm rate rises. Mountweazel batches cost tokens, and Junto records
  that cost like any other test.
- **Readiness tracker and owner.** Mountweazel does not change the measure. Its only effect on the
  measure is indirect: it tells the owner how much an AI "accepted" is worth, and how large a human
  spot check is needed before relying on one.

## 7. Plan and cost

| Phase | What happens | Model cost |
|---|---|---|
| P0 | Build `taxonomy.json` from the 17 item records and the swarm aggregate; fixture schema; `guard`; tests (guard fails on a planted forbidden-path leak; `validate_claim` rejects every fixture; render refuses a repo path). | none |
| P1 | Track S crossover: two batches of 24 items each (18 real = 9 accepted + 9 justified blocks; 6 plants), covering D10, D11, D12, D7, D4 and D13 twice each. Bowditch's production reviewer configuration. Recalibrate Y1. | about 90k reviewer tokens per batch (Bowditch Y1 used about 91k for 25 items), plus seeding and adjudication |
| P2 | Track C: batches of 40 (about 10 plants) from the claim pool, weighted to D2, D5, D6, D4 and D7. At least 5 plants per type before any per-type rate is reported. | estimate only; measure it |
| P3 | Compare configurations: same family against a different configuration, and the arm B checklist. Measure miss correlation ρ. Feed the results to Junto and Llull. | measured per batch |

P1 gives 12 plants. A pooled 11 of 12 would have a Wilson interval of about [0.65, 0.99], which is
enough to tell "reassuring" from "uninformative" for the 0/15. It is not enough for per-type rates,
which wait for P2.

Layout: `jobs/mountweazel/{README.md, mountweazel.py (taxonomy | seed | render | score | calibrate |
guard), taxonomy.json, fixtures/<batch>/*.seeded.json, results/<batch>/, output/STATUS.json,
output/SENSITIVITY.json, needs.txt}`. Commands that need more than the container can hold run as a
bounded GitHub Actions job, and their `output/STATUS.json` is checked before any result is used.

## 8. First trial: MW-C1 (2026-10-20)

20 Track C items, 6 plants, one same-family reviewer (claude-opus-5-5) reading the batch only.
Strict catch 3/6 (Wilson 0.19-0.81). Caught: D4 MW-C1-04, D5 MW-C1-07 (keyed D2, relabelled: the clause is an
annual report, not a one-time duty), D5 MW-C1-15. Missed: D3 MW-C1-09 (noticed the cut quote, accepted it as OCR
truncation), D6 MW-C1-16, D9 MW-C1-01. False alarms 0/14 real (Wilson 0-0.22).

All three caught plants carried a seeding tell: the global rationale swap rewrote sentences about sibling clauses,
so each packet contradicted itself. All three tell-free plants were missed (0/3, Wilson 0-0.56). Those are also the
subtler types, so tells and difficulty are confounded. Fixes: `_swap_safe` (skip plants whose old end is shared),
recurring-duty exclusion for D2, same-unit refutability for D9, specific-term strict matching, novel-only leak
needles in `check` (the trial's check had 24 false positives from real EO 12076 text matching a D3 prefix).

Bowditch Y1's 0/15 (flag rate at most 0.22) with a 0.5 catch rate bounds defect prevalence at 0.44 or less; at the
catch rate's lower bound, or tell-free, the bound is 1.0. A different track (status proposals), so it transfers
only as an order of magnitude. Next: MW-C2 with fixed operators, a no-access leak discriminator, a Track S batch
with source texts, and a different-family or human reviewer.

