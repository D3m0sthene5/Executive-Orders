# Lambertini: shared savings readings and recorded counterevidence searches

Named for Prospero Lambertini (Benedict XIV), who formalized the devil's advocate's search for
counterevidence. Design and probe plan: `research/plans/LAMBERTINI_DESIGN.md`. Standard library only.

```
python3 -I jobs/lambertini/lambertini.py build                     # writes output/ (about 12 s)
python3 -I jobs/lambertini/lambertini.py probe --pool LAMBS --n 20 --seed TEXT --out DIR [--exclude FILE ...]
python3 -I jobs/lambertini/test_lambertini.py
```

Zero-agent part only. It reads committed outputs (readiness tracker, claim drafts, fr-originals texts,
later-events, current-law, the parsed 1944 WPA list) and writes:

| File | One line per | What it is |
|---|---|---|
| `SAVINGS_PACKETS.jsonl` | acting EO with held official text that ends >= 1 decided NO order | source pin, text sha256, every savings/transfer phrase with offsets, where each target is named. One reading serves all its targets. |
| `SAVINGS_PREFILL.csv` | decided order with a draft | savings class (S0-S9, Y0-Y4) and a suggested state. S0 alone suggests `none_after_bounded_search`; everything else says `review`. A prefill a reader confirms, never a closure. |
| `COUNTEREVIDENCE_RECORDS.jsonl` | decided not-ready order blocked by `NO_OFR_CATALOG_ENTRY` | a claim-shaped DRAFT `later_source_search` (four searches, coverage, leads, what was not searched). `draft_not_claim: true`. |
| `POOL_LAMBS.txt`, `POOL_LAMBC.txt` | order | probe pools for Llull |
| `SUMMARY.json` | run | counts, class table, calibration against the savings states written in ready claims |

It writes no claim, no `EXHAUSTED.jsonl` line, no status or tier, and never changes the codebook or the
certified count (0). A phrase found is a lead; a phrase not found is a lead. The tracker does not read these
outputs; the counterevidence record counts only if a producer copies it into a claim after reading the leads
(and after the owner rules on its adequacy for pre-1937 orders, design Q-L2).

## Research progress and continuation gates

`progress.py --out FILE` reconciles logged attempts, per-case AI verdicts,
canonical claims, exact-hash checker results and the existing integrated tracker.
It also separates Rastell acting evidence from research opportunities and Lamm
ending records from complete claims. Every consumed file is pinned by SHA-256.
The runner writes this as `RESEARCH_PROGRESS.json`; historical outcome files are
preserved. Evidence, claims and ready orders are overlapping stages, not numbers
to add. None is independent human certification.

Use `probe` to select a new initial test. Use `continue` for work authorized by
that test's frozen continuation contract:

```sh
python3 -I jobs/lambertini/lambertini.py continue --pool LAMBS --n 8 --seed TEXT \
  --out NEW_DIRECTORY --gate-contract CONTRACT.json --gate-observation OBSERVATION.json
```

The contract and observation use `jobs/llull/gates.py` schemas. Evidence hashes
are checked before any continuation sample is selected. Missing plants or
measurements produce an `untested` receipt and exit 5. A failed gate also stops.
One caught plant does not satisfy a registered two-of-three test. A new output
directory preserves each receipt. These gates enforce this CLI's continuation
path; they cannot enforce an agent's behavior outside the tool.
