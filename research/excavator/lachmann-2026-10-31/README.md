# Lachmann working-text confirmations: audit record, 2026-10-31

`jobs/lachmann` machine-checks, for every order whose text step is open only because a compiled transcription or
the owner's ProQuest replica scan is held, whether the held working text is the right order (number and register
date in the text, or an agreeing independent witness), complete (its own opening and closing, no other order run in),
and page-checked where the fragment requires it. Under the owner ruling of 2026-10-31
(`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`), a confirmed working text lets the
readiness tracker mark the text step `provisional`, counted separately and never as an original.

Each audit round drew 59 confirmed orders at random (seeded, excluding every order audited in an earlier round),
added five planted defects (two texts under another order's header, three texts cut to 60%), and gave the blinded
items to four separate-context Claude auditors (Sonnet 5.5, 16 items each).

| Round | Rule | Confirmed | Genuine upheld | Planted defects caught | Result |
|---|---|---:|---:|---:|---|
| 1 | start, closing cue, identity, pages | 800 | 58 of 59 | 5 of 5 | fails zero-miss: EO 5528, a machine-read printing whose metes-and-bounds courses 3-6 lost their azimuths |
| 2 | + numbering-gap check | 792 | 58 of 59 | 5 of 5 | fails: EO 5252, a tract list that breaks off at a comma just before the signature |
| 3 | + break-off-before-signature check | 764 | 59 of 59 | 5 of 5 | **passes**: 95% upper bound on the error rate 4.95% |

Both rule changes target the defect found and were tested on a fresh sample of orders never audited before. The
refinement was sequential (the rule was tightened twice before a sample passed), which slightly weakens the nominal
95% bound; the two failures share one cause, damaged land descriptions in machine-read compilations, which both
new checks address. Of the 7,534 orders in scope, 764 are confirmed (all with number-and-date identity; 576 machine-
read government printings and 188 ProQuest replica scans); the rest stay open with reasons in `RESIDUAL.csv`. The
largest blockers are transcriptions that carry no order number (APP, Wikisource) and texts without a recognizable
opening; an agent pass or a bridge from the APP heading could reach more of them.

Auditor usage: 12 Sonnet 5.5 runs, about 1.03M tokens, 34-56 seconds each. Records: `audit-r1/`, `audit-r2/`,
`audit-r3/` (packets as the auditors saw them, unblinding keys, reviews). Certified count unchanged at 0.
