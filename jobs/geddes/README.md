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

The source, citation, event and literal-name checks are separate small modules.
Own-order absence checks require a verified complete body located with the
existing clause-drafts locator, or a corroborated individual APP publisher
item. Recitals are included, neighboring orders excluded, and native inventory
overrides validated. Unresolved boundaries produce coverage gaps. Concepts
allow OCR whitespace/soft-hyphen repairs; quotations preserve case and
punctuation and bind to their own exact original/actor source spans.

Reasoning citations bind the date and subject to retained publisher metadata
and hash-pinned lookup candidates, including ambiguous suffixed/unsuffixed
siblings. Federal Register issue dates are not signing or filing dates.
Later-event checks preserve grammatical actor/object and clause scope. They
do not decide the legal effect of a candidate instrument.

Name assertions search proper literal names over the exact Git-retained
`jobs/**/texts/**/*.txt` membership, excluding clause-drafts. A phrase such as
"this code" requires its named antecedent; it is never searched as a proper
name. Positive counterexamples bind publisher identity/date and exact source
spans. Missing or changed files prevent full-corpus coverage. Exported packets
without Git get an explicitly bounded packet-pin fallback, never a full-scope
label. Corpus snapshots reverify the actual bytes searched before returning
output; matching file counts and unchanged timestamps prove neither identity
nor integrity. A completed scan is not a legal-effect or authenticity verdict.

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
name is the runner registration. `needs.txt` declares literal helper roots; `inputs.txt` uses the existing
runner fnmatch contract for source TXT files (including selected-page/singular
text folders), publisher metadata and research packets. No new materializer
certificate is granted. The job
runs unit checks and telemetry accounting by default; it lints only the single
directory explicitly supplied through `GEDDES_APPLIED_DIR`. It never sweeps
historical applied directories. The command-line linter can also run locally
against any applied directory and its frozen packet. Unit tests use temporary
synthetic packets and never infer legal findings.

## Validation and interpretation

Run all checks with `python3 -I -m unittest discover -s jobs/geddes -p 'test_*.py'`.
The PR workflow also runs the exact historical comparison with the retained
text corpus. The research report under
`research/excavator/claude-geddes-2026-11-01/REPORT.md` distinguishes exact
historical recall, total warnings on filed claims, independently supported
source/schema discrepancies, false flags, and indeterminate warnings. Do not
assume every previously filed claim is source-perfect or suppress a genuine
verbatim mismatch to meet a total-warning target.
