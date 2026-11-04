# Tribonian production run, 2026-11-04: final disposition

Tribonian ran the ordinary claim-kit route (prepare, produce, apply, batch-check, blind review with planted controls, after-reveal review, completion) on 1,041 decided orders in 37 production batches and on 83 previously rejected claims in three correction batches. It filed **545 reviewed lifecycle claims**: 492 new dossiers and 53 corrections of earlier rejected claims. All 51 planted controls were caught. No human certification was performed, and the certified whole-lifecycle count stays **0**.

The authoritative per-batch record is [`evidence/DISPOSITION.json`](evidence/DISPOSITION.json) (and `.csv`), regenerated from the native completion receipts by `tools/disposition.py`. Each batch folder keeps every applied, completed, refused and stale version; packets and reviews are excluded from this branch and preserved byte-for-byte on `claude/tribonian-state` (see the end of this report).

## What happened to each order

A "blocked" order is one the producer did not submit, with the missing source named in `decisions.csv`, or one a reviewer rejected, with the defect recorded. A "rejected_mechanical" claim passed review but failed the actual claim checker at completion, almost always because a cited source is held only as a hash (`custody_record_only`).

| Kind | Orders attempted | Filed | Blocked or rejected | Mechanically unverified at completion |
|---|---|---|---|---|
| New production (37 batches) | 1,041 | 492 | 502 | 47 |
| Corrections (c01–c03) | 83 | 53 | 29 | 1 |

Low-yield batches (o13, o14, o17, o20, o22–o24, a01, a02) were dominated by producer blocks that name a missing ending or current-law source; their packets and decisions are the starting point for source acquisition, not for re-review. o25 was applied with zero submissions, because every order in it needs current-law text that is not held. o26–o30 were prepared and never started, by instruction, once the wave was being drained.

Batch a03 had been produced (12 submitted) but missed review in the first pass. It was reviewed in the paired trial below and filed 12. Its first completion was killed by the memory limit during the actual checker run (`complete-v1`, kept); `complete-v2` published.

## Corrections versus additional dossiers

The 53 correction filings replace nothing. Each corrected claim is a new version of an order whose earlier version was rejected and never filed, so it adds one dossier to the ready count. The 30 corrections that were not filed are listed with their reviewers' defects in the c01–c03 reviews. They include the EO 11051 later-event omission (EO 10346), the false "cites EO 10952" sentence (EO 11088, 11090, 11091), the "took effect the day after" sentence (EO 10084, 10098, 10118, 10158), the strike-and-insert continuation for EO 12225, the unnamed-amender question for EO 12584, and the false "modifies EO 12958" sentence (EO 13326, 13328).

## Still blocked, with the first executable step

1. **47 reviewed claims are blocked by source custody.** They are in o04 (23), o08 (5), k01, o21 and o24 (4 each), a04 and o06 (2 each), and a01, a05, f01 and c03 (1 each). They passed blind review, but a cited source was held only as a hash when completion ran. Byte retention is queued in `jobs/cotton-capture-custody/data/WANTED.jsonl`, `jobs/astra-source-retention/REQUESTS.json` and `research/readiness/FETCH_QUEUE.jsonl`. A re-completion of o04 was refused (`o04/packet/complete-v2`), because the batch's own published claims changed its Valla context. The route therefore needs a new packet. First step: when the custody runs report the bytes held, run `kit.py prepare` for exactly these ids, reapply the reviewed rows unchanged, and complete with a fresh blind review or an owner-approved reuse of the exact-version review. PR132's dispatch-check, run before assignment, would have caught this before review.
2. **EO 10156 (c02)** fails `order_exists` because the held OCR text prints "98661". It needs a better witness of the order.
3. **o25–o30.** o25 needs current-law sources. o26–o30 are ready to start with `bash tools/render_producer.sh oNN`, using the existing packets after `python3 tools/freshness.py oNN` reports them fresh; re-prepare first if it does not.

## Paired review trial: do mechanical receipts eliminate reviewer work?

