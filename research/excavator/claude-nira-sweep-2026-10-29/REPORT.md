# NIRA code-approval orders: one shared, reviewed legal analysis in ordinary production (2026-10-29)

Seven batches of executive orders approving, amending or ruling on exemptions from NIRA codes of fair
competition went through the ordinary claim-kit route on 2026-10-29: producer, separate blind reviewer with
planted controls, `kit.py complete`, actual claim checker and tracker replay. Of 132 orders attempted, 91 claims
were independently upheld and filed, and 41 orders were blocked or held with a stated cause. All ten valid
planted controls were caught. Each batch's isolated tracker replay starts from the published 395 ready orders;
the batches share no orders, so their gains add to 486 ready once the canonical checker and tracker regenerate.
Nothing here adopts a status, changes the codebook or certifies anything (certified count: 0).

The batches that used the shared analysis cost far fewer tokens per filed claim than the baseline batch that
did not. The comparison isolates the shared analysis at equal batch size, and quality held: every genuine claim
in both arms that reached completion was upheld, and planted errors were caught at the same rate. The measured
recurring saving per batch is large enough to repay the one-time setup within the remaining eligible
population, as estimated below.

## What the intervention removes

Every NRA code-approval order ends the same way: S.J. Res. 113 section 2 (49 Stat. 375, approved June 14, 1935)
repealed the provisions of NIRA Title I that authorized code approval and code enforcement. Before this work, a
producer working any batch of these orders had to locate the statute, the Act and Schechter among the held
sources, attach them as packet excerpts, decide whether May 27, June 14 or June 16, 1935 is the end, and work
out the residual effects. The baseline producer did exactly this competently, using the existing supplement
route, and reached the same June 14 answer; its own report attributes roughly a third of its time to that
shared work and the route reading.

The intervention does that work once: `SHARED_ANALYSIS.md` (independently reviewed; one planted false
proposition caught, five corrections adopted; `review-shared/`), seven exactly hashed excerpts attached to every
packet by `make_declarations.py`, and producer and reviewer briefs. Reuse of the existing supplement route earns
no credit here; the credit is for not repeating the retrieval and interpretation in every batch, and for
consistent answers across producers. The reviews confirm that individual reviewers can and do reject the shared
answer's application: they rejected two treatment claims that applied the repeal to denials of exemption, which
led to the shared rule on one-time determinations.

## Measured costs (harness transcripts; `COSTS.json` from `costs.py`)

Weighted tokens below are uncached input + 1.25 × cache writes + 0.1 × cache reads + 5 × output, a standard
relative-price weighting; producers are Sonnet 5.5 and reviewers Opus 5.5, so model prices differ further and
are not converted to money. Cache reads dominate every agent's raw count (each call re-reads its context).

| Batch | Orders | Filed | Blocked | Producer W | Reviewer W | W per filed claim |
|---|---:|---:|---:|---:|---:|---:|
| b0 baseline (ordinary route) | 6 | 4 | 2 | 5.94M | 1.07M | 1.75M |
| t3 treatment, matched size | 6 | 5 | 1 | 2.34M | 0.92M | 0.65M |
| t1 design cohort | 24 | 18 | 6 | 6.00M | 3.27M | 0.52M |
| t2 transfer cohort | 24 | 20 | 4 | 3.76M | 1.43M | 0.26M |
| t4 | 24 | 15 | 9 | 1.95M | 1.63M | 0.24M |
| t5 | 24 | 13 | 11 | 2.34M | 1.19M | 0.27M |
| t6 | 24 | 16 | 8 | 2.07M | 1.14M | 0.20M |

**Matched comparison.** At the same batch size and category mix (four approvals, one amendment, one exemption
order), the baseline cost 7.01M and the treatment 3.26M, producer plus reviewer. The baseline also lost about a
quarter of its time to stale-packet re-preparation caused by the coordinator committing in-flight packets
(below); removing that share still leaves the treatment about 45 percent cheaper. The treatment batch was at
least as complex by machine clause count (11 rows against 7).

**Ordinary production with the treatment** (t2, t4, t5, t6, after the design-cohort corrections) averaged 0.24M
weighted tokens per filed claim and 0.16M per attempted order, against 1.75M and 1.17M for the baseline. The
24-order batches also benefit from spreading fixed reading costs, so only the matched comparison isolates the
shared analysis.

