# Automatic Mission refresh

## Outcome and authority

The owner asked on November 4, 2026: “please make that repair and push to github.”
This change connects Capcom's existing flight calculation to the native reporting
pipeline and adds a Mission tab to the existing GitHub-connected control center.
It was developed on `astra/automatic-mission-refresh-20261104`, from main
`a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6`, independently of the active Tribonian
finalization in [PR 142](https://github.com/D3m0sthene5/Executive-Orders/pull/142).

This is an implementation and engineering-validation record. Pushing these files
does not itself publish a new native readiness generation or redeploy the Site.
See [INTEGRATION.md](INTEGRATION.md) for the concrete landing and acceptance path.

## Why the rocket appeared stuck

The old Claude artifact reads uploaded datasets. Its displayed October 30 mission
could remain unchanged even while GitHub acquired new work. The existing hosted
control center already checks public GitHub main when opened, when refreshed, and
every five minutes while visible, but it lacked the Mission view and a continuously
generated Mission feed. The general job runner intentionally keeps ordinary pushes
light; canonical research filings were otherwise left to its scheduled sweep.

A valid dashboard must distinguish a fresh check of GitHub from a fresh recount.
New claims, a successful code commit, or a newer wall-clock date cannot advance a
rocket whose source tracker still represents an older generation.

## Implementation

- `.github/workflows/refresh-readiness.yml` runs the existing claim checker,
  readiness tracker, and daily digest after relevant main readiness, census,
  reconciled-status, model, or workflow changes; after the main **Run jobs**
  workflow completes; or on explicit main dispatch. It uses the existing materializer, sequential
  runner, and freshness-checked transactional publisher. Its separate concurrency
  group preserves the current run and coalesces queued filings into the newest
  complete recount. It does not modify the general picker or cancel another run.
  Completion events are constrained to this repository's main branch and always
  check out trusted latest main, without consuming upstream artifacts. Native
  generation receipts are bound to the actual checkout commit, since a queued
  event's SHA can predate that checkout. The completion hook does not listen to its
  own workflow and therefore does not recursively retrigger itself.
- `jobs/daily-digest/mission.py` publishes `MISSION.json`, `MISSION_LOG.csv`, and
  `MISSION_REFRESH.json`. It consumes successful native receipts and exact input
  manifests, joins tracker rows to the census, and verifies the existing dashboard
  reconciliation. Both checker and tracker must have consumed the exact committed
  canonical readiness tree. It supports successful outputs generated earlier in
  the same native run, before those outputs have been committed.
- Capcom's maintained builder now exposes its existing snapshot/history functions
  for reuse. The CLI and arithmetic are preserved. The frozen effort weights,
  1,314-order census gap, Apollo endpoint, and archived checkpoints are unchanged.
- The control center gains `#mission`: the Earth-to-Moon flight, rocket, Apollo
  milestones, dated flight log, progress measures, and source details. It checks
  the published feed at a single main revision. Current tracker/checker receipts,
  tracker CSV/summary, census, weights, and human register are independently checked.
  Two small nonrecursive GitHub tree reads check that canonical readiness inputs
  still match the consumed tree. Immutable reads share a bounded cache.
- Missing, mismatched, or unverifiable refreshes retain the last verified flight
  and its original date with a pending notice. A first visit can retain a historical
  flight only after its source hashes validate. Missing human certification remains
  Unknown; AI readiness cannot become human certification.

The reporting path uses ordinary Python, Git metadata, browser JavaScript, and
existing native jobs. It adds no model call. Complete project token savings remain
unmeasured; this change does not claim a shorter full production run.

## Validation and resolved findings

Final local checks passed: 19 Python digest tests, 24 Mission/observability Node
tests, both JavaScript syntax checks, workflow YAML parsing, and diff whitespace
checks. The actual Python-generated synthetic feed also passes through the
JavaScript loader. [LOCAL_VALIDATION.json](LOCAL_VALIDATION.json) retains commands,
counts, measured test durations, and limits.

The independent reviewer initially rejected two defects: an isolated test command
could not import its sibling module, and a newer claim commit could make retained
old successful outputs look current. The first now uses isolated unittest
discovery. The second now binds both native producers to the committed readiness
tree and checks that tree independently in the browser. New regressions also cover
a failed/replaced checker, changed census bytes, missing/truncated tree responses,
retained pending states, output-only commits, and same-day checkpoint replacement.
The final verdict is **approved with documented limits**, with no remaining
blocking finding. Both [the initial review](INITIAL_REVIEW.json) and
[the resolved review](INDEPENDENT_REVIEW.json) are retained.

The full-history golden comparison reproduced the original builder's output
byte-for-byte across 11 daily checkpoints. All 10 archived checkpoints match
exactly. The latest historical checkpoint in that proof is November 2: 784 ready,
14,972 admitted identities, a 16,286 modeled goal, and 0.13597 modeled progress.
Those are historical verification values, not new production gains. The proof took
51.556 seconds including lazy acquisition of historical blobs; see
[HISTORY_EQUIVALENCE.json](HISTORY_EQUIVALENCE.json).

The independent review is an engineering review by another OpenAI agent. It is
neither a different-family scientific review nor human legal certification. The
coordinator used GPT-6 Astra Pro, two bounded Sol implementation workers, and an
Astra engineering reviewer. Full session tokens, cash, and total labor are unknown.

## Scope and limits

The first live feed needs successful compatible native generations on main, then
the revised static assets need publication to the existing Site. The manually
uploaded Claude artifact does not become live through this code change. Its owner
can replace the bookmark with the Site's Mission URL or explicitly refresh that
artifact separately. PR 142 owns the concurrent one-time reconciliation and
publication; this branch does not replace its evidence or output work.

Freshness here is scoped to the observed canonical readiness tree and checked
source files. It does not assert that every upstream scientific source, external
output, status register outside readiness, or legal conclusion is current. Main
runner completions request a reporting refresh even if the upstream run already
included reporting; this can repeat deterministic work. A failed attempt that
leaves all observed inputs and successful outputs unchanged is not represented by
a separate latest-attempt indicator; the displayed successful generation date
remains explicit. An unrelated custom workflow or external output publisher is not
automatically covered by the named Run jobs completion hook. A publication rejected
by the existing freshness guard can still require a later trigger or manual retry.
The three-job bound describes execution, not materialization: the existing runner
retains broad compatibility input scopes. The 90-minute hosted budget needs native
observation; a shorter production duration is not established here.

The scoped tree queries avoid a recursive repository download. Census verification
adds approximately 2.36 MB per newly checked main revision; unchanged revisions
reuse immutable responses. API failure or rate limiting produces a pending state.

Connected-browser visual acceptance was not completed: browser policy rejected the
synthetic self-contained `data:` preview. No workaround was used. Hosted acceptance
must use the normal permitted Site URL. Broader unchanged picker/freshness tests
were not declared passing in this sparse checkout; missing fixture results are
preserved in the review. Hosted CI results belong to their actual commit/run.