The trial is named Lind, after James Lind's 1747 paired scurvy trial. It reviewed the same 85 claims (a03, c01, c02 and c03) twice, in fresh Opus contexts launched together. Each claim was reviewed once under each arm, the claim order was shuffled separately per arm, and both arms saw the same planted controls. Arm A used the current reviewer prompt, in which the reviewer writes one script for hash and quoted-span checks. Arm B received the same prompt plus a per-claim receipt from PR135's maintained `blind_verify.py`. The receipts were generated on arm B's own review set (the planted versions), so no genuine counterpart or key reached a receipt. A claim was filed only when both arms upheld it. Full measurements are in [`evidence/LIND_TRIAL.json`](evidence/LIND_TRIAL.json).

The receipts removed little model work. Over the four batches, arm B used 53.7M cache-read tokens against arm A's 52.4M, 1.42M cache-write tokens against 1.17M, and 185k output tokens against 186k. It made 279 model calls against 270, with 3,653 against 3,739 active seconds. Fresh input was about 550 tokens in each arm. Arm B ran 15 commands that touch quote offsets against arm A's 24, and 13 commands that touch text hashes against 15. In other words, about a third of the offset scripting disappeared. But reviewers write these checks into the same scripts they use to read the claims, so the saving does not show in tokens or time. The receipts also fail closed on raw custody: every claim was classed `refuse` or `unresolved_custody` for want of a raw original. Nor can they express the page records and confirmation flags that reviewers check by hand.

Quality did not fall. Both arms caught all 7 planted controls, and the arms disagreed on 7 of 85 claims. Arm B alone rejected EO 11088, 11090 and 11091, and the coordinator confirmed those three defects against the held texts; it alone also rejected EO 12584, a contested ruling question. Arm A alone rejected EO 12397, 11452 and EO 7845. The 7845 defect is a reason sentence that silently corrects OCR inside quotation marks; the receipts cover only quote fields, not prose. Reviewer-to-reviewer variation was larger than any arm effect.

**Decision:** do not wire receipts into the reviewer prompt as a default, and do not expand a wave on this basis. Current practice already gives producers maintained mechanical checks (`batch-check` runs the actual claim checker, and Geddes lints before handback), so the producer side needed no trial. The review side's cost is dominated by reading sources and judging law. The useful finding is the second-reviewer effect: pairing two independent reviewers caught 7 extra defects in 85 claims, at roughly double the review cost.

## Measured cost of the run

Telemetry comes from the existing Hamilton profiler, run over the private agent transcripts by `telemetry/drive_hamilton.py`. Sanitized per-agent rows are in `telemetry/AGENT_USAGE.csv` and phase totals in `telemetry/SUMMARY.json`. The table gives token counts by phase; cash and invoice amounts are unknown. The coordinator's transcript covers only the period after a context compaction, so coordination is a lower bound.

| Phase | Agents | Calls | Fresh input | Cache read | Cache write | Output |
|---|---|---|---|---|---|---|
| Production | 35 | 3,751 | 7,684 | 758.4M | 28.5M | 3.99M |
| Review (incl. trial and after-reveal) | 36 | 2,173 | 4,440 | 384.7M | 10.8M | 2.79M |
| Correction production | 3 | 469 | 944 | 93.1M | 2.9M | 0.43M |
| Integration and engineering | 3 | 124 | 256 | 13.4M | 0.9M | 0.07M |
| Coordination (partial) | 1 | 200 | 434 | 54.2M | 0.5M | 0.12M |

Sonnet producers account for about 855M of the 1.30B cache-read tokens. Production cost about 0.73M cache-read tokens per order attempted. Losses that cost model work without filing anything: 47 reviewed claims stranded by custody; a03's first missed review; three stale-packet restarts (a01–a04, f01–f03, k01, o01 after an owner ruling; c01–c03 twice from concurrent completions); one disk-full crash; and two usage-limit pauses.

## Resumption and preserved state

- Packets, reviews, completions, review sets and planted versions: branch `claude/tribonian-state`, one commit per batch, made by `tools/snapshot_state.sh`. The private control keys never left the coordinator's scratch space.
- Coordinator log with agent roster: `COORDINATOR_LOG.txt`.
- Owner-delegated answers used in this run: `research/readiness/owner_rulings/2026-11-04-delegated-answers-to-open-asks.md`.
