# Erasmus resubmission and Geddes upgrade, 2026-11-02

Named for Erasmus of Rotterdam, who corrected his Greek New Testament through five editions. This run reworked
the 40 claims that Apollo's blind reviewers rejected and the 20 filed Apollo claims that Geddes showed to have
source discrepancies. It filed **52 claims**: 32 recovered rejects, which are new lifecycle claims, and 20
corrections that supersede the flawed Apollo versions. The run also wired Geddes into the claim-kit route and
extended its checks.

Every filed claim passed the actual claim-checker, a blind separate-context Opus review with a planted control,
and `kit.py complete`. **10 of 10 planted controls were caught.** No claim is a human certification, and the
certified count stays at 0.

## Results

| | Orders | Filed | Not filed, and why |
|---|---|---|---|
| Apollo rejects (r1–r4, then e3) | 40 | 32 | 7 blocked by producers, 1 dropped at completion (listed below) |
| Corrections of the 18 flagged filed claims (c1, c2, e1) | 18 | 18 | none |
| New Geddes v2 finds on filed claims (e1, e2) | 3 | 2 | EO 11303 |

These rejects were not filed:

- **EO 6204A:** the Cotton Textile approval with its four-month condition is not held.
- **EO 8129 and 8163:** Public Land Order 1704 and Proclamation 2416 have no evidence ids in the packet.
- **EO 9949:** EO 10804 has no evidence id in the packet.
- **EO 11026:** EO 11029 is not citable from the dossier.
- **EO 11343 and 12095:** the board reports are held only as `held_text_lead` text, which the kit refuses as a
  source.
- **EO 12891:** dropped at completion because the EO 13062 PDF bytes are not held.

Two corrections were rejected the first time in Erasmus review: EO 6811 and 7000 cited "EO 6444" for EO 6444-A.
They were fixed and filed in the e1 fix round.

The EO 11303 correction was rejected after reveal and is blocked. Its claim calls the waiver "exhausted" while
adopting the 1986 revocation as the end; under the 2026-10-28 ruling, exhaustion would put the end at 1966-09-12.
The Apollo-filed EO 11303 claim therefore still stands, with this open question and the unmentioned EO 10804.

Blind review rejected 5 of 58 genuine Erasmus claims (8.6%), against 40 of 300 in Apollo (13.3%). Producers
saw every earlier defect, so this is a resubmission rate, not a like-for-like comparison.

## Geddes changes

- **Wiring.** `kit.py batch-check` now runs Geddes on every applied directory. It writes `GEDDES_LINT.json` and
  adds a summary to the batch-check result. A Geddes failure is recorded and never fails the check. The new
  `--geddes-strict` option fails the check until every flag has an answer in `GEDDES_RESOLUTIONS.json`, which
  `geddes.py gate` checks.
- **Stable flag ids.** Each flag carries a deterministic `flag_id`. The lint output records its runtime and the
  files it read.
- **New checks** (`consistency_checks.py`, `citing_checks.py`), added in two rounds:
  - stated end dates and year bounds checked against the claim's own end;
  - entity-type and count words (for example "airline" against "railroad", or one dispute against several)
    checked against the order;
  - statute sections the order supposedly cites;
  - "only a transcription" claims checked against dossier grades;
  - held orders that revoke a parent order but go unmentioned;
  - held board reports when the claim says none is held;
  - later renamings of a name the order creates;
  - a number whose stated date belongs to a lettered sibling (6444 against 6444-A);
  - malformed or mismatched sha256 values;
  - "no hit" search claims checked against retained search outputs.
- **Cost tools.** `telemetry.py` extracts per-agent tokens and time from a roster. `geddes.py cost --compare`
  compares a run against a baseline per filed claim.
- **Slim view.** It gained the gaps producers reported: machine searches with hit counts, citable later-event
  evidence ids, clause reasons and the current claim as a draft. Long claim strings are trimmed unless
  `--full-claim` is given. A view for one order of a 24-order packet is now 68–117 KB, against an estimated
  1.07 MB for the full packet.
