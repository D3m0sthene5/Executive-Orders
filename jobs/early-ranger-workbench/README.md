# Early-Ranger source-review workbench

The existing HTML workbench displays retained page images and explicitly labelled transcripts, and exports attributed research notes. It does not admit or certify an executive order.

Run `job.py` with existing `REPO_ROOT` / `OUTPUT_DIR`. V2 worksheets bind exact per-case candidate and source versions. `--import-worksheet FILE` validates and restores current notes; stale, absent, conflicting, unknown-version and v1 notes remain in an unverified history. Rebuild the HTML to check against newly changed source files.

Optional inputs are explicit: `--retained-workbench PATH` preserves an older workbench representation, `--include-retained-facsimiles` includes the existing held facsimile inventory, and repeated `--facsimile-custody PATH` accepts source packets in that same existing custody format. Paths within an extra custody file are relative to its parent. No optional input is automatically promoted to authenticated original evidence.

The adjacent Python/JavaScript helpers implement the versioned contract; the latter is embedded in the generated HTML. Full contract, exact pins, exercised cases, corresponding census-candidates invocation and adoption requirements: [R3 integration](../../research/progress/r3-ranger-roundtrip/INTEGRATION.md).
