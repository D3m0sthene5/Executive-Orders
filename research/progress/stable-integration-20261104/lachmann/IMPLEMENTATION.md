# Lachmann repeat safety and producer scheduling

Lachmann had no automatic producer edges, and repeating a successful pass could
erase its machine confirmations. Its scope accepted only open text steps; the
tracker turns confirmed steps provisional and removes their old lead blockers.
The next pass consequently rewrote CONFIRMATIONS.jsonl without those members.

The repair freshly reassesses tracker rows that are provisional specifically
from a machine confirmation. The existing witness selection, identity,
completeness, page and exact-byte checks run again. No old approval is copied.
Missing/altered evidence fails, originals remain distinct, and the separate agent
file retains precedence, including negative agent reviews.

Five runnable witness producers now select Lachmann as a downstream consumer:
APP conversion, CSC reports, numbered early orders, Pinakes and Richardson. The
tracker already orders itself after Lachmann. Data fragment/text changes and the
shared working-text implementation select it on the existing sweep. Scheduling
Lachmann alone never selects an upstream acquisition. Hathi, APP harvesting and
Wikisource remain retained source providers without runner entrypoints; they
were not made runnable. The previous tracker snapshot remains the scope input,
so this creates no tracker-to-Lachmann scheduling cycle.

The native two-pass fixture actually runs the tracker and Lachmann wrapper.
Stable sources produce byte-identical confirmations and remain provisional;
changed text and removed declarations fail, and an agent refusal still wins.
Nothing becomes review-ready in this fixture. The job declares the existing
Stage 19 code needed by these native regressions in needs.txt.

## Validation and retained failures

- `BASELINE_REPEAT.log`: baseline ea1e52f runtime with the new native tests,
  four tests, two expected failures. A second healthy pass confirms zero instead
  of one, and a changed-source second pass assesses zero instead of one.
- `REPAIRED_LACHMANN.log`: 52 tests pass, including four native repeat tests and
  two actual picker graph tests.
- `PICKER.log`: 23 tests, one existing skip, no failures. Existing unrelated
  invalid-escape SyntaxWarnings remain visible.
- `NATIVE_WRAPPER_PASS_1.log` and `NATIVE_WRAPPER_PASS_2.log`: both ordinary job.py
  invocations succeed on one synthetic held-source fixture and preserve exactly
  the same confirmation bytes across an intervening tracker recount.
- `BASELINE_FIXTURE_MISSING_NORTON.log`: the first retained baseline harness
  omitted the tracker's transitive NORTON module. The corrected harness includes
  it; no gate was skipped. Initial development fixture setup also lacked Stage
  19 code, then empty required tracker CSVs; those setup errors were corrected
  before the observed baseline assertion failures. The first scheduling graph
  test rejected a proposed Hathi edge because it has no runnable entrypoint;
  that edge was removed rather than inventing a job.

`VALIDATION.json` pins the final owned files, baseline implementation, commands,
logs and observed machine intervals. The retained validation phase took about
five seconds; that is not the full worker or integration cost. Exact worker
deployment/tier, complete elapsed labor, tokens and cash are unavailable. This
is same-family engineering work on synthetic native inputs, without new legal
analysis, corpus-wide acceptance, source authentication, canonical claims,
status adoption, readiness gain, human certification or measured token saving.

Kean search was attempted before implementation but temporarily encountered the
coordinator's merge markers. After conflict resolution it completed and found
no earlier matching work; it also disclosed 1,059 absent tracked report files.