- **Supplement fix.** `jobs/claim-kit/source_supplement.py` now carries a parent packet's replacement routing
  into its supplement. Before this, correcting a filed NRA claim was impossible. Its 17 tests pass.

### How well Geddes performs

On the Apollo development set, recall on the 40 review defects rose from 20 to 35. Flags on the 254 filed claims
rose from 18 to 24, and every new filed flag was checked against the source and found real. The evidence is in
`research/excavator/claude-geddes-v2-2026-11-02/EVALUATION.json`. These are known defects, so the figures are not
held-out validation.

Live in Erasmus, the producer-time lint (v1 and early v2) flagged none of the 5 genuine defects that blind review
later found. Geddes now flags 4 of the 5: EO 6811, 7000, 11436 and 12121. Each of those checks was added after the
miss was shown to the builder. It still misses the "exhausted" wording in EO 11303. It raised no flag on any of
the 52 filed Erasmus claims.

Producers and Geddes together removed the earlier error classes from this run's output: no template carry-over,
no quotation mismatch and no wrong FR page reached the reviewers. Apart from the planted controls, the only
defects reviewers found were the five above.

## Cost (`TELEMETRY.csv`, `COST_COMPARE.json`)

The slim view did **not** reduce cost per order in this run. The c1 producer (Sonnet, 17 NRA orders) used 716,564
cache-read tokens per order, against 516,154 for Apollo's Sonnet NRA producers. Resubmission adds work per order:
reading the brief, the prior claim and the review defects. So this does not isolate the view's effect.

What the data does show clearly is a large fixed cost per agent. The one-order c2 producer read 5.2 million cached
tokens, and the one- and two-order fix producers read 1.5–2.5 million per order. Batching more orders per agent is
the largest cost lever available. Small fix batches are expensive.

Erasmus used 27 agents in total: 9 producers, 9 reviewers and 2 builders, plus resumptions. Totals:

| Role and model | Agents | Output tokens | Cache-read tokens | Active seconds |
|---|---|---|---|---|
| Producers, Opus | 6 | 376,129 | 80.0 M | 4,987 |
| Producers, Sonnet | 3 | 145,882 | 23.4 M | 1,520 |
| Reviewers, Opus | 9 | 220,296 | 48.3 M | 3,125 |
| Builders (Opus and Sonnet) | 2 | 184,416 | 31.0 M | 3,478 |

The view gained the missing pieces producers reported, so the next run can test it on a fresh lot rather than on
resubmissions.

## Open items

- **Filed Apollo claims Geddes still flags:**
  - EO 11547, 11646 and 12060: "no hit" U.S. Code claims contradicted by retained Code notes.
  - EO 11303: exhaustion wording, and EO 10804 unmentioned.
- **Two search-tool limits** reported by reviewers:
  - The by-number scan needs an "Executive Order" prefix, so it misses EO 12553's table of bare numbers.
  - Board reports graded `held_text_lead` cannot be cited, which blocks report-deadline claims (EO 11343 and
    12095).
- **Missing evidence ids.** Packets lack ids for many held later orders, so producers can only describe those
  orders in reasoning, not record them in `later_events`. This was reported for 6513-I, 6885-A, 6925-A, 6731-A,
  6878, 6930, 7018 and 6948-A.

## Files

- `<batch>/packet[/supp]/`: the frozen packet, `ERASMUS_BRIEF.json` (the exact defects given to the producer),
  `views/`, producer CSVs and report, `applied-v*` with `GEDDES_LINT.json`, `reviews/` (blind and after-reveal),
  `completion/` and `complete-v1/`. `TRACKER_CLAIMS.jsonl` is gzipped.
- `tools/`: the coordinator scripts, the prompts given to producers and builders, and `batches.json`.
- `briefs/`: the defect briefs.
- `ROSTER.csv`, `TELEMETRY.csv` and `.json`, `FILED.json`, `COST_COMPARE.json`.
