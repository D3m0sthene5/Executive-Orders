# Geddes advisory claim linter

Geddes runs deterministic source comparisons over a `claim-kit apply` output
directory. It is advisory pre-handback QA. It never reads review files or
review verdicts, changes claims, routes claims, or declares that a claim is
legally correct.

```sh
python3 -I jobs/geddes/geddes.py lint research/excavator/<batch>/packet/applied-v1
python3 -I jobs/geddes/geddes.py view research/excavator/<batch>/packet/PACKET.json EO:1234A --write /tmp/EO-1234A.view.json
python3 -I jobs/geddes/geddes.py cost research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv
```

`lint` finds the nearest ancestor `PACKET.json`, reads `CLAIMS.proposed.jsonl`,
decodes the exact frozen dossier, and resolves pinned held-text paths from the
repository root. It fails closed for that source when the file is missing or
its SHA-256 differs: no text-based comparison is made, and the problem appears
under `coverage_gaps` / integrity counts. It emits defect flags separately from
missing-coverage records. Flags identify source-comparison discrepancies for
human follow-up; they are not automatic rejection rules.

Checks compare attributed quotations and known carry-over phrases to the
target order's bounded text span; test target and later-actor suffixes against
their pinned identifiers; compare Federal Register page and issue-date metadata
to the same pinned event source; detect named later instruments without a
matching source-backed event record; and check verbatim operative and later
event quotations against their own cited sources. Missing event/search coverage
and literal-name search coverage are reported separately from defect flags.
No-other-order assertions search names rather than numeric IDs in the union of
Apollo packet-pinned held texts, report unavailable/conflicting files, and make
the bounded corpus limitation explicit. Apollo's lookup metadata describes
33,118 discovered and readable held texts (plus 9,761 clause-draft exclusions);
the packets pin only a subset (1,346 unique source files in this run). Geddes
does not establish a corpus-wide negative. Heuristics can miss paraphrases and
produce false positives. They do not establish source authenticity or legal
effect.

`view` renders a decoded one-order dossier with an order-scoped original text span,
matching shared analysis for the NRA batches, relevant prior research, mechanical
shared-task pointers, and that member's bounded lookup leads. It writes to
stdout by default or to a requested `--write` path. It reports
approximate compact-view and full-packet token counts (`UTF-8 bytes / 4`). This
is a rough size estimate: no model was invoked and therefore no actual prompt,
token, cache-read, or cost saving is inferred.
`cost` aggregates the columns actually present in a telemetry CSV by track,
role, and model. Per-filed-claim values require a sibling `REPORT.md`
with explicit track counts or a `--filed-manifest` JSON sidecar such as
`{"filed_claims":{"NRA":127,"General":127}}`. Missing telemetry remains
unknown.

The mandatory pre-handback sequence is: run `claim-kit batch-check`; run
`geddes lint` on its applied directory; inspect every defect flag against the
packet and source; resolve or explicitly document coverage gaps; then hand the
proposal and lint JSON to the normal blind-review process. Do not edit the
claim-kit checker or review contract as part of Geddes.

## Inputs

No static job-name registry exists in the runner; the `jobs/geddes/` folder
name is the runner registration. `needs.txt` lists the bounded data folders
needed by the manual job. The job
runs unit checks and telemetry accounting by default; it lints only the single
directory explicitly supplied through `GEDDES_APPLIED_DIR`. It never sweeps
historical applied directories. The command-line linter can also run locally
against any applied directory and its frozen packet. Unit tests use temporary
synthetic packets and never infer legal findings.
