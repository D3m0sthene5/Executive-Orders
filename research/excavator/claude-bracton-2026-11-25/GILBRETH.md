# Gilbreth: where tokens, dollars and time went in wave Bracton and the Junto lean trial

Gilbreth is a measurement probe, named for Frank and Lillian Gilbreth, whose time-and-motion studies split work into
measured steps so that wasted steps could be cut. It did no legal research, reviewed nothing and changed no claim.

This report covers every producer packet that handed back: Bracton c01-c11 on the correction route (re-work of
Claude's own filed claims that had one open step), Bracton PC packets p02 and p04, and Junto lean-trial packets
arm0/a01-a03 and arm1/b01-b02 on the claim-ready YES route. Together they hold 161 orders. It also covers 13 blind
review batches (c07-c10, o0, o1, p02, p04, a01-a03, b01, b02), the Olney scripted board route, the 8 claims the trial
filed, the 9 Bracton replacement proposals that await owner adoption, and the re-preparation of 20 upheld claims.
c12, s01 and the coordinator are not covered. The snapshot was taken at 2026-11-25T10:53Z.

Each number is marked **measured** (read from a file, ledger, transcript or timestamp), **estimated** (computed with a
stated model) or **inferred** (allocated or deduced).

## 1. Summary

The wave's workers cost about 107 USD at list price (estimated; coordinator not measured): producers 43.9, reviewers
52.6, the Olney builder 7.3 and this probe 2.8. Blind review upheld 24 claims in both arms (measured). The trial filed 8
and Bracton proposed 9 (measured), which comes to about 6.3 USD of worker cost per filed or proposed claim (estimated).

Four results matter most for the next wave.

- On the correction route, producers spent about 70% of their estimated dollars on orders that a zero-token rule on
  the kit's own pre-dispatch data marks as unfileable. The rule flagged 66 of the 79 correction-route blocks and none
  of the 9 correction-route submissions.
- Reviewer cost per claim falls from about 1.24 USD in a one-claim session to about 0.45 USD in a seven-claim session
  (estimated). A session costs about 125,000 final-context tokens before it reviews anything (inferred from a fit
  over 23 sessions). Thirteen of the 23 sessions reviewed one or two claims.
- Every Claude Code session starts with a 46,099-token prompt (system prompt plus tool definitions; measured in both
  PC transcripts). That prompt is about 16% of a producer's measured dollars, and an estimated 20-39% of a reviewer's.
- The coordinator's sparse checkout caused two kinds of waste: 9 NEA blocks in a02 and a03, and a 33-minute
  re-preparation of 20 upheld claims that changed no claim content (measured).

## 2. How it was measured

`jobs/gilbreth/gilbreth.py` (standard library only, under 1 s, no model tokens, deterministic) reads each packet's
`DISPATCH_CHECK.json`, `PREPARE.json`, views, `LOOKUPS.md`, `decisions.csv`, `ASSESSMENT.jsonl`, `applied-vN/` folders,
`PRODUCER_REPORT.md` and `reviews/`, together with the prep logs, prompts and review sets in `/home/claude/*-scr/`, the
worker ledgers, the PC ledger `LANES.csv`, the two PC transcripts, `jobs/olney-board-route/output/RESULT.json`,
`/home/claude/junto-scr/REFRESH_RESULT.json`, the filed claim files and the replacement proposals. It writes
`jobs/gilbreth/output/MEASURES.json` and one CSV per packet in `jobs/gilbreth/output/packets/`. Command:

    python3 -I jobs/gilbreth/gilbreth.py --transcripts <transcripts dir> --pc-lanes <LANES.csv>

Dollars follow one chain of methods.

1. **Measured.** The two PC transcripts are priced call by call with the method of
   `research/excavator/claude-bartolus-2026-11-24/tools/cost.py` (last usage per message id; `PRICES.json` list
   rates). p02 cost 3.89 USD over 107 calls, and p04 3.08 USD over 86 calls.
2. **Estimated.** The ledgers record only each session's final context and tool uses. The Bartolus cost model assumes
   calls = tool uses + 1, half the final context re-read per call, the final context written once, and 800 output
   tokens per call. For the same two sessions it gives 3.37 and 2.74 USD. The measured cost is 1.153 and 1.125 times
   that, because output averaged 987 and 1,034 tokens per call, not 800.
3. **Estimated, calibrated.** Every cloud session is priced with the Bartolus model times 1.139, the mean of those two
   ratios. The factor is measured on Sonnet producers only; applying it to Opus reviewers is inferred.
4. **Inferred.** When a resumed session appears in the ledger again under the same agent id, the later row replaces
   the earlier one if its tool uses and milliseconds are not smaller (the ledger then holds running totals).
   Otherwise its cost is added as a separate pass. Two passes have no usage (c10-pass2 and arm0/a01-pass3), so those
   packets are understated.
5. **Inferred.** Tokens and dollars per order split a session evenly over its assigned orders.

## 3. Producer stage

### 3.1 Outcomes and cost

Of 161 orders, producers submitted 32, blocked 100 and left 18 unresolved; the kit dispatch-blocked 11 (measured).
Producer sessions cost 43.9 USD (estimated, calibrated; the PC pair is measured).

| Group | Assigned | Submitted | Upheld by both reviewers | Producer USD | Review USD | USD per upheld |
|---|---:|---:|---:|---:|---:|---:|
| Bracton correction c01-c11 | 88 | 9 | 3 | 19.13 | 13.63 | 10.92 |
| Bracton PC p02, p04 | 18 | 5 | 4 | 6.97 (measured) | 6.36 | 3.33 |
| Trial arm 0 (a01-a03) | 29 | 12 | 6 | 10.24 | 16.86 | 5.42 per filed (5 filed) |
| Trial arm 1 (b01-b02) | 15 | 6 | 3 | 7.56 | 7.53 | 5.03 per filed (3 filed) |
| Olney scripted (o0, o1) | 12 selected | 11 checker-passing | 8 | 0 | 8.25 | 1.03 (1.94 with the one-time build) |

Counts are measured; dollars are estimated unless marked. Of the trial's upheld claims, EO:12146 was not filed
because the refreshed claim kept 6 `too_short_to_verify` items. The c10 pair was upheld but has no replacement
proposal yet (measured).

### 3.2 Where a producer session's dollars go (PC transcripts, measured)

The growth of the prompt after each call is charged to that call's tool results, and the cost of re-reading those
tokens on every later call is attributed to them (estimated attribution on measured usage).

| Part of a producer session | p02 share of USD | p04 share of USD |
|---|---:|---:|
| Output tokens, including thinking | 27% | 29% |
| First-call prompt (46,099 tokens of system prompt and tool definitions), re-read on every call | 16% | 16% |
| Held order texts and source records read through tools | 17% | 11% |
| Views | 16% | 14% |
| Other shell work (scripts, greps) | 13% | 14% |
| Fixed reading list (steps 1-4 of the prompt) | 4% | 4% |
| The producer prompt file | 3% | 3% |
| LOOKUPS.md | 1% | 4% |
| `kit apply`, `batch-check`, Geddes output | under 1% | under 1% |

The fixed reading list and the prompt file together are 7% of a producer's dollars (measured). The 46,099-token
starting prompt, which no project file controls, costs twice as much. The tool definitions and system prompt are the
same for every session, so the reviewer share follows from each reviewer's call count: 20-39% (estimated with the
same 46,099 tokens, which assumes the reviewers ran under the same harness).

