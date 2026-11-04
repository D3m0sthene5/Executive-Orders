# Geddes advisory claim linter

Geddes runs deterministic source comparisons over a `claim-kit apply` output
directory. It is advisory pre-handback QA. It never reads review files or
review verdicts, changes claims, routes claims, or declares that a claim is
legally correct.

```sh
python3 -I jobs/geddes/geddes.py lint research/excavator/<batch>/packet/applied-v1
python3 -I jobs/geddes/geddes.py view research/excavator/<batch>/packet/PACKET.json EO:1234A --write /tmp/EO-1234A.view.json
python3 -I jobs/geddes/geddes.py cost research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv
python3 -I jobs/geddes/geddes.py gate research/excavator/<batch>/packet/applied-v1
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
Besides the order's text, clauses and leads, the view now carries four sections that producers
otherwise had to pull from `PACKET.json` or `READ.md`. `machine_searches` lists the dossier's
machine searches for this order (resolved through the shared objects): the search id, its kind (the
part of the id before the colon), who ran it and when, whether it was complete, the number of hits
it found for this order, and its coverage statement (repository, query scope and scope note), with
a summed hit total that reads `"unknown"` if any count is missing. `later_events_chain` lists the
dossier's chain of later events (actor, date, verb, touched sections, a bounded excerpt of the
provision and the source), and a `citable_evidence` list of the evidence ids, such as `ACTOR_TEXT:`
and `ACT:` ids, that a `later_events` entry can cite from the packet; each chain event names the
ids belonging to its actor, and a later instrument missing from that list is not citable from the
packet. `clause_inventory` gives each clause's label, kind, page, character range, lifecycle state,
wording features, open questions and evidence ids, and, when the packet folder holds `clauses.csv`,
the draft rows for this order with their state, ending, reason and inventory reason (a
`@rationale:` reference is replaced by the text in `RATIONALES.json`); the draft rows are a prior
draft, not evidence. `current_canonical_claim` shows the order's current filed claim under
`research/readiness/claims`, chosen the way the tracker chooses it (the last line of the last file by
name), with its path, line number and hash, marked as a prior draft rather than evidence.
Every list is capped (the limits are in the view's `view_caps` key) and each capped list reports its
true total and whether it was cut. A filed claim larger than 20,000 bytes has strings over 400
characters shortened and says so; `--full-claim` keeps them whole. With `--write`, the full view goes only to
the file and standard output shows a short summary (sizes, section bounds and the claim's path).

For a producer assigned several members of one packet, render their ordinary views
in one process:

```sh
python3 -I jobs/geddes/geddes.py views research/excavator/<batch>/packet/PACKET.json EO:1234A EO:1235 --write-dir /tmp/assigned-views
```

The command writes `EO_1234A.view.json` and `EO_1235.view.json`, with the same
content and caps as separate `view` calls, and prints only summaries. Without
`--write-dir` it prints an ordered JSON list of the complete views. `--full-claim`
keeps filed-claim strings whole for every member. All requested members are checked
before output starts; duplicate members and existing output files or symlinks are rejected. The Python interface is
`view_many(packet_path, eos, write_dir=None, repo=None, full_claim=False)`.

This shares packet decoding, current-claim selection, side-sheet parsing and shared
memo reads only for that invocation. Actual held sources are still read and hashed
for each member, so a changed source cannot be hidden by the shared presentation
context. Native packet schemas (or a native-sized 64-hex fingerprint) require
an intact native envelope hash and codec maps. Historical schema-less exports
without that fingerprint remain navigable with their original dossier/source
checks; they carry no native envelope verification. This rendering check does
not rerun the full production preparation, ownership and prior-research gates.
Member scopes, source pointers, coverage qualifications and overflow bounds
stay identical. This does not remove existing view caps: consult the pinned packet,
source files and the indicated claim path/line for complete material beyond a cap.
Optional reviewed provision histories are live-validated once and scoped to each
member, with unknowns, independent review limits and source dependencies intact.
Reviewed factual occurrence intervals retain their full source marker and distinct
occurrence/observational scope; they are revalidated per member and are excluded
from the citable legal-actor catalogue. Changed sources/reviews refuse the new
context rather than silently presenting stale research. Nothing is cached between commands. The output is the same size as the ordinary
views; model-token and cash savings have not been measured. A retained 23-order
rendering benchmark and exact parity checks are recorded in
`research/progress/sol-evidence-economy/batch-views/`.

`cost` aggregates the columns actually present in a telemetry CSV by track,
role, and model. Per-filed-claim values require a sibling `REPORT.md`
with explicit track counts or a `--filed-manifest` JSON sidecar such as
`{"filed_claims":{"NRA":127,"General":127}}`. Missing telemetry remains
unknown.

## Claim-kit wiring, flag ids, the gate and run comparison

`python3 jobs/claim-kit/kit.py batch-check <packet> <applied>` now runs the Geddes
lint on the applied directory after the existing batch check finishes. The full lint
result is written to `<applied>/GEDDES_LINT.json`, and the printed batch-check result gains
a `geddes` entry with the number of flags, the instrument ids of the flagged claims, the
number of coverage gaps, the file name, and the seconds the lint took. If Geddes fails for
any reason, the entry holds `{"error": ...}` and batch-check carries on, so Geddes can never
stop a batch check from finishing. Unless `--geddes-strict` is given, Geddes does not change
the batch-check exit code. The lint output also reports its own `seconds`, the number of
distinct files it read (`files_read`) and the total number of read operations (`file_reads`).

Every flag in the lint output carries a `flag_id`: the first 16 hexadecimal characters of
a SHA-256 hash over the instrument id, the flag code, the scope id, and the flagged text span
(or, when the flag has no span, its detail sentence). The same flag on the same claim text
therefore keeps the same id from one lint run to the next, and a flag a check already labelled
keeps its own id. The ids are added by `lint`, not by `lint_one`.

The gate makes a coordinator record a response to every flag before blind review:

```sh
python3 -I jobs/geddes/geddes.py gate <applied> [--resolutions FILE]
```

The gate lints the directory again, so it judges the flags that exist now, and reads
`<applied>/GEDDES_RESOLUTIONS.json` unless `--resolutions` names another file (which must
exist). The file looks like
`{"schema": "geddes-resolutions/v1", "resolutions": [{"flag_id": "...", "instrument_id": "...", "response": "fixed_in_new_version", "note": "..."}]}`.
The allowed responses are `fixed_in_new_version`, `disputed` and `order_blocked`. A flag counts
as resolved only when an entry names its `flag_id`, uses an allowed response, carries a
non-empty note, and, if it gives an `instrument_id`, names the flagged claim's instrument. The
gate exits 0 only when every current flag is resolved, exits 1 and lists the unresolved flags
(in the JSON on standard output and one `UNRESOLVED` line each on standard error) otherwise,
and exits 2 on a read or format error. Resolutions whose flag no longer exists are listed as
`stale_resolutions` and do not fail the gate. Coverage gaps are not gated. Passing the gate shows
that each flag has a written response; it does not say the claim is correct. Running
`kit.py batch-check ... --geddes-strict` applies the same gate to the lint it has just
produced and exits nonzero when the gate fails or Geddes cannot run.

To compare two runs, give `cost` the new telemetry file, the baseline with `--compare`, and a
JSON file of filed-claim counts for each run:

```sh
python3 -I jobs/geddes/geddes.py cost --compare BASELINE.csv --filed-baseline BASE_FILED.json NEW.csv --filed-new NEW_FILED.json
```

A filed-claim file maps each track to the number of claims filed, for example
`{"filed_claims": {"NRA": 127, "General": 127}}`. For every track and role the output gives the
total input tokens (`tokens_total_input`, which is input plus cache-creation plus cache-read
tokens; the tool computes it when the CSV lacks that column), cache-read tokens, output tokens
and active seconds, each divided by the track's filed claims, for both runs, together with the
ratio new divided by baseline and a sentence such as "new run used 87.5% fewer cache-read
tokens per filed claim for NRA/producer". When a number is missing, for example a blank cell,
a track absent from one run, or a missing filed-claim count, the value and the ratio are the
string `"unknown"` with the reason given; they are never treated as zero. A smaller ratio is a
measured difference between two runs, not proof that a change caused it.

`telemetry.py` builds a telemetry CSV from subagent transcripts:

```sh
python3 -I jobs/geddes/telemetry.py TASKS_DIR OUT_PREFIX --roster ROSTER.csv
```

The roster CSV has the columns `agent_id,batch,role,track`, and each agent's transcript is
`TASKS_DIR/<agent_id>.output`. Instead of a roster, `--apollo-log COORDINATOR_LOG.txt` reads the
Apollo coordinator log format. The output has the Apollo columns in the same order, followed by
`tokens_total_input` and `track`; agents with no transcript are listed in `OUT_PREFIX.json`
rather than counted as zero.

The mandatory pre-handback sequence is: run `claim-kit batch-check`, which now runs
the lint itself; inspect every defect flag against the packet and source; record a
response to each flag in `GEDDES_RESOLUTIONS.json` and run `geddes gate`; resolve or
explicitly document coverage gaps; then hand the proposal and lint JSON to the normal
blind-review process. Do not edit the
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
