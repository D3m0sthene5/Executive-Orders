# Theophilus wave, 2026-11-05: Bentham ranks 8 and 11

The wave filed **41 reviewed lifecycle claims** and one replacement proposal that awaits the owner. All 4 planted
controls were caught by both reviewers. It stopped because both order lists were exhausted, not because the gate said
stop. No status, codebook or census row changed, and the certified count stays **0**. The coordinator ran on Opus;
producers on Sonnet; every claim had two fresh Opus blind reviewers and filed only if both upheld it. Batch records:
`BATCHES.json`; per-step log: `COORDINATOR_LOG.txt`; measured usage: `telemetry/`.

## Rank 8: custody-stranded reviewed claims (48 orders, 41 filed)

These 2026-11-04 claims passed blind review but failed completion because a cited source was held only as a hash. Before
any model ran, the 48 exact reviewed claim lines (branch `claude/tribonian-state`) went through the real claim checker
offline.

- **32 passed clean.** Their dossiers were unchanged, so the reviewed rows were reapplied unchanged and the rebuilt claims
  hashed identically to the reviewed versions. Batches r01 and r02 filed 16 and 14. Both new reviewers rejected EO 13900
  and 13965 for citing a "section 5(d)" absent from the held texts (confirmed against the texts); a single reviewer had
  upheld both on 2026-11-04.
- **16 needed correction** (batch r03, Sonnet correction producer, two reviewers): 11 filed. Not filed: EO 14012 (the
  second reviewer found its section 6 revocation took effect on issuance, which the claim denied); EO 8341, 8613 and 8639
  (the only ending source's OCR prints order numbers that do not exist, so the checker rejects it); EO 10570 (the checker
  does not recognise the quoted text file).

## Rank 11: one step from ready (43 orders, 0 filed)

Only two could be closed from held sources:

- **EO 12743**: its later event was re-cited to the held official Federal Register text of EO 13286; both reviewers upheld
  it. Because the older claim's file name sorts later, a normal filing would leave the old claim counting, so it is
  published as `p01/REPLACEMENT_PROPOSAL.jsonl` and **needs the owner's adoption**.
- **EO 9789**: blocked. OCR damage in EO 9818's text fails the checker, and the open audit question (a separate end date
  for each clause) is unanswered.
- **The other 41** are recorded in `BLOCKED_RANK11.json` with a reason and first step: 23 incomplete claims, 8 audit holds,
  4 quarantines, 4 Opus media cases, EO 10494 and EO 10926. For 15 sources the search found the document but holds only a
  hash; `RETENTION_CANDIDATES.json` lists them as one bounded retention run, which is the first step.

## Gate decisions

| After | Decision | Filed / attempted | Probability of beating the next-best action |
|---|---|---|---|
| r01, r02 | CONTINUE | 30 / 32 | 1.00 |
| r03, p01 | PILOT | 11 / 18 | 0.97 |

## Measured cost (`jobs/bentham/sessions.py`, API list prices)

| Phase | Agents | Cache read | Output | Cost |
|---|---:|---:|---:|---:|
| Production | 2 Sonnet | 23.4M | 0.14M | $10.81 |
| Review | 8 Opus | 25.9M | 0.16M | $22.49 |
| Coordination | 1 Opus | 57.2M | 0.32M | $40.16 |
| **Total** | 11 | 106.6M | 0.62M | **$73.46** (about $1.79 per filed claim) |

Coordination was over half the cost; for a wave this small, a coordinator that reuses yesterday's prepared packets would
be cheaper.

## Notes

- Workers ran as separate `claude -p` sessions with fresh contexts (`tools/launch.sh`).
- During disk cleanup the coordinator deleted the large files of r02's real completion record (checker output, tracker
  replays, receipt copies), mistaking it for a dry run. The tally, exceptions, publication record and full log survive,
  and the published claims file's hash still matches.
- Shared sources ranked 1-6 are reported in `sources/REPORT.md`.
- Kean: F-20261105-theophilus. Open owner asks A-20261103-1 and A-20261104-1 are unchanged.