### 3.3 Wall time

| Phase | Cloud correction packets | Cloud YES packets | PC packets | Basis |
|---|---|---|---|---|
| Prep | 23-33 s | 30-57 s | not logged | measured |
| Wait from prep done to launch | 333-410 s (c01-c04) | 49-186 s | not logged | measured |
| Producer session | 108-796 s | 911-1,541 s | 1,233-1,286 s | measured |
| `kit apply` plus `batch-check` | 3-16% of the session | 7-20% | 343 s and 360 s, 27-29% | cloud from file mtimes, PC from tool timestamps |

Repair rounds: correction packets needed 1-3 applied rounds, the YES packets 2-8 (a01 reached applied-v8), and the PC
packets 2 (measured). The visible causes are an apply-only first round (no batch-check output) in several packets, a
too-short quote (a02), Geddes flags, and one round with byte-identical claims (a03). Several rounds were written after
the worker's ledger end time, so their cost is unrecorded (measured mtimes).

## 4. Blocks and the zero-token pre-screen

### 4.1 Block taxonomy

Each blocker text is grouped by a fixed pattern list (in the script; first match wins). Dollars are the Bartolus
estimate before calibration, allocated evenly per order (inferred). The finished packets' producer total on the same
basis is 37.5 USD.

| Kind of missing source | Orders | Est. USD on them | Share of producer USD |
|---|---:|---:|---:|
| NMB emergency-board report PDF held only as a custody record (text held, bytes not) | 56 | 9.43 | 25% |
| Source held in the repository but not registered in the packet catalogue ("source supplement needed") | 15 | 3.96 | 11% |
| Commission or committee report or transmittal date | 14 | 2.96 | 8% |
| Statute text | 8 | 3.30 | 9% |
| NEA continuation notices | 9 | 2.70 | 7% |
| Current CFR text; task performance records; parent-order text; FR page images; a proclamation | 11 | 3.34 | 9% |
| Other | 5 | 1.63 | 4% |
| Order's own FR original held only as a custody record (dispatch-blocked) | 11 | 0 | 0% |

