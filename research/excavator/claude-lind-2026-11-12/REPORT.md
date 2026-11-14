# Lind stage 0, 2026-11-12: does the repaired workflow produce ready dossiers, and are soft-filtered orders worth processing?

Owner-approved pilot (Kean A-20261112-lind-stage0-v2; plan `research/lind/stage0/WAVE.json`, sha256 f2b07a19…, Augur
PASS). Named for James Lind's 1747 comparison of remedies on matched sailors. Human-certified count: 0.

## Design (as approved)

- **Draw:** 30 never-attempted undecided orders, drawn at random on main's fresh triage of 2026-11-12T20:51Z
  (`DRAW.json`):
  - 15 from the 3,447 that pass every Larrey gate;
  - 15 from the 1,834 that pass only the hard gates.
- **Configuration:**
  - two Sonnet 5.5 producers, one per mixed 15-order packet;
  - one Opus 5.5 status reviewer;
  - one pooled blind review set of 7 claims with 1 planted control, reviewed by two fresh Opus 5.5 arms;
  - the both-uphold rule;
  - `kit.py complete` with the actual claim checker.
- **Blinding:** producers and reviewers never saw which group an order was in. The key was held outside the repository.

## Results, by group

| | All gates (15) | Hard gates only (15) |
|---|---:|---:|
| Dispatch-blocked (a mandatory source not held) | 2 | 5 |
| Blocked by the producer (precise missing source recorded) | 6 | 9 |
| Status decision filled and accepted by the status reviewer | 7 | 1 |
| Lifecycle claim submitted to blind review | 6 (one used as the control) | 1 |
| Upheld by both blind arms | 1 (EO 12753) | 0 |
| **Ready (6/6)** | **0** | **0** |

- **EO 12753** was upheld by both arms but failed the actual checker at completion. Its ending source is held only as
  a hash (`custody_record_only`, `ending_or_current_basis`). The dispatch check covers only mandatory sources, so it
  did not see this.
- **Arm splits,** adjudicated by the coordinator against the claim text. In each, the rejecting arm found a real
  defect:
  - EO 12437 claims a search found no other citation, while its own previous sentence cites the 42 U.S.C. 8373 note;
  - EO 11294's clause dates contradict its own reasoning about section 4;
  - EO 11943's statement of the EO 12010 effective date is imprecise.
- **Rejected by both arms** for factual errors in the reasoning:
  - EO 12701 names the wrong body for EO 12334;
  - EO 13476 gives a wrong scope count.
- **Control:** the planted EO 9447 was caught by both arms. After reveal, arm A rejected the genuine version (an
  ending quote not narrowed, and the amending command treated as continuing) and arm B upheld it, so it does not file.
- **Status reviews:** all 8 decisions were accepted. Every status is NO.

## Decision (pre-set rule)

a = 0 and h = 0, so the result is **unsuccessful** (a + h ≤ 1):
- no stage 1;
- diagnose the 30 at zero production cost before any further undecided spending.

Nothing was filed or adopted, so no owner adoption decision is needed.

What the result does and does not show (n = 15 per group; a pilot, not a population estimate):
- **The soft gates separated the groups in this sample:**
  - dispatch-blocked: 5 of 15 hard-only vs 2 of 15 all-gates;
  - submissions: 1 vs 6.

  No hard-only order reached any upheld stage. That is evidence against processing hard-only orders now. It does not
  establish their yield.
- **The repaired kit's records are used:**
  - 4 of 8 accepted statuses rest on OWN_TEXT/PARENT_END records added by the merged fixes;
  - the limiting failures were source custody (1), claim-writing errors that review caught (5), and missing sources
    (22 blocks).

## Cost (Bentham usage, `telemetry/`, list-price allowance; cash $0)

| | USD |
|---|---:|
| Producers (Sonnet 5.5, 2) | 5.79 |
| Status reviewer + two blind arms incl. after-reveal (Opus 5.5) | 7.12 |
| Coordinator (Opus 5.5: setup, preparation, adjudication, reporting) | 10.16 |
| **Total** | **23.07** (cap 35) |

- **Coordinator rule breached:** $0.34 per attempt, against the stop rule's $0.25 and Papinian's lean $0.109. Production
  had already finished when it was measured.
- **Producer cost:** $0.19 per attempt, matching Papinian's $0.201.
- **Not included:** owner minutes (one approval, one merge); runner minutes for the rebuilds.
- **Dollars per ready:** undefined (0 ready).

## Correctable without new production

- **EO 12753:** retain the bytes of its ending source (FR 1991 PDF), then re-complete. This is a custody step, not
  research.
- **EO 12701, 13476, 12437, 11294, 11943:** narrow text corrections of the defects named above, then a fresh blind
  review.

Either path needs a new owner approval. Neither is a stage 1.
