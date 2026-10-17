# Readiness: getting orders ready for human review

The [readiness tracker](../../jobs/readiness-tracker/output/TRACKER.md) counts how many
orders the machines have finished: every research step the order needs is done
or recorded as searched to the end, so only human verification remains. It
runs daily and whenever its job folder changes, and it reads this folder.

## claims/

One JSON object per line, in any `*.jsonl` file here. The format is the Stage 19
whole-lifecycle claim (`../stage19/CLAIM_SCHEMA.md`), checked by the project's own
`claim_gate.py`. **Partial claims are welcome**: each step counts as soon as its
part passes the gate, so write the clause inventory as soon as you have it and
add the ending, savings and later-source search as you go. If two lines have the
same `instrument_id`, the later one (by file name, then line) wins.

## EXHAUSTED.jsonl

When a step cannot be finished by machine (no source exists or every route is
blocked), record it so the order can still reach human review with the gap
stated. One line per order and step:

```json
{"instrument_id": "EO:1234", "step": "original_text", "searched": ["govinfo FR 1942 vol. 7", "APP", "Wayback id_ for ..."], "recorded_by": "Astra", "recorded_on": "2026-10-17", "note": "never printed in the Federal Register"}
```

`step` is one of: `original_text`, `clause_inventory`, `ending_or_current_basis`,
`savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`. List the
gap in the claim's `unresolved_material_gaps` too.

Neither file changes a provisional status or any count in the research ledger.