Blocked and unresolved orders absorbed 27.3 of 37.5 USD, or 73% of producer spend (inferred).

The second row needs no new acquisition. Producers named statutes, later orders and Public Papers pages that are
already held (for example, Pub. L. 94-455 sec. 1202 at a source-ladder text for c06's EO 11206 and EO 11213), but that
prepare had not registered as citable evidence, so the producer had to block.

The NEA row is an environment defect. `DISPATCH_CHECK.json` reported the notices as held, but the files under
`jobs/selden-fr-citers/output/texts/` were written at 09:11:46Z, after the a02 and a03 producers started at 08:55:18Z
(measured). The a03 producer then found the notices graded `acceptable_as_original: false`, so materializing the files
would not by itself have made those orders fileable (inferred).

### 4.2 Pre-screen rules

Rules were scored on data each packet had before any producer ran. An "event source" is a source, other than the
order's own text or a Presidency Project mirror of it, that could show an actual event such as a report, a completed
task or an expiry.

| Rule | Blocks predicted (of 118) | NMB group (of 56) | Submissions flagged (of 32) |
|---|---:|---:|---:|
| R3: needs an actual-event fact, and no event source has held bytes | 84 (71%) | 56 | 4: EO:10717, 11858, 11990, 12146 (all YES route, a01) |
| R3r: R3 on the correction route only | 66 of 79 correction blocks (84%) | 56 | 0 of 9 correction submissions |
| R1: R3, and at least one custody-only event lead exists | 55 (47%) | 50 | 1 (EO:12146) |
| R2: needs a current-law predicate, and no `CURRENT:` source has held bytes | 27 (23%) | 0 | 21 |

All counts are measured. Two of R3's four YES-route false flags were upheld by both reviewers, EO:11990 (filed) and
EO:12146. So on the YES route R3 would have held back 2 of the wave's 24 upheld claims, and it should not be used there.
On the correction route, R3r flagged none of the 9 submissions or 3 upheld claims. Nine is a small sample: zero in 9
is consistent with a true false-flag rate up to about 28% (one-sided 95%, estimated).

R1 was registered in the first pass before 25 orders finished. 24 of those have now finished: 23 ended blocked,
unresolved or dispatch-blocked, and 1 (EO:12146) was submitted and upheld (measured, out of sample).

### 4.3 Shared-source leverage

No single document unlocks more than one order. Each NMB block needs its own board report (PEB-066 to PEB-134 and
others; measured). The leverage is per acquisition class (measured counts; whether each order then files is
inferred):

1. Commit the bytes of the source-ladder NMB report PDFs and register them in `SOURCES.jsonl`: 56 finished blocks,
   and 53 prepared members whose only event leads are custody-only NMB PDFs. Olney's exception list shows the next
   limit: 37 board orders have an unreadable or unlocated letter date and 29 a report date that is not corroborated.
2. Register already-held sources in the packet catalogue at prep: 15 blocks.
3. NEA notices with a checker-acceptable grade: 9 blocks.

## 5. Review stage

Thirteen batches put 40 claims before two blind Opus reviewers, with 13 planted controls (claims whose dates were
shifted on purpose to test the reviewers). All measured:

- **Controls.** Every arm session caught its control (26 of 26). Of the 40 blind rejections, 26 (65%) were planted
  controls and 14 were defects in genuine claims. Genuine defects included missing extension orders in later-event
  chains (three Olney o1 claims, rejected by arm A only), wrong first-end reasoning, and date or citation slips.
- **Agreement.** The two arms disagreed on 8 of the 36 claims both reviewed (22%): c08 (2), o1 (3), a01 (1) and
  a02 (2). Under the both-must-uphold rule, every disagreement became a rejection.
- **Cost.** Review cost 52.6 USD (estimated), about 2.19 USD per claim upheld by both. That is 49% of the wave's
  measured worker spend, and in arm 0 review cost more than production (16.86 against 10.24 USD).
- **Fixed overhead per session (inferred fit over 23 sessions).** A session is about 125,000 final-context tokens
  plus about 14,300 per claim. Mean cost per claim falls as sets grow (estimated):

| Claims in set | Sessions | Mean final-context tokens | Est. USD per claim |
|---:|---:|---:|---:|
| 1 | 6 | 121,238 | 1.24 |
| 2 | 7 | 166,546 | 1.03 |
| 4 | 5 | 193,219 | 0.62 |
| 7 | 4 | 213,808 | 0.45 |

**Sequential review in arm 1.** When arm A rejected a genuine claim, arm B skipped it (measured: 2 claims, one each in
b01 and b02). By the fit, that saved about 28,600 tokens, roughly 0.4 USD (estimated). The larger difference between
the arms is set size: arm 1's B sessions reviewed 1 and 3 claims where its A sessions reviewed 2 and 4.

**Arm 0 against arm 1.** Arm 0 cost 27.10 USD for 5 filed claims (5.42 per filed) and arm 1 cost 15.10 USD for 3
filed claims (5.03 per filed) (estimated). The ratio is 0.93, above the `after <= 0.9 x before` bar that `jobs/junto`
requires, so the lean arm shows no verified saving. The samples are also small, arm 0 is understated by the unpriced
a01-pass3, and arm 1 lost b03 to a prepare failure (Larrey triage held 9 of its 10 orders), which halved its
attempted count. Filed per attempted order is 17% in arm 0 and 20% in arm 1 (measured).

## 6. Scripted route (Olney) against the producer route

Olney selected 12 of the 117 board orders. It prepared all 12, and 11 passed the checker with 0 model tokens and
172 s of scripted wall time (measured). Review upheld 8 (7 of 7 in o0, 1 of 3 genuine claims in o1). That is about
1.03 USD per upheld claim for review alone, and 1.94 USD including the one-time builder session (7.25 USD)
(estimated). The producer route cost 3.33 (PC), 5.03-5.42 (trial) and 10.92 (Bracton correction) USD per upheld or
filed claim (estimated). The scripted route is therefore 3-10 times cheaper where it applies. It applies to 12 of the
117 orders: the other 105 are exceptions, led by unreadable letter dates (37) and uncorroborated report dates (29)
(measured). The o1 rejections show a defect class a script can repeat across a batch: a later-event chain that
records only the cleanup revocation and misses extension orders.

## 7. Cost of the sparse-checkout defect

Twenty upheld claims had to be re-prepared because the coordinator's sparse checkout had left their packets stale.
All 20 came back `hash_only`: no content changed, 12 were byte-identical, and the 8 Olney claims differed only in
`claim_kit.dossier_sha256`. Nineteen passed the checker (EO:12146 kept 6 earlier `too_short_to_verify` items). The
refresh took 11 refreshed packets and 1,996 s (33 minutes) between the first and last refresh file, of which 63 s was
logged apply and batch-check time. It spent 0 model tokens in scripts (measured). The coordinator wrote 13.9 KB of
refresh tooling, a floor of about 0.07 USD in output tokens (estimated); its reasoning tokens are not measured. The
same defect caused the 9 NEA blocks in a02 and a03, which carried about 2.70 USD of producer spend (inferred), and it
delayed every trial filing by at least the 33 minutes.

## 8. Ranked cuts

Each cut gives its measured share, the evidence, the risk to quality and a two-arm test in the `jobs/junto` form: two
matched arms drawn by seed from one pool; verified only if the after-arm costs at most 0.9 times the before-arm per
filed claim, with quality not lower.

1. **Hold R3r-flagged correction-route orders before dispatch and route them to acquisition.**
   - Share: 66 orders, about 13.3 of 19.1 USD of correction-route producer spend (70%; estimated).
   - Evidence: section 4.2. R3r flags 0 of 9 correction submissions, and R1, a stricter form of R3 registered in
     the first pass, held up out of sample at 23 of 24.
   - Risk: an order a producer could have closed from a source outside DISPATCH_CHECK is delayed, not lost. Do not
     apply the rule on the YES route.
   - Test: 30 R3r-flagged orders. Arm 0 dispatches them; arm 1 holds them at 0 tokens. The cut is confirmed if arm 0
     files at most 1.
2. **Pool review sets to at least 4 claims, keeping one planted control per session.**
   - Share: 13 of 23 sessions reviewed 1-2 claims. Cost per claim falls from 1.03-1.24 USD to 0.45-0.62 USD
     (estimated), about 10 USD on this wave (inferred).
   - Evidence: section 5. Controls were caught 26 of 26 at every set size.
   - Risk: attention per claim falls in larger sets.
   - Test: arm 0 reviews per packet as now; arm 1 pools 4-7 claims across packets. Compare USD per both-upheld claim
     and the control catch rate.
3. **Register held sources at prep.** Run the source supplement for every held statute, order or Public Papers page
   that LOOKUPS or the source index names.
   - Share: 15 blocks, about 4.0 USD, 11% of producer spend (estimated).
   - Evidence: section 4.1.
   - Risk: low; the producer still decides relevance.
   - Test: re-prepare the 15 orders with supplements and count submissions and upheld claims against their first pass.
4. **Check that the checkout holds every file dispatch calls held, before launch and before review.**
   - Share: 9 NEA blocks (about 2.7 USD), the 33-minute refresh of 20 claims, and the delay to filing (section 7).
   - Risk: none; it adds an `os.path.exists` pass of a few seconds.
   - Test: a defect fix, so no two-arm test is needed. Track refreshes per wave, which should reach 0.
5. **Shrink the 46,099-token starting prompt.** Run workers as stateless calls with only the tools they use, or with a
   trimmed tool set.
   - Share: about 16% of producer dollars (measured) and 20-39% of reviewer dollars (estimated).
   - Evidence: section 3.2.
   - Risk: a worker missing a tool it needs fails visibly.
   - Test: the stateless gauge already built (`jobs/maudslay-conveyor/stateless.py`). Arm 0 Agent-tool sessions,
     arm 1 stateless calls, on matched packets; compare measured USD per both-upheld claim.
6. **Extend Olney before adding producers on board orders.**
   - Share: Olney cost about 1.0-1.9 USD per upheld claim against 3.3-10.9 USD on the producer route (estimated).
   - Evidence: section 6.
   - Risk: one script defect repeats across a batch (o1). Add the extension-order check that arm A applied, and keep
     planted controls.
   - Test: the next Olney batch against producer lanes on matched board orders.
7. **Launch each lane when its own prep finishes.**
   - Share: 333-410 s of wall time per lane at wave start (measured); no tokens.
   - Test: time to first hand-back over two waves of equal size.
8. **Slim correction-route views to the open step.** Keep reviews whole.
   - Share: views are 14-16% of producer dollars (measured on PC). The earlier claim and prior research are 49% of
     correction view bytes (measured).
   - Risk: a reviewer objection is hidden from the producer.
   - Test: matched correction orders that R3r does not flag; compare USD per upheld claim.
9. **Run apply and batch-check as one command, and refuse a byte-identical re-apply.**
   - Share: 27-29% of PC session wall and 3-20% in the cloud; under 1% of dollars (measured). This is a wall-time cut.
   - Test: rounds and wall time per submitted claim.
10. **Digest the fixed reading list.**
    - Share: 7% of producer dollars with the prompt file (measured).
    - Risk: it loses ruling distinctions; rank it last.

## 9. Gaps

- Coordinator tokens are not measured in any lane.
- The calibration factor rests on two Sonnet transcripts. Opus reviewers have no transcript.
- Two resumed passes have no usage, so a01 and c10 are understated.
- The p02 and p04 batch-check times from file mtimes are invalid (the files were copied from a branch). Their tool
  timestamps are used instead.
- c12 and s01 were not finished at the snapshot. The c10 pair awaits a replacement proposal.
- Owner adoption of the 9 Bracton proposals is pending, so "filed" for Bracton means proposed.

## 10. Files

- `jobs/gilbreth/gilbreth.py`: the probe.
- `jobs/gilbreth/output/MEASURES.json`: every measure with its basis. It holds per-packet records, the block
  taxonomy, the pre-screens, leverage and the Bartolus comparison, plus `second_pass`: transcripts, calibration,
  sessions, reviews, filing, trial, Olney and refresh.
- `jobs/gilbreth/output/packets/<wave>__<packet>.csv`: one row per order.
