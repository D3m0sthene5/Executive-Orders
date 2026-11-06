# Herschel: what all remaining work costs (survey of 2026-11-05)

Herschel measured the remaining work of the project by running a probability sample of 238 orders through every step
each still needs, with instrumented workers, and projecting the measurements onto all 13,641 orders that are not yet
ready for human review. The survey cost about $350 API-equivalent (API list prices for the tokens used, not an
invoice) and ran for 90 minutes on one cloud machine.

**Main result.** Running every remaining agent step now, with the sources the project holds today, would cost about
**$21,200** (80% interval $18,900 to $23,600) and would carry only about **760 orders** (510 to 1,020) through every
step. That is roughly $28 per fully successful order. The reason is that most steps stop on a missing source: 76% of
status steps, 80% of original-text steps and 81% of ending steps ended blocked, each in a few minutes. Running an
agent wave now would mostly pay to rediscover blocks. The cost of the remaining work is set by source acquisition,
two claim-kit gaps and human certification, not by agent tokens.

**Human certification is the largest remaining cost.** An Opus reader estimated a careful human
check of six ready dossiers at 8 to 142 minutes each, mean 50 minutes (200 words a minute plus time to open each
source page; all 65 quotations matched the held bytes). Over all 14,972 orders that is about **12,400 hours**, about
six working years for one full-time reader. This rests on six dossiers and an estimated, not measured, reading speed.

## How the survey worked

- **Census.** `census.py` listed every open order-step from committed files: 96,598 cells over 14,972 orders, in 14
  strata by provisional status (yes, no, none) and era. It costs no tokens.
- **Two independent samples.** Round 1 drew 153 orders (Neyman allocation: more orders where more work is expected);
  round 2 (`replicate.py`) drew 85 more with a new seed from the orders round 1 did not take. Six Opus coordinators
  (H1 to H6) took every sampled order through every open step, one step per Sonnet worker, two blind Opus reviewers
  with planted controls (deliberately wrong items that a reviewer must reject) for every proposal or claim.
- **Projection.** `project.py` scales each stratum's measured costs and outcomes by the number of census orders the
  stratum holds (a stratified Horvitz-Thompson estimate) and gives 80% intervals from 2,000 bootstrap resamples. The
  two rounds give independent estimates: **$20,500 from round 1 and $22,300 from round 2**, which agree within the
  interval. All 238 orders were reached at every open step, so no order is missing from the estimate.

## What the sample produced

Seven lifecycle claims filed (EO 799, 5930, 10863, 12598 from H2; 11320 and 12724 from H4; 649 from H5), one
replacement proposal (EO 12720), and reviewed status proposals that wait for owner adoption (`H*/` folders). Every
planted control in all six coordinators was caught by both blind reviewers: 0 misses. No status, codebook entry,
census row or certified count changed. Certified: 0.

## Success rates by step (projected over the census)

| Step | Open cells | Succeeded | Blocked | Failed or rejected |
|---|---:|---:|---:|---:|
| Provisional status (undecided orders) | 10,681 | 24% | 76% | 0% |
| Original text | 6,228 | 21% | 79% | 0% |
| Replace a transcription with an official original | 1,359 | 9% | 91% | 0% |
| Clause inventory | 13,573 | 41% | 59% | 0% |
| Ending or current basis | 13,618 | 19% | 81% | 0% |
| Savings and residuals | 13,585 | 20% | 80% | 0% |
| Counterevidence | 12,116 | 29% | 70% | 1% |
| Claim review (both reviewers uphold) | | 17% | 65% | 18% |

## What blocks the work

Projected orders blocked by each kind of missing input (`ATLAS/BLOCKERS.csv`). "Sole" counts orders for which that
input is the only root blocker, so acquiring it alone would let the order's agent steps run (they can still fail on
the merits).