**One-time and correction costs.** The shared-analysis review cost 0.40M. The coordinator (Opus 5.5) spent
13.0M weighted tokens in total, mostly investigation, design, the X1 repair, tools and orchestration, with no
reliable split between one-time and recurring work; per batch, the routine coordinator steps are about six
calls. Correction costs that should not recur: the first t1 review (1.25M) was discarded because the
reviewer read a control key stored beside its review set; the t1 denial corrections cost about 1.5M of producer
work; and the baseline's stale-packet loops cost roughly 1.5M.

**Payback (estimate).** If each remaining batch saves what the matched pair saved (2.3M to 3.8M weighted tokens
per batch, the range spanning the stale-packet adjustment), about nine more batches over the 208 statused
orders not yet attempted would save 21M to 34M, against one-time costs no larger than the coordinator's 13M plus
0.4M of review. The saving per 24-order batch has not been measured directly against a 24-order baseline; the
estimate assumes the shared work saved is a per-batch fixed cost, as the baseline producer's report describes.

## Quality

All ten valid planted controls were rejected by blind reviewers (two dates moved to 1936; others recorded
Schechter's May 27, 1935 as the statutory end), and every genuine version of a control order was upheld after
reveal. Genuine rejections, by cause:

- **Missing shared rule (design cohort only):** EO 6242-D and EO 6346 treated a denial of exemption as ending
  with the repeal. The shared analysis now says a denial is exhausted on its date; later batches applied it and
  reviewers upheld it (EO 6274, 6331-A, 6242-E). EO 6346 was corrected and filed; EO 6242-D is held because its
  stay-exception clause needs later orders that are not packet evidence.
- **Producer factual slip:** EO 6346's corrected version first named the wrong code in a source note; fixed and
  upheld.

Blocked and held orders, by cause (41 of 132): conditions, committees, stays or report directions attached to an
approval with no held end (about 20, mostly t5 and t6); no text of the order held (6); a held later order that
decides the end but is not packet evidence (4); a code effective date needed for a "90 days after" condition
and not held (4); custody of a Wayback-only APP capture (EO 6414, 6457, 6467); a live-only APP harvest (EO 6255);
section 4(a) agreements and other outliers. Producers treated attached report directions inconsistently: t2's
were submitted as ending with the repeal and upheld, while t5 and t6 blocked similar clauses.

## Production defects found and repaired

1. **X1 event sources** (`jobs/x1-class-engine/events.py`): the reader saw only source-ladder records, so seven
   of eight held event sources showed as pending. It now reads every job's published source records; GitHub run
   40882610996 published 8 of 8 held with phrases found. Three verification phrases were corrected to the
   printed wording. No other X1 output changed.
2. **Committing in-flight packets stales every packet.** Valla's packet context pins the repository-wide count
   of tracked `RATIONALES.json` packages, and tracked packages include the packet's own sheets. A checkpoint
   commit therefore broke every packet in flight. The packets were untracked and restored; the briefs now say not
   to commit a packet until its batch is completed. The proper fix (exclude the packet's own and unrelated
   packages from the context, and raise the 100-package hard limit, which 76 tracked packages are approaching) was
   refused by the permission layer because it relaxes an integrity check, and needs the owner's approval.
3. **Producer label.** Completion requires the decision sheets' `agent` to equal the packet's preparing agent;
   the briefs now say so. Two batches were relabelled and the exact new versions re-attested by their reviewers.
4. **Control keys.** One reviewer read a key stored beside its review set; keys and seed receipts now stay outside
   every path a reviewer is given until the review is written.
5. **Concurrent completions.** Two completions running at once refuse each other ("input file set changed");
   completions run one at a time.

## Tools added (all in this folder)

`cruden.py` writes per-packet lookups (register and WPA rows, the APP page check, own-text wording signals, held
texts citing the order or naming its code) so producers stop rebuilding search scripts; batches using it (t4-t6)
cost 1.95M to 2.34M per producer against 3.76M for t2, but they also blocked more orders and were told to work
economically, so the saving is not attributed to the tool. `costs.py` turns harness transcripts into the cost
table. `make_completion.py` writes the completion manifest from exact review records. `PRODUCER_PROMPT.md` and
`REVIEWER_PROMPT.md` run a batch with a one-line instruction.

## Limits

The design cohort and the transfer cohort come from the same population; transfer is shown across disjoint
orders, not across order types. All review is same-family (Anthropic, separate contexts); a different-family
check of the shared analysis is prepared (`review-shared/PROPOSITIONS_v2_SOL.md`) but not yet run. Status-gated
NRA orders (155) received no claims. The baseline is a single batch of six.
