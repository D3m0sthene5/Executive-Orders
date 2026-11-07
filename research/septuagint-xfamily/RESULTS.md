# Septuagint results: an OpenAI-family reviewer replayed against Claude reviewers on planted controls

Pilot approved by the owner (Kean D-20261106-encyclopedie-xfamily). **The filing rule is unchanged; the owner decides
whether to change it.** Coordinator: Claude Opus 5.5, 2026-11-07.

## Conclusions first

1. **On the four batches that could be rebuilt exactly, the Codex reviewer caught every planted control: 8 of 8, 7 of
   them with strict credit.** The original Claude reviewers caught 17 of 22 reviewer-plant pairs, 16 strict.
2. **The samples are too small to say one family is better.** Wilson 95% intervals overlap widely: Codex strict 7/8
   (0.53-0.98), Claude strict 16/22 (0.52-0.87). This is a pilot, not a measurement of catch rates.
3. **The informative result is complementarity.** On every plant that at least one Claude reviewer missed, the Codex
   reviewer caught it:
   - EO 9667 (quote cut before the revoking words; arm A missed);
   - EO 14131 (signing date moved back three years; arms A and C missed);
   - EO 12295 (a later event removed): arms A and B upheld it; Codex rejected it, but for a different reason, so it earns
     lenient credit only. No reviewer of either family named the missing event.
   Under the current rule (two blind reviewers must both uphold), the EO 12295 plant was upheld by both A and B and was
   stopped only by the third arm. With one Claude and one Codex reviewer it would have been stopped by the pair.
4. **No false alarm.** Codex rejected one genuine claim (EO 10104); the blind adjudicator scored it *contestable*: it
   objects that a closing supersession sentence has no clause of its own, a point on which the project's own claims
   differ. Claude reviewers rejected no genuine claim.
5. **Cost and speed were comparable.** Codex (gpt-6-sol, medium effort, logged in to the owner's ChatGPT plan, so no
   metered dollars): 4-6 minutes and 1.05-1.86 million input tokens per batch, 95-97% cached, 8.5-11.6 thousand output
   tokens. The Claude Sonnet reviewers on the same batches used about 1.5-2.6 million cache-read tokens each.

## Method

- **Batches:** the Dorotheus YES-probe review batches of 2026-11-06 (`research/excavator/dorotheus-yesprobe-2026-11-06/`),
  each with one date-shift control and one Mountweazel plant. Six candidate batches; **four passed the exact-rebuild
  gate** (y01, y02, y03, y05): every rebuilt claim's canonical SHA-256 equals the hash every original arm recorded,
  and each rebuilt packet hash equals the committed one (`GATE.json`). ux1 and ux2 were dropped, never approximated.
- **Codex arm:** the original reviewer prompt with paths changed, run by `codex exec` in a sandbox whose working tree
  physically lacks the key, the report, the other reviews and later filed claims (`README.md`). Its event logs were
  scanned for commands naming forbidden paths; none were found. Residual risk: the Windows sandbox permits reads outside
  the workspace, so the blinding rests on absence, the prompt and the scan.
- **Blind adjudication:** a fresh Claude Opus agent that had done none of this work scored all four arms with the
  Mountweazel strict/lenient rules, with arms relabelled R1-R4 at random per batch, family words absent from the packet
  (checked), and the mapping kept private until scoring was done (`results/BLIND_PACKET.json`,
  `results/ADJUDICATION.json`, `results/UNBLINDING_MAPPING.json`).
- **Consistency check:** the blind re-scoring agrees with the original coordinator's scoring (`PLANTS.csv`) in 21 of 22
  Claude cells; the one difference is y03 arm A on EO 11135, which the original scored lenient only and the blind
  adjudicator scored strict.

## Per plant (1 = caught)

| Batch | Plant | Type | Claude A | Claude B | Claude C | Codex X |
|---|---|---|---|---|---|---|
| y01 | EO 10153 | date shift, end | 1 strict | 1 strict | 1 strict | 1 strict |
| y01 | EO 9667 | Mountweazel D3, quote cut | 0 (noticed, accepted) | 1 strict | 1 strict | 1 strict |
| y02 | EO 11219 | date shift, later event | 1 strict | 1 strict | 1 strict | 1 strict |
| y02 | EO 12295 | Mountweazel D6, later event removed | 0 | 0 | 1 lenient | 1 lenient |
| y03 | EO 12046 | date shift, end | 1 strict | 1 strict | (no arm) | 1 strict |
| y03 | EO 11135 | Mountweazel D7, end date set to printing date | 1 strict | 1 strict | (no arm) | 1 strict |
| y05 | EO 11868 | Mountweazel D5, wrong actor and date | 1 strict | 1 strict | 1 strict | 1 strict |
| y05 | EO 14131 | date shift, signing | 0 | 1 strict | 0 | 1 strict |

Arm C was a third reviewer launched only where the coordinator then chose to; y03 had none.

## Limits

- Eight plants; two defect types (D6, signing-date shift) carry all the misses. Planted defects are not the same as
  natural errors; the real-error rate on genuine claims is not measured here.
- One Codex model and effort setting (the owner's config default, medium). A higher effort or another OpenAI model may
  differ.
- The Codex reviewer's tooling differed (PowerShell and a bundled Python instead of the Linux container), and its
  sandbox read ACL grants on this PC's folders remain.
- The adjudicator is a Claude model. It was blind to family, but a family-neutral human adjudication of the eight plants
  would remove that dependence.

## What the owner could decide (not done)

- Whether to make one of the two blind reviewers a different-family model for production batches (cost: subscription
  usage under the owner's ChatGPT plan; no metered dollars in this pilot).
- Whether to run a larger replay (for example the full Dorotheus sample wave or Mountweazel batches seeded for D6 and
  signing-date shifts) to narrow the intervals.
