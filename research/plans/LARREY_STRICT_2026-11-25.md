# Larrey strict level: back-test on filed dossiers (2026-11-25)

Larrey is the zero-token check (it spends no model tokens) that runs before an agent is sent to an order. It keeps
out orders that lack an input the route needs. This plan asks whether cheap machine features in the frozen dossier
can also keep out orders that are likely to be attempted and then not filed. The aim is to raise the share of
attempts that end in a filed dossier.

**Finding.** One rule clears the bar set for this work: at least 1.5 times the filed rate among admitted attempts,
while keeping at least 85% of past filed dossiers. It is now an opt-in level, `LARREY_LEVEL=strict`, and the default
level is unchanged. Strict applies Larrey's existing hard and soft gates plus two new gates.
- **No contradicting status lead** (decided route only). The claim kit has recorded no conflict for the order, such
  as a partial ending found for a provisional YES. On a provisional YES, no held whole-scope ACT with an ending verb
  (revoke, supersede, terminate, abolish, rescind) names the order.
- **At most 5 status-history events.** The order's status history (the status-history job's record of later
  amendments, revocations and catalog notes, carried in the dossier) lists at most 5 later events.

On 570 past attempts, strict admits 52% of them. Among admitted attempts, 27.8% filed, against 16.6% at the default
level: 1.67 times as many. It keeps 83 of the 91 filed dossiers (91%).

Most of that lift was already available at the existing soft level (1.36x). Among attempts the soft level admits, the
two new gates add 1.22x. On the 50 Bartolus YES re-runs, whose dossiers already held the National Emergencies Act
continuation notices, they add 1.38x. Since 2026-11-24 the notices are held, so on today's decided pool the NEA soft
gate admits nearly every order. There, the expected gain of strict over the default is about 1.3-1.4x, not 1.67x:
it clears the bar on the pooled back-test and on the later waves, but probably not on the decided route alone from
now on.

## Data and method

**Waves.** The back-test reads the frozen packets of five waves:
- Papinian decided batches y01-y14 and c01 (370 attempts, 61 filed) and undecided batches u01b-u03 (90, 6 filed);
- Haloander undecided u01-u03 (30, 3 filed);
- Bartolus decided y01-y04 (50, 17 filed) and undecided u01 (30, 4 filed).

**Outcome.** "Filed" means a publishable lifecycle claim from completion (`complete-v*/CLAIMS.publishable.jsonl`), or
a filed undecided-route replacement proposal (`REPLACEMENT_PROPOSAL.jsonl`). This is the unit the stateless gauge
prices. The counts match the wave reports: Papinian 61 decided filed, Bartolus 17 YES filed and 4 undecided adopted.

**Excluded batches.** The recovery batches (Bartolus r01, r02 and s01; Papinian r01 and r01b) take routes Larrey does
not triage, so they are left out.

**Repeated orders.** The 50 Bartolus YES orders are orders Papinian had attempted and mostly failed on. Bartolus
re-ran them on dossiers that by then held the NEA notices and an official EO 13286. They therefore count as separate
attempts on different dossiers, but not as independent orders: 520 distinct orders across 570 attempts.

**Gates.** Every gate was evaluated with the code that is now committed: Llull `GATES` applied to
`kit_features.from_dossier` on the dossier frozen for that attempt. `python3 -I jobs/larrey-triage/strict_backtest.py`
reproduces every number below in about six seconds. The Larrey job now runs it and writes
`output/STRICT_BACKTEST.json`.

**Fitting and checking.** The rule was chosen by looking at all five waves, so no sample is fully held out. As a
partial check, the table reports the Papinian waves (where most of the data is) apart from the later Haloander and
Bartolus waves.

## Back-test

In the tables, "lift" is the filed rate among admitted attempts divided by the rate at the default (hard) level in
the same segment. "Kept" is the share of that segment's filed dossiers the rule still admits.

| Rule | Segment (attempts, filed) | Admitted | Filed among admitted | Rate | Lift | Kept |
|---|---|---:|---:|---:|---:|---:|
| hard (default) | all (570, 91) | 548 | 91 | 16.6% | 1.00 | 100% |
| soft | all | 397 | 90 | 22.7% | 1.36 | 99% |
| soft + no contradicting lead only | all | 339 | 86 | 25.4% | 1.53 | 95% |
| soft + at most 5 events only | all | 330 | 87 | 26.4% | 1.59 | 96% |
| **strict** | **all** | **299** | **83** | **27.8%** | **1.67** | **91%** |
| strict, events at most 3 | all | 255 | 76 | 29.8% | 1.79 | 84% |
| strict, events at most 4 | all | 293 | 82 | 28.0% | 1.69 | 90% |
| strict, events at most 6 | all | 308 | 85 | 27.6% | 1.66 | 93% |
| strict | decided route (420, 78) | 232 | 71 | 30.6% | 1.65 | 91% |
| strict | undecided route (150, 13) | 67 | 12 | 17.9% | 1.76 | 92% |
| strict | Papinian (460, 67) | 240 | 61 | 25.4% | 1.70 | 91% |
| strict | Haloander and Bartolus (110, 24) | 59 | 22 | 37.3% | 1.54 | 92% |
| strict | Bartolus decided, NEA notices held (50, 17) | 34 | 16 | 47.1% | 1.38 | 94% |

The rate barely changes when the event threshold moves from 4 to 6, so the cut at 5 is not finely tuned. A cut at 3
drops below 85% kept. Among the attempts the soft level admits, strict keeps out 98, and 7 of those filed (7%). Among
the 299 it admits, 28% filed.

