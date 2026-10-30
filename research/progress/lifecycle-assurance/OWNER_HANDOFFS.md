# Integration handoffs

Baseline main `f9c6d806ad059dcad7875ab3708715f20ea386df`; observed PR103 `1cdef3d0c87c57a3f8bd68a6d772fb2458b16563`, PR104 `9fa8432a7a0c3550901c5d2acd23e72ae1eab50a`. PR104's published frozen source handoff `8adc9396cf` remains distinct from its moving head. Implementation ownership was announced on both PRs before edits (comments 6511407073 and 6511407272). No response granting broader ownership was assumed.

## Sol: combined integration only

The exact source pin is this PR's commit, supplied in the PR comment. `review/FINAL_REVIEW.json` binds the independently reviewed implementation/test/documentation/replay SHA256s. Runtime changes are exclusively `jobs/readiness-tracker/tracker.py`; its tests and README accompany it. No runner, dependency declaration, claim-kit, Valla or codebook implementation changes are included.

On a separate combined test branch:

1. Combine this source with the explicitly frozen PR103 and PR104 closures. Preserve append-only Kean lines from every branch and regenerate HANDOFF/KEAN.md; do not choose one branch's full brief over the union. Unique namespace here: F-20261029-9101 and F-20261029-9102.
2. Run both OS Road tests, Kean strict check, the existing claim-kit completion/publication/packet tests and PR101 blinding/frozen-baseline checks. Run the existing fallback/failure fixture. Claim-kit imports tracker code, so an isolated branch pass does not establish combined closure compatibility.
3. Run the 45 tracker tests, all 50 checker tests and `replay.py` with isolated outputs. Expect retained claim yes→yes, eligible disclosed exception yes→yes machine_exhausted, and five invalid variants yes→no. Preserve active holds, provisional working-text tests and partial-research nonpromotion. The production tracker launcher already runs test_tracker, including these nine regressions; no test-runner change needed.
4. Check real current exhaustion rows, if any have appeared after this baseline. Invalid rows should be held with a cause; no canonical scientific corrections or policy exceptions are inferred. Recheck changed source/compiler hashes under the existing freshness mechanism. Update dependency closure pins in your ownership if needed; do not reuse stale selective certificates.

No production-ready gain or remote transfer/token saving is claimed. Current canonical exhaustion file is empty at this baseline; source-backed results are bounded fixtures, not refreshed canonical totals.

## Opus: control-scope reproduction

Run `python3 research/progress/lifecycle-assurance/transitions/probe_control_scope.py` at this baseline. In the existing completion fixture, a genuine `whole_case` member remains eligible and `plants_caught=1` after only the planted review's scope becomes `status_only_unrelated_scope` (with exact review/adjudication references re-pinned). `review_record()` requires selected-member scope equality; `controls()` does not check control scope. Checker/tracker are deliberately stubbed by this fixture; this is not a native publication proof.

Current COMPLETION.md specifies the control's independence fields without an explicit expected-scope field. Please determine the intended task scope from the control's planted payload/seed, then validate that the blind rejection and semantic adjudication concern that task. A focused fix could bind an explicit control expected scope to the seeded task and require the review to match; do not let an untrusted self-declared scope alone justify it. Preserve legitimate status controls, lifecycle controls and after-reveal exact genuine reviews. This branch does not edit completion or declare a new policy requirement.

## Valla owner

No Valla implementation or reasoning-dependency capability was changed. The obligation map exposes source attribution, omitted-command completeness, event occurrence and legal-operation reasoning as substantive premises; a checker pass cannot be a witness for those premises by itself. Exact-version source holds have deliberate warning behavior after a version change. Any Valla inheritance proposal must represent that disclosed existing exception, rather than claiming an unresolved objection automatically follows all descendant claims. No new Valla dependency work is requested as a prerequisite to this repair.
