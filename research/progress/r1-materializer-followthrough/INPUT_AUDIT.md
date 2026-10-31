# R1: Valla runner read audit

Baseline: `88cef0253ed735b2a6e612770f25f9148641ce93`.
Production evidence: `HANDOFF/final-integration-evidence-2026-10-30.json` records
run40987576100, source3c21be6f109278be15e68181d050cc788014bc19. Valla succeeded
in 48s, indexing 612 active claims,783 shared rationale references, 11 textual
leads and 97 tracked packages with none missing. Its materializer used
`unaudited_job` fallback and accounted 93,620 paths. These are input-closure
paths, not measured avoidable remote transfer. Valla produced no legal promotion.

## Supported execution

The existing runner executes `jobs/valla/job.py` → `valla.build(repo)` with
no explicit packages, IDs or exclusions. Runtime imports are standard-library
only. `correction()`'s batch import, agent `attach()` and the separate Valla pilot
workflow are outside this certificate. No Norton implementation is imported.
`job.py` does not invoke Valla's tests.

The audit used current static call/field examination, retained PR104
`INPUT_CLOSURE.md/.json` and `SOL_HANDOFF.md`, its observed-read inventory, and
fresh native fixtures exercising valid method and component review branches.
The historical trace reached five FR texts but not every valid rule-dependency
branch. It was never treated as exhaustive. Fresh workers identified branches,
reviewed concrete counterexamples and retained corrections in `review/REVIEW.md`.

| Read | Complete selector or contract |
|---|---|
| Runtime code/library | Own job folder, existing shared-library closure, materializer, freshness implementation, runner entrypoints/workflow |
| Premise patterns | `jobs/valla/premises.json` |
| Claims | Every live `research/readiness/claims/*.jsonl`; native filename/line winner convention remains unchanged |
| Method records | Every live `research/readiness/method_reviews/*.jsonl` |
| Component records | Every live `research/readiness/component_attestations/*.jsonl` |
| Protocol pins | `jobs/claim-kit/{AGENT_PROTOCOL,BATCH}.md`, Stage19 schema/gate and Stage15 operational-state draft |
| Package inventory | Native Git index query for `research/{excavator,production}/**/RATIONALES.json` |
| Package bodies | Every inventoried package's RATIONALES, decisions and clauses files, including absent sheet siblings |
| Reviewed records | Every method/component `review_ref.path` |
| Historical claim | Every component `reviewed_claim_ref.path` |
| Evidence and rules | Every method/component `dependencies` member with kind `file` or `rule`, using its `key` |
| Prior output | Entire existing Valla output generation; the existing transactional runner moves/restores it |
| Same-run source output | Explicit dynamically referenced output path; existing generation reconciliation remains authoritative |

`source_dependencies()` serializes claim source metadata without opening its
targets. In valid component branches, exact quotation text and original-artifact
paths must already occur among validated file dependencies before their reads.
Over-selecting pointer fields in refused records keeps preparation conservative;
the resolver supplies no legal interpretation or review approval.

## Scope and certificate changes

Existing `scope()` now resolves Valla's explicit pointer records. Sparse provider
bodies are read from the exact HEAD blob; live edits/deletions and newly present
providers are distinguished. Exact targets are freshness roots even if currently
absent. Direct runtime reads are also hashed when Git ignore rules hide a live
file, including package-sheet siblings and fixed protocols. Publication still
rejects bytes absent from the branch tree; no cache bytes are declared retained.
The post-execution check re-discovers live membership and rechecks direct bytes.
Selected producer outputs keep the existing captured-base/candidate rules.

The broad research/data roots in Valla declarations were replaced by the exact
static selectors above. No job or shared-library implementation was edited.
`materialization_certificates.json` extends the existing exact-version mechanism;
it holds one engineering digest, not an input registry or scientific certificate.
Keeping the digest outside the hashed implementation prevents a self-reference.
The pre-existing smoke/transcription certificate entries are unchanged.

Unknown/changed implementation versions retain full repository availability for
Valla, because an unknown version could introduce a new pointer field or import.
Malformed metadata, symlink paths/ancestors and parent traversals also restore
full availability. Their unresolved read scope cannot pass the publication guard.
This deliberately preserves evidence and prior success rather than announcing a
partially observed generation as fresh. Valid ignored direct sources are captured
but cannot be published without retained, branch-verifiable bytes.

## Costs and limits

No worker token/cash counters or complete exclusive labor telemetry are exposed.
The read-audit worker reported about 10 minutes; review and adversarial workers
used fresh OpenAI contexts with inherited model configuration. Actual model-tier
identifiers were not exposed in these workers. No different-family/human review
or scientific adoption is claimed. Initial rejected resolver versions and their
symlink/ignored/late-membership failures were construction/verification costs,
not savings. `COMPARISON.json` records actual machine construction and verification
time when the remote proof completes. OS page-cache state is uncontrolled.

Certificates must be regenerated after combined R1–R4 changes touch their
implementation closure. Other jobs and mixed selections remain conservatively
uncertified. An observed Valla gain is not a project-wide startup, transfer,
model-token or research-hour saving.