Eight filed dossiers are lost in total:
- Papinian: EO 14354, 10253, 10431 and 8399, each with a claim-kit conflict; EO 11758 and 8809, with 6 events each.
- Bartolus: YES order EO 12905, with 20 events; undecided order EO 12437, kept out by the existing soft gate for
  later-order text, not by a strict gate.

## Why these two features

Both features measure work the producer and the two review arms must do before a dossier can be filed. They are not
proxies for the answer.

**Contradicting leads.** The Papinian assessments and the Bartolus report say producers stop with "clause
reconciliation not done". The reviewers' rejections are mostly date or citation slips. A provisional-YES order with a
held whole-scope revoking ACT, or with the claim kit's own `PARTIAL_END_CANDIDATE_ON_YES_ORDER` conflict, must be
reconciled clause by clause against that lead before a YES can stand. On the decided route, 1 of 17 such YES
attempts filed, and 4 of 93 attempts with a kit conflict filed.

**Event count.** Each later event in the status history is another change to place and cite. Attempts with no
recorded events filed at 39% on the decided route. Attempts with five or more filed at 4%.

On a NO order, a whole-scope ending ACT is the ending basis, not a contradiction, so the gate ignores it there. An
undecided order has no status to contradict, so the gate does not apply to it ("na").

## Features tried that do not qualify

The other features named in the brief were tested one at a time on top of the soft level. Rates below are for the
decided route unless stated.

**Weak or no signal:**
- **Held-text grade.** The grades that need a page check filed 0 of 14 times on the decided route. Non-original
  grades on the undecided route filed 0 of 27 times, but the hard gate already keeps those out.
- **End-date leads** (a TERM record with a computed end or effective date): no signal.
- **Count of current-law leads** (STATUS_LEADS `current_law_leads`): no clean signal.

**Signal but too costly in lost filings:**
- **OFR catalog note is empty** (`EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT`): filed 40% among admitted,
  but keeps only 51% of filed dossiers.
- **Signed before 1990:** 1.35x lift, keeps 85%, with no mechanism beyond complexity.
- **At most one ACT naming the order, or at most 19 clauses:** about 1.4-1.6x lift, but these overlap the event
  count and are weaker on the later waves.
- **U.S. Code and eCFR citation hits** (the current-law machine searches): 3 or more hits filed 4%. This tracks the
  event count and adds nothing beyond it.

**Not in the frozen dossiers, so not tested:** Cruden and Clark citation counts, family-rule leads and X1 class leads.

## What strict does and does not do

Strict decides no status and changes no count. A kept-out order stays open, and its reason names the strict gate.
Strict is a predictor of how complex an order is, not an input the route requires. It therefore stays experimental,
like the soft gates (Kean F-20261112-soft-gates-untested), until a gated wave measures what it keeps out. Bentham
assumes no yield lift at the strict level, so the plan prices strict-admitted orders at the measured untriaged rate.

**Projected cost (not a measurement).** If cost per attempt stays the same, cost per filed claim scales by the inverse
of the lift. The Papinian agent lane's $4.71 per filed claim (gauge figure) would become about $2.8 at the
back-test's 1.67x, or about $3.4 at the 1.38x seen once NEA notices are held.

**Lower throughput.** Strict admits about half of attempts, against 96% at the default level, so a pool runs dry
sooner. The next triage run reports the strict-admitted counts per route in `REASONS.json` and `TODO.md`.

## What a measured gated wave should test

**Pool.** Run the test on `production.claim_ready.yes.fr`, the largest pool. There the soft gate now binds weakly, so
the strict gates are what is being measured.

**Draw and blinding.** Draw at random from the orders the soft level admits. Assign them to two arms, blind to the
producer and reviewers: orders strict admits, and orders strict keeps out.

**Size.** The Augur stage 0 (the required first stage of one lane and 30 orders) would be 30 strict-admitted orders
plus 15 to 30 strict-excluded ones. The back-test predicts about 28-47% filed against about 7%.

**Measurements:**
- the filed rate in each arm;
- dollars per filed claim in each arm;
- the share of filed dossiers that come from the excluded arm, which is the recall loss measured prospectively.

**Decision rule.** Adopt strict for a pool if the admitted arm's filed rate is at least 1.5 times the excluded arm's,
and the excluded arm contributes at most 15% of filed dossiers. If the excluded arm files at close to the admitted
arm's rate, drop the event-count gate first: it is the more fitted of the two. The rate row of a wave drawn under
strict should be marked `"gated": true` so Bentham does not apply a lift to it twice.

On the undecided route, only 13 filed dossiers exist in the back-test. The strict gates add little there over the
soft gates (1.09x among soft-admitted attempts), so this test says nothing new about that route.

## Changes on branch `claude/larrey-2026-11-25`

- **`jobs/llull/kit_features.py`:**
  - three new features: `conflicts`, `whole_end_acts` (distinct actors with a whole-scope ending ACT) and
    `status_events`;
  - for undecided orders, `status_events` is read from STATUS_LEADS;
  - `ENDING_VERBS` copies the claim kit's `own_text.ENDING_VERBS`, and a test checks the copy.
- **`jobs/llull/llull.py`:** gates `no_contradicting_status_lead` and `status_events_at_most_5`.
- **`jobs/larrey-triage/larrey.py`:**
  - a `strict` tier per route and the `LARREY_LEVEL=strict` setting;
  - `pass_strict` and `missing_strict` in `GATES.jsonl`;
  - output from before the strict tier fails closed at the strict level, and the default is unchanged.
- **`jobs/larrey-triage/strict_backtest.py`** and its run in `job.py`; `needs.txt` adds the Bartolus wave.
- **Tests:** six new tests in `jobs/larrey-triage/test_larrey.py`; 28 pass.
