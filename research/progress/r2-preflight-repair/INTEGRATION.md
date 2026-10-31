# R2 integration contract

Base: `88cef0253ed735b2a6e612770f25f9148641ce93`. Branch:
`sol/r2-preflight-repair`. Leave this PR unmerged for root integration.
`CODE_PINS.json` contains full SHA-256 pins for implementation, tests and the
unchanged locator/excavator. Engineering verdict: `engineering-review/REVIEW.json`;
independent source-first seal: `source-review/SOURCE_FIRST_SEAL.json`.

## Diagnostic changes

`original_identity` now also exposes a conflicting recognized printed heading,
with exact observed heading offsets and text hash. It is a source-review lead.
An attributable target in a multi-order source is located before coverage work;
missing/ambiguous target boundaries use `original_boundary`. Existing explicit
`Instrument:` checks and numbered-section diagnostics remain.

New `inventory_command_coverage` / `possible_omitted_command` tasks use existing
clause-drafts location, segmentation, paragraph/recital and furniture handling,
plus existing claim-kit sentence spans. They subtract source-bound exact
inventory ranges and report raw uncovered text, context offsets, modal/command
signals, page/line, source/text hashes and segmentation warnings. Ordinary
recitals and enacting formulas are excluded; authority-led duty and body
quotation candidates are explicitly qualified. Existing OCR-spacing convention
handles `sh all`. No source or inventory is selected, rewritten or approved.

## Required consumer work owned by root

Expand the existing `preflight_dependency_sha256` receipt consistently in
`jobs/claim-kit/batch.py` (packet preparation near line472, load validation near
line533) and `jobs/claim-kit/completion.py` (near line390). Pin both the unchanged
`excavate.py` and `jobs/clause-drafts/segment.py`, whose current SHA-256 is
`0ea7afd1bfd6e5776068d32bda1b58efcc367db3055740ee64709da0caef6573`.
The locator is now exercised for ordinary original evidence, extending a
pre-existing dependency gap. Test a locator-only change staling a packet at
load/apply/completion. Do not relax existing mismatched-version refusal.
Changing `evidence_preflight.py` already stales old packets under existing code
pins; prepare and review new packets through the normal workflow.

No runner/declaration edit is included. Existing claim-kit already depends on
clause-drafts through `_trailing_extent`; verify the combined runner checkout
still hydrates `segment.py`. There are no new packages, approval fields or
canonical holds. Do not dispatch a broad production rebuild from these results.

## Case and Kean actions

`SOURCE_AUDIT_PROPOSALS.json` contains exact-version proposals, including raw
PDF/text/frozen inventory hashes and source-page/character locations. Use the
existing source-audit/correction and independent-review routes if root elects
to pursue them. Three disclosed omission controls are experimental deletions,
not findings against production claims. Check actual effective claim/review
versions separately before any consumer correction. No census, status,
readiness, human certification or source grade is promoted here.

Append the two unique R2 records from `KEAN_FINDINGS.jsonl` through existing
Kean registration, then regenerate its brief. R2 records are also named in
`HANDOFF/notes-r2-preflight-repair.md`. Shared register/brief files were left
outside this assignment's explicit ownership. No new owner decision or ask is
proposed.

## Reproduction and limits

Run `reproduce_residuals.py` and `compare.py` in this directory. Both use the
exact base Git object and current repair; originals are not mutated. Frozen
selection precedes tuning. `FREEZE_CORRECTION.json` records removal of one
spurious terminal newline introduced during EO8930 local hydration; raw PDF,
case selection and operative spans are unchanged. Initial machine output is
retained separately; it is historical output, not a new acceptance benchmark.

The seven-case cohort is purposive and small; four are current segmenter leads,
three are committed native-dossier original/inventory projections. Source-first
examination is a fresh-context OpenAI-family AI review, with no human or
different-family certification. Semantic partitions, clauses without recognized
signals, OCR beyond supported spacing, recitals, post-signature material and
already-covered unrelated text can still evade diagnostics. EO13613 section2(c)
is not individually surfaced by the command signal screen, although its omitted
containing section is flagged. A complete character partition proves no legal
or semantic completeness. See source-review records for exact limits and errata.

The separate held-out `ATTACHMENT_FREEZE.json` adds actual post-signature annex
validation after implementation, without tuning or altering the core freeze.
EO12978's native inventory omits the declaration and incorporated annex names:
the repair flags the declaration and still misses the four annex members.
`source-review/ANNEX_COMPARISON.json` pins the independent complete two-page
source examination and proposed corrections. The final test-only append is
pinned by `engineering-review/APPEND_REVIEW.json`; the original engineering
seal remains unchanged. Final targeted validation: 95 passes, 3 inherited skips
across 98 executions, including 23 passing focused preflight tests.
