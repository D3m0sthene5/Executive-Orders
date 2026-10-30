# Lifecycle assurance: clause and temporal checker boundaries

**Baseline:** `f9c6d806ad059dcad7875ab3708715f20ea386df`, branch `lifecycle-assurance-2026-10-29`. Only this owned lifecycle folder is added. No production claims, checker/tracker code, index, or sparse settings were changed.

## Bounded probes

`probe.py` uses the repository's actual claim-kit assembler, claim-checker `Context` / `check_claim` / `summarise_claim`, Stage 19 gate, and readiness-tracker `build` / `summarise` functions. It composes the existing deterministic, temporary fixture builders from `jobs/claim-kit/test_assemble.py`, `jobs/claim-checker/test_checker.py`, and `jobs/readiness-tracker/test_tracker.py`. It runs with network disabled and writes the deterministic JSON receipt in `EXECUTION.json`.

The assembler-only portion constructs original text with two separate commands, omits one command from the dossier and sheet, and confirms the producer inventory flag. The assembler emits one clause with no errors. The separate report-deadline control is rejected with `clause_0_report_deadline_is_not_end`; the other-kind control passes. This portion only establishes assembly behavior.

The composed checker/tracker portion uses the checker suite's held synthetic source text for EO:90001, whose original has two numbered provisions; it drops one `operative_clauses` row while retaining the source's original full text. `check_claim` and `summarise_claim` produce zero failures and pass all five steps. The exact claim hash and those step receipts are then fed to the actual `tracker.build`; the tracker marks all applicable steps done and returns `ready_for_human_review=yes`, tier `complete_claim`. This is a synthetic test fixture, not a historical order, legal result, or certification. `ready_for_human_review` means machine steps pass, not human acceptance.

### Deterministic output

- Assembler-only: incomplete inventory assembled (`1` clause, no errors, original includes omitted command); deadline kind rejected; other-kind control assembled.
- Claim checker: zero errors/failures; `all_checks_passed=true`; all five claim steps true.
- Readiness tracker: no problems; clause inventory and ending/basis done; ready for human review `yes`, tier `complete_claim`.
- Full machine-readable output: [EXECUTION.json](EXECUTION.json).

## Assessment

This demonstrates that a false inventory completeness assertion can cross the tested assembly, checker, and tracker boundaries and appear ready for human review when the dossier/claim omits an original command. This is a real mechanical boundary; the synthetic fixture proves only the interface behavior. `jobs/claim-kit/assemble.py:384-386` requires a producer boolean, while `:475-482` compares the sheet's scopes only with dossier scopes. The Stage 19 gate requires a nonempty unique clause list (`research/stage19/code/claim_gate.py:53-67`) but cannot determine semantic completeness from a source's text. The checker verifies provenance and exact source quotes; it does not infer missing clause inventory. The protocol requires complete source and inventory confirmation (`jobs/claim-kit/AGENT_PROTOCOL.md:27-37`), and Stage 19 explicitly requires the independent human reviewer to assess completeness (`research/stage19/CLAIM_SCHEMA.md:3-12`). I found no generic, reliable lexical repair or narrow checker fix justified by this test.

The explicit `report_deadline` check works at the assembler boundary (`jobs/claim-kit/assemble.py:517-521`). A date, actor, source, and producer confirmation remain assertions; the gate does not determine whether the source proves occurrence or whether an event extinguished a command. That is consistent with Stage 19's structural/provenance limitation and the owner evidence rulings. A bad event-kind label still passes by design at a structural layer; semantic source review remains required.

A real simple original-supported canonical case (EO:12970) and its exact source files are being handled by the coordinator in the native checker-to-tracker replay, so this worker did not hydrate or duplicate it.

## Run and costs

Command: `python3 -I research/progress/lifecycle-assurance/lifecycle/probe.py`

Observed interval for this additional work: 2026-10-30 00:01:02.551965–00:03:35.491291 UTC (152.939 seconds elapsed, wall clock). Configured worker: `gpt-6-luna`. Token telemetry unavailable. The output captures no model-generated findings; all test inputs are deterministic fixtures.