| Missing input | Orders blocked | Sole blocker | Who can fix it |
|---|---:|---:|---|
| Official printing or page image of the order | 5,313 | 1,234 | source jobs (Tischendorf, NARA, GPO, ProQuest page checks) |
| Agency execution records (appointments, land status, board reports) | 3,944 | 802 | archival acquisition |
| Later law, notice or instrument for the ending | 3,011 | 1,814 | source jobs (current-law, NEA notices in PR #155) |
| Source held only as a hash; its bytes were never retained | 2,867 | 852 | `jobs/ptolemy-custody` keeps them on GitHub Actions, no tokens |
| No dated status history (claim kit refuses the order) | 5,918 of 10,681 undecided, census count | | an owner rule (ask A-20261105-1) |
| No machine later-source search for undecided dossiers | 865 | 738 | `jobs/claim-drafts` now drafts undecided orders |

Two of these have a single cause in the census, not only in the sample. **Machine later-source searches:** the claim
kit's undecided route takes each order's searches from its draft, and `jobs/claim-drafts` drafted only decided orders,
so all 10,681 undecided orders reached overlay assembly with none. The job now drafts undecided orders too; a local
draft of EO 11460, 3865 and 10773 carries the U.S. Code, eCFR and Federal Register catalog searches (the catalog with
its pre-1937 coverage warning). **Hash-only sources:** 11,285 cited sources have a recorded hash and text but no kept
bytes; `jobs/ptolemy-custody` re-reads 8,386 APP pages from their archive captures and re-downloads 2,899 stable files,
keeping each only if it hashes exactly as recorded.

Coordinators H4 and H5 also recorded 545 projected orders as blocked by the claim kit's rule that status overlays are
written only under `jobs/claim-kit/output/overlays` or `research/excavator`. That rule stopped the survey only because
the survey confined its coordinators to `research/herschel`; an ordinary wave writes under `research/excavator`, so
those orders have no tool blocker of their own and are counted in the other rows.

The status-history gap is a census count, not a sample estimate: `jobs/status-history` compiles dated histories from
the 1989 Office of the Federal Register disposition tables, which do not reach most pre-1937 orders. Of the 5,918
orders without one, 5,449 are from 1907 to 1936 and 427 are older; only 191 have any held later-event edge. The WPA
Historical Records Survey list of orders 1 to 8030 (1944), already held in `jobs/x1-class-engine/data/`, does not
fill it: its entries name an earlier order as amended or revoked 212 times, reaching only 111 of the 5,918. Most
pre-1937 orders were never expressly revoked, so a dated history for them would have to rest on the order's own
terms and a bounded search that found no later event. Whether the claim kit may start an order on that basis is an
evidence rule for the owner (ask A-20261105-1).

## Cost once an order is unblocked

The 15 sampled orders whose every open step succeeded cost **$3.92 each** (80% interval $3.38 to $4.44) including
review and coordination. If every open order became workable and behaved like them, the agent work would cost about
$53,000. That figure is a rough ceiling, not a forecast: it rests on 15 orders, mostly from the 1907-36 strata, and
many orders will never be unblocked.

## Cost by kind of work (attempting everything now)

| Kind of work | Projected cost |
|---|---:|
| Lifecycle steps (clause inventory, ending, savings, counterevidence) | $4,100 |
| Blind review with planted controls | $5,700 |
| Provisional status | $1,600 |
| Original text, replacement and media refetch | $600 |
| Coordination (Opus coordinators) | $9,200 |
| **Total** | **$21,200** |

Coordination was 43% of the cost. Each coordinator built its own launcher, prompts and checks, so a production wave
that reuses `research/herschel/H*/tools/` should spend far less on coordination.

## Time and limits

No worker or coordinator met an API rate limit, usage limit or overload. The binding limit was the machine: one
cloud session has 8 GB of memory and 2 processors, and about 20 simultaneous workers exhausted it (between 23:51 and
23:58 UTC the kernel killed about two dozen workers; all were re-run and their first attempts counted). After a shared guard capped the machine
at 18 workers, no further worker was killed. The survey handled 158 orders an hour on one machine, so attempting the
whole census at today's block rates would take about 3.6 days on one machine. Unblocked steps take longer, so faster
work needs more machines (GitHub Actions runners), not a larger plan.

## Limits of this survey

- 238 orders over 14 strata. Small strata (3 to 9 sampled orders) have wide uncertainty that the bootstrap only
  partly captures.
- Some blocks are wrong. H1's reviewers rejected 10 status blocks because held evidence was enough (for example EO
  4065 strikes EO 2112), so block rates may be overstated and success rates understated.
- One step per worker repeats context loading, so per-step costs are an upper bound on a combined claim-kit run.
- Reading-time estimates for certification are an AI's estimate from word counts, not timed human readings.
- API-equivalent dollars are not a share of a plan's week. Run `jobs/bentham/bentham.py calibrate` with the owner's
  weekly usage figure to convert them.

## Files

`census.py`, `replicate.py`, `project.py` (tests in `test_project.py`); `frame/` (sample and assignments);
`H1/` to `H6/` (traces, outcomes, batches, gates, telemetry, logs); `ATLAS/` (PROJECTION.json, BY_STEP.csv,
BY_COST_GROUP.csv, BY_STRATUM.csv, BLOCKERS.csv, ACQUISITIONS.csv, CONCURRENCY.csv, ORDERS_MEASURED.csv);
`telemetry/` (integrator and coordinator usage). Regenerate with `python3 -I research/herschel/project.py`.
